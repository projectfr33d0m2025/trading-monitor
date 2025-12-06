import React, { useState } from 'react';
import {
  BarChart,
  Bar,
  XAxis,
  YAxis,
  CartesianGrid,
  Tooltip,
  ResponsiveContainer,
  Cell,
  ReferenceLine,
} from 'recharts';
import type { PnLByPeriodDataPoint } from '../../types/analytics';

interface PnLBarChartProps {
  dailyData: PnLByPeriodDataPoint[];
  weeklyData: PnLByPeriodDataPoint[];
  monthlyData: PnLByPeriodDataPoint[];
  loading?: boolean;
  error?: string | null;
}

type PeriodType = 'daily' | 'weekly' | 'monthly';

export function PnLBarChart({ dailyData, weeklyData, monthlyData, loading, error }: PnLBarChartProps) {
  const [selectedPeriod, setSelectedPeriod] = useState<PeriodType>('daily');

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
        <h3 className="text-lg font-semibold text-red-800 mb-2">Error Loading P&L Data</h3>
        <p className="text-red-600 text-sm">{error}</p>
      </div>
    );
  }

  // Select data based on period
  const dataMap = {
    daily: dailyData,
    weekly: weeklyData,
    monthly: monthlyData,
  };

  const data = dataMap[selectedPeriod] || [];

  if (data.length === 0) {
    return (
      <div className="bg-white rounded-lg shadow-sm p-6">
        <h3 className="text-lg font-semibold text-gray-900 mb-4">P&L by Period</h3>
        <div className="h-80 flex items-center justify-center bg-gray-50 rounded">
          <p className="text-gray-500">No P&L data available for the selected period</p>
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

  // Format date based on period
  const formatDate = (dateStr: string, period: PeriodType) => {
    const date = new Date(dateStr);
    if (period === 'monthly') {
      return date.toLocaleDateString('en-US', { month: 'short', year: 'numeric' });
    } else if (period === 'weekly') {
      return date.toLocaleDateString('en-US', { month: 'short', day: 'numeric' });
    } else {
      return date.toLocaleDateString('en-US', { month: 'short', day: 'numeric' });
    }
  };

  // Custom tooltip
  const CustomTooltip = ({ active, payload }: any) => {
    if (active && payload && payload.length) {
      const data = payload[0].payload;
      return (
        <div className="bg-white p-4 border border-gray-200 rounded-lg shadow-lg">
          <p className="font-medium text-gray-900 mb-2">
            {formatDate(data.period, selectedPeriod)}
          </p>
          <div className="space-y-1 text-sm">
            <p className="text-gray-700">
              Realized P&L: <span className="font-medium">{formatCurrency(data.realized_pnl)}</span>
            </p>
            <p className={`font-bold ${data.total_pnl >= 0 ? 'text-green-600' : 'text-red-600'}`}>
              Total P&L: {formatCurrency(data.total_pnl)}
            </p>
          </div>
        </div>
      );
    }
    return null;
  };

  // Calculate total P&L
  const totalPnL = data.reduce((sum, item) => sum + item.total_pnl, 0);

  return (
    <div className="bg-white rounded-lg shadow-sm p-6">
      <div className="flex items-center justify-between mb-4">
        <h3 className="text-lg font-semibold text-gray-900">P&L by Period</h3>
        <div className="text-right">
          <p className="text-sm text-gray-600">Total</p>
          <p className={`text-xl font-bold ${totalPnL >= 0 ? 'text-green-600' : 'text-red-600'}`}>
            {formatCurrency(totalPnL)}
          </p>
        </div>
      </div>

      {/* Period Selector */}
      <div className="flex gap-2 mb-4">
        {(['daily', 'weekly', 'monthly'] as PeriodType[]).map((period) => (
          <button
            key={period}
            onClick={() => setSelectedPeriod(period)}
            className={`px-4 py-2 rounded-md text-sm font-medium transition-colors capitalize ${
              selectedPeriod === period
                ? 'bg-blue-600 text-white'
                : 'bg-gray-100 text-gray-700 hover:bg-gray-200'
            }`}
          >
            {period}
          </button>
        ))}
      </div>

      <ResponsiveContainer width="100%" height={400}>
        <BarChart data={data} margin={{ top: 5, right: 30, left: 20, bottom: 5 }}>
          <CartesianGrid strokeDasharray="3 3" stroke="#e5e7eb" />
          <XAxis
            dataKey="period"
            stroke="#6b7280"
            tick={{ fill: '#6b7280', fontSize: 12 }}
            tickFormatter={(value) => formatDate(value, selectedPeriod)}
          />
          <YAxis
            stroke="#6b7280"
            tick={{ fill: '#6b7280', fontSize: 12 }}
            tickFormatter={(value) => `$${value.toFixed(0)}`}
          />
          <Tooltip content={<CustomTooltip />} />
          <ReferenceLine
            y={0}
            stroke="#9ca3af"
            strokeDasharray="3 3"
            label={{ value: 'Break Even', position: 'insideTopLeft', fill: '#6b7280', fontSize: 12 }}
          />
          <Bar dataKey="total_pnl" name="Total P&L" radius={[4, 4, 0, 0]}>
            {data.map((entry, index) => (
              <Cell key={`cell-${index}`} fill={entry.total_pnl >= 0 ? '#16a34a' : '#dc2626'} />
            ))}
          </Bar>
        </BarChart>
      </ResponsiveContainer>

      <div className="mt-4 grid grid-cols-3 gap-4 text-sm">
        <div className="text-center">
          <p className="text-gray-600">Periods</p>
          <p className="font-semibold text-gray-900">{data.length}</p>
        </div>
        <div className="text-center">
          <p className="text-gray-600">Profitable</p>
          <p className="font-semibold text-green-600">
            {data.filter((d) => d.total_pnl > 0).length}
          </p>
        </div>
        <div className="text-center">
          <p className="text-gray-600">Loss</p>
          <p className="font-semibold text-red-600">
            {data.filter((d) => d.total_pnl < 0).length}
          </p>
        </div>
      </div>
    </div>
  );
}
