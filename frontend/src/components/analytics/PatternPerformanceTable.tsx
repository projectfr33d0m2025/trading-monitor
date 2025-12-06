import React, { useState } from 'react';
import type { PatternPerformance } from '../../types/analytics';

interface PatternPerformanceTableProps {
  data: PatternPerformance[];
  loading?: boolean;
  error?: string | null;
}

type SortField = 'pattern' | 'trade_count' | 'win_rate' | 'avg_pnl' | 'total_pnl';
type SortDirection = 'asc' | 'desc';

export function PatternPerformanceTable({ data, loading, error }: PatternPerformanceTableProps) {
  const [sortField, setSortField] = useState<SortField>('total_pnl');
  const [sortDirection, setSortDirection] = useState<SortDirection>('desc');

  if (loading) {
    return (
      <div className="bg-white rounded-lg shadow-sm p-6">
        <div className="h-6 bg-gray-200 rounded w-1/3 mb-4 animate-pulse"></div>
        <div className="space-y-3">
          {[...Array(3)].map((_, i) => (
            <div key={i} className="h-12 bg-gray-100 rounded animate-pulse"></div>
          ))}
        </div>
      </div>
    );
  }

  if (error) {
    return (
      <div className="bg-red-50 border border-red-200 rounded-lg p-6">
        <h3 className="text-lg font-semibold text-red-800 mb-2">Error Loading Pattern Data</h3>
        <p className="text-red-600 text-sm">{error}</p>
      </div>
    );
  }

  if (!data || data.length === 0) {
    return (
      <div className="bg-white rounded-lg shadow-sm p-6">
        <h3 className="text-lg font-semibold text-gray-900 mb-4">Trade Performance by Pattern</h3>
        <div className="h-40 flex items-center justify-center bg-gray-50 rounded">
          <p className="text-gray-500">No pattern data available for closed trades</p>
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

  // Sort data
  const sortedData = [...data].sort((a, b) => {
    let aValue = a[sortField];
    let bValue = b[sortField];

    if (sortDirection === 'asc') {
      return aValue > bValue ? 1 : -1;
    } else {
      return aValue < bValue ? 1 : -1;
    }
  });

  // Handle sort
  const handleSort = (field: SortField) => {
    if (sortField === field) {
      setSortDirection(sortDirection === 'asc' ? 'desc' : 'asc');
    } else {
      setSortField(field);
      setSortDirection('desc');
    }
  };

  // Sort icon
  const SortIcon = ({ field }: { field: SortField }) => {
    if (sortField !== field) {
      return (
        <svg className="w-4 h-4 text-gray-400" fill="none" viewBox="0 0 24 24" stroke="currentColor">
          <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M7 16V4m0 0L3 8m4-4l4 4m6 0v12m0 0l4-4m-4 4l-4-4" />
        </svg>
      );
    }
    return sortDirection === 'asc' ? (
      <svg className="w-4 h-4 text-blue-600" fill="none" viewBox="0 0 24 24" stroke="currentColor">
        <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M5 15l7-7 7 7" />
      </svg>
    ) : (
      <svg className="w-4 h-4 text-blue-600" fill="none" viewBox="0 0 24 24" stroke="currentColor">
        <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M19 9l-7 7-7-7" />
      </svg>
    );
  };

  // Calculate totals
  const totalTrades = data.reduce((sum, p) => sum + p.trade_count, 0);
  const totalWins = data.reduce((sum, p) => sum + p.wins, 0);
  const overallWinRate = totalTrades > 0 ? (totalWins / totalTrades) * 100 : 0;
  const totalPnL = data.reduce((sum, p) => sum + p.total_pnl, 0);

  return (
    <div className="bg-white rounded-lg shadow-sm p-6">
      <div className="flex items-center justify-between mb-4">
        <h3 className="text-lg font-semibold text-gray-900">Trade Performance by Pattern</h3>
        <div className="text-right">
          <p className="text-sm text-gray-600">Overall Win Rate</p>
          <p className={`text-xl font-bold ${overallWinRate >= 50 ? 'text-green-600' : 'text-red-600'}`}>
            {overallWinRate.toFixed(2)}%
          </p>
        </div>
      </div>

      {/* Table */}
      <div className="overflow-x-auto">
        <table className="min-w-full divide-y divide-gray-200">
          <thead className="bg-gray-50">
            <tr>
              <th
                onClick={() => handleSort('pattern')}
                className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider cursor-pointer hover:bg-gray-100"
              >
                <div className="flex items-center gap-2">
                  Pattern
                  <SortIcon field="pattern" />
                </div>
              </th>
              <th
                onClick={() => handleSort('trade_count')}
                className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider cursor-pointer hover:bg-gray-100"
              >
                <div className="flex items-center gap-2">
                  Trades
                  <SortIcon field="trade_count" />
                </div>
              </th>
              <th
                onClick={() => handleSort('win_rate')}
                className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider cursor-pointer hover:bg-gray-100"
              >
                <div className="flex items-center gap-2">
                  Win Rate
                  <SortIcon field="win_rate" />
                </div>
              </th>
              <th
                onClick={() => handleSort('avg_pnl')}
                className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider cursor-pointer hover:bg-gray-100"
              >
                <div className="flex items-center gap-2">
                  Avg P&L
                  <SortIcon field="avg_pnl" />
                </div>
              </th>
              <th
                onClick={() => handleSort('total_pnl')}
                className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider cursor-pointer hover:bg-gray-100"
              >
                <div className="flex items-center gap-2">
                  Total P&L
                  <SortIcon field="total_pnl" />
                </div>
              </th>
            </tr>
          </thead>
          <tbody className="bg-white divide-y divide-gray-200">
            {sortedData.map((pattern, index) => (
              <tr key={index} className="hover:bg-gray-50">
                <td className="px-6 py-4 whitespace-nowrap text-sm font-medium text-gray-900">
                  {pattern.pattern}
                </td>
                <td className="px-6 py-4 whitespace-nowrap text-sm text-gray-500">
                  {pattern.trade_count} ({pattern.wins}W)
                </td>
                <td className="px-6 py-4 whitespace-nowrap text-sm">
                  <span
                    className={`inline-flex items-center px-2.5 py-0.5 rounded-full text-xs font-medium ${
                      pattern.win_rate >= 50
                        ? 'bg-green-100 text-green-800'
                        : 'bg-red-100 text-red-800'
                    }`}
                  >
                    {pattern.win_rate.toFixed(2)}%
                  </span>
                </td>
                <td className="px-6 py-4 whitespace-nowrap text-sm">
                  <span className={pattern.avg_pnl >= 0 ? 'text-green-600 font-medium' : 'text-red-600 font-medium'}>
                    {formatCurrency(pattern.avg_pnl)}
                  </span>
                </td>
                <td className="px-6 py-4 whitespace-nowrap text-sm">
                  <span className={pattern.total_pnl >= 0 ? 'text-green-600 font-bold' : 'text-red-600 font-bold'}>
                    {formatCurrency(pattern.total_pnl)}
                  </span>
                </td>
              </tr>
            ))}
          </tbody>
          <tfoot className="bg-gray-50 font-semibold">
            <tr>
              <td className="px-6 py-4 whitespace-nowrap text-sm text-gray-900">Total</td>
              <td className="px-6 py-4 whitespace-nowrap text-sm text-gray-900">{totalTrades}</td>
              <td className="px-6 py-4 whitespace-nowrap text-sm">
                <span
                  className={`inline-flex items-center px-2.5 py-0.5 rounded-full text-xs font-medium ${
                    overallWinRate >= 50
                      ? 'bg-green-100 text-green-800'
                      : 'bg-red-100 text-red-800'
                  }`}
                >
                  {overallWinRate.toFixed(2)}%
                </span>
              </td>
              <td className="px-6 py-4 whitespace-nowrap text-sm text-gray-900">-</td>
              <td className="px-6 py-4 whitespace-nowrap text-sm">
                <span className={totalPnL >= 0 ? 'text-green-600 font-bold' : 'text-red-600 font-bold'}>
                  {formatCurrency(totalPnL)}
                </span>
              </td>
            </tr>
          </tfoot>
        </table>
      </div>
    </div>
  );
}
