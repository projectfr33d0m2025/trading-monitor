import { useState, useEffect } from 'react';
import { X } from 'lucide-react';
import { api } from '../../lib/api';
import type { TickerWatchlist } from '../../lib/types';

interface EditTickerModalProps {
  ticker: TickerWatchlist | null;
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
  'Other'
];

export default function EditTickerModal({ ticker, isOpen, onClose, onSuccess }: EditTickerModalProps) {
  const [industry, setIndustry] = useState('');
  const [active, setActive] = useState(true);
  const [isSubmitting, setIsSubmitting] = useState(false);
  const [error, setError] = useState<string | null>(null);

  // Initialize form with ticker data
  useEffect(() => {
    if (ticker) {
      setIndustry(ticker.Industry);
      setActive(ticker.Active);
      setError(null);
    }
  }, [ticker]);

  if (!isOpen || !ticker) return null;

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    setError(null);

    if (!industry) {
      setError('Please select an industry');
      return;
    }

    setIsSubmitting(true);

    try {
      await api.updateWatchlistTicker(ticker.id, {
        Industry: industry,
        Active: active
      });

      // Success - close modal
      onSuccess();
      onClose();
    } catch (err: any) {
      console.error('Update ticker error:', err);
      setError(err.message || 'Failed to update ticker. Please try again.');
    } finally {
      setIsSubmitting(false);
    }
  };

  const handleClose = () => {
    setError(null);
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
          <h2 className="text-2xl font-semibold">Edit Ticker: {ticker.Ticker}</h2>
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
          {/* Ticker Symbol - Locked */}
          <div>
            <label className="block text-sm font-medium text-gray-700 mb-2">
              Ticker Symbol
            </label>
            <input
              type="text"
              value={ticker.Ticker}
              readOnly
              className="w-full px-4 py-2 border border-gray-300 rounded-md bg-gray-100 text-gray-600 cursor-not-allowed"
            />
            <p className="mt-1 text-sm text-gray-500">
              Ticker symbol cannot be changed
            </p>
          </div>

          {/* Exchange - Locked */}
          <div>
            <label className="block text-sm font-medium text-gray-700 mb-2">
              Exchange
            </label>
            <input
              type="text"
              value={ticker.Exchange || 'N/A'}
              readOnly
              className="w-full px-4 py-2 border border-gray-300 rounded-md bg-gray-100 text-gray-600 cursor-not-allowed"
            />
            <p className="mt-1 text-sm text-gray-500">
              Exchange cannot be changed (locked to Alpaca data)
            </p>
          </div>

          {/* Note */}
          <div className="p-4 bg-blue-50 border border-blue-200 rounded-md">
            <p className="text-sm text-blue-800">
              <strong>Note:</strong> Ticker and Exchange cannot be changed. To change these fields, delete this entry and create a new one.
            </p>
          </div>

          {/* Industry - Editable */}
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

          {/* Active Status - Editable */}
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
                Active in watchlist
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
              {isSubmitting ? 'Updating...' : 'Update Ticker'}
            </button>
          </div>
        </form>
      </div>
    </div>
  );
}
