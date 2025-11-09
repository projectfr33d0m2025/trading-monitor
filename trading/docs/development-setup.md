# Development Setup Guide

**Last Updated:** 2025-10-26
**Audience:** Developers setting up the trading monitor system for local development

---

## Table of Contents

1. [Prerequisites](#prerequisites)
2. [Initial Setup](#initial-setup)
3. [Environment Configuration](#environment-configuration)
4. [Database Setup](#database-setup)
5. [Alpaca API Setup](#alpaca-api-setup)
6. [Running Tests](#running-tests)
7. [Running Programs Manually](#running-programs-manually)
8. [Development Workflow](#development-workflow)
9. [Troubleshooting](#troubleshooting)

---

## Prerequisites

### Required Software

- **Python 3.9+** (recommended: Python 3.10 or 3.11)
- **PostgreSQL 14+** (via Docker or native installation)
- **Git** (for version control)
- **Docker** (optional, recommended for database)
- **pip** (Python package manager)
- **virtualenv** or **venv** (for Python virtual environments)

### Required Accounts

- **Alpaca Trading Account** (paper trading enabled)
  - Sign up at: https://alpaca.markets
  - Get API credentials (API Key + Secret)
- **PostgreSQL Database** (local or cloud)
  - Option 1: Docker (easiest)
  - Option 2: Native PostgreSQL installation
  - Option 3: Cloud provider (AWS RDS, DigitalOcean, etc.)

---

## Initial Setup

### 1. Clone the Repository

```bash
# Clone the repository
git clone <repository-url>
cd trading-monitor

# Verify files
ls -la
```

### 2. Create Python Virtual Environment

**Using venv (recommended):**

```bash
# Create virtual environment
python3 -m venv venv

# Activate virtual environment
# On Linux/Mac:
source venv/bin/activate

# On Windows:
venv\Scripts\activate

# Verify activation (should show venv path)
which python
```

**Using virtualenv:**

```bash
# Install virtualenv if not available
pip install virtualenv

# Create virtual environment
virtualenv venv

# Activate (same as above)
source venv/bin/activate
```

### 3. Install Dependencies

```bash
# Upgrade pip
pip install --upgrade pip

# Install all dependencies
pip install -r requirements.txt

# Verify installation
pip list
```

**Expected packages:**
- alpaca-py
- psycopg2-binary
- python-dotenv
- APScheduler
- pytest
- pytest-cov
- testing.postgresql

---

## Environment Configuration

### 1. Create Environment File

```bash
# Copy example environment file
cp .env.example .env

# Edit with your preferred editor
nano .env
# or
vim .env
# or
code .env
```

### 2. Configure Environment Variables

Edit `.env` with your settings:

```bash
# Database Configuration
DB_HOST=localhost
DB_PORT=5432
DB_NAME=trading_dev
DB_USER=postgres
DB_PASSWORD=devpassword

# Alpaca API Configuration (Paper Trading)
ALPACA_API_KEY=your_paper_api_key_here
ALPACA_SECRET_KEY=your_paper_secret_key_here
ALPACA_BASE_URL=https://paper-api.alpaca.markets

# System Configuration
LOG_LEVEL=INFO
TRADE_MODE=paper
```

**Important Notes:**
- **ALWAYS use paper trading for development** (`TRADE_MODE=paper`)
- **DO NOT commit `.env` to git** (it's in `.gitignore`)
- Get Alpaca paper trading credentials from: https://app.alpaca.markets/paper/dashboard/overview

### 3. Verify Configuration

```bash
# Test config loading
python -c "from config import Config; c = Config(); print('Config loaded:', c.db_name)"
```

---

## Database Setup

### Option 1: Docker PostgreSQL (Recommended for Development)

**Start PostgreSQL Container:**

```bash
# Create and start PostgreSQL container
docker run --name trading-dev-db \
  -e POSTGRES_PASSWORD=devpassword \
  -e POSTGRES_DB=trading_dev \
  -p 5432:5432 \
  -d postgres:14-alpine

# Verify container is running
docker ps | grep trading-dev-db

# View logs (optional)
docker logs trading-dev-db
```

**Useful Docker Commands:**

```bash
# Stop container
docker stop trading-dev-db

# Start existing container
docker start trading-dev-db

# Remove container (data will be lost)
docker rm -f trading-dev-db

# Access PostgreSQL CLI
docker exec -it trading-dev-db psql -U postgres -d trading_dev
```

### Option 2: Native PostgreSQL Installation

**Install PostgreSQL:**

```bash
# On Ubuntu/Debian
sudo apt-get update
sudo apt-get install postgresql postgresql-contrib

# On macOS (with Homebrew)
brew install postgresql@14
brew services start postgresql@14
```

**Create Development Database:**

```bash
# Access PostgreSQL
psql -U postgres

# Create database
CREATE DATABASE trading_dev;

# Create user (if needed)
CREATE USER trading_user WITH PASSWORD 'devpassword';

# Grant privileges
GRANT ALL PRIVILEGES ON DATABASE trading_dev TO trading_user;

# Exit
\q
```

### Create Database Schema

```bash
# Activate virtual environment
source venv/bin/activate

# Create schema using Python
python -c "
from db_layer import TradingDB
db = TradingDB()
db.create_schema()
print('✅ Schema created successfully!')
"

# Verify tables were created
python -c "
from db_layer import TradingDB
import psycopg2
db = TradingDB()
cursor = db.get_cursor()
cursor.execute(\"SELECT table_name FROM information_schema.tables WHERE table_schema='public'\")
tables = [row[0] for row in cursor.fetchall()]
print('Tables:', tables)
cursor.close()
db.close()
"
```

**Expected tables:**
- `analysis_decision`
- `trade_journal`
- `order_execution`
- `position_status`

### Verify Database Connection

```bash
# Test database connection
python -c "from db_layer import TradingDB; db = TradingDB(); print('✅ Database connected!'); db.close()"
```

---

## Alpaca API Setup

### 1. Get Paper Trading Credentials

1. Sign up at https://alpaca.markets
2. Navigate to Paper Trading Dashboard
3. Go to "Your API Keys" section
4. Generate API Key and Secret
5. Copy to `.env` file

### 2. Verify Alpaca Connection

```bash
# Test Alpaca API connection
python -c "
from alpaca_client import get_trading_client
client = get_trading_client()
account = client.get_account()
print('✅ Alpaca connected!')
print(f'Account Status: {account.status}')
print(f'Buying Power: ${account.buying_power}')
"
```

### 3. Test Alpaca Functions

```bash
# Test market data retrieval
python -c "
from alpaca_client import get_latest_price
price = get_latest_price('AAPL')
print(f'AAPL Price: ${price}')
"
```

---

## Running Tests

### 1. Run All Tests

```bash
# Run all tests with verbose output
pytest -v

# Run with coverage report
pytest --cov=. --cov-report=html --cov-report=term

# View coverage report
open htmlcov/index.html  # macOS
xdg-open htmlcov/index.html  # Linux
start htmlcov/index.html  # Windows
```

### 2. Run Specific Test Files

```bash
# Database layer tests
pytest tests/test_db_layer.py -v

# Order executor tests
pytest tests/test_order_executor.py -v

# Order monitor tests
pytest tests/test_order_monitor.py -v

# Position monitor tests
pytest tests/test_position_monitor.py -v

# Integration tests
pytest tests/test_integration.py -v

# Error handling tests
pytest tests/test_error_handling.py -v
```

### 3. Run Specific Test Functions

```bash
# Run a specific test
pytest tests/test_db_layer.py::test_insert_decision -v

# Run tests matching a pattern
pytest -k "test_new_trade" -v
```

### 4. Test with Different Verbosity Levels

```bash
# Quiet mode (only show failures)
pytest -q

# Verbose mode (show each test)
pytest -v

# Very verbose mode (show more details)
pytest -vv

# Show print statements
pytest -s
```

---

## Running Programs Manually

### 1. Order Executor

```bash
# Run in test mode (recommended for development)
python order_executor.py --test-mode

# Run normally (will execute real orders in paper trading)
python order_executor.py
```

**What it does:**
- Scans for `analysis_decision` records with `signal_decision = 'EXECUTE'`
- Places entry orders with Alpaca
- Creates `trade_journal` and `order_execution` records
- Updates `analysis_decision` with execution info

### 2. Order Monitor

```bash
# Run in test mode
python order_monitor.py --test-mode

# Run normally
python order_monitor.py
```

**What it does:**
- Syncs order status from Alpaca
- Detects filled entry orders
- Places stop-loss orders for all trades
- Places take-profit orders for SWING trades
- Handles filled exit orders (calculates P&L)
- Closes completed trades

### 3. Position Monitor

```bash
# Run in test mode
python position_monitor.py --test-mode

# Run normally
python position_monitor.py
```

**What it does:**
- Updates position values from market data
- Calculates unrealized P&L
- Detects positions closed outside the system
- Reconciles missing positions

### 4. Scheduler (All Programs)

```bash
# Run scheduler (all programs on schedule)
python scheduler.py

# Stop with Ctrl+C (graceful shutdown)
```

**Schedule:**
- Order Executor: Daily at 9:45 AM ET
- Order Monitor: Every 5 minutes (+ 6:00 PM)
- Position Monitor: Every 10 minutes (+ 6:15 PM)

---

## Development Workflow

### Typical Development Day

1. **Start Development Environment**

```bash
# Start virtual environment
source venv/bin/activate

# Start database (Docker)
docker start trading-dev-db

# Verify connections
python -c "from db_layer import TradingDB; db = TradingDB(); print('✅ DB OK'); db.close()"
python -c "from alpaca_client import get_trading_client; get_trading_client(); print('✅ Alpaca OK')"
```

2. **Make Code Changes**

```bash
# Edit files
code order_executor.py

# Test changes
pytest tests/test_order_executor.py -v

# Run manually to verify
python order_executor.py --test-mode
```

3. **Run Full Test Suite**

```bash
# Before committing
pytest --cov=. --cov-report=term

# Verify coverage is >90%
```

4. **Commit Changes**

```bash
git add .
git commit -m "feat: add new feature"
git push origin your-branch
```

### Best Practices

1. **Always use test mode** when developing
2. **Write tests first** (TDD approach)
3. **Run tests before committing**
4. **Use meaningful commit messages**
5. **Keep `.env` secure** (never commit)
6. **Document complex logic** with comments
7. **Use logging** instead of print statements

### Code Style

```python
# Use type hints
def process_order(order_id: str, quantity: int) -> bool:
    pass

# Use descriptive variable names
entry_order_id = "abc123"  # Good
eo_id = "abc123"  # Bad

# Use logging
import logging
logger = logging.getLogger(__name__)
logger.info("Processing order %s", order_id)

# Handle errors gracefully
try:
    result = api_call()
except Exception as e:
    logger.error("API call failed: %s", str(e))
    return None
```

---

## Troubleshooting

### Database Connection Issues

**Problem:** `psycopg2.OperationalError: could not connect to server`

**Solutions:**

```bash
# 1. Check if PostgreSQL is running
docker ps | grep trading-dev-db  # Docker
pg_isready  # Native

# 2. Verify .env settings
cat .env | grep DB_

# 3. Test connection manually
psql -h localhost -U postgres -d trading_dev

# 4. Check firewall/network
telnet localhost 5432
```

### Alpaca API Issues

**Problem:** `APIError: Invalid API credentials`

**Solutions:**

```bash
# 1. Verify credentials in .env
cat .env | grep ALPACA_

# 2. Ensure using paper trading URL
# Should be: https://paper-api.alpaca.markets

# 3. Test credentials manually
curl -u $ALPACA_API_KEY:$ALPACA_SECRET_KEY \
  https://paper-api.alpaca.markets/v2/account

# 4. Regenerate API keys if needed
# Visit: https://app.alpaca.markets/paper/dashboard/overview
```

### Import Errors

**Problem:** `ModuleNotFoundError: No module named 'alpaca'`

**Solutions:**

```bash
# 1. Verify virtual environment is activated
which python  # Should show venv path

# 2. Reinstall dependencies
pip install -r requirements.txt

# 3. Check Python version
python --version  # Should be 3.9+

# 4. Verify package installation
pip show alpaca-py
```

### Test Failures

**Problem:** Tests failing unexpectedly

**Solutions:**

```bash
# 1. Run tests with verbose output
pytest -vv -s

# 2. Run single test to isolate issue
pytest tests/test_db_layer.py::test_insert_decision -vv

# 3. Check database state
python -c "
from db_layer import TradingDB
db = TradingDB(test_mode=True)
cursor = db.get_cursor()
cursor.execute('SELECT COUNT(*) FROM analysis_decision')
print('Records:', cursor.fetchone()[0])
cursor.close()
db.close()
"

# 4. Clear test database
# Tests use in-memory database, so just re-run
```

### Permission Issues

**Problem:** `PermissionError: [Errno 13] Permission denied`

**Solutions:**

```bash
# 1. Check file permissions
ls -la

# 2. Fix permissions if needed
chmod +x *.py

# 3. For Docker
sudo usermod -aG docker $USER
# Then logout and login

# 4. For database files
sudo chown -R $USER:$USER .
```

---

## Quick Reference

### Common Commands

```bash
# Activate environment
source venv/bin/activate

# Start database
docker start trading-dev-db

# Run all tests
pytest -v

# Run specific program
python order_executor.py --test-mode

# Check coverage
pytest --cov=. --cov-report=term

# View logs
tail -f logs/trading_system.log

# Stop all
docker stop trading-dev-db
deactivate
```

### File Locations

```
trading-monitor/
├── .env                    # Environment configuration (DO NOT COMMIT)
├── config.py              # Configuration loader
├── db_layer.py            # Database abstraction
├── alpaca_client.py       # Alpaca API helpers
├── order_executor.py      # Entry order placement
├── order_monitor.py       # Order status monitoring
├── position_monitor.py    # Position tracking
├── scheduler.py           # APScheduler setup
├── requirements.txt       # Python dependencies
├── tests/                 # Test files
│   ├── conftest.py       # pytest fixtures
│   ├── test_db_layer.py
│   ├── test_order_executor.py
│   ├── test_order_monitor.py
│   ├── test_position_monitor.py
│   ├── test_integration.py
│   └── test_error_handling.py
└── docs/                  # Documentation
    ├── database-setup.md
    ├── development-setup.md
    ├── production-deployment.md
    └── n8n-workflow-modification.md
```

### Important URLs

- **Alpaca Paper Trading Dashboard:** https://app.alpaca.markets/paper/dashboard/overview
- **Alpaca API Documentation:** https://alpaca.markets/docs/
- **PostgreSQL Documentation:** https://www.postgresql.org/docs/
- **pytest Documentation:** https://docs.pytest.org/

---

## Next Steps

After completing development setup:

1. ✅ Run all tests: `pytest -v`
2. ✅ Test individual programs manually
3. ✅ Review code and understand architecture
4. ✅ Read [Production Deployment Guide](production-deployment.md)
5. ✅ Read [Operational Runbook](operational-runbook.md)
6. ✅ Setup paper trading validation

---

**Questions or Issues?**

- Check the [Troubleshooting](#troubleshooting) section
- Review logs in `logs/trading_system.log`
- Verify configuration in `.env`
- Test connections (database and Alpaca)

---

**Last Updated:** 2025-10-26 by Claude Code
