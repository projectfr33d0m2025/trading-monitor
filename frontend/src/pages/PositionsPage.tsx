import { useState, useEffect } from 'react';
import { TrendingUp, TrendingDown, DollarSign } from 'lucide-react';
import { api } from '../lib/api';
import type { PositionTracking, PaginatedResponse } from '../lib/types';

export default function PositionsPage() {
  const [positions, setPositions] = useState<PaginatedResponse<PositionTracking> | null>(null);
  const [pnlSummary, setPnlSummary] = useState<any>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

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
          {/* Summary Cards */}
          <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 gap-4">
            <div className="bg-white rounded-lg shadow p-6">
              <div className="flex items-center">
                <DollarSign className="w-8 h-8 text-blue-500" />
                <div className="ml-4">
                  <p className="text-sm font-medium text-gray-500">Total Positions</p>
                  <p className="text-2xl font-semibold text-gray-900">
                    {pnlSummary?.summary?.total_positions || 0}
                  </p>
                </div>
              </div>
            </div>
            <div className="bg-white rounded-lg shadow p-6">
              <div className="flex items-center">
                <DollarSign className="w-8 h-8 text-purple-500" />
                <div className="ml-4">
                  <p className="text-sm font-medium text-gray-500">Market Value</p>
                  <p className="text-2xl font-semibold text-gray-900">
                    {formatCurrency(pnlSummary?.summary?.total_market_value)}
                  </p>
                </div>
              </div>
            </div>
            <div className="bg-white rounded-lg shadow p-6">
              <div className="flex items-center">
                <DollarSign className="w-8 h-8 text-gray-500" />
                <div className="ml-4">
                  <p className="text-sm font-medium text-gray-500">Cost Basis</p>
                  <p className="text-2xl font-semibold text-gray-900">
                    {formatCurrency(pnlSummary?.summary?.total_cost_basis)}
                  </p>
                </div>
              </div>
            </div>
            <div className="bg-white rounded-lg shadow p-6">
              <div className="flex items-center">
                {totalUnrealizedPnL >= 0 ? (
                  <TrendingUp className="w-8 h-8 text-green-500" />
                ) : (
                  <TrendingDown className="w-8 h-8 text-red-500" />
                )}
                <div className="ml-4">
                  <p className="text-sm font-medium text-gray-500">Unrealized P&L</p>
                  <p className={`text-2xl font-semibold ${getPnLColor(totalUnrealizedPnL)}`}>
                    {formatCurrency(totalUnrealizedPnL)}
                  </p>
                </div>
              </div>
            </div>
          </div>

          {/* Positions Table/Cards */}
          {positions && positions.data.length > 0 ? (
            <>
              {/* Desktop Table */}
              <div className="hidden md:block bg-white shadow rounded-lg overflow-hidden">
                <table className="min-w-full divide-y divide-gray-200">
                  <thead className="bg-gray-50">
                    <tr>
                      <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                        Symbol
                      </th>
                      <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                        Qty
                      </th>
                      <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                        Entry Price
                      </th>
                      <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                        Current Price
                      </th>
                      <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                        Change
                      </th>
                      <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                        Market Value
                      </th>
                      <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                        Unrealized P&L
                      </th>
                    </tr>
                  </thead>
                  <tbody className="bg-white divide-y divide-gray-200">
                    {positions.data.map((position) => {
                      const pnlColor = getPnLColor(position.unrealized_pnl);
                      return (
                        <tr key={position.id} className="hover:bg-gray-50">
                          <td className="px-6 py-4 whitespace-nowrap text-sm font-semibold text-gray-900">
                            {position.symbol}
                          </td>
                          <td className="px-6 py-4 whitespace-nowrap text-sm text-gray-500">
                            {position.qty}
                          </td>
                          <td className="px-6 py-4 whitespace-nowrap text-sm text-gray-500">
                            {formatCurrency(position.avg_entry_price)}
                          </td>
                          <td className="px-6 py-4 whitespace-nowrap text-sm text-gray-900">
                            {formatCurrency(position.current_price)}
                          </td>
                          <td className={`px-6 py-4 whitespace-nowrap text-sm font-medium ${pnlColor}`}>
                            {formatPercent(position.avg_entry_price, position.current_price)}
                          </td>
                          <td className="px-6 py-4 whitespace-nowrap text-sm text-gray-900">
                            {formatCurrency(position.market_value)}
                          </td>
                          <td className={`px-6 py-4 whitespace-nowrap text-sm font-semibold ${pnlColor}`}>
                            {formatCurrency(position.unrealized_pnl)}
                          </td>
                        </tr>
                      );
                    })}
                  </tbody>
                </table>
              </div>

              {/* Mobile Cards */}
              <div className="md:hidden space-y-4">
                {positions.data.map((position) => {
                  const pnlColor = getPnLColor(position.unrealized_pnl);
                  return (
                    <div key={position.id} className="bg-white shadow rounded-lg p-4 space-y-3">
                      <div className="flex items-center justify-between">
                        <span className="text-lg font-bold text-gray-900">{position.symbol}</span>
                        <span className={`text-lg font-bold ${pnlColor}`}>
                          {formatCurrency(position.unrealized_pnl)}
                        </span>
                      </div>
                      <div className="grid grid-cols-2 gap-3 text-sm">
                        <div>
                          <p className="text-gray-500">Quantity</p>
                          <p className="font-medium text-gray-900">{position.qty}</p>
                        </div>
                        <div>
                          <p className="text-gray-500">Market Value</p>
                          <p className="font-medium text-gray-900">{formatCurrency(position.market_value)}</p>
                        </div>
                        <div>
                          <p className="text-gray-500">Entry Price</p>
                          <p className="font-medium text-gray-900">{formatCurrency(position.avg_entry_price)}</p>
                        </div>
                        <div>
                          <p className="text-gray-500">Current Price</p>
                          <p className="font-medium text-gray-900">{formatCurrency(position.current_price)}</p>
                        </div>
                        <div className="col-span-2">
                          <p className="text-gray-500">Change</p>
                          <p className={`font-semibold ${pnlColor}`}>
                            {formatPercent(position.avg_entry_price, position.current_price)}
                          </p>
                        </div>
                      </div>
                    </div>
                  );
                })}
              </div>
            </>
          ) : (
            <div className="bg-white rounded-lg shadow p-8 text-center">
              <p className="text-gray-500">No active positions</p>
            </div>
          )}
        </>
      )}
    </div>
  );
}
