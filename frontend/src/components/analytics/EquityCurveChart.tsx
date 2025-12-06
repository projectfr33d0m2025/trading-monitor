import React from 'react';
import {
  LineChart,
  Line,
  XAxis,
  YAxis,
  CartesianGrid,
  Tooltip,
  Legend,
  ResponsiveContainer,
  ReferenceLine,
} from 'recharts';
import type { EquityCurveDataPoint } from '../../types/analytics';

interface EquityCurveChartProps {
  data: EquityCurveDataPoint[];
  loading?: boolean;
  error?: string | null;
}

export function EquityCurveChart({ data, loading, error }: EquityCurveChartProps) {
  if (loading) {
    return (
      <div className="bg-white rounded-lg shadow-sm p-6 mb-6">
        <div className="h-8 bg-gray-200 rounded w-1/3 mb-4 animate-pulse"></div>
        <div className="h-80 bg-gray-100 rounded animate-pulse"></div>
      </div>
    );
  }

  if (error) {
    return (
      <div className="bg-red-50 border border-red-200 rounded-lg p-6 mb-6">
        <h3 className="text-lg font-semibold text-red-800 mb-2">Error Loading Equity Curve</h3>
        <p className="text-red-600 text-sm">{error}</p>
      </div>
    );
  }

  if (!data || data.length === 0) {
    return (
      <div className="bg-white rounded-lg shadow-sm p-6 mb-6">
        <h3 className="text-lg font-semibold text-gray-900 mb-4">Equity Curve</h3>
        <div className="h-80 flex items-center justify-center bg-gray-50 rounded">
          <p className="text-gray-500">No trade data available for the selected period</p>
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

  // Custom tooltip
  const CustomTooltip = ({ active, payload, label }: any) => {
    if (active && payload && payload.length) {
      return (
        <div className="bg-white p-4 border border-gray-200 rounded-lg shadow-lg">
          <p className="font-medium text-gray-900 mb-2">{label}</p>
          {payload.map((entry: any, index: number) => (
            <p key={index} className="text-sm" style={{ color: entry.color }}>
              {entry.name}: {formatCurrency(entry.value)}
            </p>
          ))}
        </div>
      );
    }
    return null;
  };

  // Determine if overall P&L is positive or negative
  const finalPnL = data[data.length - 1]?.cumulative_pnl || 0;
  const lineColor = finalPnL >= 0 ? '#16a34a' : '#dc2626'; // green-600 or red-600

  return (
    <div className="bg-white rounded-lg shadow-sm p-6 mb-6">
      <div className="flex items-center justify-between mb-4">
        <h3 className="text-lg font-semibold text-gray-900">Equity Curve</h3>
        <div className="text-right">
          <p className="text-sm text-gray-600">Total P&L</p>
          <p className={`text-xl font-bold ${finalPnL >= 0 ? 'text-green-600' : 'text-red-600'}`}>
            {formatCurrency(finalPnL)}
          </p>
        </div>
      </div>

      <ResponsiveContainer width="100%" height={400}>
        <LineChart
          data={data}
          margin={{ top: 5, right: 30, left: 20, bottom: 5 }}
        >
          <CartesianGrid strokeDasharray="3 3" stroke="#e5e7eb" />
          <XAxis
            dataKey="date"
            stroke="#6b7280"
            tick={{ fill: '#6b7280', fontSize: 12 }}
          />
          <YAxis
            stroke="#6b7280"
            tick={{ fill: '#6b7280', fontSize: 12 }}
            tickFormatter={(value) => `$${value.toFixed(0)}`}
          />
          <Tooltip content={<CustomTooltip />} />
          <Legend
            wrapperStyle={{ paddingTop: '20px' }}
            iconType="line"
          />
          <ReferenceLine
            y={0}
            stroke="#9ca3af"
            strokeDasharray="3 3"
            label={{ value: 'Break Even', position: 'insideTopLeft', fill: '#6b7280', fontSize: 12 }}
          />
          <Line
            type="monotone"
            dataKey="cumulative_pnl"
            name="Cumulative P&L"
            stroke={lineColor}
            strokeWidth={3}
            dot={{ fill: lineColor, r: 4 }}
            activeDot={{ r: 6 }}
          />
        </LineChart>
      </ResponsiveContainer>

      <div className="mt-4 flex flex-wrap gap-4 text-sm text-gray-600">
        <div className="flex items-center gap-2">
          <div className="w-3 h-3 rounded-full bg-green-600"></div>
          <span>Profitable</span>
        </div>
        <div className="flex items-center gap-2">
          <div className="w-3 h-3 rounded-full bg-red-600"></div>
          <span>Loss</span>
        </div>
        <div className="flex items-center gap-2">
          <div className="w-8 h-0.5 bg-gray-400 border-dashed"></div>
          <span>Break Even</span>
        </div>
      </div>
    </div>
  );
}
