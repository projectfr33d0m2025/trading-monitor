# Alpaca API Response Samples

This directory contains sample JSON responses from the Alpaca Paper Trading API.

## API Endpoints & Corresponding Files:

### 1. **1_order_submission_market.json**
- **API Method**: `trading_client.submit_order(MarketOrderRequest(...))`
- **REST Endpoint**: `POST /v2/orders`
- **Description**: Response when submitting a market order (entry order)
- **Python Code**:
```python
trading_client.submit_order(
    MarketOrderRequest(
        symbol="AAPL",
        qty=1,
        side=OrderSide.BUY,
        time_in_force=TimeInForce.DAY
    )
)
```

### 2. **2_order_status_filled.json**
- **API Method**: `trading_client.get_order_by_id(order_id)`
- **REST Endpoint**: `GET /v2/orders/{order_id}`
- **Description**: Order status after it's been filled
- **Python Code**:
```python
trading_client.get_order_by_id(order_id)
```

### 3. **3_get_all_orders.json**
- **API Method**: `trading_client.get_orders()`
- **REST Endpoint**: `GET /v2/orders`
- **Description**: Response when getting list of all orders
- **Python Code**:
```python
trading_client.get_orders()
```

### 4. **4_get_order_by_id.json**
- **API Method**: `trading_client.get_order_by_id(order_id)`
- **REST Endpoint**: `GET /v2/orders/{order_id}`
- **Description**: Response when getting a specific order by ID
- **Python Code**:
```python
trading_client.get_order_by_id(order_id)
```

### 5. **5_get_all_positions.json**
- **API Method**: `trading_client.get_all_positions()`
- **REST Endpoint**: `GET /v2/positions`
- **Description**: Response when getting all open positions
- **Python Code**:
```python
trading_client.get_all_positions()
```

### 6. **6_get_single_position.json**
- **API Method**: `trading_client.get_open_position(symbol)`
- **REST Endpoint**: `GET /v2/positions/{symbol}`
- **Description**: Response when getting a specific position by symbol
- **Python Code**:
```python
trading_client.get_open_position("AAPL")
```

### 7. **7_stop_loss_order_submission.json**
- **API Method**: `trading_client.submit_order(StopOrderRequest(...))`
- **REST Endpoint**: `POST /v2/orders`
- **Description**: Response when submitting a stop-loss order
- **Python Code**:
```python
trading_client.submit_order(
    StopOrderRequest(
        symbol="AAPL",
        qty=1,
        side=OrderSide.SELL,
        time_in_force=TimeInForce.GTC,
        stop_price=118.89
    )
)
```

### 8. **8_bracket_order_submission.json**
- **API Method**: `trading_client.submit_order(MarketOrderRequest(..., order_class=OrderClass.BRACKET))`
- **REST Endpoint**: `POST /v2/orders`
- **Description**: Response when submitting a bracket order (entry + SL + TP)
- **Python Code**:
```python
trading_client.submit_order(
    MarketOrderRequest(
        symbol="MSFT",
        qty=1,
        side=OrderSide.BUY,
        time_in_force=TimeInForce.DAY,
        order_class=OrderClass.BRACKET,
        take_profit=TakeProfitRequest(limit_price=500),
        stop_loss=StopLossRequest(stop_price=400)
    )
)
```

### 9. **9_order_cancellation.json**
- **API Method**: `trading_client.cancel_order_by_id(order_id)`
- **REST Endpoint**: `DELETE /v2/orders/{order_id}`
- **Description**: Response after canceling an order
- **Python Code**:
```python
trading_client.cancel_order_by_id(order_id)
# Then get order to see canceled status
trading_client.get_order_by_id(order_id)
```

### 10. **10_close_position.json**
- **API Method**: `trading_client.close_position(symbol)`
- **REST Endpoint**: `DELETE /v2/positions/{symbol}`
- **Description**: Response when closing a position (creates a market sell order)
- **Python Code**:
```python
trading_client.close_position("AAPL")
```

### 11. **11_account_info.json**
- **API Method**: `trading_client.get_account()`
- **REST Endpoint**: `GET /v2/account`
- **Description**: Response when getting account information
- **Python Code**:
```python
trading_client.get_account()
```

### 12. **12_empty_positions.json**
- **API Method**: `trading_client.get_all_positions()`
- **REST Endpoint**: `GET /v2/positions`
- **Description**: Response when there are no open positions (empty array)
- **Python Code**:
```python
trading_client.get_all_positions()  # Returns []
```

---

## Important Fields for Order Responses:

- **id** - Alpaca's order ID (alpaca_order_id)
- **client_order_id** - Your custom order ID
- **status** - Order status (new, accepted, filled, partially_filled, canceled, rejected)
- **filled_qty** - Number of shares filled
- **filled_avg_price** - Average fill price
- **filled_at** - Timestamp when filled
- **symbol** - Stock symbol
- **qty** - Order quantity
- **side** - buy/sell
- **order_type** - market, limit, stop, stop_limit
- **time_in_force** - day, gtc, ioc, fok
- **stop_price** - For stop orders
- **limit_price** - For limit orders
- **legs** - Array of child orders (for bracket orders)

## Important Fields for Position Responses:

- **symbol** - Stock symbol
- **qty** - Position quantity
- **avg_entry_price** - Average entry price
- **current_price** - Current market price
- **market_value** - Current market value
- **cost_basis** - Total cost basis
- **unrealized_pl** - Unrealized profit/loss (dollar amount)
- **unrealized_plpc** - Unrealized profit/loss (percentage)
- **side** - long/short

## Important Fields for Account Response:

- **buying_power** - Available buying power
- **cash** - Cash balance
- **equity** - Account equity
- **portfolio_value** - Total portfolio value
- **status** - Account status
- **daytrading_buying_power** - Available buying power for day trading
- **pattern_day_trader** - Whether account is flagged as PDT

---

## Usage:

These sample responses can be used for:
1. Testing your order management system
2. Developing parsers for Alpaca API responses
3. Understanding the structure of different API endpoints
4. Mocking API responses in development environments
5. Building unit tests without hitting the actual API

## Python SDK Installation:

```bash
pip install alpaca-py python-dotenv
```

## Authentication Setup:

```python
from alpaca.trading.client import TradingClient
import os
from dotenv import load_dotenv

load_dotenv()

API_KEY = os.getenv('ALPACA_API_KEY')
SECRET_KEY = os.getenv('ALPACA_SECRET_KEY')

# Paper trading
trading_client = TradingClient(API_KEY, SECRET_KEY, paper=True)

# Live trading
# trading_client = TradingClient(API_KEY, SECRET_KEY, paper=False)
```

## References:

- **Alpaca Python SDK**: https://github.com/alpacahq/alpaca-py
- **API Documentation**: https://docs.alpaca.markets/
- **Trading API Reference**: https://docs.alpaca.markets/reference/postorder

---

## Note:

All timestamps, IDs, and values in these samples are examples. 
Actual API responses will contain real-time data specific to your account and orders.

Generated: 2025-10-25
