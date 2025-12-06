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
} from 'recharts';
import type { TradeDistributionBucket } from '../../types/analytics';

interface TradeDistributionChartProps {
  data: TradeDistributionBucket[];
  loading?: boolean;
  error?: string | null;
}

export function TradeDistributionChart({ data, loading, error }: TradeDistributionChartProps) {
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
        <h3 className="text-lg font-semibold text-red-800 mb-2">Error Loading Distribution Data</h3>
        <p className="text-red-600 text-sm">{error}</p>
      </div>
    );
  }

  if (!data || data.length === 0) {
    return (
      <div className="bg-white rounded-lg shadow-sm p-6">
        <h3 className="text-lg font-semibold text-gray-900 mb-4">P&L Distribution</h3>
        <div className="h-80 flex items-center justify-center bg-gray-50 rounded">
          <p className="text-gray-500">No trade distribution data available</p>
        </div>
      </div>
    );
  }

  // Custom tooltip
  const CustomTooltip = ({ active, payload }: any) => {
    if (active && payload && payload.length) {
      const data = payload[0].payload;
      return (
        <div className="bg-white p-4 border border-gray-200 rounded-lg shadow-lg">
          <p className="font-medium text-gray-900 mb-2">{data.bucket_label}</p>
          <p className="text-sm text-gray-700">
            Trades: <span className="font-medium">{data.trade_count}</span>
          </p>
        </div>
      );
    }
    return null;
  };

  // Determine color based on bucket (loss vs win)
  const getBarColor = (bucket: TradeDistributionBucket) => {
    if (bucket.max_pnl !== null && bucket.max_pnl <= 0) {
      return '#dc2626'; // red-600 for loss buckets
    } else if (bucket.min_pnl !== null && bucket.min_pnl >= 0) {
      return '#16a34a'; // green-600 for win buckets
    }
    return '#6b7280'; // gray-600 for break-even
  };

  // Calculate statistics
  const totalTrades = data.reduce((sum, bucket) => sum + bucket.trade_count, 0);
  const lossBuckets = data.filter(b => b.max_pnl !== null && b.max_pnl <= 0);
  const winBuckets = data.filter(b => b.min_pnl !== null && b.min_pnl >= 0);
  const totalLosses = lossBuckets.reduce((sum, b) => sum + b.trade_count, 0);
  const totalWins = winBuckets.reduce((sum, b) => sum + b.trade_count, 0);

  // Shorten labels for better display
  const formatLabel = (label: string) => {
    return label
      .replace('Heavy Loss ', '<-$100')
      .replace('Loss ', '-$100-$50')
      .replace('Small Loss ', '-$50-$0')
      .replace('Small Win ', '$0-$50')
      .replace('Win ', '$50-$100')
      .replace('Large Win ', '>$100');
  };

  return (
    <div className="bg-white rounded-lg shadow-sm p-6">
      <div className="flex items-center justify-between mb-4">
        <h3 className="text-lg font-semibold text-gray-900">P&L Distribution</h3>
        <div className="text-right">
          <p className="text-sm text-gray-600">Total Trades</p>
          <p className="text-xl font-bold text-gray-900">{totalTrades}</p>
        </div>
      </div>

      <ResponsiveContainer width="100%" height={400}>
        <BarChart data={data} margin={{ top: 5, right: 30, left: 20, bottom: 60 }}>
          <CartesianGrid strokeDasharray="3 3" stroke="#e5e7eb" />
          <XAxis
            dataKey="bucket_label"
            stroke="#6b7280"
            tick={{ fill: '#6b7280', fontSize: 11 }}
            tickFormatter={formatLabel}
            angle={-45}
            textAnchor="end"
            height={80}
          />
          <YAxis
            stroke="#6b7280"
            tick={{ fill: '#6b7280', fontSize: 12 }}
            label={{ value: 'Number of Trades', angle: -90, position: 'insideLeft', fill: '#6b7280' }}
          />
          <Tooltip content={<CustomTooltip />} />
          <Bar dataKey="trade_count" name="Trades" radius={[4, 4, 0, 0]}>
            {data.map((entry, index) => (
              <Cell key={`cell-${index}`} fill={getBarColor(entry)} />
            ))}
          </Bar>
        </BarChart>
      </ResponsiveContainer>

      {/* Statistics */}
      <div className="mt-6 grid grid-cols-3 gap-4">
        <div className="bg-red-50 rounded-lg p-4 border border-red-200">
          <p className="text-sm text-red-600 mb-1">Losing Trades</p>
          <p className="text-2xl font-bold text-red-700">{totalLosses}</p>
          <p className="text-xs text-red-600 mt-1">
            {totalTrades > 0 ? ((totalLosses / totalTrades) * 100).toFixed(1) : 0}% of total
          </p>
        </div>

        <div className="bg-gray-50 rounded-lg p-4 border border-gray-200">
          <p className="text-sm text-gray-600 mb-1">Total Trades</p>
          <p className="text-2xl font-bold text-gray-900">{totalTrades}</p>
          <p className="text-xs text-gray-600 mt-1">All closed trades</p>
        </div>

        <div className="bg-green-50 rounded-lg p-4 border border-green-200">
          <p className="text-sm text-green-600 mb-1">Winning Trades</p>
          <p className="text-2xl font-bold text-green-700">{totalWins}</p>
          <p className="text-xs text-green-600 mt-1">
            {totalTrades > 0 ? ((totalWins / totalTrades) * 100).toFixed(1) : 0}% of total
          </p>
        </div>
      </div>

      {/* Legend */}
      <div className="mt-4 flex flex-wrap gap-4 text-sm text-gray-600">
        <div className="flex items-center gap-2">
          <div className="w-4 h-4 rounded bg-red-600"></div>
          <span>Loss Buckets</span>
        </div>
        <div className="flex items-center gap-2">
          <div className="w-4 h-4 rounded bg-green-600"></div>
          <span>Win Buckets</span>
        </div>
      </div>
    </div>
  );
}
