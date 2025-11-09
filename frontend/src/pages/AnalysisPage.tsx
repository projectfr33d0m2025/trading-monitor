import { useState, useEffect } from 'react';
import { Filter, ChevronDown, ChevronUp, CheckCircle, XCircle, Clock } from 'lucide-react';
import { api } from '../lib/api';
import type { AnalysisDecision, PaginatedResponse } from '../lib/types';

export default function AnalysisPage() {
  const [analyses, setAnalyses] = useState<PaginatedResponse<AnalysisDecision> | null>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [selectedAnalysis, setSelectedAnalysis] = useState<AnalysisDecision | null>(null);

  // Filters
  const [filterTicker, setFilterTicker] = useState('');
  const [filterExecuted, setFilterExecuted] = useState<boolean | undefined>(undefined);
  const [filterApproved, setFilterApproved] = useState<boolean | undefined>(undefined);
  const [showFilters, setShowFilters] = useState(true);

  // Pagination
  const [currentPage, setCurrentPage] = useState(1);
  const pageSize = 20;

  useEffect(() => {
    fetchAnalyses();
  }, [currentPage, filterTicker, filterExecuted, filterApproved]);

  const fetchAnalyses = async () => {
    setLoading(true);
    setError(null);

    try {
      const data = await api.getAnalyses({
        page: currentPage,
        page_size: pageSize,
        ticker: filterTicker || undefined,
        executed: filterExecuted,
        approved: filterApproved,
      });
      setAnalyses(data);
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Failed to fetch analyses');
    } finally {
      setLoading(false);
    }
  };

  const getStatusBadge = (analysis: AnalysisDecision) => {
    if (analysis.executed) {
      return (
        <span className="inline-flex items-center px-2.5 py-0.5 rounded-full text-xs font-medium bg-green-100 text-green-800">
          <CheckCircle className="w-3 h-3 mr-1" />
          Executed
        </span>
      );
    }
    if (analysis.Approve) {
      return (
        <span className="inline-flex items-center px-2.5 py-0.5 rounded-full text-xs font-medium bg-blue-100 text-blue-800">
          <CheckCircle className="w-3 h-3 mr-1" />
          Approved
        </span>
      );
    }
    return (
      <span className="inline-flex items-center px-2.5 py-0.5 rounded-full text-xs font-medium bg-yellow-100 text-yellow-800">
        <Clock className="w-3 h-3 mr-1" />
        Pending
      </span>
    );
  };

  return (
    <div className="space-y-6">
      {/* Header */}
      <div className="flex items-center justify-between">
        <div>
          <h1 className="text-2xl font-bold text-gray-900">Analysis Decisions</h1>
          <p className="mt-1 text-sm text-gray-500">
            Review and track AI-generated trading analysis decisions
          </p>
        </div>
        <button
          onClick={() => setShowFilters(!showFilters)}
          className="inline-flex items-center px-4 py-2 border border-gray-300 rounded-md shadow-sm text-sm font-medium text-gray-700 bg-white hover:bg-gray-50"
        >
          <Filter className="w-4 h-4 mr-2" />
          Filters
          {showFilters ? <ChevronUp className="w-4 h-4 ml-2" /> : <ChevronDown className="w-4 h-4 ml-2" />}
        </button>
      </div>

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
          <div className="flex items-center">
            <XCircle className="w-5 h-5 text-red-400 mr-2" />
            <p className="text-sm text-red-800">{error}</p>
          </div>
        </div>
      )}

      {!loading && !error && analyses && (
        <>
          {/* Table */}
          <div className="bg-white shadow rounded-lg overflow-hidden">
            <table className="min-w-full divide-y divide-gray-200">
              <thead className="bg-gray-50">
                <tr>
                  <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                    Date/Time
                  </th>
                  <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                    Ticker
                  </th>
                  <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                    Trade Type
                  </th>
                  <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                    Status
                  </th>
                  <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                    Actions
                  </th>
                </tr>
              </thead>
              <tbody className="bg-white divide-y divide-gray-200">
                {analyses.data.map((analysis) => (
                  <tr key={analysis.Analysis_Id} className="hover:bg-gray-50">
                    <td className="px-6 py-4 whitespace-nowrap text-sm text-gray-900">
                      {analysis.Date_time ? new Date(analysis.Date_time).toLocaleString() : 'N/A'}
                    </td>
                    <td className="px-6 py-4 whitespace-nowrap">
                      <span className="text-sm font-medium text-gray-900">{analysis.Ticker}</span>
                    </td>
                    <td className="px-6 py-4 whitespace-nowrap text-sm text-gray-500">
                      {analysis.Trade_Type || 'N/A'}
                    </td>
                    <td className="px-6 py-4 whitespace-nowrap">
                      {getStatusBadge(analysis)}
                    </td>
                    <td className="px-6 py-4 whitespace-nowrap text-sm">
                      <button
                        onClick={() => setSelectedAnalysis(analysis)}
                        className="text-blue-600 hover:text-blue-900 font-medium"
                      >
                        View Details
                      </button>
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>

          {/* Pagination */}
          <div className="bg-white px-4 py-3 flex items-center justify-between border-t border-gray-200 sm:px-6 rounded-lg shadow">
            <div className="flex-1 flex justify-between sm:hidden">
              <button
                onClick={() => setCurrentPage(p => Math.max(1, p - 1))}
                disabled={currentPage === 1}
                className="relative inline-flex items-center px-4 py-2 border border-gray-300 text-sm font-medium rounded-md text-gray-700 bg-white hover:bg-gray-50"
              >
                Previous
              </button>
              <button
                onClick={() => setCurrentPage(p => p + 1)}
                disabled={currentPage * pageSize >= analyses.total}
                className="ml-3 relative inline-flex items-center px-4 py-2 border border-gray-300 text-sm font-medium rounded-md text-gray-700 bg-white hover:bg-gray-50"
              >
                Next
              </button>
            </div>
            <div className="hidden sm:flex-1 sm:flex sm:items-center sm:justify-between">
              <div>
                <p className="text-sm text-gray-700">
                  Showing <span className="font-medium">{(currentPage - 1) * pageSize + 1}</span> to{' '}
                  <span className="font-medium">{Math.min(currentPage * pageSize, analyses.total)}</span> of{' '}
                  <span className="font-medium">{analyses.total}</span> results
                </p>
              </div>
              <div>
                <nav className="relative z-0 inline-flex rounded-md shadow-sm -space-x-px">
                  <button
                    onClick={() => setCurrentPage(p => Math.max(1, p - 1))}
                    disabled={currentPage === 1}
                    className="relative inline-flex items-center px-2 py-2 rounded-l-md border border-gray-300 bg-white text-sm font-medium text-gray-500 hover:bg-gray-50"
                  >
                    Previous
                  </button>
                  <span className="relative inline-flex items-center px-4 py-2 border border-gray-300 bg-white text-sm font-medium text-gray-700">
                    Page {currentPage}
                  </span>
                  <button
                    onClick={() => setCurrentPage(p => p + 1)}
                    disabled={currentPage * pageSize >= analyses.total}
                    className="relative inline-flex items-center px-2 py-2 rounded-r-md border border-gray-300 bg-white text-sm font-medium text-gray-500 hover:bg-gray-50"
                  >
                    Next
                  </button>
                </nav>
              </div>
            </div>
          </div>
        </>
      )}

      {/* Detail Modal */}
      {selectedAnalysis && (
        <div className="fixed inset-0 bg-gray-500 bg-opacity-75 flex items-center justify-center p-4 z-50">
          <div className="bg-white rounded-lg shadow-xl max-w-4xl w-full max-h-[90vh] overflow-y-auto">
            <div className="px-6 py-4 border-b border-gray-200">
              <div className="flex items-center justify-between">
                <h3 className="text-lg font-medium text-gray-900">
                  Analysis Details - {selectedAnalysis.Ticker}
                </h3>
                <button
                  onClick={() => setSelectedAnalysis(null)}
                  className="text-gray-400 hover:text-gray-500"
                >
                  <XCircle className="w-6 h-6" />
                </button>
              </div>
            </div>
            <div className="px-6 py-4 space-y-4">
              <div className="grid grid-cols-2 gap-4">
                <div>
                  <p className="text-sm font-medium text-gray-500">Analysis ID</p>
                  <p className="mt-1 text-sm text-gray-900">{selectedAnalysis.Analysis_Id}</p>
                </div>
                <div>
                  <p className="text-sm font-medium text-gray-500">Date/Time</p>
                  <p className="mt-1 text-sm text-gray-900">
                    {selectedAnalysis.Date_time ? new Date(selectedAnalysis.Date_time).toLocaleString() : 'N/A'}
                  </p>
                </div>
                <div>
                  <p className="text-sm font-medium text-gray-500">Trade Type</p>
                  <p className="mt-1 text-sm text-gray-900">{selectedAnalysis.Trade_Type || 'N/A'}</p>
                </div>
                <div>
                  <p className="text-sm font-medium text-gray-500">Status</p>
                  <div className="mt-1">{getStatusBadge(selectedAnalysis)}</div>
                </div>
              </div>

              {selectedAnalysis.Analysis && (
                <div>
                  <p className="text-sm font-medium text-gray-500">Analysis</p>
                  <div className="mt-1 text-sm text-gray-900 bg-gray-50 p-3 rounded">
                    {selectedAnalysis.Analysis}
                  </div>
                </div>
              )}

              {selectedAnalysis.Decision && (
                <div>
                  <p className="text-sm font-medium text-gray-500">Decision Data</p>
                  <pre className="mt-1 text-xs text-gray-900 bg-gray-50 p-3 rounded overflow-x-auto">
                    {JSON.stringify(selectedAnalysis.Decision, null, 2)}
                  </pre>
                </div>
              )}

              {selectedAnalysis.Chart && (
                <div>
                  <p className="text-sm font-medium text-gray-500 mb-2">Chart</p>
                  <img src={selectedAnalysis.Chart} alt="Analysis Chart" className="w-full rounded" />
                </div>
              )}
            </div>
          </div>
        </div>
      )}
    </div>
  );
}
