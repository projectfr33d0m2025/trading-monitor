import { useState, useEffect } from 'react';
import { Filter, ChevronDown, ChevronUp, CheckCircle, XCircle, Clock, ShoppingCart, StopCircle, Trophy, Package } from 'lucide-react';
import { api } from '../lib/api';
import type { OrderExecution, PaginatedResponse } from '../lib/types';

export default function OrdersPage() {
  const [orders, setOrders] = useState<PaginatedResponse<OrderExecution> | null>(null);
  const [stats, setStats] = useState<any>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [expandedOrder, setExpandedOrder] = useState<number | null>(null);

  // Filters
  const [filterOrderType, setFilterOrderType] = useState<string>('');
  const [filterOrderStatus, setFilterOrderStatus] = useState<string>('');
  const [showFilters, setShowFilters] = useState(true);

  // Pagination
  const [currentPage, setCurrentPage] = useState(1);
  const pageSize = 20;

  useEffect(() => {
    fetchData();
  }, [currentPage, filterOrderType, filterOrderStatus]);

  const fetchData = async () => {
    setLoading(true);
    setError(null);

    try {
      const [ordersData, statsData] = await Promise.all([
        api.getOrders({
          page: currentPage,
          page_size: pageSize,
          order_type: filterOrderType || undefined,
          order_status: filterOrderStatus || undefined,
        }),
        api.getOrderStats(),
      ]);
      setOrders(ordersData);
      setStats(statsData);
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Failed to fetch orders');
    } finally {
      setLoading(false);
    }
  };

  const getOrderTypeIcon = (type: string) => {
    switch (type) {
      case 'ENTRY':
        return <ShoppingCart className="w-5 h-5" />;
      case 'STOP_LOSS':
        return <StopCircle className="w-5 h-5" />;
      case 'TAKE_PROFIT':
        return <Trophy className="w-5 h-5" />;
      default:
        return <Package className="w-5 h-5" />;
    }
  };

  const getOrderTypeGradient = (type: string) => {
    switch (type) {
      case 'ENTRY':
        return 'from-blue-500 to-blue-600';
      case 'STOP_LOSS':
        return 'from-red-500 to-red-600';
      case 'TAKE_PROFIT':
        return 'from-green-500 to-green-600';
      default:
        return 'from-gray-400 to-gray-500';
    }
  };

  const getStatusGradient = (status: string) => {
    switch (status) {
      case 'filled':
        return 'from-green-500 to-green-600';
      case 'cancelled':
        return 'from-red-500 to-red-600';
      case 'partially_filled':
        return 'from-yellow-500 to-yellow-600';
      default:
        return 'from-blue-500 to-blue-600';
    }
  };

  const getStatusIcon = (status: string) => {
    switch (status) {
      case 'filled':
        return <CheckCircle className="w-5 h-5" />;
      case 'cancelled':
        return <XCircle className="w-5 h-5" />;
      case 'partially_filled':
        return <Clock className="w-5 h-5" />;
      default:
        return <Clock className="w-5 h-5" />;
    }
  };

  const getOrderTypeColor = (type: string) => {
    const colors: Record<string, string> = {
      ENTRY: 'bg-blue-100 text-blue-800 border-blue-200',
      STOP_LOSS: 'bg-red-100 text-red-800 border-red-200',
      TAKE_PROFIT: 'bg-green-100 text-green-800 border-green-200',
    };
    return colors[type] || 'bg-gray-100 text-gray-800 border-gray-200';
  };

  const formatCurrency = (value?: number | string | null) => {
    if (value === undefined || value === null) return 'N/A';
    const numValue = typeof value === 'string' ? parseFloat(value) : value;
    if (isNaN(numValue)) return 'N/A';
    return `$${numValue.toFixed(2)}`;
  };

  const typeBreakdown = stats?.type_breakdown || {};
  const statusBreakdown = stats?.status_breakdown || {};

  return (
    <div className="space-y-4 sm:space-y-6">
      {/* Header */}
      <div className="flex flex-col sm:flex-row sm:items-center sm:justify-between gap-4">
        <div>
          <h1 className="text-2xl font-bold text-gray-900">Order Execution</h1>
          <p className="mt-1 text-sm text-gray-500">
            Monitor all order executions and their status
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

      {/* Summary Cards - Order Types */}
      {!loading && stats && (
        <>
          <div className="grid grid-cols-1 sm:grid-cols-3 gap-4">
            {Object.entries(typeBreakdown).map(([type, count]: [string, any]) => (
              <div key={type} className={`bg-gradient-to-br ${getOrderTypeGradient(type)} rounded-lg shadow-lg p-6 text-white`}>
                <div className="flex items-center justify-between">
                  <div>
                    <p className="text-sm font-medium opacity-90 uppercase">{type.replace('_', ' ')}</p>
                    <p className="text-3xl font-bold mt-1">{count}</p>
                  </div>
                  <div className="opacity-30">
                    {getOrderTypeIcon(type)}
                  </div>
                </div>
              </div>
            ))}
          </div>

          {/* Summary Cards - Order Status */}
          <div className="grid grid-cols-2 lg:grid-cols-4 gap-4">
            {Object.entries(statusBreakdown).map(([status, count]: [string, any]) => (
              <div key={status} className={`bg-gradient-to-br ${getStatusGradient(status)} rounded-lg shadow-lg p-6 text-white`}>
                <div className="flex items-center justify-between">
                  <div>
                    <p className="text-sm font-medium opacity-90 uppercase">{status.replace('_', ' ')}</p>
                    <p className="text-3xl font-bold mt-1">{count}</p>
                  </div>
                  <div className="opacity-30">
                    {getStatusIcon(status)}
                  </div>
                </div>
              </div>
            ))}
          </div>
        </>
      )}

      {/* Filters */}
      {showFilters && (
        <div className="bg-white p-4 rounded-lg shadow space-y-4">
          <div className="grid grid-cols-1 sm:grid-cols-2 gap-4">
            <div>
              <label className="block text-sm font-medium text-gray-700 mb-1">
                Order Type
              </label>
              <select
                value={filterOrderType}
                onChange={(e) => setFilterOrderType(e.target.value)}
                className="w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-blue-500"
              >
                <option value="">All Types</option>
                <option value="ENTRY">Entry</option>
                <option value="STOP_LOSS">Stop Loss</option>
                <option value="TAKE_PROFIT">Take Profit</option>
              </select>
            </div>
            <div>
              <label className="block text-sm font-medium text-gray-700 mb-1">
                Order Status
              </label>
              <select
                value={filterOrderStatus}
                onChange={(e) => setFilterOrderStatus(e.target.value)}
                className="w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-blue-500"
              >
                <option value="">All Statuses</option>
                <option value="pending">Pending</option>
                <option value="filled">Filled</option>
                <option value="partially_filled">Partially Filled</option>
                <option value="cancelled">Cancelled</option>
              </select>
            </div>
          </div>
        </div>
      )}

      {/* Content */}
      {loading && (
        <div className="bg-white rounded-lg shadow p-8 text-center">
          <div className="inline-block animate-spin rounded-full h-8 w-8 border-b-2 border-gray-900"></div>
          <p className="mt-2 text-gray-600">Loading orders...</p>
        </div>
      )}

      {error && (
        <div className="bg-red-50 border border-red-200 rounded-lg p-4">
          <p className="text-sm text-red-800">{error}</p>
        </div>
      )}

      {!loading && !error && orders && (
        <>
          {/* Enhanced Order Cards */}
          <div className="space-y-4">
            {orders.data.map((order) => {
              const isExpanded = expandedOrder === order.id;
              const typeColorClass = getOrderTypeColor(order.order_type);

              return (
                <div key={order.id} className={`bg-white rounded-lg shadow-md border-2 ${typeColorClass} overflow-hidden transition-all`}>
                  {/* Order Header */}
                  <div
                    className="p-4 sm:p-6 cursor-pointer hover:bg-gray-50"
                    onClick={() => setExpandedOrder(isExpanded ? null : order.id)}
                  >
                    <div className="flex items-center justify-between">
                      <div className="flex items-center space-x-4">
                        <div className="bg-white rounded-lg p-3 shadow-sm border border-gray-200">
                          {getOrderTypeIcon(order.order_type)}
                        </div>
                        <div>
                          <div className="flex items-center space-x-2">
                            <span className={`px-3 py-1 inline-flex items-center text-sm font-semibold rounded-full ${typeColorClass}`}>
                              {getOrderTypeIcon(order.order_type)}
                              <span className="ml-1.5">{order.order_type.replace('_', ' ')}</span>
                            </span>
                            <span className="text-xs uppercase font-medium text-gray-600 px-2 py-1 bg-gray-100 rounded">{order.side}</span>
                          </div>
                          <p className="text-sm text-gray-500 mt-1 font-mono">
                            {order.client_order_id || order.alpaca_order_id.substring(0, 16)}
                          </p>
                        </div>
                      </div>
                      <div className="flex items-center space-x-4">
                        <div className="text-right">
                          <div className="flex items-center space-x-1">
                            {getStatusIcon(order.order_status)}
                            <span className="text-sm font-medium capitalize">{order.order_status.replace('_', ' ')}</span>
                          </div>
                          {order.filled_qty !== null && order.filled_qty > 0 && (
                            <p className="text-xs text-gray-500 mt-1">
                              Filled: {order.filled_qty} @ {formatCurrency(order.filled_avg_price)}
                            </p>
                          )}
                        </div>
                        {isExpanded ? (
                          <ChevronUp className="w-6 h-6 text-gray-400" />
                        ) : (
                          <ChevronDown className="w-6 h-6 text-gray-400" />
                        )}
                      </div>
                    </div>

                    {/* Order Summary */}
                    <div className="mt-4 grid grid-cols-2 sm:grid-cols-4 gap-4">
                      <div>
                        <p className="text-xs text-gray-500 uppercase tracking-wide">Quantity</p>
                        <p className="text-lg font-semibold text-gray-900">{order.qty}</p>
                      </div>
                      <div>
                        <p className="text-xs text-gray-500 uppercase tracking-wide">Order Price</p>
                        <p className="text-lg font-semibold text-gray-900">
                          {formatCurrency(order.limit_price || order.stop_price)}
                        </p>
                      </div>
                      <div>
                        <p className="text-xs text-gray-500 uppercase tracking-wide">Filled Qty</p>
                        <p className="text-lg font-semibold text-gray-900">{order.filled_qty || 0}</p>
                      </div>
                      <div>
                        <p className="text-xs text-gray-500 uppercase tracking-wide">Avg Fill Price</p>
                        <p className="text-lg font-semibold text-gray-900">
                          {formatCurrency(order.filled_avg_price)}
                        </p>
                      </div>
                    </div>
                  </div>

                  {/* Expandable Details */}
                  {isExpanded && (
                    <div className="border-t border-gray-200 bg-gray-50 p-4 sm:p-6">
                      <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-3 gap-4">
                        {order.alpaca_order_id && (
                          <div>
                            <p className="text-sm text-gray-500">Alpaca Order ID</p>
                            <p className="text-base font-mono text-gray-900 break-all">{order.alpaca_order_id}</p>
                          </div>
                        )}
                        {order.submitted_at && (
                          <div>
                            <p className="text-sm text-gray-500">Submitted</p>
                            <p className="text-base font-semibold text-gray-900">
                              {new Date(order.submitted_at).toLocaleString()}
                            </p>
                          </div>
                        )}
                        {order.filled_at && (
                          <div>
                            <p className="text-sm text-gray-500">Filled At</p>
                            <p className="text-base font-semibold text-gray-900">
                              {new Date(order.filled_at).toLocaleString()}
                            </p>
                          </div>
                        )}
                        {order.cancelled_at && (
                          <div>
                            <p className="text-sm text-gray-500">Cancelled At</p>
                            <p className="text-base font-semibold text-gray-900">
                              {new Date(order.cancelled_at).toLocaleString()}
                            </p>
                          </div>
                        )}
                        <div>
                          <p className="text-sm text-gray-500">Trade Journal ID</p>
                          <p className="text-base font-semibold text-gray-900">#{order.trade_journal_id}</p>
                        </div>
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
              <span className="font-medium">{Math.min(currentPage * pageSize, orders.total)}</span> of{' '}
              <span className="font-medium">{orders.total}</span> results
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
                disabled={currentPage * pageSize >= orders.total}
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
