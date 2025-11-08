#!/usr/bin/env python3
"""
Manual Test Script for order_monitor.py - Complete Flow Testing
No real Alpaca API or manual database setup required!

This script uses:
- testing.postgresql (auto-creates temporary database)
- MockAlpacaClient (simulates Alpaca API)

Just run: python manual_test_complete_flow.py
"""
import sys
import os
import uuid
from datetime import datetime
from decimal import Decimal

# Add tests directory to path to import conftest
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'tests'))

import testing.postgresql
from conftest import MockAlpacaClient, MockAlpacaOrder
from db_layer import TradingDB
from order_monitor import OrderMonitor


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
    print(f"  Planned Entry: ${trade['planned_entry']}")
    print(f"  Planned Stop Loss: ${trade['planned_stop_loss']}")
    print(f"  Planned Take Profit: ${trade['planned_take_profit'] or 'N/A'}")
    print(f"  Actual Entry: ${trade['actual_entry'] or 'N/A'}")
    print(f"  Actual Qty: {trade['actual_qty'] or 'N/A'}")

    if trade['status'] == 'CLOSED':
        print(f"  Exit Price: ${trade['exit_price']}")
        print(f"  Actual P&L: ${trade['actual_pnl']:.2f}")
        print(f"  Exit Reason: {trade['exit_reason']}")


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


def display_all_state(db, trade_journal_id):
    """Display complete state"""
    display_trade_state(db, trade_journal_id)
    display_orders(db, trade_journal_id)
    display_position(db, trade_journal_id)
    print("\n" + "=" * 80)


def scenario_1_swing_sl_hit():
    """
    Scenario 1: SWING Trade - Stop-Loss Hit

    Flow:
    1. Entry order fills
    2. Position created, SL and TP orders placed
    3. Stop-loss order fills
    4. Trade closed, TP order cancelled
    """
    print_section("SCENARIO 1: SWING TRADE - STOP-LOSS HIT")

    with TestDatabase() as db:
        mock_client = MockAlpacaClient()

        # Step 1: Create initial trade
        print_subsection("STEP 1: Setup Initial Trade")

        trade_id = db.insert('trade_journal', {
            'trade_id': f'MANUAL_TEST_{uuid.uuid4().hex[:8].upper()}',
            'symbol': 'AAPL',
            'status': 'ORDERED',
            'planned_entry': Decimal('150.00'),
            'planned_stop_loss': Decimal('145.00'),
            'planned_take_profit': Decimal('160.00'),
            'planned_qty': 10,
            'trade_style': 'SWING',
            'pattern': 'Bull Flag'
        })

        # Create entry order in database
        entry_order_id = str(uuid.uuid4())
        db.insert('order_execution', {
            'trade_journal_id': trade_id,
            'alpaca_order_id': entry_order_id,
            'client_order_id': f'client_{uuid.uuid4().hex[:8]}',
            'order_type': 'ENTRY',
            'side': 'buy',
            'order_status': 'pending',
            'time_in_force': 'day',
            'qty': 10,
            'limit_price': Decimal('150.00')
        })

        # Mock Alpaca: Entry order is filled
        entry_order = MockAlpacaOrder(
            id=entry_order_id,
            client_order_id=f'client_{uuid.uuid4().hex[:8]}',
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
        entry_order.filled_at = datetime.now().isoformat()
        mock_client.orders[entry_order_id] = entry_order

        print("✅ Created SWING trade for AAPL")
        print(f"   Entry order {entry_order_id} set to 'filled' in mock Alpaca")
        display_all_state(db, trade_id)

        input("\n🔵 Press Enter to run OrderMonitor and process entry fill...")

        # Step 2: Run monitor - should create position and place SL/TP
        print_subsection("STEP 2: Process Entry Fill")

        monitor = OrderMonitor(test_mode=True, db=db, alpaca_client=mock_client)
        monitor.run()

        print("✅ OrderMonitor completed")
        display_all_state(db, trade_id)

        # Get the SL order ID that was just placed
        sl_orders = db.query('order_execution',
                            'trade_journal_id = %s AND order_type = %s',
                            (trade_id, 'STOP_LOSS'))
        sl_order_id = sl_orders[0]['alpaca_order_id'] if sl_orders else None

        input("\n🔵 Press Enter to trigger Stop-Loss fill...")

        # Step 3: Trigger stop-loss
        print_subsection("STEP 3: Trigger Stop-Loss")

        if sl_order_id:
            # Update SL order in mock Alpaca to filled
            sl_order = mock_client.orders[sl_order_id]
            sl_order.status = 'filled'
            sl_order.filled_qty = 10
            sl_order.filled_avg_price = 144.90
            sl_order.filled_at = datetime.now().isoformat()

            print(f"✅ Stop-loss order {sl_order_id} set to 'filled' at $144.90")

        input("\n🔵 Press Enter to run OrderMonitor and process SL fill...")

        # Step 4: Run monitor - should close trade and cancel TP
        print_subsection("STEP 4: Process Stop-Loss Fill")

        monitor.run()

        print("✅ OrderMonitor completed")
        display_all_state(db, trade_id)

        # Final summary
        print_section("SCENARIO 1 COMPLETE", "=")
        trade = db.get_by_id('trade_journal', trade_id)
        print(f"✅ Trade Status: {trade['status']}")
        print(f"✅ Exit Reason: {trade['exit_reason']}")
        print(f"✅ P&L: ${trade['actual_pnl']:.2f}")
        print(f"✅ Entry: ${trade['actual_entry']} → Exit: ${trade['exit_price']}")

        input("\n🔵 Press Enter to close database connection and exit scenario...")


def scenario_2_swing_tp_hit():
    """
    Scenario 2: SWING Trade - Take-Profit Hit

    Flow:
    1. Entry order fills
    2. Position created, SL and TP orders placed
    3. Take-profit order fills
    4. Trade closed, SL order cancelled
    """
    print_section("SCENARIO 2: SWING TRADE - TAKE-PROFIT HIT")

    with TestDatabase() as db:
        mock_client = MockAlpacaClient()

        # Step 1: Create initial trade
        print_subsection("STEP 1: Setup Initial Trade")

        trade_id = db.insert('trade_journal', {
            'trade_id': f'MANUAL_TEST_{uuid.uuid4().hex[:8].upper()}',
            'symbol': 'TSLA',
            'status': 'ORDERED',
            'planned_entry': Decimal('250.00'),
            'planned_stop_loss': Decimal('240.00'),
            'planned_take_profit': Decimal('270.00'),
            'planned_qty': 5,
            'trade_style': 'SWING',
            'pattern': 'Breakout'
        })

        # Create entry order
        entry_order_id = str(uuid.uuid4())
        db.insert('order_execution', {
            'trade_journal_id': trade_id,
            'alpaca_order_id': entry_order_id,
            'client_order_id': f'client_{uuid.uuid4().hex[:8]}',
            'order_type': 'ENTRY',
            'side': 'buy',
            'order_status': 'pending',
            'time_in_force': 'day',
            'qty': 5,
            'limit_price': Decimal('250.00')
        })

        # Mock entry filled
        entry_order = MockAlpacaOrder(
            id=entry_order_id,
            client_order_id=f'client_{uuid.uuid4().hex[:8]}',
            symbol='TSLA',
            qty=5,
            side='buy',
            order_type='limit',
            time_in_force='day',
            limit_price=250.00,
            filled_avg_price=249.75,
            status='filled',
            filled_qty=5
        )
        entry_order.filled_at = datetime.now().isoformat()
        mock_client.orders[entry_order_id] = entry_order

        print("✅ Created SWING trade for TSLA")
        display_all_state(db, trade_id)

        input("\n🔵 Press Enter to run OrderMonitor and process entry fill...")

        # Step 2: Process entry
        print_subsection("STEP 2: Process Entry Fill")

        monitor = OrderMonitor(test_mode=True, db=db, alpaca_client=mock_client)
        monitor.run()

        print("✅ OrderMonitor completed")
        display_all_state(db, trade_id)

        # Get the TP order ID
        tp_orders = db.query('order_execution',
                            'trade_journal_id = %s AND order_type = %s',
                            (trade_id, 'TAKE_PROFIT'))
        tp_order_id = tp_orders[0]['alpaca_order_id'] if tp_orders else None

        input("\n🔵 Press Enter to trigger Take-Profit fill...")

        # Step 3: Trigger take-profit
        print_subsection("STEP 3: Trigger Take-Profit")

        if tp_order_id:
            tp_order = mock_client.orders[tp_order_id]
            tp_order.status = 'filled'
            tp_order.filled_qty = 5
            tp_order.filled_avg_price = 270.50
            tp_order.filled_at = datetime.now().isoformat()

            print(f"✅ Take-profit order {tp_order_id} set to 'filled' at $270.50")

        input("\n🔵 Press Enter to run OrderMonitor and process TP fill...")

        # Step 4: Process TP fill
        print_subsection("STEP 4: Process Take-Profit Fill")

        monitor.run()

        print("✅ OrderMonitor completed")
        display_all_state(db, trade_id)

        # Final summary
        print_section("SCENARIO 2 COMPLETE", "=")
        trade = db.get_by_id('trade_journal', trade_id)
        print(f"✅ Trade Status: {trade['status']}")
        print(f"✅ Exit Reason: {trade['exit_reason']}")
        print(f"✅ P&L: ${trade['actual_pnl']:.2f}")
        print(f"✅ Entry: ${trade['actual_entry']} → Exit: ${trade['exit_price']}")

        input("\n🔵 Press Enter to close database connection and exit scenario...")


def scenario_3_trend_sl_only():
    """
    Scenario 3: TREND Trade - Only Stop-Loss (No TP)

    Flow:
    1. Entry order fills
    2. Position created, only SL order placed (no TP for TREND)
    3. Stop-loss order fills
    4. Trade closed
    """
    print_section("SCENARIO 3: TREND TRADE - ONLY STOP-LOSS (NO TP)")

    with TestDatabase() as db:
        mock_client = MockAlpacaClient()

        # Step 1: Create initial trade
        print_subsection("STEP 1: Setup Initial Trade")

        trade_id = db.insert('trade_journal', {
            'trade_id': f'MANUAL_TEST_{uuid.uuid4().hex[:8].upper()}',
            'symbol': 'NVDA',
            'status': 'ORDERED',
            'planned_entry': Decimal('500.00'),
            'planned_stop_loss': Decimal('485.00'),
            'planned_take_profit': None,  # No TP for TREND
            'planned_qty': 8,
            'trade_style': 'TREND',  # Changed from DAYTRADE
            'pattern': 'Uptrend'
        })

        # Create entry order
        entry_order_id = str(uuid.uuid4())
        db.insert('order_execution', {
            'trade_journal_id': trade_id,
            'alpaca_order_id': entry_order_id,
            'client_order_id': f'client_{uuid.uuid4().hex[:8]}',
            'order_type': 'ENTRY',
            'side': 'buy',
            'order_status': 'pending',
            'time_in_force': 'day',
            'qty': 8,
            'limit_price': Decimal('500.00')
        })

        # Mock entry filled
        entry_order = MockAlpacaOrder(
            id=entry_order_id,
            client_order_id=f'client_{uuid.uuid4().hex[:8]}',
            symbol='NVDA',
            qty=8,
            side='buy',
            order_type='limit',
            time_in_force='day',
            limit_price=500.00,
            filled_avg_price=499.50,
            status='filled',
            filled_qty=8
        )
        entry_order.filled_at = datetime.now().isoformat()
        mock_client.orders[entry_order_id] = entry_order

        print("✅ Created TREND trade for NVDA")
        print("   Note: TREND trades do not have take-profit targets")
        display_all_state(db, trade_id)

        input("\n🔵 Press Enter to run OrderMonitor and process entry fill...")

        # Step 2: Process entry
        print_subsection("STEP 2: Process Entry Fill")

        monitor = OrderMonitor(test_mode=True, db=db, alpaca_client=mock_client)
        monitor.run()

        print("✅ OrderMonitor completed")
        print("   Should see: SL order placed, NO TP order")
        display_all_state(db, trade_id)

        # Verify no TP order was created
        tp_orders = db.query('order_execution',
                            'trade_journal_id = %s AND order_type = %s',
                            (trade_id, 'TAKE_PROFIT'))
        sl_orders = db.query('order_execution',
                            'trade_journal_id = %s AND order_type = %s',
                            (trade_id, 'STOP_LOSS'))

        print(f"\n   Verification:")
        print(f"   - Stop-Loss orders: {len(sl_orders)}")
        print(f"   - Take-Profit orders: {len(tp_orders)}")

        sl_order_id = sl_orders[0]['alpaca_order_id'] if sl_orders else None

        input("\n🔵 Press Enter to trigger Stop-Loss fill...")

        # Step 3: Trigger stop-loss
        print_subsection("STEP 3: Trigger Stop-Loss")

        if sl_order_id:
            sl_order = mock_client.orders[sl_order_id]
            sl_order.status = 'filled'
            sl_order.filled_qty = 8
            sl_order.filled_avg_price = 485.25
            sl_order.filled_at = datetime.now().isoformat()

            print(f"✅ Stop-loss order {sl_order_id} set to 'filled' at $485.25")

        input("\n🔵 Press Enter to run OrderMonitor and process SL fill...")

        # Step 4: Process SL fill
        print_subsection("STEP 4: Process Stop-Loss Fill")

        monitor.run()

        print("✅ OrderMonitor completed")
        display_all_state(db, trade_id)

        # Final summary
        print_section("SCENARIO 3 COMPLETE", "=")
        trade = db.get_by_id('trade_journal', trade_id)
        print(f"✅ Trade Status: {trade['status']}")
        print(f"✅ Exit Reason: {trade['exit_reason']}")
        print(f"✅ P&L: ${trade['actual_pnl']:.2f}")
        print(f"✅ Entry: ${trade['actual_entry']} → Exit: ${trade['exit_price']}")

        input("\n🔵 Press Enter to close database connection and exit scenario...")


def main():
    """Main menu"""
    print_section("ORDER MONITOR - MANUAL TESTING TOOL")

    print("This tool allows you to manually test the complete order flow:")
    print("Entry → Position → SL/TP Placement → Exit → Close")
    print("\nNo real Alpaca API or manual database setup required!")
    print("\nAvailable Scenarios:\n")

    scenarios = {
        '1': ('SWING Trade - Stop-Loss Hit', scenario_1_swing_sl_hit),
        '2': ('SWING Trade - Take-Profit Hit', scenario_2_swing_tp_hit),
        '3': ('TREND Trade - Only Stop-Loss (No TP)', scenario_3_trend_sl_only),
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
