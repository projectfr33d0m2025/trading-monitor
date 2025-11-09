import { useState, useEffect } from 'react';
import { TrendingUp, TrendingDown, DollarSign, ChevronDown, ChevronUp, Package, ShoppingCart, StopCircle, Trophy, CheckCircle } from 'lucide-react';
import { api } from '../lib/api';
import type { PositionTracking, PaginatedResponse, OrderExecution } from '../lib/types';

export default function PositionsPage() {
  const [positions, setPositions] = useState<PaginatedResponse<PositionTracking> | null>(null);
  const [pnlSummary, setPnlSummary] = useState<any>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [expandedPosition, setExpandedPosition] = useState<number | null>(null);
  const [positionOrders, setPositionOrders] = useState<Record<number, OrderExecution[]>>({});

  useEffect(() => {
    fetchData();
  }, []);

  const fetchData = async () => {
    setLoading(true);
    setError(null);

    try {
      const [positionsData, summaryData] = await Promise.all([
        api.getPositions({ page: 1, page_size: 100 }),
        api.getPnLSummary(),
      ]);
      setPositions(positionsData);
      setPnlSummary(summaryData);
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Failed to fetch positions');
    } finally {
      setLoading(false);
    }
  };

  const togglePosition = async (positionId: number, tradeJournalId: number) => {
    if (expandedPosition === positionId) {
      setExpandedPosition(null);
    } else {
      setExpandedPosition(positionId);

      // Fetch orders for this position if not already loaded
      if (!positionOrders[positionId]) {
        try {
          const orders = await api.getOrdersByTrade(tradeJournalId);
          setPositionOrders(prev => ({ ...prev, [positionId]: orders.data }));
        } catch (err) {
          console.error('Failed to fetch orders:', err);
        }
      }
    }
  };

  const formatCurrency = (value?: number) => {
    if (value === undefined || value === null) return '$0.00';
    return `$${value.toFixed(2)}`;
  };

  const formatPercent = (entry: number, current: number) => {
    const change = ((current - entry) / entry) * 100;
    return `${change >= 0 ? '+' : ''}${change.toFixed(2)}%`;
  };

  const getPnLColor = (pnl: number) => {
    return pnl >= 0 ? 'text-green-600' : 'text-red-600';
  };

  const getPnLBgColor = (pnl: number) => {
    return pnl >= 0 ? 'bg-green-50 border-green-200' : 'bg-red-50 border-red-200';
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

  const totalUnrealizedPnL = pnlSummary?.summary?.total_unrealized_pnl || 0;

  return (
    <div className="space-y-4 sm:space-y-6">
      {/* Header */}
      <div>
        <h1 className="text-2xl font-bold text-gray-900">Position Tracking</h1>
        <p className="mt-1 text-sm text-gray-500">
          Monitor current positions and unrealized P&L
        </p>
      </div>

      {/* Content */}
      {loading && (
        <div className="bg-white rounded-lg shadow p-8 text-center">
          <div className="inline-block animate-spin rounded-full h-8 w-8 border-b-2 border-gray-900"></div>
          <p className="mt-2 text-gray-600">Loading positions...</p>
        </div>
      )}

      {error && (
        <div className="bg-red-50 border border-red-200 rounded-lg p-4">
          <p className="text-sm text-red-800">{error}</p>
        </div>
      )}

      {!loading && !error && (
        <>
          {/* Summary Cards with Gradients */}
          <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 gap-4">
            {/* Total Positions */}
            <div className="bg-gradient-to-br from-blue-500 to-blue-600 rounded-lg shadow-lg p-6 text-white">
              <div className="flex items-center justify-between">
                <div>
                  <p className="text-sm font-medium opacity-90">Total Positions</p>
                  <p className="text-3xl font-bold mt-1">
                    {pnlSummary?.summary?.total_positions || 0}
                  </p>
                </div>
                <Package className="w-12 h-12 opacity-30" />
              </div>
            </div>

            {/* Market Value */}
            <div className="bg-gradient-to-br from-purple-500 to-purple-600 rounded-lg shadow-lg p-6 text-white">
              <div className="flex items-center justify-between">
                <div>
                  <p className="text-sm font-medium opacity-90">Market Value</p>
                  <p className="text-3xl font-bold mt-1">
                    {formatCurrency(pnlSummary?.summary?.total_market_value)}
                  </p>
                </div>
                <DollarSign className="w-12 h-12 opacity-30" />
              </div>
            </div>

            {/* Cost Basis */}
            <div className="bg-gradient-to-br from-gray-500 to-gray-600 rounded-lg shadow-lg p-6 text-white">
              <div className="flex items-center justify-between">
                <div>
                  <p className="text-sm font-medium opacity-90">Cost Basis</p>
                  <p className="text-3xl font-bold mt-1">
                    {formatCurrency(pnlSummary?.summary?.total_cost_basis)}
                  </p>
                </div>
                <DollarSign className="w-12 h-12 opacity-30" />
              </div>
            </div>

            {/* Unrealized P&L */}
            <div className={`bg-gradient-to-br ${totalUnrealizedPnL >= 0 ? 'from-green-500 to-green-600' : 'from-red-500 to-red-600'} rounded-lg shadow-lg p-6 text-white`}>
              <div className="flex items-center justify-between">
                <div>
                  <p className="text-sm font-medium opacity-90">Unrealized P&L</p>
                  <p className="text-3xl font-bold mt-1">
                    {formatCurrency(totalUnrealizedPnL)}
                  </p>
                </div>
                {totalUnrealizedPnL >= 0 ? (
                  <TrendingUp className="w-12 h-12 opacity-30" />
                ) : (
                  <TrendingDown className="w-12 h-12 opacity-30" />
                )}
              </div>
            </div>
          </div>

          {/* Positions Cards with Progressive Disclosure */}
          {positions && positions.data.length > 0 ? (
            <div className="space-y-4">
              {positions.data.map((position) => {
                const pnlColor = getPnLColor(position.unrealized_pnl);
                const pnlBgColor = getPnLBgColor(position.unrealized_pnl);
                const isExpanded = expandedPosition === position.id;
                const orders = positionOrders[position.id] || [];

                return (
                  <div key={position.id} className={`bg-white rounded-lg shadow-md border-2 ${pnlBgColor} overflow-hidden transition-all`}>
                    {/* Position Header */}
                    <div
                      className="p-4 sm:p-6 cursor-pointer hover:bg-gray-50"
                      onClick={() => togglePosition(position.id, position.trade_journal_id)}
                    >
                      <div className="flex items-center justify-between">
                        <div className="flex items-center space-x-4">
                          <div className="bg-white rounded-lg p-3 shadow-sm border border-gray-200">
                            <Package className="w-8 h-8 text-blue-600" />
                          </div>
                          <div>
                            <h3 className="text-xl font-bold text-gray-900">{position.symbol}</h3>
                            <p className="text-sm text-gray-500">Position #{position.id}</p>
                          </div>
                        </div>
                        <div className="flex items-center space-x-4">
                          <div className="text-right">
                            <p className={`text-2xl font-bold ${pnlColor}`}>
                              {formatCurrency(position.unrealized_pnl)}
                            </p>
                            <p className={`text-sm font-medium ${pnlColor}`}>
                              {formatPercent(position.avg_entry_price, position.current_price)}
                            </p>
                          </div>
                          {isExpanded ? (
                            <ChevronUp className="w-6 h-6 text-gray-400" />
                          ) : (
                            <ChevronDown className="w-6 h-6 text-gray-400" />
                          )}
                        </div>
                      </div>

                      {/* Position Summary */}
                      <div className="mt-4 grid grid-cols-2 sm:grid-cols-4 gap-4">
                        <div>
                          <p className="text-xs text-gray-500 uppercase tracking-wide">Quantity</p>
                          <p className="text-lg font-semibold text-gray-900">{position.qty}</p>
                        </div>
                        <div>
                          <p className="text-xs text-gray-500 uppercase tracking-wide">Entry Price</p>
                          <p className="text-lg font-semibold text-gray-900">{formatCurrency(position.avg_entry_price)}</p>
                        </div>
                        <div>
                          <p className="text-xs text-gray-500 uppercase tracking-wide">Current Price</p>
                          <p className="text-lg font-semibold text-gray-900">{formatCurrency(position.current_price)}</p>
                        </div>
                        <div>
                          <p className="text-xs text-gray-500 uppercase tracking-wide">Market Value</p>
                          <p className="text-lg font-semibold text-gray-900">{formatCurrency(position.market_value)}</p>
                        </div>
                      </div>
                    </div>

                    {/* Expandable Orders Section */}
                    {isExpanded && (
                      <div className="border-t border-gray-200 bg-gray-50 p-4 sm:p-6">
                        <h4 className="text-sm font-semibold text-gray-700 mb-4 flex items-center">
                          <ShoppingCart className="w-4 h-4 mr-2" />
                          Active Orders ({orders.length})
                        </h4>

                        {orders.length > 0 ? (
                          <div className="space-y-2">
                            {orders.map((order) => (
                              <div key={order.id} className="bg-white rounded-lg p-4 shadow-sm border border-gray-200">
                                <div className="flex items-center justify-between">
                                  <div className="flex items-center space-x-3">
                                    <div className={`p-2 rounded-lg ${getOrderTypeBadgeColor(order.order_type)}`}>
                                      {getOrderTypeIcon(order.order_type)}
                                    </div>
                                    <div>
                                      <div className="flex items-center space-x-2">
                                        <span className={`px-2 py-1 rounded-full text-xs font-semibold ${getOrderTypeBadgeColor(order.order_type)}`}>
                                          {order.order_type}
                                        </span>
                                        <span className="text-xs uppercase font-medium text-gray-600">{order.side}</span>
                                      </div>
                                      <p className="text-sm text-gray-500 mt-1">
                                        {order.qty} @ {formatCurrency(order.limit_price || order.stop_price)}
                                      </p>
                                    </div>
                                  </div>
                                  <div className="text-right">
                                    <div className="flex items-center space-x-1">
                                      {order.order_status === 'filled' && (
                                        <CheckCircle className="w-4 h-4 text-green-500" />
                                      )}
                                      <span className={`text-sm font-medium capitalize ${
                                        order.order_status === 'filled' ? 'text-green-600' :
                                        order.order_status === 'cancelled' ? 'text-red-600' :
                                        'text-yellow-600'
                                      }`}>
                                        {order.order_status}
                                      </span>
                                    </div>
                                    {order.filled_qty !== null && order.filled_qty > 0 && (
                                      <p className="text-xs text-gray-500 mt-1">
                                        Filled: {order.filled_qty} @ {formatCurrency(order.filled_avg_price)}
                                      </p>
                                    )}
                                  </div>
                                </div>
                              </div>
                            ))}
                          </div>
                        ) : (
                          <p className="text-sm text-gray-500 italic">No active orders for this position</p>
                        )}
                      </div>
                    )}
                  </div>
                );
              })}
            </div>
          ) : (
            <div className="bg-white rounded-lg shadow p-8 text-center">
              <Package className="w-16 h-16 text-gray-400 mx-auto mb-4" />
              <p className="text-gray-500">No active positions</p>
            </div>
          )}
        </>
      )}
    </div>
  );
}
