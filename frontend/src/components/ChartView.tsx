import { TrendingUp } from 'lucide-react';

interface ChartViewProps {
  symbol: string;
}

export function ChartView({ symbol }: ChartViewProps) {
  return (
    <div className="h-full flex items-center justify-center bg-gray-100 rounded-lg p-8">
      <div className="text-center text-gray-500">
        <TrendingUp className="mx-auto h-12 w-12 text-gray-400 mb-3" />
        <p className="text-sm font-medium">Chart for {symbol}</p>
        <p className="text-xs mt-1">Chart visualization coming soon</p>
      </div>
    </div>
  );
}
