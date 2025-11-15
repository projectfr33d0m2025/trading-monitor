"""
Unit tests for Position Monitor
Tests position value updates and reconciliation
"""
import pytest
from position_monitor import PositionMonitor


class TestPositionMonitorUpdate:
    """Test position value updates"""

    def test_update_position_with_price_increase(self, test_db, mock_alpaca_client, mock_data_client):
        """Test updating position with price increase"""
        # Create trade
        trade_id = test_db.insert('trade_journal', {
            'trade_id': 'TEST_POS_UP',
            'symbol': 'AAPL',
            'status': 'POSITION',
            'actual_entry': 150.00,
            'actual_qty': 10
        })

        # Create position
        position_id = test_db.insert('position_tracking', {
            'trade_journal_id': trade_id,
            'symbol': 'AAPL',
            'qty': 10,
            'avg_entry_price': 150.00,
            'current_price': 150.00,
            'market_value': 1500.00,
            'cost_basis': 1500.00,
            'unrealized_pnl': 0.00
        })

        # Add position to mock Alpaca client (so it's not reconciled as closed)
        from tests.conftest import MockAlpacaPosition
        mock_alpaca_client.positions['AAPL'] = MockAlpacaPosition(
            symbol='AAPL',
            qty=10,
            side='long',
            avg_entry_price=150.00,
            current_price=155.25,
            market_value=1552.50,
            unrealized_pl=52.50,
            unrealized_plpc=0.035
        )

        # Set current market price (higher than entry)
        mock_data_client.add_quote('AAPL', 155.00, 155.50)  # Midpoint = 155.25

        # Run position monitor
        monitor = PositionMonitor(
            test_mode=True,
            db=test_db,
            trading_client=mock_alpaca_client,
            data_client=mock_data_client
        )
        monitor.run()

        # Verify position was updated
        position = test_db.get_by_id('position_tracking', position_id)
        assert float(position['current_price']) == 155.25  # Midpoint
        assert float(position['market_value']) == 155.25 * 10
        assert float(position['unrealized_pnl']) == (155.25 - 150.00) * 10

    def test_update_position_with_price_decrease(self, test_db, mock_alpaca_client, mock_data_client):
        """Test updating position with price decrease (unrealized loss)"""
        # Create trade
        trade_id = test_db.insert('trade_journal', {
            'trade_id': 'TEST_POS_DOWN',
            'symbol': 'TSLA',
            'status': 'POSITION',
            'actual_entry': 200.00,
            'actual_qty': 5
        })

        # Create position
        position_id = test_db.insert('position_tracking', {
            'trade_journal_id': trade_id,
            'symbol': 'TSLA',
            'qty': 5,
            'avg_entry_price': 200.00,
            'current_price': 200.00,
            'market_value': 1000.00,
            'cost_basis': 1000.00,
            'unrealized_pnl': 0.00
        })

        # Add position to mock Alpaca client
        from tests.conftest import MockAlpacaPosition
        mock_alpaca_client.positions['TSLA'] = MockAlpacaPosition(
            symbol='TSLA',
            qty=5,
            side='long',
            avg_entry_price=200.00,
            current_price=190.25,
            market_value=951.25,
            unrealized_pl=-48.75,
            unrealized_plpc=-0.04875
        )

        # Set current market price (lower than entry)
        mock_data_client.add_quote('TSLA', 190.00, 190.50)  # Midpoint = 190.25

        # Run position monitor
        monitor = PositionMonitor(
            test_mode=True,
            db=test_db,
            trading_client=mock_alpaca_client,
            data_client=mock_data_client
        )
        monitor.run()

        # Verify position was updated with loss
        position = test_db.get_by_id('position_tracking', position_id)
        assert float(position['current_price']) == 190.25
        assert float(position['market_value']) == 190.25 * 5
        expected_pnl = (190.25 - 200.00) * 5
        assert abs(float(position['unrealized_pnl']) - expected_pnl) < 0.01

    def test_update_multiple_positions(self, test_db, mock_alpaca_client, mock_data_client):
        """Test updating multiple positions"""
        # Create multiple positions
        symbols = [
            ('AAPL', 150.00, 10, 155.00, 155.50),
            ('MSFT', 300.00, 5, 310.00, 310.50),
            ('GOOGL', 140.00, 3, 138.00, 138.50)
        ]

        from tests.conftest import MockAlpacaPosition
        for symbol, entry, qty, bid, ask in symbols:
            trade_id = test_db.insert('trade_journal', {
                'trade_id': f'{symbol}_TEST',
                'symbol': symbol,
                'status': 'POSITION',
                'actual_entry': entry,
                'actual_qty': qty
            })

            test_db.insert('position_tracking', {
                'trade_journal_id': trade_id,
                'symbol': symbol,
                'qty': qty,
                'avg_entry_price': entry,
                'current_price': entry,
                'market_value': entry * qty,
                'cost_basis': entry * qty,
                'unrealized_pnl': 0.00
            })

            # Add position to mock Alpaca client
            mock_alpaca_client.positions[symbol] = MockAlpacaPosition(
                symbol=symbol,
                qty=qty,
                side='long',
                avg_entry_price=entry,
                current_price=entry,
                market_value=entry * qty,
                unrealized_pl=0.00,
                unrealized_plpc=0.00
            )

            mock_data_client.add_quote(symbol, bid, ask)

        # Run position monitor
        monitor = PositionMonitor(
            test_mode=True,
            db=test_db,
            trading_client=mock_alpaca_client,
            data_client=mock_data_client
        )
        monitor.run()

        # Verify all positions were updated
        positions = test_db.execute_query("SELECT * FROM position_tracking ORDER BY symbol")
        assert len(positions) == 3

        # Check AAPL (profit)
        aapl = positions[0]
        assert aapl['symbol'] == 'AAPL'
        assert float(aapl['current_price']) == 155.25
        assert float(aapl['unrealized_pnl']) > 0

        # Check GOOGL (loss)
        googl = positions[1]
        assert googl['symbol'] == 'GOOGL'
        assert float(googl['current_price']) == 138.25
        assert float(googl['unrealized_pnl']) < 0

        # Check MSFT (profit)
        msft = positions[2]
        assert msft['symbol'] == 'MSFT'
        assert float(msft['current_price']) == 310.25
        assert float(msft['unrealized_pnl']) > 0

    def test_no_positions_to_update(self, test_db, mock_alpaca_client, mock_data_client):
        """Test monitor with no active positions"""
        monitor = PositionMonitor(
            test_mode=True,
            db=test_db,
            trading_client=mock_alpaca_client,
            data_client=mock_data_client
        )
        monitor.run()
        # Should complete without errors


class TestPositionMonitorReconciliation:
    """Test position reconciliation for positions closed outside system"""

    def test_reconcile_manually_closed_position(self, test_db, mock_alpaca_client, mock_data_client):
        """Test reconciling a position closed manually (not by our system)"""
        # Create trade with position
        trade_id = test_db.insert('trade_journal', {
            'trade_id': 'TEST_MANUAL_CLOSE',
            'symbol': 'AAPL',
            'status': 'POSITION',
            'actual_entry': 150.00,
            'actual_qty': 10
        })

        # Create position in database
        position_id = test_db.insert('position_tracking', {
            'trade_journal_id': trade_id,
            'symbol': 'AAPL',
            'qty': 10,
            'avg_entry_price': 150.00,
            'current_price': 155.00,
            'market_value': 1550.00,
            'cost_basis': 1500.00,
            'unrealized_pnl': 50.00
        })

        # Set market data
        mock_data_client.add_quote('AAPL', 155.00, 155.50)

        # Don't add position to mock_alpaca_client.positions
        # This simulates position being closed outside our system

        # Run position monitor
        monitor = PositionMonitor(
            test_mode=True,
            db=test_db,
            trading_client=mock_alpaca_client,
            data_client=mock_data_client
        )
        monitor.run()

        # Verify trade_journal was updated to CLOSED
        trade = test_db.get_by_id('trade_journal', trade_id)
        assert trade['status'] == 'CLOSED'
        assert trade['exit_reason'] == 'MANUAL_EXIT'
        assert float(trade['exit_price']) == 155.25  # Current market price (midpoint)
        assert float(trade['actual_pnl']) == 52.50  # Recalculated P&L: (155.25 - 150.00) * 10

        # Verify position_tracking was deleted
        positions = test_db.query('position_tracking', 'id = %s', (position_id,))
        assert len(positions) == 0

    def test_reconcile_with_filled_stop_loss(self, test_db, mock_alpaca_client, mock_data_client):
        """Test reconciling position with filled stop-loss order"""
        # Create trade with position
        trade_id = test_db.insert('trade_journal', {
            'trade_id': 'TEST_SL_RECONCILE',
            'symbol': 'AAPL',
            'status': 'POSITION',
            'actual_entry': 150.00,
            'actual_qty': 10
        })

        # Create position
        position_id = test_db.insert('position_tracking', {
            'trade_journal_id': trade_id,
            'symbol': 'AAPL',
            'qty': 10,
            'avg_entry_price': 150.00,
            'current_price': 145.00,
            'market_value': 1450.00,
            'cost_basis': 1500.00,
            'unrealized_pnl': -50.00
        })

        # Create filled SL order in database
        test_db.insert('order_execution', {
            'trade_journal_id': trade_id,
            'alpaca_order_id': 'sl-filled-reconcile',
            'order_type': 'STOP_LOSS',
            'side': 'sell',
            'order_status': 'filled',
            'qty': 10,
            'stop_price': 145.00,
            'filled_avg_price': 144.90,
            'filled_at': '2025-10-26T14:00:00Z'
        })

        # Position not in Alpaca (closed)
        # Run monitor
        monitor = PositionMonitor(
            test_mode=True,
            db=test_db,
            trading_client=mock_alpaca_client,
            data_client=mock_data_client
        )
        monitor.run()

        # Verify trade was closed with SL data
        trade = test_db.get_by_id('trade_journal', trade_id)
        assert trade['status'] == 'CLOSED'
        assert trade['exit_reason'] == 'STOPPED_OUT'
        assert float(trade['exit_price']) == 144.90
        expected_pnl = (144.90 - 150.00) * 10
        assert abs(float(trade['actual_pnl']) - expected_pnl) < 0.01

    def test_reconcile_with_filled_take_profit(self, test_db, mock_alpaca_client, mock_data_client):
        """Test reconciling position with filled take-profit order"""
        # Create trade with position
        trade_id = test_db.insert('trade_journal', {
            'trade_id': 'TEST_TP_RECONCILE',
            'symbol': 'AAPL',
            'status': 'POSITION',
            'actual_entry': 150.00,
            'actual_qty': 10
        })

        # Create position
        position_id = test_db.insert('position_tracking', {
            'trade_journal_id': trade_id,
            'symbol': 'AAPL',
            'qty': 10,
            'avg_entry_price': 150.00,
            'current_price': 160.00,
            'market_value': 1600.00,
            'cost_basis': 1500.00,
            'unrealized_pnl': 100.00
        })

        # Create filled TP order in database
        test_db.insert('order_execution', {
            'trade_journal_id': trade_id,
            'alpaca_order_id': 'tp-filled-reconcile',
            'order_type': 'TAKE_PROFIT',
            'side': 'sell',
            'order_status': 'filled',
            'qty': 10,
            'limit_price': 160.00,
            'filled_avg_price': 160.10,
            'filled_at': '2025-10-26T14:00:00Z'
        })

        # Position not in Alpaca (closed)
        # Run monitor
        monitor = PositionMonitor(
            test_mode=True,
            db=test_db,
            trading_client=mock_alpaca_client,
            data_client=mock_data_client
        )
        monitor.run()

        # Verify trade was closed with TP data
        trade = test_db.get_by_id('trade_journal', trade_id)
        assert trade['status'] == 'CLOSED'
        assert trade['exit_reason'] == 'TARGET_HIT'
        assert float(trade['exit_price']) == 160.10
        expected_pnl = (160.10 - 150.00) * 10
        assert abs(float(trade['actual_pnl']) - expected_pnl) < 0.01

    def test_position_still_exists_in_alpaca(self, test_db, mock_alpaca_client, mock_data_client):
        """Test that position is not reconciled if it still exists in Alpaca"""
        # Create trade with position
        trade_id = test_db.insert('trade_journal', {
            'trade_id': 'TEST_STILL_OPEN',
            'symbol': 'AAPL',
            'status': 'POSITION',
            'actual_entry': 150.00,
            'actual_qty': 10
        })

        # Create position
        position_id = test_db.insert('position_tracking', {
            'trade_journal_id': trade_id,
            'symbol': 'AAPL',
            'qty': 10,
            'avg_entry_price': 150.00,
            'current_price': 155.00,
            'market_value': 1550.00,
            'cost_basis': 1500.00,
            'unrealized_pnl': 50.00
        })

        # Add position to Alpaca (still exists)
        from tests.conftest import MockAlpacaPosition
        mock_alpaca_client.positions['AAPL'] = MockAlpacaPosition(
            symbol='AAPL',
            qty=10,
            side='long',
            avg_entry_price=150.00,
            current_price=155.00,
            market_value=1550.00,
            unrealized_pl=50.00,
            unrealized_plpc=0.0333
        )

        # Set market data
        mock_data_client.add_quote('AAPL', 155.00, 155.50)

        # Run monitor
        monitor = PositionMonitor(
            test_mode=True,
            db=test_db,
            trading_client=mock_alpaca_client,
            data_client=mock_data_client
        )
        monitor.run()

        # Verify trade is still POSITION (not closed)
        trade = test_db.get_by_id('trade_journal', trade_id)
        assert trade['status'] == 'POSITION'

        # Verify position still exists
        positions = test_db.query('position_tracking', 'id = %s', (position_id,))
        assert len(positions) == 1

    def test_reconcile_multiple_closed_positions(self, test_db, mock_alpaca_client, mock_data_client):
        """Test reconciling multiple closed positions"""
        # Create multiple closed positions
        symbols = ['AAPL', 'MSFT', 'GOOGL']
        for symbol in symbols:
            trade_id = test_db.insert('trade_journal', {
                'trade_id': f'{symbol}_CLOSED',
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
                'current_price': 155.00,
                'market_value': 1550.00,
                'cost_basis': 1500.00,
                'unrealized_pnl': 50.00
            })

        # None of them exist in Alpaca (all closed)
        # Run monitor
        monitor = PositionMonitor(
            test_mode=True,
            db=test_db,
            trading_client=mock_alpaca_client,
            data_client=mock_data_client
        )
        monitor.run()

        # Verify all trades were closed
        trades = test_db.execute_query("SELECT * FROM trade_journal WHERE status = 'CLOSED'")
        assert len(trades) == 3

        # Verify all positions were deleted
        positions = test_db.execute_query("SELECT * FROM position_tracking")
        assert len(positions) == 0
