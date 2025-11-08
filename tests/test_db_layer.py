"""
Unit tests for database layer
Tests basic CRUD operations and schema creation
"""
import pytest
from db_layer import TradingDB


def test_database_connection(test_db):
    """Test database connection is established"""
    assert test_db.conn is not None
    assert test_db.conn.closed == 0  # 0 means connection is open


def test_schema_creation(test_db):
    """Test all tables are created"""
    # Query for table names
    tables = test_db.execute_query("""
        SELECT table_name FROM information_schema.tables
        WHERE table_schema = 'public'
    """)

    table_names = [t['table_name'] for t in tables]

    # Verify all required tables exist
    assert 'analysis_decision' in table_names
    assert 'trade_journal' in table_names
    assert 'order_execution' in table_names
    assert 'position_tracking' in table_names


def test_insert_record(test_db, sample_trade_journal):
    """Test inserting a record"""
    trade_id = test_db.insert('trade_journal', sample_trade_journal)

    assert trade_id is not None
    assert isinstance(trade_id, int)
    assert trade_id > 0


def test_get_by_id(test_db, sample_trade_journal):
    """Test getting a record by ID"""
    # Insert a record
    trade_id = test_db.insert('trade_journal', sample_trade_journal)

    # Retrieve it
    record = test_db.get_by_id('trade_journal', trade_id)

    assert record is not None
    assert record['id'] == trade_id
    assert record['symbol'] == 'AAPL'
    assert record['trade_style'] == 'SWING'


def test_update_record(test_db, sample_trade_journal):
    """Test updating a record"""
    # Insert a record
    trade_id = test_db.insert('trade_journal', sample_trade_journal)

    # Update it
    updated = test_db.update('trade_journal', trade_id, {
        'status': 'POSITION',
        'actual_entry': 151.25,
        'actual_qty': 10
    })

    assert updated is True

    # Verify update
    record = test_db.get_by_id('trade_journal', trade_id)
    assert record['status'] == 'POSITION'
    assert float(record['actual_entry']) == 151.25
    assert record['actual_qty'] == 10


def test_query_with_where(test_db, sample_trade_journal):
    """Test querying with WHERE clause"""
    # Insert multiple records
    sample_trade_journal['symbol'] = 'AAPL'
    test_db.insert('trade_journal', sample_trade_journal)

    sample_trade_journal['trade_id'] = 'MSFT_20251026120001'
    sample_trade_journal['symbol'] = 'MSFT'
    test_db.insert('trade_journal', sample_trade_journal)

    # Query for AAPL only
    results = test_db.query('trade_journal', 'symbol = %s', ('AAPL',))

    assert len(results) == 1
    assert results[0]['symbol'] == 'AAPL'


def test_execute_query(test_db, sample_trade_journal):
    """Test execute_query method"""
    # Insert a record
    test_db.insert('trade_journal', sample_trade_journal)

    # Query it
    results = test_db.execute_query(
        "SELECT * FROM trade_journal WHERE symbol = %s",
        ('AAPL',)
    )

    assert len(results) > 0
    assert results[0]['symbol'] == 'AAPL'


def test_execute_update(test_db, sample_trade_journal):
    """Test execute_update method"""
    # Insert a record
    trade_id = test_db.insert('trade_journal', sample_trade_journal)

    # Update using execute_update
    rows_affected = test_db.execute_update(
        "UPDATE trade_journal SET status = %s WHERE id = %s",
        ('CLOSED', trade_id)
    )

    assert rows_affected == 1

    # Verify
    record = test_db.get_by_id('trade_journal', trade_id)
    assert record['status'] == 'CLOSED'


def test_insert_analysis_decision_with_json(test_db, sample_analysis_decision):
    """Test inserting analysis_decision with JSONB field"""
    import json

    # Convert decision dict to JSON string for insertion
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

    # Query it back
    results = test_db.execute_query(
        'SELECT * FROM analysis_decision WHERE "Analysis_Id" = %s',
        ('TEST_001',)
    )

    assert len(results) == 1
    assert results[0]['Ticker'] == 'AAPL'
    assert results[0]['Decision']['action'] == 'BUY'
    assert results[0]['Decision']['qty'] == 10
