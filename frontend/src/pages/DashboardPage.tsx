import { useState, useEffect } from 'react';
import { Link } from 'react-router-dom';
import { BarChart3, FileText, TrendingUp, TrendingDown, Clock } from 'lucide-react';
import { api } from '../lib/api';

export default function DashboardPage() {
  const [loading, setLoading] = useState(true);
  const [stats, setStats] = useState<any>({
    pendingAnalyses: 0,
    activeTrades: 0,
    totalPositions: 0,
    unrealizedPnL: 0,
    tradeStats: null,
    recentTrades: [],
  });

  useEffect(() => {
    fetchDashboardData();
  }, []);

  const fetchDashboardData = async () => {
    setLoading(true);
    try {
      const [pendingAnalyses, activeTrades, positions, tradeStats] = await Promise.all([
        api.getPendingApprovals({ page: 1, page_size: 5 }),
        api.getActiveTrades({ page: 1, page_size: 5 }),
        api.getPnLSummary(),
        api.getTradeStats(),
      ]);

      setStats({
        pendingAnalyses: pendingAnalyses.total,
        activeTrades: activeTrades.total,
        totalPositions: positions.summary?.total_positions || 0,
        unrealizedPnL: positions.summary?.total_unrealized_pnl || 0,
        tradeStats,
        recentTrades: activeTrades.data,
      });
    } catch (err) {
      console.error('Failed to fetch dashboard data:', err);
    } finally {
      setLoading(false);
    }
  };

  const formatCurrency = (value?: number | string | null) => {
    if (value === undefined || value === null) return '$0.00';
    const numValue = typeof value === 'string' ? parseFloat(value) : value;
    if (isNaN(numValue)) return '$0.00';
    return `$${numValue.toFixed(2)}`;
  };

  const getPnLColor = (pnl: number) => {
    return pnl >= 0 ? 'text-green-600' : 'text-red-600';
  };

  if (loading) {
    return (
      <div className="bg-white rounded-lg shadow p-8 text-center">
        <div className="inline-block animate-spin rounded-full h-8 w-8 border-b-2 border-gray-900"></div>
        <p className="mt-2 text-gray-600">Loading dashboard...</p>
      </div>
    );
  }

  return (
    <div className="space-y-6">
      {/* Welcome */}
      <div>
        <h1 className="text-2xl sm:text-3xl font-bold text-gray-900 ml-15">Trading Monitor Dashboard</h1>
        <br/>
        <p className="mt-1 text-sm text-gray-500">
          Overview of your trading activities and performance
        </p>
      </div>

      {/* Stats Grid */}
      <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 gap-4">
        {/* Pending Analyses */}
        <Link to="/analysis" className="block">
          <div className="bg-white rounded-lg shadow p-6 hover:shadow-lg transition-shadow">
            <div className="flex items-center">
              <div className="flex-shrink-0">
                <Clock className="w-8 h-8 text-yellow-500" />
              </div>
              <div className="ml-4 flex-1">
                <p className="text-sm font-medium text-gray-500">Pending Analyses</p>
                <p className="text-2xl font-semibold text-gray-900">{stats.pendingAnalyses}</p>
              </div>
            </div>
            <div className="mt-4">
              <span className="text-sm text-blue-600 hover:text-blue-800">View all →</span>
            </div>
          </div>
        </Link>

        {/* Active Trades */}
        <Link to="/trades" className="block">
          <div className="bg-white rounded-lg shadow p-6 hover:shadow-lg transition-shadow">
            <div className="flex items-center">
              <div className="flex-shrink-0">
                <FileText className="w-8 h-8 text-blue-500" />
              </div>
              <div className="ml-4 flex-1">
                <p className="text-sm font-medium text-gray-500">Active Trades</p>
                <p className="text-2xl font-semibold text-gray-900">{stats.activeTrades}</p>
              </div>
            </div>
            <div className="mt-4">
              <span className="text-sm text-blue-600 hover:text-blue-800">View all →</span>
            </div>
          </div>
        </Link>

        {/* Active Positions */}
        <div className="bg-white rounded-lg shadow p-6">
          <div className="flex items-center">
            <div className="flex-shrink-0">
              <TrendingUp className="w-8 h-8 text-purple-500" />
            </div>
            <div className="ml-4 flex-1">
              <p className="text-sm font-medium text-gray-500">Active Positions</p>
              <p className="text-2xl font-semibold text-gray-900">{stats.totalPositions}</p>
            </div>
          </div>
        </div>

        {/* Unrealized P&L */}
        <div className="bg-white rounded-lg shadow p-6">
          <div className="flex items-center">
            <div className="flex-shrink-0">
              {stats.unrealizedPnL >= 0 ? (
                <TrendingUp className="w-8 h-8 text-green-500" />
              ) : (
                <TrendingDown className="w-8 h-8 text-red-500" />
              )}
            </div>
            <div className="ml-4 flex-1">
              <p className="text-sm font-medium text-gray-500">Unrealized P&L</p>
              <p className={`text-2xl font-semibold ${getPnLColor(stats.unrealizedPnL)}`}>
                {formatCurrency(stats.unrealizedPnL)}
              </p>
            </div>
          </div>
        </div>
      </div>

      {/* Trade Statistics */}
      {stats.tradeStats && (
        <div className="bg-white rounded-lg shadow">
          <div className="px-6 py-4 border-b border-gray-200">
            <h2 className="text-lg font-semibold text-gray-900">Trade Statistics</h2>
          </div>
          <div className="p-6">
            <div className="grid grid-cols-2 sm:grid-cols-4 gap-4">
              {Object.entries(stats.tradeStats.status_breakdown || {}).map(([status, count]: [string, any]) => (
                <div key={status} className="text-center">
                  <p className="text-2xl font-bold text-gray-900">{count}</p>
                  <p className="text-sm text-gray-500 capitalize">{status.toLowerCase()}</p>
                </div>
              ))}
            </div>
            {stats.tradeStats.pnl_summary && (
              <div className="mt-6 pt-6 border-t border-gray-200">
                <h3 className="text-sm font-medium text-gray-700 mb-4">Closed Trades P&L Summary</h3>
                <div className="grid grid-cols-1 sm:grid-cols-3 gap-4">
                  <div>
                    <p className="text-xs text-gray-500">Total Closed</p>
                    <p className="text-lg font-semibold text-gray-900">
                      {stats.tradeStats.pnl_summary.total_closed || 0}
                    </p>
                  </div>
                  <div>
                    <p className="text-xs text-gray-500">Total P&L</p>
                    <p className={`text-lg font-semibold ${getPnLColor(stats.tradeStats.pnl_summary.total_pnl || 0)}`}>
                      {formatCurrency(stats.tradeStats.pnl_summary.total_pnl)}
                    </p>
                  </div>
                  <div>
                    <p className="text-xs text-gray-500">Average P&L</p>
                    <p className={`text-lg font-semibold ${getPnLColor(stats.tradeStats.pnl_summary.avg_pnl || 0)}`}>
                      {formatCurrency(stats.tradeStats.pnl_summary.avg_pnl)}
                    </p>
                  </div>
                </div>
              </div>
            )}
          </div>
        </div>
      )}

      {/* Recent Active Trades */}
      {stats.recentTrades.length > 0 && (
        <div className="bg-white rounded-lg shadow">
          <div className="px-6 py-4 border-b border-gray-200 flex items-center justify-between">
            <h2 className="text-lg font-semibold text-gray-900">Recent Active Trades</h2>
            <Link to="/trades" className="text-sm text-blue-600 hover:text-blue-800">
              View all →
            </Link>
          </div>
          <div className="divide-y divide-gray-200">
            {stats.recentTrades.slice(0, 5).map((trade: any) => (
              <div key={trade.id} className="px-6 py-4 hover:bg-gray-50">
                <div className="flex flex-col sm:flex-row sm:items-center sm:justify-between gap-2">
                  <div className="flex items-center space-x-3">
                    <span className="text-lg font-semibold text-gray-900">{trade.symbol}</span>
                    <span className="px-2 py-1 bg-green-100 text-green-800 text-xs font-medium rounded-full">
                      {trade.status}
                    </span>
                  </div>
                  <div className="flex items-center space-x-4 text-sm text-gray-500">
                    <span>Qty: {trade.actual_qty || trade.planned_qty}</span>
                    <span>Entry: {formatCurrency(trade.actual_entry || trade.planned_entry)}</span>
                    <span>Days: {trade.days_open}</span>
                  </div>
                </div>
              </div>
            ))}
          </div>
        </div>
      )}

      {/* Quick Links */}
      <div className="grid grid-cols-1 sm:grid-cols-2 gap-4">
        <Link
          to="/analysis"
          className="flex items-center p-4 bg-blue-50 rounded-lg hover:bg-blue-100 transition-colors"
        >
          <BarChart3 className="w-6 h-6 text-blue-600 mr-3" />
          <span className="text-sm font-medium text-blue-900">View Analysis</span>
        </Link>
        <Link
          to="/trades"
          className="flex items-center p-4 bg-green-50 rounded-lg hover:bg-green-100 transition-colors"
        >
          <FileText className="w-6 h-6 text-green-600 mr-3" />
          <span className="text-sm font-medium text-green-900">Trade Journal</span>
        </Link>
      </div>
    </div>
  );
}
