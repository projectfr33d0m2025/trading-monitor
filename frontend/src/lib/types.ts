/**
 * TypeScript types for Trading Monitor API
 */

export interface AnalysisDecision {
  Analysis_Id: string;
  Date_time?: string;
  Ticker: string;
  Chart?: string;
  Analysis_Prompt?: string;
  "3_Month_Chart"?: string;
  Analysis?: string;
  Trade_Type?: string;
  Decision?: any;
  Approve?: boolean;
  Date?: string;
  Remarks?: string;
  existing_order_id?: string;
  existing_trade_journal_id?: number;
  executed?: boolean;
  execution_time?: string;
}

export interface TradeJournal {
  id: number;
  trade_id: string;
  symbol: string;
  trade_style?: string;
  pattern?: string;
  status: string;
  initial_analysis_id?: string;
  planned_entry?: number;
  planned_stop_loss?: number;
  planned_take_profit?: number;
  planned_qty?: number;
  actual_entry?: number;
  actual_qty?: number;
  current_stop_loss?: number;
  days_open: number;
  last_review_date?: string;
  exit_date?: string;
  exit_price?: number;
  actual_pnl?: number;
  exit_reason?: string;
  created_at?: string;
  updated_at?: string;
}

export interface OrderExecution {
  id: number;
  trade_journal_id: number;
  analysis_decision_id?: string;
  alpaca_order_id: string;
  client_order_id?: string;
  order_type: string;
  side: string;
  order_status: string;
  time_in_force?: string;
  qty: number;
  limit_price?: number;
  stop_price?: number;
  filled_qty?: number;
  filled_avg_price?: number;
  filled_at?: string;
  created_at?: string;
}

export interface PositionTracking {
  id: number;
  trade_journal_id: number;
  symbol: string;
  qty: number;
  avg_entry_price: number;
  current_price: number;
  market_value: number;
  cost_basis: number;
  unrealized_pnl: number;
  stop_loss_order_id?: string;
  take_profit_order_id?: string;
  updated_at?: string; // NocoDB uses updated_at instead of last_updated
}

export interface PaginatedResponse<T> {
  total: number;
  page: number;
  page_size: number;
  data: T[];
}

export type TradeStatus = 'ORDERED' | 'POSITION' | 'CLOSED' | 'CANCELLED';
export type OrderType = 'ENTRY' | 'STOP_LOSS' | 'TAKE_PROFIT';
export type OrderStatus = 'pending' | 'filled' | 'cancelled' | 'partially_filled';
