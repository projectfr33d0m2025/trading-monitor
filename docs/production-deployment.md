# Production Deployment Guide

**Last Updated:** 2025-10-26
**Audience:** DevOps/System Administrators deploying the trading monitor to production

---

## Table of Contents

1. [Prerequisites](#prerequisites)
2. [Pre-Deployment Checklist](#pre-deployment-checklist)
3. [Server Setup](#server-setup)
4. [Production Database Setup](#production-database-setup)
5. [Application Deployment](#application-deployment)
6. [Service Configuration](#service-configuration)
7. [Monitoring & Logging](#monitoring--logging)
8. [Security Hardening](#security-hardening)
9. [Backup Strategy](#backup-strategy)
10. [Deployment Verification](#deployment-verification)
11. [Rollback Procedures](#rollback-procedures)

---

## Prerequisites

### Required Resources

- **Production Server** (Linux-based, Ubuntu 20.04+ or similar)
  - Minimum: 2 CPU cores, 4GB RAM, 20GB storage
  - Recommended: 4 CPU cores, 8GB RAM, 50GB storage
- **PostgreSQL Database** (NocoDB-hosted or dedicated)
  - Version 14 or higher
  - Backup enabled
  - Network accessible from production server
- **Alpaca Trading Account** (with live API credentials)
  - Paper trading credentials for initial validation
  - Live trading credentials for production use
- **Domain/Network Access**
  - Firewall rules configured
  - SSL/TLS certificates (if exposing APIs)
  - SSH access to server

### Completed Prerequisites

Before deploying to production, ensure you have:

1. ✅ Completed paper trading validation (1-2 weeks)
2. ✅ All tests passing with >90% coverage
3. ✅ Production database schema created
4. ✅ n8n workflow modified and tested
5. ✅ Monitoring and alerting configured
6. ✅ Backup strategy defined and tested
7. ✅ Rollback procedure documented

---

## Pre-Deployment Checklist

### Code Quality Verification

```bash
# 1. Run full test suite
pytest --cov=. --cov-report=term
# Ensure: All tests pass, coverage >90%

# 2. Verify no uncommitted changes
git status
# Should show: nothing to commit, working tree clean

# 3. Tag release version
git tag -a v1.0.0 -m "Production release v1.0.0"
git push origin v1.0.0

# 4. Create production branch
git checkout -b production
git push -u origin production
```

### Configuration Verification

- [ ] All environment variables documented
- [ ] Production API credentials obtained and secured
- [ ] Database connection strings verified
- [ ] Logging configuration appropriate for production
- [ ] Error notification system configured
- [ ] Backup schedule defined

### Documentation Review

- [ ] README.md is up-to-date
- [ ] API credentials documented (securely)
- [ ] Deployment procedures documented
- [ ] Rollback procedures documented
- [ ] Contact information for support

---

## Server Setup

### 1. Provision Production Server

**Recommended Providers:**
- DigitalOcean (Droplets)
- AWS (EC2)
- Linode
- Vultr
- Any VPS with Ubuntu 20.04+

**Create Server:**

```bash
# Example: DigitalOcean Droplet
# - Ubuntu 22.04 LTS
# - 4GB RAM / 2 CPUs
# - 50GB SSD
# - Region: Closest to Alpaca servers (US East recommended)
```

### 2. Initial Server Configuration

**Connect to server:**

```bash
ssh root@your-server-ip
```

**Update system:**

```bash
# Update package lists
apt-get update && apt-get upgrade -y

# Install basic utilities
apt-get install -y \
  git \
  curl \
  wget \
  vim \
  htop \
  tmux \
  ufw \
  fail2ban

# Set timezone to US Eastern (for trading hours)
timedatectl set-timezone America/New_York

# Verify timezone
timedatectl
```

### 3. Create Application User

```bash
# Create dedicated user (non-root)
adduser trading
usermod -aG sudo trading

# Setup SSH key authentication for trading user
mkdir -p /home/trading/.ssh
cp ~/.ssh/authorized_keys /home/trading/.ssh/
chown -R trading:trading /home/trading/.ssh
chmod 700 /home/trading/.ssh
chmod 600 /home/trading/.ssh/authorized_keys

# Switch to trading user
su - trading
```

### 4. Install Python

```bash
# Install Python 3.10+
sudo apt-get install -y \
  python3.10 \
  python3.10-venv \
  python3-pip \
  python3.10-dev \
  build-essential

# Verify installation
python3 --version
# Should show: Python 3.10.x or higher

# Upgrade pip
pip3 install --upgrade pip
```

### 5. Install PostgreSQL Client

```bash
# Install PostgreSQL client (for connecting to NocoDB)
sudo apt-get install -y postgresql-client

# Verify installation
psql --version
```

---

## Production Database Setup

### Option 1: Using Existing NocoDB Instance

**1. Add Required Fields to analysis_decision Table:**

Follow the guide in [docs/database-setup.md](database-setup.md) to add:
- `signal_decision` (varchar)
- `executed_at` (timestamp)
- `execution_status` (varchar)
- `entry_order_id` (varchar)

**2. Create Additional Tables:**

```bash
# On production server, download creation script
cd /home/trading
git clone <repository-url> trading-monitor
cd trading-monitor

# Edit .env with production database credentials
cp .env.example .env
nano .env

# Set production database connection:
DB_HOST=your-nocodb-host
DB_PORT=5432
DB_NAME=your_db_name
DB_USER=your_db_user
DB_PASSWORD=your_db_password

# Run table creation script
python3 scripts/create_production_tables.py
```

**3. Verify Tables:**

```bash
# Connect to database
psql -h $DB_HOST -U $DB_USER -d $DB_NAME

# List tables
\dt

# Expected tables:
# - analysis_decision (should already exist)
# - trade_journal
# - order_execution
# - position_status

# Verify schema
\d trade_journal
\d order_execution
\d position_status

# Exit
\q
```

### Option 2: Dedicated PostgreSQL Instance

If using a separate PostgreSQL instance:

```bash
# Install PostgreSQL server
sudo apt-get install -y postgresql postgresql-contrib

# Configure PostgreSQL
sudo -u postgres psql

# Create database and user
CREATE DATABASE trading_prod;
CREATE USER trading_user WITH ENCRYPTED PASSWORD 'strong_password_here';
GRANT ALL PRIVILEGES ON DATABASE trading_prod TO trading_user;

# Exit
\q

# Create schema
cd /home/trading/trading-monitor
python3 -c "from db_layer import TradingDB; db = TradingDB(); db.create_schema(); print('✅ Schema created')"
```

---

## Application Deployment

### 1. Clone Repository

```bash
# As trading user
cd /home/trading

# Clone repository
git clone <repository-url> trading-monitor
cd trading-monitor

# Checkout production branch
git checkout production

# Verify clean state
git status
```

### 2. Create Virtual Environment

```bash
# Create virtual environment
python3 -m venv venv

# Activate virtual environment
source venv/bin/activate

# Upgrade pip
pip install --upgrade pip

# Install dependencies
pip install -r requirements.txt

# Verify installation
pip list
```

### 3. Configure Production Environment

```bash
# Create production .env file
cp .env.example .env

# Edit with production settings
nano .env
```

**Production .env Configuration:**

```bash
# Database Configuration (NocoDB or dedicated PostgreSQL)
DB_HOST=your-production-db-host
DB_PORT=5432
DB_NAME=trading_prod
DB_USER=trading_user
DB_PASSWORD=your_secure_password_here

# Alpaca API Configuration - PAPER TRADING (for initial validation)
ALPACA_API_KEY=your_paper_api_key
ALPACA_SECRET_KEY=your_paper_secret_key
ALPACA_BASE_URL=https://paper-api.alpaca.markets

# IMPORTANT: Switch to live trading only after paper trading validation
# ALPACA_API_KEY=your_live_api_key
# ALPACA_SECRET_KEY=your_live_secret_key
# ALPACA_BASE_URL=https://api.alpaca.markets

# System Configuration
LOG_LEVEL=INFO
TRADE_MODE=paper  # Change to 'live' after validation
```

**Secure the .env file:**

```bash
# Set restrictive permissions
chmod 600 .env

# Verify ownership
ls -la .env
# Should show: -rw------- 1 trading trading
```

### 4. Verify Deployment

```bash
# Test database connection
python3 -c "from db_layer import TradingDB; db = TradingDB(); print('✅ Database connected'); db.close()"

# Test Alpaca connection
python3 -c "from alpaca_client import get_trading_client; client = get_trading_client(); print('✅ Alpaca connected'); print('Mode:', client.get_account().status)"

# Run test suite
pytest -v

# Test individual programs
python3 order_executor.py --test-mode
python3 order_monitor.py --test-mode
python3 position_monitor.py --test-mode
```

---

## Service Configuration

### Option 1: systemd (Linux - Recommended)

**1. Create systemd service file:**

```bash
sudo nano /etc/systemd/system/trading-monitor.service
```

**Service file content:**

```ini
[Unit]
Description=Trading Monitor Scheduler
After=network.target postgresql.service
Wants=postgresql.service

[Service]
Type=simple
User=trading
Group=trading
WorkingDirectory=/home/trading/trading-monitor
Environment="PATH=/home/trading/trading-monitor/venv/bin"
ExecStart=/home/trading/trading-monitor/venv/bin/python3 /home/trading/trading-monitor/scheduler.py
Restart=always
RestartSec=10
StandardOutput=append:/home/trading/trading-monitor/logs/service.log
StandardError=append:/home/trading/trading-monitor/logs/service-error.log

# Security hardening
NoNewPrivileges=true
PrivateTmp=true
ProtectSystem=strict
ProtectHome=read-only
ReadWritePaths=/home/trading/trading-monitor/logs

[Install]
WantedBy=multi-user.target
```

**2. Enable and start service:**

```bash
# Create logs directory
mkdir -p /home/trading/trading-monitor/logs

# Reload systemd
sudo systemctl daemon-reload

# Enable service (start on boot)
sudo systemctl enable trading-monitor

# Start service
sudo systemctl start trading-monitor

# Check status
sudo systemctl status trading-monitor

# View logs
sudo journalctl -u trading-monitor -f
```

**3. Useful systemd commands:**

```bash
# Stop service
sudo systemctl stop trading-monitor

# Restart service
sudo systemctl restart trading-monitor

# View logs (last 100 lines)
sudo journalctl -u trading-monitor -n 100

# View logs (follow)
sudo journalctl -u trading-monitor -f

# Disable service
sudo systemctl disable trading-monitor
```

### Option 2: macOS LaunchAgent

**1. Create LaunchAgent plist:**

```bash
nano ~/Library/LaunchAgents/com.trading.monitor.plist
```

**Plist content:**

```xml
<?xml version="1.0" encoding="UTF-8"?>
<!DOCTYPE plist PUBLIC "-//Apple//DTD PLIST 1.0//EN" "http://www.apple.com/DTDs/PropertyList-1.0.dtd">
<plist version="1.0">
<dict>
    <key>Label</key>
    <string>com.trading.monitor</string>

    <key>ProgramArguments</key>
    <array>
        <string>/Users/trading/trading-monitor/venv/bin/python3</string>
        <string>/Users/trading/trading-monitor/scheduler.py</string>
    </array>

    <key>WorkingDirectory</key>
    <string>/Users/trading/trading-monitor</string>

    <key>RunAtLoad</key>
    <true/>

    <key>KeepAlive</key>
    <true/>

    <key>StandardOutPath</key>
    <string>/Users/trading/trading-monitor/logs/service.log</string>

    <key>StandardErrorPath</key>
    <string>/Users/trading/trading-monitor/logs/service-error.log</string>
</dict>
</plist>
```

**2. Load and start:**

```bash
# Load LaunchAgent
launchctl load ~/Library/LaunchAgents/com.trading.monitor.plist

# Start service
launchctl start com.trading.monitor

# Check status
launchctl list | grep trading

# View logs
tail -f ~/trading-monitor/logs/service.log
```

---

## Monitoring & Logging

### 1. Application Logs

**Configure log rotation:**

```bash
# Create logrotate configuration
sudo nano /etc/logrotate.d/trading-monitor
```

**Logrotate configuration:**

```
/home/trading/trading-monitor/logs/*.log {
    daily
    rotate 30
    compress
    delaycompress
    missingok
    notifempty
    create 0640 trading trading
    sharedscripts
    postrotate
        systemctl reload trading-monitor > /dev/null 2>&1 || true
    endscript
}
```

**Test logrotate:**

```bash
sudo logrotate -f /etc/logrotate.d/trading-monitor
```

### 2. System Monitoring

**Install monitoring tools:**

```bash
# Install htop for resource monitoring
sudo apt-get install -y htop

# Monitor in real-time
htop
```

**Create monitoring script:**

```bash
nano /home/trading/check_service.sh
```

**Script content:**

```bash
#!/bin/bash

# Check if service is running
if systemctl is-active --quiet trading-monitor; then
    echo "✅ Service is running"

    # Check last log entry time
    LAST_LOG=$(tail -1 /home/trading/trading-monitor/logs/service.log)
    echo "Last log: $LAST_LOG"

    # Check process
    ps aux | grep scheduler.py | grep -v grep
else
    echo "❌ Service is NOT running"

    # Send alert (configure email/SMS)
    # mail -s "Trading Monitor Down" admin@example.com < /dev/null
fi
```

**Make executable and schedule:**

```bash
chmod +x /home/trading/check_service.sh

# Add to crontab (check every 5 minutes)
crontab -e

# Add line:
*/5 * * * * /home/trading/check_service.sh >> /home/trading/monitoring.log 2>&1
```

### 3. Database Monitoring

**Create database health check script:**

```bash
nano /home/trading/check_database.sh
```

**Script content:**

```bash
#!/bin/bash

cd /home/trading/trading-monitor
source venv/bin/activate

python3 << EOF
from db_layer import TradingDB
import sys

try:
    db = TradingDB()
    cursor = db.get_cursor()
    cursor.execute("SELECT COUNT(*) FROM analysis_decision")
    count = cursor.fetchone()[0]
    print(f"✅ Database connected. Records: {count}")
    cursor.close()
    db.close()
    sys.exit(0)
except Exception as e:
    print(f"❌ Database connection failed: {e}")
    sys.exit(1)
EOF
```

**Make executable:**

```bash
chmod +x /home/trading/check_database.sh
```

---

## Security Hardening

### 1. Firewall Configuration

```bash
# Enable UFW
sudo ufw enable

# Allow SSH (adjust port if using non-standard)
sudo ufw allow 22/tcp

# Allow PostgreSQL (only if running local database)
# sudo ufw allow from your_ip to any port 5432

# Check status
sudo ufw status verbose
```

### 2. SSH Hardening

```bash
# Edit SSH configuration
sudo nano /etc/ssh/sshd_config

# Recommended settings:
# PermitRootLogin no
# PasswordAuthentication no
# PubkeyAuthentication yes
# Port 2222  # Change to non-standard port (optional)

# Restart SSH
sudo systemctl restart sshd
```

### 3. Fail2Ban Configuration

```bash
# Install fail2ban
sudo apt-get install -y fail2ban

# Create local configuration
sudo cp /etc/fail2ban/jail.conf /etc/fail2ban/jail.local

# Edit configuration
sudo nano /etc/fail2ban/jail.local

# Enable SSH jail:
# [sshd]
# enabled = true
# maxretry = 3
# bantime = 3600

# Restart fail2ban
sudo systemctl restart fail2ban

# Check status
sudo fail2ban-client status
```

### 4. Secure API Credentials

```bash
# Ensure .env is secure
chmod 600 /home/trading/trading-monitor/.env
chown trading:trading /home/trading/trading-monitor/.env

# Verify no credentials in git
cd /home/trading/trading-monitor
grep -r "ALPACA_API_KEY" --exclude=.env --exclude-dir=.git .
# Should return no results

# Consider using environment variables instead of .env
sudo nano /etc/environment
# Add:
# ALPACA_API_KEY=your_key
# ALPACA_SECRET_KEY=your_secret
```

---

## Backup Strategy

### 1. Database Backups

**Create backup script:**

```bash
sudo nano /home/trading/backup_database.sh
```

**Script content:**

```bash
#!/bin/bash

BACKUP_DIR="/home/trading/backups"
DATE=$(date +%Y%m%d_%H%M%S)
BACKUP_FILE="$BACKUP_DIR/trading_db_$DATE.sql"

# Create backup directory
mkdir -p $BACKUP_DIR

# Perform backup
PGPASSWORD=$DB_PASSWORD pg_dump \
  -h $DB_HOST \
  -U $DB_USER \
  -d $DB_NAME \
  > $BACKUP_FILE

# Compress backup
gzip $BACKUP_FILE

# Delete backups older than 30 days
find $BACKUP_DIR -name "*.sql.gz" -mtime +30 -delete

echo "✅ Backup created: ${BACKUP_FILE}.gz"
```

**Make executable and schedule:**

```bash
chmod +x /home/trading/backup_database.sh

# Add to crontab (daily at 2 AM)
crontab -e

# Add line:
0 2 * * * /home/trading/backup_database.sh >> /home/trading/backup.log 2>&1
```

### 2. Code Backups

```bash
# Repository is already version controlled
# Ensure regular pushes to remote
cd /home/trading/trading-monitor

# Create backup script
nano /home/trading/backup_code.sh
```

**Script content:**

```bash
#!/bin/bash

cd /home/trading/trading-monitor

# Backup .env file (encrypted)
tar -czf /home/trading/backups/env_backup_$(date +%Y%m%d).tar.gz .env
openssl enc -aes-256-cbc -salt -in /home/trading/backups/env_backup_$(date +%Y%m%d).tar.gz -out /home/trading/backups/env_backup_$(date +%Y%m%d).tar.gz.enc -k your_encryption_password
rm /home/trading/backups/env_backup_$(date +%Y%m%d).tar.gz

# Backup logs
tar -czf /home/trading/backups/logs_backup_$(date +%Y%m%d).tar.gz logs/

echo "✅ Code and logs backed up"
```

---

## Deployment Verification

### 1. Post-Deployment Checks

```bash
# 1. Verify service is running
sudo systemctl status trading-monitor

# 2. Check recent logs
sudo journalctl -u trading-monitor -n 50

# 3. Test database connection
cd /home/trading/trading-monitor
source venv/bin/activate
python3 -c "from db_layer import TradingDB; db = TradingDB(); print('✅ DB OK'); db.close()"

# 4. Test Alpaca connection
python3 -c "from alpaca_client import get_trading_client; c = get_trading_client(); print('✅ Alpaca OK')"

# 5. Verify scheduled jobs
# Wait for next scheduled run and check logs
tail -f logs/service.log
```

### 2. Smoke Tests

```bash
# Run full test suite
pytest -v

# Test order executor manually
python3 order_executor.py --test-mode

# Test order monitor manually
python3 order_monitor.py --test-mode

# Test position monitor manually
python3 position_monitor.py --test-mode
```

### 3. Paper Trading Validation

**CRITICAL:** Always validate with paper trading before live trading!

```bash
# Ensure .env has paper trading settings
grep ALPACA_BASE_URL .env
# Should show: ALPACA_BASE_URL=https://paper-api.alpaca.markets

# Ensure trade mode is paper
grep TRADE_MODE .env
# Should show: TRADE_MODE=paper

# Run for 1-2 weeks and monitor:
# - All trades execute correctly
# - Stop losses are placed
# - Take profits are placed
# - Positions are tracked
# - P&L is calculated correctly
# - Logs show no errors
```

---

## Rollback Procedures

### 1. Rollback Service

```bash
# Stop service
sudo systemctl stop trading-monitor

# Checkout previous version
cd /home/trading/trading-monitor
git log --oneline  # Find previous version
git checkout <previous-commit-hash>

# Restart service
sudo systemctl start trading-monitor

# Verify
sudo systemctl status trading-monitor
```

### 2. Rollback Database

```bash
# Restore from backup
BACKUP_FILE="/home/trading/backups/trading_db_20251025_020000.sql.gz"

# Decompress
gunzip $BACKUP_FILE

# Restore
PGPASSWORD=$DB_PASSWORD psql \
  -h $DB_HOST \
  -U $DB_USER \
  -d $DB_NAME \
  < ${BACKUP_FILE%.gz}

echo "✅ Database restored"
```

### 3. Emergency Shutdown

```bash
# Stop service immediately
sudo systemctl stop trading-monitor

# Cancel all open orders via Alpaca UI
# Visit: https://app.alpaca.markets/paper/dashboard/orders

# Or via API:
cd /home/trading/trading-monitor
source venv/bin/activate
python3 << EOF
from alpaca_client import get_trading_client
client = get_trading_client()
orders = client.get_orders()
for order in orders:
    if order.status in ['new', 'partially_filled', 'accepted']:
        client.cancel_order_by_id(order.id)
        print(f"Cancelled order: {order.id}")
EOF
```

---

## Going Live

### Prerequisites for Live Trading

- [ ] Completed 1-2 weeks of paper trading validation
- [ ] All test scenarios passed
- [ ] No errors in logs during paper trading
- [ ] Database backup strategy working
- [ ] Monitoring and alerting configured
- [ ] Rollback procedure tested
- [ ] Live API credentials obtained

### Switch to Live Trading

```bash
# 1. Stop service
sudo systemctl stop trading-monitor

# 2. Update .env
cd /home/trading/trading-monitor
nano .env

# Change to live credentials:
ALPACA_API_KEY=your_live_api_key
ALPACA_SECRET_KEY=your_live_secret_key
ALPACA_BASE_URL=https://api.alpaca.markets
TRADE_MODE=live

# 3. Verify configuration
grep ALPACA_BASE_URL .env
grep TRADE_MODE .env

# 4. Test connection
source venv/bin/activate
python3 -c "from alpaca_client import get_trading_client; c = get_trading_client(); a = c.get_account(); print(f'✅ Live trading connected. Buying power: ${a.buying_power}')"

# 5. Restart service
sudo systemctl start trading-monitor

# 6. Monitor closely for first few days
tail -f logs/service.log
```

---

## Support and Maintenance

### Regular Maintenance Tasks

**Daily:**
- Check service status
- Review logs for errors
- Monitor trade executions

**Weekly:**
- Review P&L
- Check database size
- Verify backups

**Monthly:**
- Update dependencies
- Review and optimize code
- Test rollback procedures

### Useful Commands

```bash
# Service management
sudo systemctl status trading-monitor
sudo systemctl restart trading-monitor
sudo journalctl -u trading-monitor -f

# Database queries
psql -h $DB_HOST -U $DB_USER -d $DB_NAME

# View recent trades
# SELECT * FROM trade_journal ORDER BY created_at DESC LIMIT 10;

# Check service health
/home/trading/check_service.sh

# View resource usage
htop
df -h
```

---

**Last Updated:** 2025-10-26 by Claude Code
