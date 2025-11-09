import { useState, useEffect } from 'react';
import { Filter, ChevronDown, ChevronUp, CheckCircle, XCircle, Clock } from 'lucide-react';
import { api } from '../lib/api';
import type { OrderExecution, PaginatedResponse } from '../lib/types';

export default function OrdersPage() {
  const [orders, setOrders] = useState<PaginatedResponse<OrderExecution> | null>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  // Filters
  const [filterOrderType, setFilterOrderType] = useState<string>('');
  const [filterOrderStatus, setFilterOrderStatus] = useState<string>('');
  const [showFilters, setShowFilters] = useState(true);

  // Pagination
  const [currentPage, setCurrentPage] = useState(1);
  const pageSize = 20;

  useEffect(() => {
    fetchOrders();
  }, [currentPage, filterOrderType, filterOrderStatus]);

  const fetchOrders = async () => {
    setLoading(true);
    setError(null);

    try {
      const data = await api.getOrders({
        page: currentPage,
        page_size: pageSize,
        order_type: filterOrderType || undefined,
        order_status: filterOrderStatus || undefined,
      });
      setOrders(data);
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Failed to fetch orders');
    } finally {
      setLoading(false);
    }
  };

  const getStatusIcon = (status: string) => {
    if (status === 'filled') return <CheckCircle className="w-4 h-4 text-green-500" />;
    if (status === 'cancelled') return <XCircle className="w-4 h-4 text-red-500" />;
    return <Clock className="w-4 h-4 text-yellow-500" />;
  };

  const getOrderTypeColor = (type: string) => {
    const colors: Record<string, string> = {
      ENTRY: 'bg-blue-100 text-blue-800',
      STOP_LOSS: 'bg-red-100 text-red-800',
      TAKE_PROFIT: 'bg-green-100 text-green-800',
    };
    return colors[type] || 'bg-gray-100 text-gray-800';
  };

  const formatCurrency = (value?: number) => {
    if (value === undefined || value === null) return 'N/A';
    return `$${value.toFixed(2)}`;
  };

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
          {/* Desktop Table */}
          <div className="hidden lg:block bg-white shadow rounded-lg overflow-hidden">
            <div className="overflow-x-auto">
              <table className="min-w-full divide-y divide-gray-200">
                <thead className="bg-gray-50">
                  <tr>
                    <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                      Order ID
                    </th>
                    <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                      Type
                    </th>
                    <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                      Side
                    </th>
                    <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                      Qty
                    </th>
                    <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                      Price
                    </th>
                    <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                      Filled
                    </th>
                    <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                      Status
                    </th>
                  </tr>
                </thead>
                <tbody className="bg-white divide-y divide-gray-200">
                  {orders.data.map((order) => (
                    <tr key={order.id} className="hover:bg-gray-50">
                      <td className="px-6 py-4 whitespace-nowrap text-sm font-mono text-gray-900">
                        {order.client_order_id || order.alpaca_order_id.substring(0, 8)}
                      </td>
                      <td className="px-6 py-4 whitespace-nowrap">
                        <span className={`px-2 py-1 inline-flex text-xs leading-5 font-semibold rounded-full ${getOrderTypeColor(order.order_type)}`}>
                          {order.order_type}
                        </span>
                      </td>
                      <td className="px-6 py-4 whitespace-nowrap text-sm text-gray-900 uppercase">
                        {order.side}
                      </td>
                      <td className="px-6 py-4 whitespace-nowrap text-sm text-gray-500">
                        {order.qty}
                      </td>
                      <td className="px-6 py-4 whitespace-nowrap text-sm text-gray-500">
                        {formatCurrency(order.limit_price || order.stop_price)}
                      </td>
                      <td className="px-6 py-4 whitespace-nowrap text-sm text-gray-500">
                        {order.filled_qty || 0} @ {formatCurrency(order.filled_avg_price)}
                      </td>
                      <td className="px-6 py-4 whitespace-nowrap">
                        <div className="flex items-center">
                          {getStatusIcon(order.order_status)}
                          <span className="ml-2 text-sm text-gray-900 capitalize">{order.order_status}</span>
                        </div>
                      </td>
                    </tr>
                  ))}
                </tbody>
              </table>
            </div>
          </div>

          {/* Mobile Cards */}
          <div className="lg:hidden space-y-4">
            {orders.data.map((order) => (
              <div key={order.id} className="bg-white shadow rounded-lg p-4 space-y-3">
                <div className="flex items-center justify-between">
                  <span className="text-xs font-mono text-gray-500">
                    {order.client_order_id || order.alpaca_order_id.substring(0, 12)}
                  </span>
                  <div className="flex items-center">
                    {getStatusIcon(order.order_status)}
                    <span className="ml-1 text-sm capitalize">{order.order_status}</span>
                  </div>
                </div>
                <div className="flex items-center justify-between">
                  <span className={`px-2 py-1 inline-flex text-xs leading-5 font-semibold rounded-full ${getOrderTypeColor(order.order_type)}`}>
                    {order.order_type}
                  </span>
                  <span className="text-sm font-semibold text-gray-900 uppercase">{order.side}</span>
                </div>
                <div className="grid grid-cols-2 gap-2 text-sm">
                  <div>
                    <p className="text-gray-500">Quantity</p>
                    <p className="font-medium text-gray-900">{order.qty}</p>
                  </div>
                  <div>
                    <p className="text-gray-500">Price</p>
                    <p className="font-medium text-gray-900">{formatCurrency(order.limit_price || order.stop_price)}</p>
                  </div>
                  <div className="col-span-2">
                    <p className="text-gray-500">Filled</p>
                    <p className="font-medium text-gray-900">
                      {order.filled_qty || 0} @ {formatCurrency(order.filled_avg_price)}
                    </p>
                  </div>
                </div>
              </div>
            ))}
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
