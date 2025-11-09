import { useState, useEffect } from 'react';
import { Filter, ChevronDown, ChevronUp, TrendingUp, TrendingDown } from 'lucide-react';
import { api } from '../lib/api';
import type { TradeJournal, PaginatedResponse } from '../lib/types';

export default function TradeJournalPage() {
  const [trades, setTrades] = useState<PaginatedResponse<TradeJournal> | null>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  // Filters
  const [filterSymbol, setFilterSymbol] = useState('');
  const [filterStatus, setFilterStatus] = useState<string>('');
  const [showFilters, setShowFilters] = useState(true);

  // Pagination
  const [currentPage, setCurrentPage] = useState(1);
  const pageSize = 20;

  useEffect(() => {
    fetchTrades();
  }, [currentPage, filterSymbol, filterStatus]);

  const fetchTrades = async () => {
    setLoading(true);
    setError(null);

    try {
      const data = await api.getTrades({
        page: currentPage,
        page_size: pageSize,
        symbol: filterSymbol || undefined,
        status: filterStatus || undefined,
      });
      setTrades(data);
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Failed to fetch trades');
    } finally {
      setLoading(false);
    }
  };

  const getStatusColor = (status: string) => {
    const colors: Record<string, string> = {
      ORDERED: 'bg-blue-100 text-blue-800',
      POSITION: 'bg-green-100 text-green-800',
      CLOSED: 'bg-gray-100 text-gray-800',
      CANCELLED: 'bg-red-100 text-red-800',
    };
    return colors[status] || 'bg-gray-100 text-gray-800';
  };

  const formatCurrency = (value?: number) => {
    if (value === undefined || value === null) return 'N/A';
    return `$${value.toFixed(2)}`;
  };

  const formatPnL = (pnl?: number) => {
    if (pnl === undefined || pnl === null) return null;
    const isPositive = pnl >= 0;
    return (
      <span className={`inline-flex items-center ${isPositive ? 'text-green-600' : 'text-red-600'}`}>
        {isPositive ? <TrendingUp className="w-4 h-4 mr-1" /> : <TrendingDown className="w-4 h-4 mr-1" />}
        {formatCurrency(pnl)}
      </span>
    );
  };

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
          {/* Desktop Table */}
          <div className="hidden md:block bg-white shadow rounded-lg overflow-hidden">
            <div className="overflow-x-auto">
              <table className="min-w-full divide-y divide-gray-200">
                <thead className="bg-gray-50">
                  <tr>
                    <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                      Trade ID
                    </th>
                    <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                      Symbol
                    </th>
                    <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                      Status
                    </th>
                    <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                      Entry
                    </th>
                    <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                      Qty
                    </th>
                    <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                      Days Open
                    </th>
                    <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                      P&L
                    </th>
                  </tr>
                </thead>
                <tbody className="bg-white divide-y divide-gray-200">
                  {trades.data.map((trade) => (
                    <tr key={trade.id} className="hover:bg-gray-50">
                      <td className="px-6 py-4 whitespace-nowrap text-sm font-medium text-gray-900">
                        {trade.trade_id}
                      </td>
                      <td className="px-6 py-4 whitespace-nowrap text-sm text-gray-900">
                        {trade.symbol}
                      </td>
                      <td className="px-6 py-4 whitespace-nowrap">
                        <span className={`px-2 py-1 inline-flex text-xs leading-5 font-semibold rounded-full ${getStatusColor(trade.status)}`}>
                          {trade.status}
                        </span>
                      </td>
                      <td className="px-6 py-4 whitespace-nowrap text-sm text-gray-500">
                        {formatCurrency(trade.actual_entry || trade.planned_entry)}
                      </td>
                      <td className="px-6 py-4 whitespace-nowrap text-sm text-gray-500">
                        {trade.actual_qty || trade.planned_qty || 'N/A'}
                      </td>
                      <td className="px-6 py-4 whitespace-nowrap text-sm text-gray-500">
                        {trade.days_open}
                      </td>
                      <td className="px-6 py-4 whitespace-nowrap text-sm font-medium">
                        {formatPnL(trade.actual_pnl) || '-'}
                      </td>
                    </tr>
                  ))}
                </tbody>
              </table>
            </div>
          </div>

          {/* Mobile Cards */}
          <div className="md:hidden space-y-4">
            {trades.data.map((trade) => (
              <div key={trade.id} className="bg-white shadow rounded-lg p-4 space-y-3">
                <div className="flex items-center justify-between">
                  <span className="text-lg font-semibold text-gray-900">{trade.symbol}</span>
                  <span className={`px-2 py-1 inline-flex text-xs leading-5 font-semibold rounded-full ${getStatusColor(trade.status)}`}>
                    {trade.status}
                  </span>
                </div>
                <div className="grid grid-cols-2 gap-2 text-sm">
                  <div>
                    <p className="text-gray-500">Trade ID</p>
                    <p className="font-medium text-gray-900">{trade.trade_id}</p>
                  </div>
                  <div>
                    <p className="text-gray-500">Entry Price</p>
                    <p className="font-medium text-gray-900">{formatCurrency(trade.actual_entry || trade.planned_entry)}</p>
                  </div>
                  <div>
                    <p className="text-gray-500">Quantity</p>
                    <p className="font-medium text-gray-900">{trade.actual_qty || trade.planned_qty || 'N/A'}</p>
                  </div>
                  <div>
                    <p className="text-gray-500">Days Open</p>
                    <p className="font-medium text-gray-900">{trade.days_open}</p>
                  </div>
                  {trade.actual_pnl !== null && trade.actual_pnl !== undefined && (
                    <div className="col-span-2">
                      <p className="text-gray-500">P&L</p>
                      <p className="font-medium">{formatPnL(trade.actual_pnl)}</p>
                    </div>
                  )}
                </div>
              </div>
            ))}
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
