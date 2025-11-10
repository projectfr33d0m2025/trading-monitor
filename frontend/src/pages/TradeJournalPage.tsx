import { useState, useEffect, useRef } from 'react';
import { Link, useSearchParams } from 'react-router-dom';
import { Filter, ChevronDown, ChevronUp, TrendingUp, TrendingDown, Zap, Clock, CheckCircle, XCircle, Package, ShoppingCart, StopCircle, Trophy, FileText } from 'lucide-react';
import { api } from '../lib/api';
import type { TradeJournal, PaginatedResponse, OrderExecution, PositionTracking } from '../lib/types';

interface TradeWithDetails extends TradeJournal {
  orders?: OrderExecution[];
  position?: PositionTracking;
}

export default function TradeJournalPage() {
  const [searchParams] = useSearchParams();
  const [trades, setTrades] = useState<PaginatedResponse<TradeWithDetails> | null>(null);
  const [stats, setStats] = useState<any>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [expandedTrade, setExpandedTrade] = useState<number | null>(null);
  const expandedTradeRef = useRef<HTMLDivElement | null>(null);
  const hasProcessedUrlParam = useRef(false);

  // Filters
  const [filterSymbol, setFilterSymbol] = useState('');
  const [filterStatus, setFilterStatus] = useState<string>('PENDING_ACTIVE');
  const [filterDateRange, setFilterDateRange] = useState<string>('ALL');
  const [showFilters, setShowFilters] = useState(true);

  // Pagination
  const [currentPage, setCurrentPage] = useState(1);
  const pageSize = 20;

  useEffect(() => {
    fetchData();
  }, [currentPage, filterSymbol, filterStatus, filterDateRange]);

  // Auto-expand trade from URL parameter (only once on initial load)
  useEffect(() => {
    const tradeIdParam = searchParams.get('tradeId');

    // Only process if we haven't already processed a URL param
    if (tradeIdParam && trades && !loading && !hasProcessedUrlParam.current) {
      const tradeId = parseInt(tradeIdParam);
      const trade = trades.data.find(t => t.id === tradeId);
      if (trade) {
        // Mark as processed to prevent re-running
        hasProcessedUrlParam.current = true;

        // Auto-expand the trade
        toggleTrade(trade.id, trade.id, trade.status);

        // Scroll to the expanded trade after a short delay to ensure DOM is updated
        setTimeout(() => {
          if (expandedTradeRef.current) {
            expandedTradeRef.current.scrollIntoView({
              behavior: 'smooth',
              block: 'center'
            });
          }
        }, 300);
      }
    }
  }, [searchParams, trades, loading]);

  const fetchData = async () => {
    setLoading(true);
    setError(null);

    try {
      // Build status filter
      let statusParam: string | undefined = undefined;
      if (filterStatus === 'PENDING_ACTIVE') {
        // We'll filter client-side for multiple statuses
        statusParam = undefined;
      } else if (filterStatus !== 'ALL') {
        statusParam = filterStatus;
      }

      const [tradesData, statsData] = await Promise.all([
        api.getTrades({
          page: currentPage,
          page_size: pageSize,
          symbol: filterSymbol || undefined,
          status: statusParam,
        }),
        api.getTradeStats(),
      ]);

      // Apply client-side filtering
      let filteredTrades = tradesData.data;

      // Filter by status for PENDING_ACTIVE
      if (filterStatus === 'PENDING_ACTIVE') {
        filteredTrades = filteredTrades.filter(
          (trade) => trade.status === 'ORDERED' || trade.status === 'POSITION'
        );
      }

      // Filter by date range
      if (filterDateRange !== 'ALL' && tradesData.data.length > 0) {
        const now = new Date();
        const cutoffDate = new Date();

        if (filterDateRange === 'LAST_7_DAYS') {
          cutoffDate.setDate(now.getDate() - 7);
        } else if (filterDateRange === 'LAST_30_DAYS') {
          cutoffDate.setDate(now.getDate() - 30);
        }

        filteredTrades = filteredTrades.filter((trade) => {
          if (!trade.created_at) return true;
          return new Date(trade.created_at) >= cutoffDate;
        });
      }

      setTrades({
        ...tradesData,
        data: filteredTrades,
        total: filteredTrades.length,
      });
      setStats(statsData);
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Failed to fetch trades');
    } finally {
      setLoading(false);
    }
  };

  const toggleTrade = async (tradeId: number, tradeJournalId: number, status: string) => {
    if (expandedTrade === tradeId) {
      setExpandedTrade(null);
    } else {
      setExpandedTrade(tradeId);

      // Find the trade in our state
      const trade = trades?.data.find((t) => t.id === tradeId);
      if (trade && !trade.orders) {
        try {
          // Fetch orders for this trade
          const ordersData = await api.getOrdersByTrade(tradeJournalId);

          // Fetch position data if it's an active position
          let positionData: PositionTracking | undefined = undefined;
          if (status === 'POSITION') {
            try {
              const positionsData = await api.getPositions({ page: 1, page_size: 100 });
              positionData = positionsData.data.find((p) => p.trade_journal_id === tradeJournalId);
            } catch (err) {
              console.error('Failed to fetch position:', err);
            }
          }

          // Update the trade with orders and position data
          setTrades((prev) => {
            if (!prev) return prev;
            return {
              ...prev,
              data: prev.data.map((t) =>
                t.id === tradeId ? { ...t, orders: ordersData.data, position: positionData } : t
              ),
            };
          });
        } catch (err) {
          console.error('Failed to fetch orders:', err);
        }
      }
    }
  };

  const getStatusIcon = (status: string) => {
    switch (status) {
      case 'ORDERED':
        return <Clock className="w-5 h-5" />;
      case 'POSITION':
        return <Package className="w-5 h-5" />;
      case 'CLOSED':
        return <CheckCircle className="w-5 h-5" />;
      case 'CANCELLED':
        return <XCircle className="w-5 h-5" />;
      default:
        return <Package className="w-5 h-5" />;
    }
  };

  const getStatusGradient = (status: string) => {
    switch (status) {
      case 'ORDERED':
        return 'from-blue-500 to-blue-600';
      case 'POSITION':
        return 'from-green-500 to-green-600';
      case 'CLOSED':
        return 'from-gray-500 to-gray-600';
      case 'CANCELLED':
        return 'from-red-500 to-red-600';
      default:
        return 'from-gray-400 to-gray-500';
    }
  };

  const getStatusColor = (status: string) => {
    const colors: Record<string, string> = {
      ORDERED: 'bg-blue-100 text-blue-800 border-blue-200',
      POSITION: 'bg-green-100 text-green-800 border-green-200',
      CLOSED: 'bg-gray-100 text-gray-800 border-gray-200',
      CANCELLED: 'bg-red-100 text-red-800 border-red-200',
    };
    return colors[status] || 'bg-gray-100 text-gray-800 border-gray-200';
  };

  const getTradeStyleIcon = (style?: string) => {
    if (style === 'SWING') return <Zap className="w-4 h-4" />;
    if (style === 'TREND') return <TrendingUp className="w-4 h-4" />;
    return <Package className="w-4 h-4" />;
  };

  const getOrderTypeIcon = (orderType: string) => {
    switch (orderType) {
      case 'ENTRY':
        return <ShoppingCart className="w-4 h-4" />;
      case 'STOP_LOSS':
        return <StopCircle className="w-4 h-4" />;
      case 'TAKE_PROFIT':
        return <Trophy className="w-4 h-4" />;
      default:
        return <Package className="w-4 h-4" />;
    }
  };

  const getOrderTypeBadgeColor = (orderType: string) => {
    switch (orderType) {
      case 'ENTRY':
        return 'bg-blue-100 text-blue-800';
      case 'STOP_LOSS':
        return 'bg-red-100 text-red-800';
      case 'TAKE_PROFIT':
        return 'bg-green-100 text-green-800';
      default:
        return 'bg-gray-100 text-gray-800';
    }
  };

  const formatCurrency = (value?: number | string | null) => {
    if (value === undefined || value === null) return 'N/A';
    const numValue = typeof value === 'string' ? parseFloat(value) : value;
    if (isNaN(numValue)) return 'N/A';
    return `$${numValue.toFixed(2)}`;
  };

  const formatPnL = (pnl?: number) => {
    if (pnl === undefined || pnl === null) return null;
    const isPositive = pnl >= 0;
    return (
      <span className={`inline-flex items-center font-semibold ${isPositive ? 'text-green-600' : 'text-red-600'}`}>
        {isPositive ? <TrendingUp className="w-4 h-4 mr-1" /> : <TrendingDown className="w-4 h-4 mr-1" />}
        {formatCurrency(pnl)}
      </span>
    );
  };

  const formatPercent = (entry: number, current: number) => {
    const change = ((current - entry) / entry) * 100;
    return `${change >= 0 ? '+' : ''}${change.toFixed(2)}%`;
  };

  const statusCounts = stats?.status_breakdown || {};

  return (
    <div className="space-y-4 sm:space-y-6">
      {/* Header */}
      <div className="flex flex-col sm:flex-row sm:items-center sm:justify-between gap-4">
        <div>
          <h1 className="text-2xl font-bold text-gray-900">Trade Journal</h1>
          <p className="mt-1 text-sm text-gray-500">
            Track all your trades from entry to exit with positions and orders
          </p>
        </div>
        <button
          onClick={() => setShowFilters(!showFilters)}
          className="inline-flex items-center justify-center px-4 py-2 border border-gray-300 rounded-md shadow-sm text-sm font-medium text-gray-700 bg-white hover:bg-gray-50"
        >
          <Filter className="w-4 h-4 mr-2" />
          Filters
          {showFilters ? <ChevronUp className="w-4 h-4 ml-2" /> : <ChevronDown className="w-4 h-4 ml-2" />}
        </button>
      </div>

      {/* Summary Cards */}
      {!loading && stats && (
        <div className="grid grid-cols-2 lg:grid-cols-4 gap-4">
          {Object.entries(statusCounts).map(([status, count]: [string, any]) => (
            <div key={status} className={`bg-gradient-to-br ${getStatusGradient(status)} rounded-lg shadow-lg p-6 text-white`}>
              <div className="flex items-center justify-between">
                <div>
                  <p className="text-sm font-medium opacity-90 uppercase">{status === 'ORDERED' ? 'PENDING' : status}</p>
                  <p className="text-3xl font-bold mt-1">{count}</p>
                </div>
                <div className="opacity-30">
                  {getStatusIcon(status)}
                </div>
              </div>
            </div>
          ))}
        </div>
      )}

      {/* Filters */}
      {showFilters && (
        <div className="bg-white p-4 rounded-lg shadow space-y-4">
          <div className="grid grid-cols-1 sm:grid-cols-3 gap-4">
            <div>
              <label className="block text-sm font-medium text-gray-700 mb-1">
                Status
              </label>
              <select
                value={filterStatus}
                onChange={(e) => setFilterStatus(e.target.value)}
                className="w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-blue-500"
              >
                <option value="PENDING_ACTIVE">Pending & Active</option>
                <option value="ORDERED">Pending</option>
                <option value="POSITION">Active</option>
                <option value="CLOSED">Closed</option>
                <option value="CANCELLED">Cancelled</option>
                <option value="ALL">All Statuses</option>
              </select>
            </div>
            <div>
              <label className="block text-sm font-medium text-gray-700 mb-1">
                Symbol
              </label>
              <input
                type="text"
                value={filterSymbol}
                onChange={(e) => setFilterSymbol(e.target.value.toUpperCase())}
                placeholder="Type symbol (e.g., NVDA)"
                className="w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-blue-500"
              />
            </div>
            <div>
              <label className="block text-sm font-medium text-gray-700 mb-1">
                Date Range
              </label>
              <select
                value={filterDateRange}
                onChange={(e) => setFilterDateRange(e.target.value)}
                className="w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-blue-500"
              >
                <option value="ALL">All Time</option>
                <option value="LAST_7_DAYS">Last 7 Days</option>
                <option value="LAST_30_DAYS">Last 30 Days</option>
              </select>
            </div>
          </div>
        </div>
      )}

      {/* Content */}
      {loading && (
        <div className="bg-white rounded-lg shadow p-8 text-center">
          <div className="inline-block animate-spin rounded-full h-8 w-8 border-b-2 border-gray-900"></div>
          <p className="mt-2 text-gray-600">Loading trades...</p>
        </div>
      )}

      {error && (
        <div className="bg-red-50 border border-red-200 rounded-lg p-4">
          <p className="text-sm text-red-800">{error}</p>
        </div>
      )}

      {!loading && !error && trades && (
        <>
          {/* Enhanced Trade Cards */}
          <div className="space-y-4">
            {trades.data.map((trade) => {
              const isExpanded = expandedTrade === trade.id;
              const statusColorClass = getStatusColor(trade.status);
              const orders = trade.orders || [];

              return (
                <div
                  key={trade.id}
                  ref={isExpanded ? expandedTradeRef : null}
                  className={`bg-white rounded-lg shadow-md border-2 ${statusColorClass} overflow-hidden transition-all`}
                >
                  {/* Trade Header */}
                  <div
                    className="p-4 sm:p-6 cursor-pointer hover:bg-gray-50"
                    onClick={() => toggleTrade(trade.id, trade.id, trade.status)}
                  >
                    <div className="flex items-center justify-between">
                      <div className="flex items-center space-x-4">
                        <div className="bg-white rounded-lg p-3 shadow-sm border border-gray-200">
                          {getStatusIcon(trade.status)}
                        </div>
                        <div>
                          <div className="flex items-center space-x-2">
                            <h3 className="text-xl font-bold text-gray-900">{trade.symbol}</h3>
                            {trade.trade_style && (
                              <span className="inline-flex items-center px-2 py-1 rounded-full text-xs font-semibold bg-purple-100 text-purple-800">
                                {getTradeStyleIcon(trade.trade_style)}
                                <span className="ml-1">{trade.trade_style}</span>
                              </span>
                            )}
                          </div>
                          <p className="text-sm text-gray-500">{trade.trade_id}</p>
                        </div>
                      </div>
                      <div className="flex items-center space-x-4">
                        <div className="text-right">
                          <span className={`px-3 py-1 inline-flex items-center text-sm font-semibold rounded-full ${statusColorClass}`}>
                            {getStatusIcon(trade.status)}
                            <span className="ml-1.5">{trade.status === 'ORDERED' ? 'PENDING' : trade.status}</span>
                          </span>
                          {trade.status === 'POSITION' && trade.position && (
                            <div className="mt-2">
                              {formatPnL(trade.position.unrealized_pnl)}
                            </div>
                          )}
                          {trade.status === 'CLOSED' && trade.actual_pnl !== null && trade.actual_pnl !== undefined && (
                            <div className="mt-2">
                              {formatPnL(trade.actual_pnl)}
                            </div>
                          )}
                        </div>
                        {isExpanded ? (
                          <ChevronUp className="w-6 h-6 text-gray-400" />
                        ) : (
                          <ChevronDown className="w-6 h-6 text-gray-400" />
                        )}
                      </div>
                    </div>

                    {/* Trade Summary - Different based on status */}
                    <div className="mt-4 grid grid-cols-2 sm:grid-cols-4 gap-4">
                      {trade.status === 'ORDERED' && (
                        <>
                          <div>
                            <p className="text-xs text-gray-500 uppercase tracking-wide">Planned Entry</p>
                            <p className="text-lg font-semibold text-gray-900">
                              {formatCurrency(trade.planned_entry)}
                            </p>
                          </div>
                          <div>
                            <p className="text-xs text-gray-500 uppercase tracking-wide">Quantity</p>
                            <p className="text-lg font-semibold text-gray-900">
                              {trade.planned_qty || 'N/A'}
                            </p>
                          </div>
                          <div>
                            <p className="text-xs text-gray-500 uppercase tracking-wide">Stop Loss</p>
                            <p className="text-lg font-semibold text-gray-900">
                              {formatCurrency(trade.planned_stop_loss)}
                            </p>
                          </div>
                          <div>
                            <p className="text-xs text-gray-500 uppercase tracking-wide">Pattern</p>
                            <p className="text-lg font-semibold text-gray-900">
                              {trade.pattern || 'N/A'}
                            </p>
                          </div>
                        </>
                      )}

                      {trade.status === 'POSITION' && (
                        <>
                          <div>
                            <p className="text-xs text-gray-500 uppercase tracking-wide">Entry Price</p>
                            <p className="text-lg font-semibold text-gray-900">
                              {formatCurrency(trade.actual_entry || trade.planned_entry)}
                            </p>
                          </div>
                          <div>
                            <p className="text-xs text-gray-500 uppercase tracking-wide">Quantity</p>
                            <p className="text-lg font-semibold text-gray-900">
                              {trade.actual_qty || trade.planned_qty || 'N/A'}
                            </p>
                          </div>
                          <div>
                            <p className="text-xs text-gray-500 uppercase tracking-wide">Days Open</p>
                            <p className="text-lg font-semibold text-gray-900">{trade.days_open}</p>
                          </div>
                          <div>
                            <p className="text-xs text-gray-500 uppercase tracking-wide">Current Price</p>
                            <p className="text-lg font-semibold text-gray-900">
                              {trade.position ? formatCurrency(trade.position.current_price) : 'N/A'}
                            </p>
                          </div>
                        </>
                      )}

                      {(trade.status === 'CLOSED' || trade.status === 'CANCELLED') && (
                        <>
                          <div>
                            <p className="text-xs text-gray-500 uppercase tracking-wide">Entry → Exit</p>
                            <p className="text-lg font-semibold text-gray-900">
                              {formatCurrency(trade.actual_entry)} → {formatCurrency(trade.exit_price)}
                            </p>
                          </div>
                          <div>
                            <p className="text-xs text-gray-500 uppercase tracking-wide">Duration</p>
                            <p className="text-lg font-semibold text-gray-900">{trade.days_open} days</p>
                          </div>
                          <div>
                            <p className="text-xs text-gray-500 uppercase tracking-wide">Final P&L</p>
                            <p className="text-lg font-semibold text-gray-900">
                              {formatPnL(trade.actual_pnl)}
                            </p>
                          </div>
                          <div>
                            <p className="text-xs text-gray-500 uppercase tracking-wide">Exit Reason</p>
                            <p className="text-lg font-semibold text-gray-900">
                              {trade.exit_reason || 'N/A'}
                            </p>
                          </div>
                        </>
                      )}
                    </div>
                  </div>

                  {/* Expandable Details */}
                  {isExpanded && (
                    <div className="border-t border-gray-200 bg-gray-50 p-4 sm:p-6">
                      {/* View Analysis Link */}
                      {trade.initial_analysis_id && (
                        <div className="mb-6">
                          <Link
                            to={`/analysis?analysisId=${trade.initial_analysis_id}`}
                            className="inline-flex items-center px-4 py-2 bg-blue-600 text-white rounded-lg hover:bg-blue-700 transition-colors shadow-sm"
                          >
                            <FileText className="w-4 h-4 mr-2" />
                            View Analysis
                          </Link>
                        </div>
                      )}

                      {/* Position Details for POSITION status */}
                      {trade.status === 'POSITION' && trade.position && (
                        <div className="mb-6">
                          <h4 className="text-sm font-semibold text-gray-700 mb-4 flex items-center">
                            <Package className="w-4 h-4 mr-2" />
                            Position Details
                          </h4>
                          <div className="grid grid-cols-2 sm:grid-cols-4 gap-4 p-4 bg-white rounded-lg">
                            <div className="text-center">
                              <p className="text-xs text-gray-500 mb-1">Avg Entry</p>
                              <p className="text-lg font-semibold text-gray-900">{formatCurrency(trade.position.avg_entry_price)}</p>
                            </div>
                            <div className="text-center">
                              <p className="text-xs text-gray-500 mb-1">Current Price</p>
                              <p className="text-lg font-semibold text-gray-900">{formatCurrency(trade.position.current_price)}</p>
                            </div>
                            <div className="text-center">
                              <p className="text-xs text-gray-500 mb-1">Market Value</p>
                              <p className="text-lg font-semibold text-gray-900">{formatCurrency(trade.position.market_value)}</p>
                            </div>
                            <div className="text-center">
                              <p className="text-xs text-gray-500 mb-1">Unrealized P&L</p>
                              <p className={`text-lg font-semibold ${trade.position.unrealized_pnl >= 0 ? 'text-green-600' : 'text-red-600'}`}>
                                {formatCurrency(trade.position.unrealized_pnl)}
                              </p>
                            </div>
                          </div>
                        </div>
                      )}

                      {/* Order Chain */}
                      <div>
                        <h4 className="text-sm font-semibold text-gray-700 mb-4 flex items-center">
                          <ShoppingCart className="w-4 h-4 mr-2" />
                          {trade.status === 'CLOSED' || trade.status === 'CANCELLED' ? 'Order History' : 'Order Chain'}
                        </h4>

                        {orders.length > 0 ? (
                          <div className="space-y-3">
                            {orders.map((order) => (
                              <div key={order.id} className="bg-white rounded-lg p-4 shadow-sm border-l-4" style={{
                                borderLeftColor: order.order_type === 'ENTRY' ? '#3b82f6' : order.order_type === 'STOP_LOSS' ? '#ef4444' : '#10b981'
                              }}>
                                <div className="flex items-center justify-between mb-2">
                                  <div className="flex items-center space-x-3">
                                    <div className={`p-2 rounded-lg ${getOrderTypeBadgeColor(order.order_type)}`}>
                                      {getOrderTypeIcon(order.order_type)}
                                    </div>
                                    <div>
                                      <div className="flex items-center space-x-2">
                                        <span className={`px-2 py-1 rounded-full text-xs font-semibold ${getOrderTypeBadgeColor(order.order_type)}`}>
                                          {order.order_type.replace('_', ' ')}
                                        </span>
                                        <span className="text-xs uppercase font-medium text-gray-600">{order.side}</span>
                                      </div>
                                    </div>
                                  </div>
                                  <div className="text-right">
                                    <span className={`text-sm font-medium px-2 py-1 rounded ${
                                      order.order_status === 'filled' ? 'bg-green-100 text-green-800' :
                                      order.order_status === 'cancelled' ? 'bg-red-100 text-red-800' :
                                      'bg-yellow-100 text-yellow-800'
                                    }`}>
                                      {order.order_status === 'filled' && <CheckCircle className="w-3 h-3 inline mr-1" />}
                                      {order.order_status.toUpperCase()}
                                    </span>
                                  </div>
                                </div>
                                <div className="grid grid-cols-2 sm:grid-cols-4 gap-2 text-sm text-gray-600">
                                  <div>
                                    <span className="text-gray-500">Qty:</span>{' '}
                                    <span className="font-semibold text-gray-900">{order.qty}</span>
                                  </div>
                                  <div>
                                    <span className="text-gray-500">Price:</span>{' '}
                                    <span className="font-semibold text-gray-900">
                                      {formatCurrency(order.limit_price || order.stop_price)}
                                    </span>
                                  </div>
                                  {order.filled_qty !== null && order.filled_qty > 0 && (
                                    <>
                                      <div>
                                        <span className="text-gray-500">Filled:</span>{' '}
                                        <span className="font-semibold text-gray-900">{order.filled_qty}</span>
                                      </div>
                                      <div>
                                        <span className="text-gray-500">Avg:</span>{' '}
                                        <span className="font-semibold text-gray-900">
                                          {formatCurrency(order.filled_avg_price)}
                                        </span>
                                      </div>
                                    </>
                                  )}
                                </div>
                              </div>
                            ))}
                          </div>
                        ) : (
                          <p className="text-sm text-gray-500 italic">No orders found for this trade</p>
                        )}
                      </div>

                      {/* Additional Trade Details */}
                      {(trade.pattern || trade.created_at || trade.exit_date) && (
                        <div className="mt-6 pt-4 border-t border-gray-200">
                          <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-3 gap-4">
                            {trade.pattern && (
                              <div>
                                <p className="text-sm text-gray-500">Pattern</p>
                                <p className="text-base font-semibold text-gray-900">{trade.pattern}</p>
                              </div>
                            )}
                            {trade.created_at && (
                              <div>
                                <p className="text-sm text-gray-500">Created</p>
                                <p className="text-base font-semibold text-gray-900">
                                  {new Date(trade.created_at).toLocaleDateString()}
                                </p>
                              </div>
                            )}
                            {trade.exit_date && (
                              <div>
                                <p className="text-sm text-gray-500">Exit Date</p>
                                <p className="text-base font-semibold text-gray-900">
                                  {new Date(trade.exit_date).toLocaleDateString()}
                                </p>
                              </div>
                            )}
                          </div>
                        </div>
                      )}
                    </div>
                  )}
                </div>
              );
            })}
          </div>

          {/* Pagination */}
          {trades.total > pageSize && (
            <div className="bg-white px-4 py-3 flex flex-col sm:flex-row items-center justify-between border-t border-gray-200 rounded-lg shadow gap-3">
              <div className="text-sm text-gray-700 text-center sm:text-left">
                Showing <span className="font-medium">{(currentPage - 1) * pageSize + 1}</span> to{' '}
                <span className="font-medium">{Math.min(currentPage * pageSize, trades.total)}</span> of{' '}
                <span className="font-medium">{trades.total}</span> results
              </div>
              <div className="flex gap-2">
                <button
                  onClick={() => setCurrentPage(p => Math.max(1, p - 1))}
                  disabled={currentPage === 1}
                  className="px-3 py-1.5 border border-gray-300 rounded-md text-sm font-medium text-gray-700 bg-white hover:bg-gray-50 disabled:opacity-50"
                >
                  Previous
                </button>
                <span className="px-3 py-1.5 border border-gray-300 rounded-md text-sm font-medium text-gray-700 bg-white">
                  Page {currentPage}
                </span>
                <button
                  onClick={() => setCurrentPage(p => p + 1)}
                  disabled={currentPage * pageSize >= trades.total}
                  className="px-3 py-1.5 border border-gray-300 rounded-md text-sm font-medium text-gray-700 bg-white hover:bg-gray-50 disabled:opacity-50"
                >
                  Next
                </button>
              </div>
            </div>
          )}
        </>
      )}
    </div>
  );
}
