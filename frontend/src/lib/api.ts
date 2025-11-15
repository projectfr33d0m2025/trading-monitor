/**
 * API Client for Trading Monitor
 * Connects to FastAPI backend
 */

import type {
  AnalysisDecision,
  TradeJournal,
  OrderExecution,
  PositionTracking,
  PaginatedResponse,
} from './types';

// Determine API base URL dynamically
const getApiBaseUrl = (): string => {
  // Use environment variable if provided
  if (import.meta.env.VITE_API_BASE_URL) {
    return import.meta.env.VITE_API_BASE_URL;
  }

  // Otherwise, construct based on current hostname
  // This allows the app to work when accessed from any IP/domain
  const protocol = window.location.protocol;
  const hostname = window.location.hostname;
  return `${protocol}//${hostname}:8085/api`;
};

const API_BASE_URL = getApiBaseUrl();

class ApiClient {
  private async fetchAPI<T>(endpoint: string): Promise<T> {
    const response = await fetch(`${API_BASE_URL}${endpoint}`);

    if (!response.ok) {
      throw new Error(`API Error: ${response.statusText}`);
    }

    return response.json();
  }

  // Analysis Decision endpoints
  async getAnalyses(params?: {
    page?: number;
    page_size?: number;
    ticker?: string;
    executed?: boolean;
    approved?: boolean;
    date?: string;
  }): Promise<PaginatedResponse<AnalysisDecision>> {
    const searchParams = new URLSearchParams();
    if (params?.page) searchParams.set('page', params.page.toString());
    if (params?.page_size) searchParams.set('page_size', params.page_size.toString());
    if (params?.ticker) searchParams.set('ticker', params.ticker);
    if (params?.executed !== undefined) searchParams.set('executed', params.executed.toString());
    if (params?.approved !== undefined) searchParams.set('approved', params.approved.toString());
    if (params?.date) searchParams.set('date', params.date);

    const query = searchParams.toString();
    return this.fetchAPI(`/analysis${query ? `?${query}` : ''}`);
  }

  async getAnalysis(analysisId: string): Promise<AnalysisDecision> {
    return this.fetchAPI(`/analysis/${analysisId}`);
  }

  async getPendingApprovals(params?: {
    page?: number;
    page_size?: number;
  }): Promise<PaginatedResponse<AnalysisDecision>> {
    const searchParams = new URLSearchParams();
    if (params?.page) searchParams.set('page', params.page.toString());
    if (params?.page_size) searchParams.set('page_size', params.page_size.toString());

    const query = searchParams.toString();
    return this.fetchAPI(`/analysis/pending-approvals/list${query ? `?${query}` : ''}`);
  }

  async getAnalysisStats(): Promise<any> {
    return this.fetchAPI('/analysis/stats/summary');
  }

  // Trade Journal endpoints
  async getTrades(params?: {
    page?: number;
    page_size?: number;
    symbol?: string;
    status?: string;
    trade_style?: string;
  }): Promise<PaginatedResponse<TradeJournal>> {
    const searchParams = new URLSearchParams();
    if (params?.page) searchParams.set('page', params.page.toString());
    if (params?.page_size) searchParams.set('page_size', params.page_size.toString());
    if (params?.symbol) searchParams.set('symbol', params.symbol);
    if (params?.status) searchParams.set('status', params.status);
    if (params?.trade_style) searchParams.set('trade_style', params.trade_style);

    const query = searchParams.toString();
    return this.fetchAPI(`/trades${query ? `?${query}` : ''}`);
  }

  async getTrade(tradeId: number): Promise<TradeJournal> {
    return this.fetchAPI(`/trades/${tradeId}`);
  }

  async getActiveTrades(params?: {
    page?: number;
    page_size?: number;
  }): Promise<PaginatedResponse<TradeJournal>> {
    const searchParams = new URLSearchParams();
    if (params?.page) searchParams.set('page', params.page.toString());
    if (params?.page_size) searchParams.set('page_size', params.page_size.toString());

    const query = searchParams.toString();
    return this.fetchAPI(`/trades/active/list${query ? `?${query}` : ''}`);
  }

  async getTradeStats(): Promise<any> {
    return this.fetchAPI('/trades/stats/summary');
  }

  // Order Execution endpoints
  async getOrders(params?: {
    page?: number;
    page_size?: number;
    trade_journal_id?: number;
    order_type?: string;
    order_status?: string;
    side?: string;
  }): Promise<PaginatedResponse<OrderExecution>> {
    const searchParams = new URLSearchParams();
    if (params?.page) searchParams.set('page', params.page.toString());
    if (params?.page_size) searchParams.set('page_size', params.page_size.toString());
    if (params?.trade_journal_id) searchParams.set('trade_journal_id', params.trade_journal_id.toString());
    if (params?.order_type) searchParams.set('order_type', params.order_type);
    if (params?.order_status) searchParams.set('order_status', params.order_status);
    if (params?.side) searchParams.set('side', params.side);

    const query = searchParams.toString();
    return this.fetchAPI(`/orders${query ? `?${query}` : ''}`);
  }

  async getOrder(orderId: number): Promise<OrderExecution> {
    return this.fetchAPI(`/orders/${orderId}`);
  }

  async getOrdersByTrade(tradeId: number, params?: {
    page?: number;
    page_size?: number;
  }): Promise<PaginatedResponse<OrderExecution>> {
    const searchParams = new URLSearchParams();
    if (params?.page) searchParams.set('page', params.page.toString());
    if (params?.page_size) searchParams.set('page_size', params.page_size.toString());

    const query = searchParams.toString();
    return this.fetchAPI(`/orders/trade/${tradeId}/list${query ? `?${query}` : ''}`);
  }

  async getOrderStats(): Promise<any> {
    return this.fetchAPI('/orders/stats/summary');
  }

  // Position Tracking endpoints
  async getPositions(params?: {
    page?: number;
    page_size?: number;
    symbol?: string;
  }): Promise<PaginatedResponse<PositionTracking>> {
    const searchParams = new URLSearchParams();
    if (params?.page) searchParams.set('page', params.page.toString());
    if (params?.page_size) searchParams.set('page_size', params.page_size.toString());
    if (params?.symbol) searchParams.set('symbol', params.symbol);

    const query = searchParams.toString();
    return this.fetchAPI(`/positions${query ? `?${query}` : ''}`);
  }

  async getPosition(positionId: number): Promise<PositionTracking> {
    return this.fetchAPI(`/positions/${positionId}`);
  }

  async getPnLSummary(): Promise<any> {
    return this.fetchAPI('/positions/pnl/summary');
  }
}

export const api = new ApiClient();
