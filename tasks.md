# Trading System Monitoring - Implementation Tasks

## Project Overview
Building a Python-based trading system that monitors the complete trading lifecycle: Analysis → Decision → Trade Plan → Order → Position. The system replaces n8n workflows with scheduled Python programs that interact with NocoDB (PostgreSQL) for data persistence and Alpaca API for order execution.

**Full PRD**: [trading-monitor-prd.md](trading-monitor-prd.md)

---

## Progress Tracking

- **Total Tasks**: 38
- **Completed**: 0
- **In Progress**: 0
- **Blocked**: 0

---

## Pre-requisites

Before starting implementation:

- [ ] Alpaca Paper Trading account created ([alpaca.markets](https://alpaca.markets))
- [ ] Alpaca API keys generated (paper trading)
- [ ] NocoDB instance running with access to underlying PostgreSQL
- [ ] PostgreSQL connection credentials available
- [ ] Python 3.9+ installed on development machine
- [ ] Git repository initialized (optional but recommended)

---

# PHASE 1: Foundation & Database Setup

## TASK-001: Setup Project Environment

**Phase**: Foundation
**Complexity**: Low
**Dependencies**: None

### Description
Initialize the Python project structure with virtual environment and install all required dependencies, including testing.postgresql for in-memory database testing.

### Steps
1. Create project directory structure
2. Initialize virtual environment
3. Create requirements.txt with all dependencies:
   - alpaca-py
   - psycopg2-binary
   - python-dotenv
   - APScheduler
   - pytz
   - testing.postgresql (for in-memory tests)
   - pytest
4. Install dependencies
5. Create .env.example file
6. Create .gitignore

### Acceptance Criteria
- [ ] Virtual environment activated successfully
- [ ] All dependencies installed without errors
- [ ] .env.example file contains all required variables
- [ ] Can import alpaca-py, psycopg2, APScheduler, testing.postgresql
- [ ] pytest command works
- [ ] .gitignore includes .env, venv/, __pycache__/

### Files to Create
- `requirements.txt`
- `.env.example`
- `.gitignore`

### Verification
```bash
source venv/bin/activate
pip list | grep alpaca-py
pip list | grep testing.postgresql
python -c "import alpaca, psycopg2, pytest"
```

---

## TASK-002: Create Environment Configuration

**Phase**: Foundation
**Complexity**: Low
**Dependencies**: TASK-001

### Description
Create configuration module to load environment variables and provide database configuration based on mode (production vs test).

### Steps
1. Create config.py with environment variable loading
2. Implement `get_postgres_config(test_mode=False)` function
3. Add Alpaca API configuration
4. Add trading schedule configuration
5. Create .env file from template (not committed to git)

### Acceptance Criteria
- [ ] config.py loads all required environment variables
- [ ] Supports both production and test database configurations
- [ ] .env file contains all required variables
- [ ] Can import and use config without errors

### Files to Create
- `config.py`
- `.env` (from .env.example, not committed)

### Verification
```python
from config import get_postgres_config, ALPACA_API_KEY
print(get_postgres_config(test_mode=False))
print(get_postgres_config(test_mode=True))
assert ALPACA_API_KEY is not None
```

---

## TASK-003: Implement Database Abstraction Layer

**Phase**: Foundation
**Complexity**: Medium
**Dependencies**: TASK-002

### Description
Create the TradingDB class that provides PostgreSQL abstraction with support for both production (NocoDB) and test databases.

### Steps
1. Create db_layer.py with TradingDB class
2. Implement connection management with test_mode parameter
3. Implement basic CRUD methods:
   - `execute_query()` - SELECT queries
   - `execute_update()` - INSERT/UPDATE/DELETE
   - `insert()` - Insert and return ID
   - `update()` - Update by ID
   - `get_by_id()` - Get single record
   - `query()` - Query with WHERE clause
4. Add proper error handling and logging
5. Add connection cleanup method

### Acceptance Criteria
- [ ] TradingDB class connects successfully to PostgreSQL
- [ ] All CRUD methods work correctly
- [ ] Supports both test_mode and production mode
- [ ] Proper error handling for connection failures
- [ ] Logging configured for database operations
- [ ] Returns results as list of dicts (using RealDictCursor)

### Files to Create
- `db_layer.py`

### Verification
```python
from db_layer import TradingDB
db = TradingDB()  # Production mode
db.connect()
result = db.execute_query("SELECT 1 as value")
assert result[0]['value'] == 1
db.close()
```

---

## TASK-004: Implement Database Schema Creation

**Phase**: Foundation
**Complexity**: Medium
**Dependencies**: TASK-003

### Description
Add `create_schema()` method to TradingDB class that creates all required tables for testing/development. This includes the complete `analysis_decision` table and all new tables.

### Steps
1. Add `create_schema()` method to TradingDB class
2. Create SQL schema for all tables:
   - `analysis_decision` (complete table with all fields)
   - `trade_journal`
   - `order_execution`
   - `position_tracking`
3. **IMPORTANT**: Do NOT create foreign key constraints (NocoDB doesn't support them)
4. Create indices for performance:
   - analysis_decision: executed, ticker
   - trade_journal: status, symbol, initial_analysis_id
   - order_execution: order_status, trade_journal_id
   - position_tracking: symbol, trade_journal_id
5. Add proper error handling and transaction management

### Acceptance Criteria
- [ ] create_schema() creates all tables successfully
- [ ] All tables have correct column types
- [ ] No foreign key constraints created
- [ ] Indices created for key lookup columns
- [ ] Can run create_schema() multiple times (IF NOT EXISTS)
- [ ] Works with empty PostgreSQL database

### Files to Modify
- `db_layer.py`

### Verification
```python
from db_layer import TradingDB
db = TradingDB(test_mode=True)
db.create_schema()

# Verify tables exist
tables = db.execute_query("""
    SELECT table_name FROM information_schema.tables
    WHERE table_schema = 'public'
""")
table_names = [t['table_name'] for t in tables]
assert 'analysis_decision' in table_names
assert 'trade_journal' in table_names
assert 'order_execution' in table_names
assert 'position_tracking' in table_names
```

---

## TASK-005: Create Test Database Fixtures with testing.postgresql

**Phase**: Foundation
**Complexity**: Medium
**Dependencies**: TASK-004

### Description
Set up pytest fixtures using testing.postgresql to provide isolated, in-memory PostgreSQL instances for all tests. This eliminates the need for manual database setup during testing.

### Steps
1. Create `tests/` directory
2. Create `conftest.py` with pytest fixtures:
   - `postgresql_instance`: Session-scoped fixture for PostgreSQL server
   - `test_db`: Function-scoped fixture for clean database per test
   - Automatic schema creation using `TradingDB.create_schema()`
3. Create test data fixtures:
   - Sample analysis decisions
   - Sample trade journal entries
   - Sample orders
4. Create basic test to verify fixtures work

### Acceptance Criteria
- [ ] conftest.py created with all fixtures
- [ ] Can run `pytest tests/` successfully
- [ ] Each test gets a fresh database instance
- [ ] Schema is created automatically for each test
- [ ] No manual PostgreSQL installation required
- [ ] Tests run in isolation (no shared state)

### Files to Create
- `tests/__init__.py`
- `tests/conftest.py`
- `tests/fixtures.py` (optional - for test data)
- `tests/test_db_layer.py` (simple test to verify fixtures work)

### Verification
```bash
pytest tests/test_db_layer.py -v
# Should show tests passing with clean database
```

---

## TASK-006: Production Database Setup Instructions

**Phase**: Foundation
**Complexity**: Low
**Dependencies**: TASK-004

### Description
Create documentation for production database setup with NocoDB, including manual steps to add fields to existing `analysis_decision` table and script to create new tables.

### Steps
1. Create `docs/database-setup.md` with:
   - Instructions to add 4 fields to existing `analysis_decision` table in NocoDB UI
   - Python script to create new tables (trade_journal, order_execution, position_tracking)
   - Verification steps
2. Create `scripts/create_production_tables.py`:
   - Connects to production PostgreSQL
   - Creates only NEW tables (not analysis_decision)
   - Creates indices
   - No foreign key constraints

### Acceptance Criteria
- [ ] Clear documentation for manual NocoDB steps
- [ ] Script creates all new tables successfully
- [ ] Script is idempotent (can run multiple times)
- [ ] Verification queries to check setup
- [ ] Warning about not creating analysis_decision in production

### Files to Create
- `docs/database-setup.md`
- `scripts/create_production_tables.py`

### Notes
- **PRODUCTION**: Only add 4 fields to existing analysis_decision table
- **TESTING**: Create complete analysis_decision table from scratch
- Relationships managed at application level (no FKs)

---

# PHASE 2: Core Programs

## TASK-007: Create Alpaca API Helper Module

**Phase**: Core Programs
**Complexity**: Low
**Dependencies**: TASK-002

### Description
Create a helper module for Alpaca API interactions to avoid code duplication across programs.

### Steps
1. Create `alpaca_client.py` with:
   - Function to initialize TradingClient
   - Function to initialize StockHistoricalDataClient
   - Common API error handling
   - Logging for API calls
2. Support paper trading mode from environment variable

### Acceptance Criteria
- [ ] Can initialize Alpaca clients successfully
- [ ] Paper trading mode configurable via env var
- [ ] Proper error handling for API failures
- [ ] Logging for API calls

### Files to Create
- `alpaca_client.py`

### Verification
```python
from alpaca_client import get_trading_client, get_data_client
trading = get_trading_client()
data = get_data_client()
assert trading is not None
assert data is not None
```

---

## TASK-008: Implement Order Executor - NEW_TRADE Handler

**Phase**: Core Programs
**Complexity**: High
**Dependencies**: TASK-003, TASK-007

### Description
Create order_executor.py program with NEW_TRADE action handler that places entry orders and creates trade journal entries.

### Steps
1. Create `order_executor.py` with OrderExecutor class
2. Implement `run()` method to fetch unexecuted decisions
3. Implement `handle_new_trade()` method:
   - Extract trade parameters from decision JSON
   - Submit limit order to Alpaca
   - Create trade_journal entry
   - Create order_execution entry
   - Update analysis_decision (set executed=true, execution_time, existing_order_id, existing_trade_journal_id)
4. Add logging for all actions
5. Add error handling with proper rollback

### Acceptance Criteria
- [ ] Fetches unexecuted decisions correctly
- [ ] Places limit order with Alpaca
- [ ] Creates trade_journal record with correct data
- [ ] Creates order_execution record
- [ ] Updates analysis_decision with execution info
- [ ] Handles errors gracefully (logs and continues)
- [ ] Can run standalone: `python order_executor.py`

### Files to Create
- `order_executor.py`

### Verification
```bash
# Insert test decision in database
# Run: python order_executor.py
# Verify order placed in Alpaca dashboard
# Verify trade_journal created
# Verify decision marked as executed
```

---

## TASK-009: Implement Order Executor - CANCEL Handler

**Phase**: Core Programs
**Complexity**: Medium
**Dependencies**: TASK-008

### Description
Add CANCEL action handler to order_executor.py that cancels pending orders and updates trade journal.

### Steps
1. Implement `handle_cancel()` method:
   - Get order_id from decision.existing_order_id
   - Cancel order with Alpaca
   - Update trade_journal (status=CANCELLED, exit_date, exit_reason)
   - Mark decision as executed
2. Handle case where order_id is missing
3. Add logging and error handling

### Acceptance Criteria
- [ ] Cancels Alpaca order successfully
- [ ] Updates trade_journal status to CANCELLED
- [ ] Marks decision as executed
- [ ] Handles missing order_id gracefully
- [ ] Logs all actions

### Files to Modify
- `order_executor.py`

### Verification
```python
# Insert test decision with primary_action=CANCEL
# Run order_executor.py
# Verify order cancelled in Alpaca
# Verify trade_journal updated to CANCELLED
```

---

## TASK-010: Implement Order Executor - AMEND Handler

**Phase**: Core Programs
**Complexity**: Low
**Dependencies**: TASK-009

### Description
Add AMEND action handler to order_executor.py that cancels old order and places new order with updated parameters.

### Steps
1. Implement `handle_amend()` method:
   - Call `handle_cancel()` to cancel old order
   - Call `handle_new_trade()` to place new order
   - Log the amendment
2. Add error handling for partial failures

### Acceptance Criteria
- [ ] Cancels old order successfully
- [ ] Places new order with updated parameters
- [ ] Logs amendment action
- [ ] Handles errors if cancel or new order fails

### Files to Modify
- `order_executor.py`

### Verification
```python
# Insert test decision with primary_action=AMEND
# Run order_executor.py
# Verify old order cancelled
# Verify new order placed
# Verify trade_journal updated
```

---

## TASK-011: Implement Order Monitor - Order Status Sync

**Phase**: Core Programs
**Complexity**: Medium
**Dependencies**: TASK-003, TASK-007

### Description
Create order_monitor.py program that syncs order status from Alpaca and updates order_execution table.

### Steps
1. Create `order_monitor.py` with OrderMonitor class
2. Implement `run()` method to fetch pending/partially_filled orders
3. Implement `sync_order_status()` method:
   - Get order status from Alpaca
   - Update order_execution record (status, filled_qty, filled_avg_price, filled_at)
   - Detect filled entry orders and trigger entry handler
   - Detect filled exit orders (SL/TP) and trigger exit handler
4. Add logging and error handling

### Acceptance Criteria
- [ ] Fetches pending orders from database
- [ ] Syncs status from Alpaca API
- [ ] Updates order_execution records
- [ ] Can run standalone: `python order_monitor.py`
- [ ] Handles API errors gracefully

### Files to Create
- `order_monitor.py`

### Verification
```bash
# Place test order via order_executor
# Run: python order_monitor.py
# Verify order_execution updated with current status
```

---

## TASK-012: Implement Order Monitor - Entry Order Fill Handler

**Phase**: Core Programs
**Complexity**: High
**Dependencies**: TASK-011

### Description
Add handler to order_monitor.py that processes filled entry orders, creates positions, and places SL/TP orders.

### Steps
1. Implement `handle_entry_filled()` method:
   - Update trade_journal (status=POSITION, actual_entry, actual_qty)
   - Create position_tracking entry
   - Call `place_stop_loss()` to place SL order
   - Call `place_take_profit()` for SWING trades
2. Implement `place_stop_loss()` method:
   - Submit stop order to Alpaca
   - Create order_execution record
   - Update position_tracking with stop_loss_order_id
3. Implement `place_take_profit()` method:
   - Submit limit order to Alpaca (for SWING trades only)
   - Create order_execution record
   - Update position_tracking with take_profit_order_id
4. Add comprehensive logging

### Acceptance Criteria
- [ ] Updates trade_journal when entry fills
- [ ] Creates position_tracking record
- [ ] Places SL order for all positions
- [ ] Places TP order for SWING trades only
- [ ] Updates position_tracking with SL/TP order IDs
- [ ] Handles partial fills correctly
- [ ] Logs all actions

### Files to Modify
- `order_monitor.py`

### Verification
```python
# Place test entry order
# Mark it as filled in test database
# Run order_monitor.py
# Verify position_tracking created
# Verify SL and TP orders placed in Alpaca
```

---

## TASK-013: Implement Order Monitor - Exit Order Fill Handler

**Phase**: Core Programs
**Complexity**: Medium
**Dependencies**: TASK-012

### Description
Add handler to order_monitor.py that processes filled exit orders (SL/TP), calculates P&L, closes trades, and cancels remaining orders.

### Steps
1. Implement `handle_exit_filled()` method:
   - Calculate P&L: (exit_price - entry_price) * qty
   - Determine exit_reason (STOPPED_OUT or TARGET_HIT)
   - Update trade_journal (status=CLOSED, exit_date, exit_price, actual_pnl, exit_reason)
   - Delete position_tracking record
   - Call `cancel_remaining_orders()` to cancel opposite order (SL if TP hit, TP if SL hit)
2. Implement `cancel_remaining_orders()` method:
   - Find remaining SL/TP orders for trade
   - Cancel them with Alpaca
   - Log cancellations
3. Add error handling for cancel failures

### Acceptance Criteria
- [ ] Calculates P&L correctly
- [ ] Updates trade_journal to CLOSED
- [ ] Deletes position_tracking record
- [ ] Cancels remaining orders (SL or TP)
- [ ] Handles errors if cancel fails
- [ ] Logs all actions

### Files to Modify
- `order_monitor.py`

### Verification
```python
# Create test position with SL and TP orders
# Mark SL order as filled
# Run order_monitor.py
# Verify trade_journal closed
# Verify position_tracking deleted
# Verify TP order cancelled
```

---

## TASK-014: Implement Position Monitor - Position Value Updates

**Phase**: Core Programs
**Complexity**: Medium
**Dependencies**: TASK-003, TASK-007

### Description
Create position_monitor.py program that updates position values and unrealized P&L based on current market prices.

### Steps
1. Create `position_monitor.py` with PositionMonitor class
2. Implement `run()` method to fetch all positions from position_tracking
3. Implement `update_position()` method:
   - Get current price from Alpaca data API
   - Calculate market_value: current_price * qty
   - Calculate unrealized_pnl: (current_price - avg_entry_price) * qty
   - Update position_tracking record
4. Add logging and error handling

### Acceptance Criteria
- [ ] Fetches all open positions
- [ ] Gets current prices from Alpaca
- [ ] Calculates market value correctly
- [ ] Calculates unrealized P&L correctly
- [ ] Updates position_tracking records
- [ ] Can run standalone: `python position_monitor.py`
- [ ] Handles price data unavailable gracefully

### Files to Create
- `position_monitor.py`

### Verification
```bash
# Create test position in database
# Run: python position_monitor.py
# Verify position_tracking updated with current price and P&L
```

---

## TASK-015: Implement Position Monitor - Position Reconciliation

**Phase**: Core Programs
**Complexity**: Medium
**Dependencies**: TASK-014

### Description
Add reconciliation logic to position_monitor.py that detects positions closed outside the system and updates records accordingly.

### Steps
1. Implement `check_for_closed_positions()` method:
   - Get all positions from Alpaca
   - Compare with position_tracking table
   - Find positions in tracking but not in Alpaca
   - Call `reconcile_closed_position()` for each discrepancy
2. Implement `reconcile_closed_position()` method:
   - Try to find closing order in order_execution
   - If found, use filled order data
   - If not found, use last known price and mark as MANUAL_EXIT
   - Update trade_journal to CLOSED
   - Delete position_tracking record
3. Add logging for all reconciliations

### Acceptance Criteria
- [ ] Detects positions closed outside system
- [ ] Uses filled order data if available
- [ ] Marks as MANUAL_EXIT if no order found
- [ ] Updates trade_journal correctly
- [ ] Deletes position_tracking record
- [ ] Logs all reconciliations

### Files to Modify
- `position_monitor.py`

### Verification
```python
# Create test position in tracking
# Manually close position in Alpaca
# Run position_monitor.py with check_for_closed_positions()
# Verify trade_journal updated to CLOSED
# Verify position_tracking deleted
```

---

# PHASE 3: Scheduling & Integration

## TASK-016: Implement Scheduler with APScheduler

**Phase**: Scheduling & Integration
**Complexity**: Medium
**Dependencies**: TASK-010, TASK-013, TASK-015

### Description
Create scheduler.py that runs all programs on their defined schedules using APScheduler with US Eastern timezone.

### Steps
1. Create `scheduler.py` with:
   - BlockingScheduler initialized with US/Eastern timezone
   - Job for order_executor: Once at 9:45 AM ET (Mon-Fri)
   - Job for order_monitor: Every 5 min during trading hours (9:30 AM - 4:00 PM ET, Mon-Fri)
   - Job for order_monitor: Once at 6:00 PM ET (Mon-Fri)
   - Job for position_monitor: Every 10 min during trading hours (9:30 AM - 4:00 PM ET, Mon-Fri)
   - Job for position_monitor: Once at 6:15 PM ET (Mon-Fri)
2. Add job listing on startup
3. Add proper signal handling for graceful shutdown
4. Add logging configuration

### Acceptance Criteria
- [ ] All programs scheduled correctly
- [ ] Uses US/Eastern timezone
- [ ] Only runs Monday-Friday
- [ ] Displays scheduled jobs on startup
- [ ] Can be stopped gracefully with Ctrl+C
- [ ] Logs all job executions
- [ ] Can run: `python scheduler.py`

### Files to Create
- `scheduler.py`

### Verification
```bash
python scheduler.py
# Verify jobs listed
# Wait for next scheduled time
# Verify job executes
# Press Ctrl+C to stop
```

---

## TASK-017: Add Test Mode Support to All Programs

**Phase**: Scheduling & Integration
**Complexity**: Low
**Dependencies**: TASK-010, TASK-013, TASK-015

### Description
Add test_mode parameter to all programs (order_executor, order_monitor, position_monitor) to support testing with in-memory database.

### Steps
1. Modify OrderExecutor class to accept test_mode and db instance:
   - Add `__init__(self, test_mode=False, db=None)` parameter
   - Use provided db instance if given
2. Modify OrderMonitor class similarly
3. Modify PositionMonitor class similarly
4. Update all programs to support command-line flag: `--test-mode`

### Acceptance Criteria
- [ ] All programs accept test_mode parameter
- [ ] All programs accept db instance parameter
- [ ] Can run with: `python order_executor.py --test-mode`
- [ ] Uses test database when test_mode=True
- [ ] Backward compatible (runs normally without flags)

### Files to Modify
- `order_executor.py`
- `order_monitor.py`
- `position_monitor.py`

### Verification
```bash
python order_executor.py --test-mode
# Should use test database configuration
```

---

## TASK-018: Create n8n Workflow Modification Guide

**Phase**: Scheduling & Integration
**Complexity**: Low
**Dependencies**: None

### Description
Create detailed instructions for modifying existing n8n Workflow 1 to add the 4 new fields to analysis_decision table after "Save Analysis" node.

### Steps
1. Create `docs/n8n-workflow-modification.md` with:
   - Step-by-step instructions to add "Update Analysis Decision" node
   - Node configuration details
   - JavaScript expressions for field mapping
   - Logic for existing_order_id and existing_trade_journal_id
   - Special case for NO_ACTION with days_open increment
2. Add screenshots or ASCII diagrams of workflow structure
3. Add verification steps

### Acceptance Criteria
- [ ] Clear step-by-step instructions
- [ ] Node configuration details provided
- [ ] JavaScript/expressions documented
- [ ] Special cases explained (NO_ACTION)
- [ ] Verification steps included

### Files to Create
- `docs/n8n-workflow-modification.md`

### Notes
- This is documentation only, not code changes
- User will implement in their n8n instance
- Critical for integration between n8n and Python programs

---

# PHASE 4: Testing

## TASK-019: Write Unit Tests for Database Layer

**Phase**: Testing
**Complexity**: Medium
**Dependencies**: TASK-005

### Description
Create comprehensive unit tests for the TradingDB class using in-memory PostgreSQL.

### Steps
1. Create `tests/test_db_layer.py` with tests for:
   - Connection establishment
   - Schema creation (all tables)
   - execute_query() method
   - execute_update() method
   - insert() method
   - update() method
   - get_by_id() method
   - query() method with WHERE clause
   - Error handling
2. Use test_db fixture from conftest.py

### Acceptance Criteria
- [ ] All CRUD operations tested
- [ ] Schema creation tested
- [ ] Error handling tested
- [ ] All tests pass with: `pytest tests/test_db_layer.py -v`
- [ ] Tests use isolated in-memory database
- [ ] No manual database setup required

### Files to Create
- `tests/test_db_layer.py`

### Verification
```bash
pytest tests/test_db_layer.py -v --cov=db_layer
# Should show high coverage and all tests passing
```

---

## TASK-020: Create Mock Alpaca API Fixtures

**Phase**: Testing
**Complexity**: Medium
**Dependencies**: TASK-005

### Description
Create reusable mock fixtures for Alpaca API responses to use in all program tests.

### Steps
1. Create `tests/mocks.py` with:
   - MockAlpacaOrder class (mimics Alpaca Order object)
   - MockAlpacaPosition class (mimics Alpaca Position object)
   - MockAlpacaQuote class (mimics Alpaca Quote object)
2. Create pytest fixtures in conftest.py:
   - mock_alpaca_trading_client
   - mock_alpaca_data_client
   - Configurable return values for different scenarios
3. Add helper functions to create mock data

### Acceptance Criteria
- [ ] Mock classes match Alpaca API structure
- [ ] Fixtures can be reused across all tests
- [ ] Support different scenarios (pending, filled, cancelled orders)
- [ ] Easy to configure for different test cases

### Files to Create
- `tests/mocks.py`

### Files to Modify
- `tests/conftest.py`

### Verification
```python
# In test file
def test_example(mock_alpaca_trading_client):
    order = mock_alpaca_trading_client.submit_order(...)
    assert order.id is not None
```

---

## TASK-021: Write Unit Tests for Order Executor - NEW_TRADE

**Phase**: Testing
**Complexity**: High
**Dependencies**: TASK-019, TASK-020

### Description
Create comprehensive tests for order_executor.py NEW_TRADE action using in-memory database and mocked Alpaca API.

### Steps
1. Create `tests/test_order_executor.py`
2. Write test cases:
   - `test_new_trade_execution`: Verify order placement and database updates
   - `test_new_trade_daytrade`: Test DAYTRADE style
   - `test_new_trade_swing`: Test SWING style with take_profit
   - `test_no_unexecuted_decisions`: Verify no action when no pending decisions
   - `test_multiple_decisions`: Verify batch processing
   - `test_alpaca_api_failure`: Handle order submission failure
   - `test_invalid_decision_data`: Handle malformed decision JSON
3. Use test_db and mock_alpaca fixtures

### Acceptance Criteria
- [ ] All NEW_TRADE scenarios tested
- [ ] Database state verified after execution
- [ ] Mock Alpaca API called with correct parameters
- [ ] Error handling tested
- [ ] All tests pass: `pytest tests/test_order_executor.py::test_new_trade* -v`

### Files to Create
- `tests/test_order_executor.py`

### Verification
```bash
pytest tests/test_order_executor.py -v -k "new_trade"
# All NEW_TRADE tests should pass
```

---

## TASK-022: Write Unit Tests for Order Executor - CANCEL & AMEND

**Phase**: Testing
**Complexity**: Medium
**Dependencies**: TASK-021

### Description
Add tests for CANCEL and AMEND actions in order_executor.py.

### Steps
1. Add test cases to `tests/test_order_executor.py`:
   - `test_cancel_order`: Verify order cancellation
   - `test_cancel_nonexistent_order`: Handle missing order_id
   - `test_amend_order`: Verify old order cancelled and new order placed
   - `test_amend_partial_failure`: Handle cancel success but new order failure
2. Verify trade_journal status updates
3. Verify analysis_decision marked as executed

### Acceptance Criteria
- [ ] CANCEL action tested
- [ ] AMEND action tested
- [ ] Error scenarios covered
- [ ] Database state verified
- [ ] All tests pass: `pytest tests/test_order_executor.py -v`

### Files to Modify
- `tests/test_order_executor.py`

### Verification
```bash
pytest tests/test_order_executor.py -v
# All order executor tests should pass
```

---

## TASK-023: Write Unit Tests for Order Monitor - Status Sync

**Phase**: Testing
**Complexity**: Medium
**Dependencies**: TASK-020

### Description
Create tests for order_monitor.py order status synchronization logic.

### Steps
1. Create `tests/test_order_monitor.py`
2. Write test cases:
   - `test_sync_pending_order`: Order still pending
   - `test_sync_partially_filled`: Order partially filled
   - `test_sync_filled_order`: Order fully filled
   - `test_sync_cancelled_order`: Order cancelled
   - `test_alpaca_api_failure`: Handle API errors
   - `test_order_not_found`: Handle missing orders
3. Mock Alpaca responses for each scenario
4. Verify order_execution updates

### Acceptance Criteria
- [ ] All status sync scenarios tested
- [ ] Database updates verified
- [ ] Error handling tested
- [ ] All tests pass: `pytest tests/test_order_monitor.py::test_sync* -v`

### Files to Create
- `tests/test_order_monitor.py`

### Verification
```bash
pytest tests/test_order_monitor.py -v -k "sync"
# All sync tests should pass
```

---

## TASK-024: Write Unit Tests for Order Monitor - Entry Fill Handler

**Phase**: Testing
**Complexity**: High
**Dependencies**: TASK-023

### Description
Add tests for entry order fill handling, position creation, and SL/TP order placement.

### Steps
1. Add test cases to `tests/test_order_monitor.py`:
   - `test_entry_filled_daytrade`: Entry fills, position created, SL placed (no TP)
   - `test_entry_filled_swing`: Entry fills, position created, SL and TP placed
   - `test_entry_partial_fill`: Verify partial fill handling
   - `test_stop_loss_placement`: Verify SL order parameters
   - `test_take_profit_placement`: Verify TP order parameters
   - `test_sl_placement_failure`: Handle SL order rejection
2. Verify position_tracking created correctly
3. Verify trade_journal status updated to POSITION

### Acceptance Criteria
- [ ] Entry fill scenarios tested
- [ ] Position creation verified
- [ ] SL/TP placement verified
- [ ] Partial fills handled correctly
- [ ] Error scenarios covered
- [ ] All tests pass

### Files to Modify
- `tests/test_order_monitor.py`

### Verification
```bash
pytest tests/test_order_monitor.py -v -k "entry"
# All entry fill tests should pass
```

---

## TASK-025: Write Unit Tests for Order Monitor - Exit Fill Handler

**Phase**: Testing
**Complexity**: Medium
**Dependencies**: TASK-024

### Description
Add tests for exit order fill handling (SL/TP), P&L calculation, and position closure.

### Steps
1. Add test cases to `tests/test_order_monitor.py`:
   - `test_stop_loss_filled`: SL fills, P&L calculated (loss), trade closed
   - `test_take_profit_filled`: TP fills, P&L calculated (gain), trade closed
   - `test_exit_cancels_remaining_orders`: Verify opposite order cancelled
   - `test_pnl_calculation`: Verify P&L math
   - `test_position_tracking_deleted`: Verify position removed
2. Verify trade_journal closed correctly
3. Verify exit_reason set properly

### Acceptance Criteria
- [ ] SL fill tested
- [ ] TP fill tested
- [ ] P&L calculation verified
- [ ] Trade closure verified
- [ ] Remaining orders cancelled
- [ ] All tests pass

### Files to Modify
- `tests/test_order_monitor.py`

### Verification
```bash
pytest tests/test_order_monitor.py -v -k "exit"
# All exit fill tests should pass
```

---

## TASK-026: Write Unit Tests for Position Monitor

**Phase**: Testing
**Complexity**: Medium
**Dependencies**: TASK-020

### Description
Create comprehensive tests for position_monitor.py position value updates and reconciliation.

### Steps
1. Create `tests/test_position_monitor.py`
2. Write test cases:
   - `test_update_position_values`: Verify price update and P&L calculation
   - `test_multiple_positions`: Update multiple positions
   - `test_unrealized_pnl_gain`: Verify positive P&L
   - `test_unrealized_pnl_loss`: Verify negative P&L
   - `test_price_data_unavailable`: Handle API failure
   - `test_reconcile_closed_position`: Detect and reconcile closed position
   - `test_reconcile_with_order`: Use filled order data
   - `test_reconcile_without_order`: Mark as MANUAL_EXIT
3. Mock Alpaca price data responses

### Acceptance Criteria
- [ ] Position update logic tested
- [ ] P&L calculation verified
- [ ] Reconciliation tested
- [ ] Error handling tested
- [ ] All tests pass: `pytest tests/test_position_monitor.py -v`

### Files to Create
- `tests/test_position_monitor.py`

### Verification
```bash
pytest tests/test_position_monitor.py -v
# All position monitor tests should pass
```

---

## TASK-027: Write Integration Tests - Complete Trade Lifecycle

**Phase**: Testing
**Complexity**: High
**Dependencies**: TASK-022, TASK-025, TASK-026

### Description
Create end-to-end integration tests that simulate complete trade lifecycles from decision to closure.

### Steps
1. Create `tests/test_integration.py`
2. Write integration test scenarios:
   - `test_complete_trade_stopped_out`: NEW_TRADE → Entry Fill → SL Fill → Closed
   - `test_complete_trade_target_hit`: NEW_TRADE → Entry Fill → TP Fill → Closed
   - `test_trade_cancelled_before_fill`: NEW_TRADE → CANCEL → Cancelled
   - `test_trade_amended`: NEW_TRADE → AMEND → New Order
   - `test_daytrade_lifecycle`: Full DAYTRADE flow
   - `test_swing_trade_lifecycle`: Full SWING flow with TP
3. Run all programs in sequence for each scenario
4. Verify final database state

### Acceptance Criteria
- [ ] Complete trade lifecycles tested
- [ ] All programs interact correctly
- [ ] Database state consistent across program runs
- [ ] Both DAYTRADE and SWING tested
- [ ] All tests pass: `pytest tests/test_integration.py -v`

### Files to Create
- `tests/test_integration.py`

### Verification
```bash
pytest tests/test_integration.py -v
# All integration tests should pass
```

---

## TASK-028: Write Error Handling Tests

**Phase**: Testing
**Complexity**: Medium
**Dependencies**: TASK-027

### Description
Create tests for error handling and edge cases across all programs.

### Steps
1. Create `tests/test_error_handling.py`
2. Write test cases:
   - `test_database_connection_failure`: Handle DB disconnect
   - `test_alpaca_api_rate_limit`: Handle rate limiting
   - `test_alpaca_api_timeout`: Handle timeouts
   - `test_invalid_order_rejection`: Handle order rejections
   - `test_partial_database_failure`: Transaction rollback
   - `test_concurrent_execution`: Handle race conditions
   - `test_malformed_json_decision`: Handle bad data
   - `test_missing_environment_variables`: Handle config errors
3. Verify programs don't crash
4. Verify proper error logging

### Acceptance Criteria
- [ ] All error scenarios tested
- [ ] Programs handle errors gracefully
- [ ] No crashes or unhandled exceptions
- [ ] Proper logging of errors
- [ ] All tests pass: `pytest tests/test_error_handling.py -v`

### Files to Create
- `tests/test_error_handling.py`

### Verification
```bash
pytest tests/test_error_handling.py -v
# All error handling tests should pass
```

---

## TASK-029: Run Full Test Suite and Measure Coverage

**Phase**: Testing
**Complexity**: Low
**Dependencies**: TASK-028

### Description
Run complete test suite with coverage measurement and achieve minimum 80% code coverage.

### Steps
1. Install pytest-cov: `pip install pytest-cov`
2. Run full test suite with coverage: `pytest tests/ --cov=. --cov-report=html`
3. Review coverage report
4. Add tests for uncovered code paths
5. Aim for 80%+ coverage on core modules

### Acceptance Criteria
- [ ] All tests pass: `pytest tests/ -v`
- [ ] Coverage >= 80% for core modules:
  - [ ] db_layer.py
  - [ ] order_executor.py
  - [ ] order_monitor.py
  - [ ] position_monitor.py
- [ ] HTML coverage report generated
- [ ] No critical code paths untested

### Files to Modify
- `requirements.txt` (add pytest-cov)

### Verification
```bash
pytest tests/ -v --cov=. --cov-report=html --cov-report=term
# Open htmlcov/index.html to view detailed coverage
```

---

# PHASE 5: Documentation & Deployment

## TASK-030: Create Main README.md

**Phase**: Documentation & Deployment
**Complexity**: Low
**Dependencies**: TASK-029

### Description
Create comprehensive README.md with project overview, setup instructions, and usage guide.

### Steps
1. Create README.md with sections:
   - Project overview and architecture
   - Features
   - Prerequisites
   - Installation (development and production)
   - Configuration (.env setup)
   - Database setup (development vs production)
   - Running the programs
   - Running tests
   - Deployment
   - Troubleshooting
   - Project structure
2. Add badges (if using CI/CD)
3. Add diagrams (optional)

### Acceptance Criteria
- [ ] Clear project overview
- [ ] Step-by-step installation instructions
- [ ] Both development and production setup covered
- [ ] Running instructions for all programs
- [ ] Testing instructions
- [ ] Troubleshooting section

### Files to Create
- `README.md`

---

## TASK-031: Create Development Setup Guide

**Phase**: Documentation & Deployment
**Complexity**: Low
**Dependencies**: TASK-030

### Description
Create detailed guide for development environment setup using in-memory PostgreSQL and Docker options.

### Steps
1. Create `docs/development-setup.md` with:
   - Option 1: testing.postgresql (recommended)
   - Option 2: Docker PostgreSQL
   - Option 3: Local PostgreSQL
   - Alpaca paper trading account setup
   - IDE/editor setup recommendations
   - Debugging tips
2. Add common issues and solutions

### Acceptance Criteria
- [ ] Multiple setup options documented
- [ ] Clear step-by-step instructions
- [ ] Troubleshooting tips included
- [ ] Easy for new developers to follow

### Files to Create
- `docs/development-setup.md`

---

## TASK-032: Create Production Deployment Guide

**Phase**: Documentation & Deployment
**Complexity**: Medium
**Dependencies**: TASK-030

### Description
Create comprehensive production deployment guide for deploying to server/cloud.

### Steps
1. Create `docs/production-deployment.md` with:
   - Server requirements
   - NocoDB database setup
   - Environment variable configuration
   - Systemd service setup (Linux)
   - macOS LaunchAgent setup (macOS)
   - Monitoring and logging setup
   - Backup procedures
   - Security considerations
2. Create systemd service files
3. Create macOS plist file
4. Add health check scripts

### Acceptance Criteria
- [ ] Clear deployment instructions
- [ ] Service configuration files provided
- [ ] Multiple deployment options (Linux/macOS)
- [ ] Monitoring and logging covered
- [ ] Security best practices documented

### Files to Create
- `docs/production-deployment.md`
- `deployment/trading-monitor.service` (systemd)
- `deployment/com.trading.monitor.plist` (macOS LaunchAgent)
- `scripts/health_check.py`

---

## TASK-033: Create Operational Runbook

**Phase**: Documentation & Deployment
**Complexity**: Low
**Dependencies**: TASK-032

### Description
Create operational runbook for day-to-day operations and troubleshooting.

### Steps
1. Create `docs/operations.md` with:
   - Daily operations checklist
   - How to monitor system health
   - Common issues and solutions
   - How to manually trigger programs
   - How to investigate failed trades
   - Database maintenance
   - Alpaca API status checking
   - Emergency procedures (stop all trading)
2. Add SQL queries for common investigations

### Acceptance Criteria
- [ ] Daily operations documented
- [ ] Troubleshooting procedures clear
- [ ] Manual override instructions provided
- [ ] Emergency stop procedure documented
- [ ] Investigation queries included

### Files to Create
- `docs/operations.md`

---

## TASK-034: Create Testing Strategy Documentation

**Phase**: Documentation & Deployment
**Complexity**: Low
**Dependencies**: TASK-029

### Description
Document the testing strategy, test structure, and how to write new tests.

### Steps
1. Create `docs/testing.md` with:
   - Testing philosophy
   - Test structure (unit, integration, error handling)
   - How to run tests
   - How to write new tests
   - Mock fixtures usage
   - Coverage requirements
   - Testing with in-memory PostgreSQL
   - Paper trading validation
2. Add examples of good test cases

### Acceptance Criteria
- [ ] Testing approach documented
- [ ] How to run tests explained
- [ ] How to write new tests explained
- [ ] Examples provided
- [ ] Coverage goals stated

### Files to Create
- `docs/testing.md`

---

## TASK-035: Create Paper Trading Validation Checklist

**Phase**: Documentation & Deployment
**Complexity**: Low
**Dependencies**: TASK-029

### Description
Create checklist for validating the system with Alpaca paper trading before production.

### Steps
1. Create `docs/paper-trading-validation.md` with:
   - Pre-validation setup
   - Test scenarios to validate:
     - NEW_TRADE (BUY)
     - Entry fill and SL/TP placement
     - Stop-loss execution
     - Take-profit execution
     - CANCEL action
     - AMEND action
     - Position monitoring
     - Multi-day position tracking
   - Validation checklist for each scenario
   - How to verify in Alpaca dashboard
   - Database verification queries
   - Sign-off criteria

### Acceptance Criteria
- [ ] All critical scenarios covered
- [ ] Clear validation steps
- [ ] Verification methods documented
- [ ] Sign-off criteria defined

### Files to Create
- `docs/paper-trading-validation.md`

---

## TASK-036: Setup Production Database (NocoDB)

**Phase**: Documentation & Deployment
**Complexity**: Medium
**Dependencies**: TASK-006

### Description
Execute production database setup by adding 4 fields to existing analysis_decision table and creating new tables in NocoDB PostgreSQL.

### Steps
1. Access NocoDB UI
2. Add 4 fields to existing `analysis_decision` table:
   - existing_order_id (SingleLineText, optional)
   - existing_trade_journal_id (Number, optional)
   - executed (Checkbox, default: false)
   - execution_time (DateTime, optional)
3. Run `scripts/create_production_tables.py` to create:
   - trade_journal
   - order_execution
   - position_tracking
4. Verify tables created with correct schema
5. Verify indices created
6. Run verification queries

### Acceptance Criteria
- [ ] 4 fields added to analysis_decision in NocoDB
- [ ] New tables created successfully
- [ ] Indices created
- [ ] No foreign key constraints
- [ ] Verification queries return expected results
- [ ] Tables visible in NocoDB UI

### Notes
- **IMPORTANT**: Do NOT create new analysis_decision table (it already exists)
- **IMPORTANT**: Do NOT create foreign key constraints (NocoDB limitation)
- Backup database before making changes

---

## TASK-037: Deploy to Production Server

**Phase**: Documentation & Deployment
**Complexity**: High
**Dependencies**: TASK-036, TASK-032

### Description
Deploy the trading system to production server/environment with scheduler running.

### Steps
1. Provision server (Linux or macOS)
2. Clone/copy code to server
3. Setup Python virtual environment
4. Install production dependencies
5. Configure .env with production credentials
6. Setup systemd service (Linux) or LaunchAgent (macOS)
7. Start scheduler service
8. Verify jobs scheduling correctly
9. Monitor first few job executions
10. Setup log rotation

### Acceptance Criteria
- [ ] Code deployed to production server
- [ ] Virtual environment created and activated
- [ ] Production .env configured correctly
- [ ] Scheduler service installed and running
- [ ] Jobs executing on schedule
- [ ] Logs being generated correctly
- [ ] No errors in initial runs
- [ ] Log rotation configured

### Notes
- Start with Alpaca paper trading first
- Monitor closely for first week
- Have rollback plan ready

---

## TASK-038: Paper Trading Validation

**Phase**: Documentation & Deployment
**Complexity**: High
**Dependencies**: TASK-037, TASK-035

### Description
Execute comprehensive paper trading validation using the checklist before considering production use.

### Steps
1. Use paper trading validation checklist
2. Execute all test scenarios:
   - Create NEW_TRADE decision (BUY)
   - Verify order placed at 9:45 AM
   - Verify entry fill detected
   - Verify SL/TP orders placed
   - Verify position tracking updates
   - Test SL execution
   - Test TP execution
   - Test CANCEL action
   - Test AMEND action
   - Run for at least 5 trading days
3. Verify database state after each scenario
4. Cross-check with Alpaca dashboard
5. Document any issues found
6. Fix issues and re-test
7. Get sign-off from stakeholders

### Acceptance Criteria
- [ ] All scenarios from checklist executed successfully
- [ ] Database state correct after each scenario
- [ ] No errors in logs
- [ ] System runs for 5+ trading days without issues
- [ ] All edge cases handled correctly
- [ ] Performance acceptable (no delays/timeouts)
- [ ] Stakeholder sign-off obtained

### Notes
- This is the final gate before live trading
- Take time to validate thoroughly
- Better to find issues in paper trading than live
- Document all test results

---

# Common Commands

## Development

```bash
# Activate virtual environment
source venv/bin/activate

# Install dependencies
pip install -r requirements.txt

# Run tests (all)
pytest tests/ -v

# Run tests with coverage
pytest tests/ --cov=. --cov-report=html

# Run specific test file
pytest tests/test_order_executor.py -v

# Run specific test
pytest tests/test_order_executor.py::test_new_trade_execution -v
```

## Running Programs

```bash
# Run individual programs
python order_executor.py
python order_monitor.py
python position_monitor.py

# Run with test mode
python order_executor.py --test-mode

# Run scheduler (all programs)
python scheduler.py
```

## Database

```bash
# Create schema in test database (development)
python -c "from db_layer import TradingDB; db = TradingDB(test_mode=True); db.create_schema()"

# Create production tables (NocoDB)
python scripts/create_production_tables.py

# Health check
python scripts/health_check.py
```

## Docker (Development)

```bash
# Start PostgreSQL for development
docker run --name trading-dev-db \
  -e POSTGRES_PASSWORD=devpassword \
  -e POSTGRES_DB=trading_dev \
  -p 5432:5432 \
  -d postgres:14-alpine

# Stop development database
docker stop trading-dev-db
docker rm trading-dev-db
```

## Production

```bash
# Start service (Linux)
sudo systemctl start trading-monitor
sudo systemctl status trading-monitor
sudo systemctl logs -f trading-monitor

# Start service (macOS)
launchctl load ~/Library/LaunchAgents/com.trading.monitor.plist
launchctl list | grep trading
tail -f /tmp/trading-monitor.log
```

---

# Notes

## Key Implementation Points

1. **Testing Philosophy**: All tests use in-memory PostgreSQL via `testing.postgresql` - no Docker or manual setup needed
2. **Database Constraints**: No foreign key constraints due to NocoDB limitation - relationships managed in application code
3. **Production vs Testing**:
   - Testing: Create ALL tables including complete `analysis_decision`
   - Production: Only add 4 fields to existing `analysis_decision`, create new tables
4. **Timezone**: All scheduling uses US Eastern Time (NYSE hours)
5. **Error Handling**: Programs log errors and continue - retry on next cycle
6. **Paper Trading**: Always start with paper trading for validation

## Critical Dependencies

- Must complete TASK-005 (test fixtures) before any program tests
- Must complete TASK-010, TASK-013, TASK-015 (all programs) before TASK-016 (scheduler)
- Must complete TASK-029 (full test suite) before production deployment
- Must complete TASK-038 (paper trading validation) before live trading

## Quick Wins (Start Here)

Easy tasks to build momentum:
1. TASK-001: Setup Project Environment
2. TASK-002: Create Environment Configuration
3. TASK-007: Create Alpaca API Helper Module
4. TASK-018: Create n8n Workflow Modification Guide
5. TASK-030: Create Main README.md

---

**Last Updated**: 2025-10-03
**Status**: Ready for Implementation
**Version**: 1.0
