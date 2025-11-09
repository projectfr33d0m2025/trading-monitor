import { useState, useEffect } from 'react';
import { Filter, ChevronDown, ChevronUp, TrendingUp, TrendingDown, Zap, FileText, XCircle, Clock, CheckCircle, Package } from 'lucide-react';
import { api } from '../lib/api';
import type { TradeJournal, PaginatedResponse } from '../lib/types';

export default function TradeJournalPage() {
  const [trades, setTrades] = useState<PaginatedResponse<TradeJournal> | null>(null);
  const [stats, setStats] = useState<any>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [expandedTrade, setExpandedTrade] = useState<number | null>(null);

  // Filters
  const [filterSymbol, setFilterSymbol] = useState('');
  const [filterStatus, setFilterStatus] = useState<string>('');
  const [showFilters, setShowFilters] = useState(true);

  // Pagination
  const [currentPage, setCurrentPage] = useState(1);
  const pageSize = 20;

  useEffect(() => {
    fetchData();
  }, [currentPage, filterSymbol, filterStatus]);

  const fetchData = async () => {
    setLoading(true);
    setError(null);

    try {
      const [tradesData, statsData] = await Promise.all([
        api.getTrades({
          page: currentPage,
          page_size: pageSize,
          symbol: filterSymbol || undefined,
          status: filterStatus || undefined,
        }),
        api.getTradeStats(),
      ]);
      setTrades(tradesData);
      setStats(statsData);
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Failed to fetch trades');
    } finally {
      setLoading(false);
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
        return <FileText className="w-5 h-5" />;
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

  const formatCurrency = (value?: number) => {
    if (value === undefined || value === null) return 'N/A';
    return `$${value.toFixed(2)}`;
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

  const statusCounts = stats?.status_breakdown || {};

  return (
    <div className="space-y-4 sm:space-y-6">
      {/* Header */}
      <div className="flex flex-col sm:flex-row sm:items-center sm:justify-between gap-4">
        <div>
          <h1 className="text-2xl font-bold text-gray-900">Trade Journal</h1>
          <p className="mt-1 text-sm text-gray-500">
            Track all your trades from entry to exit
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
                  <p className="text-sm font-medium opacity-90 uppercase">{status}</p>
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
          <div className="grid grid-cols-1 sm:grid-cols-2 gap-4">
            <div>
              <label className="block text-sm font-medium text-gray-700 mb-1">
                Symbol
              </label>
              <input
                type="text"
                value={filterSymbol}
                onChange={(e) => setFilterSymbol(e.target.value.toUpperCase())}
                placeholder="e.g., NVDA"
                className="w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-blue-500"
              />
            </div>
            <div>
              <label className="block text-sm font-medium text-gray-700 mb-1">
                Status
              </label>
              <select
                value={filterStatus}
                onChange={(e) => setFilterStatus(e.target.value)}
                className="w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-blue-500"
              >
                <option value="">All Statuses</option>
                <option value="ORDERED">Ordered</option>
                <option value="POSITION">Position</option>
                <option value="CLOSED">Closed</option>
                <option value="CANCELLED">Cancelled</option>
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

              return (
                <div key={trade.id} className={`bg-white rounded-lg shadow-md border-2 ${statusColorClass} overflow-hidden transition-all`}>
                  {/* Trade Header */}
                  <div
                    className="p-4 sm:p-6 cursor-pointer hover:bg-gray-50"
                    onClick={() => setExpandedTrade(isExpanded ? null : trade.id)}
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
                            <span className="ml-1.5">{trade.status}</span>
                          </span>
                          {trade.actual_pnl !== null && trade.actual_pnl !== undefined && (
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

                    {/* Trade Summary */}
                    <div className="mt-4 grid grid-cols-2 sm:grid-cols-4 gap-4">
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
                        <p className="text-xs text-gray-500 uppercase tracking-wide">Stop Loss</p>
                        <p className="text-lg font-semibold text-gray-900">
                          {formatCurrency(trade.current_stop_loss || trade.planned_stop_loss)}
                        </p>
                      </div>
                    </div>
                  </div>

                  {/* Expandable Details */}
                  {isExpanded && (
                    <div className="border-t border-gray-200 bg-gray-50 p-4 sm:p-6">
                      <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-3 gap-4">
                        {trade.planned_take_profit && (
                          <div>
                            <p className="text-sm text-gray-500">Take Profit Target</p>
                            <p className="text-base font-semibold text-gray-900">
                              {formatCurrency(trade.planned_take_profit)}
                            </p>
                          </div>
                        )}
                        {trade.exit_price && (
                          <div>
                            <p className="text-sm text-gray-500">Exit Price</p>
                            <p className="text-base font-semibold text-gray-900">
                              {formatCurrency(trade.exit_price)}
                            </p>
                          </div>
                        )}
                        {trade.exit_reason && (
                          <div>
                            <p className="text-sm text-gray-500">Exit Reason</p>
                            <p className="text-base font-semibold text-gray-900">{trade.exit_reason}</p>
                          </div>
                        )}
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
              );
            })}
          </div>

          {/* Pagination */}
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
        </>
      )}
    </div>
  );
}
