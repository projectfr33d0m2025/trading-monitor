import { useState, useEffect } from 'react';
import { Calendar } from 'lucide-react';

interface DateSelectorProps {
  value?: Date;
  onDateSelect: (date: Date) => void;
  inline?: boolean;
}

export function DateSelector({ value, onDateSelect, inline = false }: DateSelectorProps) {
  const [selectedDate, setSelectedDate] = useState<Date>(value || new Date());

  // Sync internal state when external value changes
  useEffect(() => {
    if (value) {
      setSelectedDate(value);
    }
  }, [value]);

  const handleDateChange = (e: React.ChangeEvent<HTMLInputElement>) => {
    const newDate = new Date(e.target.value);
    setSelectedDate(newDate);
    onDateSelect(newDate);
  };

  const formatDateForInput = (date: Date): string => {
    const year = date.getFullYear();
    const month = String(date.getMonth() + 1).padStart(2, '0');
    const day = String(date.getDate()).padStart(2, '0');
    return `${year}-${month}-${day}`;
  };

  if (inline) {
    return (
      <div className="flex items-center w-full">
        <label className="hidden sm:inline text-sm font-medium text-gray-700 whitespace-nowrap mr-2">
          Analysis Date
        </label>
        <div className="relative w-full">
          <input
            type="date"
            value={formatDateForInput(selectedDate)}
            onChange={handleDateChange}
            className="w-full pl-8 pr-2 py-1.5 sm:py-2 border border-gray-300 rounded-md shadow-sm focus:outline-none focus:ring-blue-500 focus:border-blue-500 text-xs sm:text-sm"
          />
          <Calendar className="absolute left-2 top-1/2 transform -translate-y-1/2 text-gray-400 pointer-events-none" size={14} />
        </div>
      </div>
    );
  }

  return (
    <div className="mb-4">
      <label className="block text-sm font-medium text-gray-700 mb-1">
        Analysis Date
      </label>
      <div className="relative">
        <input
          type="date"
          value={formatDateForInput(selectedDate)}
          onChange={handleDateChange}
          className="w-full px-3 py-2 pl-10 border border-gray-300 rounded-md shadow-sm focus:outline-none focus:ring-2 focus:ring-blue-500 focus:border-blue-500"
        />
        <Calendar className="absolute left-3 top-1/2 transform -translate-y-1/2 h-5 w-5 text-gray-400 pointer-events-none" />
      </div>
    </div>
  );
}
