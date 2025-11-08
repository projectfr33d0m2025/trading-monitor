# Trading System Architecture: Component Explainer

## Overview

This document explains the architecture and necessity of three core components that manage the complete lifecycle of trades in our automated trading system:

1. **order_executor.py** - The Decision Executor
2. **order_monitor.py** - The Lifecycle Manager
3. **position_monitor.py** - The Position Valuator

These components follow a **Staged Event-Driven Architecture (SEDA)** pattern, where each stage operates independently at its optimal frequency while communicating through database state changes.

---

## Component 1: order_executor.py - The Decision Executor

### Primary Responsibility
**Translate approved trading decisions into live market orders**

### Schedule
- **Once daily at 9:45 AM ET** (15 minutes after market open)
- Allows market to stabilize before executing orders

### What It Creates
- `trade_journal` records (tracks the complete trade lifecycle)
- `order_execution` records (tracks individual order details)
- Live orders via Alpaca Trading API

### Database Interactions
**Reads:**
- `analysis_decision` (WHERE `executed = false` AND `Approve = true`)

**Writes:**
- `trade_journal` (creates new trade records with status='ORDERED')
- `order_execution` (creates order records with status='pending')
- `analysis_decision` (updates `executed = true`)

### Key Workflows

#### 1. NEW_TRADE Flow
```
Input: Approved, unexecuted decision
↓
Submit limit order → Alpaca API
↓
Create trade_journal entry (status='ORDERED')
↓
Create order_execution entry (order_type='ENTRY', status='pending')
↓
Mark analysis_decision as executed
```

#### 2. CANCEL Flow
```
Input: Approved CANCEL decision
↓
Cancel order via Alpaca API
↓
Update order_execution.order_status = 'cancelled'
↓
Update trade_journal.status = 'CANCELLED'
↓
Mark analysis_decision as executed
```

#### 3. AMEND Flow
```
Execute CANCEL flow (existing order)
↓
Execute NEW_TRADE flow (with updated parameters)
```

### Why It's Necessary

1. **Timing Control** - Only executes once per day after market stabilizes, avoiding pre-market volatility
2. **Clean Separation** - Decision-making (AI/human) is separate from execution
3. **Audit Trail** - Every order links back to the original analysis decision via `decision_id`
4. **Idempotency** - Won't re-execute already-executed decisions (checks `executed` flag)
5. **Error Resilience** - Handles order placement failures gracefully without crashing

### Problems It Solves

- **Duplicate Order Prevention** - `executed` flag prevents re-submitting same decision
- **Decision Accountability** - Links every order to originating analysis
- **Timing Precision** - Executes at optimal time (not too early, not missed)
- **Foundation Layer** - Creates the records that downstream monitors depend on

---

## Component 2: order_monitor.py - The Lifecycle Manager

### Primary Responsibility
**Monitor order status changes and manage the transition from orders to positions with risk controls**

### Schedule
- **Every 5 minutes** during trading hours (9:30 AM - 4:00 PM ET)
- **Once at 6:00 PM ET** (post-market check)

### What It Creates
- `position_tracking` records (when entry orders fill)
- Stop-loss orders (always placed after entry fills)
- Take-profit orders (placed for SWING trades only)
- `order_execution` records for SL/TP orders

### Database Interactions
**Reads:**
- `order_execution` (WHERE `order_status` IN ['pending', 'partially_filled', 'new', 'accepted'])
- `trade_journal` (to get trade parameters like stop_loss, take_profit)

**Writes:**
- `order_execution` (updates status, filled quantities, prices, timestamps)
- `trade_journal` (updates status, entry/exit prices, P&L)
- `position_tracking` (creates positions, deletes when closed)

### Key Workflows

#### 1. Sync Order Status
```
For each active order:
  ↓
  Fetch current status from Alpaca API (get_order_by_id)
  ↓
  Update order_execution with:
    - order_status (new/accepted/filled/cancelled)
    - filled_avg_price
    - filled_qty
    - filled_at timestamp
```

#### 2. Entry Order Filled → Position Creation
```
Trigger: order_type='ENTRY' AND status='filled'
  ↓
Update trade_journal.status = 'POSITION'
  ↓
Create position_tracking record:
  - avg_entry_price (from filled_avg_price)
  - qty (from filled_qty)
  - cost_basis = price × qty
  - unrealized_pnl = 0 (initially)
  ↓
Place STOP_LOSS order (always)
  ↓
Place TAKE_PROFIT order (only if trade_style='SWING')
  ↓
Store SL/TP order IDs in position_tracking
```

#### 3. Exit Order Filled → Trade Closure
```
Trigger: order_type IN ['STOP_LOSS', 'TAKE_PROFIT'] AND status='filled'
  ↓
Calculate realized P&L:
  actual_pnl = (exit_price - entry_price) × qty
  ↓
Update trade_journal:
  - status = 'CLOSED'
  - exit_price
  - actual_pnl
  - exit_reason ('STOPPED_OUT' or 'PROFIT_TAKEN')
  ↓
Delete position_tracking record (position no longer exists)
  ↓
Cancel remaining orders:
  - If SL filled → cancel TP
  - If TP filled → cancel SL
```

### State Transitions Managed
```
ORDERED ──(entry fills)──→ POSITION ──(exit fills)──→ CLOSED
   │
   └──(order cancelled)──→ CANCELLED
```

### Why It's Necessary

1. **Real-Time Awareness** - Orders can fill anytime during market hours; 5-minute frequency catches fills quickly
2. **Automatic Risk Management** - Places protective SL/TP orders immediately after entry fills (critical for risk control)
3. **Lifecycle Completion** - Closes trades when exits execute, calculates final realized P&L
4. **Order Cleanup** - Cancels orphaned orders (prevents accidental double-sells)
5. **Frequent Polling Required** - Can't rely on webhooks alone (unreliable in production)

### Problems It Solves

- **Unprotected Positions** - Without SL/TP placement, positions would have no automatic risk controls
- **Stale Order Status** - Database shows 'pending' but order already filled → Creates discrepancy
- **Orphaned Exit Orders** - If SL fills but TP remains active → Could sell non-existent position
- **Partial Fills** - Handles cases where only part of order executes
- **Entry/Exit Price Reconciliation** - Captures actual filled prices vs. planned prices

### Edge Cases Handled

- **Partial Fills** - Tracks `filled_qty` separately from requested quantity
- **Broker Rejections** - Logs errors, continues processing other orders
- **API Errors** - Graceful handling when order not found in Alpaca
- **Simultaneous Fills** - `cancel_remaining_orders()` prevents SL and TP both executing

---

## Component 3: position_monitor.py - The Position Valuator

### Primary Responsibility
**Update real-time position values and detect positions closed outside the system**

### Schedule
- **Every 10 minutes** during trading hours (9:30 AM - 4:00 PM ET)
- **Once at 6:15 PM ET** (post-market reconciliation)

### What It Updates
- Existing `position_tracking` records (current prices, market values, unrealized P&L)
- `trade_journal` records (when reconciling external closures)

### Database Interactions
**Reads:**
- `position_tracking` (all active positions, no status filter)
- `order_execution` (when reconciling closures)
- `trade_journal` (to update closed trades)

**Writes:**
- `position_tracking` (updates `current_price`, `market_value`, `unrealized_pnl`, `last_updated`)
- `trade_journal` (closes trades if detected as externally closed)

### Key Workflows

#### 1. Update Position Values
```
For each position in position_tracking:
  ↓
  Fetch latest quote from Alpaca Data API (get_stock_latest_quote)
  ↓
  Calculate current_price = (bid + ask) / 2
  ↓
  Calculate market_value = current_price × qty
  ↓
  Calculate unrealized_pnl = (current_price - avg_entry_price) × qty
  ↓
  Update position_tracking with new values + timestamp
```

#### 2. Check for Closed Positions (Reconciliation)
```
Fetch all current positions from Alpaca API
  ↓
Compare with positions in database
  ↓
If position exists in DB but NOT in Alpaca:
  → Position was closed externally
  → Trigger reconciliation
```

#### 3. Reconcile Externally Closed Position
```
Position missing from Alpaca:
  ↓
Search for filled SL/TP order in database
  ↓
If found:
  - Use filled order data for exit_price
  - Set exit_reason based on order type
Else:
  - Use last known price from position_tracking
  - Set exit_reason = 'MANUAL_EXIT'
  ↓
Update trade_journal:
  - status = 'CLOSED'
  - exit_price
  - actual_pnl
  ↓
Delete position_tracking record
  ↓
Cancel any remaining pending orders
```

### Why It's Necessary

1. **Real-Time Portfolio Visibility** - Traders need current P&L, not stale entry values
2. **External Action Detection** - Users might close positions via Alpaca mobile app or web dashboard
3. **Data Integrity Safety Net** - Keeps database synchronized with actual broker state
4. **Slower Cadence Acceptable** - 10-minute frequency sufficient for valuation (vs 5-min for orders)
5. **Independent Data Source** - Uses Market Data API (different from Orders API used by order_monitor)

### Problems It Solves

- **Manual Closures** - Position closed via Alpaca dashboard → System detects and reconciles
- **Missed Events** - If order_monitor misses a fill event → Reconciliation catches it during next position check
- **Stale Valuations** - Without this, position values would freeze at entry price
- **Ghost Positions** - Database shows position but broker account doesn't → Gets cleaned up
- **Decision Input Data** - Current P&L needed for next analysis cycle decisions

### Edge Cases Handled

- **Alpaca API Unavailable** - Logs warning, skips update, continues to next position
- **No Quote Data** - If symbol has no valid quote, skips that position
- **Position Closed But No Order Record** - Assumes 'MANUAL_EXIT', uses last known price
- **Partial Quote Data** - Uses ask price if bid unavailable (or vice versa)

---

## How They Work Together

### Sequential Dependency Chain

```
┌─────────────────┐       ┌──────────────────┐       ┌───────────────────┐
│ order_executor  │──────▶│ order_monitor    │──────▶│ position_monitor  │
│                 │       │                  │       │                   │
│ 9:45 AM daily   │       │ Every 5 minutes  │       │ Every 10 minutes  │
└─────────────────┘       └──────────────────┘       └───────────────────┘
        │                          │                          │
        │                          │                          │
        ▼                          ▼                          ▼
  Places orders            Manages lifecycle           Updates values
  Creates records          Places SL/TP               Reconciles state
  Links to decisions       Handles fills              Detects external changes
```

### Data Flow

```
analysis_decision (approved, unexecuted)
         │
         │ (order_executor reads)
         ▼
trade_journal (ORDERED) + order_execution (ENTRY, pending)
         │
         │ (order_monitor polls Alpaca)
         ▼
order_execution (ENTRY, filled)
         │
         │ (order_monitor creates)
         ▼
position_tracking + order_execution (STOP_LOSS, TAKE_PROFIT, pending)
         │
         │ (position_monitor updates)
         ▼
position_tracking (current_price, unrealized_pnl updated every 10 min)
         │
         │ (order_monitor detects SL/TP fill)
         ▼
trade_journal (CLOSED) + position_tracking (deleted)
```

### Complete Lifecycle Example: SWING Trade

#### Day 1, 9:45 AM - order_executor.py runs

**Input:** `analysis_decision` record
```
{
  symbol: 'AAPL',
  action: 'NEW_TRADE',
  planned_entry: 150.00,
  planned_sl: 145.00,
  planned_tp: 160.00,
  trade_style: 'SWING',
  Approve: true,
  executed: false
}
```

**Creates:**
```sql
-- trade_journal
{
  decision_id: 123,
  symbol: 'AAPL',
  status: 'ORDERED',
  planned_entry: 150.00,
  planned_sl: 145.00,
  planned_tp: 160.00
}

-- order_execution
{
  trade_id: 456,
  order_type: 'ENTRY',
  order_status: 'pending',
  limit_price: 150.00,
  alpaca_order_id: 'abc-123'
}
```

---

#### Day 1, 10:05 AM - order_monitor.py runs (entry fills)

**Detects:** Order 'abc-123' status changed to 'filled'

**Updates:**
```sql
-- order_execution
{
  order_status: 'filled',
  filled_avg_price: 150.25,  -- Actual fill price
  filled_qty: 10,
  filled_at: '2024-01-15 10:03:22'
}

-- trade_journal
{
  status: 'POSITION',
  actual_entry: 150.25,
  actual_qty: 10
}
```

**Creates:**
```sql
-- position_tracking
{
  trade_id: 456,
  symbol: 'AAPL',
  qty: 10,
  avg_entry_price: 150.25,
  cost_basis: 1502.50,
  current_price: 150.25,
  market_value: 1502.50,
  unrealized_pnl: 0.00
}

-- order_execution (stop-loss)
{
  trade_id: 456,
  order_type: 'STOP_LOSS',
  order_status: 'pending',
  stop_price: 145.00,
  alpaca_order_id: 'sl-456'
}

-- order_execution (take-profit)
{
  trade_id: 456,
  order_type: 'TAKE_PROFIT',
  order_status: 'pending',
  limit_price: 160.00,
  alpaca_order_id: 'tp-789'
}
```

---

#### Day 1, 10:15 AM - position_monitor.py runs

**Fetches:** Latest AAPL quote from Alpaca → $151.00

**Updates:**
```sql
-- position_tracking
{
  current_price: 151.00,
  market_value: 1510.00,    -- 151.00 × 10
  unrealized_pnl: +7.50,     -- (151.00 - 150.25) × 10
  last_updated: '2024-01-15 10:15:00'
}
```

---

#### Day 1, 2:30 PM - position_monitor.py runs

**Fetches:** Latest AAPL quote → $148.75

**Updates:**
```sql
-- position_tracking
{
  current_price: 148.75,
  market_value: 1487.50,
  unrealized_pnl: -15.00,    -- (148.75 - 150.25) × 10 = -$15.00
  last_updated: '2024-01-15 14:30:00'
}
```

---

#### Day 2, 2:45 PM - order_monitor.py runs (stop-loss fills)

**Detects:** SL order 'sl-456' status changed to 'filled'

**Updates:**
```sql
-- order_execution (stop-loss)
{
  order_status: 'filled',
  filled_avg_price: 144.90,  -- Slippage from 145.00
  filled_at: '2024-01-16 14:43:11'
}

-- trade_journal
{
  status: 'CLOSED',
  exit_price: 144.90,
  actual_pnl: -53.50,        -- (144.90 - 150.25) × 10
  exit_reason: 'STOPPED_OUT',
  exit_time: '2024-01-16 14:43:11'
}

-- order_execution (take-profit)
{
  order_status: 'cancelled'  -- Remaining order cancelled
}
```

**Deletes:**
```sql
-- position_tracking record removed (position no longer exists)
```

---

## Why All Three Are Necessary

### Different Responsibilities

| Component | Focus | Frequency | Alpaca API Used | Creates |
|-----------|-------|-----------|-----------------|---------|
| **order_executor** | Order Placement | Once/day (9:45 AM) | `TradingClient.submit_order()` | Orders, Journal entries |
| **order_monitor** | Lifecycle Transitions | Every 5 min | `TradingClient.get_order_by_id()` | Positions, SL/TP orders |
| **position_monitor** | Position Valuation | Every 10 min | `DataClient.get_stock_latest_quote()` | Nothing (updates only) |

### Complementary Design Principles

#### 1. Why order_executor doesn't monitor orders
- **Different Time Scales** - Execution is daily; monitoring is continuous
- **Separation of Concerns** - Placement vs. management are distinct operations
- **Resource Efficiency** - Daily runner doesn't need to stay active for monitoring

#### 2. Why order_monitor doesn't place entry orders
- **Idempotency Risk** - Running every 5 min would create duplicate orders without careful guards
- **Timing Control** - Entry orders should execute at specific times (9:45 AM), not continuously
- **Single Responsibility** - Monitor focuses on state changes, not initial creation

#### 3. Why position_monitor doesn't manage orders
- **Different Data Sources** - Uses Market Data API (quotes) not Trading API (orders)
- **Different Cadence** - Position values change slowly (10 min OK); orders need faster checks (5 min)
- **Distinct Concern** - Valuation ≠ Order management

### Architecture Pattern: Staged Event-Driven Architecture (SEDA)

This system follows **SEDA** principles:

1. **Staged Processing** - Each component is an independent stage in the pipeline
2. **Event-Driven** - State changes in database trigger next stage (implicit events)
3. **Asynchronous** - No direct calls between components (communicate via DB)
4. **Failure Isolation** - If position_monitor fails, order_monitor still works
5. **Independent Scaling** - Can adjust frequency of each component independently

**Benefits:**
- Each component runs at its optimal frequency
- Failures don't cascade
- Easy to test in isolation
- Can add new stages without modifying existing ones
- Database acts as persistent queue between stages

---

## Key Design Decisions

### 1. Communication via Database (Not Direct Calls)
**Why:** Allows asynchronous, decoupled operation
**Trade-off:** Slight latency vs. resilience and simplicity

### 2. No Foreign Key Constraints
**Why:** NocoDB doesn't support them
**Solution:** Application-level relationship management via IDs (`trade_id`, `decision_id`)

### 3. Frequent Order Monitoring (5 min) vs. Slower Position Monitoring (10 min)
**Why:** Order fills require immediate action (place SL/TP); position updates are informational
**Trade-off:** API rate limits vs. responsiveness

### 4. Reconciliation in position_monitor
**Why:** Positions can be closed outside the system (mobile app, manual trades)
**Benefit:** Data integrity safety net

### 5. Status Fields in Multiple Tables
- `trade_journal.status` - Trade lifecycle (ORDERED/POSITION/CLOSED/CANCELLED)
- `order_execution.order_status` - Order state (pending/filled/cancelled)
- `position_tracking` - No status (existence = open position)

**Why:** Different entities, different lifecycles, different queries

### 6. Separate Tables for Different Purposes
- **trade_journal** - Permanent trade history (NEVER deleted)
- **position_tracking** - Active positions only (DELETED when closed)
- **order_execution** - All orders ever placed (permanent, for audit)

**Why:** Optimizes for different query patterns (history vs. current state)

---

## Quick Reference

### When Each Component Runs

| Time | Component | What Happens |
|------|-----------|--------------|
| 9:45 AM | order_executor | Places today's approved orders |
| 9:30 AM - 4:00 PM (every 5 min) | order_monitor | Checks for order fills, places SL/TP, closes trades |
| 9:30 AM - 4:00 PM (every 10 min) | position_monitor | Updates position values, reconciles externals |
| 6:00 PM | order_monitor | Post-market check for late fills |
| 6:15 PM | position_monitor | Post-market reconciliation |

### State Flow Summary

```
analysis_decision (approved)
         ↓
    [EXECUTOR]
         ↓
trade_journal: ORDERED + order_execution: pending
         ↓
    [MONITOR] ← (polls Alpaca every 5 min)
         ↓
order_execution: filled → position_tracking created + SL/TP placed
         ↓
    [MONITOR] ← (updates prices every 10 min)
         ↓
position_tracking: unrealized_pnl updated continuously
         ↓
    [MONITOR] ← (SL or TP fills)
         ↓
trade_journal: CLOSED + position_tracking deleted
```

### Critical Insights

1. **order_executor** creates the foundation (orders and journal entries)
2. **order_monitor** manages risk (places SL/TP immediately after entry fills)
3. **position_monitor** provides visibility (real-time P&L) and safety (reconciliation)

Without any one of these components:
- **No executor** → No orders placed, system doesn't act on decisions
- **No order_monitor** → No SL/TP protection, no trade closure detection
- **No position_monitor** → Stale P&L data, ghost positions possible

---

## Troubleshooting

### "Position exists in DB but not in broker"
**Solution:** position_monitor reconciliation will detect and close it

### "Order filled but position not created"
**Check:** order_monitor logs - likely order status sync issue

### "SL and TP both executed"
**Prevention:** order_monitor's `cancel_remaining_orders()` should prevent this
**Check:** Order execution timing in logs

### "Position P&L not updating"
**Check:**
1. position_monitor running?
2. Market data API accessible?
3. Symbol has valid quote data?

### "Order placed twice for same decision"
**Root Cause:** `executed` flag not set properly in order_executor
**Check:** Database transaction completion

---

**Document Version:** 1.0
**Last Updated:** 2025-11-08
**System:** trading-monitor
**Components Covered:** order_executor.py, order_monitor.py, position_monitor.py
