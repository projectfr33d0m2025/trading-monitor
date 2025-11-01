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
                "Analysis Id", "Ticker", "Decision", executed, "Approve"
            ) VALUES (%s, %s, %s::jsonb, %s, %s)
        """, (
            sample_analysis_decision['Analysis Id'],
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
            'SELECT * FROM analysis_decision WHERE "Analysis Id" = %s',
            ('TEST_001',)
        )[0]
        assert decision['executed'] is True
        assert decision['existing_order_id'] == order.id

    def test_new_trade_sell_order(self, test_db, mock_alpaca_client):
        """Test NEW_TRADE with SELL action"""
        # Insert SELL decision
        decision = {
            "action": "SELL",
            "primary_action": "NEW_TRADE",
            "qty": 5,
            "entry_price": 200.00,
            "stop_loss": 205.00,
            "trade_style": "DAYTRADE"
        }
        decision_json = json.dumps(decision)

        test_db.execute_query("""
            INSERT INTO analysis_decision (
                "Analysis Id", "Ticker", "Decision", executed, "Approve"
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
        # Insert decision without qty
        decision = {
            "action": "BUY",
            "primary_action": "NEW_TRADE",
            "entry_price": 150.00,
            "stop_loss": 145.00
        }
        decision_json = json.dumps(decision)

        test_db.execute_query("""
            INSERT INTO analysis_decision (
                "Analysis Id", "Ticker", "Decision", executed, "Approve"
            ) VALUES (%s, %s, %s::jsonb, %s, %s)
        """, ('TEST_MISSING', 'AAPL', decision_json, False, True))

        # Create and run executor
        executor = OrderExecutor(test_mode=True, db=test_db, alpaca_client=mock_alpaca_client)
        executor.run()

        # Verify no order was placed
        assert len(mock_alpaca_client.orders) == 0

        # Verify decision was NOT marked as executed
        decision = test_db.execute_query(
            'SELECT * FROM analysis_decision WHERE "Analysis Id" = %s',
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
        # Insert multiple decisions
        decisions = [
            ('TEST_001', 'AAPL', {"action": "BUY", "primary_action": "NEW_TRADE", "qty": 10, "entry_price": 150.00, "stop_loss": 145.00}),
            ('TEST_002', 'MSFT', {"action": "BUY", "primary_action": "NEW_TRADE", "qty": 5, "entry_price": 300.00, "stop_loss": 290.00}),
            ('TEST_003', 'GOOGL', {"action": "BUY", "primary_action": "NEW_TRADE", "qty": 3, "entry_price": 140.00, "stop_loss": 135.00})
        ]

        for analysis_id, ticker, decision in decisions:
            decision_json = json.dumps(decision)
            test_db.execute_query("""
                INSERT INTO analysis_decision (
                    "Analysis Id", "Ticker", "Decision", executed, "Approve"
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
        """Test NEW_TRADE with take_profit specified"""
        decision = {
            "action": "BUY",
            "primary_action": "NEW_TRADE",
            "qty": 10,
            "entry_price": 150.00,
            "stop_loss": 145.00,
            "take_profit": 160.00,
            "trade_style": "SWING"
        }
        decision_json = json.dumps(decision)

        test_db.execute_query("""
            INSERT INTO analysis_decision (
                "Analysis Id", "Ticker", "Decision", executed, "Approve"
            ) VALUES (%s, %s, %s::jsonb, %s, %s)
        """, ('TEST_TP', 'AAPL', decision_json, False, True))

        executor = OrderExecutor(test_mode=True, db=test_db, alpaca_client=mock_alpaca_client)
        executor.run()

        # Verify trade_journal has take_profit
        trades = test_db.query('trade_journal', 'symbol = %s', ('AAPL',))
        assert len(trades) == 1
        assert float(trades[0]['planned_take_profit']) == 160.00

    def test_new_trade_daytrade_style(self, test_db, mock_alpaca_client):
        """Test NEW_TRADE with DAYTRADE style (no take_profit)"""
        decision = {
            "action": "BUY",
            "primary_action": "NEW_TRADE",
            "qty": 10,
            "entry_price": 150.00,
            "stop_loss": 145.00,
            "trade_style": "DAYTRADE"
        }
        decision_json = json.dumps(decision)

        test_db.execute_query("""
            INSERT INTO analysis_decision (
                "Analysis Id", "Ticker", "Decision", executed, "Approve"
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
        # First create an order
        decision = {
            "action": "BUY",
            "primary_action": "NEW_TRADE",
            "qty": 10,
            "entry_price": 150.00,
            "stop_loss": 145.00
        }
        decision_json = json.dumps(decision)

        test_db.execute_query("""
            INSERT INTO analysis_decision (
                "Analysis Id", "Ticker", "Decision", executed, "Approve"
            ) VALUES (%s, %s, %s::jsonb, %s, %s)
        """, ('TEST_CANCEL_ORIG', 'AAPL', decision_json, False, True))

        executor = OrderExecutor(test_mode=True, db=test_db, alpaca_client=mock_alpaca_client)
        executor.run()

        # Get the order ID and trade journal ID
        original_decision = test_db.execute_query(
            'SELECT * FROM analysis_decision WHERE "Analysis Id" = %s',
            ('TEST_CANCEL_ORIG',)
        )[0]
        order_id = original_decision['existing_order_id']
        trade_journal_id = original_decision['existing_trade_journal_id']

        # Verify order exists
        assert order_id in mock_alpaca_client.orders
        assert mock_alpaca_client.orders[order_id].status == 'pending'

        # Now create a CANCEL decision
        cancel_decision = {
            "action": "BUY",
            "primary_action": "CANCEL"
        }
        cancel_json = json.dumps(cancel_decision)

        test_db.execute_query("""
            INSERT INTO analysis_decision (
                "Analysis Id", "Ticker", "Decision", executed, "Approve",
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

        # Verify decision was marked as executed
        cancel_dec = test_db.execute_query(
            'SELECT * FROM analysis_decision WHERE "Analysis Id" = %s',
            ('TEST_CANCEL',)
        )[0]
        assert cancel_dec['executed'] is True

    def test_cancel_without_order_id(self, test_db, mock_alpaca_client):
        """Test CANCEL without existing order ID"""
        decision = {
            "action": "BUY",
            "primary_action": "CANCEL"
        }
        decision_json = json.dumps(decision)

        test_db.execute_query("""
            INSERT INTO analysis_decision (
                "Analysis Id", "Ticker", "Decision", executed, "Approve"
            ) VALUES (%s, %s, %s::jsonb, %s, %s)
        """, ('TEST_CANCEL_NO_ID', 'AAPL', decision_json, False, True))

        executor = OrderExecutor(test_mode=True, db=test_db, alpaca_client=mock_alpaca_client)
        executor.run()

        # Verify decision was marked as executed (to prevent reprocessing)
        decision = test_db.execute_query(
            'SELECT * FROM analysis_decision WHERE "Analysis Id" = %s',
            ('TEST_CANCEL_NO_ID',)
        )[0]
        assert decision['executed'] is True


class TestOrderExecutorAmend:
    """Test AMEND functionality"""

    def test_amend_order(self, test_db, mock_alpaca_client):
        """Test amending an existing order"""
        # First create an order
        decision = {
            "action": "BUY",
            "primary_action": "NEW_TRADE",
            "qty": 10,
            "entry_price": 150.00,
            "stop_loss": 145.00
        }
        decision_json = json.dumps(decision)

        test_db.execute_query("""
            INSERT INTO analysis_decision (
                "Analysis Id", "Ticker", "Decision", executed, "Approve"
            ) VALUES (%s, %s, %s::jsonb, %s, %s)
        """, ('TEST_AMEND_ORIG', 'AAPL', decision_json, False, True))

        executor = OrderExecutor(test_mode=True, db=test_db, alpaca_client=mock_alpaca_client)
        executor.run()

        # Get original order ID
        original_decision = test_db.execute_query(
            'SELECT * FROM analysis_decision WHERE "Analysis Id" = %s',
            ('TEST_AMEND_ORIG',)
        )[0]
        original_order_id = original_decision['existing_order_id']
        original_trade_id = original_decision['existing_trade_journal_id']

        # Create AMEND decision with new price
        amend_decision = {
            "action": "BUY",
            "primary_action": "AMEND",
            "qty": 15,  # Changed quantity
            "entry_price": 155.00,  # Changed price
            "stop_loss": 150.00
        }
        amend_json = json.dumps(amend_decision)

        test_db.execute_query("""
            INSERT INTO analysis_decision (
                "Analysis Id", "Ticker", "Decision", executed, "Approve",
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
            'SELECT * FROM analysis_decision WHERE "Analysis Id" = %s',
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
            "action": "BUY",
            "primary_action": "INVALID_ACTION",
            "qty": 10,
            "entry_price": 150.00,
            "stop_loss": 145.00
        }
        decision_json = json.dumps(decision)

        test_db.execute_query("""
            INSERT INTO analysis_decision (
                "Analysis Id", "Ticker", "Decision", executed, "Approve"
            ) VALUES (%s, %s, %s::jsonb, %s, %s)
        """, ('TEST_INVALID', 'AAPL', decision_json, False, True))

        executor = OrderExecutor(test_mode=True, db=test_db, alpaca_client=mock_alpaca_client)
        executor.run()

        # Should not crash - verify decision was NOT marked as executed
        decision = test_db.execute_query(
            'SELECT * FROM analysis_decision WHERE "Analysis Id" = %s',
            ('TEST_INVALID',)
        )[0]
        assert decision['executed'] is False
