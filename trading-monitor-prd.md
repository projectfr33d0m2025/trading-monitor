# Trading System Monitoring - Product Requirements Document

## 1. Overview

### 1.1 Purpose
Develop a Python-based trading system monitoring solution that tracks the complete trading lifecycle: Analysis → Decision → Trade Plan → Order → Position. This system replaces n8n workflows with scheduled Python programs that interact with NocoDB tables for data persistence.

### 1.2 Scope
- **In Scope**: Workflows 1-4 (Analysis, Order Execution, Order Monitoring, Position Monitoring)
- **Out of Scope**: Workflow 5 (Trade Adjustments - advanced topic for later)

### 1.3 Architecture
- **Execution**: Python programs scheduled via cron/scheduler
- **Database**: NocoDB tables with abstraction layer
- **Trading API**: Alpaca API integration
- **AI Integration**: AI agent for trade analysis and decision making

---

## 2. Database Schema (NocoDB Tables)

### 2.1 Table: `analysis_decision`

**For PRODUCTION (NocoDB)**: Table already exists, only ADD these 4 fields:

| Column | Data Type | Default | Description | When Used |
|--------|-----------|---------|-------------|-----------|
| existing_order_id | VARCHAR(255) | NULL | Alpaca order ID if order exists | Workflow 1 (after Save Analysis) |
| existing_trade_journal_id | INT | NULL | FK to trade_journal if position exists | Workflow 1 (after Save Analysis) |
| executed | BOOLEAN | false | Whether decision has been executed | Workflow 2 (when order placed) |
| execution_time | DATETIME | NULL | When decision was executed | Workflow 2 (when order placed) |

**For TESTING/DEVELOPMENT**: Create complete table with all fields:

| Column | Data Type | Default | Description |
|--------|-----------|---------|-------------|
| Analysis_Id | VARCHAR(255) | PRIMARY KEY | Unique analysis identifier |
| Date_time | TIMESTAMP | NOW() | Analysis timestamp |
| Ticker | VARCHAR(50) | NOT NULL | Stock symbol |
| Chart | TEXT | NULL | Chart image reference |
| Analysis_Prompt | TEXT | NULL | Prompt sent to AI |
| 3_Month_Chart | TEXT | NULL | 3-month chart reference |
| Analysis | TEXT | NULL | AI analysis text |
| Trade_Type | VARCHAR(50) | NULL | Type of trade |
| Decision | JSONB | NULL | AI decision in JSON format |
| Approve | BOOLEAN | false | Manual approval flag |
| Date | DATE | NULL | Date formula field |
| Remarks | TEXT | NULL | Additional notes |
| **existing_order_id** | VARCHAR(255) | NULL | **Alpaca order ID** |
| **existing_trade_journal_id** | INT | NULL | **FK to trade_journal** |
| **executed** | BOOLEAN | false | **Execution status** |
| **execution_time** | TIMESTAMP | NULL | **When executed** |

**Decision JSON Structure** (stored in `Decision` column):

**PRIMARY_ACTION VALUES**: "NEW_TRADE" | "AMEND" | "CANCEL" | "NO_ACTION"

**NEW_TRADE - Swing Trade Example:**
```json
{
    "symbol": "NVDA",
    "analysis_date": "2025-01-15",
    "support": 100.1,
    "resistance": 150.1,
    "primary_action": "NEW_TRADE",
    "new_trade": {
        "strategy": "SWING",
        "pattern": "PATTERN_1",
        "qty": 45,
        "side": "buy",
        "type": "limit",
        "time_in_force": "day",
        "limit_price": 133.80,
        "stop_loss": {
            "stop_price": 124.00
        },
        "take_profit": {
            "limit_price": 145.50
        },
        "reward_risk_ratio": 2.15,
        "risk_amount": 100.00,
        "risk_percentage": 1.0
    }
}
```

**NEW_TRADE - Trend Trade Example:**
```json
{
    "symbol": "AAPL",
    "analysis_date": "2025-01-15",
    "support": 100.1,
    "resistance": 150.1,
    "primary_action": "NEW_TRADE",
    "new_trade": {
        "strategy": "TREND",
        "pattern": "PATTERN_3",
        "qty": 30,
        "side": "buy",
        "type": "limit",
        "time_in_force": "day",
        "limit_price": 225.50,
        "stop_loss": {
            "stop_price": 218.00
        },
        "reward_risk_ratio": 3.5,
        "risk_amount": 100.00,
        "risk_percentage": 1.0
    }
}
```
Note: TREND trades do not include take_profit.

**AMEND Example:**
```json
{
    "symbol": "NVDA",
    "analysis_date": "2025-01-15",
    "support": 100.1,
    "resistance": 150.1,
    "primary_action": "AMEND",
    "new_trade": {
        "strategy": "SWING",
        "pattern": "PATTERN_1",
        "qty": 45,
        "side": "buy",
        "type": "limit",
        "time_in_force": "day",
        "limit_price": 133.80,
        "stop_loss": {
            "stop_price": 124.00
        },
        "take_profit": {
            "limit_price": 145.50
        },
        "reward_risk_ratio": 2.15,
        "risk_amount": 100.00,
        "risk_percentage": 1.0
    }
}
```

**CANCEL Example:**
```json
{
    "symbol": "NVDA",
    "analysis_date": "2025-01-15",
    "support": 100.1,
    "resistance": 150.1,
    "primary_action": "CANCEL"
}
```

**NO_ACTION Example:**
```json
{
    "symbol": "AMD",
    "analysis_date": "2025-01-15",
    "support": 100.1,
    "resistance": 150.1,
    "primary_action": "NO_ACTION"
}
```

### 2.2 Table: `trade_journal`
**Purpose**: Track individual trades from order to completion

| Column | Data Type | Default | Description | When Used |
|--------|-----------|---------|-------------|-----------|
| id | INT AUTO_INCREMENT | - | Primary key | Auto-generated |
| trade_id | VARCHAR(50) UNIQUE | - | Unique trade identifier | Workflow 2 |
| symbol | VARCHAR(50) | - | Stock ticker | Workflow 2 |
| trade_style | VARCHAR(20) | - | DAYTRADE or SWING | Workflow 2 |
| pattern | VARCHAR(50) | - | Chart pattern | Workflow 2 |
| status | VARCHAR(20) | ORDERED | Trade status | Workflows 2-4 |
| initial_analysis_id | VARCHAR(255) | - | References analysis_decision (no FK) | Workflow 2 |
| planned_entry | DECIMAL(10,2) | - | Planned entry price | Workflow 2 |
| planned_stop_loss | DECIMAL(10,2) | - | Planned SL price | Workflow 2 |
| planned_take_profit | DECIMAL(10,2) | NULL | Planned TP price | Workflow 2 |
| planned_qty | INT | - | Planned quantity | Workflow 2 |
| actual_entry | DECIMAL(10,2) | NULL | Actual entry price | Workflow 3 |
| actual_qty | INT | NULL | Actual quantity filled | Workflow 3 |
| current_stop_loss | DECIMAL(10,2) | NULL | Current SL (if adjusted) | Workflow 4 |
| days_open | INT | 0 | Days position held | Workflow 1 |
| last_review_date | DATE | NULL | Last analysis review | Workflow 1 |
| exit_date | DATE | NULL | Trade exit date | Workflow 4 |
| exit_price | DECIMAL(10,2) | NULL | Exit price | Workflow 4 |
| actual_pnl | DECIMAL(10,2) | NULL | Realized P&L | Workflow 4 |
| exit_reason | VARCHAR(100) | NULL | Exit reason | Workflow 4 |
| created_at | DATETIME | NOW() | Record creation | Auto |
| updated_at | DATETIME | NOW() | Last update | Auto on update |

**Status Values**: ORDERED, POSITION, CLOSED, CANCELLED

**Exit Reasons**: STOPPED_OUT, TARGET_HIT, MANUAL_EXIT, CANCELLED, AMENDED

**Note**: Relationships managed at application level (no foreign key constraints)

### 2.3 Table: `order_execution`
**Purpose**: Track all orders (entry, stop-loss, take-profit)

| Column | Data Type | Default | Description | When Used |
|--------|-----------|---------|-------------|-----------|
| id | INT AUTO_INCREMENT | - | Primary key | Auto-generated |
| trade_journal_id | INT | - | References trade_journal (no FK) | Workflows 2-3 |
| analysis_decision_id | VARCHAR(255) | NULL | References analysis_decision (no FK) | Workflow 2 |
| alpaca_order_id | VARCHAR(255) | - | Alpaca's order ID | Workflows 2-3 |
| client_order_id | VARCHAR(255) | NULL | Our internal order ID | Workflow 2 |
| order_type | VARCHAR(50) | - | ENTRY/STOP_LOSS/TAKE_PROFIT | Workflows 2-3 |
| side | VARCHAR(10) | - | buy or sell | Workflows 2-3 |
| order_status | VARCHAR(20) | pending | Order status | Workflow 3 |
| time_in_force | VARCHAR(10) | - | day, gtc, ioc, fok | Workflows 2-3 |
| qty | INT | - | Order quantity | Workflows 2-3 |
| limit_price | DECIMAL(10,2) | NULL | Limit price if applicable | Workflows 2-3 |
| stop_price | DECIMAL(10,2) | NULL | Stop price if applicable | Workflow 3 |
| filled_qty | INT | NULL | Quantity filled | Workflow 3 |
| filled_avg_price | DECIMAL(10,2) | NULL | Average fill price | Workflow 3 |
| filled_at | DATETIME | NULL | Fill timestamp | Workflow 3 |
| created_at | DATETIME | NOW() | Record creation | Auto |

**Order Status Values**: pending, partially_filled, filled, cancelled, rejected

**Note**: Relationships managed at application level (no foreign key constraints)

### 2.4 Table: `position_tracking`
**Purpose**: Real-time tracking of open positions

| Column | Data Type | Default | Description | When Used |
|--------|-----------|---------|-------------|-----------|
| id | INT AUTO_INCREMENT | - | Primary key | Auto-generated |
| trade_journal_id | INT | - | References trade_journal (no FK) | Workflow 3 |
| symbol | VARCHAR(50) | - | Stock ticker | Workflow 3 |
| qty | INT | - | Current position size | Workflow 3 |
| avg_entry_price | DECIMAL(10,2) | - | Average entry price | Workflow 3 |
| current_price | DECIMAL(10,2) | - | Latest market price | Workflow 4 |
| market_value | DECIMAL(10,2) | - | Position market value | Workflow 4 |
| cost_basis | DECIMAL(10,2) | - | Total cost basis | Workflow 3 |
| unrealized_pnl | DECIMAL(10,2) | 0 | Unrealized P&L | Workflow 4 |
| stop_loss_order_id | VARCHAR(255) | NULL | Active SL order ID | Workflow 3 |
| take_profit_order_id | VARCHAR(255) | NULL | Active TP order ID | Workflow 3 |
| last_updated | DATETIME | NOW() | Last sync time | Workflow 4 |

**Note**: Relationships managed at application level (no foreign key constraints)

### 2.5 Table: `trade_adjustments`
**Purpose**: Track all trade modifications (future use - Workflow 5)

| Column | Data Type | Default | Description |
|--------|-----------|---------|-------------|
| id | INT AUTO_INCREMENT | - | Primary key |
| trade_journal_id | INT | - | References trade_journal (no FK) |
| analysis_decision_id | VARCHAR(255) | - | References analysis_decision (no FK) |
| adjustment_type | VARCHAR(50) | - | ADD_POSITION/ADJUST_STOP_LOSS/TAKE_PARTIAL_PROFITS |
| old_stop_loss | DECIMAL(10,2) | NULL | Previous SL price |
| new_stop_loss | DECIMAL(10,2) | NULL | New SL price |
| old_qty | INT | NULL | Previous quantity |
| new_qty | INT | NULL | New quantity |
| order_id_affected | VARCHAR(255) | NULL | Related order ID |
| reason | TEXT | - | Adjustment rationale |
| executed | BOOLEAN | false | Execution status |
| created_at | DATETIME | NOW() | Record creation |

**Note**: Relationships managed at application level (no foreign key constraints)

---

## 3. PostgreSQL Abstraction Layer (Direct DB Access)

### 3.1 Requirements
Create a Python abstraction layer that connects directly to the PostgreSQL database underneath NocoDB:

```python
# Interface design
class TradingDB:
    def __init__(self, connection_string: str)
    def execute_query(self, query: str, params: tuple = None) -> List[dict]
    def execute_update(self, query: str, params: tuple = None) -> int
    def insert(self, table: str, data: dict) -> int  # Returns record ID
    def update(self, table: str, record_id: int, data: dict) -> bool
    def get_by_id(self, table: str, record_id: int) -> dict
    def query(self, table: str, where_clause: str = None, params: tuple = None) -> List[dict]
```

### 3.2 Features (Simplified)
- PostgreSQL connection using psycopg2
- Basic CRUD operations
- Parameterized queries to prevent SQL injection
- Simple error handling and logging

### 3.3 Configuration
```python
# config.py or environment variables
POSTGRES_HOST = "localhost"  # or NocoDB's Postgres host
POSTGRES_PORT = 5432
POSTGRES_DB = "nocodb_database"
POSTGRES_USER = "postgres"
POSTGRES_PASSWORD = "your_password"
```

---

## 4. Programs & Workflows

### 4.1 n8n Workflow 1: Analysis & Decision (EXISTING - Modify Only)
**Your existing n8n workflow handles this - NO Python program needed**

#### Modification Required: After "Save Analysis" Node

Add a new node to update the `analysis_decision` record with these 4 fields:

**Node: "Update Analysis Decision"**
- **Type**: PostgreSQL node (or NocoDB update)
- **Operation**: UPDATE
- **Table**: `analysis_decision`
- **Where**: `id = {{ $node["Save Analysis"].json["id"] }}`

**Fields to Set**:
```javascript
{
  "existing_order_id": "{{ $node["Current Position"].json["pending_order_id"] || null }}",
  "existing_trade_journal_id": "{{ $node["Current Position"].json["trade_journal_id"] || null }}",
  "executed": false,
  "execution_time": null
}
```

**Logic**:
- `existing_order_id`: Get from "Current Position" node if there's a pending order for this symbol
- `existing_trade_journal_id`: Get from "Current Position" node if there's an open position for this symbol  
- `executed`: Always set to `false` initially
- `execution_time`: Always set to `null` initially

**Additional Logic for NO_ACTION**:
If `primary_action = 'NO_ACTION'` AND `existing_trade_journal_id` is not null:
```sql
UPDATE trade_journal 
SET 
  days_open = days_open + 1,
  last_review_date = CURRENT_DATE
WHERE id = existing_trade_journal_id
```

---

### 4.2 Program 2: `order_executor.py`
---

### 4.2 Program 2: `order_executor.py`
**Schedule**: Once daily at 9:45 AM ET (15 minutes after market open)  
**Purpose**: Execute approved trading decisions from overnight/pre-market analysis

#### Python Implementation:

```python
#!/usr/bin/env python3
"""
Order Executor - Executes approved trading decisions
"""
import os
from datetime import datetime
from dotenv import load_dotenv
from alpaca.trading.client import TradingClient
from alpaca.trading.requests import MarketOrderRequest, LimitOrderRequest
from alpaca.trading.enums import OrderSide, TimeInForce
from db_layer import TradingDB
import logging

load_dotenv()
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class OrderExecutor:
    def __init__(self):
        self.db = TradingDB()
        self.alpaca = TradingClient(
            api_key=os.getenv('ALPACA_API_KEY'),
            secret_key=os.getenv('ALPACA_SECRET_KEY'),
            paper=os.getenv('ALPACA_PAPER', 'true').lower() == 'true'
        )
    
    def run(self):
        """Main execution loop"""
        try:
            # Get unexecuted decisions
            decisions = self.db.execute_query("""
                SELECT * FROM analysis_decision
                WHERE executed = false
                AND "Approve" = true
                AND decision->>'primary_action' IN ('NEW_TRADE', 'CANCEL', 'AMEND')
                ORDER BY "Date_time" ASC
            """)
            
            logger.info(f"Found {len(decisions)} unexecuted decisions")
            
            for decision in decisions:
                self.process_decision(decision)
                
        except Exception as e:
            logger.error(f"Error in order executor: {e}")
    
    def process_decision(self, decision):
        """Process a single trading decision"""
        decision_data = decision['decision']  # JSON field
        primary_action = decision_data.get('primary_action')
        
        try:
            if primary_action == 'NEW_TRADE':
                self.handle_new_trade(decision)
            elif primary_action == 'CANCEL':
                self.handle_cancel(decision)
            elif primary_action == 'AMEND':
                self.handle_amend(decision)
            
        except Exception as e:
            logger.error(f"Error processing decision {decision['Analysis Id']}: {e}")
    
    def handle_new_trade(self, decision):
        """Handle NEW_TRADE action"""
        decision_data = decision['decision']
        
        # Extract trade parameters
        symbol = decision['Ticker']
        qty = decision_data.get('qty')
        entry_price = decision_data.get('entry_price')
        stop_loss = decision_data.get('stop_loss')
        take_profit = decision_data.get('take_profit')
        trade_style = decision_data.get('trade_style', 'DAYTRADE')
        
        # Submit order to Alpaca
        order_request = LimitOrderRequest(
            symbol=symbol,
            qty=qty,
            side=OrderSide.BUY,
            time_in_force=TimeInForce.DAY,
            limit_price=entry_price
        )
        
        order = self.alpaca.submit_order(order_request)
        
        # Create trade_journal entry
        trade_journal_id = self.db.execute_query("""
            INSERT INTO trade_journal (
                trade_id, symbol, trade_style, pattern, status,
                initial_analysis_id, planned_entry, planned_stop_loss,
                planned_take_profit, planned_qty, created_at, updated_at
            ) VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, NOW(), NOW())
            RETURNING id
        """, (
            f"{symbol}_{datetime.now().strftime('%Y%m%d%H%M%S')}",
            symbol,
            trade_style,
            decision_data.get('pattern'),
            'ORDERED',
            decision['Analysis Id'],
            entry_price,
            stop_loss,
            take_profit,
            qty
        ))[0]['id']
        
        # Create order_execution entry
        self.db.execute_query("""
            INSERT INTO order_execution (
                trade_journal_id, analysis_decision_id, alpaca_order_id,
                order_type, side, order_status, time_in_force, qty,
                limit_price, created_at
            ) VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, NOW())
        """, (
            trade_journal_id,
            decision['Analysis Id'],
            order.id,
            'ENTRY',
            'buy',
            'pending',
            'day',
            qty,
            entry_price
        ))
        
        # Update analysis_decision
        self.db.execute_query("""
            UPDATE analysis_decision
            SET executed = true,
                execution_time = NOW(),
                existing_order_id = %s,
                existing_trade_journal_id = %s
            WHERE "Analysis_Id" = %s
        """, (order.id, trade_journal_id, decision['Analysis Id']))
        
        logger.info(f"Placed order {order.id} for {symbol}")
    
    def handle_cancel(self, decision):
        """Handle CANCEL action"""
        order_id = decision['existing_order_id']
        
        if not order_id:
            logger.warning(f"No order to cancel for {decision['Analysis Id']}")
            return
        
        # Cancel order with Alpaca
        self.alpaca.cancel_order_by_id(order_id)
        
        # Update trade_journal
        self.db.execute_query("""
            UPDATE trade_journal
            SET status = 'CANCELLED',
                exit_date = CURRENT_DATE,
                exit_reason = 'CANCELLED',
                updated_at = NOW()
            WHERE id = %s
        """, (decision['existing_trade_journal_id'],))
        
        # Mark decision as executed
        self.db.execute_query("""
            UPDATE analysis_decision
            SET executed = true,
                execution_time = NOW()
            WHERE "Analysis_Id" = %s
        """, (decision['Analysis Id'],))
        
        logger.info(f"Cancelled order {order_id}")
    
    def handle_amend(self, decision):
        """Handle AMEND action"""
        # Cancel old order
        self.handle_cancel(decision)
        
        # Place new order
        self.handle_new_trade(decision)
        
        logger.info(f"Amended order for {decision['Ticker']}")

if __name__ == "__main__":
    executor = OrderExecutor()
    executor.run()
```

#### Error Handling:
- Order rejection → log error, mark as executed with note
- API failures → log and skip, will retry next run
- Database errors → log and continue to next decision

---

### 4.3 Program 3: `order_monitor.py`
**Schedule**: Every 5 minutes during trading hours (9:30 AM - 4:00 PM ET) + Once at 6:00 PM ET  
**Purpose**: Monitor order status and place stop-loss/take-profit orders

#### Python Implementation:

```python
#!/usr/bin/env python3
"""
Order Monitor - Syncs order status and manages risk orders
"""
import os
from datetime import datetime
from dotenv import load_dotenv
from alpaca.trading.client import TradingClient
from alpaca.trading.requests import StopLossRequest, TakeProfitRequest
from alpaca.trading.enums import OrderSide, TimeInForce, OrderType
from db_layer import TradingDB
import logging

load_dotenv()
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class OrderMonitor:
    def __init__(self):
        self.db = TradingDB()
        self.alpaca = TradingClient(
            api_key=os.getenv('ALPACA_API_KEY'),
            secret_key=os.getenv('ALPACA_SECRET_KEY'),
            paper=os.getenv('ALPACA_PAPER', 'true').lower() == 'true'
        )
    
    def run(self):
        """Main monitoring loop"""
        try:
            # Get active orders
            orders = self.db.execute_query("""
                SELECT * FROM order_execution
                WHERE order_status IN ('pending', 'partially_filled')
            """)
            
            for order in orders:
                self.sync_order_status(order)
                
        except Exception as e:
            logger.error(f"Error in order monitor: {e}")
    
    def sync_order_status(self, order):
        """Sync order status with Alpaca"""
        try:
            alpaca_order = self.alpaca.get_order_by_id(order['alpaca_order_id'])
            
            # Update order_execution record
            self.db.execute_query("""
                UPDATE order_execution
                SET order_status = %s,
                    filled_qty = %s,
                    filled_avg_price = %s,
                    filled_at = %s
                WHERE id = %s
            """, (
                alpaca_order.status,
                alpaca_order.filled_qty if alpaca_order.filled_qty else None,
                float(alpaca_order.filled_avg_price) if alpaca_order.filled_avg_price else None,
                alpaca_order.filled_at,
                order['id']
            ))
            
            # Handle filled entry orders
            if alpaca_order.status == 'filled' and order['order_type'] == 'ENTRY':
                self.handle_entry_filled(order, alpaca_order)
            
            # Handle filled exit orders (SL/TP)
            elif alpaca_order.status == 'filled' and order['order_type'] in ('STOP_LOSS', 'TAKE_PROFIT'):
                self.handle_exit_filled(order, alpaca_order)
                
        except Exception as e:
            logger.error(f"Error syncing order {order['alpaca_order_id']}: {e}")
    
    def handle_entry_filled(self, order, alpaca_order):
        """Handle filled entry order"""
        trade_journal_id = order['trade_journal_id']
        
        # Get trade details
        trade = self.db.execute_query("""
            SELECT * FROM trade_journal WHERE id = %s
        """, (trade_journal_id,))[0]
        
        # Update trade_journal
        self.db.execute_query("""
            UPDATE trade_journal
            SET status = 'POSITION',
                actual_entry = %s,
                actual_qty = %s,
                updated_at = NOW()
            WHERE id = %s
        """, (
            float(alpaca_order.filled_avg_price),
            alpaca_order.filled_qty,
            trade_journal_id
        ))
        
        # Create position_tracking entry
        self.db.execute_query("""
            INSERT INTO position_tracking (
                trade_journal_id, symbol, qty, avg_entry_price,
                current_price, market_value, cost_basis,
                unrealized_pnl, last_updated
            ) VALUES (%s, %s, %s, %s, %s, %s, %s, %s, NOW())
        """, (
            trade_journal_id,
            trade['symbol'],
            alpaca_order.filled_qty,
            float(alpaca_order.filled_avg_price),
            float(alpaca_order.filled_avg_price),  # Initial price
            float(alpaca_order.filled_avg_price) * alpaca_order.filled_qty,
            float(alpaca_order.filled_avg_price) * alpaca_order.filled_qty,
            0.0  # Initial P&L
        ))
        
        # Place Stop-Loss order
        sl_order = self.place_stop_loss(trade, alpaca_order.filled_qty)
        
        # Place Take-Profit order (if SWING trade)
        tp_order = None
        if trade['trade_style'] == 'SWING' and trade['planned_take_profit']:
            tp_order = self.place_take_profit(trade, alpaca_order.filled_qty)
        
        logger.info(f"Entry filled for {trade['symbol']}, placed SL/TP orders")
    
    def place_stop_loss(self, trade, qty):
        """Place stop-loss order"""
        from alpaca.trading.requests import StopOrderRequest
        
        order_request = StopOrderRequest(
            symbol=trade['symbol'],
            qty=qty,
            side=OrderSide.SELL,
            time_in_force=TimeInForce.GTC,
            stop_price=float(trade['planned_stop_loss'])
        )
        
        sl_order = self.alpaca.submit_order(order_request)
        
        # Record in order_execution
        self.db.execute_query("""
            INSERT INTO order_execution (
                trade_journal_id, alpaca_order_id, order_type,
                side, order_status, time_in_force, qty,
                stop_price, created_at
            ) VALUES (%s, %s, %s, %s, %s, %s, %s, %s, NOW())
        """, (
            trade['id'],
            sl_order.id,
            'STOP_LOSS',
            'sell',
            'pending',
            'gtc',
            qty,
            float(trade['planned_stop_loss'])
        ))
        
        # Update position_tracking
        self.db.execute_query("""
            UPDATE position_tracking
            SET stop_loss_order_id = %s
            WHERE trade_journal_id = %s
        """, (sl_order.id, trade['id']))
        
        return sl_order
    
    def place_take_profit(self, trade, qty):
        """Place take-profit order"""
        from alpaca.trading.requests import LimitOrderRequest
        
        order_request = LimitOrderRequest(
            symbol=trade['symbol'],
            qty=qty,
            side=OrderSide.SELL,
            time_in_force=TimeInForce.GTC,
            limit_price=float(trade['planned_take_profit'])
        )
        
        tp_order = self.alpaca.submit_order(order_request)
        
        # Record in order_execution
        self.db.execute_query("""
            INSERT INTO order_execution (
                trade_journal_id, alpaca_order_id, order_type,
                side, order_status, time_in_force, qty,
                limit_price, created_at
            ) VALUES (%s, %s, %s, %s, %s, %s, %s, %s, NOW())
        """, (
            trade['id'],
            tp_order.id,
            'TAKE_PROFIT',
            'sell',
            'pending',
            'gtc',
            qty,
            float(trade['planned_take_profit'])
        ))
        
        # Update position_tracking
        self.db.execute_query("""
            UPDATE position_tracking
            SET take_profit_order_id = %s
            WHERE trade_journal_id = %s
        """, (tp_order.id, trade['id']))
        
        return tp_order
    
    def handle_exit_filled(self, order, alpaca_order):
        """Handle filled exit order (SL or TP)"""
        trade_journal_id = order['trade_journal_id']
        
        # Get trade details
        trade = self.db.execute_query("""
            SELECT * FROM trade_journal WHERE id = %s
        """, (trade_journal_id,))[0]
        
        # Calculate P&L
        exit_price = float(alpaca_order.filled_avg_price)
        entry_price = float(trade['actual_entry'])
        qty = alpaca_order.filled_qty
        pnl = (exit_price - entry_price) * qty
        
        # Determine exit reason
        exit_reason = 'STOPPED_OUT' if order['order_type'] == 'STOP_LOSS' else 'TARGET_HIT'
        
        # Update trade_journal
        self.db.execute_query("""
            UPDATE trade_journal
            SET status = 'CLOSED',
                exit_date = CURRENT_DATE,
                exit_price = %s,
                actual_pnl = %s,
                exit_reason = %s,
                updated_at = NOW()
            WHERE id = %s
        """, (exit_price, pnl, exit_reason, trade_journal_id))
        
        # Delete position_tracking
        self.db.execute_query("""
            DELETE FROM position_tracking WHERE trade_journal_id = %s
        """, (trade_journal_id,))
        
        # Cancel remaining order (if SL hit, cancel TP and vice versa)
        self.cancel_remaining_orders(trade_journal_id, order['alpaca_order_id'])
        
        logger.info(f"Position closed: {trade['symbol']}, P&L: ${pnl:.2f}, Reason: {exit_reason}")
    
    def cancel_remaining_orders(self, trade_journal_id, filled_order_id):
        """Cancel remaining SL/TP orders"""
        orders = self.db.execute_query("""
            SELECT alpaca_order_id FROM order_execution
            WHERE trade_journal_id = %s
            AND order_type IN ('STOP_LOSS', 'TAKE_PROFIT')
            AND order_status = 'pending'
            AND alpaca_order_id != %s
        """, (trade_journal_id, filled_order_id))
        
        for order in orders:
            try:
                self.alpaca.cancel_order_by_id(order['alpaca_order_id'])
                logger.info(f"Cancelled order {order['alpaca_order_id']}")
            except Exception as e:
                logger.warning(f"Could not cancel order {order['alpaca_order_id']}: {e}")

if __name__ == "__main__":
    monitor = OrderMonitor()
    monitor.run()
```

#### Error Handling:
- Order not found → log and skip
- Order placement failure → log and retry next cycle
- Cancel failure → log warning, continue
---

### 4.4 Program 4: `position_monitor.py`
**Schedule**: Every 10 minutes during trading hours (9:30 AM - 4:00 PM ET) + Once at 6:15 PM ET  
**Purpose**: Update position values and unrealized P&L

#### Python Implementation:

```python
#!/usr/bin/env python3
"""
Position Monitor - Updates position values and P&L
"""
import os
from dotenv import load_dotenv
from alpaca.trading.client import TradingClient
from alpaca.data.historical import StockHistoricalDataClient
from alpaca.data.requests import StockLatestQuoteRequest
from db_layer import TradingDB
import logging

load_dotenv()
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class PositionMonitor:
    def __init__(self):
        self.db = TradingDB()
        self.trading_client = TradingClient(
            api_key=os.getenv('ALPACA_API_KEY'),
            secret_key=os.getenv('ALPACA_SECRET_KEY'),
            paper=os.getenv('ALPACA_PAPER', 'true').lower() == 'true'
        )
        self.data_client = StockHistoricalDataClient(
            api_key=os.getenv('ALPACA_API_KEY'),
            secret_key=os.getenv('ALPACA_SECRET_KEY')
        )
    
    def run(self):
        """Main monitoring loop"""
        try:
            # Get all active positions
            positions = self.db.execute_query("""
                SELECT * FROM position_tracking
            """)
            
            for position in positions:
                self.update_position(position)
                
        except Exception as e:
            logger.error(f"Error in position monitor: {e}")
    
    def update_position(self, position):
        """Update position values"""
        try:
            symbol = position['symbol']
            
            # Get current price
            request = StockLatestQuoteRequest(symbol_or_symbols=symbol)
            quote = self.data_client.get_stock_latest_quote(request)[symbol]
            current_price = float(quote.ask_price)
            
            # Calculate metrics
            qty = position['qty']
            avg_entry = float(position['avg_entry_price'])
            market_value = current_price * qty
            unrealized_pnl = (current_price - avg_entry) * qty
            
            # Update position_tracking
            self.db.execute_query("""
                UPDATE position_tracking
                SET current_price = %s,
                    market_value = %s,
                    unrealized_pnl = %s,
                    last_updated = NOW()
                WHERE id = %s
            """, (current_price, market_value, unrealized_pnl, position['id']))
            
            logger.info(f"Updated {symbol}: Price ${current_price:.2f}, P&L ${unrealized_pnl:.2f}")
            
        except Exception as e:
            logger.error(f"Error updating position {position['symbol']}: {e}")
    
    def check_for_closed_positions(self):
        """Verify positions still exist in Alpaca"""
        try:
            # Get Alpaca positions
            alpaca_positions = {p.symbol: p for p in self.trading_client.get_all_positions()}
            
            # Get our tracked positions
            tracked_positions = self.db.execute_query("""
                SELECT * FROM position_tracking
            """)
            
            for position in tracked_positions:
                if position['symbol'] not in alpaca_positions:
                    # Position closed but we missed it
                    logger.warning(f"Position {position['symbol']} closed outside of monitoring")
                    self.reconcile_closed_position(position)
                    
        except Exception as e:
            logger.error(f"Error checking closed positions: {e}")
    
    def reconcile_closed_position(self, position):
        """Reconcile a position that was closed"""
        # Try to find the closing order
        orders = self.db.execute_query("""
            SELECT * FROM order_execution
            WHERE trade_journal_id = %s
            AND order_type IN ('STOP_LOSS', 'TAKE_PROFIT')
            AND order_status = 'filled'
            ORDER BY filled_at DESC
            LIMIT 1
        """, (position['trade_journal_id'],))
        
        if orders:
            # Use the filled order data
            order = orders[0]
            exit_price = float(order['filled_avg_price'])
            pnl = (exit_price - float(position['avg_entry_price'])) * position['qty']
            exit_reason = 'STOPPED_OUT' if order['order_type'] == 'STOP_LOSS' else 'TARGET_HIT'
        else:
            # Manual close or unknown
            exit_price = float(position['current_price'])
            pnl = float(position['unrealized_pnl'])
            exit_reason = 'MANUAL_EXIT'
        
        # Update trade_journal
        self.db.execute_query("""
            UPDATE trade_journal
            SET status = 'CLOSED',
                exit_date = CURRENT_DATE,
                exit_price = %s,
                actual_pnl = %s,
                exit_reason = %s,
                updated_at = NOW()
            WHERE id = %s
        """, (exit_price, pnl, exit_reason, position['trade_journal_id']))
        
        # Delete position_tracking
        self.db.execute_query("""
            DELETE FROM position_tracking WHERE id = %s
        """, (position['id'],))
        
        logger.info(f"Reconciled closed position: {position['symbol']}")

if __name__ == "__main__":
    monitor = PositionMonitor()
    monitor.run()
    monitor.check_for_closed_positions()
```

#### Error Handling:
- Price data unavailable → skip update, retry next cycle
- Position mismatch → reconcile with Alpaca
- Network errors → log and retry next cycle

---

## 5. Database Abstraction Layer Implementation

### 5.1 `db_layer.py`

```python
"""
PostgreSQL Database Abstraction Layer
Connects directly to Postgres DB underneath NocoDB
"""
import psycopg2
from psycopg2.extras import RealDictCursor
import logging
import os
from dotenv import load_dotenv

load_dotenv()
logger = logging.getLogger(__name__)

class TradingDB:
    def __init__(self, test_mode=False):
        """
        Initialize database connection using environment variables
        test_mode: If True, use TEST_ prefixed environment variables
        """
        if test_mode:
            prefix = 'TEST_'
        else:
            prefix = ''
            
        self.connection_string = (
            f"host={os.getenv(f'{prefix}POSTGRES_HOST', 'localhost')} "
            f"port={os.getenv(f'{prefix}POSTGRES_PORT', '5432')} "
            f"dbname={os.getenv(f'{prefix}POSTGRES_DB', 'nocodb')} "
            f"user={os.getenv(f'{prefix}POSTGRES_USER', 'postgres')} "
            f"password={os.getenv(f'{prefix}POSTGRES_PASSWORD', '')}"
        )
        self.conn = None
        self.connect()
    
    def connect(self):
        """Establish database connection"""
        try:
            self.conn = psycopg2.connect(
                self.connection_string,
                cursor_factory=RealDictCursor
            )
            logger.info("Database connected successfully")
        except Exception as e:
            logger.error(f"Database connection failed: {e}")
            raise
    
    def execute_query(self, query, params=None):
        """
        Execute a SELECT query and return results as list of dicts
        """
        try:
            with self.conn.cursor() as cursor:
                cursor.execute(query, params)
                return cursor.fetchall()
        except Exception as e:
            logger.error(f"Query execution failed: {e}")
            self.conn.rollback()
            raise
    
    def execute_update(self, query, params=None):
        """
        Execute INSERT/UPDATE/DELETE and return affected rows
        """
        try:
            with self.conn.cursor() as cursor:
                cursor.execute(query, params)
                self.conn.commit()
                return cursor.rowcount
        except Exception as e:
            logger.error(f"Update execution failed: {e}")
            self.conn.rollback()
            raise
    
    def insert(self, table, data):
        """
        Insert a record and return the ID
        data: dict of column: value
        """
        columns = ', '.join(data.keys())
        placeholders = ', '.join(['%s'] * len(data))
        query = f"INSERT INTO {table} ({columns}) VALUES ({placeholders}) RETURNING id"
        
        try:
            with self.conn.cursor() as cursor:
                cursor.execute(query, tuple(data.values()))
                self.conn.commit()
                return cursor.fetchone()['id']
        except Exception as e:
            logger.error(f"Insert failed: {e}")
            self.conn.rollback()
            raise
    
    def update(self, table, record_id, data):
        """
        Update a record by ID
        """
        set_clause = ', '.join([f"{k} = %s" for k in data.keys()])
        query = f"UPDATE {table} SET {set_clause} WHERE id = %s"
        params = tuple(data.values()) + (record_id,)
        
        try:
            with self.conn.cursor() as cursor:
                cursor.execute(query, params)
                self.conn.commit()
                return cursor.rowcount > 0
        except Exception as e:
            logger.error(f"Update failed: {e}")
            self.conn.rollback()
            raise
    
    def get_by_id(self, table, record_id):
        """Get a single record by ID"""
        query = f"SELECT * FROM {table} WHERE id = %s"
        results = self.execute_query(query, (record_id,))
        return results[0] if results else None
    
    def query(self, table, where_clause=None, params=None):
        """
        Query table with optional WHERE clause
        """
        query = f"SELECT * FROM {table}"
        if where_clause:
            query += f" WHERE {where_clause}"
        return self.execute_query(query, params)
    
    def create_schema(self):
        """
        Create all required tables for testing/development
        Use this for test databases that start empty!
        For production NocoDB, manually add 4 fields to existing analysis_decision table.
        
        NOTE: No foreign key constraints as NocoDB doesn't support them.
        Relationships are managed at application level.
        """
        schema_sql = """
        -- Create analysis_decision table (for testing/dev only)
        CREATE TABLE IF NOT EXISTS analysis_decision (
            "Analysis_Id" VARCHAR(255) PRIMARY KEY,
            "Date_time" TIMESTAMP DEFAULT NOW(),
            "Ticker" VARCHAR(50) NOT NULL,
            "Chart" TEXT,
            "Analysis_Prompt" TEXT,
            "3_Month_Chart" TEXT,
            "Analysis" TEXT,
            "Trade_Type" VARCHAR(50),
            "Decision" JSONB,
            "Approve" BOOLEAN DEFAULT false,
            "Date" DATE,
            "Remarks" TEXT,
            existing_order_id VARCHAR(255),
            existing_trade_journal_id INT,
            executed BOOLEAN DEFAULT false,
            execution_time TIMESTAMP
        );
        
        -- Create trade_journal table
        CREATE TABLE IF NOT EXISTS trade_journal (
            id SERIAL PRIMARY KEY,
            trade_id VARCHAR(50) UNIQUE NOT NULL,
            symbol VARCHAR(50) NOT NULL,
            trade_style VARCHAR(20) NOT NULL,
            pattern VARCHAR(50),
            status VARCHAR(20) NOT NULL DEFAULT 'ORDERED',
            initial_analysis_id VARCHAR(255),
            planned_entry DECIMAL(10,2) NOT NULL,
            planned_stop_loss DECIMAL(10,2) NOT NULL,
            planned_take_profit DECIMAL(10,2),
            planned_qty INT NOT NULL,
            actual_entry DECIMAL(10,2),
            actual_qty INT,
            current_stop_loss DECIMAL(10,2),
            days_open INT DEFAULT 0,
            last_review_date DATE,
            exit_date DATE,
            exit_price DECIMAL(10,2),
            actual_pnl DECIMAL(10,2),
            exit_reason VARCHAR(100),
            created_at TIMESTAMP DEFAULT NOW(),
            updated_at TIMESTAMP DEFAULT NOW()
        );
        
        -- Create order_execution table
        CREATE TABLE IF NOT EXISTS order_execution (
            id SERIAL PRIMARY KEY,
            trade_journal_id INT NOT NULL,
            analysis_decision_id VARCHAR(255),
            alpaca_order_id VARCHAR(255) NOT NULL,
            client_order_id VARCHAR(255),
            order_type VARCHAR(50) NOT NULL,
            side VARCHAR(10) NOT NULL,
            order_status VARCHAR(20) NOT NULL DEFAULT 'pending',
            time_in_force VARCHAR(10) NOT NULL,
            qty INT NOT NULL,
            limit_price DECIMAL(10,2),
            stop_price DECIMAL(10,2),
            filled_qty INT,
            filled_avg_price DECIMAL(10,2),
            filled_at TIMESTAMP,
            created_at TIMESTAMP DEFAULT NOW()
        );
        
        -- Create position_tracking table
        CREATE TABLE IF NOT EXISTS position_tracking (
            id SERIAL PRIMARY KEY,
            trade_journal_id INT NOT NULL UNIQUE,
            symbol VARCHAR(50) NOT NULL,
            qty INT NOT NULL,
            avg_entry_price DECIMAL(10,2) NOT NULL,
            current_price DECIMAL(10,2) NOT NULL,
            market_value DECIMAL(10,2) NOT NULL,
            cost_basis DECIMAL(10,2) NOT NULL,
            unrealized_pnl DECIMAL(10,2) DEFAULT 0,
            stop_loss_order_id VARCHAR(255),
            take_profit_order_id VARCHAR(255),
            last_updated TIMESTAMP DEFAULT NOW()
        );
        
        -- Create indices
        CREATE INDEX IF NOT EXISTS idx_analysis_decision_executed ON analysis_decision(executed);
        CREATE INDEX IF NOT EXISTS idx_analysis_decision_ticker ON analysis_decision("Ticker");
        CREATE INDEX IF NOT EXISTS idx_trade_journal_status ON trade_journal(status);
        CREATE INDEX IF NOT EXISTS idx_trade_journal_symbol ON trade_journal(symbol);
        CREATE INDEX IF NOT EXISTS idx_trade_journal_analysis_id ON trade_journal(initial_analysis_id);
        CREATE INDEX IF NOT EXISTS idx_order_execution_status ON order_execution(order_status);
        CREATE INDEX IF NOT EXISTS idx_order_execution_trade_journal ON order_execution(trade_journal_id);
        CREATE INDEX IF NOT EXISTS idx_position_tracking_symbol ON position_tracking(symbol);
        CREATE INDEX IF NOT EXISTS idx_position_tracking_trade_journal ON position_tracking(trade_journal_id);
        """
        
        try:
            with self.conn.cursor() as cursor:
                cursor.execute(schema_sql)
                self.conn.commit()
                logger.info("Schema created successfully")
        except Exception as e:
            logger.error(f"Schema creation failed: {e}")
            self.conn.rollback()
            raise
    
    def close(self):
        """Close database connection"""
        if self.conn:
            self.conn.close()
            logger.info("Database connection closed")
```

---

## 6. Implementation Priorities

### Phase 1: Foundation (Week 1)
1. Database abstraction layer (`db_layer.py`)
2. Add 4 new fields to `analysis_decision` table in NocoDB
3. Create other required tables: `trade_journal`, `order_execution`, `position_tracking`
4. Environment configuration
5. Basic logging setup

### Phase 2: Core Programs (Week 2)
1. Program 2: `order_executor.py`
2. Program 3: `order_monitor.py`  
3. Program 4: `position_monitor.py`
4. Manual testing with Alpaca paper trading

### Phase 3: Integration (Week 3)
1. Modify n8n Workflow 1 (add "Update Analysis Decision" node)
2. Set up APScheduler
3. End-to-end testing

### Phase 4: Testing & Deployment (Week 4)
1. Write unit tests for different scenarios
2. Paper trading validation
3. Documentation

---

## 7. Technical Requirements

### 7.1 Python Environment
- Python 3.9+
- Virtual environment
- Requirements:
  ```
  alpaca-py>=0.8.0
  psycopg2-binary>=2.9.0
  python-dotenv>=1.0.0
  APScheduler>=3.10.0
  pytz>=2023.3
  
  # Development/Testing only
  testing.postgresql>=1.3.0  # For in-memory PostgreSQL during testing
  ```

### 7.1a Development Database Options

**Option 1: In-Memory PostgreSQL (Recommended for Testing)**
Use `testing.postgresql` library for automated tests:

```python
# test_config.py
import testing.postgresql
from db_layer import TradingDB

# Create temporary PostgreSQL instance
postgresql = testing.postgresql.Postgresql()

# Get connection parameters
db_params = postgresql.dsn()
# {'database': 'test', 'host': '127.0.0.1', 'port': 15432, 'user': 'postgres'}

# Use in tests
db = TradingDB()  # Will connect to test instance via env vars

# Cleanup when done
postgresql.stop()
```

**Option 2: Docker PostgreSQL (Recommended for Development)**
Lightweight isolated instance:

```bash
# Start temporary PostgreSQL
docker run --name trading-dev-db \
  -e POSTGRES_PASSWORD=devpassword \
  -e POSTGRES_DB=trading_dev \
  -p 5432:5432 \
  --rm \
  postgres:14-alpine

# Update .env for development
POSTGRES_HOST=localhost
POSTGRES_PORT=5432
POSTGRES_DB=trading_dev
POSTGRES_USER=postgres
POSTGRES_PASSWORD=devpassword
```

**Option 3: SQLite for Simple Testing (Limited Compatibility)**
⚠️ **Warning**: Won't work with PostgreSQL JSON operators (`->`, `->>`)

For simple unit tests only:
```python
# Use SQLite in-memory
# Note: Requires rewriting JSON queries
import sqlite3
conn = sqlite3.connect(':memory:')
```

### 7.2 External APIs
- **Alpaca Trading API**: Order execution and market data
- **PostgreSQL**: Direct database access (under NocoDB)

### 7.3 Scheduling with APScheduler

**Timezone**: US Eastern Time (NYSE trading hours)  
**Trading Hours**: 9:30 AM - 4:00 PM ET

```python
# scheduler.py
from apscheduler.schedulers.blocking import BlockingScheduler
from apscheduler.triggers.cron import CronTrigger
from order_executor import OrderExecutor
from order_monitor import OrderMonitor
from position_monitor import PositionMonitor
import logging
import pytz

logging.basicConfig(level=logging.INFO)

# US Eastern timezone
eastern = pytz.timezone('US/Eastern')
scheduler = BlockingScheduler(timezone=eastern)

# Program 2: Order Executor - Once at 9:45 AM ET
scheduler.add_job(
    lambda: OrderExecutor().run(),
    CronTrigger(hour=9, minute=45, timezone=eastern),
    id='order_executor',
    name='Order Executor (9:45 AM)'
)

# Program 3: Order Monitor - Every 5 minutes during trading hours (9:30 AM - 4:00 PM)
scheduler.add_job(
    lambda: OrderMonitor().run(),
    CronTrigger(
        day_of_week='mon-fri',
        hour='9-15',  # 9 AM to 3:59 PM
        minute='*/5',
        timezone=eastern
    ),
    id='order_monitor_trading',
    name='Order Monitor (every 5 min during trading)'
)

# Program 3: Order Monitor - Once at 6:00 PM ET
scheduler.add_job(
    lambda: OrderMonitor().run(),
    CronTrigger(hour=18, minute=0, timezone=eastern),
    id='order_monitor_eod',
    name='Order Monitor (6:00 PM)'
)

# Program 4: Position Monitor - Every 10 minutes during trading hours (9:30 AM - 4:00 PM)
scheduler.add_job(
    lambda: PositionMonitor().run(),
    CronTrigger(
        day_of_week='mon-fri',
        hour='9-15',  # 9 AM to 3:59 PM
        minute='*/10',
        timezone=eastern
    ),
    id='position_monitor_trading',
    name='Position Monitor (every 10 min during trading)'
)

# Program 4: Position Monitor - Once at 6:15 PM ET
scheduler.add_job(
    lambda: PositionMonitor().run(),
    CronTrigger(hour=18, minute=15, timezone=eastern),
    id='position_monitor_eod',
    name='Position Monitor (6:15 PM)'
)

if __name__ == '__main__':
    print("Starting trading system scheduler...")
    print("Scheduled jobs:")
    for job in scheduler.get_jobs():
        print(f"  - {job.name}: {job.trigger}")
    scheduler.start()
```

### 7.4 Error Handling
- Try-catch blocks in each program
- Basic logging to console and file
- Continue on error, retry next cycle

### 7.5 Configuration

**All configuration via environment variables in `.env` file:**

```bash
# .env file

# PostgreSQL Connection (Production - NocoDB underlying database)
POSTGRES_HOST=localhost
POSTGRES_PORT=5432
POSTGRES_DB=nocodb
POSTGRES_USER=postgres
POSTGRES_PASSWORD=your_password

# PostgreSQL Connection (Testing - Optional, managed by testing.postgresql)
TEST_POSTGRES_HOST=localhost
TEST_POSTGRES_PORT=15432
TEST_POSTGRES_DB=test
TEST_POSTGRES_USER=postgres
TEST_POSTGRES_PASSWORD=

# Alpaca API (Paper Trading)
ALPACA_API_KEY=your_alpaca_paper_key
ALPACA_SECRET_KEY=your_alpaca_paper_secret
ALPACA_PAPER=true

# Trading Schedule (US Eastern Time)
TRADING_START_HOUR=9
TRADING_START_MINUTE=30
TRADING_END_HOUR=16
TRADING_END_MINUTE=0
```

**Loading configuration in Python:**

```python
# config.py
import os
from dotenv import load_dotenv

load_dotenv()

# PostgreSQL Configuration
def get_postgres_config(test_mode=False):
    """Get PostgreSQL configuration based on mode"""
    prefix = 'TEST_' if test_mode else ''
    return {
        'host': os.getenv(f'{prefix}POSTGRES_HOST', 'localhost'),
        'port': os.getenv(f'{prefix}POSTGRES_PORT', '5432'),
        'database': os.getenv(f'{prefix}POSTGRES_DB', 'nocodb'),
        'user': os.getenv(f'{prefix}POSTGRES_USER', 'postgres'),
        'password': os.getenv(f'{prefix}POSTGRES_PASSWORD', '')
    }

# Alpaca Configuration
ALPACA_API_KEY = os.getenv('ALPACA_API_KEY')
ALPACA_SECRET_KEY = os.getenv('ALPACA_SECRET_KEY')
ALPACA_PAPER = os.getenv('ALPACA_PAPER', 'true').lower() == 'true'
```

---

## 8. Testing Strategy

### 8.1 Test Database Setup

**Using testing.postgresql for automated tests:**

```python
# conftest.py (pytest configuration)
import pytest
import testing.postgresql
from db_layer import TradingDB
import os

@pytest.fixture(scope='session')
def postgresql_instance():
    """Create a temporary PostgreSQL instance for all tests"""
    postgresql = testing.postgresql.Postgresql()
    yield postgresql
    postgresql.stop()

@pytest.fixture
def test_db(postgresql_instance):
    """Create database with schema for each test"""
    # Set test environment variables
    dsn = postgresql_instance.dsn()
    os.environ['TEST_POSTGRES_HOST'] = dsn['host']
    os.environ['TEST_POSTGRES_PORT'] = str(dsn['port'])
    os.environ['TEST_POSTGRES_DB'] = dsn['database']
    os.environ['TEST_POSTGRES_USER'] = dsn['user']
    os.environ['TEST_POSTGRES_PASSWORD'] = ''
    
    # Create database connection
    db = TradingDB(test_mode=True)
    
    # Create schema
    db.create_schema()
    
    yield db
    
    # Cleanup
    db.close()
```

### 8.2 Unit Tests with Mock Alpaca API

```python
# test_order_executor.py
import pytest
from unittest.mock import Mock, patch, MagicMock
from order_executor import OrderExecutor
from datetime import datetime

class MockAlpacaOrder:
    def __init__(self, id='order123', status='pending', filled_qty=0):
        self.id = id
        self.status = status
        self.filled_qty = filled_qty
        self.filled_avg_price = 150.0
        self.filled_at = None

@pytest.fixture
def mock_alpaca():
    """Mock Alpaca client"""
    with patch('order_executor.TradingClient') as mock:
        instance = mock.return_value
        instance.submit_order.return_value = MockAlpacaOrder()
        instance.cancel_order_by_id.return_value = None
        yield instance

def test_new_trade_execution(test_db, mock_alpaca):
    """Test NEW_TRADE order placement"""
    # Insert test analysis decision (complete table available in test DB)
    test_db.execute_query("""
        INSERT INTO analysis_decision (
            "Analysis_Id", "Ticker", "Date_time", 
            "Decision", executed, "Approve"
        ) VALUES (
            'TEST_001', 'AAPL', NOW(),
            '{"action": "BUY", "primary_action": "NEW_TRADE", 
              "qty": 10, "entry_price": 150.00, 
              "stop_loss": 145.00, "take_profit": 160.00,
              "trade_style": "SWING", "pattern": "Breakout"}'::jsonb,
            false,
            true
        )
    """)
    
    # Execute order
    with patch('order_executor.TradingDB', return_value=test_db):
        executor = OrderExecutor()
        executor.alpaca = mock_alpaca
        executor.run()
    
    # Verify order was placed
    assert mock_alpaca.submit_order.called
    
    # Verify database updates
    decisions = test_db.query('analysis_decision', 'executed = true')
    assert len(decisions) == 1
    assert decisions[0]['existing_order_id'] == 'order123'
    
    # Verify trade_journal created
    trades = test_db.query('trade_journal')
    assert len(trades) == 1
    assert trades[0]['symbol'] == 'AAPL'
    assert trades[0]['status'] == 'ORDERED'

def test_cancel_order(test_db, mock_alpaca):
    """Test CANCEL action"""
    # Setup existing trade and decision
    # ... test implementation
    pass

def test_order_monitoring(test_db, mock_alpaca):
    """Test order status sync"""
    # Setup order in pending state
    # Mock Alpaca response as filled
    # Verify position_tracking created
    # Verify SL/TP orders placed
    pass

def test_position_update(test_db, mock_alpaca):
    """Test position value updates"""
    # Setup open position
    # Mock price data
    # Verify P&L calculation
    pass

def test_order_executor_no_decisions(test_db, mock_alpaca):
    """Test executor with no pending decisions"""
    with patch('order_executor.TradingDB', return_value=test_db):
        executor = OrderExecutor()
        executor.alpaca = mock_alpaca
        executor.run()
    
    assert not mock_alpaca.submit_order.called

def test_order_executor_invalid_decision(test_db, mock_alpaca):
    """Test executor handles invalid decision gracefully"""
    # Insert malformed decision
    test_db.execute_query("""
        INSERT INTO analysis_decision (
            "Analysis_Id", "Ticker", "Date_time", 
            decision, executed
        ) VALUES (
            'test_002', 'AAPL', NOW(),
            '{}'::jsonb,  -- Empty decision
            false
        )
    """)
    
    with patch('order_executor.TradingDB', return_value=test_db):
        executor = OrderExecutor()
        executor.alpaca = mock_alpaca
        executor.run()
    
    # Should not crash, just log error
    assert not mock_alpaca.submit_order.called
```

### 8.3 Test Scenarios

**Scenario 1: Complete Trade Lifecycle**
1. Analysis decision created (NEW_TRADE)
2. Order executor places entry order
3. Order monitor detects fill
4. Order monitor places SL/TP orders
5. Position monitor updates P&L
6. SL order fills
7. Trade closed with loss

**Scenario 2: Partial Fills**
1. Entry order partially filled
2. Monitor detects partial fill
3. System places SL/TP for filled quantity
4. Remaining order fills later
5. System adjusts SL/TP quantities

**Scenario 3: Order Cancellation**
1. Analysis decision to CANCEL
2. Executor cancels Alpaca order
3. Trade journal marked CANCELLED
4. No position created

**Scenario 4: Market Data Unavailable**
1. Position exists
2. Price data API fails
3. System logs warning
4. Uses last known price
5. Continues operation

**Scenario 5: Position Closed Outside System**
1. Position exists in tracking
2. User manually closes in Alpaca
3. Monitor reconciles discrepancy
4. Updates trade_journal
5. Removes from position_tracking

---

## 9. Deployment

### 9.1 macOS Setup

**Option A: Development with In-Memory PostgreSQL (Recommended for Testing)**

```bash
# Create project directory
mkdir trading_system
cd trading_system

# Create virtual environment
python3 -m venv venv
source venv/bin/activate

# Install dependencies (including testing tools)
pip install alpaca-py psycopg2-binary python-dotenv APScheduler pytz testing.postgresql pytest

# Create .env file (test database managed by testing.postgresql)
cat > .env << EOF
# PostgreSQL Connection (Production - NocoDB)
POSTGRES_HOST=localhost
POSTGRES_PORT=5432
POSTGRES_DB=nocodb
POSTGRES_USER=postgres
POSTGRES_PASSWORD=your_password

# Alpaca API (Paper Trading)
ALPACA_API_KEY=your_alpaca_paper_key
ALPACA_SECRET_KEY=your_alpaca_paper_secret
ALPACA_PAPER=true
EOF

# Run tests (will create in-memory database automatically with ALL tables)
pytest tests/

# Note: testing.postgresql automatically:
# - Creates temporary PostgreSQL instance
# - Runs db.create_schema() which creates ALL tables including analysis_decision
# - Provides clean database for each test
# - Destroys database after tests complete

# For development, initialize test database manually
python -c "
from db_layer import TradingDB
import testing.postgresql

# Start temporary PostgreSQL
postgresql = testing.postgresql.Postgresql()
print(f'Test PostgreSQL running on port {postgresql.dsn()[\"port\"]}')
print('Update your .env TEST_POSTGRES_* variables accordingly')
print('Press Ctrl+C to stop')
try:
    import time
    while True:
        time.sleep(1)
except KeyboardInterrupt:
    postgresql.stop()
"
```

**Option B: Development with Docker PostgreSQL**

```bash
# Start PostgreSQL container
docker run --name trading-dev-db \
  -e POSTGRES_PASSWORD=devpassword \
  -e POSTGRES_DB=trading_dev \
  -p 5432:5432 \
  -d \
  postgres:14-alpine

# Wait for PostgreSQL to be ready
sleep 5

# Create schema
python -c "
from db_layer import TradingDB
import os
os.environ['POSTGRES_HOST'] = 'localhost'
os.environ['POSTGRES_PORT'] = '5432'
os.environ['POSTGRES_DB'] = 'trading_dev'
os.environ['POSTGRES_USER'] = 'postgres'
os.environ['POSTGRES_PASSWORD'] = 'devpassword'

db = TradingDB()
db.create_schema()
print('Schema created successfully')
"

# Update .env
cat > .env << EOF
POSTGRES_HOST=localhost
POSTGRES_PORT=5432
POSTGRES_DB=trading_dev
POSTGRES_USER=postgres
POSTGRES_PASSWORD=devpassword

ALPACA_API_KEY=your_alpaca_paper_key
ALPACA_SECRET_KEY=your_alpaca_paper_secret
ALPACA_PAPER=true
EOF

# Run programs
python order_executor.py  # Test individual program
python scheduler.py        # Run full scheduler

# Stop and remove container when done
docker stop trading-dev-db
docker rm trading-dev-db
```

**Option C: Production with NocoDB PostgreSQL**

```bash
# Standard setup (connects to existing NocoDB database)
mkdir trading_system
cd trading_system
python3 -m venv venv
source venv/bin/activate
pip install alpaca-py psycopg2-binary python-dotenv APScheduler pytz

# Create .env with actual NocoDB credentials
cat > .env << EOF
POSTGRES_HOST=your_nocodb_postgres_host
POSTGRES_PORT=5432
POSTGRES_DB=nocodb
POSTGRES_USER=postgres
POSTGRES_PASSWORD=your_actual_password

ALPACA_API_KEY=your_alpaca_paper_key
ALPACA_SECRET_KEY=your_alpaca_paper_secret
ALPACA_PAPER=true
EOF

# PRODUCTION SETUP - TWO STEPS:

# Step 1: Manually add 4 fields to EXISTING analysis_decision table in NocoDB UI
# Add these columns:
#   - existing_order_id (VARCHAR 255)
#   - existing_trade_journal_id (INT)
#   - executed (BOOLEAN, default false)
#   - execution_time (DATETIME)

# Step 2: Create the NEW tables (trade_journal, order_execution, position_tracking)
python -c "
from db_layer import TradingDB
import psycopg2

# Connect to NocoDB PostgreSQL
db = TradingDB()

# Create only the NEW tables (not analysis_decision, it already exists!)
# NOTE: No foreign key constraints as NocoDB doesn't support them
schema_sql = '''
CREATE TABLE IF NOT EXISTS trade_journal (
    id SERIAL PRIMARY KEY,
    trade_id VARCHAR(50) UNIQUE NOT NULL,
    symbol VARCHAR(50) NOT NULL,
    trade_style VARCHAR(20) NOT NULL,
    pattern VARCHAR(50),
    status VARCHAR(20) NOT NULL DEFAULT ''ORDERED'',
    initial_analysis_id VARCHAR(255),
    planned_entry DECIMAL(10,2) NOT NULL,
    planned_stop_loss DECIMAL(10,2) NOT NULL,
    planned_take_profit DECIMAL(10,2),
    planned_qty INT NOT NULL,
    actual_entry DECIMAL(10,2),
    actual_qty INT,
    current_stop_loss DECIMAL(10,2),
    days_open INT DEFAULT 0,
    last_review_date DATE,
    exit_date DATE,
    exit_price DECIMAL(10,2),
    actual_pnl DECIMAL(10,2),
    exit_reason VARCHAR(100),
    created_at TIMESTAMP DEFAULT NOW(),
    updated_at TIMESTAMP DEFAULT NOW()
);

CREATE TABLE IF NOT EXISTS order_execution (
    id SERIAL PRIMARY KEY,
    trade_journal_id INT NOT NULL,
    analysis_decision_id VARCHAR(255),
    alpaca_order_id VARCHAR(255) NOT NULL,
    client_order_id VARCHAR(255),
    order_type VARCHAR(50) NOT NULL,
    side VARCHAR(10) NOT NULL,
    order_status VARCHAR(20) NOT NULL DEFAULT ''pending'',
    time_in_force VARCHAR(10) NOT NULL,
    qty INT NOT NULL,
    limit_price DECIMAL(10,2),
    stop_price DECIMAL(10,2),
    filled_qty INT,
    filled_avg_price DECIMAL(10,2),
    filled_at TIMESTAMP,
    created_at TIMESTAMP DEFAULT NOW()
);

CREATE TABLE IF NOT EXISTS position_tracking (
    id SERIAL PRIMARY KEY,
    trade_journal_id INT NOT NULL UNIQUE,
    symbol VARCHAR(50) NOT NULL,
    qty INT NOT NULL,
    avg_entry_price DECIMAL(10,2) NOT NULL,
    current_price DECIMAL(10,2) NOT NULL,
    market_value DECIMAL(10,2) NOT NULL,
    cost_basis DECIMAL(10,2) NOT NULL,
    unrealized_pnl DECIMAL(10,2) DEFAULT 0,
    stop_loss_order_id VARCHAR(255),
    take_profit_order_id VARCHAR(255),
    last_updated TIMESTAMP DEFAULT NOW()
);

CREATE INDEX IF NOT EXISTS idx_trade_journal_status ON trade_journal(status);
CREATE INDEX IF NOT EXISTS idx_trade_journal_symbol ON trade_journal(symbol);
CREATE INDEX IF NOT EXISTS idx_trade_journal_analysis_id ON trade_journal(initial_analysis_id);
CREATE INDEX IF NOT EXISTS idx_order_execution_status ON order_execution(order_status);
CREATE INDEX IF NOT EXISTS idx_order_execution_trade_journal ON order_execution(trade_journal_id);
CREATE INDEX IF NOT EXISTS idx_position_tracking_symbol ON position_tracking(symbol);
CREATE INDEX IF NOT EXISTS idx_position_tracking_trade_journal ON position_tracking(trade_journal_id);
'''

with db.conn.cursor() as cursor:
    cursor.execute(schema_sql)
    db.conn.commit()
    print('New tables created successfully')
"

# Run scheduler
python scheduler.py
```

### 9.2 Monitoring
- Check logs in console
- Monitor trade_journal table for new trades
- Monitor position_tracking for open positions
- Verify orders in Alpaca dashboard

---

## 10. Glossary

- **SL**: Stop-Loss order
- **TP**: Take-Profit order
- **P&L**: Profit and Loss
- **FK**: Foreign Key (logical reference only - not enforced by database constraints)
- **DAYTRADE**: Position closed same day
- **SWING**: Position held multiple days
- **NocoDB**: No-code database platform (runs on top of PostgreSQL)
- **Paper Trading**: Simulated trading with fake money (Alpaca sandbox)

---

## 11. Open Questions

1. n8n workflow "Current Position" node:
   - What is the current structure of output?
   - Does it return `pending_order_id` and `trade_journal_id` fields?
   - How are these fields named in the node output?