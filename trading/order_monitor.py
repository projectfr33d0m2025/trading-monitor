#!/usr/bin/env python3
"""
Order Monitor - Syncs order status and manages risk orders
Schedule: Every 5 minutes during trading hours (9:30 AM - 4:00 PM ET) + Once at 6:00 PM ET
"""
import os
import sys
from datetime import datetime
from dotenv import load_dotenv
from alpaca.trading.requests import StopOrderRequest, LimitOrderRequest
from alpaca.trading.enums import OrderSide, TimeInForce
import sys
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from shared.database import TradingDB
from alpaca_client import get_trading_client, handle_alpaca_error
import logging

load_dotenv()
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


class OrderMonitor:
    def __init__(self, test_mode=False, db=None, alpaca_client=None):
        """
        Initialize OrderMonitor

        Args:
            test_mode (bool): If True, use test database
            db (TradingDB): Database instance (for testing)
            alpaca_client: Alpaca client instance (for testing)
        """
        self.test_mode = test_mode
        self.db = db if db else TradingDB(test_mode=test_mode)

        try:
            self.alpaca = alpaca_client if alpaca_client else get_trading_client()
        except Exception as e:
            logger.error(f"Failed to initialize Alpaca client: {e}")
            raise

    def run(self):
        """Main monitoring loop"""
        try:
            logger.info("=" * 60)
            logger.info("Order Monitor Starting")
            logger.info("=" * 60)

            # Get orders to monitor (active + terminal statuses that may need trade status update)
            orders = self.db.execute_query("""
                SELECT * FROM order_execution
                WHERE order_status IN ('pending', 'partially_filled', 'new', 'accepted', 'expired', 'cancelled', 'rejected')
                ORDER BY created_at ASC
            """)

            logger.info(f"Found {len(orders)} active orders to monitor")

            if len(orders) == 0:
                logger.info("No active orders to monitor")
                return

            for order in orders:
                self.sync_order_status(order)

            logger.info("Order Monitor Completed")

        except Exception as e:
            logger.error(f"Error in order monitor: {e}", exc_info=True)

    def sync_order_status(self, order):
        """
        Sync order status with Alpaca

        Args:
            order (dict): Order execution record from database
        """
        alpaca_order_id = order['alpaca_order_id']

        try:
            logger.info(f"Syncing order {alpaca_order_id} (type: {order['order_type']})")

            # Get order status from Alpaca
            alpaca_order = self.alpaca.get_order_by_id(alpaca_order_id)

            # Map Alpaca status to our status
            # Alpaca statuses: new, accepted, pending_new, filled, partially_filled, canceled, rejected, expired, etc.
            status_map = {
                'new': 'pending',
                'accepted': 'pending',
                'pending_new': 'pending',
                'filled': 'filled',
                'partially_filled': 'partially_filled',
                'canceled': 'cancelled',
                'rejected': 'cancelled',
                'expired': 'cancelled'
            }
            our_status = status_map.get(alpaca_order.status, alpaca_order.status)

            logger.info(f"Order {alpaca_order_id} status: {alpaca_order.status} -> {our_status}")

            # Update order_execution record
            self.db.execute_query("""
                UPDATE order_execution
                SET order_status = %s,
                    filled_qty = %s,
                    filled_avg_price = %s,
                    filled_at = %s
                WHERE id = %s
            """, (
                our_status,
                int(alpaca_order.filled_qty) if alpaca_order.filled_qty else None,
                float(alpaca_order.filled_avg_price) if alpaca_order.filled_avg_price else None,
                alpaca_order.filled_at,
                order['id']
            ))

            logger.info(f"Updated order_execution record for {alpaca_order_id}")

            # Handle filled entry orders
            if our_status == 'filled' and order['order_type'] == 'ENTRY':
                self.handle_entry_filled(order, alpaca_order)

            # Handle filled exit orders (SL/TP)
            elif our_status == 'filled' and order['order_type'] in ('STOP_LOSS', 'TAKE_PROFIT'):
                self.handle_exit_filled(order, alpaca_order)

            # Handle cancelled/expired/rejected entry orders
            elif our_status == 'cancelled' and order['order_type'] == 'ENTRY':
                self.handle_cancelled_entry_order(order, our_status)

        except Exception as e:
            error_msg = handle_alpaca_error(e, f"syncing order {alpaca_order_id}")
            logger.error(f"Error syncing order: {error_msg}")
            # Continue to next order instead of crashing

    def handle_cancelled_entry_order(self, order, our_status):
        """
        Handle entry orders that were cancelled/expired/rejected.
        These should transition the trade from ORDERED to CANCELLED.

        Args:
            order (dict): Order execution record from database
            our_status (str): The cancelled/rejected/expired status
        """
        trade_journal_id = order['trade_journal_id']

        try:
            # Get current trade status
            trade = self.db.execute_query("""
                SELECT status FROM trade_journal WHERE id = %s
            """, (trade_journal_id,))[0]

            # Only update if trade is still in ORDERED status
            if trade['status'] == 'ORDERED':
                logger.info(f"Entry order {our_status} for trade {trade_journal_id}, updating to CANCELLED")

                # Update trade_journal to CANCELLED
                self.db.execute_query("""
                    UPDATE trade_journal
                    SET status = 'CANCELLED',
                        updated_at = NOW()
                    WHERE id = %s
                """, (trade_journal_id,))

                logger.info(f"✅ Trade {trade_journal_id} cancelled due to {our_status} entry order")
            else:
                logger.info(f"Trade {trade_journal_id} already in {trade['status']} status, skipping cancellation")

        except Exception as e:
            logger.error(f"Error handling cancelled entry order: {e}", exc_info=True)
            raise

    def handle_entry_filled(self, order, alpaca_order):
        """
        Handle filled entry order - Create position and place SL/TP orders

        Args:
            order (dict): Order execution record from database
            alpaca_order: Alpaca order object
        """
        trade_journal_id = order['trade_journal_id']
        symbol = alpaca_order.symbol

        logger.info(f"Entry order filled for {symbol}, creating position...")

        try:
            # Get trade details
            trade = self.db.execute_query("""
                SELECT * FROM trade_journal WHERE id = %s
            """, (trade_journal_id,))[0]

            filled_price = float(alpaca_order.filled_avg_price)
            filled_qty_actual = float(alpaca_order.filled_qty)  # Actual qty for calculations
            filled_qty_db = max(1, int(alpaca_order.filled_qty))  # Qty for database (handle fractional)

            # Update trade_journal
            self.db.execute_query("""
                UPDATE trade_journal
                SET status = 'POSITION',
                    actual_entry = %s,
                    actual_qty = %s,
                    updated_at = NOW()
                WHERE id = %s
            """, (
                filled_price,
                filled_qty_db,
                trade_journal_id
            ))

            logger.info(f"Updated trade_journal {trade_journal_id} to POSITION status")

            # Create position_tracking entry
            cost_basis = filled_price * filled_qty_actual  # Use actual qty for accurate cost basis
            self.db.execute_query("""
                INSERT INTO position_tracking (
                    trade_journal_id, symbol, qty, avg_entry_price,
                    current_price, market_value, cost_basis,
                    unrealized_pnl
                ) VALUES (%s, %s, %s, %s, %s, %s, %s, %s)
            """, (
                trade_journal_id,
                symbol,
                filled_qty_db,
                filled_price,
                filled_price,  # Initial current price = entry price
                cost_basis,  # Initial market value = cost basis
                cost_basis,
                0.0  # Initial P&L = 0
            ))

            logger.info(f"Created position_tracking entry for {symbol}")

            # Place Stop-Loss order
            sl_order = self.place_stop_loss(trade, filled_qty_actual)

            # Place Take-Profit order (if SWING trade)
            tp_order = None
            if trade['trade_style'] == 'SWING' and trade['planned_take_profit']:
                tp_order = self.place_take_profit(trade, filled_qty_actual)

            logger.info(f"✅ Entry filled for {symbol}: price=${filled_price}, qty={filled_qty_actual}")

        except Exception as e:
            logger.error(f"Error handling entry fill for {symbol}: {e}", exc_info=True)
            raise

    def place_stop_loss(self, trade, qty):
        """
        Place stop-loss order

        Args:
            trade (dict): Trade journal record
            qty (int): Quantity to protect

        Returns:
            Order object from Alpaca
        """
        symbol = trade['symbol']
        stop_price = float(trade['planned_stop_loss'])

        logger.info(f"Placing stop-loss order for {symbol} at ${stop_price}")

        try:
            order_request = StopOrderRequest(
                symbol=symbol,
                qty=qty,
                side=OrderSide.SELL,
                time_in_force=TimeInForce.GTC,
                stop_price=stop_price
            )

            sl_order = self.alpaca.submit_order(order_request)

            logger.info(f"Stop-loss order placed: {sl_order.id}")

            # Record in order_execution
            self.db.execute_query("""
                INSERT INTO order_execution (
                    trade_journal_id, alpaca_order_id, client_order_id,
                    order_type, side, order_status, time_in_force, qty,
                    stop_price, created_at
                ) VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, NOW())
            """, (
                trade['id'],
                sl_order.id,
                sl_order.client_order_id,
                'STOP_LOSS',
                'sell',
                'pending',
                'gtc',
                qty,
                stop_price
            ))

            # Update position_tracking with SL order ID
            self.db.execute_query("""
                UPDATE position_tracking
                SET stop_loss_order_id = %s
                WHERE trade_journal_id = %s
            """, (sl_order.id, trade['id']))

            logger.info(f"Recorded stop-loss order in database")

            return sl_order

        except Exception as e:
            error_msg = handle_alpaca_error(e, f"placing stop-loss for {symbol}")
            logger.error(f"Failed to place stop-loss: {error_msg}")
            raise

    def place_take_profit(self, trade, qty):
        """
        Place take-profit order

        Args:
            trade (dict): Trade journal record
            qty (int): Quantity to sell

        Returns:
            Order object from Alpaca
        """
        symbol = trade['symbol']
        limit_price = float(trade['planned_take_profit'])

        logger.info(f"Placing take-profit order for {symbol} at ${limit_price}")

        try:
            order_request = LimitOrderRequest(
                symbol=symbol,
                qty=qty,
                side=OrderSide.SELL,
                time_in_force=TimeInForce.GTC,
                limit_price=limit_price
            )

            tp_order = self.alpaca.submit_order(order_request)

            logger.info(f"Take-profit order placed: {tp_order.id}")

            # Record in order_execution
            self.db.execute_query("""
                INSERT INTO order_execution (
                    trade_journal_id, alpaca_order_id, client_order_id,
                    order_type, side, order_status, time_in_force, qty,
                    limit_price, created_at
                ) VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, NOW())
            """, (
                trade['id'],
                tp_order.id,
                tp_order.client_order_id,
                'TAKE_PROFIT',
                'sell',
                'pending',
                'gtc',
                qty,
                limit_price
            ))

            # Update position_tracking with TP order ID
            self.db.execute_query("""
                UPDATE position_tracking
                SET take_profit_order_id = %s
                WHERE trade_journal_id = %s
            """, (tp_order.id, trade['id']))

            logger.info(f"Recorded take-profit order in database")

            return tp_order

        except Exception as e:
            error_msg = handle_alpaca_error(e, f"placing take-profit for {symbol}")
            logger.error(f"Failed to place take-profit: {error_msg}")
            raise

    def handle_exit_filled(self, order, alpaca_order):
        """
        Handle filled exit order (SL or TP) - Close trade

        Args:
            order (dict): Order execution record from database
            alpaca_order: Alpaca order object
        """
        trade_journal_id = order['trade_journal_id']
        symbol = alpaca_order.symbol

        logger.info(f"Exit order filled for {symbol}, closing trade...")

        try:
            # Get trade details
            trade = self.db.execute_query("""
                SELECT * FROM trade_journal WHERE id = %s
            """, (trade_journal_id,))[0]

            # Calculate P&L
            exit_price = float(alpaca_order.filled_avg_price)
            entry_price = float(trade['actual_entry'])
            qty_actual = float(alpaca_order.filled_qty)  # Use actual qty for accurate P&L
            pnl = (exit_price - entry_price) * qty_actual

            # Determine exit reason
            exit_reason = 'STOPPED_OUT' if order['order_type'] == 'STOP_LOSS' else 'TARGET_HIT'

            logger.info(f"Trade closed: entry=${entry_price}, exit=${exit_price}, P&L=${pnl:.2f}, reason={exit_reason}")

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
                DELETE FROM position_tracking WHERE trade_journal_id = %s
            """, (trade_journal_id,))

            logger.info(f"Deleted position_tracking for {symbol}")

            # Cancel remaining order (if SL hit, cancel TP and vice versa)
            self.cancel_remaining_orders(trade_journal_id, alpaca_order.id)

            logger.info(f"✅ Position closed: {symbol}, P&L=${pnl:.2f}, Reason={exit_reason}")

        except Exception as e:
            logger.error(f"Error handling exit fill for {symbol}: {e}", exc_info=True)
            raise

    def cancel_remaining_orders(self, trade_journal_id, filled_order_id):
        """
        Cancel remaining SL/TP orders after one fills

        Args:
            trade_journal_id (int): Trade journal ID
            filled_order_id (str): Alpaca order ID that was filled
        """
        try:
            # Find remaining pending SL/TP orders
            orders = self.db.execute_query("""
                SELECT alpaca_order_id FROM order_execution
                WHERE trade_journal_id = %s
                AND order_type IN ('STOP_LOSS', 'TAKE_PROFIT')
                AND order_status IN ('pending', 'new', 'accepted')
                AND alpaca_order_id != %s
            """, (trade_journal_id, filled_order_id))

            for order in orders:
                try:
                    order_id = order['alpaca_order_id']
                    self.alpaca.cancel_order_by_id(order_id)
                    logger.info(f"Cancelled remaining order: {order_id}")

                    # Update status in database
                    self.db.execute_query("""
                        UPDATE order_execution
                        SET order_status = 'cancelled'
                        WHERE alpaca_order_id = %s
                    """, (order_id,))

                except Exception as e:
                    logger.warning(f"Could not cancel order {order_id}: {e}")
                    # Continue even if cancel fails

        except Exception as e:
            logger.error(f"Error canceling remaining orders: {e}")


def main():
    """Main entry point"""
    # Check for test mode flag
    test_mode = '--test-mode' in sys.argv

    if test_mode:
        logger.info("Running in TEST MODE")

    try:
        monitor = OrderMonitor(test_mode=test_mode)
        monitor.run()
    except Exception as e:
        logger.error(f"Order monitor failed: {e}", exc_info=True)
        sys.exit(1)


if __name__ == "__main__":
    main()
