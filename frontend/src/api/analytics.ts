// API client for analytics endpoints

import type {
  EquityCurveResponse,
  PerformanceMetricsResponse,
  PnLByPeriodResponse,
  PatternPerformanceResponse,
  PositionBreakdownResponse,
  StylePerformanceResponse,
  DurationAnalysisResponse,
  DrawdownCurveResponse,
  TradeDistributionResponse,
} from '../types/analytics';

const API_BASE_URL = import.meta.env.VITE_API_URL || 'http://localhost:8085';

interface QueryParams {
  start_date?: string | null;
  end_date?: string | null;
  period?: 'daily' | 'weekly' | 'monthly';
  symbol?: string;
}

/**
 * Builds query string from params object
 */
function buildQueryString(params: QueryParams): string {
  const queryParams = new URLSearchParams();

  Object.entries(params).forEach(([key, value]) => {
    if (value !== null && value !== undefined) {
      queryParams.append(key, String(value));
    }
  });

  const queryString = queryParams.toString();
  return queryString ? `?${queryString}` : '';
}

/**
 * Generic fetch wrapper with error handling
 */
async function fetchAPI<T>(endpoint: string): Promise<T> {
  const response = await fetch(`${API_BASE_URL}${endpoint}`);

  if (!response.ok) {
    throw new Error(`API request failed: ${response.statusText}`);
  }

  return response.json();
}

/**
 * Get equity curve data (cumulative P&L over time)
 */
export async function getEquityCurve(
  startDate?: string | null,
  endDate?: string | null
): Promise<EquityCurveResponse> {
  const queryString = buildQueryString({ start_date: startDate, end_date: endDate });
  return fetchAPI<EquityCurveResponse>(`/api/analytics/equity-curve${queryString}`);
}

/**
 * Get performance metrics (win rate, avg win/loss, profit factor, etc.)
 */
export async function getPerformanceMetrics(
  startDate?: string | null,
  endDate?: string | null
): Promise<PerformanceMetricsResponse> {
  const queryString = buildQueryString({ start_date: startDate, end_date: endDate });
  return fetchAPI<PerformanceMetricsResponse>(`/api/analytics/performance-metrics${queryString}`);
}

/**
 * Get P&L aggregated by period (daily/weekly/monthly)
 */
export async function getPnLByPeriod(
  period: 'daily' | 'weekly' | 'monthly',
  startDate?: string | null,
  endDate?: string | null
): Promise<PnLByPeriodResponse> {
  const queryString = buildQueryString({ period, start_date: startDate, end_date: endDate });
  return fetchAPI<PnLByPeriodResponse>(`/api/analytics/pnl-by-period${queryString}`);
}

/**
 * Get trade performance grouped by pattern
 */
export async function getPatternPerformance(
  startDate?: string | null,
  endDate?: string | null
): Promise<PatternPerformanceResponse> {
  const queryString = buildQueryString({ start_date: startDate, end_date: endDate });
  return fetchAPI<PatternPerformanceResponse>(`/api/analytics/pattern-performance${queryString}`);
}

/**
 * Get current position P&L breakdown by symbol
 */
export async function getPositionBreakdown(): Promise<PositionBreakdownResponse> {
  return fetchAPI<PositionBreakdownResponse>('/api/analytics/position-breakdown');
}

/**
 * Get trade performance grouped by style (SWING vs TREND)
 */
export async function getStylePerformance(
  startDate?: string | null,
  endDate?: string | null
): Promise<StylePerformanceResponse> {
  const queryString = buildQueryString({ start_date: startDate, end_date: endDate });
  return fetchAPI<StylePerformanceResponse>(`/api/analytics/style-performance${queryString}`);
}

/**
 * Get trade duration analysis (days_open vs P&L)
 */
export async function getDurationAnalysis(
  startDate?: string | null,
  endDate?: string | null
): Promise<DurationAnalysisResponse> {
  const queryString = buildQueryString({ start_date: startDate, end_date: endDate });
  return fetchAPI<DurationAnalysisResponse>(`/api/analytics/duration-analysis${queryString}`);
}

/**
 * Get drawdown curve data
 */
export async function getDrawdownCurve(
  startDate?: string | null,
  endDate?: string | null
): Promise<DrawdownCurveResponse> {
  const queryString = buildQueryString({ start_date: startDate, end_date: endDate });
  return fetchAPI<DrawdownCurveResponse>(`/api/analytics/drawdown-curve${queryString}`);
}

/**
 * Get trade distribution by P&L buckets (histogram data)
 */
export async function getTradeDistribution(
  startDate?: string | null,
  endDate?: string | null
): Promise<TradeDistributionResponse> {
  const queryString = buildQueryString({ start_date: startDate, end_date: endDate });
  return fetchAPI<TradeDistributionResponse>(`/api/analytics/trade-distribution${queryString}`);
}
