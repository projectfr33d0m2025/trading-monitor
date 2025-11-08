"""
Integration tests for complete trade lifecycle
Tests the full flow from order execution to position close
"""
import pytest
import json
from order_executor import OrderExecutor
from order_monitor import OrderMonitor
from position_monitor import PositionMonitor
from tests.conftest import MockAlpacaOrder


class TestCompleteTradeLifecycle:
    """Test complete trade lifecycle from start to finish"""

    def test_successful_trade_with_take_profit(self, test_db, mock_alpaca_client, mock_data_client):
        """
        Test complete successful trade lifecycle:
        1. Place entry order
        2. Entry order fills
        3. SL and TP orders placed
        4. Position value updates
        5. TP order fills
        6. Trade closes with profit
        """
        # STEP 1: Create analysis decision for NEW_TRADE
        decision = {
            "action": "BUY",
            "primary_action": "NEW_TRADE",
            "qty": 10,
            "entry_price": 150.00,
            "stop_loss": 145.00,
            "take_profit": 160.00,
            "trade_style": "SWING",
            "pattern": "Breakout"
        }
        decision_json = json.dumps(decision)
        test_db.execute_query("""
            INSERT INTO analysis_decision (
                "Analysis_Id", "Ticker", "Decision", executed, "Approve"
            ) VALUES (%s, %s, %s::jsonb, %s, %s)
        """, ('INTEGRATION_001', 'AAPL', decision_json, False, True))

        # STEP 2: Run Order Executor - Place entry order
        executor = OrderExecutor(test_mode=True, db=test_db, alpaca_client=mock_alpaca_client)
        executor.run()

        # Verify entry order was placed
        entry_orders = test_db.query('order_execution', 'order_type = %s', ('ENTRY',))
        assert len(entry_orders) == 1
        entry_order = entry_orders[0]
        assert entry_order['order_status'] == 'pending'

        # Verify trade_journal was created
        trades = test_db.query('trade_journal', 'symbol = %s', ('AAPL',))
        assert len(trades) == 1
        trade = trades[0]
        assert trade['status'] == 'ORDERED'

        # STEP 3: Simulate entry order fill
        alpaca_order_id = entry_order['alpaca_order_id']
        mock_alpaca_client.orders[alpaca_order_id].status = 'filled'
        mock_alpaca_client.orders[alpaca_order_id].filled_qty = '10'
        mock_alpaca_client.orders[alpaca_order_id].filled_avg_price = 150.25
        mock_alpaca_client.orders[alpaca_order_id].filled_at = '2025-10-26T10:00:00Z'

        # STEP 4: Run Order Monitor - Detect entry fill, place SL/TP
        monitor = OrderMonitor(test_mode=True, db=test_db, alpaca_client=mock_alpaca_client)
        monitor.run()

        # Verify trade status changed to POSITION
        trade = test_db.get_by_id('trade_journal', trade['id'])
        assert trade['status'] == 'POSITION'
        assert float(trade['actual_entry']) == 150.25
        assert trade['actual_qty'] == 10

        # Verify position was created
        positions = test_db.query('position_tracking', 'symbol = %s', ('AAPL',))
        assert len(positions) == 1
        position = positions[0]
        assert position['qty'] == 10
        assert float(position['avg_entry_price']) == 150.25

        # Verify SL and TP orders were placed
        sl_orders = test_db.query('order_execution', 'order_type = %s', ('STOP_LOSS',))
        tp_orders = test_db.query('order_execution', 'order_type = %s', ('TAKE_PROFIT',))
        assert len(sl_orders) == 1
        assert len(tp_orders) == 1

        # STEP 5: Update position values
        # Add position to mock Alpaca client
        from tests.conftest import MockAlpacaPosition
        mock_alpaca_client.positions['AAPL'] = MockAlpacaPosition(
            symbol='AAPL',
            qty=10,
            side='long',
            avg_entry_price=150.25,
            current_price=157.25,
            market_value=1572.50,
            unrealized_pl=70.00,
            unrealized_plpc=0.0466
        )

        mock_data_client.add_quote('AAPL', 157.00, 157.50)
        pos_monitor = PositionMonitor(
            test_mode=True,
            db=test_db,
            trading_client=mock_alpaca_client,
            data_client=mock_data_client
        )
        pos_monitor.run()

        # Verify position was updated
        position = test_db.get_by_id('position_tracking', position['id'])
        assert float(position['current_price']) == 157.25  # Midpoint
        assert float(position['unrealized_pnl']) > 0  # Should be profitable

        # STEP 6: Simulate TP order fill
        tp_order = tp_orders[0]
        tp_alpaca_id = tp_order['alpaca_order_id']
        mock_alpaca_client.orders[tp_alpaca_id].status = 'filled'
        mock_alpaca_client.orders[tp_alpaca_id].filled_qty = '10'
        mock_alpaca_client.orders[tp_alpaca_id].filled_avg_price = 160.10
        mock_alpaca_client.orders[tp_alpaca_id].filled_at = '2025-10-26T15:00:00Z'

        # STEP 7: Run Order Monitor - Detect TP fill, close trade
        monitor.run()

        # Verify trade was closed
        trade = test_db.get_by_id('trade_journal', trade['id'])
        assert trade['status'] == 'CLOSED'
        assert trade['exit_reason'] == 'TARGET_HIT'
        assert float(trade['exit_price']) == 160.10

        # Verify P&L is correct
        expected_pnl = (160.10 - 150.25) * 10
        assert abs(float(trade['actual_pnl']) - expected_pnl) < 0.01

        # Verify position was deleted
        positions = test_db.query('position_tracking', 'symbol = %s', ('AAPL',))
        assert len(positions) == 0

        # Verify SL order was cancelled
        sl_order = test_db.get_by_id('order_execution', sl_orders[0]['id'])
        assert sl_order['order_status'] == 'cancelled'

    def test_losing_trade_with_stop_loss(self, test_db, mock_alpaca_client, mock_data_client):
        """
        Test trade that hits stop loss:
        1. Place entry order
        2. Entry fills
        3. Position loses value
        4. SL hits
        5. Trade closes with loss
        """
        # STEP 1: Create decision
        decision = {
            "action": "BUY",
            "primary_action": "NEW_TRADE",
            "qty": 5,
            "entry_price": 200.00,
            "stop_loss": 195.00,
            "trade_style": "DAYTRADE"
        }
        decision_json = json.dumps(decision)
        test_db.execute_query("""
            INSERT INTO analysis_decision (
                "Analysis_Id", "Ticker", "Decision", executed, "Approve"
            ) VALUES (%s, %s, %s::jsonb, %s, %s)
        """, ('INTEGRATION_002', 'TSLA', decision_json, False, True))

        # STEP 2: Execute order
        executor = OrderExecutor(test_mode=True, db=test_db, alpaca_client=mock_alpaca_client)
        executor.run()

        entry_orders = test_db.query('order_execution', 'order_type = %s', ('ENTRY',))
        entry_order = entry_orders[0]

        # STEP 3: Fill entry order
        alpaca_order_id = entry_order['alpaca_order_id']
        mock_alpaca_client.orders[alpaca_order_id].status = 'filled'
        mock_alpaca_client.orders[alpaca_order_id].filled_qty = '5'
        mock_alpaca_client.orders[alpaca_order_id].filled_avg_price = 200.50
        mock_alpaca_client.orders[alpaca_order_id].filled_at = '2025-10-26T10:00:00Z'

        # STEP 4: Monitor detects fill
        monitor = OrderMonitor(test_mode=True, db=test_db, alpaca_client=mock_alpaca_client)
        monitor.run()

        # Get position
        positions = test_db.query('position_tracking', 'symbol = %s', ('TSLA',))
        position = positions[0]

        # STEP 5: Update position with losing price
        # Add position to mock Alpaca client
        from tests.conftest import MockAlpacaPosition
        mock_alpaca_client.positions['TSLA'] = MockAlpacaPosition(
            symbol='TSLA',
            qty=5,
            side='long',
            avg_entry_price=200.25,
            current_price=196.25,
            market_value=981.25,
            unrealized_pl=-20.00,
            unrealized_plpc=-0.01
        )

        mock_data_client.add_quote('TSLA', 196.00, 196.50)
        pos_monitor = PositionMonitor(
            test_mode=True,
            db=test_db,
            trading_client=mock_alpaca_client,
            data_client=mock_data_client
        )
        pos_monitor.run()

        # Verify position shows loss
        position = test_db.get_by_id('position_tracking', position['id'])
        assert float(position['unrealized_pnl']) < 0

        # STEP 6: Simulate SL fill
        sl_orders = test_db.query('order_execution', 'order_type = %s', ('STOP_LOSS',))
        sl_order = sl_orders[0]
        sl_alpaca_id = sl_order['alpaca_order_id']
        mock_alpaca_client.orders[sl_alpaca_id].status = 'filled'
        mock_alpaca_client.orders[sl_alpaca_id].filled_qty = '5'
        mock_alpaca_client.orders[sl_alpaca_id].filled_avg_price = 194.90
        mock_alpaca_client.orders[sl_alpaca_id].filled_at = '2025-10-26T14:00:00Z'

        # STEP 7: Monitor detects SL fill
        monitor.run()

        # Verify trade closed with loss
        trades = test_db.query('trade_journal', 'symbol = %s', ('TSLA',))
        trade = trades[0]
        assert trade['status'] == 'CLOSED'
        assert trade['exit_reason'] == 'STOPPED_OUT'
        assert float(trade['exit_price']) == 194.90

        # Verify loss
        expected_pnl = (194.90 - 200.50) * 5
        assert abs(float(trade['actual_pnl']) - expected_pnl) < 0.01
        assert float(trade['actual_pnl']) < 0

    def test_daytrade_lifecycle(self, test_db, mock_alpaca_client, mock_data_client):
        """Test DAYTRADE lifecycle (no take profit)"""
        # Create DAYTRADE decision
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
                "Analysis_Id", "Ticker", "Decision", executed, "Approve"
            ) VALUES (%s, %s, %s::jsonb, %s, %s)
        """, ('INTEGRATION_003', 'AAPL', decision_json, False, True))

        # Execute order
        executor = OrderExecutor(test_mode=True, db=test_db, alpaca_client=mock_alpaca_client)
        executor.run()

        # Fill entry
        entry_orders = test_db.query('order_execution', 'order_type = %s', ('ENTRY',))
        entry_order = entry_orders[0]
        alpaca_order_id = entry_order['alpaca_order_id']
        mock_alpaca_client.orders[alpaca_order_id].status = 'filled'
        mock_alpaca_client.orders[alpaca_order_id].filled_qty = '10'
        mock_alpaca_client.orders[alpaca_order_id].filled_avg_price = 150.25
        mock_alpaca_client.orders[alpaca_order_id].filled_at = '2025-10-26T10:00:00Z'

        # Monitor processes fill
        monitor = OrderMonitor(test_mode=True, db=test_db, alpaca_client=mock_alpaca_client)
        monitor.run()

        # Verify SL was placed but NOT TP
        sl_orders = test_db.query('order_execution', 'order_type = %s', ('STOP_LOSS',))
        tp_orders = test_db.query('order_execution', 'order_type = %s', ('TAKE_PROFIT',))
        assert len(sl_orders) == 1
        assert len(tp_orders) == 0  # No TP for DAYTRADE

    def test_cancel_order_lifecycle(self, test_db, mock_alpaca_client):
        """Test CANCEL action lifecycle"""
        # STEP 1: Create and execute NEW_TRADE
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
                "Analysis_Id", "Ticker", "Decision", executed, "Approve"
            ) VALUES (%s, %s, %s::jsonb, %s, %s)
        """, ('INTEGRATION_CANCEL_1', 'AAPL', decision_json, False, True))

        executor = OrderExecutor(test_mode=True, db=test_db, alpaca_client=mock_alpaca_client)
        executor.run()

        # Get order and trade IDs
        original_decision = test_db.execute_query(
            'SELECT * FROM analysis_decision WHERE "Analysis_Id" = %s',
            ('INTEGRATION_CANCEL_1',)
        )[0]
        order_id = original_decision['existing_order_id']
        trade_id = original_decision['existing_trade_journal_id']

        # STEP 2: Create CANCEL decision
        cancel_decision = {
            "action": "BUY",
            "primary_action": "CANCEL"
        }
        cancel_json = json.dumps(cancel_decision)
        test_db.execute_query("""
            INSERT INTO analysis_decision (
                "Analysis_Id", "Ticker", "Decision", executed, "Approve",
                existing_order_id, existing_trade_journal_id
            ) VALUES (%s, %s, %s::jsonb, %s, %s, %s, %s)
        """, ('INTEGRATION_CANCEL_2', 'AAPL', cancel_json, False, True, order_id, trade_id))

        # STEP 3: Execute CANCEL
        executor.run()

        # Verify order was cancelled
        assert mock_alpaca_client.orders[order_id].status == 'cancelled'

        # Verify trade was marked CANCELLED
        trade = test_db.get_by_id('trade_journal', trade_id)
        assert trade['status'] == 'CANCELLED'

    def test_amend_order_lifecycle(self, test_db, mock_alpaca_client):
        """Test AMEND action lifecycle"""
        # STEP 1: Create and execute original order
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
                "Analysis_Id", "Ticker", "Decision", executed, "Approve"
            ) VALUES (%s, %s, %s::jsonb, %s, %s)
        """, ('INTEGRATION_AMEND_1', 'AAPL', decision_json, False, True))

        executor = OrderExecutor(test_mode=True, db=test_db, alpaca_client=mock_alpaca_client)
        executor.run()

        # Get original order
        original_decision = test_db.execute_query(
            'SELECT * FROM analysis_decision WHERE "Analysis_Id" = %s',
            ('INTEGRATION_AMEND_1',)
        )[0]
        original_order_id = original_decision['existing_order_id']
        original_trade_id = original_decision['existing_trade_journal_id']

        # STEP 2: Create AMEND decision with new parameters
        amend_decision = {
            "action": "BUY",
            "primary_action": "AMEND",
            "qty": 15,  # Changed
            "entry_price": 155.00,  # Changed
            "stop_loss": 150.00,  # Changed
            "trade_style": "DAYTRADE"
        }
        amend_json = json.dumps(amend_decision)
        test_db.execute_query("""
            INSERT INTO analysis_decision (
                "Analysis_Id", "Ticker", "Decision", executed, "Approve",
                existing_order_id, existing_trade_journal_id
            ) VALUES (%s, %s, %s::jsonb, %s, %s, %s, %s)
        """, ('INTEGRATION_AMEND_2', 'AAPL', amend_json, False, True, original_order_id, original_trade_id))

        # STEP 3: Execute AMEND
        executor.run()

        # Verify original order was cancelled
        assert mock_alpaca_client.orders[original_order_id].status == 'cancelled'

        # Verify new order was created with new parameters
        new_orders = [o for o in mock_alpaca_client.orders.values() if o.id != original_order_id]
        assert len(new_orders) == 1
        new_order = new_orders[0]
        assert float(new_order.qty) == 15.0
        assert new_order.limit_price == 155.00

    def test_multiple_positions_lifecycle(self, test_db, mock_alpaca_client, mock_data_client):
        """Test handling multiple positions simultaneously"""
        symbols = ['AAPL', 'MSFT', 'GOOGL']

        # Create and execute multiple trades
        for i, symbol in enumerate(symbols):
            decision = {
                "action": "BUY",
                "primary_action": "NEW_TRADE",
                "qty": 10,
                "entry_price": 150.00 + i * 10,
                "stop_loss": 145.00 + i * 10,
                "take_profit": 160.00 + i * 10,
                "trade_style": "SWING"
            }
            decision_json = json.dumps(decision)
            test_db.execute_query("""
                INSERT INTO analysis_decision (
                    "Analysis_Id", "Ticker", "Decision", executed, "Approve"
                ) VALUES (%s, %s, %s::jsonb, %s, %s)
            """, (f'MULTI_{i}', symbol, decision_json, False, True))

        # Execute all orders
        executor = OrderExecutor(test_mode=True, db=test_db, alpaca_client=mock_alpaca_client)
        executor.run()

        # Fill all entry orders
        entry_orders = test_db.query('order_execution', 'order_type = %s', ('ENTRY',))
        assert len(entry_orders) == 3

        for order in entry_orders:
            alpaca_order_id = order['alpaca_order_id']
            mock_alpaca_client.orders[alpaca_order_id].status = 'filled'
            mock_alpaca_client.orders[alpaca_order_id].filled_qty = '10'
            mock_alpaca_client.orders[alpaca_order_id].filled_avg_price = float(order['limit_price']) + 0.25
            mock_alpaca_client.orders[alpaca_order_id].filled_at = '2025-10-26T10:00:00Z'

        # Process all fills
        monitor = OrderMonitor(test_mode=True, db=test_db, alpaca_client=mock_alpaca_client)
        monitor.run()

        # Verify all positions were created
        positions = test_db.execute_query("SELECT * FROM position_tracking ORDER BY symbol")
        assert len(positions) == 3

        # Update all positions
        from tests.conftest import MockAlpacaPosition
        for i, symbol in enumerate(symbols):
            entry_price = 150.00 + i * 10 + 0.25
            current_price = entry_price + 10  # All positions are up $10/share
            unrealized_pl = (current_price - entry_price) * 10

            # Add position to mock Alpaca client
            mock_alpaca_client.positions[symbol] = MockAlpacaPosition(
                symbol=symbol,
                qty=10,
                side='long',
                avg_entry_price=entry_price,
                current_price=current_price,
                market_value=current_price * 10,
                unrealized_pl=unrealized_pl,
                unrealized_plpc=unrealized_pl / (entry_price * 10)
            )
            mock_data_client.add_quote(symbol, current_price - 0.25, current_price + 0.25)

        pos_monitor = PositionMonitor(
            test_mode=True,
            db=test_db,
            trading_client=mock_alpaca_client,
            data_client=mock_data_client
        )
        pos_monitor.run()

        # Verify all positions were updated
        for position in positions:
            updated_pos = test_db.get_by_id('position_tracking', position['id'])
            # Each position should be up $10/share from entry
            assert float(updated_pos['current_price']) > float(position['avg_entry_price'])
            assert float(updated_pos['unrealized_pnl']) > 0
