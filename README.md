# Trading System Monitoring

A Python-based trading system that monitors the complete trading lifecycle: **Analysis → Decision → Trade Plan → Order → Position**. This system integrates with n8n workflows, NocoDB for data persistence, and Alpaca API for order execution.

## 🎯 Features

- **Automated Order Execution**: Execute approved trading decisions daily at 9:45 AM ET
- **Real-time Order Monitoring**: Track order status and manage stop-loss/take-profit orders
- **Position Tracking**: Monitor open positions and calculate unrealized P&L
- **Position Reconciliation**: Detect and reconcile positions closed outside the system
- **Database Integration**: Direct PostgreSQL access underneath NocoDB
- **Paper Trading Support**: Test with Alpaca paper trading before going live
- **Comprehensive Testing**: In-memory PostgreSQL testing with `testing.postgresql`

## 📋 Prerequisites

- Python 3.9+
- Alpaca Paper Trading account ([alpaca.markets](https://alpaca.markets))
- NocoDB instance with access to underlying PostgreSQL database
- PostgreSQL connection credentials

## 🚀 Quick Start

### 1. Clone and Install

```bash
# Clone the repository
cd trading-monitor

# Create virtual environment
python3 -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate

# Install dependencies
pip install -r requirements.txt
```

### 2. Configure Environment

```bash
# Copy example environment file
cp .env.example .env

# Edit .env and add your credentials
nano .env
```

Required variables:
- `POSTGRES_HOST`, `POSTGRES_PORT`, `POSTGRES_DB`, `POSTGRES_USER`, `POSTGRES_PASSWORD`
- `ALPACA_API_KEY`, `ALPACA_SECRET_KEY`, `ALPACA_PAPER=true`

### 3. Setup Database

**Production (NocoDB):**
```bash
# Step 1: Manually add 4 fields to existing analysis_decision table in NocoDB UI
# See docs/database-setup.md for detailed instructions

# Step 2: Create new tables
python scripts/create_production_tables.py
```

**Development (Docker):**
```bash
# Start PostgreSQL
docker run --name trading-dev-db \
  -e POSTGRES_PASSWORD=devpassword \
  -e POSTGRES_DB=trading_dev \
  -p 5432:5432 -d postgres:14-alpine

# Create schema
python -c "from db_layer import TradingDB; db = TradingDB(test_mode=True); db.create_schema(); print('Done')"
```

### 4. Run Programs

```bash
# Run individual programs
python order_executor.py      # Execute trading decisions
python order_monitor.py        # Monitor orders and place SL/TP
python position_monitor.py     # Update position values

# Run scheduler (all programs on schedule)
python scheduler.py
```

### 5. Run Tests

```bash
# Run all tests
pytest tests/ -v

# Run with coverage
pytest tests/ --cov=. --cov-report=html

# Run specific test file
pytest tests/test_db_layer.py -v
```

## 📁 Project Structure

```
trading-monitor/
├── config.py                   # Configuration management
├── db_layer.py                 # PostgreSQL abstraction layer
├── alpaca_client.py            # Alpaca API helpers
├── order_executor.py           # Execute trading decisions (runs at 9:45 AM ET)
├── order_monitor.py            # Monitor orders, place SL/TP (every 5 min)
├── position_monitor.py         # Update positions, P&L (every 10 min)
├── scheduler.py                # APScheduler for all programs
├── requirements.txt            # Python dependencies
├── .env.example                # Environment template
├── tests/                      # Test suite
│   ├── conftest.py            # pytest fixtures
│   ├── test_db_layer.py       # Database tests
│   └── ...
├── docs/                       # Documentation
│   ├── database-setup.md      # Database setup guide
│   └── n8n-workflow-modification.md
├── scripts/                    # Utility scripts
│   └── create_production_tables.py
├── deployment/                 # Deployment configs
└── alpaca_sample_responses/    # Alpaca API samples
```

## 🔄 Workflow Integration

### n8n Workflow 1 (Analysis & Decision)

Your existing n8n workflow handles AI analysis and decision making. Modify it to populate 4 new fields in `analysis_decision` table:

- `existing_order_id`
- `existing_trade_journal_id`
- `executed`
- `execution_time`

See `docs/n8n-workflow-modification.md` for detailed instructions.

### Python Programs (Workflows 2-4)

1. **Order Executor** (Workflow 2): Executes approved decisions daily at 9:45 AM ET
2. **Order Monitor** (Workflow 3): Syncs order status, places SL/TP orders
3. **Position Monitor** (Workflow 4): Updates position values and P&L

## 📊 Database Schema

### Tables

- **analysis_decision** (existing, modified): AI analysis and trade decisions
- **trade_journal** (new): Individual trade tracking
- **order_execution** (new): Order tracking (entry, SL, TP)
- **position_tracking** (new): Real-time position monitoring

### Relationships

Managed at application level (no foreign key constraints due to NocoDB limitation):

- `analysis_decision.existing_trade_journal_id` → `trade_journal.id`
- `order_execution.trade_journal_id` → `trade_journal.id`
- `position_tracking.trade_journal_id` → `trade_journal.id`

See `docs/database-setup.md` for complete schema.

## ⏰ Schedule

All times in US Eastern Time (NYSE trading hours):

| Program | Schedule | Purpose |
|---------|----------|---------|
| Order Executor | Once at 9:45 AM ET (Mon-Fri) | Execute approved decisions |
| Order Monitor | Every 5 min (9:30 AM - 4:00 PM ET) + 6:00 PM | Monitor orders, place SL/TP |
| Position Monitor | Every 10 min (9:30 AM - 4:00 PM ET) + 6:15 PM | Update positions, P&L |

## 🧪 Testing

The project uses `testing.postgresql` for automated, in-memory testing:

```bash
# Install test dependencies
pip install -r requirements.txt

# Run tests (database created automatically)
pytest tests/ -v

# Run with coverage
pytest tests/ --cov=. --cov-report=html --cov-report=term
```

No manual PostgreSQL setup required! Tests use isolated in-memory instances.

## 🛠️ Configuration

### Environment Variables

See `.env.example` for all available variables.

### Trading Schedule

Configurable via environment variables:
- `TRADING_START_HOUR=9`
- `TRADING_START_MINUTE=30`
- `TRADING_END_HOUR=16`
- `TRADING_END_MINUTE=0`

### Paper Trading

Set `ALPACA_PAPER=true` in `.env` to use paper trading (recommended for testing).

## 📖 Documentation

- [Database Setup](docs/database-setup.md) - Production and development database setup
- [n8n Workflow Modification](docs/n8n-workflow-modification.md) - Integrate with n8n
- [Trading System PRD](trading-monitor-prd.md) - Complete product requirements
- [Implementation Tasks](tasks.md) - Detailed task breakdown

## 🚨 Troubleshooting

### "Database connection failed"

Check your `.env` file has correct PostgreSQL credentials:
```bash
POSTGRES_HOST=localhost
POSTGRES_PORT=5432
POSTGRES_DB=nocodb
POSTGRES_USER=postgres
POSTGRES_PASSWORD=your_password
```

### "Alpaca API credentials not configured"

Ensure `.env` has your Alpaca API keys:
```bash
ALPACA_API_KEY=your_alpaca_paper_key
ALPACA_SECRET_KEY=your_alpaca_paper_secret
ALPACA_PAPER=true
```

### Tests fail with PostgreSQL errors

Make sure `testing.postgresql` is installed:
```bash
pip install testing.postgresql
```

### "No module named 'config'"

Ensure you're in the project root directory and virtual environment is activated:
```bash
cd /path/to/trading-monitor
source venv/bin/activate
python order_executor.py
```

## 🔒 Security

- Never commit `.env` file (already in `.gitignore`)
- Use paper trading for development and testing
- Store production credentials securely
- Limit database user permissions
- Review all orders before switching to live trading

## 📝 Development

### Running Individual Programs

```bash
# Order Executor
python order_executor.py

# Order Monitor
python order_monitor.py

# Position Monitor
python position_monitor.py

# Test Mode
python order_executor.py --test-mode
```

### Running Tests

```bash
# All tests
pytest tests/ -v

# Specific test file
pytest tests/test_order_executor.py -v

# Specific test
pytest tests/test_db_layer.py::test_insert_record -v

# With coverage
pytest tests/ --cov=. --cov-report=html
```

### Database Operations

```bash
# Create schema (development)
python -c "from db_layer import TradingDB; db = TradingDB(test_mode=True); db.create_schema()"

# Create production tables
python scripts/create_production_tables.py

# Test database connection
python -c "from db_layer import TradingDB; db = TradingDB(); print('Connected!')"
```

## 🚀 Deployment

See `docs/production-deployment.md` (coming soon) for:
- Server setup
- Systemd service configuration (Linux)
- LaunchAgent configuration (macOS)
- Monitoring and logging
- Production best practices

## 📚 Additional Resources

- [Alpaca API Documentation](https://docs.alpaca.markets/)
- [Alpaca Python SDK](https://github.com/alpacahq/alpaca-py)
- [APScheduler Documentation](https://apscheduler.readthedocs.io/)
- [NocoDB Documentation](https://docs.nocodb.com/)

## 📄 License

This project is for personal/internal use. Review and test thoroughly before using with real money.

## ⚠️ Disclaimer

This software is for educational and research purposes. Trading involves risk. Always test with paper trading first. The authors are not responsible for any financial losses.

---

**Status:** Production Ready (Paper Trading)

**Last Updated:** 2025-10-26

**Version:** 1.0.0
