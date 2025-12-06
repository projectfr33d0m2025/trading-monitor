import React, { useState } from 'react';
import type { DateRange, DateRangePreset } from '../../types/analytics';

interface DateRangeFilterProps {
  selectedRange: DateRange;
  onRangeChange: (range: DateRange) => void;
  onRefresh?: () => void;
}

export function DateRangeFilter({ selectedRange, onRangeChange, onRefresh }: DateRangeFilterProps) {
  const [showCustomPicker, setShowCustomPicker] = useState(false);
  const [customStartDate, setCustomStartDate] = useState('');
  const [customEndDate, setCustomEndDate] = useState('');

  const presets: { label: string; value: DateRangePreset; days?: number }[] = [
    { label: '7 Days', value: '7d', days: 7 },
    { label: '30 Days', value: '30d', days: 30 },
    { label: '90 Days', value: '90d', days: 90 },
    { label: 'YTD', value: 'ytd' },
    { label: 'All Time', value: 'all' },
    { label: 'Custom', value: 'custom' },
  ];

  const handlePresetClick = (preset: DateRangePreset, days?: number) => {
    if (preset === 'custom') {
      setShowCustomPicker(!showCustomPicker);
      return;
    }

    const endDate = new Date();
    let startDate: Date | null = null;

    if (preset === '7d' || preset === '30d' || preset === '90d') {
      startDate = new Date();
      startDate.setDate(startDate.getDate() - (days || 0));
    } else if (preset === 'ytd') {
      startDate = new Date(endDate.getFullYear(), 0, 1);
    } else if (preset === 'all') {
      startDate = null;
    }

    onRangeChange({
      start_date: startDate ? startDate.toISOString().split('T')[0] : null,
      end_date: endDate.toISOString().split('T')[0],
      preset,
    });

    setShowCustomPicker(false);
  };

  const handleCustomDateApply = () => {
    if (!customStartDate || !customEndDate) {
      alert('Please select both start and end dates');
      return;
    }

    onRangeChange({
      start_date: customStartDate,
      end_date: customEndDate,
      preset: 'custom',
    });

    setShowCustomPicker(false);
  };

  return (
    <div className="bg-white rounded-lg shadow-sm p-4 mb-6">
      <div className="flex items-center justify-between flex-wrap gap-4">
        <div className="flex items-center gap-2 flex-wrap">
          <span className="text-sm font-medium text-gray-700">Time Range:</span>
          {presets.map((preset) => (
            <button
              key={preset.value}
              onClick={() => handlePresetClick(preset.value, preset.days)}
              className={`px-4 py-2 rounded-md text-sm font-medium transition-colors ${
                selectedRange.preset === preset.value
                  ? 'bg-blue-600 text-white'
                  : 'bg-gray-100 text-gray-700 hover:bg-gray-200'
              }`}
            >
              {preset.label}
            </button>
          ))}
        </div>

        {onRefresh && (
          <button
            onClick={onRefresh}
            className="px-4 py-2 bg-green-600 text-white rounded-md text-sm font-medium hover:bg-green-700 transition-colors flex items-center gap-2"
          >
            <svg
              xmlns="http://www.w3.org/2000/svg"
              className="h-4 w-4"
              fill="none"
              viewBox="0 0 24 24"
              stroke="currentColor"
            >
              <path
                strokeLinecap="round"
                strokeLinejoin="round"
                strokeWidth={2}
                d="M4 4v5h.582m15.356 2A8.001 8.001 0 004.582 9m0 0H9m11 11v-5h-.581m0 0a8.003 8.003 0 01-15.357-2m15.357 2H15"
              />
            </svg>
            Refresh
          </button>
        )}
      </div>

      {showCustomPicker && (
        <div className="mt-4 p-4 bg-gray-50 rounded-md">
          <div className="flex items-end gap-4 flex-wrap">
            <div className="flex-1 min-w-[200px]">
              <label htmlFor="start-date" className="block text-sm font-medium text-gray-700 mb-1">
                Start Date
              </label>
              <input
                id="start-date"
                type="date"
                value={customStartDate}
                onChange={(e) => setCustomStartDate(e.target.value)}
                className="w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-blue-500"
              />
            </div>

            <div className="flex-1 min-w-[200px]">
              <label htmlFor="end-date" className="block text-sm font-medium text-gray-700 mb-1">
                End Date
              </label>
              <input
                id="end-date"
                type="date"
                value={customEndDate}
                onChange={(e) => setCustomEndDate(e.target.value)}
                className="w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-blue-500"
              />
            </div>

            <button
              onClick={handleCustomDateApply}
              className="px-6 py-2 bg-blue-600 text-white rounded-md text-sm font-medium hover:bg-blue-700 transition-colors"
            >
              Apply
            </button>
          </div>
        </div>
      )}

      {selectedRange.start_date && selectedRange.end_date && selectedRange.preset !== 'all' && (
        <div className="mt-3 text-sm text-gray-600">
          Showing data from{' '}
          <span className="font-medium">{selectedRange.start_date}</span> to{' '}
          <span className="font-medium">{selectedRange.end_date}</span>
        </div>
      )}

      {selectedRange.preset === 'all' && (
        <div className="mt-3 text-sm text-gray-600">
          Showing <span className="font-medium">all-time</span> data
        </div>
      )}
    </div>
  );
}
