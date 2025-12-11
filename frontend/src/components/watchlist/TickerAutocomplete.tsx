import { useState, useEffect, useRef } from 'react';
import { Search, Loader } from 'lucide-react';
import { api } from '../../lib/api';
import type { AlpacaAsset } from '../../lib/types';

interface TickerAutocompleteProps {
  value: string;
  onChange: (value: string) => void;
  onSelect: (asset: AlpacaAsset) => void;
  disabled?: boolean;
  error?: string;
}

export default function TickerAutocomplete({
  value,
  onChange,
  onSelect,
  disabled,
  error
}: TickerAutocompleteProps) {
  const [isSearching, setIsSearching] = useState(false);
  const [results, setResults] = useState<AlpacaAsset[]>([]);
  const [showDropdown, setShowDropdown] = useState(false);
  const [searchError, setSearchError] = useState<string | null>(null);
  const debounceTimer = useRef<number | null>(null);
  const dropdownRef = useRef<HTMLDivElement>(null);
  const justSelectedRef = useRef(false);
  const abortControllerRef = useRef<AbortController | null>(null);

  // Debounced search
  useEffect(() => {
    // Don't search if we just selected an item
    if (justSelectedRef.current) {
      justSelectedRef.current = false;
      return;
    }

    if (value.length < 1) {
      setResults([]);
      setShowDropdown(false);
      return;
    }

    // Clear previous timer
    if (debounceTimer.current) {
      clearTimeout(debounceTimer.current);
    }

    // Cancel any in-flight request
    if (abortControllerRef.current) {
      abortControllerRef.current.abort();
    }

    // Set new timer
    debounceTimer.current = setTimeout(async () => {
      setIsSearching(true);
      setSearchError(null);

      // Create new AbortController for this request
      const controller = new AbortController();
      abortControllerRef.current = controller;

      try {
        const assets = await api.searchTickers(value, 10, controller.signal);

        // Only update state if request wasn't aborted
        if (!controller.signal.aborted) {
          setResults(assets);
          setShowDropdown(true);
        }
      } catch (err) {
        // Don't show error UI for aborted requests
        if (err instanceof Error && err.name === 'AbortError') {
          console.log('Search request cancelled');
          return;
        }

        console.error('Ticker search error:', err);
        setSearchError('Failed to search tickers. Please try again.');
        setResults([]);
      } finally {
        if (!controller.signal.aborted) {
          setIsSearching(false);
        }
      }
    }, 300); // 300ms debounce

    return () => {
      if (debounceTimer.current) {
        clearTimeout(debounceTimer.current);
      }
      // Cancel in-flight request on unmount or dependency change
      if (abortControllerRef.current) {
        abortControllerRef.current.abort();
      }
    };
  }, [value]);

  // Close dropdown when clicking outside
  useEffect(() => {
    const handleClickOutside = (event: MouseEvent) => {
      if (dropdownRef.current && !dropdownRef.current.contains(event.target as Node)) {
        setShowDropdown(false);
      }
    };

    document.addEventListener('mousedown', handleClickOutside);
    return () => document.removeEventListener('mousedown', handleClickOutside);
  }, []);

  const handleSelect = (asset: AlpacaAsset) => {
    // Set flag to prevent search from triggering when parent updates value
    justSelectedRef.current = true;
    onSelect(asset);
    setShowDropdown(false);
    setResults([]);
  };

  return (
    <div className="relative" ref={dropdownRef}>
      {/* Input Field */}
      <div className="relative">
        <div className="absolute inset-y-0 left-0 pl-3 flex items-center pointer-events-none">
          {isSearching ? (
            <Loader className="w-5 h-5 text-gray-400 animate-spin" />
          ) : (
            <Search className="w-5 h-5 text-gray-400" />
          )}
        </div>
        <input
          type="text"
          value={value}
          onChange={(e) => onChange(e.target.value)}
          placeholder="Search ticker symbol (e.g., AAPL)"
          className={`w-full pl-10 pr-4 py-2 border rounded-md focus:ring-2 focus:ring-blue-500 focus:border-transparent ${
            error ? 'border-red-500' : 'border-gray-300'
          }`}
          disabled={disabled}
        />
      </div>

      {/* Error Message */}
      {error && <p className="mt-1 text-sm text-red-600">{error}</p>}
      {searchError && <p className="mt-1 text-sm text-red-600">{searchError}</p>}

      {/* Dropdown Results */}
      {showDropdown && results.length > 0 && (
        <div className="absolute z-10 w-full mt-1 bg-white border border-gray-300 rounded-md shadow-lg max-h-60 overflow-auto">
          {results.map((asset) => (
            <button
              key={asset.symbol}
              onClick={() => handleSelect(asset)}
              className="w-full px-4 py-3 text-left hover:bg-blue-50 border-b border-gray-100 last:border-b-0"
            >
              <div className="flex items-center justify-between">
                <div>
                  <div className="font-semibold text-gray-900">{asset.symbol}</div>
                  <div className="text-sm text-gray-600">{asset.name}</div>
                </div>
                <div className="text-sm text-gray-500">{asset.exchange}</div>
              </div>
            </button>
          ))}
        </div>
      )}

      {/* No Results */}
      {showDropdown && !isSearching && results.length === 0 && value.length >= 1 && (
        <div className="absolute z-10 w-full mt-1 bg-white border border-gray-300 rounded-md shadow-lg p-4 text-center text-gray-500">
          No tickers found matching "{value}"
        </div>
      )}
    </div>
  );
}
