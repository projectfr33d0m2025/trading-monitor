# Paper Trading Validation Checklist

**Last Updated:** 2025-10-26
**Purpose:** Comprehensive validation checklist for paper trading phase
**Duration:** Minimum 1-2 weeks (10+ trading days recommended)

---

## Overview

This checklist ensures the trading monitor system is thoroughly validated with real market data before deploying to live trading. **DO NOT skip this phase** - it's your last line of defense against costly bugs.

### Validation Goals

- ✅ Verify all trading logic works correctly
- ✅ Validate order execution and management
- ✅ Ensure P&L calculations are accurate
- ✅ Confirm error handling works in production
- ✅ Test all trade scenarios (LONG/SHORT, DAY/SWING)
- ✅ Build confidence for live trading

### Success Criteria

All items in this checklist must be checked off before proceeding to live trading.

---

## Pre-Validation Setup

### Environment Configuration

- [ ] **Paper trading environment configured**
  ```bash
  cat .env | grep ALPACA_BASE_URL
  # Must show: https://paper-api.alpaca.markets
  ```

- [ ] **Trade mode set to paper**
  ```bash
  cat .env | grep TRADE_MODE
  # Must show: paper
  ```

- [ ] **Database connection verified**
  ```bash
  python3 -c "from db_layer import TradingDB; db = TradingDB(); print('✅ DB connected'); db.close()"
  ```

- [ ] **Alpaca paper trading connection verified**
  ```bash
  python3 -c "from alpaca_client import get_trading_client; c = get_trading_client(); a = c.get_account(); print(f'✅ Paper trading active. Buying power: \${a.buying_power}')"
  ```

- [ ] **Service running and scheduled correctly**
  ```bash
  sudo systemctl status trading-monitor
  # Should show: active (running)
  ```

- [ ] **Log monitoring setup**
  ```bash
  tail -f /home/trading/trading-monitor/logs/service.log
  ```

### Paper Trading Account

- [ ] **Alpaca paper account reset to starting balance**
  - Visit: https://app.alpaca.markets/paper/dashboard/overview
  - Click "Reset Account" to start fresh
  - Verify starting balance (e.g., $100,000)

- [ ] **No existing positions**
  ```bash
  python3 -c "from alpaca_client import get_trading_client; c = get_trading_client(); print(f'Positions: {len(c.get_all_positions())}')"
  # Should show: 0
  ```

- [ ] **No open orders**
  ```bash
  python3 -c "from alpaca_client import get_trading_client; c = get_trading_client(); print(f'Orders: {len(c.get_orders(status=\"open\"))}')"
  # Should show: 0
  ```

### Database Preparation

- [ ] **Production database tables created**
  ```bash
  python3 -c "from db_layer import TradingDB; db = TradingDB(); cursor = db.get_cursor(); cursor.execute(\"SELECT table_name FROM information_schema.tables WHERE table_schema='public'\"); print([r[0] for r in cursor.fetchall()]); cursor.close(); db.close()"
  # Should show: analysis_decision, trade_journal, order_execution, position_status
  ```

- [ ] **Database backup taken before starting**
  ```bash
  /home/trading/backup_database.sh
  ```

- [ ] **n8n workflow configured and tested**
  - Signals being written to `analysis_decision` table
  - Fields populated: symbol, signal_type, signal_decision, entry_price, stop_loss, take_profit, trade_type, quantity

### Monitoring Setup

- [ ] **Daily checklist prepared** (see Daily Validation section)
- [ ] **Performance tracking spreadsheet created**
- [ ] **Alert thresholds defined**
- [ ] **Logs being saved and rotated**

---

## Day 1: Initial Validation

### Morning Setup (Before Market Open)

- [ ] **Service status check**
  ```bash
  sudo systemctl status trading-monitor
  ```

- [ ] **Review overnight logs**
  ```bash
  tail -100 /home/trading/trading-monitor/logs/service.log
  ```

- [ ] **Verify scheduler times (US Eastern)**
  ```bash
  sudo journalctl -u trading-monitor | grep "Next run"
  # Verify: Order Executor at 9:45 AM ET
  #         Order Monitor every 5 min
  #         Position Monitor every 10 min
  ```

- [ ] **Check for trading signals**
  ```bash
  python3 << EOF
  from db_layer import TradingDB
  db = TradingDB()
  cursor = db.get_cursor()
  cursor.execute("SELECT symbol, signal_type, entry_price FROM analysis_decision WHERE signal_decision = 'EXECUTE' AND execution_status IS NULL")
  signals = cursor.fetchall()
  print(f"Pending signals: {len(signals)}")
  for s in signals: print(s)
  cursor.close()
  db.close()
  EOF
  ```

### Order Execution Validation (9:45 AM ET)

- [ ] **Order Executor ran at 9:45 AM ET**
  ```bash
  sudo journalctl -u trading-monitor | grep "Order Executor" | tail -5
  ```

- [ ] **Entry orders placed successfully**
  - Check Alpaca dashboard: https://app.alpaca.markets/paper/dashboard/orders
  - Verify orders match signals

- [ ] **Database records created**
  ```bash
  python3 << EOF
  from db_layer import TradingDB
  from datetime import date
  db = TradingDB()
  cursor = db.get_cursor()

  # Check trade_journal
  cursor.execute("SELECT COUNT(*) FROM trade_journal WHERE DATE(entry_time) = %s", (date.today(),))
  print(f"Trades created: {cursor.fetchone()[0]}")

  # Check order_execution
  cursor.execute("SELECT COUNT(*) FROM order_execution WHERE DATE(created_at) = %s", (date.today(),))
  print(f"Orders created: {cursor.fetchone()[0]}")

  # Check analysis_decision updated
  cursor.execute("SELECT COUNT(*) FROM analysis_decision WHERE execution_status = 'executed' AND DATE(executed_at) = %s", (date.today(),))
  print(f"Signals executed: {cursor.fetchone()[0]}")

  cursor.close()
  db.close()
  EOF
  ```

- [ ] **No errors in logs**
  ```bash
  sudo journalctl -u trading-monitor --since "09:40" | grep -i error
  # Should return no results
  ```

### Order Monitoring Validation (First Hour)

- [ ] **Order Monitor running every 5 minutes**
  ```bash
  sudo journalctl -u trading-monitor | grep "Order Monitor" | tail -10
  ```

- [ ] **Order status being synced**
  ```bash
  python3 << EOF
  from db_layer import TradingDB
  db = TradingDB()
  cursor = db.get_cursor()
  cursor.execute("SELECT order_id, status FROM order_execution ORDER BY updated_at DESC LIMIT 5")
  for row in cursor.fetchall(): print(row)
  cursor.close()
  db.close()
  EOF
  ```

- [ ] **Entry fills detected** (when orders fill)
  - Watch for "Entry order filled" in logs
  - Verify stop-loss orders placed immediately

- [ ] **Stop-loss orders placed for all filled entries**
  ```bash
  python3 << EOF
  from db_layer import TradingDB
  db = TradingDB()
  cursor = db.get_cursor()
  cursor.execute("SELECT symbol, sl_order_id FROM trade_journal WHERE current_status = 'open'")
  for row in cursor.fetchall():
      if row[1] is None:
          print(f"⚠️  {row[0]} missing SL order!")
      else:
          print(f"✅ {row[0]} has SL: {row[1]}")
  cursor.close()
  db.close()
  EOF
  ```

- [ ] **Take-profit orders placed for SWING trades**
  ```bash
  python3 << EOF
  from db_layer import TradingDB
  db = TradingDB()
  cursor = db.get_cursor()
  cursor.execute("SELECT symbol, trade_type, tp_order_id FROM trade_journal WHERE current_status = 'open' AND trade_type = 'SWING'")
  for row in cursor.fetchall():
      if row[2] is None:
          print(f"⚠️  {row[0]} SWING missing TP order!")
      else:
          print(f"✅ {row[0]} SWING has TP: {row[2]}")
  cursor.close()
  db.close()
  EOF
  ```

### Position Monitoring Validation

- [ ] **Position Monitor running every 10 minutes**
  ```bash
  sudo journalctl -u trading-monitor | grep "Position Monitor" | tail -10
  ```

- [ ] **Position values being updated**
  ```bash
  python3 << EOF
  from db_layer import TradingDB
  db = TradingDB()
  cursor = db.get_cursor()
  cursor.execute("SELECT symbol, current_price, unrealized_pnl FROM trade_journal WHERE current_status = 'open' ORDER BY entry_time DESC")
  print("Open positions:")
  for row in cursor.fetchall():
      print(f"{row[0]}: \${row[1]}, P&L: \${row[2]}")
  cursor.close()
  db.close()
  EOF
  ```

- [ ] **Unrealized P&L calculation verified**
  - Manually calculate: (current_price - entry_price) × quantity
  - Compare with database value
  - Should match exactly

- [ ] **Position_status table updated**
  ```bash
  python3 << EOF
  from db_layer import TradingDB
  db = TradingDB()
  cursor = db.get_cursor()
  cursor.execute("SELECT COUNT(*) FROM position_status WHERE DATE(updated_at) = CURRENT_DATE")
  print(f"Position updates today: {cursor.fetchone()[0]}")
  cursor.close()
  db.close()
  EOF
  ```

### End of Day Review

- [ ] **All trades tracked correctly**
  - Compare Alpaca positions with database
  - Should be 1-to-1 match

- [ ] **No errors during the day**
  ```bash
  sudo journalctl -u trading-monitor --since "09:00" | grep -i error
  ```

- [ ] **Performance summary**
  ```bash
  python3 << EOF
  from db_layer import TradingDB
  from datetime import date
  db = TradingDB()
  cursor = db.get_cursor()

  # Trades today
  cursor.execute("SELECT COUNT(*) FROM trade_journal WHERE DATE(entry_time) = %s", (date.today(),))
  print(f"Trades entered: {cursor.fetchone()[0]}")

  # Open positions
  cursor.execute("SELECT COUNT(*) FROM trade_journal WHERE current_status = 'open'")
  print(f"Still open: {cursor.fetchone()[0]}")

  # Unrealized P&L
  cursor.execute("SELECT SUM(unrealized_pnl) FROM trade_journal WHERE current_status = 'open'")
  pnl = cursor.fetchone()[0] or 0
  print(f"Unrealized P&L: \${pnl:.2f}")

  cursor.close()
  db.close()
  EOF
  ```

- [ ] **Day 1 summary documented**
  - Record in spreadsheet: date, trades entered, errors, notes

---

## Days 2-5: Scenario Validation

### Test Different Trade Types

- [ ] **LONG DAY trade** executed and tracked
  - Entry order placed
  - Stop loss placed
  - Position monitored
  - Exit via SL or TP

- [ ] **SHORT DAY trade** executed and tracked
  - Entry order placed
  - Stop loss placed (above entry for short)
  - Position monitored
  - Exit via SL or TP

- [ ] **LONG SWING trade** executed and tracked
  - Entry order placed
  - Stop loss placed
  - **Take profit placed**
  - Position monitored over multiple days

- [ ] **SHORT SWING trade** executed and tracked
  - Entry order placed
  - Stop loss placed (above entry)
  - **Take profit placed** (below entry)
  - Position monitored over multiple days

### Test Exit Scenarios

- [ ] **Stop-loss exit validated**
  - Trade exited via stop loss
  - Realized P&L calculated correctly
  - Trade status set to 'closed'
  - Exit reason = 'stop_loss'
  - Remaining orders cancelled

- [ ] **Take-profit exit validated**
  - SWING trade exited via take profit
  - Realized P&L calculated correctly
  - Trade status set to 'closed'
  - Exit reason = 'take_profit'
  - Remaining orders cancelled

- [ ] **Manual close validated** (if needed)
  - Manually close position in Alpaca
  - Order Monitor detects closure
  - Database updated to 'closed'
  - P&L calculated

### Test Multiple Positions

- [ ] **Multiple concurrent positions**
  - 2+ positions open simultaneously
  - All tracked correctly
  - All have SL orders
  - Position values update independently

- [ ] **Rapid succession trades**
  - Multiple signals on same day
  - All executed correctly
  - No race conditions
  - Database integrity maintained

---

## Days 6-10: Edge Cases & Error Handling

### Market Conditions

- [ ] **Volatile market day**
  - Rapid price movements
  - Position values update correctly
  - SL orders triggered appropriately

- [ ] **Low volume day**
  - Orders may take longer to fill
  - System handles pending orders correctly
  - No timeouts or errors

- [ ] **Market gap**
  - Overnight gap up/down
  - SL orders may fill at worse price
  - P&L calculated with actual fill price

- [ ] **Extended hours** (if enabled)
  - Pre-market and after-hours behavior
  - System handles correctly or ignores

### Error Scenarios

- [ ] **Alpaca API slowness**
  - Monitor response times
  - System handles delays gracefully
  - No crashes or failures

- [ ] **Order rejection**
  - Simulate rejected order (invalid symbol, etc.)
  - System logs error
  - Database marked as 'failed'
  - Alert sent (if configured)

- [ ] **Database connection issue**
  - Temporarily disconnect database
  - Service handles gracefully
  - Recovers when connection restored

- [ ] **Service restart during market hours**
  ```bash
  sudo systemctl restart trading-monitor
  ```
  - Service restarts cleanly
  - Picks up where left off
  - No duplicate orders placed
  - All positions still tracked

### Data Integrity

- [ ] **Database consistency check**
  ```bash
  python3 << EOF
  from db_layer import TradingDB
  db = TradingDB()
  cursor = db.get_cursor()

  # Check orphaned orders
  cursor.execute("""
      SELECT COUNT(*) FROM order_execution
      WHERE trade_id NOT IN (SELECT id FROM trade_journal)
  """)
  orphaned = cursor.fetchone()[0]
  print(f"Orphaned orders: {orphaned}")  # Should be 0

  # Check trades without entry orders
  cursor.execute("""
      SELECT COUNT(*) FROM trade_journal
      WHERE entry_order_id IS NULL
  """)
  missing_entry = cursor.fetchone()[0]
  print(f"Trades without entry: {missing_entry}")  # Should be 0

  # Check open trades without SL
  cursor.execute("""
      SELECT COUNT(*) FROM trade_journal
      WHERE current_status = 'open' AND sl_order_id IS NULL
  """)
  missing_sl = cursor.fetchone()[0]
  print(f"Open trades without SL: {missing_sl}")  # Should be 0

  cursor.close()
  db.close()
  EOF
  ```

- [ ] **Alpaca vs Database reconciliation**
  ```bash
  python3 << EOF
  from alpaca_client import get_trading_client
  from db_layer import TradingDB

  client = get_trading_client()
  db = TradingDB()
  cursor = db.get_cursor()

  # Get Alpaca positions
  alpaca_positions = {p.symbol: float(p.qty) for p in client.get_all_positions()}

  # Get database positions
  cursor.execute("SELECT symbol, quantity FROM trade_journal WHERE current_status = 'open'")
  db_positions = {row[0]: row[1] for row in cursor.fetchall()}

  # Compare
  print("Alpaca positions:", alpaca_positions)
  print("Database positions:", db_positions)

  if alpaca_positions == db_positions:
      print("✅ Positions match!")
  else:
      print("⚠️  Mismatch detected!")

  cursor.close()
  db.close()
  EOF
  ```

---

## Daily Validation Checklist

Use this checklist **every trading day** during paper trading:

### Morning (Before 9:30 AM ET)

- [ ] Service running
- [ ] No errors in overnight logs
- [ ] Database connection OK
- [ ] Alpaca connection OK
- [ ] Check pending signals

### Mid-Morning (10:00 AM ET)

- [ ] Order Executor ran at 9:45 AM
- [ ] Entry orders placed
- [ ] Order Monitor running every 5 min
- [ ] No errors since market open

### Mid-Day (12:00 PM ET)

- [ ] Filled orders detected
- [ ] SL orders placed
- [ ] TP orders placed (SWING)
- [ ] Position Monitor running every 10 min
- [ ] Position values updating

### End of Day (4:30 PM ET)

- [ ] Review all trades
- [ ] Check for any exits
- [ ] Verify P&L calculations
- [ ] No errors during trading hours
- [ ] Document day's activity

---

## Performance Metrics to Track

### Daily Metrics

| Date | Signals | Executed | Filled | Open | Closed | P&L | Errors | Notes |
|------|---------|----------|--------|------|--------|-----|--------|-------|
| 10/26 | 3 | 3 | 3 | 3 | 0 | $0.00 | 0 | First day |
| 10/27 | 2 | 2 | 2 | 4 | 1 | +$15.50 | 0 | 1 SL hit |
| ... | | | | | | | | |

### Cumulative Metrics

Track over the validation period:

- **Total trades:** ___
- **Win rate:** ___% (profitable trades / total trades)
- **Average P&L per trade:** $___
- **Largest win:** $___
- **Largest loss:** $___
- **Total P&L:** $___
- **Error count:** ___
- **Uptime:** ___%

### Trade Type Distribution

- **LONG DAY:** ___ trades
- **SHORT DAY:** ___ trades
- **LONG SWING:** ___ trades
- **SHORT SWING:** ___ trades

### Exit Reason Distribution

- **Stop Loss:** ___ trades
- **Take Profit:** ___ trades
- **Manual Close:** ___ trades
- **Other:** ___ trades

---

## Final Validation (End of Paper Trading)

### System Reliability

- [ ] **99%+ uptime** during validation period
- [ ] **Zero critical errors** (service crashes, data loss)
- [ ] **All scheduled jobs ran as expected**
- [ ] **Logs clean** (no repeated warnings)

### Trading Accuracy

- [ ] **100% of valid signals executed**
- [ ] **100% of filled entries have SL orders**
- [ ] **100% of SWING trades have TP orders**
- [ ] **All exits detected and processed**
- [ ] **All P&L calculations verified**

### Data Integrity

- [ ] **Alpaca and database positions match**
- [ ] **No orphaned records in database**
- [ ] **No missing required fields**
- [ ] **All foreign keys valid**
- [ ] **Database backup working**

### Scenario Coverage

- [ ] **At least 1 LONG DAY trade completed**
- [ ] **At least 1 SHORT DAY trade completed**
- [ ] **At least 1 SWING trade completed**
- [ ] **At least 1 stop-loss exit**
- [ ] **At least 1 take-profit exit**
- [ ] **Multiple concurrent positions tested**
- [ ] **Service restart tested**
- [ ] **Error scenario handled**

### Documentation

- [ ] **Daily logs reviewed and archived**
- [ ] **Performance metrics documented**
- [ ] **Issues/bugs documented and fixed**
- [ ] **Validation summary written**

### Sign-Off

**Paper trading validation completed by:** ___________________

**Date:** ___________________

**Duration:** ___ trading days

**Total trades:** ___

**Win rate:** ___%

**Total P&L:** $___

**Critical issues found:** ___

**All issues resolved:** [ ] Yes [ ] No

**Ready for live trading:** [ ] Yes [ ] No

**Notes:**
```
_______________________________________________________________
_______________________________________________________________
_______________________________________________________________
```

---

## Go/No-Go Decision

### GO Criteria (All must be checked)

- [ ] Paper trading validation completed (10+ trading days)
- [ ] All checklist items completed
- [ ] Zero critical errors
- [ ] All trade types tested successfully
- [ ] P&L calculations verified accurate
- [ ] Database integrity confirmed
- [ ] System uptime >99%
- [ ] Team confident in system reliability

### NO-GO Criteria (Any one fails)

- [ ] Critical errors occurred
- [ ] Data integrity issues found
- [ ] P&L calculation errors
- [ ] Missing SL orders on live trades
- [ ] System crashes or failures
- [ ] Less than 10 trading days
- [ ] Any unresolved issues

---

## Next Steps After Validation

### If GO

1. **Switch to live trading**
   - Update .env with live API credentials
   - Change ALPACA_BASE_URL to https://api.alpaca.markets
   - Change TRADE_MODE to 'live'

2. **Start conservatively**
   - Use small position sizes initially
   - Monitor closely for first week
   - Gradually increase to full size

3. **Enhanced monitoring**
   - Daily reviews mandatory
   - Set up real-time alerts
   - Keep backup systems ready

### If NO-GO

1. **Document all issues**
2. **Fix critical bugs**
3. **Re-test affected scenarios**
4. **Restart paper trading validation**
5. **Do NOT proceed to live trading**

---

## Important Reminders

⚠️ **NEVER skip paper trading validation**
⚠️ **DO NOT rush the validation period**
⚠️ **Test ALL trade scenarios before going live**
⚠️ **Verify P&L calculations manually**
⚠️ **Document EVERYTHING during validation**

💰 **Your real money depends on this validation being thorough**

---

**Last Updated:** 2025-10-26 by Claude Code
