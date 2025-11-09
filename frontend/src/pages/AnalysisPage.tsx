import { useState, useEffect } from 'react';
import { Filter, ChevronDown, ChevronUp, CheckCircle, XCircle, Clock, TrendingUp, FileText, Zap } from 'lucide-react';
import { api } from '../lib/api';
import type { AnalysisDecision, PaginatedResponse } from '../lib/types';

export default function AnalysisPage() {
  const [analyses, setAnalyses] = useState<PaginatedResponse<AnalysisDecision> | null>(null);
  const [stats, setStats] = useState<any>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [expandedAnalysis, setExpandedAnalysis] = useState<string | null>(null);

  // Filters
  const [filterTicker, setFilterTicker] = useState('');
  const [filterExecuted, setFilterExecuted] = useState<boolean | undefined>(undefined);
  const [filterApproved, setFilterApproved] = useState<boolean | undefined>(undefined);
  const [showFilters, setShowFilters] = useState(true);

  // Pagination
  const [currentPage, setCurrentPage] = useState(1);
  const pageSize = 20;

  useEffect(() => {
    fetchData();
  }, [currentPage, filterTicker, filterExecuted, filterApproved]);

  const fetchData = async () => {
    setLoading(true);
    setError(null);

    try {
      const [analysesData, statsData] = await Promise.all([
        api.getAnalyses({
          page: currentPage,
          page_size: pageSize,
          ticker: filterTicker || undefined,
          executed: filterExecuted,
          approved: filterApproved,
        }),
        api.getAnalysisStats(),
      ]);
      setAnalyses(analysesData);
      setStats(statsData);
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Failed to fetch analyses');
    } finally {
      setLoading(false);
    }
  };

  const getStatusIcon = (analysis: AnalysisDecision) => {
    if (analysis.executed) {
      return <CheckCircle className="w-5 h-5" />;
    }
    if (analysis.Approve) {
      return <CheckCircle className="w-5 h-5" />;
    }
    return <Clock className="w-5 h-5" />;
  };

  const getStatusGradient = (status: string) => {
    switch (status) {
      case 'PENDING':
        return 'from-yellow-500 to-yellow-600';
      case 'APPROVED':
        return 'from-blue-500 to-blue-600';
      case 'EXECUTED':
        return 'from-green-500 to-green-600';
      default:
        return 'from-gray-400 to-gray-500';
    }
  };

  const getStatusColor = (analysis: AnalysisDecision) => {
    if (analysis.executed) {
      return 'bg-green-100 text-green-800 border-green-200';
    }
    if (analysis.Approve) {
      return 'bg-blue-100 text-blue-800 border-blue-200';
    }
    return 'bg-yellow-100 text-yellow-800 border-yellow-200';
  };

  const getStatusLabel = (analysis: AnalysisDecision) => {
    if (analysis.executed) return 'EXECUTED';
    if (analysis.Approve) return 'APPROVED';
    return 'PENDING';
  };

  const getTradeTypeIcon = (tradeType?: string) => {
    if (!tradeType) return <FileText className="w-4 h-4" />;
    if (tradeType.toLowerCase().includes('swing')) return <Zap className="w-4 h-4" />;
    if (tradeType.toLowerCase().includes('trend')) return <TrendingUp className="w-4 h-4" />;
    return <FileText className="w-4 h-4" />;
  };

  const statusBreakdown = stats?.status_breakdown || {};

  return (
    <div className="space-y-4 sm:space-y-6">
      {/* Header */}
      <div className="flex flex-col sm:flex-row sm:items-center sm:justify-between gap-4">
        <div>
          <h1 className="text-2xl font-bold text-gray-900">Analysis Decisions</h1>
          <p className="mt-1 text-sm text-gray-500">
            Review and track AI-generated trading analysis decisions
          </p>
        </div>
        <button
          onClick={() => setShowFilters(!showFilters)}
          className="inline-flex items-center justify-center px-4 py-2 border border-gray-300 rounded-md shadow-sm text-sm font-medium text-gray-700 bg-white hover:bg-gray-50"
        >
          <Filter className="w-4 h-4 mr-2" />
          Filters
          {showFilters ? <ChevronUp className="w-4 h-4 ml-2" /> : <ChevronDown className="w-4 h-4 ml-2" />}
        </button>
      </div>

      {/* Summary Cards */}
      {!loading && stats && (
        <div className="grid grid-cols-1 sm:grid-cols-3 gap-4">
          {Object.entries(statusBreakdown).map(([status, count]: [string, any]) => (
            <div key={status} className={`bg-gradient-to-br ${getStatusGradient(status)} rounded-lg shadow-lg p-6 text-white`}>
              <div className="flex items-center justify-between">
                <div>
                  <p className="text-sm font-medium opacity-90 uppercase">{status}</p>
                  <p className="text-3xl font-bold mt-1">{count}</p>
                </div>
                <div className="opacity-30">
                  {status === 'PENDING' && <Clock className="w-12 h-12" />}
                  {status === 'APPROVED' && <CheckCircle className="w-12 h-12" />}
                  {status === 'EXECUTED' && <CheckCircle className="w-12 h-12" />}
                </div>
              </div>
            </div>
          ))}
        </div>
      )}

      {/* Filters */}
      {showFilters && (
        <div className="bg-white p-4 rounded-lg shadow space-y-4">
          <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
            <div>
              <label className="block text-sm font-medium text-gray-700 mb-1">
                Ticker Symbol
              </label>
              <input
                type="text"
                value={filterTicker}
                onChange={(e) => setFilterTicker(e.target.value.toUpperCase())}
                placeholder="e.g., AAPL"
                className="w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-blue-500"
              />
            </div>
            <div>
              <label className="block text-sm font-medium text-gray-700 mb-1">
                Execution Status
              </label>
              <select
                value={filterExecuted === undefined ? '' : filterExecuted.toString()}
                onChange={(e) => setFilterExecuted(e.target.value === '' ? undefined : e.target.value === 'true')}
                className="w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-blue-500"
              >
                <option value="">All</option>
                <option value="true">Executed</option>
                <option value="false">Not Executed</option>
              </select>
            </div>
            <div>
              <label className="block text-sm font-medium text-gray-700 mb-1">
                Approval Status
              </label>
              <select
                value={filterApproved === undefined ? '' : filterApproved.toString()}
                onChange={(e) => setFilterApproved(e.target.value === '' ? undefined : e.target.value === 'true')}
                className="w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-blue-500"
              >
                <option value="">All</option>
                <option value="true">Approved</option>
                <option value="false">Not Approved</option>
              </select>
            </div>
          </div>
        </div>
      )}

      {/* Content */}
      {loading && (
        <div className="bg-white rounded-lg shadow p-8 text-center">
          <div className="inline-block animate-spin rounded-full h-8 w-8 border-b-2 border-gray-900"></div>
          <p className="mt-2 text-gray-600">Loading analyses...</p>
        </div>
      )}

      {error && (
        <div className="bg-red-50 border border-red-200 rounded-lg p-4">
          <p className="text-sm text-red-800">{error}</p>
        </div>
      )}

      {!loading && !error && analyses && (
        <>
          {/* Enhanced Analysis Cards */}
          <div className="space-y-4">
            {analyses.data.map((analysis) => {
              const isExpanded = expandedAnalysis === analysis.Analysis_Id;
              const statusColorClass = getStatusColor(analysis);
              const statusLabel = getStatusLabel(analysis);

              return (
                <div key={analysis.Analysis_Id} className={`bg-white rounded-lg shadow-md border-2 ${statusColorClass} overflow-hidden transition-all`}>
                  {/* Analysis Header */}
                  <div
                    className="p-4 sm:p-6 cursor-pointer hover:bg-gray-50"
                    onClick={() => setExpandedAnalysis(isExpanded ? null : analysis.Analysis_Id)}
                  >
                    <div className="flex items-center justify-between">
                      <div className="flex items-center space-x-4">
                        <div className="bg-white rounded-lg p-3 shadow-sm border border-gray-200">
                          {getStatusIcon(analysis)}
                        </div>
                        <div>
                          <div className="flex items-center space-x-2">
                            <h3 className="text-xl font-bold text-gray-900">{analysis.Ticker}</h3>
                            {analysis.Trade_Type && (
                              <span className="inline-flex items-center px-2 py-1 rounded-full text-xs font-semibold bg-purple-100 text-purple-800">
                                {getTradeTypeIcon(analysis.Trade_Type)}
                                <span className="ml-1">{analysis.Trade_Type}</span>
                              </span>
                            )}
                          </div>
                          <p className="text-sm text-gray-500">{analysis.Analysis_Id}</p>
                        </div>
                      </div>
                      <div className="flex items-center space-x-4">
                        <div className="text-right">
                          <span className={`px-3 py-1 inline-flex items-center text-sm font-semibold rounded-full ${statusColorClass}`}>
                            {getStatusIcon(analysis)}
                            <span className="ml-1.5">{statusLabel}</span>
                          </span>
                          {analysis.Date_time && (
                            <p className="text-xs text-gray-500 mt-2">
                              {new Date(analysis.Date_time).toLocaleString()}
                            </p>
                          )}
                        </div>
                        {isExpanded ? (
                          <ChevronUp className="w-6 h-6 text-gray-400" />
                        ) : (
                          <ChevronDown className="w-6 h-6 text-gray-400" />
                        )}
                      </div>
                    </div>

                    {/* Analysis Summary */}
                    {analysis.Analysis && (
                      <div className="mt-4">
                        <p className="text-sm text-gray-700 line-clamp-2">
                          {analysis.Analysis}
                        </p>
                      </div>
                    )}
                  </div>

                  {/* Expandable Details */}
                  {isExpanded && (
                    <div className="border-t border-gray-200 bg-gray-50 p-4 sm:p-6 space-y-4">
                      {analysis.Analysis && (
                        <div>
                          <p className="text-sm font-medium text-gray-700 mb-2">Full Analysis</p>
                          <div className="text-sm text-gray-900 bg-white p-4 rounded-lg border border-gray-200 whitespace-pre-wrap">
                            {analysis.Analysis}
                          </div>
                        </div>
                      )}

                      {analysis.Decision && (
                        <div>
                          <p className="text-sm font-medium text-gray-700 mb-2">Decision Data</p>
                          <pre className="text-xs text-gray-900 bg-white p-4 rounded-lg border border-gray-200 overflow-x-auto">
                            {JSON.stringify(analysis.Decision, null, 2)}
                          </pre>
                        </div>
                      )}

                      {analysis.Chart && (
                        <div>
                          <p className="text-sm font-medium text-gray-700 mb-2">Chart</p>
                          <img
                            src={analysis.Chart}
                            alt="Analysis Chart"
                            className="w-full rounded-lg border border-gray-200 shadow-sm"
                          />
                        </div>
                      )}

                      <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-3 gap-4 pt-4">
                        <div>
                          <p className="text-sm text-gray-500">Analysis ID</p>
                          <p className="text-base font-semibold text-gray-900 font-mono">{analysis.Analysis_Id}</p>
                        </div>
                        <div>
                          <p className="text-sm text-gray-500">Date/Time</p>
                          <p className="text-base font-semibold text-gray-900">
                            {analysis.Date_time ? new Date(analysis.Date_time).toLocaleString() : 'N/A'}
                          </p>
                        </div>
                        {analysis.Trade_Type && (
                          <div>
                            <p className="text-sm text-gray-500">Trade Type</p>
                            <p className="text-base font-semibold text-gray-900">{analysis.Trade_Type}</p>
                          </div>
                        )}
                      </div>
                    </div>
                  )}
                </div>
              );
            })}
          </div>

          {/* Pagination */}
          <div className="bg-white px-4 py-3 flex flex-col sm:flex-row items-center justify-between border-t border-gray-200 rounded-lg shadow gap-3">
            <div className="text-sm text-gray-700 text-center sm:text-left">
              Showing <span className="font-medium">{(currentPage - 1) * pageSize + 1}</span> to{' '}
              <span className="font-medium">{Math.min(currentPage * pageSize, analyses.total)}</span> of{' '}
              <span className="font-medium">{analyses.total}</span> results
            </div>
            <div className="flex gap-2">
              <button
                onClick={() => setCurrentPage(p => Math.max(1, p - 1))}
                disabled={currentPage === 1}
                className="px-3 py-1.5 border border-gray-300 rounded-md text-sm font-medium text-gray-700 bg-white hover:bg-gray-50 disabled:opacity-50"
              >
                Previous
              </button>
              <span className="px-3 py-1.5 border border-gray-300 rounded-md text-sm font-medium text-gray-700 bg-white">
                Page {currentPage}
              </span>
              <button
                onClick={() => setCurrentPage(p => p + 1)}
                disabled={currentPage * pageSize >= analyses.total}
                className="px-3 py-1.5 border border-gray-300 rounded-md text-sm font-medium text-gray-700 bg-white hover:bg-gray-50 disabled:opacity-50"
              >
                Next
              </button>
            </div>
          </div>
        </>
      )}
    </div>
  );
}
