import { ChevronDown } from 'lucide-react';
import type { AnalysisDecision } from '../lib/types';

interface SymbolDropdownProps {
  analyses: AnalysisDecision[];
  selectedSymbol: string | null;
  onSymbolSelect: (symbol: string) => void;
  inline?: boolean;
}

export function SymbolDropdown({
  analyses,
  selectedSymbol,
  onSymbolSelect,
  inline = false
}: SymbolDropdownProps) {
  // Get unique symbols from analyses
  const symbols = Array.from(new Set(analyses.map(a => a.Ticker))).sort();

  const handleSymbolChange = (e: React.ChangeEvent<HTMLSelectElement>) => {
    const symbol = e.target.value;
    if (symbol) {
      onSymbolSelect(symbol);
    }
  };

  if (inline) {
    return (
      <div className="flex items-center w-full min-w-0">
        <label className="hidden sm:inline text-base font-medium text-gray-700 whitespace-nowrap mr-2">
          Symbol
        </label>
        <div className="relative w-full min-w-0">
          <select
            value={selectedSymbol || ''}
            onChange={handleSymbolChange}
            className="w-full max-w-full pl-2 pr-7 py-1.5 sm:py-2 text-sm sm:text-base border border-gray-300 rounded-md shadow-sm focus:outline-none focus:ring-blue-500 focus:border-blue-500 appearance-none bg-white truncate"
            disabled={symbols.length === 0}
          >
            <option value="">
              {symbols.length === 0 ? 'No symbols available' : 'Select a symbol'}
            </option>
            {symbols.map(symbol => (
              <option key={symbol} value={symbol}>
                {symbol}
              </option>
            ))}
          </select>
          <ChevronDown className="absolute right-1 top-1/2 transform -translate-y-1/2 h-4 w-4 text-gray-400 pointer-events-none" />
        </div>
      </div>
    );
  }

  return (
    <div className="mb-4">
      <label className="block text-sm font-medium text-gray-700 mb-1">
        Symbol
      </label>
      <div className="relative">
        <select
          value={selectedSymbol || ''}
          onChange={handleSymbolChange}
          className="w-full px-3 py-2 pr-10 border border-gray-300 rounded-md shadow-sm focus:outline-none focus:ring-2 focus:ring-blue-500 focus:border-blue-500 appearance-none bg-white"
          disabled={symbols.length === 0}
        >
          <option value="">
            {symbols.length === 0 ? 'No symbols available' : 'Select a symbol'}
          </option>
          {symbols.map(symbol => (
            <option key={symbol} value={symbol}>
              {symbol}
            </option>
          ))}
        </select>
        <ChevronDown className="absolute right-3 top-1/2 transform -translate-y-1/2 h-5 w-5 text-gray-400 pointer-events-none" />
      </div>
    </div>
  );
}
