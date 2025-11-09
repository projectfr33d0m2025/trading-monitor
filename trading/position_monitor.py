#!/usr/bin/env python3
"""
Position Monitor - Updates position values and P&L
Schedule: Every 10 minutes during trading hours (9:30 AM - 4:00 PM ET) + Once at 6:15 PM ET
"""
import os
import sys
from dotenv import load_dotenv
from alpaca.data.requests import StockLatestQuoteRequest
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from shared.database import TradingDB
from alpaca_client import get_trading_client, get_data_client, handle_alpaca_error
import logging

load_dotenv()
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


class PositionMonitor:
    def __init__(self, test_mode=False, db=None, trading_client=None, data_client=None):
        """
        Initialize PositionMonitor

        Args:
            test_mode (bool): If True, use test database
            db (TradingDB): Database instance (for testing)
            trading_client: Alpaca trading client (for testing)
            data_client: Alpaca data client (for testing)
        """
        self.test_mode = test_mode
        self.db = db if db else TradingDB(test_mode=test_mode)

        try:
            self.trading_client = trading_client if trading_client else get_trading_client()
            self.data_client = data_client if data_client else get_data_client()
        except Exception as e:
            logger.error(f"Failed to initialize Alpaca clients: {e}")
            raise

    def run(self):
        """Main monitoring loop"""
        try:
            logger.info("=" * 60)
            logger.info("Position Monitor Starting")
            logger.info("=" * 60)

            # Get all active positions
            positions = self.db.execute_query("""
                SELECT * FROM position_tracking
                ORDER BY symbol ASC
            """)

            logger.info(f"Found {len(positions)} active positions to monitor")

            if len(positions) == 0:
                logger.info("No active positions to monitor")
                return

            for position in positions:
                self.update_position(position)

            # Check for positions closed outside system
            self.check_for_closed_positions()

            logger.info("Position Monitor Completed")

        except Exception as e:
            logger.error(f"Error in position monitor: {e}", exc_info=True)

    def update_position(self, position):
        """
        Update position values and unrealized P&L

        Args:
            position (dict): Position tracking record from database
        """
        symbol = position['symbol']

        try:
            logger.info(f"Updating position: {symbol}")

            # Get current price from Alpaca
            request = StockLatestQuoteRequest(symbol_or_symbols=symbol)
            quote_data = self.data_client.get_stock_latest_quote(request)

            # Extract quote for this symbol
            quote = quote_data[symbol]

            # Use bid/ask midpoint for more accurate pricing
            # Use ask price if bid is not available
            if quote.bid_price and quote.ask_price:
                current_price = (float(quote.bid_price) + float(quote.ask_price)) / 2
            elif quote.ask_price:
                current_price = float(quote.ask_price)
            else:
                logger.warning(f"No valid price data for {symbol}, skipping update")
                return

            # Calculate metrics
            qty = position.get('qty_', position.get('qty'))  # Handle both NocoDB (qty_) and direct DB (qty)
            avg_entry = float(position['avg_entry_price'])
            market_value = current_price * qty
            cost_basis = float(position['cost_basis'])
            unrealized_pnl = (current_price - avg_entry) * qty

            # Update position_tracking
            self.db.execute_query("""
                UPDATE position_tracking
                SET current_price = %s,
                    market_value = %s,
                    unrealized_pnl = %s,
                    last_updated = NOW()
                WHERE id = %s
            """, (current_price, market_value, unrealized_pnl, position['id']))

            logger.info(
                f"Updated {symbol}: price=${current_price:.2f}, "
                f"value=${market_value:.2f}, P&L=${unrealized_pnl:.2f}"
            )

        except Exception as e:
            error_msg = handle_alpaca_error(e, f"updating position {symbol}")
            logger.error(f"Error updating position: {error_msg}")
            # Continue to next position instead of crashing

    def check_for_closed_positions(self):
        """
        Verify positions still exist in Alpaca and reconcile any closed positions
        """
        try:
            logger.info("Checking for positions closed outside system...")

            # Get Alpaca positions
            try:
                alpaca_positions_list = self.trading_client.get_all_positions()
                alpaca_positions = {p.symbol: p for p in alpaca_positions_list}
                logger.info(f"Found {len(alpaca_positions)} positions in Alpaca")
            except Exception as e:
                logger.warning(f"Could not fetch Alpaca positions: {e}")
                return

            # Get our tracked positions
            tracked_positions = self.db.execute_query("""
                SELECT * FROM position_tracking
            """)

            for position in tracked_positions:
                symbol = position['symbol']
                if symbol not in alpaca_positions:
                    logger.warning(f"Position {symbol} closed outside of monitoring system")
                    self.reconcile_closed_position(position)

        except Exception as e:
            logger.error(f"Error checking closed positions: {e}", exc_info=True)

    def reconcile_closed_position(self, position):
        """
        Reconcile a position that was closed outside the system

        Args:
            position (dict): Position tracking record
        """
        trade_journal_id = position['trade_journal_id']
        symbol = position['symbol']

        logger.info(f"Reconciling closed position: {symbol}")

        try:
            # Try to find the closing order in our database
            orders = self.db.execute_query("""
                SELECT * FROM order_execution
                WHERE trade_journal_id = %s
                AND order_type IN ('STOP_LOSS', 'TAKE_PROFIT')
                AND order_status = 'filled'
                ORDER BY filled_at DESC
                LIMIT 1
            """, (trade_journal_id,))

            if orders:
                # Use the filled order data
                order = orders[0]
                exit_price = float(order['filled_avg_price'])
                qty = position.get('qty_', position.get('qty'))  # Handle both NocoDB (qty_) and direct DB (qty)
                pnl = (exit_price - float(position['avg_entry_price'])) * qty
                exit_reason = 'STOPPED_OUT' if order['order_type'] == 'STOP_LOSS' else 'TARGET_HIT'

                logger.info(f"Found closing order: exit=${exit_price}, P&L=${pnl:.2f}, reason={exit_reason}")
            else:
                # Manual close or unknown - use last known price
                exit_price = float(position['current_price'])
                pnl = float(position['unrealized_pnl'])
                exit_reason = 'MANUAL_EXIT'

                logger.info(f"No closing order found, using last price: exit=${exit_price}, P&L=${pnl:.2f}")

            # Update trade_journal
            self.db.execute_query("""
                UPDATE trade_journal
                SET status = 'CLOSED',
                    exit_date = CURRENT_DATE,
                    exit_price = %s,
                    actual_pnl = %s,
                    exit_reason = %s,
                    updated_at = NOW()
                WHERE id = %s
            """, (exit_price, pnl, exit_reason, trade_journal_id))

            logger.info(f"Updated trade_journal {trade_journal_id} to CLOSED")

            # Delete position_tracking
            self.db.execute_query("""
                DELETE FROM position_tracking WHERE id = %s
            """, (position['id'],))

            logger.info(f"Deleted position_tracking for {symbol}")

            # Try to cancel any remaining orders
            try:
                remaining_orders = self.db.execute_query("""
                    SELECT alpaca_order_id FROM order_execution
                    WHERE trade_journal_id = %s
                    AND order_type IN ('STOP_LOSS', 'TAKE_PROFIT')
                    AND order_status IN ('pending', 'new', 'accepted')
                """, (trade_journal_id,))

                for order in remaining_orders:
                    try:
                        self.trading_client.cancel_order_by_id(order['alpaca_order_id'])
                        logger.info(f"Cancelled remaining order: {order['alpaca_order_id']}")
                    except:
                        pass  # Ignore errors, order might already be cancelled

            except Exception as e:
                logger.warning(f"Could not cancel remaining orders: {e}")

            logger.info(f"✅ Reconciled closed position: {symbol}, P&L=${pnl:.2f}")

        except Exception as e:
            logger.error(f"Error reconciling closed position {symbol}: {e}", exc_info=True)


def main():
    """Main entry point"""
    # Check for test mode flag
    test_mode = '--test-mode' in sys.argv

    if test_mode:
        logger.info("Running in TEST MODE")

    try:
        monitor = PositionMonitor(test_mode=test_mode)
        monitor.run()
    except Exception as e:
        logger.error(f"Position monitor failed: {e}", exc_info=True)
        sys.exit(1)


if __name__ == "__main__":
    main()
