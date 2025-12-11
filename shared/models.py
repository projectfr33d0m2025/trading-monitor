"""
Pydantic Models for API Responses
Data models for the four main tables used by both trading scripts and API
"""
from pydantic import BaseModel, Field
from typing import Optional, Dict, Any
from datetime import datetime, date
from decimal import Decimal


class AnalysisDecision(BaseModel):
    """Analysis Decision from n8n workflow"""
    Analysis_Id: Optional[str] = None
    Date_time: Optional[datetime] = None
    Ticker: Optional[str] = None
    Chart: Optional[str] = None
    Analysis_Prompt: Optional[str] = None
    three_Month_Chart: Optional[str] = Field(None, alias="3_Month_Chart")
    Analysis: Optional[str] = None
    Trade_Type: Optional[str] = None
    Decision: Optional[Dict[str, Any]] = None
    Approve: Optional[bool] = False
    Date: Optional[date] = None
    Remarks: Optional[str] = None
    existing_order_id: Optional[str] = None
    existing_trade_journal_id: Optional[int] = None
    executed: Optional[bool] = False
    execution_time: Optional[datetime] = None

    class Config:
        from_attributes = True
        populate_by_name = True


class TradeJournal(BaseModel):
    """Trade Journal entry tracking complete trade lifecycle"""
    id: int
    trade_id: str
    symbol: str
    trade_style: Optional[str] = None
    pattern: Optional[str] = None
    status: str = "ORDERED"
    initial_analysis_id: Optional[str] = None
    planned_entry: Optional[Decimal] = None
    planned_stop_loss: Optional[Decimal] = None
    planned_take_profit: Optional[Decimal] = None
    planned_qty: Optional[int] = None
    actual_entry: Optional[Decimal] = None
    actual_qty: Optional[int] = None
    current_stop_loss: Optional[Decimal] = None
    days_open: Optional[int] = 0
    last_review_date: Optional[date] = None
    exit_date: Optional[date] = None
    exit_price: Optional[Decimal] = None
    actual_pnl: Optional[Decimal] = None
    exit_reason: Optional[str] = None
    created_at: Optional[datetime] = None
    updated_at: Optional[datetime] = None

    class Config:
        from_attributes = True


class OrderExecution(BaseModel):
    """Order execution tracking (entry, SL, TP orders)"""
    id: int
    trade_journal_id: int
    analysis_decision_id: Optional[str] = None
    alpaca_order_id: str
    client_order_id: Optional[str] = None
    order_type: str
    side: str
    order_status: str = "pending"
    time_in_force: Optional[str] = None
    qty: int
    limit_price: Optional[Decimal] = None
    stop_price: Optional[Decimal] = None
    filled_qty: Optional[int] = None
    filled_avg_price: Optional[Decimal] = None
    filled_at: Optional[datetime] = None
    created_at: Optional[datetime] = None

    class Config:
        from_attributes = True


class PositionTracking(BaseModel):
    """Position tracking with real-time P&L"""
    id: int
    trade_journal_id: int
    symbol: str
    qty: int
    avg_entry_price: Decimal
    current_price: Decimal
    market_value: Decimal
    cost_basis: Decimal
    unrealized_pnl: Decimal = Decimal('0')
    stop_loss_order_id: Optional[str] = None
    take_profit_order_id: Optional[str] = None
    updated_at: Optional[datetime] = None  # NocoDB uses updated_at instead of last_updated

    class Config:
        from_attributes = True


# Response models for API with pagination
class PaginatedResponse(BaseModel):
    """Paginated response wrapper"""
    total: int
    page: int
    page_size: int
    data: list


class AnalysisListResponse(PaginatedResponse):
    """Paginated list of analysis decisions"""
    data: list[AnalysisDecision]


class TradeListResponse(PaginatedResponse):
    """Paginated list of trades"""
    data: list[TradeJournal]


class OrderListResponse(PaginatedResponse):
    """Paginated list of orders"""
    data: list[OrderExecution]


class PositionListResponse(PaginatedResponse):
    """Paginated list of positions"""
    data: list[PositionTracking]


class TickerWatchlist(BaseModel):
    """Ticker watchlist entry"""
    id: int
    Ticker: str
    Ticker_Name: Optional[str] = None
    Exchange: Optional[str] = None
    Industry: Optional[str] = None
    Active: bool = True
    created_at: Optional[datetime] = None
    updated_at: Optional[datetime] = None

    class Config:
        from_attributes = True


class CreateTickerWatchlist(BaseModel):
    """Create ticker watchlist entry"""
    Ticker: str
    Ticker_Name: str  # Required - comes from Alpaca
    Exchange: str  # Required - comes from Alpaca
    Industry: Optional[str] = None
    Active: bool = True


class UpdateTickerWatchlist(BaseModel):
    """Update ticker watchlist entry"""
    # Ticker and Exchange cannot be updated (locked to Alpaca data)
    Industry: Optional[str] = None
    Active: Optional[bool] = None


class WatchlistListResponse(PaginatedResponse):
    """Paginated list of watchlist tickers"""
    data: list[TickerWatchlist]


class AlpacaAsset(BaseModel):
    """Alpaca asset for ticker search"""
    symbol: str
    name: str
    exchange: str
    asset_class: str
    tradable: bool
