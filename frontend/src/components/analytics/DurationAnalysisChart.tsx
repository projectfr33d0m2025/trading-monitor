import React from 'react';
import {
  ScatterChart,
  Scatter,
  XAxis,
  YAxis,
  CartesianGrid,
  Tooltip,
  ResponsiveContainer,
  ReferenceLine,
  ZAxis,
} from 'recharts';
import type { DurationAnalysisDataPoint } from '../../types/analytics';

interface DurationAnalysisChartProps {
  data: DurationAnalysisDataPoint[];
  loading?: boolean;
  error?: string | null;
}

export function DurationAnalysisChart({ data, loading, error }: DurationAnalysisChartProps) {
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
        <h3 className="text-lg font-semibold text-red-800 mb-2">Error Loading Duration Data</h3>
        <p className="text-red-600 text-sm">{error}</p>
      </div>
    );
  }

  if (!data || data.length === 0) {
    return (
      <div className="bg-white rounded-lg shadow-sm p-6">
        <h3 className="text-lg font-semibold text-gray-900 mb-4">Trade Duration Analysis</h3>
        <div className="h-80 flex items-center justify-center bg-gray-50 rounded">
          <p className="text-gray-500">No duration data available for closed trades</p>
        </div>
      </div>
    );
  }

  // Format currency
  const formatCurrency = (value: number) => {
    return new Intl.NumberFormat('en-US', {
      style: 'currency',
      currency: 'USD',
      minimumFractionDigits: 2,
      maximumFractionDigits: 2,
    }).format(value);
  };

  // Separate winners and losers
  const winners = data.filter((d) => d.is_winner);
  const losers = data.filter((d) => !d.is_winner);

  // Custom tooltip
  const CustomTooltip = ({ active, payload }: any) => {
    if (active && payload && payload.length) {
      const data = payload[0].payload;
      return (
        <div className="bg-white p-4 border border-gray-200 rounded-lg shadow-lg">
          <p className="font-bold text-gray-900 mb-2">{data.symbol}</p>
          <div className="space-y-1 text-sm">
            <p className="text-gray-700">
              Days Held: <span className="font-medium">{data.days_open}</span>
            </p>
            <p className={`font-bold ${data.is_winner ? 'text-green-600' : 'text-red-600'}`}>
              P&L: {formatCurrency(data.actual_pnl)}
            </p>
          </div>
        </div>
      );
    }
    return null;
  };

  // Calculate statistics
  const avgDaysWinner = winners.length > 0
    ? winners.reduce((sum, w) => sum + w.days_open, 0) / winners.length
    : 0;
  const avgDaysLoser = losers.length > 0
    ? losers.reduce((sum, l) => sum + l.days_open, 0) / losers.length
    : 0;

  return (
    <div className="bg-white rounded-lg shadow-sm p-6">
      <div className="flex items-center justify-between mb-4">
        <h3 className="text-lg font-semibold text-gray-900">Trade Duration Analysis</h3>
        <div className="text-right">
          <p className="text-sm text-gray-600">Total Trades</p>
          <p className="text-xl font-bold text-gray-900">{data.length}</p>
        </div>
      </div>

      <ResponsiveContainer width="100%" height={400}>
        <ScatterChart margin={{ top: 20, right: 30, bottom: 20, left: 20 }}>
          <CartesianGrid strokeDasharray="3 3" stroke="#e5e7eb" />
          <XAxis
            type="number"
            dataKey="days_open"
            name="Days Held"
            stroke="#6b7280"
            tick={{ fill: '#6b7280', fontSize: 12 }}
            label={{ value: 'Days Held', position: 'insideBottom', offset: -10, fill: '#6b7280' }}
          />
          <YAxis
            type="number"
            dataKey="actual_pnl"
            name="P&L"
            stroke="#6b7280"
            tick={{ fill: '#6b7280', fontSize: 12 }}
            tickFormatter={(value) => `$${value.toFixed(0)}`}
            label={{ value: 'P&L ($)', angle: -90, position: 'insideLeft', fill: '#6b7280' }}
          />
          <ZAxis range={[100, 100]} />
          <Tooltip content={<CustomTooltip />} cursor={{ strokeDasharray: '3 3' }} />
          <ReferenceLine
            y={0}
            stroke="#9ca3af"
            strokeDasharray="3 3"
            label={{ value: 'Break Even', position: 'right', fill: '#6b7280', fontSize: 12 }}
          />
          {/* Winners */}
          <Scatter
            name="Winning Trades"
            data={winners}
            fill="#16a34a"
            shape="circle"
          />
          {/* Losers */}
          <Scatter
            name="Losing Trades"
            data={losers}
            fill="#dc2626"
            shape="circle"
          />
        </ScatterChart>
      </ResponsiveContainer>

      {/* Statistics */}
      <div className="mt-6 grid grid-cols-2 md:grid-cols-4 gap-4">
        <div className="bg-green-50 rounded-lg p-4 border border-green-200">
          <p className="text-xs text-green-600 mb-1">Winners</p>
          <p className="text-2xl font-bold text-green-700">{winners.length}</p>
          <p className="text-xs text-green-600 mt-1">
            Avg: {avgDaysWinner.toFixed(1)} days
          </p>
        </div>

        <div className="bg-red-50 rounded-lg p-4 border border-red-200">
          <p className="text-xs text-red-600 mb-1">Losers</p>
          <p className="text-2xl font-bold text-red-700">{losers.length}</p>
          <p className="text-xs text-red-600 mt-1">
            Avg: {avgDaysLoser.toFixed(1)} days
          </p>
        </div>

        <div className="bg-blue-50 rounded-lg p-4 border border-blue-200">
          <p className="text-xs text-blue-600 mb-1">Longest Hold</p>
          <p className="text-2xl font-bold text-blue-700">
            {Math.max(...data.map((d) => d.days_open))}
          </p>
          <p className="text-xs text-blue-600 mt-1">days</p>
        </div>

        <div className="bg-gray-50 rounded-lg p-4 border border-gray-200">
          <p className="text-xs text-gray-600 mb-1">Shortest Hold</p>
          <p className="text-2xl font-bold text-gray-700">
            {Math.min(...data.map((d) => d.days_open))}
          </p>
          <p className="text-xs text-gray-600 mt-1">days</p>
        </div>
      </div>

      {/* Legend */}
      <div className="mt-4 flex flex-wrap gap-4 text-sm text-gray-600">
        <div className="flex items-center gap-2">
          <div className="w-4 h-4 rounded-full bg-green-600"></div>
          <span>Winning Trades</span>
        </div>
        <div className="flex items-center gap-2">
          <div className="w-4 h-4 rounded-full bg-red-600"></div>
          <span>Losing Trades</span>
        </div>
      </div>

      {/* Insights */}
      {winners.length > 0 && losers.length > 0 && (
        <div className="mt-4 p-4 bg-blue-50 rounded-lg border border-blue-200">
          <p className="text-sm text-blue-900">
            <span className="font-semibold">Insight:</span>{' '}
            {avgDaysWinner > avgDaysLoser
              ? `Winners are held ${(avgDaysWinner - avgDaysLoser).toFixed(1)} days longer on average than losers.`
              : `Losers are held ${(avgDaysLoser - avgDaysWinner).toFixed(1)} days longer on average than winners.`}
          </p>
        </div>
      )}
    </div>
  );
}
