"""
Unit tests for Order Executor
Tests NEW_TRADE, CANCEL, and AMEND actions
"""
import pytest
import json
from order_executor import OrderExecutor


class TestOrderExecutorNewTrade:
    """Test NEW_TRADE functionality"""

    def test_new_trade_basic(self, test_db, mock_alpaca_client, sample_analysis_decision):
        """Test basic NEW_TRADE execution"""
        # Insert analysis decision
        decision_json = json.dumps(sample_analysis_decision['Decision'])
        test_db.execute_query("""
            INSERT INTO analysis_decision (
                "Analysis_Id", "Ticker", "Decision", executed, "Approve"
            ) VALUES (%s, %s, %s::jsonb, %s, %s)
        """, (
            sample_analysis_decision['Analysis_Id'],
            sample_analysis_decision['Ticker'],
            decision_json,
            sample_analysis_decision['executed'],
            sample_analysis_decision['Approve']
        ))

        # Create executor
        executor = OrderExecutor(test_mode=True, db=test_db, alpaca_client=mock_alpaca_client)

        # Run executor
        executor.run()

        # Verify order was submitted
        assert len(mock_alpaca_client.orders) == 1
        order = list(mock_alpaca_client.orders.values())[0]
        assert order.symbol == 'AAPL'
        assert float(order.qty) == 10.0
        assert order.side == 'buy'
        assert order.limit_price == 150.00

        # Verify trade_journal entry was created
        trades = test_db.query('trade_journal', 'symbol = %s', ('AAPL',))
        assert len(trades) == 1
        trade = trades[0]
        assert trade['status'] == 'ORDERED'
        assert float(trade['planned_entry']) == 150.00
        assert float(trade['planned_stop_loss']) == 145.00
        assert float(trade['planned_take_profit']) == 160.00
        assert trade['planned_qty'] == 10

        # Verify order_execution entry was created
        orders = test_db.query('order_execution', 'order_type = %s', ('ENTRY',))
        assert len(orders) == 1
        order_exec = orders[0]
        assert order_exec['side'] == 'buy'
        assert order_exec['order_status'] == 'pending'
        assert order_exec['qty'] == 10
        assert float(order_exec['limit_price']) == 150.00

        # Verify analysis_decision was marked as executed
        decision = test_db.execute_query(
            'SELECT * FROM analysis_decision WHERE "Analysis_Id" = %s',
            ('TEST_001',)
        )[0]
        assert decision['executed'] is True
        assert decision['existing_order_id'] == order.id

    def test_new_trade_sell_order(self, test_db, mock_alpaca_client):
        """Test NEW_TRADE with SELL action"""
        # Insert SELL decision with new structure
        decision = {
            "symbol": "TSLA",
            "analysis_date": "2025-01-15",
            "support": 190.0,
            "resistance": 210.0,
            "primary_action": "NEW_TRADE",
            "new_trade": {
                "strategy": "SWING",
                "pattern": "SHORT_PATTERN",
                "qty": 5,
                "side": "sell",
                "type": "limit",
                "time_in_force": "day",
                "limit_price": 200.00,
                "stop_loss": {
                    "stop_price": 205.00
                },
                "reward_risk_ratio": 2.0,
                "risk_amount": 25.00,
                "risk_percentage": 1.0
            }
        }
        decision_json = json.dumps(decision)

        test_db.execute_query("""
            INSERT INTO analysis_decision (
                "Analysis_Id", "Ticker", "Decision", executed, "Approve"
            ) VALUES (%s, %s, %s::jsonb, %s, %s)
        """, ('TEST_SELL', 'TSLA', decision_json, False, True))

        # Create and run executor
        executor = OrderExecutor(test_mode=True, db=test_db, alpaca_client=mock_alpaca_client)
        executor.run()

        # Verify SELL order
        assert len(mock_alpaca_client.orders) == 1
        order = list(mock_alpaca_client.orders.values())[0]
        assert order.symbol == 'TSLA'
        assert order.side == 'sell'
        assert float(order.qty) == 5.0

    def test_new_trade_missing_required_fields(self, test_db, mock_alpaca_client):
        """Test NEW_TRADE with missing required fields"""
        # Insert decision without qty (missing required field)
        decision = {
            "symbol": "AAPL",
            "analysis_date": "2025-01-15",
            "support": 140.0,
            "resistance": 165.0,
            "primary_action": "NEW_TRADE",
            "new_trade": {
                "strategy": "SWING",
                "side": "buy",
                "type": "limit",
                "time_in_force": "day",
                "limit_price": 150.00,
                "stop_loss": {
                    "stop_price": 145.00
                }
                # Missing qty!
            }
        }
        decision_json = json.dumps(decision)

        test_db.execute_query("""
            INSERT INTO analysis_decision (
                "Analysis_Id", "Ticker", "Decision", executed, "Approve"
            ) VALUES (%s, %s, %s::jsonb, %s, %s)
        """, ('TEST_MISSING', 'AAPL', decision_json, False, True))

        # Create and run executor
        executor = OrderExecutor(test_mode=True, db=test_db, alpaca_client=mock_alpaca_client)
        executor.run()

        # Verify no order was placed
        assert len(mock_alpaca_client.orders) == 0

        # Verify decision was NOT marked as executed
        decision = test_db.execute_query(
            'SELECT * FROM analysis_decision WHERE "Analysis_Id" = %s',
            ('TEST_MISSING',)
        )[0]
        assert decision['executed'] is False

    def test_new_trade_no_pending_decisions(self, test_db, mock_alpaca_client):
        """Test executor with no pending decisions"""
        executor = OrderExecutor(test_mode=True, db=test_db, alpaca_client=mock_alpaca_client)
        executor.run()

        # Verify no orders were placed
        assert len(mock_alpaca_client.orders) == 0

    def test_new_trade_multiple_decisions(self, test_db, mock_alpaca_client):
        """Test executor with multiple pending decisions"""
        # Insert multiple decisions with new structure
        decisions = [
            ('TEST_001', 'AAPL', {
                "symbol": "AAPL", "analysis_date": "2025-01-15", "support": 140.0, "resistance": 165.0,
                "primary_action": "NEW_TRADE",
                "new_trade": {"strategy": "SWING", "qty": 10, "side": "buy", "type": "limit",
                              "time_in_force": "day", "limit_price": 150.00,
                              "stop_loss": {"stop_price": 145.00}}}),
            ('TEST_002', 'MSFT', {
                "symbol": "MSFT", "analysis_date": "2025-01-15", "support": 285.0, "resistance": 315.0,
                "primary_action": "NEW_TRADE",
                "new_trade": {"strategy": "SWING", "qty": 5, "side": "buy", "type": "limit",
                              "time_in_force": "day", "limit_price": 300.00,
                              "stop_loss": {"stop_price": 290.00}}}),
            ('TEST_003', 'GOOGL', {
                "symbol": "GOOGL", "analysis_date": "2025-01-15", "support": 130.0, "resistance": 150.0,
                "primary_action": "NEW_TRADE",
                "new_trade": {"strategy": "SWING", "qty": 3, "side": "buy", "type": "limit",
                              "time_in_force": "day", "limit_price": 140.00,
                              "stop_loss": {"stop_price": 135.00}}})
        ]

        for analysis_id, ticker, decision in decisions:
            decision_json = json.dumps(decision)
            test_db.execute_query("""
                INSERT INTO analysis_decision (
                    "Analysis_Id", "Ticker", "Decision", executed, "Approve"
                ) VALUES (%s, %s, %s::jsonb, %s, %s)
            """, (analysis_id, ticker, decision_json, False, True))

        # Run executor
        executor = OrderExecutor(test_mode=True, db=test_db, alpaca_client=mock_alpaca_client)
        executor.run()

        # Verify all orders were placed
        assert len(mock_alpaca_client.orders) == 3

        # Verify all symbols
        symbols = [order.symbol for order in mock_alpaca_client.orders.values()]
        assert 'AAPL' in symbols
        assert 'MSFT' in symbols
        assert 'GOOGL' in symbols

    def test_new_trade_with_take_profit(self, test_db, mock_alpaca_client):
        """Test NEW_TRADE with take_profit specified (SWING trade)"""
        decision = {
            "symbol": "AAPL",
            "analysis_date": "2025-01-15",
            "support": 140.0,
            "resistance": 165.0,
            "primary_action": "NEW_TRADE",
            "new_trade": {
                "strategy": "SWING",
                "pattern": "Breakout",
                "qty": 10,
                "side": "buy",
                "type": "limit",
                "time_in_force": "day",
                "limit_price": 150.00,
                "stop_loss": {
                    "stop_price": 145.00
                },
                "take_profit": {
                    "limit_price": 160.00
                },
                "reward_risk_ratio": 2.0,
                "risk_amount": 50.00,
                "risk_percentage": 1.0
            }
        }
        decision_json = json.dumps(decision)

        test_db.execute_query("""
            INSERT INTO analysis_decision (
                "Analysis_Id", "Ticker", "Decision", executed, "Approve"
            ) VALUES (%s, %s, %s::jsonb, %s, %s)
        """, ('TEST_TP', 'AAPL', decision_json, False, True))

        executor = OrderExecutor(test_mode=True, db=test_db, alpaca_client=mock_alpaca_client)
        executor.run()

        # Verify trade_journal has take_profit
        trades = test_db.query('trade_journal', 'symbol = %s', ('AAPL',))
        assert len(trades) == 1
        assert float(trades[0]['planned_take_profit']) == 160.00

    def test_new_trade_daytrade_style(self, test_db, mock_alpaca_client):
        """Test NEW_TRADE with TREND strategy (no take_profit)"""
        decision = {
            "symbol": "AAPL",
            "analysis_date": "2025-01-15",
            "support": 140.0,
            "resistance": 165.0,
            "primary_action": "NEW_TRADE",
            "new_trade": {
                "strategy": "TREND",
                "pattern": "TrendFollowing",
                "qty": 10,
                "side": "buy",
                "type": "limit",
                "time_in_force": "day",
                "limit_price": 150.00,
                "stop_loss": {
                    "stop_price": 145.00
                },
                # No take_profit for TREND trades
                "reward_risk_ratio": 3.0,
                "risk_amount": 50.00,
                "risk_percentage": 1.0
            }
        }
        decision_json = json.dumps(decision)

        test_db.execute_query("""
            INSERT INTO analysis_decision (
                "Analysis_Id", "Ticker", "Decision", executed, "Approve"
            ) VALUES (%s, %s, %s::jsonb, %s, %s)
        """, ('TEST_DT', 'AAPL', decision_json, False, True))

        executor = OrderExecutor(test_mode=True, db=test_db, alpaca_client=mock_alpaca_client)
        executor.run()

        # Verify trade_journal has no take_profit
        trades = test_db.query('trade_journal', 'symbol = %s', ('AAPL',))
        assert len(trades) == 1
        assert trades[0]['planned_take_profit'] is None


class TestOrderExecutorCancel:
    """Test CANCEL functionality"""

    def test_cancel_existing_order(self, test_db, mock_alpaca_client):
        """Test canceling an existing order"""
        # First create an order with new structure
        decision = {
            "symbol": "AAPL",
            "analysis_date": "2025-01-15",
            "support": 140.0,
            "resistance": 165.0,
            "primary_action": "NEW_TRADE",
            "new_trade": {
                "strategy": "SWING",
                "qty": 10,
                "side": "buy",
                "type": "limit",
                "time_in_force": "day",
                "limit_price": 150.00,
                "stop_loss": {
                    "stop_price": 145.00
                }
            }
        }
        decision_json = json.dumps(decision)

        test_db.execute_query("""
            INSERT INTO analysis_decision (
                "Analysis_Id", "Ticker", "Decision", executed, "Approve"
            ) VALUES (%s, %s, %s::jsonb, %s, %s)
        """, ('TEST_CANCEL_ORIG', 'AAPL', decision_json, False, True))

        executor = OrderExecutor(test_mode=True, db=test_db, alpaca_client=mock_alpaca_client)
        executor.run()

        # Get the order ID and trade journal ID
        original_decision = test_db.execute_query(
            'SELECT * FROM analysis_decision WHERE "Analysis_Id" = %s',
            ('TEST_CANCEL_ORIG',)
        )[0]
        order_id = original_decision['existing_order_id']
        trade_journal_id = original_decision['existing_trade_journal_id']

        # Verify order exists
        assert order_id in mock_alpaca_client.orders
        assert mock_alpaca_client.orders[order_id].status == 'pending'

        # Now create a CANCEL decision with new structure
        cancel_decision = {
            "symbol": "AAPL",
            "analysis_date": "2025-01-15",
            "support": 140.0,
            "resistance": 165.0,
            "primary_action": "CANCEL"
        }
        cancel_json = json.dumps(cancel_decision)

        test_db.execute_query("""
            INSERT INTO analysis_decision (
                "Analysis_Id", "Ticker", "Decision", executed, "Approve",
                existing_order_id, existing_trade_journal_id
            ) VALUES (%s, %s, %s::jsonb, %s, %s, %s, %s)
        """, ('TEST_CANCEL', 'AAPL', cancel_json, False, True, order_id, trade_journal_id))

        # Run executor again
        executor.run()

        # Verify order was cancelled
        assert mock_alpaca_client.orders[order_id].status == 'cancelled'

        # Verify trade_journal was updated
        trade = test_db.get_by_id('trade_journal', trade_journal_id)
        assert trade['status'] == 'CANCELLED'
        assert trade['exit_reason'] == 'CANCELLED'

        # Verify order_execution was updated
        order_execution = test_db.execute_query(
            'SELECT * FROM order_execution WHERE alpaca_order_id = %s',
            (order_id,)
        )[0]
        assert order_execution['order_status'] == 'cancelled'

        # Verify decision was marked as executed
        cancel_dec = test_db.execute_query(
            'SELECT * FROM analysis_decision WHERE "Analysis_Id" = %s',
            ('TEST_CANCEL',)
        )[0]
        assert cancel_dec['executed'] is True

    def test_cancel_without_order_id(self, test_db, mock_alpaca_client):
        """Test CANCEL without existing order ID - no order_execution update should occur"""
        decision = {
            "symbol": "AAPL",
            "analysis_date": "2025-01-15",
            "support": 140.0,
            "resistance": 165.0,
            "primary_action": "CANCEL"
        }
        decision_json = json.dumps(decision)

        test_db.execute_query("""
            INSERT INTO analysis_decision (
                "Analysis_Id", "Ticker", "Decision", executed, "Approve"
            ) VALUES (%s, %s, %s::jsonb, %s, %s)
        """, ('TEST_CANCEL_NO_ID', 'AAPL', decision_json, False, True))

        executor = OrderExecutor(test_mode=True, db=test_db, alpaca_client=mock_alpaca_client)
        executor.run()

        # Verify decision was marked as executed (to prevent reprocessing)
        decision = test_db.execute_query(
            'SELECT * FROM analysis_decision WHERE "Analysis_Id" = %s',
            ('TEST_CANCEL_NO_ID',)
        )[0]
        assert decision['executed'] is True


class TestOrderExecutorAmend:
    """Test AMEND functionality"""

    def test_amend_order(self, test_db, mock_alpaca_client):
        """Test amending an existing order"""
        # First create an order with new structure
        decision = {
            "symbol": "AAPL",
            "analysis_date": "2025-01-15",
            "support": 140.0,
            "resistance": 165.0,
            "primary_action": "NEW_TRADE",
            "new_trade": {
                "strategy": "SWING",
                "qty": 10,
                "side": "buy",
                "type": "limit",
                "time_in_force": "day",
                "limit_price": 150.00,
                "stop_loss": {
                    "stop_price": 145.00
                }
            }
        }
        decision_json = json.dumps(decision)

        test_db.execute_query("""
            INSERT INTO analysis_decision (
                "Analysis_Id", "Ticker", "Decision", executed, "Approve"
            ) VALUES (%s, %s, %s::jsonb, %s, %s)
        """, ('TEST_AMEND_ORIG', 'AAPL', decision_json, False, True))

        executor = OrderExecutor(test_mode=True, db=test_db, alpaca_client=mock_alpaca_client)
        executor.run()

        # Get original order ID
        original_decision = test_db.execute_query(
            'SELECT * FROM analysis_decision WHERE "Analysis_Id" = %s',
            ('TEST_AMEND_ORIG',)
        )[0]
        original_order_id = original_decision['existing_order_id']
        original_trade_id = original_decision['existing_trade_journal_id']

        # Create AMEND decision with new price and quantity
        amend_decision = {
            "symbol": "AAPL",
            "analysis_date": "2025-01-15",
            "support": 145.0,
            "resistance": 170.0,
            "primary_action": "AMEND",
            "new_trade": {
                "strategy": "SWING",
                "qty": 15,  # Changed quantity
                "side": "buy",
                "type": "limit",
                "time_in_force": "day",
                "limit_price": 155.00,  # Changed price
                "stop_loss": {
                    "stop_price": 150.00
                }
            }
        }
        amend_json = json.dumps(amend_decision)

        test_db.execute_query("""
            INSERT INTO analysis_decision (
                "Analysis_Id", "Ticker", "Decision", executed, "Approve",
                existing_order_id, existing_trade_journal_id
            ) VALUES (%s, %s, %s::jsonb, %s, %s, %s, %s)
        """, ('TEST_AMEND', 'AAPL', amend_json, False, True, original_order_id, original_trade_id))

        # Run executor again
        executor.run()

        # Verify original order was cancelled
        assert mock_alpaca_client.orders[original_order_id].status == 'cancelled'

        # Verify new order was created
        assert len(mock_alpaca_client.orders) == 2
        new_orders = [o for o in mock_alpaca_client.orders.values() if o.id != original_order_id]
        assert len(new_orders) == 1
        new_order = new_orders[0]
        assert float(new_order.qty) == 15.0
        assert new_order.limit_price == 155.00

        # Verify AMEND decision was marked as executed
        amend_dec = test_db.execute_query(
            'SELECT * FROM analysis_decision WHERE "Analysis_Id" = %s',
            ('TEST_AMEND',)
        )[0]
        assert amend_dec['executed'] is True

        # Verify new trade_journal entry was created
        trades = test_db.query('trade_journal', 'symbol = %s', ('AAPL',))
        assert len(trades) == 2  # Original (cancelled) + new


class TestOrderExecutorErrorHandling:
    """Test error handling"""

    def test_invalid_primary_action(self, test_db, mock_alpaca_client):
        """Test handling of invalid primary_action"""
        decision = {
            "symbol": "AAPL",
            "analysis_date": "2025-01-15",
            "support": 140.0,
            "resistance": 165.0,
            "primary_action": "INVALID_ACTION",
            "new_trade": {
                "strategy": "SWING",
                "qty": 10,
                "side": "buy",
                "type": "limit",
                "time_in_force": "day",
                "limit_price": 150.00,
                "stop_loss": {
                    "stop_price": 145.00
                }
            }
        }
        decision_json = json.dumps(decision)

        test_db.execute_query("""
            INSERT INTO analysis_decision (
                "Analysis_Id", "Ticker", "Decision", executed, "Approve"
            ) VALUES (%s, %s, %s::jsonb, %s, %s)
        """, ('TEST_INVALID', 'AAPL', decision_json, False, True))

        executor = OrderExecutor(test_mode=True, db=test_db, alpaca_client=mock_alpaca_client)
        executor.run()

        # Should not crash - verify decision was NOT marked as executed
        decision = test_db.execute_query(
            'SELECT * FROM analysis_decision WHERE "Analysis_Id" = %s',
            ('TEST_INVALID',)
        )[0]
        assert decision['executed'] is False

    def test_unapproved_decision_not_executed(self, test_db, mock_alpaca_client):
        """Test that unapproved decisions (Approve=false) are not executed"""
        decision = {
            "symbol": "AAPL",
            "analysis_date": "2025-01-15",
            "support": 140.0,
            "resistance": 165.0,
            "primary_action": "NEW_TRADE",
            "new_trade": {
                "strategy": "SWING",
                "qty": 10,
                "side": "buy",
                "type": "limit",
                "time_in_force": "day",
                "limit_price": 150.00,
                "stop_loss": {
                    "stop_price": 145.00
                }
            }
        }
        decision_json = json.dumps(decision)

        # Insert decision with Approve = false
        test_db.execute_query("""
            INSERT INTO analysis_decision (
                "Analysis_Id", "Ticker", "Decision", executed, "Approve"
            ) VALUES (%s, %s, %s::jsonb, %s, %s)
        """, ('TEST_UNAPPROVED', 'AAPL', decision_json, False, False))

        executor = OrderExecutor(test_mode=True, db=test_db, alpaca_client=mock_alpaca_client)
        executor.run()

        # Verify no orders were placed
        assert len(mock_alpaca_client.orders) == 0

        # Verify decision was NOT marked as executed
        decision = test_db.execute_query(
            'SELECT * FROM analysis_decision WHERE "Analysis_Id" = %s',
            ('TEST_UNAPPROVED',)
        )[0]
        assert decision['executed'] is False
