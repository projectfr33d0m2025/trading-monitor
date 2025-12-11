import { Pencil, Trash2 } from 'lucide-react';
import type { TickerWatchlist } from '../../lib/types';

interface WatchlistCardProps {
  ticker: TickerWatchlist;
  onEdit: (ticker: TickerWatchlist) => void;
  onDelete: (ticker: TickerWatchlist) => void;
}

export default function WatchlistCard({ ticker, onEdit, onDelete }: WatchlistCardProps) {
  return (
    <div className="bg-white rounded-lg shadow border border-gray-200 p-4 hover:shadow-md transition-shadow">
      {/* Header with Ticker and Actions */}
      <div className="flex items-start justify-between mb-3">
        <div>
          <h3 className="text-xl font-bold text-gray-900">{ticker.Ticker}</h3>
          {ticker.Ticker_Name && (
            <p className="text-sm text-gray-600 mt-1">{ticker.Ticker_Name}</p>
          )}
        </div>
        <div className="flex gap-2">
          <button
            onClick={() => onEdit(ticker)}
            className="p-2 text-gray-600 hover:text-blue-600 hover:bg-blue-50 rounded transition-colors"
            title="Edit ticker"
          >
            <Pencil className="w-4 h-4" />
          </button>
          <button
            onClick={() => onDelete(ticker)}
            className="p-2 text-gray-600 hover:text-red-600 hover:bg-red-50 rounded transition-colors"
            title="Delete ticker"
          >
            <Trash2 className="w-4 h-4" />
          </button>
        </div>
      </div>

      {/* Divider */}
      <div className="border-t border-gray-200 mb-3"></div>

      {/* Details */}
      <div className="space-y-2">
        {/* Exchange */}
        {ticker.Exchange && (
          <div className="flex items-center gap-2">
            <span className="text-sm text-gray-500">Exchange:</span>
            <span className="text-sm font-medium text-gray-700">{ticker.Exchange}</span>
          </div>
        )}

        {/* Industry */}
        {ticker.Industry && (
          <div className="flex items-center gap-2">
            <span className="text-sm text-gray-500">Industry:</span>
            <span className="text-sm font-medium text-gray-700">{ticker.Industry}</span>
          </div>
        )}

        {/* Active Status */}
        <div className="flex items-center gap-2">
          <span className="text-sm text-gray-500">Status:</span>
          <span
            className={`px-2 py-1 text-xs font-medium rounded ${
              ticker.Active
                ? 'bg-green-100 text-green-800'
                : 'bg-gray-100 text-gray-600'
            }`}
          >
            {ticker.Active ? 'Active' : 'Inactive'}
          </span>
        </div>
      </div>
    </div>
  );
}
