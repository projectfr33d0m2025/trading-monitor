#!/usr/bin/env python3
"""
Order Executor - Executes approved trading decisions
Schedule: Once daily at 9:45 AM ET (15 minutes after market open)
"""
import os
import sys
from datetime import datetime
from dotenv import load_dotenv
from alpaca.trading.requests import MarketOrderRequest, LimitOrderRequest
from alpaca.trading.enums import OrderSide, TimeInForce
import sys
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from shared.database import TradingDB
from alpaca_client import get_trading_client, handle_alpaca_error
import logging
import json

load_dotenv()
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


class OrderExecutor:
    def __init__(self, test_mode=False, db=None, alpaca_client=None):
        """
        Initialize OrderExecutor

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
        """Main execution loop"""
        try:
            logger.info("=" * 60)
            logger.info("Order Executor Starting")
            logger.info("=" * 60)

            # Get unexecuted decisions where primary_action requires execution
            decisions = self.db.execute_query("""
                SELECT * FROM analysis_decision
                WHERE executed = false
                AND "Approve" = true
                AND "Decision"->>'primary_action' IN ('NEW_TRADE', 'CANCEL', 'AMEND')
                ORDER BY "Date_time" ASC
            """)

            logger.info(f"Found {len(decisions)} unexecuted decisions")

            if len(decisions) == 0:
                logger.info("No pending decisions to execute")
                return

            for decision in decisions:
                self.process_decision(decision)

            logger.info("Order Executor Completed")

        except Exception as e:
            logger.error(f"Error in order executor: {e}", exc_info=True)

    def process_decision(self, decision):
        """
        Process a single trading decision

        Args:
            decision (dict): Decision record from database
        """
        decision_data = decision.get('Decision', {})
        primary_action = decision_data.get('primary_action')
        analysis_id = decision['Analysis_Id']

        logger.info(f"Processing decision {analysis_id}: {primary_action}")

        try:
            if primary_action == 'NEW_TRADE':
                self.handle_new_trade(decision)
            elif primary_action == 'CANCEL':
                self.handle_cancel(decision)
            elif primary_action == 'AMEND':
                self.handle_amend(decision)
            else:
                logger.warning(f"Unknown primary_action: {primary_action} for decision {analysis_id}")

        except Exception as e:
            logger.error(f"Error processing decision {analysis_id}: {e}", exc_info=True)
            # Continue to next decision instead of crashing

    def handle_new_trade(self, decision):
        """
        Handle NEW_TRADE action - Place entry order

        Args:
            decision (dict): Decision record from database
        """
        decision_data = decision.get('Decision', {})
        analysis_id = decision['Analysis_Id']

        # Extract from structure: Decision.new_trade
        new_trade = decision_data.get('new_trade', {})

        # Extract trade parameters
        # Use Ticker column as authoritative source (strip exchange suffix like ':NYSE')
        ticker_raw = decision['Ticker']
        symbol = ticker_raw.split(':')[0] if ':' in ticker_raw else ticker_raw
        side = new_trade.get('side', 'buy')  # buy or sell
        qty = new_trade.get('qty')
        limit_price = new_trade.get('limit_price')  # entry price

        # stop_loss and take_profit are now objects
        stop_loss_obj = new_trade.get('stop_loss', {})
        stop_price = stop_loss_obj.get('stop_price') if isinstance(stop_loss_obj, dict) else stop_loss_obj

        take_profit_obj = new_trade.get('take_profit')
        take_profit_price = None
        if take_profit_obj and isinstance(take_profit_obj, dict):
            take_profit_price = take_profit_obj.get('limit_price')
        elif take_profit_obj:
            take_profit_price = take_profit_obj

        strategy = new_trade.get('strategy', 'SWING')  # SWING or TREND (was trade_style)
        pattern = new_trade.get('pattern', '')

        # Extract time_in_force from JSON, default to GTC
        time_in_force_str = new_trade.get('time_in_force', 'gtc')

        # Map string to Alpaca TimeInForce enum
        time_in_force_map = {
            'day': TimeInForce.DAY,
            'gtc': TimeInForce.GTC,
            'ioc': TimeInForce.IOC,
            'fok': TimeInForce.FOK,
            'opg': TimeInForce.OPG,
            'cls': TimeInForce.CLS
        }
        time_in_force = time_in_force_map.get(time_in_force_str.lower(), TimeInForce.GTC)

        # Validate required fields
        if not all([qty, limit_price, stop_price]):
            logger.error(f"Missing required fields for {analysis_id}: qty={qty}, limit_price={limit_price}, stop_price={stop_price}")
            return

        logger.info(f"Placing {side.upper()} order for {symbol}: qty={qty}, entry=${limit_price}, sl=${stop_price}, tp=${take_profit_price}, time_in_force=${time_in_force}")

        try:
            # Determine order side from new structure
            order_side = OrderSide.BUY if side.lower() == 'buy' else OrderSide.SELL

            # Submit limit order to Alpaca
            order_request = LimitOrderRequest(
                symbol=symbol,
                qty=float(qty),  # Send actual fractional qty to Alpaca
                side=order_side,
                time_in_force=time_in_force,
                limit_price=float(limit_price)
            )

            order = self.alpaca.submit_order(order_request)

            logger.info(f"Order submitted successfully: {order.id}")

            # Create unique trade_id with microseconds to avoid collisions
            trade_id = f"{symbol}_{datetime.now().strftime('%Y%m%d%H%M%S%f')}"

            # Create trade_journal entry (trade_style is now strategy)
            trade_journal_id = self.db.execute_query("""
                INSERT INTO trade_journal (
                    trade_id, symbol, trade_style, pattern, status,
                    initial_analysis_id, planned_entry, planned_stop_loss,
                    planned_take_profit, planned_qty, created_at, updated_at
                ) VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, NOW(), NOW())
                RETURNING id
            """, (
                trade_id,
                symbol,
                strategy,  # Using strategy from new_trade
                pattern,
                'ORDERED',
                analysis_id,
                float(limit_price),  # Was entry_price
                float(stop_price),    # Was stop_loss
                float(take_profit_price) if take_profit_price else None,
                max(1, int(qty))  # Store 1 for fractional, int(qty) for whole numbers
            ))[0]['id']

            logger.info(f"Created trade_journal entry: {trade_journal_id}")

            # Create order_execution entry
            self.db.execute_query("""
                INSERT INTO order_execution (
                    trade_journal_id, analysis_decision_id, alpaca_order_id,
                    client_order_id, order_type, side, order_status,
                    time_in_force, qty, limit_price, created_at
                ) VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, NOW())
            """, (
                trade_journal_id,
                analysis_id,
                order.id,
                order.client_order_id,
                'ENTRY',
                side.lower(),  # buy or sell from new_trade
                'pending',
                time_in_force_str.lower(),  # Use actual time_in_force from decision
                max(1, int(qty)),  # Store 1 for fractional, int(qty) for whole numbers
                float(limit_price)  # Was entry_price
            ))

            logger.info(f"Created order_execution entry for order {order.id}")

            # Update analysis_decision - mark as executed
            self.db.execute_query("""
                UPDATE analysis_decision
                SET executed = true,
                    execution_time = NOW(),
                    existing_order_id = %s,
                    existing_trade_journal_id = %s
                WHERE "Analysis_Id" = %s
            """, (order.id, trade_journal_id, analysis_id))

            logger.info(f"✅ Successfully placed order {order.id} for {symbol}")

        except Exception as e:
            error_msg = handle_alpaca_error(e, f"placing order for {symbol}")
            logger.error(f"Failed to place order for {analysis_id}: {error_msg}")
            raise

    def handle_cancel(self, decision):
        """
        Handle CANCEL action - Cancel existing order

        Args:
            decision (dict): Decision record from database
        """
        analysis_id = decision['Analysis_Id']
        order_id = decision.get('existing_order_id')
        trade_journal_id = decision.get('existing_trade_journal_id')

        if not order_id:
            logger.warning(f"No order to cancel for decision {analysis_id}")
            # Still mark as executed to prevent reprocessing
            self.db.execute_query("""
                UPDATE analysis_decision
                SET executed = true,
                    execution_time = NOW()
                WHERE "Analysis_Id" = %s
            """, (analysis_id,))
            return

        logger.info(f"Canceling order {order_id}")

        try:
            # Cancel order with Alpaca
            self.alpaca.cancel_order_by_id(order_id)

            logger.info(f"Order {order_id} cancelled successfully")

            # Update order_execution status immediately
            self.db.execute_query("""
                UPDATE order_execution
                SET order_status = 'cancelled'
                WHERE alpaca_order_id = %s
            """, (order_id,))

            logger.info(f"Updated order_execution for {order_id} to cancelled")

            # Update trade_journal if it exists
            if trade_journal_id:
                self.db.execute_query("""
                    UPDATE trade_journal
                    SET status = 'CANCELLED',
                        exit_date = CURRENT_DATE,
                        exit_reason = 'CANCELLED',
                        updated_at = NOW()
                    WHERE id = %s
                """, (trade_journal_id,))

                logger.info(f"Updated trade_journal {trade_journal_id} to CANCELLED")

            # Mark decision as executed
            self.db.execute_query("""
                UPDATE analysis_decision
                SET executed = true,
                    execution_time = NOW()
                WHERE "Analysis_Id" = %s
            """, (analysis_id,))

            logger.info(f"✅ Successfully cancelled order {order_id}")

        except Exception as e:
            error_msg = handle_alpaca_error(e, f"canceling order {order_id}")
            logger.error(f"Failed to cancel order: {error_msg}")
            raise

    def handle_amend(self, decision):
        """
        Handle AMEND action - Cancel old order and place new one

        Args:
            decision (dict): Decision record from database
        """
        analysis_id = decision['Analysis_Id']
        symbol = decision['Ticker']

        logger.info(f"Amending order for {symbol}")

        try:
            # First, cancel the old order
            self.handle_cancel(decision)

            # Reset executed flag so new order can be placed
            self.db.execute_query("""
                UPDATE analysis_decision
                SET executed = false
                WHERE "Analysis_Id" = %s
            """, (analysis_id,))

            # Place the new order
            self.handle_new_trade(decision)

            logger.info(f"✅ Successfully amended order for {symbol}")

        except Exception as e:
            logger.error(f"Failed to amend order for {analysis_id}: {e}", exc_info=True)
            raise


def main():
    """Main entry point"""
    # Check for test mode flag
    test_mode = '--test-mode' in sys.argv

    if test_mode:
        logger.info("Running in TEST MODE")

    try:
        executor = OrderExecutor(test_mode=test_mode)
        executor.run()
    except Exception as e:
        logger.error(f"Order executor failed: {e}", exc_info=True)
        sys.exit(1)


if __name__ == "__main__":
    main()
