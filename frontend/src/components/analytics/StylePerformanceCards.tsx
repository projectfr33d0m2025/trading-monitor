import React from 'react';
import type { StylePerformance } from '../../types/analytics';

interface StylePerformanceCardsProps {
  data: StylePerformance[];
  loading?: boolean;
  error?: string | null;
}

export function StylePerformanceCards({ data, loading, error }: StylePerformanceCardsProps) {
  if (loading) {
    return (
      <div className="bg-white rounded-lg shadow-sm p-6">
        <div className="h-6 bg-gray-200 rounded w-1/3 mb-4 animate-pulse"></div>
        <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
          {[...Array(2)].map((_, i) => (
            <div key={i} className="h-48 bg-gray-100 rounded animate-pulse"></div>
          ))}
        </div>
      </div>
    );
  }

  if (error) {
    return (
      <div className="bg-red-50 border border-red-200 rounded-lg p-6">
        <h3 className="text-lg font-semibold text-red-800 mb-2">Error Loading Style Data</h3>
        <p className="text-red-600 text-sm">{error}</p>
      </div>
    );
  }

  if (!data || data.length === 0) {
    return (
      <div className="bg-white rounded-lg shadow-sm p-6">
        <h3 className="text-lg font-semibold text-gray-900 mb-4">Trade Performance by Style</h3>
        <div className="h-40 flex items-center justify-center bg-gray-50 rounded">
          <p className="text-gray-500">No trade style data available</p>
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

  // Create style map
  const styleMap: { [key: string]: StylePerformance } = {};
  data.forEach((style) => {
    styleMap[style.trade_style] = style;
  });

  const swing = styleMap['SWING'];
  const trend = styleMap['TREND'];

  // Calculate totals
  const totalTrades = data.reduce((sum, s) => sum + s.trade_count, 0);
  const totalPnL = data.reduce((sum, s) => sum + s.total_pnl, 0);

  return (
    <div className="bg-white rounded-lg shadow-sm p-6">
      <div className="flex items-center justify-between mb-6">
        <h3 className="text-lg font-semibold text-gray-900">Trade Performance by Style</h3>
        <div className="text-right">
          <p className="text-sm text-gray-600">Combined Total</p>
          <p className={`text-xl font-bold ${totalPnL >= 0 ? 'text-green-600' : 'text-red-600'}`}>
            {formatCurrency(totalPnL)}
          </p>
        </div>
      </div>

      <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
        {/* SWING Style */}
        {swing && (
          <div className="border-2 border-blue-200 rounded-lg p-6 bg-blue-50">
            <div className="flex items-center justify-between mb-4">
              <h4 className="text-xl font-bold text-blue-900">SWING Trading</h4>
              <div className="px-3 py-1 bg-blue-600 text-white rounded-full text-sm font-medium">
                {swing.trade_count} trades
              </div>
            </div>

            <div className="space-y-4">
              <div className="flex justify-between items-center pb-3 border-b border-blue-200">
                <span className="text-sm text-blue-700">Win Rate</span>
                <span
                  className={`text-lg font-bold ${
                    swing.win_rate >= 50 ? 'text-green-600' : 'text-red-600'
                  }`}
                >
                  {swing.win_rate.toFixed(2)}%
                </span>
              </div>

              <div className="flex justify-between items-center pb-3 border-b border-blue-200">
                <span className="text-sm text-blue-700">Average P&L</span>
                <span
                  className={`text-lg font-bold ${
                    swing.avg_pnl >= 0 ? 'text-green-600' : 'text-red-600'
                  }`}
                >
                  {formatCurrency(swing.avg_pnl)}
                </span>
              </div>

              <div className="flex justify-between items-center">
                <span className="text-sm text-blue-700">Total P&L</span>
                <span
                  className={`text-2xl font-bold ${
                    swing.total_pnl >= 0 ? 'text-green-600' : 'text-red-600'
                  }`}
                >
                  {formatCurrency(swing.total_pnl)}
                </span>
              </div>
            </div>

            <div className="mt-4 text-xs text-blue-600">
              {((swing.trade_count / totalTrades) * 100).toFixed(1)}% of total trades
            </div>
          </div>
        )}

        {/* TREND Style */}
        {trend && (
          <div className="border-2 border-purple-200 rounded-lg p-6 bg-purple-50">
            <div className="flex items-center justify-between mb-4">
              <h4 className="text-xl font-bold text-purple-900">TREND Following</h4>
              <div className="px-3 py-1 bg-purple-600 text-white rounded-full text-sm font-medium">
                {trend.trade_count} trades
              </div>
            </div>

            <div className="space-y-4">
              <div className="flex justify-between items-center pb-3 border-b border-purple-200">
                <span className="text-sm text-purple-700">Win Rate</span>
                <span
                  className={`text-lg font-bold ${
                    trend.win_rate >= 50 ? 'text-green-600' : 'text-red-600'
                  }`}
                >
                  {trend.win_rate.toFixed(2)}%
                </span>
              </div>

              <div className="flex justify-between items-center pb-3 border-b border-purple-200">
                <span className="text-sm text-purple-700">Average P&L</span>
                <span
                  className={`text-lg font-bold ${
                    trend.avg_pnl >= 0 ? 'text-green-600' : 'text-red-600'
                  }`}
                >
                  {formatCurrency(trend.avg_pnl)}
                </span>
              </div>

              <div className="flex justify-between items-center">
                <span className="text-sm text-purple-700">Total P&L</span>
                <span
                  className={`text-2xl font-bold ${
                    trend.total_pnl >= 0 ? 'text-green-600' : 'text-red-600'
                  }`}
                >
                  {formatCurrency(trend.total_pnl)}
                </span>
              </div>
            </div>

            <div className="mt-4 text-xs text-purple-600">
              {((trend.trade_count / totalTrades) * 100).toFixed(1)}% of total trades
            </div>
          </div>
        )}
      </div>

      {/* Comparison */}
      {swing && trend && (
        <div className="mt-6 p-4 bg-gray-50 rounded-lg">
          <h5 className="text-sm font-semibold text-gray-700 mb-3">Performance Comparison</h5>
          <div className="grid grid-cols-3 gap-4 text-center">
            <div>
              <p className="text-xs text-gray-600 mb-1">Better Win Rate</p>
              <p className={`font-bold ${swing.win_rate > trend.win_rate ? 'text-blue-600' : 'text-purple-600'}`}>
                {swing.win_rate > trend.win_rate ? 'SWING' : 'TREND'}
              </p>
            </div>
            <div>
              <p className="text-xs text-gray-600 mb-1">Better Avg P&L</p>
              <p className={`font-bold ${swing.avg_pnl > trend.avg_pnl ? 'text-blue-600' : 'text-purple-600'}`}>
                {swing.avg_pnl > trend.avg_pnl ? 'SWING' : 'TREND'}
              </p>
            </div>
            <div>
              <p className="text-xs text-gray-600 mb-1">Higher Total P&L</p>
              <p className={`font-bold ${swing.total_pnl > trend.total_pnl ? 'text-blue-600' : 'text-purple-600'}`}>
                {swing.total_pnl > trend.total_pnl ? 'SWING' : 'TREND'}
              </p>
            </div>
          </div>
        </div>
      )}
    </div>
  );
}
