# Operational Runbook

**Last Updated:** 2025-10-26
**Audience:** System operators and support staff managing the trading monitor system

---

## Table of Contents

1. [System Overview](#system-overview)
2. [Daily Operations](#daily-operations)
3. [Common Tasks](#common-tasks)
4. [Troubleshooting Guide](#troubleshooting-guide)
5. [Emergency Procedures](#emergency-procedures)
6. [Monitoring & Alerts](#monitoring--alerts)
7. [Database Operations](#database-operations)
8. [Trade Lifecycle Management](#trade-lifecycle-management)
9. [Performance Optimization](#performance-optimization)
10. [FAQ](#faq)

---

## System Overview

### Architecture

```
┌─────────────────┐
│   n8n Workflow  │ (Trading signals)
└────────┬────────┘
         │
         v
┌─────────────────┐
│  PostgreSQL DB  │ (analysis_decision table)
└────────┬────────┘
         │
         v
┌─────────────────┐      ┌─────────────────┐
│ Order Executor  │─────>│   Alpaca API    │
│  (9:45 AM ET)   │      └─────────────────┘
└─────────────────┘
         │
         v
┌─────────────────┐      ┌─────────────────┐
│ Order Monitor   │─────>│   Alpaca API    │
│  (Every 5 min)  │      └─────────────────┘
└─────────────────┘
         │
         v
┌─────────────────┐      ┌─────────────────┐
│Position Monitor │─────>│   Alpaca API    │
│  (Every 10 min) │      └─────────────────┘
└─────────────────┘
```

### Components

1. **Order Executor** - Places entry orders based on trading signals
2. **Order Monitor** - Tracks order status, places SL/TP orders
3. **Position Monitor** - Updates position values and P&L
4. **Scheduler** - Runs programs on schedule (APScheduler)
5. **Database Layer** - PostgreSQL abstraction for all data operations
6. **Alpaca Client** - API helpers for broker integration

### Key Files

```
/home/trading/trading-monitor/
├── scheduler.py           # Main entry point (runs all programs)
├── order_executor.py      # Entry order placement
├── order_monitor.py       # Order status tracking
├── position_monitor.py    # Position value updates
├── db_layer.py           # Database operations
├── alpaca_client.py      # Alpaca API helpers
├── config.py             # Configuration management
├── .env                  # Environment variables (SECURE!)
└── logs/                 # Application logs
    ├── service.log       # Main service log
    └── service-error.log # Error log
```

---

## Daily Operations

### Morning Routine (Before Market Open)

**Time: 9:00 AM - 9:30 AM ET**

```bash
# 1. SSH to production server
ssh trading@your-server-ip

# 2. Check service status
sudo systemctl status trading-monitor
# Expected: active (running)

# 3. Review overnight logs
tail -100 /home/trading/trading-monitor/logs/service.log

# 4. Check for new trading signals
cd /home/trading/trading-monitor
source venv/bin/activate
python3 << EOF
from db_layer import TradingDB
db = TradingDB()
cursor = db.get_cursor()
cursor.execute("SELECT COUNT(*) FROM analysis_decision WHERE signal_decision = 'EXECUTE' AND execution_status IS NULL")
pending = cursor.fetchone()[0]
print(f"📊 Pending orders: {pending}")
cursor.close()
db.close()
EOF

# 5. Verify Alpaca connection
python3 -c "from alpaca_client import get_trading_client; c = get_trading_client(); a = c.get_account(); print(f'✅ Alpaca connected. Buying power: \${a.buying_power}')"

# 6. Check database connectivity
python3 -c "from db_layer import TradingDB; db = TradingDB(); print('✅ Database connected'); db.close()"

# 7. Review market calendar (is market open today?)
python3 << EOF
from alpaca_client import get_trading_client
from datetime import date
client = get_trading_client()
calendar = client.get_calendar(start=date.today(), end=date.today())
if calendar:
    print(f"✅ Market OPEN today")
    print(f"   Opens: {calendar[0].open}")
    print(f"   Closes: {calendar[0].close}")
else:
    print("⚠️  Market CLOSED today")
EOF
```

### Mid-Day Check (During Market Hours)

**Time: 12:00 PM ET**

```bash
# 1. Check for execution errors
sudo journalctl -u trading-monitor --since "09:00" | grep ERROR

# 2. Review executed trades today
cd /home/trading/trading-monitor
source venv/bin/activate
python3 << EOF
from db_layer import TradingDB
from datetime import date
db = TradingDB()
cursor = db.get_cursor()
cursor.execute("""
    SELECT symbol, action, quantity, entry_price, current_status
    FROM trade_journal
    WHERE DATE(entry_time) = %s
    ORDER BY entry_time DESC
""", (date.today(),))
trades = cursor.fetchall()
print(f"📊 Trades today: {len(trades)}")
for trade in trades:
    print(f"   {trade[0]} {trade[1]} {trade[2]} @ \${trade[3]} - {trade[4]}")
cursor.close()
db.close()
EOF

# 3. Check open positions
python3 << EOF
from alpaca_client import get_trading_client
client = get_trading_client()
positions = client.get_all_positions()
print(f"📊 Open positions: {len(positions)}")
for pos in positions:
    pnl_pct = (float(pos.unrealized_plpc) * 100)
    print(f"   {pos.symbol}: {pos.qty} @ \${pos.avg_entry_price} (P&L: {pnl_pct:.2f}%)")
EOF

# 4. Check for stuck orders
python3 << EOF
from alpaca_client import get_trading_client
client = get_trading_client()
orders = client.get_orders(status='open')
print(f"📊 Open orders: {len(orders)}")
for order in orders:
    print(f"   {order.symbol} {order.side} {order.qty} @ \${order.limit_price} - {order.status}")
EOF
```

### End of Day Review (After Market Close)

**Time: 4:30 PM - 5:00 PM ET**

```bash
# 1. Review day's performance
cd /home/trading/trading-monitor
source venv/bin/activate
python3 << EOF
from db_layer import TradingDB
from datetime import date
db = TradingDB()
cursor = db.get_cursor()

# Closed trades today
cursor.execute("""
    SELECT COUNT(*), SUM(realized_pnl)
    FROM trade_journal
    WHERE DATE(exit_time) = %s
""", (date.today(),))
closed_count, total_pnl = cursor.fetchone()
print(f"📊 Closed trades: {closed_count}")
print(f"💰 Total P&L: \${total_pnl or 0:.2f}")

# Still open
cursor.execute("""
    SELECT COUNT(*)
    FROM trade_journal
    WHERE current_status = 'open'
""")
open_count = cursor.fetchone()[0]
print(f"📊 Still open: {open_count}")

cursor.close()
db.close()
EOF

# 2. Check for any errors during the day
sudo journalctl -u trading-monitor --since "09:00" | grep -i error

# 3. Verify all SL orders are placed
python3 << EOF
from db_layer import TradingDB
db = TradingDB()
cursor = db.get_cursor()
cursor.execute("""
    SELECT symbol FROM trade_journal
    WHERE current_status = 'open'
    AND sl_order_id IS NULL
""")
missing_sl = cursor.fetchall()
if missing_sl:
    print(f"⚠️  Trades missing SL orders: {[t[0] for t in missing_sl]}")
else:
    print("✅ All open trades have SL orders")
cursor.close()
db.close()
EOF

# 4. Check system resources
df -h  # Disk space
free -h  # Memory
top -bn1 | head -20  # CPU and processes
```

---

## Common Tasks

### Check Service Status

```bash
# Status
sudo systemctl status trading-monitor

# Start
sudo systemctl start trading-monitor

# Stop
sudo systemctl stop trading-monitor

# Restart
sudo systemctl restart trading-monitor

# Enable (start on boot)
sudo systemctl enable trading-monitor

# Disable (don't start on boot)
sudo systemctl disable trading-monitor
```

### View Logs

```bash
# View last 50 lines
sudo journalctl -u trading-monitor -n 50

# Follow logs in real-time
sudo journalctl -u trading-monitor -f

# View logs since specific time
sudo journalctl -u trading-monitor --since "2025-10-26 09:00:00"

# View logs between time range
sudo journalctl -u trading-monitor --since "09:00" --until "12:00"

# View only errors
sudo journalctl -u trading-monitor -p err

# View application logs
tail -f /home/trading/trading-monitor/logs/service.log
tail -f /home/trading/trading-monitor/logs/service-error.log
```

### Manual Program Execution

```bash
cd /home/trading/trading-monitor
source venv/bin/activate

# Run order executor manually (test mode)
python3 order_executor.py --test-mode

# Run order executor (real execution)
python3 order_executor.py

# Run order monitor
python3 order_monitor.py

# Run position monitor
python3 position_monitor.py
```

### Database Queries

```bash
cd /home/trading/trading-monitor
source venv/bin/activate

# Connect to database
python3 << EOF
from db_layer import TradingDB
db = TradingDB()
cursor = db.get_cursor()

# Your queries here
cursor.execute("SELECT * FROM trade_journal ORDER BY entry_time DESC LIMIT 10")
rows = cursor.fetchall()
for row in rows:
    print(row)

cursor.close()
db.close()
EOF
```

### Update Code from Repository

```bash
# Stop service
sudo systemctl stop trading-monitor

# Backup current version
cd /home/trading/trading-monitor
git log -1 --oneline > /tmp/current_version.txt

# Pull latest changes
git pull origin production

# Install any new dependencies
source venv/bin/activate
pip install -r requirements.txt

# Run tests
pytest -v

# Restart service
sudo systemctl start trading-monitor

# Verify
sudo systemctl status trading-monitor
```

---

## Troubleshooting Guide

### Service Won't Start

**Symptoms:**
- `systemctl status` shows "failed" or "inactive"
- Service stops immediately after starting

**Diagnosis:**

```bash
# Check service logs
sudo journalctl -u trading-monitor -n 100

# Check for Python errors
sudo journalctl -u trading-monitor | grep -i traceback

# Try running manually
cd /home/trading/trading-monitor
source venv/bin/activate
python3 scheduler.py
# Watch for errors
```

**Common Causes & Solutions:**

1. **Database Connection Failed**
   ```bash
   # Test database connection
   python3 -c "from db_layer import TradingDB; db = TradingDB()"

   # Check .env configuration
   cat .env | grep DB_

   # Verify database is accessible
   psql -h $DB_HOST -U $DB_USER -d $DB_NAME
   ```

2. **Alpaca API Credentials Invalid**
   ```bash
   # Test Alpaca connection
   python3 -c "from alpaca_client import get_trading_client; get_trading_client()"

   # Check .env configuration
   cat .env | grep ALPACA_

   # Verify credentials at: https://alpaca.markets
   ```

3. **Missing Dependencies**
   ```bash
   # Reinstall dependencies
   source venv/bin/activate
   pip install -r requirements.txt --force-reinstall
   ```

4. **Permission Issues**
   ```bash
   # Check file ownership
   ls -la /home/trading/trading-monitor/

   # Fix ownership
   sudo chown -R trading:trading /home/trading/trading-monitor/

   # Check log directory
   ls -la /home/trading/trading-monitor/logs/
   mkdir -p /home/trading/trading-monitor/logs/
   ```

### Orders Not Executing

**Symptoms:**
- `analysis_decision` has `signal_decision = 'EXECUTE'`
- No orders placed with Alpaca
- No errors in logs

**Diagnosis:**

```bash
# Check pending signals
cd /home/trading/trading-monitor
source venv/bin/activate
python3 << EOF
from db_layer import TradingDB
db = TradingDB()
cursor = db.get_cursor()
cursor.execute("""
    SELECT id, symbol, signal_decision, execution_status
    FROM analysis_decision
    WHERE signal_decision = 'EXECUTE'
    AND execution_status IS NULL
""")
pending = cursor.fetchall()
print(f"Pending signals: {len(pending)}")
for p in pending:
    print(p)
cursor.close()
db.close()
EOF

# Check when order executor last ran
sudo journalctl -u trading-monitor | grep "Order Executor" | tail -5

# Check if market is open
python3 << EOF
from alpaca_client import get_trading_client
client = get_trading_client()
clock = client.get_clock()
print(f"Market open: {clock.is_open}")
print(f"Next open: {clock.next_open}")
EOF
```

**Common Causes & Solutions:**

1. **Market is Closed**
   - Orders only execute when market is open
   - Check market calendar
   - Wait for next market open

2. **Order Executor Not Running on Schedule**
   ```bash
   # Check scheduler is running
   ps aux | grep scheduler.py

   # Check APScheduler logs
   sudo journalctl -u trading-monitor | grep APScheduler

   # Manually trigger order executor
   python3 order_executor.py
   ```

3. **Insufficient Buying Power**
   ```bash
   # Check account buying power
   python3 -c "from alpaca_client import get_trading_client; c = get_trading_client(); print(c.get_account().buying_power)"
   ```

4. **Symbol Not Tradable**
   ```bash
   # Check if symbol is tradable
   python3 << EOF
   from alpaca_client import get_trading_client
   client = get_trading_client()
   asset = client.get_asset('SYMBOL')
   print(f"Tradable: {asset.tradable}")
   print(f"Shortable: {asset.shortable}")
   EOF
   ```

### Stop Loss Orders Not Placed

**Symptoms:**
- Positions are open
- No SL orders in Alpaca
- `sl_order_id` is NULL in database

**Diagnosis:**

```bash
# Check trades without SL orders
cd /home/trading/trading-monitor
source venv/bin/activate
python3 << EOF
from db_layer import TradingDB
db = TradingDB()
cursor = db.get_cursor()
cursor.execute("""
    SELECT symbol, entry_order_id, sl_order_id
    FROM trade_journal
    WHERE current_status = 'open'
    AND sl_order_id IS NULL
""")
missing = cursor.fetchall()
print(f"Trades missing SL: {len(missing)}")
for m in missing:
    print(m)
cursor.close()
db.close()
EOF

# Check order monitor logs
sudo journalctl -u trading-monitor | grep "Order Monitor" | tail -20
```

**Solutions:**

```bash
# Manually trigger order monitor
cd /home/trading/trading-monitor
source venv/bin/activate
python3 order_monitor.py

# Check logs for errors
tail -50 /home/trading/trading-monitor/logs/service-error.log
```

### Database Connection Lost

**Symptoms:**
- Logs show "connection refused" or "connection timeout"
- Programs fail with database errors

**Diagnosis:**

```bash
# Test database connection
psql -h $DB_HOST -U $DB_USER -d $DB_NAME

# Check network connectivity
ping $DB_HOST

# Check if database server is running
# (if local)
sudo systemctl status postgresql
```

**Solutions:**

1. **Restart Database Connection**
   ```bash
   # Restart service (will reconnect)
   sudo systemctl restart trading-monitor
   ```

2. **Check Database Server**
   ```bash
   # If local PostgreSQL
   sudo systemctl restart postgresql

   # If cloud database, check provider status
   ```

3. **Check Firewall Rules**
   ```bash
   # Ensure database port is accessible
   telnet $DB_HOST 5432
   ```

### High Memory Usage

**Symptoms:**
- Server becomes slow
- Out of memory errors
- Service crashes

**Diagnosis:**

```bash
# Check memory usage
free -h

# Check process memory
ps aux --sort=-%mem | head -10

# Check trading-monitor memory
ps aux | grep scheduler.py
```

**Solutions:**

```bash
# Restart service (clears memory)
sudo systemctl restart trading-monitor

# Check for memory leaks
# Monitor over time
watch -n 5 'ps aux | grep scheduler.py'

# Consider upgrading server if consistently high
```

---

## Emergency Procedures

### Emergency Shutdown

**When to use:**
- System malfunction
- Unexpected trading behavior
- Security breach
- Critical bug discovered

**Procedure:**

```bash
# 1. IMMEDIATELY stop the service
sudo systemctl stop trading-monitor

# 2. Verify service is stopped
sudo systemctl status trading-monitor
# Should show: inactive (dead)

# 3. Cancel all open orders via Alpaca
cd /home/trading/trading-monitor
source venv/bin/activate
python3 << EOF
from alpaca_client import get_trading_client
client = get_trading_client()
orders = client.get_orders(status='open')
print(f"Cancelling {len(orders)} open orders...")
for order in orders:
    try:
        client.cancel_order_by_id(order.id)
        print(f"✅ Cancelled: {order.symbol} {order.side} {order.qty}")
    except Exception as e:
        print(f"❌ Failed to cancel {order.id}: {e}")
EOF

# 4. Check open positions (decide if to close)
python3 << EOF
from alpaca_client import get_trading_client
client = get_trading_client()
positions = client.get_all_positions()
print(f"Open positions: {len(positions)}")
for pos in positions:
    print(f"{pos.symbol}: {pos.qty} @ \${pos.avg_entry_price}")
EOF

# 5. (Optional) Close all positions
python3 << EOF
from alpaca_client import get_trading_client
client = get_trading_client()
client.close_all_positions(cancel_orders=True)
print("✅ All positions closed")
EOF

# 6. Document the incident
echo "Emergency shutdown at $(date)" >> /home/trading/incident.log
echo "Reason: <describe reason>" >> /home/trading/incident.log

# 7. Notify team
# Send email/Slack notification
```

### Rollback to Previous Version

```bash
# 1. Stop service
sudo systemctl stop trading-monitor

# 2. Check current version
cd /home/trading/trading-monitor
git log -1 --oneline

# 3. View recent commits
git log --oneline -10

# 4. Rollback to specific commit
git checkout <commit-hash>

# 5. Verify
git log -1 --oneline

# 6. Restart service
sudo systemctl start trading-monitor

# 7. Monitor logs
sudo journalctl -u trading-monitor -f
```

### Restore Database from Backup

```bash
# 1. Stop service
sudo systemctl stop trading-monitor

# 2. List available backups
ls -lh /home/trading/backups/

# 3. Choose backup to restore
BACKUP_FILE="/home/trading/backups/trading_db_20251025_020000.sql.gz"

# 4. Decompress backup
gunzip -c $BACKUP_FILE > /tmp/restore.sql

# 5. Restore database
PGPASSWORD=$DB_PASSWORD psql \
  -h $DB_HOST \
  -U $DB_USER \
  -d $DB_NAME \
  < /tmp/restore.sql

# 6. Verify restoration
psql -h $DB_HOST -U $DB_USER -d $DB_NAME -c "SELECT COUNT(*) FROM trade_journal"

# 7. Clean up
rm /tmp/restore.sql

# 8. Restart service
sudo systemctl start trading-monitor
```

### Handle Stuck Positions

**Scenario:** Position exists in Alpaca but not tracked in database

```bash
cd /home/trading/trading-monitor
source venv/bin/activate

# 1. List Alpaca positions
python3 << EOF
from alpaca_client import get_trading_client
client = get_trading_client()
positions = client.get_all_positions()
for pos in positions:
    print(f"{pos.symbol}: {pos.qty} @ \${pos.avg_entry_price}")
EOF

# 2. Check database
python3 << EOF
from db_layer import TradingDB
db = TradingDB()
cursor = db.get_cursor()
cursor.execute("SELECT symbol, quantity FROM trade_journal WHERE current_status = 'open'")
db_positions = {row[0]: row[1] for row in cursor.fetchall()}
print("Database positions:", db_positions)
cursor.close()
db.close()
EOF

# 3. Manually close position in Alpaca (if needed)
python3 << EOF
from alpaca_client import get_trading_client
client = get_trading_client()
client.close_position('SYMBOL')
print("✅ Position closed")
EOF

# 4. Update database to match
python3 << EOF
from db_layer import TradingDB
db = TradingDB()
cursor = db.get_cursor()
cursor.execute("""
    UPDATE trade_journal
    SET current_status = 'closed',
        exit_time = NOW(),
        exit_reason = 'manual_close'
    WHERE symbol = %s
    AND current_status = 'open'
""", ('SYMBOL',))
db.conn.commit()
print("✅ Database updated")
cursor.close()
db.close()
EOF
```

---

## Monitoring & Alerts

### Key Metrics to Monitor

1. **Service Health**
   - Service uptime
   - Last successful run of each program
   - Error count in logs

2. **Trading Activity**
   - Number of trades per day
   - Win rate
   - Average P&L
   - Open positions count

3. **System Resources**
   - CPU usage
   - Memory usage
   - Disk space
   - Database connections

4. **API Health**
   - Alpaca API response time
   - Database query time
   - Failed API calls

### Alert Triggers

**Critical (Immediate Action Required):**
- Service stopped unexpectedly
- Database connection lost
- Alpaca API authentication failed
- Disk space >90%
- Memory usage >90%

**Warning (Review Soon):**
- No trades executed in 2+ days (when signals present)
- Order execution failure rate >10%
- Unusual P&L (>5% loss in single day)
- High API error rate (>5%)

**Info (For Awareness):**
- Service restarted
- Daily trade summary
- Weekly performance report

### Setting Up Alerts

**Using Cron for Email Alerts:**

```bash
# Create monitoring script
cat > /home/trading/monitor_alerts.sh << 'EOF'
#!/bin/bash

cd /home/trading/trading-monitor
source venv/bin/activate

# Check service health
if ! systemctl is-active --quiet trading-monitor; then
    echo "CRITICAL: Trading monitor service is DOWN" | mail -s "ALERT: Service Down" admin@example.com
fi

# Check disk space
DISK_USAGE=$(df -h / | tail -1 | awk '{print $5}' | sed 's/%//')
if [ $DISK_USAGE -gt 90 ]; then
    echo "WARNING: Disk usage is at ${DISK_USAGE}%" | mail -s "ALERT: Low Disk Space" admin@example.com
fi

# Check for errors in last hour
ERROR_COUNT=$(sudo journalctl -u trading-monitor --since "1 hour ago" | grep -c ERROR)
if [ $ERROR_COUNT -gt 10 ]; then
    echo "WARNING: ${ERROR_COUNT} errors in last hour" | mail -s "ALERT: High Error Rate" admin@example.com
fi
EOF

chmod +x /home/trading/monitor_alerts.sh

# Add to crontab (run every 15 minutes)
crontab -e
# Add line:
*/15 * * * * /home/trading/monitor_alerts.sh
```

---

## Database Operations

### Common Queries

```python
# Connect and run queries
cd /home/trading/trading-monitor
source venv/bin/activate

python3 << EOF
from db_layer import TradingDB
db = TradingDB()
cursor = db.get_cursor()

# Get all open trades
cursor.execute("""
    SELECT symbol, action, quantity, entry_price, current_status
    FROM trade_journal
    WHERE current_status = 'open'
""")
for row in cursor.fetchall():
    print(row)

# Get daily P&L
cursor.execute("""
    SELECT DATE(exit_time) as date, SUM(realized_pnl) as pnl
    FROM trade_journal
    WHERE exit_time IS NOT NULL
    GROUP BY DATE(exit_time)
    ORDER BY date DESC
    LIMIT 30
""")
for row in cursor.fetchall():
    print(f"{row[0]}: ${row[1]:.2f}")

# Get win rate
cursor.execute("""
    SELECT
        COUNT(*) as total_trades,
        SUM(CASE WHEN realized_pnl > 0 THEN 1 ELSE 0 END) as winning_trades,
        SUM(CASE WHEN realized_pnl > 0 THEN 1 ELSE 0 END)::float / COUNT(*)::float * 100 as win_rate
    FROM trade_journal
    WHERE current_status = 'closed'
""")
total, winning, rate = cursor.fetchone()
print(f"Total: {total}, Winning: {winning}, Win Rate: {rate:.2f}%")

cursor.close()
db.close()
EOF
```

### Database Maintenance

```bash
# Vacuum database (reclaim space)
PGPASSWORD=$DB_PASSWORD psql \
  -h $DB_HOST \
  -U $DB_USER \
  -d $DB_NAME \
  -c "VACUUM ANALYZE"

# Check database size
PGPASSWORD=$DB_PASSWORD psql \
  -h $DB_HOST \
  -U $DB_USER \
  -d $DB_NAME \
  -c "SELECT pg_size_pretty(pg_database_size('$DB_NAME'))"

# Check table sizes
PGPASSWORD=$DB_PASSWORD psql \
  -h $DB_HOST \
  -U $DB_USER \
  -d $DB_NAME \
  -c "SELECT tablename, pg_size_pretty(pg_total_relation_size(schemaname||'.'||tablename)) AS size FROM pg_tables WHERE schemaname = 'public' ORDER BY pg_total_relation_size(schemaname||'.'||tablename) DESC"
```

---

## Trade Lifecycle Management

### Normal Trade Flow

1. **Signal Generation** (n8n workflow)
   - Creates `analysis_decision` with `signal_decision = 'EXECUTE'`

2. **Order Execution** (9:45 AM ET)
   - Order Executor places entry order
   - Creates `trade_journal` record
   - Creates `order_execution` record

3. **Order Monitoring** (Every 5 min)
   - Syncs order status
   - Detects filled entry orders
   - Places SL order (all trades)
   - Places TP order (SWING trades only)

4. **Position Monitoring** (Every 10 min)
   - Updates position values
   - Calculates unrealized P&L

5. **Exit Detection** (Order Monitor)
   - Detects filled SL/TP orders
   - Calculates realized P&L
   - Closes trade
   - Cancels remaining orders

### Manual Trade Management

**Close a specific trade:**

```python
cd /home/trading/trading-monitor
source venv/bin/activate

python3 << EOF
from alpaca_client import get_trading_client
from db_layer import TradingDB

# Close position in Alpaca
symbol = 'AAPL'
client = get_trading_client()
client.close_position(symbol)
print(f"✅ {symbol} position closed")

# Update database
db = TradingDB()
cursor = db.get_cursor()
cursor.execute("""
    UPDATE trade_journal
    SET current_status = 'closed',
        exit_time = NOW(),
        exit_reason = 'manual_close'
    WHERE symbol = %s
    AND current_status = 'open'
""", (symbol,))
db.conn.commit()
print(f"✅ Database updated")
cursor.close()
db.close()
EOF
```

**Cancel a specific order:**

```python
cd /home/trading/trading-monitor
source venv/bin/activate

python3 << EOF
from alpaca_client import get_trading_client

order_id = 'order_id_here'
client = get_trading_client()
client.cancel_order_by_id(order_id)
print(f"✅ Order {order_id} cancelled")
EOF
```

---

## Performance Optimization

### Database Optimization

```sql
-- Create indices (should already exist from schema)
CREATE INDEX IF NOT EXISTS idx_trade_journal_status ON trade_journal(current_status);
CREATE INDEX IF NOT EXISTS idx_trade_journal_symbol ON trade_journal(symbol);
CREATE INDEX IF NOT EXISTS idx_analysis_decision_signal ON analysis_decision(signal_decision);

-- Analyze tables
ANALYZE trade_journal;
ANALYZE order_execution;
ANALYZE position_status;
ANALYZE analysis_decision;
```

### Log Rotation

Ensure logs don't fill up disk:

```bash
# Check log sizes
du -sh /home/trading/trading-monitor/logs/*

# Configure logrotate (should be set up already)
cat /etc/logrotate.d/trading-monitor
```

### Resource Monitoring

```bash
# Monitor resource usage over time
watch -n 5 'ps aux | grep scheduler.py | grep -v grep'

# Check I/O
iostat -x 5

# Check network
iftop
```

---

## FAQ

### Q: How do I check if the system is working?

```bash
# Quick health check
sudo systemctl status trading-monitor
tail -20 /home/trading/trading-monitor/logs/service.log
python3 -c "from db_layer import TradingDB; db = TradingDB(); print('✅ DB OK'); db.close()"
```

### Q: Why are no orders executing?

Check:
1. Market is open
2. Signals exist in database (`signal_decision = 'EXECUTE'`)
3. Order Executor ran at 9:45 AM ET
4. Sufficient buying power
5. No errors in logs

### Q: How do I temporarily pause trading?

```bash
# Stop the service
sudo systemctl stop trading-monitor

# To resume
sudo systemctl start trading-monitor
```

### Q: How do I check today's performance?

```python
cd /home/trading/trading-monitor
source venv/bin/activate
python3 << EOF
from db_layer import TradingDB
from datetime import date
db = TradingDB()
cursor = db.get_cursor()
cursor.execute("SELECT SUM(realized_pnl) FROM trade_journal WHERE DATE(exit_time) = %s", (date.today(),))
pnl = cursor.fetchone()[0] or 0
print(f"Today's P&L: \${pnl:.2f}")
cursor.close()
db.close()
EOF
```

### Q: What if I want to add a trade manually?

Not recommended. Let the system handle all trades. If necessary, document manual trades separately.

### Q: How do I update the code?

See [Common Tasks > Update Code from Repository](#update-code-from-repository)

---

## Contact & Support

### Escalation Path

1. **Check logs** for errors
2. **Review this runbook** for solutions
3. **Check documentation** in `docs/`
4. **Contact development team**

### Useful Resources

- [README.md](../README.md) - Main documentation
- [Development Setup Guide](development-setup.md)
- [Production Deployment Guide](production-deployment.md)
- [Database Setup Guide](database-setup.md)
- Alpaca API Docs: https://alpaca.markets/docs/

---

**Last Updated:** 2025-10-26 by Claude Code
