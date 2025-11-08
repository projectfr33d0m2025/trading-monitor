# Database Setup Guide

This guide covers setting up the database for both production (NocoDB) and development/testing.

## Production Setup (NocoDB)

### Important Notes
- **DO NOT** create a new `analysis_decision` table - it already exists in your NocoDB instance
- **DO** add 4 new fields to the existing `analysis_decision` table
- **DO** create new tables: `trade_journal`, `order_execution`, `position_tracking`
- **NO foreign key constraints** - NocoDB doesn't support them (relationships managed in application code)

### Step 1: Add Fields to Existing `analysis_decision` Table (Manual in NocoDB UI)

Access your NocoDB instance and add these 4 fields to the `analysis_decision` table:

| Field Name | Field Type | Default Value | Required | Description |
|------------|-----------|---------------|----------|-------------|
| `existing_order_id` | SingleLineText | NULL | No | Alpaca order ID if order exists |
| `existing_trade_journal_id` | Number | NULL | No | FK to trade_journal if position exists |
| `executed` | Checkbox | false | No | Whether decision has been executed |
| `execution_time` | DateTime | NULL | No | When decision was executed |

**Steps in NocoDB UI:**
1. Open your NocoDB workspace
2. Navigate to the `analysis_decision` table
3. Click the "+" button to add a new field
4. For each field above:
   - Enter the field name
   - Select the appropriate field type
   - Set default value if applicable
   - Save the field

### Step 2: Create New Tables (Using Python Script)

Run the provided script to create the new tables in your PostgreSQL database:

```bash
# Make sure you're in the project directory
cd /path/to/trading-monitor

# Ensure your .env file has the correct PostgreSQL connection details
# POSTGRES_HOST, POSTGRES_PORT, POSTGRES_DB, POSTGRES_USER, POSTGRES_PASSWORD

# Run the script
python scripts/create_production_tables.py
```

The script will create:
- `trade_journal` - Track individual trades
- `order_execution` - Track all orders
- `position_tracking` - Track open positions

### Step 3: Verify Setup

Run these SQL queries to verify everything is set up correctly:

```sql
-- Check analysis_decision has new fields
SELECT column_name, data_type, column_default
FROM information_schema.columns
WHERE table_name = 'analysis_decision'
AND column_name IN ('existing_order_id', 'existing_trade_journal_id', 'executed', 'execution_time');

-- Check new tables exist
SELECT table_name
FROM information_schema.tables
WHERE table_schema = 'public'
AND table_name IN ('trade_journal', 'order_execution', 'position_tracking');

-- Check indices exist
SELECT indexname
FROM pg_indexes
WHERE schemaname = 'public'
AND tablename IN ('trade_journal', 'order_execution', 'position_tracking');
```

Expected results:
- 4 new columns in `analysis_decision`
- 3 new tables created
- 8 indices created

## Development/Testing Setup (In-Memory PostgreSQL)

For development and testing, the system uses `testing.postgresql` which automatically creates an in-memory PostgreSQL instance with all tables.

### Automated Setup (Recommended)

The test fixtures automatically set up the database for each test:

```bash
# Install dependencies
pip install -r requirements.txt

# Run tests (database created automatically)
pytest tests/
```

The `conftest.py` file handles:
- Creating temporary PostgreSQL instance
- Creating all tables (including complete `analysis_decision` table)
- Providing clean database for each test
- Cleaning up after tests complete

### Manual Development Database

If you want a persistent development database, use Docker:

```bash
# Start PostgreSQL container
docker run --name trading-dev-db \
  -e POSTGRES_PASSWORD=devpassword \
  -e POSTGRES_DB=trading_dev \
  -p 5432:5432 \
  -d postgres:14-alpine

# Create schema
python -c "from db_layer import TradingDB; db = TradingDB(test_mode=True); db.create_schema(); print('Schema created')"
```

Update your `.env`:
```bash
TEST_POSTGRES_HOST=localhost
TEST_POSTGRES_PORT=5432
TEST_POSTGRES_DB=trading_dev
TEST_POSTGRES_USER=postgres
TEST_POSTGRES_PASSWORD=devpassword
```

## Troubleshooting

### "relation already exists" error
This is normal if running create_schema() multiple times. The `IF NOT EXISTS` clause prevents errors.

### NocoDB shows "Unknown column type"
Make sure you're using standard PostgreSQL data types. NocoDB UI may display them differently:
- VARCHAR(255) → SingleLineText
- INT → Number
- BOOLEAN → Checkbox
- TIMESTAMP → DateTime
- JSONB → LongText (displays as JSON)

### Foreign key constraint violations
We don't use foreign key constraints. Relationships are managed in application code. If you see FK errors, check your PostgreSQL setup - it might have accidentally added constraints.

### Permission denied errors
Make sure your PostgreSQL user has CREATE TABLE and CREATE INDEX permissions:

```sql
GRANT CREATE ON DATABASE your_database TO your_user;
GRANT ALL PRIVILEGES ON ALL TABLES IN SCHEMA public TO your_user;
```

## Schema Reference

### Tables Created
1. **analysis_decision** (modified) - AI analysis and trade decisions
2. **trade_journal** (new) - Individual trade tracking
3. **order_execution** (new) - Order execution tracking
4. **position_tracking** (new) - Real-time position tracking

### Relationships (Application-Level Only)
- `analysis_decision.existing_trade_journal_id` → `trade_journal.id`
- `trade_journal.initial_analysis_id` → `analysis_decision.Analysis_Id`
- `order_execution.trade_journal_id` → `trade_journal.id`
- `order_execution.analysis_decision_id` → `analysis_decision.Analysis_Id`
- `position_tracking.trade_journal_id` → `trade_journal.id`

**Note:** These relationships are NOT enforced by foreign key constraints. The application code manages referential integrity.
