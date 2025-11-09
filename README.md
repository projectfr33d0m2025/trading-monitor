# Trading Monitor with UI Dashboard

A comprehensive trading system with automated execution and a modern web-based dashboard for monitoring trades, positions, and analysis decisions.

## 📁 Project Structure

```
trading-monitor/
├── trading/              # Trading automation scripts
│   ├── order_executor.py       # Executes approved trades
│   ├── order_monitor.py        # Monitors order status
│   ├── position_monitor.py     # Tracks position P&L
│   ├── scheduler.py            # Runs scripts on schedule
│   └── docs/                   # Trading system documentation
│
├── shared/               # Shared utilities
│   ├── database.py             # Database connection
│   ├── config.py               # Configuration
│   └── models.py               # Pydantic data models
│
├── api/                  # FastAPI Backend
│   ├── main.py                 # FastAPI application
│   ├── routers/                # API endpoints
│   │   ├── analysis.py         # Analysis decisions
│   │   ├── trades.py           # Trade journal
│   │   ├── orders.py           # Order execution
│   │   └── positions.py        # Position tracking
│   └── requirements.txt        # Python dependencies
│
├── frontend/             # React Dashboard
│   ├── src/
│   │   ├── pages/              # Page components
│   │   │   ├── DashboardPage.tsx
│   │   │   ├── AnalysisPage.tsx
│   │   │   ├── TradeJournalPage.tsx
│   │   │   ├── OrdersPage.tsx
│   │   │   └── PositionsPage.tsx
│   │   ├── lib/                # Utilities
│   │   │   ├── api.ts          # API client
│   │   │   └── types.ts        # TypeScript types
│   │   └── App.tsx             # Main app component
│   └── package.json            # Node dependencies
│
├── docker-compose.yml    # Docker orchestration
└── .env                  # Environment variables
```

## 🚀 Quick Start

### Option 1: Docker Compose (Recommended)

1. **Prerequisites**
   - Docker and Docker Compose installed
   - PostgreSQL database running (or use existing NocoDB setup)

2. **Start all services**
   ```bash
   docker-compose up
   ```

3. **Access the dashboard**
   - Frontend: http://localhost:3000
   - API: http://localhost:8000
   - API Docs: http://localhost:8000/docs

### Option 2: Manual Setup

#### Backend API

1. **Install Python dependencies**
   ```bash
   cd api
   pip install -r requirements.txt
   ```

2. **Configure environment**
   ```bash
   # Copy .env.example to .env and update with your settings
   cp .env.example .env
   ```

3. **Run the API**
   ```bash
   # From project root
   cd api
   uvicorn main:app --reload
   ```

   API will be available at http://localhost:8000

#### Frontend Dashboard

1. **Install Node dependencies**
   ```bash
   cd frontend
   npm install
   ```

2. **Run the development server**
   ```bash
   npm run dev
   ```

   Dashboard will be available at http://localhost:5173

#### Trading Scripts

1. **Install Python dependencies**
   ```bash
   cd trading
   pip install -r requirements.txt
   ```

2. **Run individual scripts**
   ```bash
   # From trading directory
   python order_executor.py
   python order_monitor.py
   python position_monitor.py
   ```

3. **Run scheduled automation**
   ```bash
   python scheduler.py
   ```

## 🎯 Features

### Dashboard Features

- **📊 Overview Dashboard**
  - Real-time statistics
  - Pending analyses count
  - Active trades count
  - Unrealized P&L summary
  - Recent active trades

- **📈 Analysis Page**
  - View AI-generated trading analysis with gradient summary cards
  - Status breakdown (Pending, Approved, Executed)
  - Filter by ticker, execution status, approval status
  - Progressive disclosure with expandable cards
  - Full analysis text, decision JSON, and chart visualization
  - Icon-first design with status indicators
  - Responsive mobile/desktop views

- **📋 Trade Journal**
  - Complete trade lifecycle tracking
  - Gradient summary cards showing status breakdown
  - Filter by symbol, status, trade style
  - P&L tracking with color-coded indicators
  - Days open counter
  - Progressive disclosure with expandable trade details
  - Trade style badges (Swing, Trend)
  - Icon-first design with status icons
  - Responsive mobile/desktop views

- **🛒 Order Execution**
  - Monitor all order types with gradient summary cards
  - Order type breakdown (Entry, Stop Loss, Take Profit)
  - Order status breakdown (Pending, Filled, Cancelled)
  - Filter by order type and status
  - Progressive disclosure with expandable order details
  - Fill price tracking with detailed timestamps
  - Icon-first design (ShoppingCart, StopCircle, Trophy)
  - Responsive mobile/desktop views

- **💰 Position Tracking**
  - Real-time position values with gradient summary cards
  - Unrealized P&L calculation with color-coded indicators
  - Market value and cost basis tracking
  - Progressive disclosure with related orders
  - Lazy loading of order details on expand
  - Icon-first design with status indicators
  - Responsive mobile/desktop views

### API Endpoints

#### Analysis Decisions
- `GET /api/analysis` - List all analyses (with pagination & filters)
- `GET /api/analysis/{id}` - Get single analysis
- `GET /api/analysis/pending-approvals/list` - Get pending approvals
- `GET /api/analysis/stats/summary` - Get analysis statistics (status & type breakdown)

#### Trade Journal
- `GET /api/trades` - List all trades (with pagination & filters)
- `GET /api/trades/{id}` - Get single trade
- `GET /api/trades/active/list` - Get active trades
- `GET /api/trades/stats/summary` - Get trade statistics (status breakdown & P&L)

#### Order Execution
- `GET /api/orders` - List all orders (with pagination & filters)
- `GET /api/orders/{id}` - Get single order
- `GET /api/orders/trade/{trade_id}/list` - Get orders for a trade
- `GET /api/orders/stats/summary` - Get order statistics (type & status breakdown)

#### Position Tracking
- `GET /api/positions` - List all positions (with pagination & filters)
- `GET /api/positions/{id}` - Get single position
- `GET /api/positions/pnl/summary` - Get P&L summary with aggregations

## 🔧 Configuration

### Environment Variables

Create a `.env` file in the project root:

```env
# PostgreSQL Configuration
POSTGRES_HOST=localhost
POSTGRES_PORT=5432
POSTGRES_DB=nocodb
POSTGRES_USER=postgres
POSTGRES_PASSWORD=your_password
POSTGRES_SCHEMA=public

# Alpaca API Configuration
ALPACA_API_KEY=your_api_key
ALPACA_SECRET_KEY=your_secret_key
ALPACA_PAPER=true

# Trading Schedule (US Eastern Time)
TRADING_START_HOUR=9
TRADING_START_MINUTE=30
TRADING_END_HOUR=16
TRADING_END_MINUTE=0
```

## 📱 Responsive Design

The dashboard is fully responsive and optimized for:
- **Desktop** (1024px and above) - Full table views
- **Tablet** (768px - 1023px) - Optimized layouts
- **Mobile** (below 768px) - Card-based views

## 🛠️ Development

### Tech Stack

**Backend:**
- FastAPI - Modern Python web framework
- Pydantic - Data validation
- psycopg2 - PostgreSQL adapter
- Uvicorn - ASGI server

**Frontend:**
- React 18 - UI library
- TypeScript - Type safety
- Vite - Build tool
- Tailwind CSS - Styling
- React Router - Navigation
- Lucide React - Icons

**Trading Automation:**
- Alpaca API - Trading execution
- APScheduler - Task scheduling
- Python 3.9+ - Core language

### API Documentation

Once the API is running, visit http://localhost:8000/docs for interactive API documentation powered by Swagger UI.

## 📊 Database Schema

The system uses 4 main tables:

1. **analysis_decision** - AI-generated trading analysis
2. **trade_journal** - Complete trade lifecycle tracking
3. **order_execution** - Order execution records
4. **position_tracking** - Real-time position monitoring

See `/trading/docs/` for detailed schema documentation.

## 🔐 Security

- No authentication required (local access only)
- CORS enabled for localhost development
- Environment variables for sensitive data
- Database connection pooling

## 📝 License

[Your License Here]

## 🤝 Contributing

1. Create a new branch (`git checkout -b feature/amazing-feature`)
2. Make your changes
3. Commit your changes (`git commit -m 'Add amazing feature'`)
4. Push to the branch (`git push origin feature/amazing-feature`)
5. Open a Pull Request

## 📞 Support

For issues and questions, please open an issue on GitHub.

---

**Built with ❤️ for automated trading**
