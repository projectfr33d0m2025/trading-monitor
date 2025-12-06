// Analytics data types for Trading Monitor Dashboard

export interface EquityCurveDataPoint {
  date: string;
  cumulative_pnl: number;
  realized_pnl: number;
  unrealized_pnl: number;
}

export interface PerformanceMetrics {
  total_trades: number;
  winning_trades: number;
  losing_trades: number;
  win_rate: number;
  avg_win: number;
  avg_loss: number;
  profit_factor: number;
  largest_win: number;
  largest_loss: number;
  total_wins: number;
  total_losses: number;
  total_pnl: number;
}

export interface PnLByPeriodDataPoint {
  period: string; // Date string or period label
  realized_pnl: number;
  unrealized_pnl: number;
  total_pnl: number;
}

export interface PatternPerformance {
  pattern: string;
  trade_count: number;
  wins: number;
  win_rate: number;
  avg_pnl: number;
  total_pnl: number;
}

export interface PositionBreakdown {
  symbol: string;
  qty: number;
  avg_entry_price: number;
  current_price: number;
  market_value: number;
  cost_basis: number;
  unrealized_pnl: number;
  unrealized_pnl_pct: number;
}

export interface StylePerformance {
  trade_style: string;
  trade_count: number;
  win_rate: number;
  avg_pnl: number;
  total_pnl: number;
}

export interface DurationAnalysisDataPoint {
  trade_id: string;
  symbol: string;
  days_open: number;
  actual_pnl: number;
  is_winner: boolean;
}

export interface DrawdownCurveDataPoint {
  date: string;
  portfolio_value: number;
  peak_value: number;
  drawdown_pct: number;
}

export interface TradeDistributionBucket {
  bucket_label: string;
  min_pnl: number | null;
  max_pnl: number | null;
  trade_count: number;
}

// API Response types
export interface EquityCurveResponse {
  data: EquityCurveDataPoint[];
}

export interface PerformanceMetricsResponse {
  metrics: PerformanceMetrics;
}

export interface PnLByPeriodResponse {
  data: PnLByPeriodDataPoint[];
}

export interface PatternPerformanceResponse {
  data: PatternPerformance[];
}

export interface PositionBreakdownResponse {
  data: PositionBreakdown[];
}

export interface StylePerformanceResponse {
  data: StylePerformance[];
}

export interface DurationAnalysisResponse {
  data: DurationAnalysisDataPoint[];
}

export interface DrawdownCurveResponse {
  data: DrawdownCurveDataPoint[];
}

export interface TradeDistributionResponse {
  data: TradeDistributionBucket[];
}

// Date range types
export type DateRangePreset = '7d' | '30d' | '90d' | 'ytd' | 'all' | 'custom';

export interface DateRange {
  start_date: string | null; // ISO date string
  end_date: string | null;   // ISO date string
  preset: DateRangePreset;
}

// Chart configuration types
export interface ChartColors {
  positive: string;
  negative: string;
  neutral: string;
  accent: string;
}
