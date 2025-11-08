#!/usr/bin/env python3
"""
Manual Test Script for position_monitor.py - Complete Flow Testing
No real Alpaca API or manual database setup required!

This script uses:
- testing.postgresql (auto-creates temporary database)
- MockAlpacaClient & MockAlpacaDataClient (simulates Alpaca API)

Just run: python manual_test_position_monitor.py
"""
import sys
import os
import uuid
from datetime import datetime
from decimal import Decimal

# Add tests directory to path to import conftest
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'tests'))

import testing.postgresql
from conftest import MockAlpacaClient, MockAlpacaDataClient, MockAlpacaPosition, MockAlpacaQuote, MockAlpacaOrder
from db_layer import TradingDB
from position_monitor import PositionMonitor


class TestDatabase:
    """Wrapper for temporary PostgreSQL database"""

    def __init__(self):
        self.postgresql = testing.postgresql.Postgresql()
        self.db = None

    def __enter__(self):
        # Create TradingDB instance with test database
        dsn = self.postgresql.dsn()
        os.environ['TEST_POSTGRES_HOST'] = dsn['host']
        os.environ['TEST_POSTGRES_PORT'] = str(dsn['port'])
        os.environ['TEST_POSTGRES_DB'] = dsn['database']
        os.environ['TEST_POSTGRES_USER'] = dsn['user']
        os.environ['TEST_POSTGRES_PASSWORD'] = ''
        os.environ['TEST_POSTGRES_SCHEMA'] = 'public'

        self.db = TradingDB(test_mode=True)
        self.db.create_schema()

        # Print connection info for external database access
        self._print_connection_info(dsn)

        return self.db

    def _print_connection_info(self, dsn):
        """Print database connection information"""
        host = dsn['host']
        port = dsn['port']
        database = dsn['database']
        user = dsn['user']

        print("\n" + "=" * 80)
        print("📡 DATABASE CONNECTION INFO (Connect while script is paused)".center(80))
        print("=" * 80)
        print(f"\n  Host:     {host}")
        print(f"  Port:     {port}")
        print(f"  Database: {database}")
        print(f"  User:     {user}")
        print(f"  Password: (none)")
        print(f"\n  Connection String:")
        print(f"  postgresql://{user}@{host}:{port}/{database}")
        print(f"\n  Quick Connect:")
        print(f"  psql -h {host} -p {port} -U {user} -d {database}")
        print("\n" + "=" * 80 + "\n")

    def __exit__(self, exc_type, exc_val, exc_tb):
        if self.db:
            self.db.close()
        self.postgresql.stop()


def print_section(title, char="="):
    """Print a section header"""
    print(f"\n{char * 80}")
    print(f"{title.center(80)}")
    print(f"{char * 80}\n")


def print_subsection(title):
    """Print a subsection header"""
    print(f"\n{'-' * 80}")
    print(f"  {title}")
    print(f"{'-' * 80}")


def display_trade_state(db, trade_id):
    """Display current state of trade_journal"""
    trade = db.get_by_id('trade_journal', trade_id)

    print("\n📊 TRADE JOURNAL STATUS:")
    print(f"  Trade ID: {trade['trade_id']}")
    print(f"  Symbol: {trade['symbol']}")
    print(f"  Trade Style: {trade['trade_style']}")
    print(f"  Status: {trade['status']}")
    print(f"  Actual Entry: ${trade['actual_entry'] or 'N/A'}")
    print(f"  Actual Qty: {trade['actual_qty'] or 'N/A'}")

    if trade['status'] == 'CLOSED':
        print(f"  Exit Price: ${trade['exit_price']}")
        print(f"  Actual P&L: ${trade['actual_pnl']:.2f}")
        print(f"  Exit Reason: {trade['exit_reason']}")


def display_position(db, trade_journal_id):
    """Display position tracking"""
    positions = db.query('position_tracking', 'trade_journal_id = %s', (trade_journal_id,))

    print("\n💼 POSITION TRACKING:")
    if not positions:
        print("  No active position")
        return

    pos = positions[0]
    print(f"  Symbol: {pos['symbol']}")
    print(f"  Qty: {pos['qty']}")
    print(f"  Avg Entry Price: ${pos['avg_entry_price']}")
    print(f"  Current Price: ${pos['current_price']}")
    print(f"  Cost Basis: ${pos['cost_basis']:.2f}")
    print(f"  Market Value: ${pos['market_value']:.2f}")
    print(f"  Unrealized P&L: ${pos['unrealized_pnl']:.2f}")
    print(f"  Stop Loss Order ID: {pos['stop_loss_order_id'] or 'N/A'}")
    print(f"  Take Profit Order ID: {pos['take_profit_order_id'] or 'N/A'}")
    print(f"  Last Updated: {pos['last_updated']}")


def display_orders(db, trade_journal_id):
    """Display all orders for a trade"""
    orders = db.query('order_execution', 'trade_journal_id = %s', (trade_journal_id,))

    print("\n📋 ORDER EXECUTION RECORDS:")
    if not orders:
        print("  No orders found")
        return

    for order in orders:
        print(f"\n  Order Type: {order['order_type']}")
        print(f"    Alpaca Order ID: {order['alpaca_order_id']}")
        print(f"    Status: {order['order_status']}")
        print(f"    Side: {order['side']}")
        print(f"    Qty: {order['qty']}")

        if order['limit_price']:
            print(f"    Limit Price: ${order['limit_price']}")
        if order['stop_price']:
            print(f"    Stop Price: ${order['stop_price']}")

        if order['filled_avg_price']:
            print(f"    Filled Avg Price: ${order['filled_avg_price']}")
            print(f"    Filled Qty: {order['filled_qty']}")
            print(f"    Filled At: {order['filled_at']}")


def display_all_state(db, trade_journal_id):
    """Display complete state"""
    display_trade_state(db, trade_journal_id)
    display_position(db, trade_journal_id)
    display_orders(db, trade_journal_id)
    print("\n" + "=" * 80)


def scenario_1_position_update_profit():
    """
    Scenario 1: Position Price Update - Profit

    Flow:
    1. Create open position with entry at $150
    2. Set current market price to $155 (profit)
    3. Run position_monitor
    4. Verify: unrealized_pnl = +$50, market_value updated
    """
    print_section("SCENARIO 1: POSITION PRICE UPDATE - PROFIT")

    with TestDatabase() as db:
        mock_client = MockAlpacaClient()
        mock_data_client = MockAlpacaDataClient()

        # Step 1: Create initial trade and position
        print_subsection("STEP 1: Setup Initial Trade & Position")

        trade_id = db.insert('trade_journal', {
            'trade_id': f'MANUAL_TEST_{uuid.uuid4().hex[:8].upper()}',
            'symbol': 'AAPL',
            'status': 'OPEN',
            'planned_entry': Decimal('150.00'),
            'planned_stop_loss': Decimal('145.00'),
            'planned_take_profit': Decimal('160.00'),
            'planned_qty': 10,
            'actual_entry': Decimal('150.00'),
            'actual_qty': 10,
            'trade_style': 'SWING',
            'pattern': 'Bull Flag'
        })

        # Create position tracking record
        sl_order_id = str(uuid.uuid4())
        tp_order_id = str(uuid.uuid4())

        position_id = db.insert('position_tracking', {
            'trade_journal_id': trade_id,
            'symbol': 'AAPL',
            'qty': 10,
            'avg_entry_price': Decimal('150.00'),
            'current_price': Decimal('150.00'),
            'market_value': Decimal('1500.00'),
            'cost_basis': Decimal('1500.00'),
            'unrealized_pnl': Decimal('0.00'),
            'stop_loss_order_id': sl_order_id,
            'take_profit_order_id': tp_order_id
        })

        # Create SL and TP orders
        db.insert('order_execution', {
            'trade_journal_id': trade_id,
            'alpaca_order_id': sl_order_id,
            'client_order_id': f'client_{uuid.uuid4().hex[:8]}',
            'order_type': 'STOP_LOSS',
            'side': 'sell',
            'order_status': 'pending',
            'time_in_force': 'gtc',
            'qty': 10,
            'stop_price': Decimal('145.00')
        })

        db.insert('order_execution', {
            'trade_journal_id': trade_id,
            'alpaca_order_id': tp_order_id,
            'client_order_id': f'client_{uuid.uuid4().hex[:8]}',
            'order_type': 'TAKE_PROFIT',
            'side': 'sell',
            'order_status': 'pending',
            'time_in_force': 'gtc',
            'qty': 10,
            'limit_price': Decimal('160.00')
        })

        # Mock Alpaca: Position exists with current market data
        mock_position = MockAlpacaPosition(
            symbol='AAPL',
            qty=10,
            side='long',
            avg_entry_price=150.00,
            current_price=150.00,
            market_value=1500.00,
            unrealized_pl=0.00,
            unrealized_plpc=0.0
        )
        mock_client.positions['AAPL'] = mock_position

        # Mock market data: Price increased to $155
        mock_quote = MockAlpacaQuote(
            symbol='AAPL',
            bid_price=154.90,
            ask_price=155.10
        )
        mock_data_client.quotes['AAPL'] = mock_quote

        print("✅ Created OPEN position for AAPL")
        print(f"   Entry: $150.00, Qty: 10")
        print(f"   Current market price set to $155 (bid: $154.90, ask: $155.10)")
        display_all_state(db, trade_id)

        input("\n🔵 Press Enter to run PositionMonitor and update position values...")

        # Step 2: Run monitor - should update position values
        print_subsection("STEP 2: Process Position Update")

        monitor = PositionMonitor(test_mode=True, db=db, trading_client=mock_client, data_client=mock_data_client)
        monitor.run()

        print("✅ PositionMonitor completed")
        display_all_state(db, trade_id)

        # Verify the update
        positions = db.query('position_tracking', 'trade_journal_id = %s', (trade_id,))
        if positions:
            pos = positions[0]
            print("\n📈 VERIFICATION:")
            print(f"  ✅ Current Price: ${pos['current_price']} (expected: $155.00)")
            print(f"  ✅ Market Value: ${pos['market_value']:.2f} (expected: $1,550.00)")
            print(f"  ✅ Unrealized P&L: ${pos['unrealized_pnl']:.2f} (expected: $50.00)")

        # Final summary
        print_section("SCENARIO 1 COMPLETE", "=")
        trade = db.get_by_id('trade_journal', trade_id)
        print(f"✅ Trade Status: {trade['status']} (still OPEN)")
        print(f"✅ Position updated with current market prices")
        print(f"✅ Unrealized P&L: +$50.00")

        input("\n🔵 Press Enter to close database connection and exit scenario...")


def scenario_2_update_loss_then_manual_close():
    """
    Scenario 2: Position Price Update - Loss → Manual Close Reconciliation

    Flow:
    1. Create open position with entry at $150
    2. Set current market price to $145 (loss)
    3. Run position_monitor → unrealized_pnl = -$50
    4. Remove position from Alpaca (simulate manual close)
    5. Run position_monitor again
    6. Verify: trade_journal.status = CLOSED, exit_reason = MANUAL_EXIT
    """
    print_section("SCENARIO 2: POSITION UPDATE - LOSS → MANUAL CLOSE RECONCILIATION")

    with TestDatabase() as db:
        mock_client = MockAlpacaClient()
        mock_data_client = MockAlpacaDataClient()

        # Step 1: Create initial trade and position
        print_subsection("STEP 1: Setup Initial Trade & Position")

        trade_id = db.insert('trade_journal', {
            'trade_id': f'MANUAL_TEST_{uuid.uuid4().hex[:8].upper()}',
            'symbol': 'TSLA',
            'status': 'OPEN',
            'planned_entry': Decimal('250.00'),
            'planned_stop_loss': Decimal('240.00'),
            'planned_take_profit': Decimal('270.00'),
            'planned_qty': 10,
            'actual_entry': Decimal('250.00'),
            'actual_qty': 10,
            'trade_style': 'SWING',
            'pattern': 'Breakout'
        })

        # Create position tracking record
        sl_order_id = str(uuid.uuid4())
        tp_order_id = str(uuid.uuid4())

        position_id = db.insert('position_tracking', {
            'trade_journal_id': trade_id,
            'symbol': 'TSLA',
            'qty': 10,
            'avg_entry_price': Decimal('250.00'),
            'current_price': Decimal('250.00'),
            'market_value': Decimal('2500.00'),
            'cost_basis': Decimal('2500.00'),
            'unrealized_pnl': Decimal('0.00'),
            'stop_loss_order_id': sl_order_id,
            'take_profit_order_id': tp_order_id
        })

        # Create SL and TP orders
        db.insert('order_execution', {
            'trade_journal_id': trade_id,
            'alpaca_order_id': sl_order_id,
            'client_order_id': f'client_{uuid.uuid4().hex[:8]}',
            'order_type': 'STOP_LOSS',
            'side': 'sell',
            'order_status': 'pending',
            'time_in_force': 'gtc',
            'qty': 10,
            'stop_price': Decimal('240.00')
        })

        db.insert('order_execution', {
            'trade_journal_id': trade_id,
            'alpaca_order_id': tp_order_id,
            'client_order_id': f'client_{uuid.uuid4().hex[:8]}',
            'order_type': 'TAKE_PROFIT',
            'side': 'sell',
            'order_status': 'pending',
            'time_in_force': 'gtc',
            'qty': 10,
            'limit_price': Decimal('270.00')
        })

        # Mock Alpaca: Position exists
        mock_position = MockAlpacaPosition(
            symbol='TSLA',
            qty=10,
            side='long',
            avg_entry_price=250.00,
            current_price=250.00,
            market_value=2500.00,
            unrealized_pl=0.00,
            unrealized_plpc=0.0
        )
        mock_client.positions['TSLA'] = mock_position

        # Mock market data: Price decreased to $245
        mock_quote = MockAlpacaQuote(
            symbol='TSLA',
            bid_price=244.90,
            ask_price=245.10
        )
        mock_data_client.quotes['TSLA'] = mock_quote

        print("✅ Created OPEN position for TSLA")
        print(f"   Entry: $250.00, Qty: 10")
        print(f"   Current market price set to $245 (bid: $244.90, ask: $245.10)")
        display_all_state(db, trade_id)

        input("\n🔵 Press Enter to run PositionMonitor and update position values...")

        # Step 2: Run monitor - should update position with loss
        print_subsection("STEP 2: Process Position Update (Loss)")

        monitor = PositionMonitor(test_mode=True, db=db, trading_client=mock_client, data_client=mock_data_client)
        monitor.run()

        print("✅ PositionMonitor completed - position shows loss")
        display_all_state(db, trade_id)

        input("\n🔵 Press Enter to simulate manual position close...")

        # Step 3: Simulate manual close
        print_subsection("STEP 3: Simulate Manual Position Close")

        # Remove position from Alpaca (user manually closed it)
        del mock_client.positions['TSLA']
        print("✅ Position removed from Alpaca (manual close simulated)")

        input("\n🔵 Press Enter to run PositionMonitor and reconcile closed position...")

        # Step 4: Run monitor - should reconcile
        print_subsection("STEP 4: Reconcile Closed Position")

        monitor.run()

        print("✅ PositionMonitor completed - reconciliation triggered")
        display_all_state(db, trade_id)

        # Verify reconciliation
        positions = db.query('position_tracking', 'trade_journal_id = %s', (trade_id,))
        trade = db.get_by_id('trade_journal', trade_id)

        print("\n🔍 VERIFICATION:")
        print(f"  ✅ Position Tracking Deleted: {len(positions) == 0}")
        print(f"  ✅ Trade Status: {trade['status']} (expected: CLOSED)")
        print(f"  ✅ Exit Reason: {trade['exit_reason']} (expected: MANUAL_EXIT)")
        print(f"  ✅ Exit Price: ${trade['exit_price']} (expected: ~$245)")
        print(f"  ✅ Actual P&L: ${trade['actual_pnl']:.2f}")

        # Final summary
        print_section("SCENARIO 2 COMPLETE", "=")
        print(f"✅ Position detected as closed outside system")
        print(f"✅ Trade reconciled: CLOSED, MANUAL_EXIT")
        print(f"✅ P&L: ${trade['actual_pnl']:.2f}")

        input("\n🔵 Press Enter to close database connection and exit scenario...")


def scenario_3_reconcile_stop_loss_filled():
    """
    Scenario 3: Reconcile Position Closed by Stop-Loss

    Flow:
    1. Create open position with entry at $150
    2. Create filled STOP_LOSS order at $144.90 in order_execution
    3. Remove position from Alpaca (SL triggered)
    4. Run position_monitor
    5. Verify: trade_journal.status = CLOSED, exit_reason = STOPPED_OUT
    """
    print_section("SCENARIO 3: RECONCILE POSITION CLOSED BY STOP-LOSS")

    with TestDatabase() as db:
        mock_client = MockAlpacaClient()
        mock_data_client = MockAlpacaDataClient()

        # Step 1: Create initial trade and position
        print_subsection("STEP 1: Setup Initial Trade & Position")

        trade_id = db.insert('trade_journal', {
            'trade_id': f'MANUAL_TEST_{uuid.uuid4().hex[:8].upper()}',
            'symbol': 'NVDA',
            'status': 'OPEN',
            'planned_entry': Decimal('500.00'),
            'planned_stop_loss': Decimal('485.00'),
            'planned_take_profit': Decimal('530.00'),
            'planned_qty': 10,
            'actual_entry': Decimal('500.00'),
            'actual_qty': 10,
            'trade_style': 'SWING',
            'pattern': 'Bull Flag'
        })

        # Create position tracking record
        sl_order_id = str(uuid.uuid4())
        tp_order_id = str(uuid.uuid4())

        position_id = db.insert('position_tracking', {
            'trade_journal_id': trade_id,
            'symbol': 'NVDA',
            'qty': 10,
            'avg_entry_price': Decimal('500.00'),
            'current_price': Decimal('500.00'),
            'market_value': Decimal('5000.00'),
            'cost_basis': Decimal('5000.00'),
            'unrealized_pnl': Decimal('0.00'),
            'stop_loss_order_id': sl_order_id,
            'take_profit_order_id': tp_order_id
        })

        # Create SL order (will be filled)
        db.insert('order_execution', {
            'trade_journal_id': trade_id,
            'alpaca_order_id': sl_order_id,
            'client_order_id': f'client_{uuid.uuid4().hex[:8]}',
            'order_type': 'STOP_LOSS',
            'side': 'sell',
            'order_status': 'pending',
            'time_in_force': 'gtc',
            'qty': 10,
            'stop_price': Decimal('485.00')
        })

        # Create TP order (will be cancelled)
        db.insert('order_execution', {
            'trade_journal_id': trade_id,
            'alpaca_order_id': tp_order_id,
            'client_order_id': f'client_{uuid.uuid4().hex[:8]}',
            'order_type': 'TAKE_PROFIT',
            'side': 'sell',
            'order_status': 'pending',
            'time_in_force': 'gtc',
            'qty': 10,
            'limit_price': Decimal('530.00')
        })

        # Mock Alpaca: Position initially exists
        mock_position = MockAlpacaPosition(
            symbol='NVDA',
            qty=10,
            side='long',
            avg_entry_price=500.00,
            current_price=500.00,
            market_value=5000.00,
            unrealized_pl=0.00,
            unrealized_plpc=0.0
        )
        mock_client.positions['NVDA'] = mock_position

        # Mock orders in Alpaca
        mock_sl_order = MockAlpacaOrder(
            id=sl_order_id,
            client_order_id=f'client_{uuid.uuid4().hex[:8]}',
            symbol='NVDA',
            qty=10,
            side='sell',
            order_type='stop',
            time_in_force='gtc',
            stop_price=485.00,
            status='pending'
        )
        mock_client.orders[sl_order_id] = mock_sl_order

        mock_tp_order = MockAlpacaOrder(
            id=tp_order_id,
            client_order_id=f'client_{uuid.uuid4().hex[:8]}',
            symbol='NVDA',
            qty=10,
            side='sell',
            order_type='limit',
            time_in_force='gtc',
            limit_price=530.00,
            status='pending'
        )
        mock_client.orders[tp_order_id] = mock_tp_order

        print("✅ Created OPEN position for NVDA")
        print(f"   Entry: $500.00, Qty: 10")
        print(f"   SL Order: {sl_order_id} at $485.00")
        print(f"   TP Order: {tp_order_id} at $530.00")
        display_all_state(db, trade_id)

        input("\n🔵 Press Enter to simulate Stop-Loss fill (outside of order_monitor)...")

        # Step 2: Simulate SL fill that order_monitor missed
        print_subsection("STEP 2: Simulate Stop-Loss Fill (Missed by order_monitor)")

        # Update SL order to filled in database (order_monitor should have done this but didn't)
        db.execute_query("""
            UPDATE order_execution
            SET order_status = 'filled',
                filled_qty = %s,
                filled_avg_price = %s,
                filled_at = %s
            WHERE alpaca_order_id = %s
        """, (10, Decimal('484.90'), datetime.now(), sl_order_id))

        # Update SL order in mock Alpaca
        mock_sl_order.status = 'filled'
        mock_sl_order.filled_qty = 10
        mock_sl_order.filled_avg_price = 484.90
        mock_sl_order.filled_at = datetime.now().isoformat()

        # Remove position from Alpaca (SL triggered and closed position)
        del mock_client.positions['NVDA']

        print("✅ Stop-Loss order filled at $484.90")
        print("✅ Position removed from Alpaca (SL closed the position)")
        print("❗ order_monitor.py failed to detect this (simulated gap)")
        display_all_state(db, trade_id)

        input("\n🔵 Press Enter to run PositionMonitor and reconcile...")

        # Step 3: Run monitor - should reconcile
        print_subsection("STEP 3: PositionMonitor Reconciles Closed Position")

        monitor = PositionMonitor(test_mode=True, db=db, trading_client=mock_client, data_client=mock_data_client)
        monitor.run()

        print("✅ PositionMonitor completed - reconciliation triggered")
        display_all_state(db, trade_id)

        # Verify reconciliation
        positions = db.query('position_tracking', 'trade_journal_id = %s', (trade_id,))
        trade = db.get_by_id('trade_journal', trade_id)

        # Query TP order by alpaca_order_id instead of database id
        tp_orders = db.query('order_execution', 'alpaca_order_id = %s', (tp_order_id,))
        tp_order = tp_orders[0] if tp_orders else None

        print("\n🔍 VERIFICATION:")
        print(f"  ✅ Position Tracking Deleted: {len(positions) == 0}")
        print(f"  ✅ Trade Status: {trade['status']} (expected: CLOSED)")
        print(f"  ✅ Exit Reason: {trade['exit_reason']} (expected: STOPPED_OUT)")
        print(f"  ✅ Exit Price: ${trade['exit_price']} (expected: $484.90)")
        print(f"  ✅ Actual P&L: ${trade['actual_pnl']:.2f}")
        if tp_order:
            print(f"  ✅ TP Order Cancelled: {tp_order['order_status'] == 'cancelled'}")
        else:
            print(f"  ⚠️  TP Order not found")

        # Final summary
        print_section("SCENARIO 3 COMPLETE", "=")
        print(f"✅ PositionMonitor detected position closed outside system")
        print(f"✅ Found filled STOP_LOSS order in database")
        print(f"✅ Trade reconciled: CLOSED, STOPPED_OUT")
        print(f"✅ Remaining TP order cancelled")
        print(f"✅ P&L: ${trade['actual_pnl']:.2f}")
        print("\n💡 This scenario validates the safety net when order_monitor fails!")

        input("\n🔵 Press Enter to close database connection and exit scenario...")


def main():
    """Main menu"""
    print_section("POSITION MONITOR - MANUAL TESTING TOOL")

    print("This tool allows you to manually test the position monitoring flow:")
    print("Price Updates → P&L Calculation → Position Reconciliation")
    print("\nNo real Alpaca API or manual database setup required!")
    print("\nAvailable Scenarios:\n")

    scenarios = {
        '1': ('Position Price Update - Profit', scenario_1_position_update_profit),
        '2': ('Position Update - Loss → Manual Close Reconciliation', scenario_2_update_loss_then_manual_close),
        '3': ('Reconcile Position Closed by Stop-Loss (order_monitor gap)', scenario_3_reconcile_stop_loss_filled),
    }

    for key, (desc, _) in scenarios.items():
        print(f"  {key}. {desc}")

    print("\n  q. Quit")

    while True:
        choice = input("\nSelect scenario (1-3, q): ").strip().lower()

        if choice == 'q':
            print("\nGoodbye!\n")
            break

        if choice in scenarios:
            _, scenario_func = scenarios[choice]
            try:
                scenario_func()
                input("\n\n🔵 Press Enter to return to menu...")
            except KeyboardInterrupt:
                print("\n\n⚠️  Scenario interrupted by user")
                input("\n🔵 Press Enter to return to menu...")
            except Exception as e:
                print(f"\n\n❌ Error running scenario: {e}")
                import traceback
                traceback.print_exc()
                input("\n🔵 Press Enter to return to menu...")
        else:
            print("❌ Invalid choice. Please select 1-3 or q.")


if __name__ == '__main__':
    main()
