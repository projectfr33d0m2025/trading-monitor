import { useState, useEffect } from 'react';
import { Filter, ChevronDown, ChevronUp, Plus, List, Eye } from 'lucide-react';
import { api } from '../lib/api';
import type { TickerWatchlist, PaginatedResponse } from '../lib/types';
import WatchlistCard from '../components/watchlist/WatchlistCard';
import AddTickerModal from '../components/watchlist/AddTickerModal';
import EditTickerModal from '../components/watchlist/EditTickerModal';
import DeleteConfirmDialog from '../components/watchlist/DeleteConfirmDialog';

export default function WatchlistPage() {
  const [watchlist, setWatchlist] = useState<PaginatedResponse<TickerWatchlist> | null>(null);
  const [stats, setStats] = useState<{ total: number; active: number; inactive: number } | null>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  // Filters
  const [filterExchange, setFilterExchange] = useState<string>('ALL');
  const [filterIndustry, setFilterIndustry] = useState<string>('ALL');
  const [filterActive, setFilterActive] = useState<string>('ALL');
  const [filterSearch, setFilterSearch] = useState('');
  const [showFilters, setShowFilters] = useState(false);

  // Pagination
  const [currentPage, setCurrentPage] = useState(1);
  const pageSize = 20;

  // Modals
  const [showAddModal, setShowAddModal] = useState(false);
  const [showEditModal, setShowEditModal] = useState(false);
  const [showDeleteDialog, setShowDeleteDialog] = useState(false);
  const [selectedTicker, setSelectedTicker] = useState<TickerWatchlist | null>(null);
  const [isDeleting, setIsDeleting] = useState(false);

  // Toast notification
  const [toast, setToast] = useState<{ message: string; type: 'success' | 'error' } | null>(null);

  // Dynamic filter options (extracted from data)
  const [exchanges, setExchanges] = useState<string[]>([]);
  const [industries, setIndustries] = useState<string[]>([]);

  useEffect(() => {
    fetchData();
  }, [currentPage, filterExchange, filterIndustry, filterActive, filterSearch]);

  const fetchData = async () => {
    setLoading(true);
    setError(null);

    try {
      const [watchlistData, statsData] = await Promise.all([
        api.getWatchlist({
          page: currentPage,
          page_size: pageSize,
          exchange: filterExchange !== 'ALL' ? filterExchange : undefined,
          industry: filterIndustry !== 'ALL' ? filterIndustry : undefined,
          active: filterActive === 'ACTIVE' ? true : filterActive === 'INACTIVE' ? false : undefined,
          search: filterSearch || undefined,
        }),
        api.getWatchlistStats(),
      ]);

      setWatchlist(watchlistData);
      setStats(statsData);

      // Extract unique exchanges and industries for filter dropdowns
      const uniqueExchanges = Array.from(
        new Set(watchlistData.data.map((t) => t.Exchange).filter((e): e is string => !!e))
      ).sort();
      const uniqueIndustries = Array.from(
        new Set(watchlistData.data.map((t) => t.Industry).filter((i): i is string => !!i))
      ).sort();

      setExchanges(uniqueExchanges);
      setIndustries(uniqueIndustries);
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Failed to fetch watchlist');
    } finally {
      setLoading(false);
    }
  };

  const handleEdit = (ticker: TickerWatchlist) => {
    setSelectedTicker(ticker);
    setShowEditModal(true);
  };

  const handleDelete = (ticker: TickerWatchlist) => {
    setSelectedTicker(ticker);
    setShowDeleteDialog(true);
  };

  const confirmDelete = async () => {
    if (!selectedTicker) return;

    setIsDeleting(true);
    try {
      await api.deleteWatchlistTicker(selectedTicker.id);
      showToast(`${selectedTicker.Ticker} removed from watchlist`, 'success');
      setShowDeleteDialog(false);
      setSelectedTicker(null);
      fetchData(); // Refresh list
    } catch (err) {
      showToast(err instanceof Error ? err.message : 'Failed to delete ticker', 'error');
    } finally {
      setIsDeleting(false);
    }
  };

  const showToast = (message: string, type: 'success' | 'error') => {
    setToast({ message, type });
    setTimeout(() => setToast(null), 3000);
  };

  const handlePageChange = (newPage: number) => {
    setCurrentPage(newPage);
    window.scrollTo({ top: 0, behavior: 'smooth' });
  };

  if (loading && !watchlist) {
    return (
      <div className="flex items-center justify-center min-h-screen">
        <div className="text-center">
          <div className="animate-spin rounded-full h-12 w-12 border-b-2 border-blue-600 mx-auto"></div>
          <p className="mt-4 text-gray-600">Loading watchlist...</p>
        </div>
      </div>
    );
  }

  if (error) {
    return (
      <div className="p-6">
        <div className="bg-red-50 border border-red-200 rounded-lg p-4">
          <p className="text-red-600">Error: {error}</p>
        </div>
      </div>
    );
  }

  return (
    <div className="p-4 sm:p-6">
      {/* Header */}
      <div className="flex flex-col sm:flex-row sm:items-center sm:justify-between gap-4 mb-6">
        <h1 className="text-2xl sm:text-3xl font-bold text-gray-900">Watchlist</h1>
        {/* Desktop Add Button */}
        <button
          onClick={() => setShowAddModal(true)}
          className="hidden sm:flex items-center gap-2 px-4 py-2 bg-blue-600 text-white rounded-md hover:bg-blue-700 shadow"
        >
          <Plus className="w-5 h-5" />
          Add Ticker
        </button>
      </div>

      {/* Summary Cards */}
      <div className="grid grid-cols-2 gap-4 mb-6">
        {/* Active Tickers */}
        <div className="bg-gradient-to-br from-green-500 to-green-600 rounded-lg shadow p-4 text-white">
          <div className="flex items-center gap-3">
            <Eye className="w-8 h-8" />
            <div>
              <p className="text-sm opacity-90">Active Tickers</p>
              <p className="text-3xl font-bold">{stats?.active || 0}</p>
            </div>
          </div>
        </div>

        {/* Total Tickers */}
        <div className="bg-gradient-to-br from-blue-500 to-blue-600 rounded-lg shadow p-4 text-white">
          <div className="flex items-center gap-3">
            <List className="w-8 h-8" />
            <div>
              <p className="text-sm opacity-90">Total Tickers</p>
              <p className="text-3xl font-bold">{stats?.total || 0}</p>
            </div>
          </div>
        </div>
      </div>

      {/* Filters */}
      <div className="mb-6">
        <button
          onClick={() => setShowFilters(!showFilters)}
          className="flex items-center gap-2 px-4 py-2 bg-white border border-gray-300 rounded-md hover:bg-gray-50 w-full sm:w-auto"
        >
          <Filter className="w-5 h-5" />
          <span>Filters</span>
          {showFilters ? <ChevronUp className="w-4 h-4" /> : <ChevronDown className="w-4 h-4" />}
        </button>

        {showFilters && (
          <div className="mt-4 p-4 bg-white border border-gray-200 rounded-lg grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 gap-4">
            {/* Exchange Filter */}
            <div>
              <label className="block text-sm font-medium text-gray-700 mb-1">Exchange</label>
              <select
                value={filterExchange}
                onChange={(e) => {
                  setFilterExchange(e.target.value);
                  setCurrentPage(1);
                }}
                className="w-full px-3 py-2 border border-gray-300 rounded-md focus:ring-2 focus:ring-blue-500 focus:border-transparent"
              >
                <option value="ALL">All Exchanges</option>
                {exchanges.map((exchange) => (
                  <option key={exchange} value={exchange}>
                    {exchange}
                  </option>
                ))}
              </select>
            </div>

            {/* Industry Filter */}
            <div>
              <label className="block text-sm font-medium text-gray-700 mb-1">Industry</label>
              <select
                value={filterIndustry}
                onChange={(e) => {
                  setFilterIndustry(e.target.value);
                  setCurrentPage(1);
                }}
                className="w-full px-3 py-2 border border-gray-300 rounded-md focus:ring-2 focus:ring-blue-500 focus:border-transparent"
              >
                <option value="ALL">All Industries</option>
                {industries.map((industry) => (
                  <option key={industry} value={industry}>
                    {industry}
                  </option>
                ))}
              </select>
            </div>

            {/* Active Status Filter */}
            <div>
              <label className="block text-sm font-medium text-gray-700 mb-1">Status</label>
              <select
                value={filterActive}
                onChange={(e) => {
                  setFilterActive(e.target.value);
                  setCurrentPage(1);
                }}
                className="w-full px-3 py-2 border border-gray-300 rounded-md focus:ring-2 focus:ring-blue-500 focus:border-transparent"
              >
                <option value="ALL">All</option>
                <option value="ACTIVE">Active Only</option>
                <option value="INACTIVE">Inactive Only</option>
              </select>
            </div>

            {/* Search */}
            <div>
              <label className="block text-sm font-medium text-gray-700 mb-1">Search</label>
              <input
                type="text"
                value={filterSearch}
                onChange={(e) => {
                  setFilterSearch(e.target.value);
                  setCurrentPage(1);
                }}
                placeholder="Search ticker..."
                className="w-full px-3 py-2 border border-gray-300 rounded-md focus:ring-2 focus:ring-blue-500 focus:border-transparent"
              />
            </div>
          </div>
        )}
      </div>

      {/* Watchlist Cards */}
      {watchlist && watchlist.data.length > 0 ? (
        <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-3 gap-4">
          {watchlist.data.map((ticker) => (
            <WatchlistCard
              key={ticker.id}
              ticker={ticker}
              onEdit={handleEdit}
              onDelete={handleDelete}
            />
          ))}
        </div>
      ) : (
        <div className="text-center py-12 bg-white rounded-lg border border-gray-200">
          <Eye className="w-16 h-16 text-gray-400 mx-auto mb-4" />
          <h3 className="text-lg font-medium text-gray-900 mb-2">Your watchlist is empty</h3>
          <p className="text-gray-500 mb-4">Add tickers to start tracking</p>
          <button
            onClick={() => setShowAddModal(true)}
            className="px-4 py-2 bg-blue-600 text-white rounded-md hover:bg-blue-700"
          >
            Add Ticker
          </button>
        </div>
      )}

      {/* Pagination */}
      {watchlist && watchlist.total > pageSize && (
        <div className="mt-6 flex items-center justify-between">
          <p className="text-sm text-gray-600">
            Showing {(currentPage - 1) * pageSize + 1} to{' '}
            {Math.min(currentPage * pageSize, watchlist.total)} of {watchlist.total} tickers
          </p>
          <div className="flex gap-2">
            <button
              onClick={() => handlePageChange(currentPage - 1)}
              disabled={currentPage === 1}
              className="px-4 py-2 border border-gray-300 rounded-md hover:bg-gray-50 disabled:opacity-50 disabled:cursor-not-allowed"
            >
              Previous
            </button>
            <button
              onClick={() => handlePageChange(currentPage + 1)}
              disabled={currentPage * pageSize >= watchlist.total}
              className="px-4 py-2 border border-gray-300 rounded-md hover:bg-gray-50 disabled:opacity-50 disabled:cursor-not-allowed"
            >
              Next
            </button>
          </div>
        </div>
      )}

      {/* Mobile FAB */}
      <button
        onClick={() => setShowAddModal(true)}
        className="sm:hidden fixed bottom-6 right-6 w-14 h-14 bg-blue-600 text-white rounded-full shadow-lg hover:bg-blue-700 flex items-center justify-center z-40"
      >
        <Plus className="w-6 h-6" />
      </button>

      {/* Modals */}
      <AddTickerModal
        isOpen={showAddModal}
        onClose={() => setShowAddModal(false)}
        onSuccess={() => {
          showToast('Ticker added to watchlist', 'success');
          fetchData();
        }}
      />

      <EditTickerModal
        ticker={selectedTicker}
        isOpen={showEditModal}
        onClose={() => {
          setShowEditModal(false);
          setSelectedTicker(null);
        }}
        onSuccess={() => {
          showToast('Ticker updated', 'success');
          fetchData();
        }}
      />

      <DeleteConfirmDialog
        ticker={selectedTicker!}
        isOpen={showDeleteDialog}
        onClose={() => {
          setShowDeleteDialog(false);
          setSelectedTicker(null);
        }}
        onConfirm={confirmDelete}
        isDeleting={isDeleting}
      />

      {/* Toast Notification */}
      {toast && (
        <div className="fixed bottom-6 left-1/2 transform -translate-x-1/2 z-50">
          <div
            className={`px-6 py-3 rounded-lg shadow-lg ${
              toast.type === 'success' ? 'bg-green-600' : 'bg-red-600'
            } text-white`}
          >
            {toast.message}
          </div>
        </div>
      )}
    </div>
  );
}
