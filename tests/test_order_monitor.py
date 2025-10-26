"""
Unit tests for Order Monitor
Tests order status sync, entry fill handling, and exit fill handling
"""
import pytest
import json
from order_monitor import OrderMonitor
from tests.conftest import MockAlpacaOrder


class TestOrderMonitorStatusSync:
    """Test order status synchronization"""

    def test_sync_pending_order(self, test_db, mock_alpaca_client):
        """Test syncing a pending order status"""
        # Create a trade and order
        trade_id = test_db.insert('trade_journal', {
            'trade_id': 'TEST_SYNC',
            'symbol': 'AAPL',
            'status': 'ORDERED',
            'planned_entry': 150.00,
            'planned_qty': 10
        })

        # Create order in mock client
        order_in_alpaca = MockAlpacaOrder(
            id='test-order-1',
            client_order_id='client-1',
            symbol='AAPL',
            qty=10,
            side='buy',
            order_type='limit',
            time_in_force='day',
            limit_price=150.00,
            status='pending'
        )
        mock_alpaca_client.orders['test-order-1'] = order_in_alpaca

        # Create order in database
        order_id = test_db.insert('order_execution', {
            'trade_journal_id': trade_id,
            'alpaca_order_id': 'test-order-1',
            'order_type': 'ENTRY',
            'side': 'buy',
            'order_status': 'new',  # Old status
            'qty': 10,
            'limit_price': 150.00
        })

        # Run monitor
        monitor = OrderMonitor(test_mode=True, db=test_db, alpaca_client=mock_alpaca_client)
        monitor.run()

        # Verify order status was updated
        updated_order = test_db.get_by_id('order_execution', order_id)
        assert updated_order['order_status'] == 'pending'

    def test_sync_filled_order(self, test_db, mock_alpaca_client):
        """Test syncing a filled order status"""
        # Create trade
        trade_id = test_db.insert('trade_journal', {
            'trade_id': 'TEST_FILLED',
            'symbol': 'AAPL',
            'status': 'ORDERED',
            'planned_entry': 150.00,
            'planned_stop_loss': 145.00,
            'planned_qty': 10,
            'trade_style': 'DAYTRADE'
        })

        # Create filled order in mock client
        filled_order = MockAlpacaOrder(
            id='test-order-filled',
            client_order_id='client-filled',
            symbol='AAPL',
            qty=10,
            side='buy',
            order_type='limit',
            time_in_force='day',
            limit_price=150.00,
            filled_avg_price=150.25,
            status='filled',
            filled_qty=10
        )
        filled_order.filled_at = '2025-10-26T10:00:00Z'
        mock_alpaca_client.orders['test-order-filled'] = filled_order

        # Create order in database
        order_id = test_db.insert('order_execution', {
            'trade_journal_id': trade_id,
            'alpaca_order_id': 'test-order-filled',
            'order_type': 'ENTRY',
            'side': 'buy',
            'order_status': 'pending',
            'qty': 10,
            'limit_price': 150.00
        })

        # Run monitor
        monitor = OrderMonitor(test_mode=True, db=test_db, alpaca_client=mock_alpaca_client)
        monitor.run()

        # Verify order status was updated
        updated_order = test_db.get_by_id('order_execution', order_id)
        assert updated_order['order_status'] == 'filled'
        assert updated_order['filled_qty'] == 10
        assert float(updated_order['filled_avg_price']) == 150.25

    def test_sync_cancelled_order(self, test_db, mock_alpaca_client):
        """Test syncing a cancelled order"""
        # Create trade
        trade_id = test_db.insert('trade_journal', {
            'trade_id': 'TEST_CANCELLED',
            'symbol': 'AAPL',
            'status': 'ORDERED',
            'planned_entry': 150.00,
            'planned_qty': 10
        })

        # Create cancelled order
        cancelled_order = MockAlpacaOrder(
            id='test-order-cancelled',
            client_order_id='client-cancelled',
            symbol='AAPL',
            qty=10,
            side='buy',
            order_type='limit',
            time_in_force='day',
            limit_price=150.00,
            status='canceled'
        )
        mock_alpaca_client.orders['test-order-cancelled'] = cancelled_order

        # Create order in database
        order_id = test_db.insert('order_execution', {
            'trade_journal_id': trade_id,
            'alpaca_order_id': 'test-order-cancelled',
            'order_type': 'ENTRY',
            'side': 'buy',
            'order_status': 'pending',
            'qty': 10,
            'limit_price': 150.00
        })

        # Run monitor
        monitor = OrderMonitor(test_mode=True, db=test_db, alpaca_client=mock_alpaca_client)
        monitor.run()

        # Verify status was updated
        updated_order = test_db.get_by_id('order_execution', order_id)
        assert updated_order['order_status'] == 'cancelled'

    def test_no_orders_to_monitor(self, test_db, mock_alpaca_client):
        """Test monitor with no active orders"""
        monitor = OrderMonitor(test_mode=True, db=test_db, alpaca_client=mock_alpaca_client)
        monitor.run()
        # Should complete without errors


class TestOrderMonitorEntryFill:
    """Test entry order fill handling"""

    def test_entry_fill_creates_position(self, test_db, mock_alpaca_client):
        """Test that filled entry order creates position"""
        # Create trade
        trade_id = test_db.insert('trade_journal', {
            'trade_id': 'TEST_ENTRY',
            'symbol': 'AAPL',
            'status': 'ORDERED',
            'planned_entry': 150.00,
            'planned_stop_loss': 145.00,
            'planned_take_profit': 160.00,
            'planned_qty': 10,
            'trade_style': 'SWING'
        })

        # Create filled order in Alpaca
        filled_order = MockAlpacaOrder(
            id='entry-order-1',
            client_order_id='client-entry-1',
            symbol='AAPL',
            qty=10,
            side='buy',
            order_type='limit',
            time_in_force='day',
            limit_price=150.00,
            filled_avg_price=150.25,
            status='filled',
            filled_qty=10
        )
        filled_order.filled_at = '2025-10-26T10:00:00Z'
        mock_alpaca_client.orders['entry-order-1'] = filled_order

        # Create order in database
        order_id = test_db.insert('order_execution', {
            'trade_journal_id': trade_id,
            'alpaca_order_id': 'entry-order-1',
            'order_type': 'ENTRY',
            'side': 'buy',
            'order_status': 'pending',
            'qty': 10,
            'limit_price': 150.00
        })

        # Run monitor
        monitor = OrderMonitor(test_mode=True, db=test_db, alpaca_client=mock_alpaca_client)
        monitor.run()

        # Verify trade_journal was updated to POSITION
        trade = test_db.get_by_id('trade_journal', trade_id)
        assert trade['status'] == 'POSITION'
        assert float(trade['actual_entry']) == 150.25
        assert trade['actual_qty'] == 10

        # Verify position_tracking was created
        positions = test_db.query('position_tracking', 'symbol = %s', ('AAPL',))
        assert len(positions) == 1
        position = positions[0]
        assert position['symbol'] == 'AAPL'
        assert position['qty'] == 10
        assert float(position['avg_entry_price']) == 150.25
        assert float(position['cost_basis']) == 150.25 * 10
        assert float(position['unrealized_pnl']) == 0.0

    def test_entry_fill_places_stop_loss(self, test_db, mock_alpaca_client):
        """Test that entry fill places stop-loss order"""
        # Create trade
        trade_id = test_db.insert('trade_journal', {
            'trade_id': 'TEST_SL',
            'symbol': 'AAPL',
            'status': 'ORDERED',
            'planned_entry': 150.00,
            'planned_stop_loss': 145.00,
            'planned_qty': 10,
            'trade_style': 'DAYTRADE'
        })

        # Create filled entry order
        filled_order = MockAlpacaOrder(
            id='entry-order-sl',
            client_order_id='client-entry-sl',
            symbol='AAPL',
            qty=10,
            side='buy',
            order_type='limit',
            time_in_force='day',
            limit_price=150.00,
            filled_avg_price=150.25,
            status='filled',
            filled_qty=10
        )
        filled_order.filled_at = '2025-10-26T10:00:00Z'
        mock_alpaca_client.orders['entry-order-sl'] = filled_order

        # Create order in database
        test_db.insert('order_execution', {
            'trade_journal_id': trade_id,
            'alpaca_order_id': 'entry-order-sl',
            'order_type': 'ENTRY',
            'side': 'buy',
            'order_status': 'pending',
            'qty': 10,
            'limit_price': 150.00
        })

        # Run monitor
        monitor = OrderMonitor(test_mode=True, db=test_db, alpaca_client=mock_alpaca_client)
        monitor.run()

        # Verify stop-loss order was placed
        sl_orders = test_db.query('order_execution', 'order_type = %s', ('STOP_LOSS',))
        assert len(sl_orders) == 1
        sl_order = sl_orders[0]
        assert sl_order['side'] == 'sell'
        assert float(sl_order['stop_price']) == 145.00
        assert sl_order['qty'] == 10

        # Verify order exists in mock client
        assert len(mock_alpaca_client.orders) == 2  # Entry + SL

    def test_entry_fill_places_take_profit_for_swing(self, test_db, mock_alpaca_client):
        """Test that SWING entry fill places take-profit order"""
        # Create SWING trade
        trade_id = test_db.insert('trade_journal', {
            'trade_id': 'TEST_TP',
            'symbol': 'AAPL',
            'status': 'ORDERED',
            'planned_entry': 150.00,
            'planned_stop_loss': 145.00,
            'planned_take_profit': 160.00,
            'planned_qty': 10,
            'trade_style': 'SWING'
        })

        # Create filled entry order
        filled_order = MockAlpacaOrder(
            id='entry-order-tp',
            client_order_id='client-entry-tp',
            symbol='AAPL',
            qty=10,
            side='buy',
            order_type='limit',
            time_in_force='day',
            limit_price=150.00,
            filled_avg_price=150.25,
            status='filled',
            filled_qty=10
        )
        filled_order.filled_at = '2025-10-26T10:00:00Z'
        mock_alpaca_client.orders['entry-order-tp'] = filled_order

        # Create order in database
        test_db.insert('order_execution', {
            'trade_journal_id': trade_id,
            'alpaca_order_id': 'entry-order-tp',
            'order_type': 'ENTRY',
            'side': 'buy',
            'order_status': 'pending',
            'qty': 10,
            'limit_price': 150.00
        })

        # Run monitor
        monitor = OrderMonitor(test_mode=True, db=test_db, alpaca_client=mock_alpaca_client)
        monitor.run()

        # Verify take-profit order was placed
        tp_orders = test_db.query('order_execution', 'order_type = %s', ('TAKE_PROFIT',))
        assert len(tp_orders) == 1
        tp_order = tp_orders[0]
        assert tp_order['side'] == 'sell'
        assert float(tp_order['limit_price']) == 160.00
        assert tp_order['qty'] == 10

        # Verify both SL and TP were placed
        assert len(mock_alpaca_client.orders) == 3  # Entry + SL + TP

    def test_entry_fill_no_take_profit_for_daytrade(self, test_db, mock_alpaca_client):
        """Test that DAYTRADE entry fill does NOT place take-profit"""
        # Create DAYTRADE trade
        trade_id = test_db.insert('trade_journal', {
            'trade_id': 'TEST_DT',
            'symbol': 'AAPL',
            'status': 'ORDERED',
            'planned_entry': 150.00,
            'planned_stop_loss': 145.00,
            'planned_qty': 10,
            'trade_style': 'DAYTRADE'
        })

        # Create filled entry order
        filled_order = MockAlpacaOrder(
            id='entry-order-dt',
            client_order_id='client-entry-dt',
            symbol='AAPL',
            qty=10,
            side='buy',
            order_type='limit',
            time_in_force='day',
            limit_price=150.00,
            filled_avg_price=150.25,
            status='filled',
            filled_qty=10
        )
        filled_order.filled_at = '2025-10-26T10:00:00Z'
        mock_alpaca_client.orders['entry-order-dt'] = filled_order

        # Create order in database
        test_db.insert('order_execution', {
            'trade_journal_id': trade_id,
            'alpaca_order_id': 'entry-order-dt',
            'order_type': 'ENTRY',
            'side': 'buy',
            'order_status': 'pending',
            'qty': 10,
            'limit_price': 150.00
        })

        # Run monitor
        monitor = OrderMonitor(test_mode=True, db=test_db, alpaca_client=mock_alpaca_client)
        monitor.run()

        # Verify NO take-profit order was placed
        tp_orders = test_db.query('order_execution', 'order_type = %s', ('TAKE_PROFIT',))
        assert len(tp_orders) == 0

        # Verify only SL was placed
        assert len(mock_alpaca_client.orders) == 2  # Entry + SL only


class TestOrderMonitorExitFill:
    """Test exit order fill handling"""

    def test_stop_loss_filled_closes_trade(self, test_db, mock_alpaca_client):
        """Test that filled stop-loss order closes the trade"""
        # Create trade with position
        trade_id = test_db.insert('trade_journal', {
            'trade_id': 'TEST_SL_FILL',
            'symbol': 'AAPL',
            'status': 'POSITION',
            'planned_entry': 150.00,
            'planned_stop_loss': 145.00,
            'actual_entry': 150.25,
            'actual_qty': 10,
            'trade_style': 'DAYTRADE'
        })

        # Create position
        test_db.insert('position_tracking', {
            'trade_journal_id': trade_id,
            'symbol': 'AAPL',
            'qty': 10,
            'avg_entry_price': 150.25,
            'current_price': 147.00,
            'market_value': 1470.00,
            'cost_basis': 1502.50,
            'unrealized_pnl': -32.50
        })

        # Create filled SL order in Alpaca
        sl_filled_order = MockAlpacaOrder(
            id='sl-order-filled',
            client_order_id='client-sl-filled',
            symbol='AAPL',
            qty=10,
            side='sell',
            order_type='stop',
            time_in_force='gtc',
            stop_price=145.00,
            filled_avg_price=144.90,
            status='filled',
            filled_qty=10
        )
        sl_filled_order.filled_at = '2025-10-26T14:00:00Z'
        mock_alpaca_client.orders['sl-order-filled'] = sl_filled_order

        # Create SL order in database
        test_db.insert('order_execution', {
            'trade_journal_id': trade_id,
            'alpaca_order_id': 'sl-order-filled',
            'order_type': 'STOP_LOSS',
            'side': 'sell',
            'order_status': 'pending',
            'qty': 10,
            'stop_price': 145.00
        })

        # Run monitor
        monitor = OrderMonitor(test_mode=True, db=test_db, alpaca_client=mock_alpaca_client)
        monitor.run()

        # Verify trade was closed
        trade = test_db.get_by_id('trade_journal', trade_id)
        assert trade['status'] == 'CLOSED'
        assert trade['exit_reason'] == 'STOPPED_OUT'
        assert float(trade['exit_price']) == 144.90

        # Calculate expected P&L: (144.90 - 150.25) * 10 = -53.50
        expected_pnl = (144.90 - 150.25) * 10
        assert abs(float(trade['actual_pnl']) - expected_pnl) < 0.01

        # Verify position was deleted
        positions = test_db.query('position_tracking', 'symbol = %s', ('AAPL',))
        assert len(positions) == 0

    def test_take_profit_filled_closes_trade(self, test_db, mock_alpaca_client):
        """Test that filled take-profit order closes the trade"""
        # Create trade with position
        trade_id = test_db.insert('trade_journal', {
            'trade_id': 'TEST_TP_FILL',
            'symbol': 'AAPL',
            'status': 'POSITION',
            'planned_entry': 150.00,
            'planned_stop_loss': 145.00,
            'planned_take_profit': 160.00,
            'actual_entry': 150.25,
            'actual_qty': 10,
            'trade_style': 'SWING'
        })

        # Create position
        test_db.insert('position_tracking', {
            'trade_journal_id': trade_id,
            'symbol': 'AAPL',
            'qty': 10,
            'avg_entry_price': 150.25,
            'current_price': 160.00,
            'market_value': 1600.00,
            'cost_basis': 1502.50,
            'unrealized_pnl': 97.50
        })

        # Create filled TP order
        tp_filled_order = MockAlpacaOrder(
            id='tp-order-filled',
            client_order_id='client-tp-filled',
            symbol='AAPL',
            qty=10,
            side='sell',
            order_type='limit',
            time_in_force='gtc',
            limit_price=160.00,
            filled_avg_price=160.10,
            status='filled',
            filled_qty=10
        )
        tp_filled_order.filled_at = '2025-10-26T14:00:00Z'
        mock_alpaca_client.orders['tp-order-filled'] = tp_filled_order

        # Create TP order in database
        test_db.insert('order_execution', {
            'trade_journal_id': trade_id,
            'alpaca_order_id': 'tp-order-filled',
            'order_type': 'TAKE_PROFIT',
            'side': 'sell',
            'order_status': 'pending',
            'qty': 10,
            'limit_price': 160.00
        })

        # Run monitor
        monitor = OrderMonitor(test_mode=True, db=test_db, alpaca_client=mock_alpaca_client)
        monitor.run()

        # Verify trade was closed with profit
        trade = test_db.get_by_id('trade_journal', trade_id)
        assert trade['status'] == 'CLOSED'
        assert trade['exit_reason'] == 'TARGET_HIT'
        assert float(trade['exit_price']) == 160.10

        # Calculate expected P&L: (160.10 - 150.25) * 10 = 98.50
        expected_pnl = (160.10 - 150.25) * 10
        assert abs(float(trade['actual_pnl']) - expected_pnl) < 0.01

    def test_exit_fill_cancels_remaining_orders(self, test_db, mock_alpaca_client):
        """Test that exit fill cancels the remaining order"""
        # Create trade with position
        trade_id = test_db.insert('trade_journal', {
            'trade_id': 'TEST_CANCEL_REMAINING',
            'symbol': 'AAPL',
            'status': 'POSITION',
            'actual_entry': 150.25,
            'actual_qty': 10,
            'trade_style': 'SWING'
        })

        # Create position
        test_db.insert('position_tracking', {
            'trade_journal_id': trade_id,
            'symbol': 'AAPL',
            'qty': 10,
            'avg_entry_price': 150.25
        })

        # Create filled TP order
        tp_filled = MockAlpacaOrder(
            id='tp-filled',
            client_order_id='client-tp',
            symbol='AAPL',
            qty=10,
            side='sell',
            order_type='limit',
            time_in_force='gtc',
            limit_price=160.00,
            filled_avg_price=160.10,
            status='filled',
            filled_qty=10
        )
        tp_filled.filled_at = '2025-10-26T14:00:00Z'
        mock_alpaca_client.orders['tp-filled'] = tp_filled

        # Create pending SL order
        sl_pending = MockAlpacaOrder(
            id='sl-pending',
            client_order_id='client-sl',
            symbol='AAPL',
            qty=10,
            side='sell',
            order_type='stop',
            time_in_force='gtc',
            stop_price=145.00,
            status='pending'
        )
        mock_alpaca_client.orders['sl-pending'] = sl_pending

        # Create TP order in database (filled)
        test_db.insert('order_execution', {
            'trade_journal_id': trade_id,
            'alpaca_order_id': 'tp-filled',
            'order_type': 'TAKE_PROFIT',
            'side': 'sell',
            'order_status': 'pending',
            'qty': 10,
            'limit_price': 160.00
        })

        # Create SL order in database (pending)
        test_db.insert('order_execution', {
            'trade_journal_id': trade_id,
            'alpaca_order_id': 'sl-pending',
            'order_type': 'STOP_LOSS',
            'side': 'sell',
            'order_status': 'pending',
            'qty': 10,
            'stop_price': 145.00
        })

        # Run monitor
        monitor = OrderMonitor(test_mode=True, db=test_db, alpaca_client=mock_alpaca_client)
        monitor.run()

        # Verify SL order was cancelled
        assert mock_alpaca_client.orders['sl-pending'].status == 'cancelled'

        # Verify database was updated
        sl_order = test_db.query('order_execution', 'alpaca_order_id = %s', ('sl-pending',))[0]
        assert sl_order['order_status'] == 'cancelled'
