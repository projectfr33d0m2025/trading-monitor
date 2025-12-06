import React from 'react';
import type { PerformanceMetrics } from '../../types/analytics';

interface PerformanceMetricsCardsProps {
  metrics: PerformanceMetrics | null;
  loading?: boolean;
  error?: string | null;
}

export function PerformanceMetricsCards({ metrics, loading, error }: PerformanceMetricsCardsProps) {
  if (loading) {
    return (
      <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-6 mb-6">
        {[...Array(4)].map((_, i) => (
          <div key={i} className="bg-white rounded-lg shadow-sm p-6 animate-pulse">
            <div className="h-4 bg-gray-200 rounded w-1/2 mb-4"></div>
            <div className="h-8 bg-gray-200 rounded w-3/4"></div>
          </div>
        ))}
      </div>
    );
  }

  if (error) {
    return (
      <div className="bg-red-50 border border-red-200 rounded-lg p-4 mb-6">
        <p className="text-red-800 text-sm">{error}</p>
      </div>
    );
  }

  if (!metrics) {
    return null;
  }

  const formatCurrency = (value: number) => {
    return new Intl.NumberFormat('en-US', {
      style: 'currency',
      currency: 'USD',
      minimumFractionDigits: 2,
      maximumFractionDigits: 2,
    }).format(value);
  };

  const formatPercent = (value: number) => {
    return `${value.toFixed(2)}%`;
  };

  const cards = [
    {
      label: 'Win Rate',
      value: formatPercent(metrics.win_rate),
      subValue: `${metrics.winning_trades} / ${metrics.total_trades} trades`,
      colorClass: metrics.win_rate >= 50 ? 'text-green-600' : 'text-red-600',
      bgClass: metrics.win_rate >= 50 ? 'bg-green-50' : 'bg-red-50',
      borderClass: metrics.win_rate >= 50 ? 'border-green-200' : 'border-red-200',
    },
    {
      label: 'Average Win',
      value: formatCurrency(metrics.avg_win),
      subValue: metrics.winning_trades > 0 ? `${metrics.winning_trades} winners` : 'No winners yet',
      colorClass: 'text-green-600',
      bgClass: 'bg-green-50',
      borderClass: 'border-green-200',
    },
    {
      label: 'Average Loss',
      value: formatCurrency(metrics.avg_loss),
      subValue: metrics.losing_trades > 0 ? `${metrics.losing_trades} losers` : 'No losers yet',
      colorClass: 'text-red-600',
      bgClass: 'bg-red-50',
      borderClass: 'border-red-200',
    },
    {
      label: 'Profit Factor',
      value: metrics.profit_factor.toFixed(2),
      subValue:
        metrics.profit_factor > 0
          ? `${formatCurrency(metrics.total_wins)} / ${formatCurrency(metrics.total_losses)}`
          : 'N/A',
      colorClass: metrics.profit_factor >= 2 ? 'text-green-600' : metrics.profit_factor >= 1 ? 'text-blue-600' : 'text-red-600',
      bgClass: metrics.profit_factor >= 2 ? 'bg-green-50' : metrics.profit_factor >= 1 ? 'bg-blue-50' : 'bg-red-50',
      borderClass: metrics.profit_factor >= 2 ? 'border-green-200' : metrics.profit_factor >= 1 ? 'border-blue-200' : 'border-red-200',
    },
  ];

  const detailCards = [
    {
      label: 'Largest Win',
      value: formatCurrency(metrics.largest_win),
      colorClass: 'text-green-600',
      bgClass: 'bg-green-50',
      borderClass: 'border-green-200',
    },
    {
      label: 'Largest Loss',
      value: formatCurrency(metrics.largest_loss),
      colorClass: 'text-red-600',
      bgClass: 'bg-red-50',
      borderClass: 'border-red-200',
    },
    {
      label: 'Total P&L',
      value: formatCurrency(metrics.total_pnl),
      subValue: `${metrics.total_trades} closed trades`,
      colorClass: metrics.total_pnl >= 0 ? 'text-green-600' : 'text-red-600',
      bgClass: metrics.total_pnl >= 0 ? 'bg-green-50' : 'bg-red-50',
      borderClass: metrics.total_pnl >= 0 ? 'border-green-200' : 'border-red-200',
    },
  ];

  return (
    <div className="space-y-6 mb-6">
      {/* Primary Metrics */}
      <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-6">
        {cards.map((card, index) => (
          <div
            key={index}
            className={`rounded-lg shadow-sm p-6 border ${card.bgClass} ${card.borderClass}`}
          >
            <div className="flex items-start justify-between">
              <div className="flex-1">
                <p className="text-sm font-medium text-gray-600 mb-1">{card.label}</p>
                <p className={`text-3xl font-bold ${card.colorClass} mb-1`}>{card.value}</p>
                {card.subValue && <p className="text-xs text-gray-500">{card.subValue}</p>}
              </div>
            </div>
          </div>
        ))}
      </div>

      {/* Detail Metrics */}
      <div className="grid grid-cols-1 md:grid-cols-3 gap-6">
        {detailCards.map((card, index) => (
          <div
            key={index}
            className={`rounded-lg shadow-sm p-6 border ${card.bgClass} ${card.borderClass}`}
          >
            <p className="text-sm font-medium text-gray-600 mb-1">{card.label}</p>
            <p className={`text-2xl font-bold ${card.colorClass} mb-1`}>{card.value}</p>
            {card.subValue && <p className="text-xs text-gray-500">{card.subValue}</p>}
          </div>
        ))}
      </div>
    </div>
  );
}
