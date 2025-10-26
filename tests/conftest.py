"""
pytest fixtures for trading system tests
Uses testing.postgresql to provide isolated, in-memory PostgreSQL instances
"""
import pytest
import testing.postgresql
import os
import sys

# Add parent directory to path for imports
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from db_layer import TradingDB


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

    # Cleanup
    db.close()


@pytest.fixture
def sample_analysis_decision():
    """Sample analysis decision data for testing"""
    return {
        "Analysis Id": "TEST_001",
        "Ticker": "AAPL",
        "Decision": {
            "action": "BUY",
            "primary_action": "NEW_TRADE",
            "qty": 10,
            "entry_price": 150.00,
            "stop_loss": 145.00,
            "take_profit": 160.00,
            "trade_style": "SWING",
            "pattern": "Breakout"
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
