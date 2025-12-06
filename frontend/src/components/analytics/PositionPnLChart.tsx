import React from 'react';
import {
  BarChart,
  Bar,
  XAxis,
  YAxis,
  CartesianGrid,
  Tooltip,
  ResponsiveContainer,
  Cell,
  Legend,
} from 'recharts';
import type { PositionBreakdown } from '../../types/analytics';

interface PositionPnLChartProps {
  data: PositionBreakdown[];
  loading?: boolean;
  error?: string | null;
}

export function PositionPnLChart({ data, loading, error }: PositionPnLChartProps) {
  if (loading) {
    return (
      <div className="bg-white rounded-lg shadow-sm p-6">
        <div className="h-6 bg-gray-200 rounded w-1/3 mb-4 animate-pulse"></div>
        <div className="h-80 bg-gray-100 rounded animate-pulse"></div>
      </div>
    );
  }

  if (error) {
    return (
      <div className="bg-red-50 border border-red-200 rounded-lg p-6">
        <h3 className="text-lg font-semibold text-red-800 mb-2">Error Loading Positions</h3>
        <p className="text-red-600 text-sm">{error}</p>
      </div>
    );
  }

  if (!data || data.length === 0) {
    return (
      <div className="bg-white rounded-lg shadow-sm p-6">
        <h3 className="text-lg font-semibold text-gray-900 mb-4">Current Positions P&L</h3>
        <div className="h-80 flex items-center justify-center bg-gray-50 rounded">
          <p className="text-gray-500">No active positions</p>
        </div>
      </div>
    );
  }

  // Format currency for tooltip
  const formatCurrency = (value: number) => {
    return new Intl.NumberFormat('en-US', {
      style: 'currency',
      currency: 'USD',
      minimumFractionDigits: 2,
      maximumFractionDigits: 2,
    }).format(value);
  };

  // Sort by absolute P&L (largest to smallest)
  const sortedData = [...data].sort(
    (a, b) => Math.abs(b.unrealized_pnl) - Math.abs(a.unrealized_pnl)
  );

  // Custom tooltip
  const CustomTooltip = ({ active, payload }: any) => {
    if (active && payload && payload.length) {
      const data = payload[0].payload;
      return (
        <div className="bg-white p-4 border border-gray-200 rounded-lg shadow-lg">
          <p className="font-bold text-gray-900 mb-2">{data.symbol}</p>
          <div className="space-y-1 text-sm">
            <p className="text-gray-700">
              Quantity: <span className="font-medium">{data.qty}</span>
            </p>
            <p className="text-gray-700">
              Entry: <span className="font-medium">{formatCurrency(data.avg_entry_price)}</span>
            </p>
            <p className="text-gray-700">
              Current: <span className="font-medium">{formatCurrency(data.current_price)}</span>
            </p>
            <p className="text-gray-700">
              Market Value: <span className="font-medium">{formatCurrency(data.market_value)}</span>
            </p>
            <p className={`font-bold ${data.unrealized_pnl >= 0 ? 'text-green-600' : 'text-red-600'}`}>
              P&L: {formatCurrency(data.unrealized_pnl)} ({data.unrealized_pnl_pct.toFixed(2)}%)
            </p>
          </div>
        </div>
      );
    }
    return null;
  };

  // Calculate total unrealized P&L
  const totalUnrealizedPnL = sortedData.reduce((sum, pos) => sum + pos.unrealized_pnl, 0);

  return (
    <div className="bg-white rounded-lg shadow-sm p-6">
      <div className="flex items-center justify-between mb-4">
        <h3 className="text-lg font-semibold text-gray-900">Current Positions P&L</h3>
        <div className="text-right">
          <p className="text-sm text-gray-600">Total Unrealized</p>
          <p
            className={`text-xl font-bold ${
              totalUnrealizedPnL >= 0 ? 'text-green-600' : 'text-red-600'
            }`}
          >
            {formatCurrency(totalUnrealizedPnL)}
          </p>
        </div>
      </div>

      <ResponsiveContainer width="100%" height={400}>
        <BarChart
          data={sortedData}
          layout="vertical"
          margin={{ top: 5, right: 30, left: 20, bottom: 5 }}
        >
          <CartesianGrid strokeDasharray="3 3" stroke="#e5e7eb" />
          <XAxis
            type="number"
            stroke="#6b7280"
            tick={{ fill: '#6b7280', fontSize: 12 }}
            tickFormatter={(value) => `$${value.toFixed(0)}`}
          />
          <YAxis
            type="category"
            dataKey="symbol"
            stroke="#6b7280"
            tick={{ fill: '#6b7280', fontSize: 12 }}
          />
          <Tooltip content={<CustomTooltip />} />
          <Bar dataKey="unrealized_pnl" name="Unrealized P&L" radius={[0, 4, 4, 0]}>
            {sortedData.map((entry, index) => (
              <Cell
                key={`cell-${index}`}
                fill={entry.unrealized_pnl >= 0 ? '#16a34a' : '#dc2626'}
              />
            ))}
          </Bar>
        </BarChart>
      </ResponsiveContainer>

      <div className="mt-6 space-y-2">
        {sortedData.map((position) => (
          <div
            key={position.symbol}
            className="flex items-center justify-between p-3 bg-gray-50 rounded-lg hover:bg-gray-100 transition-colors"
          >
            <div className="flex items-center gap-3">
              <span className="font-semibold text-gray-900">{position.symbol}</span>
              <span className="text-sm text-gray-600">
                {position.qty} shares @ {formatCurrency(position.avg_entry_price)}
              </span>
            </div>
            <div className="flex items-center gap-4">
              <span className="text-sm text-gray-600">
                Current: {formatCurrency(position.current_price)}
              </span>
              <span
                className={`font-bold ${
                  position.unrealized_pnl >= 0 ? 'text-green-600' : 'text-red-600'
                }`}
              >
                {formatCurrency(position.unrealized_pnl)} ({position.unrealized_pnl_pct.toFixed(2)}
                %)
              </span>
            </div>
          </div>
        ))}
      </div>
    </div>
  );
}
