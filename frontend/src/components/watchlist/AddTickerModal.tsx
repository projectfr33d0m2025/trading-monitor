import { useState } from 'react';
import { X } from 'lucide-react';
import { api } from '../../lib/api';
import type { AlpacaAsset } from '../../lib/types';
import TickerAutocomplete from './TickerAutocomplete';

interface AddTickerModalProps {
  isOpen: boolean;
  onClose: () => void;
  onSuccess: () => void;
}

const COMMON_INDUSTRIES = [
  'Technology',
  'Semiconductor',
  'Finance',
  'Healthcare',
  'Energy',
  'Consumer Goods',
  'Consumer Services',
  'Industrials',
  'Materials',
  'Utilities',
  'Real Estate',
  'Telecommunications',
  'ETF - US',
  'ETF - Europe',
  'ETF - Asia Pacific',
  'ETF - Emerging Markets',
  'ETF - Global',
  'Other'
];

export default function AddTickerModal({ isOpen, onClose, onSuccess }: AddTickerModalProps) {
  const [tickerSearch, setTickerSearch] = useState('');
  const [selectedTicker, setSelectedTicker] = useState('');
  const [selectedTickerName, setSelectedTickerName] = useState('');
  const [selectedExchange, setSelectedExchange] = useState('');
  const [industry, setIndustry] = useState('');
  const [active, setActive] = useState(true);
  const [isSubmitting, setIsSubmitting] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [tickerError, setTickerError] = useState<string | null>(null);

  if (!isOpen) return null;

  const handleTickerSelect = (asset: AlpacaAsset) => {
    setSelectedTicker(asset.symbol);
    setSelectedTickerName(asset.name);
    setSelectedExchange(asset.exchange);
    setTickerSearch(asset.symbol);
    setTickerError(null);
  };

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    setError(null);
    setTickerError(null);

    // Validation
    if (!selectedTicker) {
      setTickerError('Please select a ticker from the search results');
      return;
    }

    if (!selectedExchange) {
      setError('Exchange is required');
      return;
    }

    if (!industry) {
      setError('Please select an industry');
      return;
    }

    setIsSubmitting(true);

    try {
      await api.createWatchlistTicker({
        Ticker: selectedTicker,
        Ticker_Name: selectedTickerName,
        Exchange: selectedExchange,
        Industry: industry,
        Active: active
      });

      // Success - reset and close
      resetForm();
      onSuccess();
      onClose();
    } catch (err: any) {
      console.error('Create ticker error:', err);
      if (err.message.includes('already exists')) {
        setError(`${selectedTicker} is already in your watchlist`);
      } else {
        setError(err.message || 'Failed to add ticker. Please try again.');
      }
    } finally {
      setIsSubmitting(false);
    }
  };

  const resetForm = () => {
    setTickerSearch('');
    setSelectedTicker('');
    setSelectedTickerName('');
    setSelectedExchange('');
    setIndustry('');
    setActive(true);
    setError(null);
    setTickerError(null);
  };

  const handleClose = () => {
    resetForm();
    onClose();
  };

  return (
    <div className="fixed inset-0 bg-black bg-opacity-50 flex items-center justify-center z-50 p-4">
      <div
        className="bg-white rounded-lg shadow-xl max-w-2xl w-full max-h-[90vh] overflow-y-auto"
        onClick={(e) => e.stopPropagation()}
      >
        {/* Header */}
        <div className="flex items-center justify-between p-6 border-b sticky top-0 bg-white">
          <h2 className="text-2xl font-semibold">Add Ticker to Watchlist</h2>
          <button
            onClick={handleClose}
            className="text-gray-400 hover:text-gray-600"
            disabled={isSubmitting}
          >
            <X className="w-6 h-6" />
          </button>
        </div>

        {/* Form */}
        <form onSubmit={handleSubmit} className="p-6 space-y-6">
          {/* Ticker Symbol - Autocomplete */}
          <div>
            <label className="block text-sm font-medium text-gray-700 mb-2">
              Ticker Symbol <span className="text-red-500">*</span>
            </label>
            <TickerAutocomplete
              value={tickerSearch}
              onChange={setTickerSearch}
              onSelect={handleTickerSelect}
              disabled={isSubmitting}
              error={tickerError || undefined}
            />
            <p className="mt-1 text-sm text-gray-500">
              Search and select a ticker from Alpaca
            </p>
          </div>

          {/* Ticker Name - Read-only after selection */}
          <div>
            <label className="block text-sm font-medium text-gray-700 mb-2">
              Company Name <span className="text-red-500">*</span>
            </label>
            <input
              type="text"
              value={selectedTickerName}
              readOnly
              placeholder="Auto-filled from Alpaca"
              className="w-full px-4 py-2 border border-gray-300 rounded-md bg-gray-50 text-gray-700"
            />
            <p className="mt-1 text-sm text-gray-500">
              Company name is automatically set from Alpaca data
            </p>
          </div>

          {/* Exchange - Read-only after selection */}
          <div>
            <label className="block text-sm font-medium text-gray-700 mb-2">
              Exchange <span className="text-red-500">*</span>
            </label>
            <input
              type="text"
              value={selectedExchange}
              readOnly
              placeholder="Auto-filled from Alpaca"
              className="w-full px-4 py-2 border border-gray-300 rounded-md bg-gray-50 text-gray-700"
            />
            <p className="mt-1 text-sm text-gray-500">
              Exchange is automatically set from Alpaca data
            </p>
          </div>

          {/* Industry - Dropdown */}
          <div>
            <label className="block text-sm font-medium text-gray-700 mb-2">
              Industry <span className="text-red-500">*</span>
            </label>
            <select
              value={industry}
              onChange={(e) => setIndustry(e.target.value)}
              className="w-full px-4 py-2 border border-gray-300 rounded-md focus:ring-2 focus:ring-blue-500 focus:border-transparent"
              disabled={isSubmitting}
            >
              <option value="">Select industry</option>
              {COMMON_INDUSTRIES.map((ind) => (
                <option key={ind} value={ind}>
                  {ind}
                </option>
              ))}
            </select>
          </div>

          {/* Active Status - Toggle */}
          <div>
            <label className="flex items-center gap-3 cursor-pointer">
              <input
                type="checkbox"
                checked={active}
                onChange={(e) => setActive(e.target.checked)}
                className="w-5 h-5 text-blue-600 border-gray-300 rounded focus:ring-2 focus:ring-blue-500"
                disabled={isSubmitting}
              />
              <span className="text-sm font-medium text-gray-700">
                Add to active watchlist
              </span>
            </label>
            <p className="mt-1 ml-8 text-sm text-gray-500">
              Inactive tickers are hidden by default
            </p>
          </div>

          {/* Error Message */}
          {error && (
            <div className="p-4 bg-red-50 border border-red-200 rounded-md">
              <p className="text-sm text-red-600">{error}</p>
            </div>
          )}

          {/* Actions */}
          <div className="flex gap-3 pt-4 border-t">
            <button
              type="button"
              onClick={handleClose}
              className="flex-1 px-4 py-2 border border-gray-300 rounded-md text-gray-700 hover:bg-gray-50 disabled:opacity-50"
              disabled={isSubmitting}
            >
              Cancel
            </button>
            <button
              type="submit"
              className="flex-1 px-4 py-2 bg-blue-600 text-white rounded-md hover:bg-blue-700 disabled:opacity-50"
              disabled={isSubmitting}
            >
              {isSubmitting ? 'Adding...' : 'Add to Watchlist'}
            </button>
          </div>
        </form>
      </div>
    </div>
  );
}
