import { Link } from 'react-router-dom';
import { Tag, Clock, Briefcase, FileText } from 'lucide-react';
import type { AnalysisDecision } from '../lib/types';

interface AnalysisDetailsProps {
  analysis: AnalysisDecision;
  className?: string;
}

export function AnalysisDetails({ analysis, className = '' }: AnalysisDetailsProps) {
  const hasTradeJournal = !!analysis.existing_trade_journal_id;

  return (
    <div className={`bg-white rounded-lg shadow-sm border border-gray-200 ${className}`}>
      <div className="p-4 sm:p-6">
        <div className={`grid grid-cols-1 sm:grid-cols-2 ${hasTradeJournal ? 'lg:grid-cols-5' : 'lg:grid-cols-4'} gap-4 sm:gap-6`}>
          {/* Analysis ID */}
          <div className="flex items-start gap-3">
            <div className="flex-shrink-0 mt-1">
              <div className="w-10 h-10 rounded-lg bg-blue-50 flex items-center justify-center">
                <Tag className="w-5 h-5 text-blue-600" />
              </div>
            </div>
            <div className="flex-1 min-w-0">
              <p className="text-xs text-gray-500 mb-1">Analysis ID</p>
              <p className="text-sm font-semibold text-gray-900 break-all">
                {analysis.Analysis_Id}
              </p>
            </div>
          </div>

          {/* Date Time */}
          <div className="flex items-start gap-3">
            <div className="flex-shrink-0 mt-1">
              <div className="w-10 h-10 rounded-lg bg-green-50 flex items-center justify-center">
                <Clock className="w-5 h-5 text-green-600" />
              </div>
            </div>
            <div className="flex-1 min-w-0">
              <p className="text-xs text-gray-500 mb-1">Date Time</p>
              <p className="text-sm font-semibold text-gray-900">
                {analysis.Date_time
                  ? new Date(analysis.Date_time).toLocaleString('en-US', {
                      month: '2-digit',
                      day: '2-digit',
                      year: 'numeric',
                      hour: '2-digit',
                      minute: '2-digit',
                      second: '2-digit',
                      hour12: true
                    })
                  : 'N/A'}
              </p>
            </div>
          </div>

          {/* Ticker */}
          <div className="flex items-start gap-3">
            <div className="flex-shrink-0 mt-1">
              <div className="w-10 h-10 rounded-lg bg-purple-50 flex items-center justify-center">
                <Tag className="w-5 h-5 text-purple-600" />
              </div>
            </div>
            <div className="flex-1 min-w-0">
              <p className="text-xs text-gray-500 mb-1">Ticker</p>
              <p className="text-sm font-semibold text-gray-900">
                {analysis.Ticker}
              </p>
            </div>
          </div>

          {/* Trade Type */}
          <div className="flex items-start gap-3">
            <div className="flex-shrink-0 mt-1">
              <div className="w-10 h-10 rounded-lg bg-amber-50 flex items-center justify-center">
                <Briefcase className="w-5 h-5 text-amber-600" />
              </div>
            </div>
            <div className="flex-1 min-w-0">
              <p className="text-xs text-gray-500 mb-1">Trade Type</p>
              <p className="text-sm font-semibold text-gray-900">
                {analysis.Trade_Type || 'N/A'}
              </p>
            </div>
          </div>

          {/* Trade Journal Link */}
          {hasTradeJournal && (
            <div className="flex items-start gap-3">
              <div className="flex-shrink-0 mt-1">
                <div className="w-10 h-10 rounded-lg bg-indigo-50 flex items-center justify-center">
                  <FileText className="w-5 h-5 text-indigo-600" />
                </div>
              </div>
              <div className="flex-1 min-w-0">
                <p className="text-xs text-gray-500 mb-1">Trade Journal</p>
                <Link
                  to={`/trades?tradeId=${analysis.existing_trade_journal_id}`}
                  className="text-sm font-semibold text-indigo-600 hover:text-indigo-800 hover:underline"
                >
                  View Trade #{analysis.existing_trade_journal_id}
                </Link>
              </div>
            </div>
          )}
        </div>
      </div>
    </div>
  );
}
