# n8n Workflow 1 Modification Guide

## Overview

This guide provides step-by-step instructions to modify your existing n8n Workflow 1 (Analysis & Decision) to integrate with the Python trading system.

## What You Need to Do

Add a new node **after the "Save Analysis" node** that updates the newly added fields in the `analysis_decision` table.

## Prerequisites

Before modifying the workflow, ensure you have:
1. ✅ Added 4 new fields to `analysis_decision` table in NocoDB (see `docs/database-setup.md`)
2. ✅ Verified the fields exist in NocoDB UI
3. ✅ Noted the "Current Position" node output structure in your workflow

---

## Step-by-Step Instructions

### Step 1: Locate the "Save Analysis" Node

1. Open your n8n workflow editor
2. Find the node named "Save Analysis" (or similar) that creates/updates the `analysis_decision` record
3. This is the node that saves the AI analysis and decision to NocoDB

### Step 2: Add "Update Analysis Decision" Node

After the "Save Analysis" node, add a new node:

**Node Type:** PostgreSQL (or NocoDB Update)

**Node Name:** Update Analysis Decision

**Configuration:**

```yaml
Operation: UPDATE
Table: analysis_decision
Where Clause: "Analysis Id" = {{ $node["Save Analysis"].json["Analysis Id"] }}
```

### Step 3: Configure Field Mappings

Set the following fields in the update node:

| Field | Expression | Description |
|-------|-----------|-------------|
| `existing_order_id` | `{{ $node["Current Position"].json["pending_order_id"] || null }}` | Alpaca order ID if pending order exists |
| `existing_trade_journal_id` | `{{ $node["Current Position"].json["trade_journal_id"] || null }}` | Trade journal ID if position exists |
| `executed` | `false` | Always set to false initially |
| `execution_time` | `null` | Always set to null initially |

### Step 4: Handle "Current Position" Node Output

The "Current Position" node should check if there's an existing order or position for this symbol.

**Expected "Current Position" Node Output:**

```json
{
  "symbol": "AAPL",
  "pending_order_id": "abc-123-def",  // Alpaca order ID if exists, otherwise null
  "trade_journal_id": 42,              // Trade journal ID if exists, otherwise null
  "has_position": true                 // Boolean flag
}
```

If your "Current Position" node has different field names, adjust the expressions accordingly.

### Step 5: Add Special Logic for NO_ACTION

Add a **conditional branch** after "Update Analysis Decision":

**IF Node Configuration:**

```yaml
Condition: {{ $node["Save Analysis"].json["Decision"]["primary_action"] === "NO_ACTION" && $node["Update Analysis Decision"].json["existing_trade_journal_id"] !== null }}
```

**If TRUE branch** - Add "Update Trade Days" node:

**Node Type:** PostgreSQL

**Operation:** UPDATE

**Configuration:**

```sql
UPDATE trade_journal
SET
  days_open = days_open + 1,
  last_review_date = CURRENT_DATE,
  updated_at = NOW()
WHERE id = {{ $node["Update Analysis Decision"].json["existing_trade_journal_id"] }}
```

**If FALSE branch** - No action needed

---

## Workflow Structure

```
┌─────────────────────┐
│  AI Analysis        │
└──────────┬──────────┘
           │
           ▼
┌─────────────────────┐
│  Save Analysis      │  ← Creates/updates analysis_decision
└──────────┬──────────┘
           │
           ▼
┌─────────────────────┐
│  Current Position   │  ← Checks for existing orders/positions
└──────────┬──────────┘
           │
           ▼
┌─────────────────────┐
│  Update Analysis    │  ← NEW NODE - Updates 4 new fields
│  Decision           │
└──────────┬──────────┘
           │
           ▼
┌─────────────────────┐
│  IF: NO_ACTION      │  ← NEW BRANCH - Check if NO_ACTION
│  with Position?     │
└──────────┬──────────┘
           │
     ┌─────┴─────┐
     ▼           ▼
   TRUE        FALSE
     │           │
     ▼           └──> End
┌─────────────┐
│ Update Trade│
│ Days Open   │
└─────────────┘
```

---

## Field Expressions Reference

### PostgreSQL Node

If using PostgreSQL node directly:

```sql
UPDATE analysis_decision
SET
  existing_order_id = COALESCE(:pending_order_id, NULL),
  existing_trade_journal_id = COALESCE(:trade_journal_id, NULL),
  executed = false,
  execution_time = NULL
WHERE "Analysis Id" = :analysis_id
```

**Parameters:**
- `:pending_order_id` → `{{ $node["Current Position"].json["pending_order_id"] }}`
- `:trade_journal_id` → `{{ $node["Current Position"].json["trade_journal_id"] }}`
- `:analysis_id` → `{{ $node["Save Analysis"].json["Analysis Id"] }}`

### NocoDB Node

If using NocoDB Update node:

```javascript
{
  "existing_order_id": {{ $node["Current Position"].json["pending_order_id"] || null }},
  "existing_trade_journal_id": {{ $node["Current Position"].json["trade_journal_id"] || null }},
  "executed": false,
  "execution_time": null
}
```

---

## How "Current Position" Node Should Work

The "Current Position" node needs to query the database to check:

1. **For pending orders**: Check `order_execution` table
2. **For open positions**: Check `position_tracking` table

**Example PostgreSQL Query:**

```sql
SELECT
  oe.alpaca_order_id as pending_order_id,
  pt.trade_journal_id
FROM analysis_decision ad
LEFT JOIN order_execution oe
  ON oe.analysis_decision_id = ad."Analysis Id"
  AND oe.order_status IN ('pending', 'new', 'accepted')
  AND oe.order_type = 'ENTRY'
LEFT JOIN position_tracking pt
  ON pt.symbol = ad."Ticker"
WHERE ad."Analysis Id" = :analysis_id
LIMIT 1
```

Or if you only have the symbol:

```sql
SELECT
  oe.alpaca_order_id as pending_order_id,
  pt.trade_journal_id
FROM order_execution oe
FULL OUTER JOIN position_tracking pt
  ON oe.trade_journal_id = pt.trade_journal_id
WHERE
  (oe.order_status IN ('pending', 'new', 'accepted') AND oe.order_type = 'ENTRY')
  OR pt.symbol = :symbol
LIMIT 1
```

---

## Verification Steps

After modifying the workflow:

### 1. Test with NEW_TRADE Decision

Run the workflow and verify:

```sql
SELECT
  "Analysis Id",
  "Ticker",
  "Decision"->>'primary_action' as action,
  existing_order_id,
  existing_trade_journal_id,
  executed,
  execution_time
FROM analysis_decision
ORDER BY "Date time" DESC
LIMIT 1;
```

Expected results:
- `existing_order_id`: NULL (no existing order)
- `existing_trade_journal_id`: NULL (no existing position)
- `executed`: false
- `execution_time`: NULL

### 2. Test with NO_ACTION on Existing Position

Create a decision with `primary_action = "NO_ACTION"` for a symbol that has an open position.

Verify:

```sql
SELECT
  id,
  symbol,
  days_open,
  last_review_date
FROM trade_journal
WHERE symbol = 'YOUR_SYMBOL'
AND status = 'POSITION';
```

Expected results:
- `days_open`: Should increment by 1
- `last_review_date`: Should be updated to today

### 3. Test Workflow End-to-End

1. Create a new analysis for a symbol
2. Check that `analysis_decision` record is created
3. Verify the 4 new fields are populated
4. Run the Python `order_executor.py` at 9:45 AM (or manually)
5. Verify order is placed in Alpaca
6. Verify `executed` is set to `true`
7. Verify `execution_time` is set to current timestamp

---

## Troubleshooting

### Issue: Fields not updating

**Check:**
1. Field names match exactly (case-sensitive)
2. "Current Position" node is executing before "Update Analysis Decision"
3. Node execution order is correct

**Fix:** Verify node connections and field names

### Issue: NULL values not working

**Check:**
1. Using `null` not `"null"` (string)
2. Using `||` operator for default values

**Fix:** Use proper JavaScript null: `{{ value || null }}`

### Issue: NO_ACTION not incrementing days_open

**Check:**
1. `existing_trade_journal_id` is not NULL
2. Conditional branch logic is correct
3. Trade exists in `trade_journal` table

**Fix:** Verify conditional expression and database state

### Issue: PostgreSQL syntax errors

**Check:**
1. Field names with spaces are quoted: `"Analysis Id"`
2. JSON operators use proper syntax: `->>`
3. Parameters use correct placeholder syntax

**Fix:** Review SQL syntax for your database version

---

## Advanced: Alternative Implementations

### Option 1: Combine with Save Analysis Node

Instead of a separate node, you can add the 4 fields directly in the "Save Analysis" node:

```javascript
{
  // ... existing fields ...
  "existing_order_id": {{ $node["Current Position"].json["pending_order_id"] || null }},
  "existing_trade_journal_id": {{ $node["Current Position"].json["trade_journal_id"] || null }},
  "executed": false,
  "execution_time": null
}
```

### Option 2: Use Function Node

Add a Function node to process the data:

```javascript
const currentPos = $node["Current Position"].json;
const analysis = $node["Save Analysis"].json;

return {
  analysis_id: analysis["Analysis Id"],
  existing_order_id: currentPos.pending_order_id || null,
  existing_trade_journal_id: currentPos.trade_journal_id || null,
  executed: false,
  execution_time: null
};
```

Then use this output in your update node.

---

## Summary

After completing this modification:

✅ n8n Workflow 1 will populate the 4 new fields in `analysis_decision`

✅ Python `order_executor.py` can read these fields to know if there's an existing order/position

✅ NO_ACTION decisions will properly increment `days_open` for existing positions

✅ The system is ready for automated order execution

**Next Steps:**
1. Complete the modification
2. Test thoroughly with various scenarios
3. Deploy Python programs with scheduler
4. Start paper trading validation

---

## Need Help?

- Check `trading-monitor-prd.md` for schema details
- Review `docs/database-setup.md` for field definitions
- Test with small data set first
- Monitor logs for any errors

Good luck! 🚀
