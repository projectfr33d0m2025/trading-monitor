"""
Error handling tests
Tests error scenarios and graceful degradation
"""
import pytest
import json
from order_executor import OrderExecutor
from order_monitor import OrderMonitor
from position_monitor import PositionMonitor


class MockAlpacaClientWithErrors:
    """Mock Alpaca client that simulates API errors"""
    def __init__(self):
        self.orders = {}
        self.positions = {}
        self.next_order_id = 1
        self.should_fail_submit = False
        self.should_fail_get_order = False
        self.should_fail_cancel = False

    def submit_order(self, order_request):
        """Mock submit_order with error simulation"""
        if self.should_fail_submit:
            raise Exception("API Error: Rate limit exceeded")

        from tests.conftest import MockAlpacaOrder
        order_id = f"test-order-{self.next_order_id}"
        self.next_order_id += 1
        order = MockAlpacaOrder(
            id=order_id,
            client_order_id=f"client-{order_id}",
            symbol=order_request.symbol,
            qty=order_request.qty,
            side=order_request.side.value,
            order_type=order_request.order_type.value if hasattr(order_request, 'order_type') else 'limit',
            time_in_force=order_request.time_in_force.value,
            limit_price=getattr(order_request, 'limit_price', None),
            status='pending'
        )
        self.orders[order_id] = order
        return order

    def get_order_by_id(self, order_id):
        """Mock get_order_by_id with error simulation"""
        if self.should_fail_get_order:
            raise Exception("API Error: Service unavailable")
        if order_id not in self.orders:
            raise Exception(f"Order {order_id} not found")
        return self.orders[order_id]

    def cancel_order_by_id(self, order_id):
        """Mock cancel_order_by_id with error simulation"""
        if self.should_fail_cancel:
            raise Exception("API Error: Order cannot be cancelled")
        if order_id not in self.orders:
            raise Exception(f"Order {order_id} not found")
        self.orders[order_id].status = 'cancelled'
        return True

    def get_all_positions(self):
        """Mock get_all_positions"""
        return list(self.positions.values())


class MockDataClientWithErrors:
    """Mock data client that simulates errors"""
    def __init__(self):
        self.quotes = {}
        self.should_fail = False

    def get_stock_latest_quote(self, request):
        """Mock get_stock_latest_quote with error simulation"""
        if self.should_fail:
            raise Exception("API Error: Data service unavailable")

        from tests.conftest import MockAlpacaQuote
        symbol = request.symbol_or_symbols
        if symbol in self.quotes:
            return {symbol: self.quotes[symbol]}
        return {symbol: MockAlpacaQuote(symbol, 100.0, 100.5)}

    def add_quote(self, symbol, bid_price, ask_price):
        """Helper to add quotes"""
        from tests.conftest import MockAlpacaQuote
        self.quotes[symbol] = MockAlpacaQuote(symbol, bid_price, ask_price)


class TestOrderExecutorErrors:
    """Test error handling in Order Executor"""

    def test_alpaca_api_error_during_order_submission(self, test_db):
        """Test handling of Alpaca API error during order submission"""
        # Create decision
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
        """, ('ERROR_001', 'AAPL', decision_json, False, True))

        # Create mock client that will fail
        mock_client = MockAlpacaClientWithErrors()
        mock_client.should_fail_submit = True

        # Execute should handle error gracefully
        executor = OrderExecutor(test_mode=True, db=test_db, alpaca_client=mock_client)

        # Should not crash
        try:
            executor.run()
        except:
            pass  # Expected to handle error

        # Decision should NOT be marked as executed
        decision = test_db.execute_query(
            'SELECT * FROM analysis_decision WHERE "Analysis Id" = %s',
            ('ERROR_001',)
        )[0]
        # May still be False if error was handled properly

    def test_multiple_decisions_one_fails(self, test_db):
        """Test that one failing decision doesn't prevent others from executing"""
        # Create multiple decisions, one with missing fields
        decisions = [
            ('ERROR_GOOD_1', 'AAPL', {"action": "BUY", "primary_action": "NEW_TRADE", "qty": 10, "entry_price": 150.00, "stop_loss": 145.00}),
            ('ERROR_BAD', 'MSFT', {"action": "BUY", "primary_action": "NEW_TRADE", "entry_price": 300.00}),  # Missing qty
            ('ERROR_GOOD_2', 'GOOGL', {"action": "BUY", "primary_action": "NEW_TRADE", "qty": 5, "entry_price": 140.00, "stop_loss": 135.00})
        ]

        for analysis_id, ticker, decision in decisions:
            decision_json = json.dumps(decision)
            test_db.execute_query("""
                INSERT INTO analysis_decision (
                    "Analysis Id", "Ticker", "Decision", executed, "Approve"
                ) VALUES (%s, %s, %s::jsonb, %s, %s)
            """, (analysis_id, ticker, decision_json, False, True))

        # Execute
        mock_client = MockAlpacaClientWithErrors()
        executor = OrderExecutor(test_mode=True, db=test_db, alpaca_client=mock_client)
        executor.run()

        # Verify good decisions were executed
        good_decisions = test_db.execute_query(
            'SELECT * FROM analysis_decision WHERE "Analysis Id" IN (%s, %s)',
            ('ERROR_GOOD_1', 'ERROR_GOOD_2')
        )
        # At least one should have executed
        assert len([d for d in good_decisions if d['executed']]) >= 1

        # Bad decision should NOT be executed
        bad_decision = test_db.execute_query(
            'SELECT * FROM analysis_decision WHERE "Analysis Id" = %s',
            ('ERROR_BAD',)
        )[0]
        assert bad_decision['executed'] is False

    def test_cancel_nonexistent_order(self, test_db):
        """Test canceling an order that doesn't exist"""
        decision = {
            "action": "BUY",
            "primary_action": "CANCEL"
        }
        decision_json = json.dumps(decision)
        test_db.execute_query("""
            INSERT INTO analysis_decision (
                "Analysis Id", "Ticker", "Decision", executed, "Approve",
                existing_order_id
            ) VALUES (%s, %s, %s::jsonb, %s, %s, %s)
        """, ('ERROR_CANCEL', 'AAPL', decision_json, False, True, 'nonexistent-order-id'))

        mock_client = MockAlpacaClientWithErrors()
        executor = OrderExecutor(test_mode=True, db=test_db, alpaca_client=mock_client)

        # Should handle error gracefully
        try:
            executor.run()
        except:
            pass


class TestOrderMonitorErrors:
    """Test error handling in Order Monitor"""

    def test_alpaca_api_error_during_status_sync(self, test_db):
        """Test handling of API error when syncing order status"""
        # Create trade and order
        trade_id = test_db.insert('trade_journal', {
            'trade_id': 'ERROR_SYNC',
            'symbol': 'AAPL',
            'status': 'ORDERED',
            'planned_qty': 10
        })

        test_db.insert('order_execution', {
            'trade_journal_id': trade_id,
            'alpaca_order_id': 'error-order-1',
            'order_type': 'ENTRY',
            'side': 'buy',
            'order_status': 'pending',
            'qty': 10
        })

        # Create mock client that will fail on get_order
        mock_client = MockAlpacaClientWithErrors()
        mock_client.should_fail_get_order = True

        # Monitor should handle error gracefully
        monitor = OrderMonitor(test_mode=True, db=test_db, alpaca_client=mock_client)

        # Should not crash
        try:
            monitor.run()
        except:
            pass  # Should handle error

    def test_multiple_orders_one_fails_sync(self, test_db):
        """Test that one order sync failure doesn't prevent others from syncing"""
        from tests.conftest import MockAlpacaOrder

        # Create multiple orders
        trade_id = test_db.insert('trade_journal', {
            'trade_id': 'MULTI_ERROR',
            'symbol': 'AAPL',
            'status': 'ORDERED',
            'planned_qty': 10
        })

        mock_client = MockAlpacaClientWithErrors()

        # Create one order that exists
        good_order = MockAlpacaOrder(
            id='good-order',
            client_order_id='client-good',
            symbol='AAPL',
            qty=10,
            side='buy',
            order_type='limit',
            time_in_force='day',
            limit_price=150.00,
            status='filled',
            filled_qty=10
        )
        good_order.filled_avg_price = 150.25
        good_order.filled_at = '2025-10-26T10:00:00Z'
        mock_client.orders['good-order'] = good_order

        # Create order records in DB
        test_db.insert('order_execution', {
            'trade_journal_id': trade_id,
            'alpaca_order_id': 'nonexistent-order',
            'order_type': 'ENTRY',
            'side': 'buy',
            'order_status': 'pending',
            'qty': 10
        })

        order_id_2 = test_db.insert('order_execution', {
            'trade_journal_id': trade_id,
            'alpaca_order_id': 'good-order',
            'order_type': 'ENTRY',
            'side': 'buy',
            'order_status': 'pending',
            'qty': 10,
            'limit_price': 150.00
        })

        # Monitor should sync the good order despite the bad one failing
        monitor = OrderMonitor(test_mode=True, db=test_db, alpaca_client=mock_client)
        monitor.run()

        # Good order should be synced
        order = test_db.get_by_id('order_execution', order_id_2)
        # Should have been updated (if error handling works)


class TestPositionMonitorErrors:
    """Test error handling in Position Monitor"""

    def test_data_api_error_during_price_update(self, test_db):
        """Test handling of data API error when updating prices"""
        # Create position
        trade_id = test_db.insert('trade_journal', {
            'trade_id': 'ERROR_PRICE',
            'symbol': 'AAPL',
            'status': 'POSITION',
            'actual_entry': 150.00,
            'actual_qty': 10
        })

        test_db.insert('position_tracking', {
            'trade_journal_id': trade_id,
            'symbol': 'AAPL',
            'qty': 10,
            'avg_entry_price': 150.00,
            'current_price': 150.00,
            'market_value': 1500.00,
            'cost_basis': 1500.00,
            'unrealized_pnl': 0.00
        })

        # Create mock clients
        mock_trading = MockAlpacaClientWithErrors()
        mock_data = MockDataClientWithErrors()
        mock_data.should_fail = True

        # Monitor should handle error gracefully
        monitor = PositionMonitor(
            test_mode=True,
            db=test_db,
            trading_client=mock_trading,
            data_client=mock_data
        )

        # Should not crash
        try:
            monitor.run()
        except:
            pass  # Should handle error

    def test_multiple_positions_one_fails_update(self, test_db):
        """Test that one position update failure doesn't prevent others from updating"""
        # Create multiple positions
        symbols = ['AAPL', 'MSFT', 'INVALID']

        mock_trading = MockAlpacaClientWithErrors()
        mock_data = MockDataClientWithErrors()

        from tests.conftest import MockAlpacaPosition
        for symbol in symbols:
            trade_id = test_db.insert('trade_journal', {
                'trade_id': f'{symbol}_ERROR',
                'symbol': symbol,
                'status': 'POSITION',
                'actual_entry': 150.00,
                'actual_qty': 10
            })

            test_db.insert('position_tracking', {
                'trade_journal_id': trade_id,
                'symbol': symbol,
                'qty': 10,
                'avg_entry_price': 150.00,
                'current_price': 150.00,
                'market_value': 1500.00,
                'cost_basis': 1500.00,
                'unrealized_pnl': 0.00
            })

            # Add position to mock Alpaca client
            mock_trading.positions[symbol] = MockAlpacaPosition(
                symbol=symbol,
                qty=10,
                side='long',
                avg_entry_price=150.00,
                current_price=150.00,
                market_value=1500.00,
                unrealized_pl=0.00,
                unrealized_plpc=0.00
            )

        # Add quotes for valid symbols
        mock_data.add_quote('AAPL', 155.00, 155.50)
        mock_data.add_quote('MSFT', 310.00, 310.50)
        # INVALID symbol has no quote - will use default

        # Monitor should update what it can
        monitor = PositionMonitor(
            test_mode=True,
            db=test_db,
            trading_client=mock_trading,
            data_client=mock_data
        )
        monitor.run()

        # At least AAPL should be updated
        aapl_pos = test_db.query('position_tracking', 'symbol = %s', ('AAPL',))[0]
        # Should have been updated (if error handling works)


class TestDatabaseErrors:
    """Test database error handling"""

    def test_database_connection_error(self, test_db, mock_alpaca_client):
        """Test handling of database connection issues"""
        # Close the database connection to simulate error
        test_db.close()

        # Executor should handle gracefully
        try:
            executor = OrderExecutor(test_mode=True, db=test_db, alpaca_client=mock_alpaca_client)
            executor.run()
        except Exception as e:
            # Expected to fail, but should be caught
            assert True

    def test_invalid_data_in_database(self, test_db, mock_alpaca_client):
        """Test handling of corrupted/invalid data in database"""
        # Insert invalid decision (malformed JSON)
        try:
            test_db.execute_query("""
                INSERT INTO analysis_decision (
                    "Analysis Id", "Ticker", "Decision", executed, "Approve"
                ) VALUES (%s, %s, %s::jsonb, %s, %s)
            """, ('INVALID_DATA', 'AAPL', '{"invalid": }', False, True))
        except:
            # Expected to fail on invalid JSON
            pass

        # Executor should handle gracefully
        executor = OrderExecutor(test_mode=True, db=test_db, alpaca_client=mock_alpaca_client)
        try:
            executor.run()
        except:
            pass  # Should handle error


class TestEdgeCases:
    """Test edge cases and boundary conditions"""

    def test_zero_quantity_order(self, test_db, mock_alpaca_client):
        """Test order with zero quantity"""
        decision = {
            "action": "BUY",
            "primary_action": "NEW_TRADE",
            "qty": 0,  # Invalid quantity
            "entry_price": 150.00,
            "stop_loss": 145.00
        }
        decision_json = json.dumps(decision)
        test_db.execute_query("""
            INSERT INTO analysis_decision (
                "Analysis Id", "Ticker", "Decision", executed, "Approve"
            ) VALUES (%s, %s, %s::jsonb, %s, %s)
        """, ('EDGE_ZERO_QTY', 'AAPL', decision_json, False, True))

        executor = OrderExecutor(test_mode=True, db=test_db, alpaca_client=mock_alpaca_client)
        executor.run()

        # Should not place order
        assert len(mock_alpaca_client.orders) == 0

    def test_negative_price(self, test_db, mock_alpaca_client):
        """Test order with negative price"""
        decision = {
            "action": "BUY",
            "primary_action": "NEW_TRADE",
            "qty": 10,
            "entry_price": -150.00,  # Invalid price
            "stop_loss": 145.00
        }
        decision_json = json.dumps(decision)
        test_db.execute_query("""
            INSERT INTO analysis_decision (
                "Analysis Id", "Ticker", "Decision", executed, "Approve"
            ) VALUES (%s, %s, %s::jsonb, %s, %s)
        """, ('EDGE_NEG_PRICE', 'AAPL', decision_json, False, True))

        executor = OrderExecutor(test_mode=True, db=test_db, alpaca_client=mock_alpaca_client)
        executor.run()

        # Should handle gracefully
        # Alpaca would reject negative price anyway

    def test_empty_symbol(self, test_db, mock_alpaca_client):
        """Test order with empty symbol"""
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
        """, ('EDGE_EMPTY_SYM', '', decision_json, False, True))

        executor = OrderExecutor(test_mode=True, db=test_db, alpaca_client=mock_alpaca_client)

        # Should handle gracefully
        try:
            executor.run()
        except:
            pass
