"""
pytest fixtures for trading system tests
Uses testing.postgresql to provide isolated, in-memory PostgreSQL instances
"""
import pytest
import testing.postgresql
import os
import sys
import uuid

# Add parent directory and shared directory to path for imports
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))

from shared.database import TradingDB


@pytest.fixture(scope='session')
def postgresql_instance():
    """Create a temporary PostgreSQL instance for all tests"""
    postgresql = testing.postgresql.Postgresql()
    yield postgresql
    postgresql.stop()


@pytest.fixture
def test_db(postgresql_instance):
    """
    Create database with schema for each test
    Provides a clean database instance for each test
    """
    # Set test environment variables
    dsn = postgresql_instance.dsn()
    os.environ['TEST_POSTGRES_HOST'] = dsn['host']
    os.environ['TEST_POSTGRES_PORT'] = str(dsn['port'])
    os.environ['TEST_POSTGRES_DB'] = dsn['database']
    os.environ['TEST_POSTGRES_USER'] = dsn['user']
    os.environ['TEST_POSTGRES_PASSWORD'] = ''

    # Create database connection
    db = TradingDB(test_mode=True)

    # Create schema
    db.create_schema()

    yield db

    # Cleanup - truncate all tables to ensure test isolation
    try:
        db.execute_query("""
            TRUNCATE TABLE position_tracking, order_execution, trade_journal, analysis_decision RESTART IDENTITY CASCADE
        """)
    except Exception as e:
        # If truncate fails, it's okay - the connection will be closed anyway
        pass

    db.close()


@pytest.fixture
def sample_analysis_decision():
    """Sample analysis decision data for testing - NEW JSON STRUCTURE"""
    return {
        "Analysis_Id": "TEST_001",
        "Ticker": "AAPL",
        "Decision": {
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
        },
        "executed": False,
        "Approve": True
    }


@pytest.fixture
def sample_trade_journal():
    """Sample trade journal data for testing"""
    return {
        "trade_id": "AAPL_20251026120000",
        "symbol": "AAPL",
        "trade_style": "SWING",
        "pattern": "Breakout",
        "status": "ORDERED",
        "initial_analysis_id": "TEST_001",
        "planned_entry": 150.00,
        "planned_stop_loss": 145.00,
        "planned_take_profit": 160.00,
        "planned_qty": 10
    }


@pytest.fixture
def sample_order_execution():
    """Sample order execution data for testing"""
    return {
        "trade_journal_id": 1,
        "analysis_decision_id": "TEST_001",
        "alpaca_order_id": "test-order-123",
        "order_type": "ENTRY",
        "side": "buy",
        "order_status": "pending",
        "time_in_force": "day",
        "qty": 10,
        "limit_price": 150.00
    }


# ============================================================================
# Mock Alpaca API Fixtures
# ============================================================================

class MockAlpacaOrder:
    """Mock Alpaca Order object"""
    def __init__(self, id, client_order_id, symbol, qty, side, order_type,
                 time_in_force, limit_price=None, stop_price=None, filled_avg_price=None,
                 status='pending', filled_qty=0, filled_at=None):
        self.id = id
        self.client_order_id = client_order_id
        self.symbol = symbol
        self.qty = str(qty)  # Alpaca returns as string
        self.side = side
        self.order_type = order_type
        self.time_in_force = time_in_force
        self.limit_price = limit_price
        self.stop_price = stop_price
        self.filled_avg_price = filled_avg_price
        self.status = status
        self.filled_qty = str(filled_qty)
        self.filled_at = filled_at
        self.created_at = "2025-10-26T09:45:00Z"
        self.updated_at = "2025-10-26T09:45:00Z"


class MockAlpacaPosition:
    """Mock Alpaca Position object"""
    def __init__(self, symbol, qty, side, avg_entry_price, current_price,
                 market_value, unrealized_pl, unrealized_plpc):
        self.symbol = symbol
        self.qty = str(qty)
        self.side = side
        self.avg_entry_price = str(avg_entry_price)
        self.current_price = str(current_price)
        self.market_value = str(market_value)
        self.unrealized_pl = str(unrealized_pl)
        self.unrealized_plpc = str(unrealized_plpc)


class MockAlpacaBar:
    """Mock Alpaca Bar (market data)"""
    def __init__(self, symbol, close, high, low, open, volume):
        self.symbol = symbol
        self.close = close
        self.high = high
        self.low = low
        self.open = open
        self.volume = volume


class MockAlpacaClient:
    """Mock Alpaca Trading Client for testing"""
    def __init__(self):
        self.orders = {}
        self.positions = {}
        self.next_order_id = 1

    def submit_order(self, order_request):
        """Mock submit_order - returns UUID objects like real Alpaca API"""
        order_id = uuid.uuid4()  # Generate UUID like real Alpaca API
        client_order_id = uuid.uuid4()
        self.next_order_id += 1

        order = MockAlpacaOrder(
            id=order_id,
            client_order_id=client_order_id,
            symbol=order_request.symbol,
            qty=order_request.qty,
            side=order_request.side.value,
            order_type=order_request.order_type.value if hasattr(order_request, 'order_type') else 'limit',
            time_in_force=order_request.time_in_force.value,
            limit_price=getattr(order_request, 'limit_price', None),
            status='pending'
        )

        self.orders[str(order_id)] = order  # Use string as dict key
        return order

    def get_order_by_id(self, order_id):
        """Mock get_order_by_id"""
        if order_id not in self.orders:
            raise Exception(f"Order {order_id} not found")
        return self.orders[order_id]

    def get_orders(self, filter=None):
        """Mock get_orders"""
        return list(self.orders.values())

    def cancel_order_by_id(self, order_id):
        """Mock cancel_order_by_id"""
        if order_id not in self.orders:
            raise Exception(f"Order {order_id} not found")
        self.orders[order_id].status = 'cancelled'
        return True

    def get_all_positions(self):
        """Mock get_all_positions"""
        return list(self.positions.values())

    def get_open_position(self, symbol):
        """Mock get_open_position"""
        if symbol not in self.positions:
            raise Exception(f"Position {symbol} not found")
        return self.positions[symbol]

    def close_position(self, symbol):
        """Mock close_position"""
        if symbol in self.positions:
            del self.positions[symbol]
        return True


@pytest.fixture
def mock_alpaca_client():
    """Provide a mock Alpaca client for testing"""
    return MockAlpacaClient()


@pytest.fixture
def mock_pending_order():
    """Mock pending order - uses UUID objects like real Alpaca API"""
    return MockAlpacaOrder(
        id=uuid.uuid4(),
        client_order_id=uuid.uuid4(),
        symbol="AAPL",
        qty=10,
        side="buy",
        order_type="limit",
        time_in_force="day",
        limit_price=150.00,
        status="pending"
    )


@pytest.fixture
def mock_filled_order():
    """Mock filled order - uses UUID objects like real Alpaca API"""
    return MockAlpacaOrder(
        id=uuid.uuid4(),
        client_order_id=uuid.uuid4(),
        symbol="AAPL",
        qty=10,
        side="buy",
        order_type="limit",
        time_in_force="day",
        limit_price=150.00,
        filled_avg_price=150.25,
        status="filled",
        filled_qty=10
    )


@pytest.fixture
def mock_cancelled_order():
    """Mock cancelled order - uses UUID objects like real Alpaca API"""
    return MockAlpacaOrder(
        id=uuid.uuid4(),
        client_order_id=uuid.uuid4(),
        symbol="AAPL",
        qty=10,
        side="buy",
        order_type="limit",
        time_in_force="day",
        limit_price=150.00,
        status="cancelled"
    )


@pytest.fixture
def mock_position():
    """Mock Alpaca position"""
    return MockAlpacaPosition(
        symbol="AAPL",
        qty=10,
        side="long",
        avg_entry_price=150.25,
        current_price=155.00,
        market_value=1550.00,
        unrealized_pl=47.50,
        unrealized_plpc=0.0316
    )


class MockAlpacaQuote:
    """Mock Alpaca Quote for market data"""
    def __init__(self, symbol, bid_price, ask_price):
        self.symbol = symbol
        self.bid_price = bid_price
        self.ask_price = ask_price


class MockAlpacaDataClient:
    """Mock Alpaca Data Client for market data"""
    def __init__(self):
        self.quotes = {}

    def get_stock_latest_quote(self, request):
        """Mock get_stock_latest_quote"""
        symbol = request.symbol_or_symbols
        if symbol in self.quotes:
            return {symbol: self.quotes[symbol]}
        # Default quote
        return {symbol: MockAlpacaQuote(symbol, 100.0, 100.5)}

    def add_quote(self, symbol, bid_price, ask_price):
        """Helper to add quotes for testing"""
        self.quotes[symbol] = MockAlpacaQuote(symbol, bid_price, ask_price)


@pytest.fixture
def mock_data_client():
    """Provide a mock Alpaca data client for testing"""
    return MockAlpacaDataClient()
