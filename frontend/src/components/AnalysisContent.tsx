import React, { useState, useEffect } from 'react';
import { Edit2, Save, X } from 'lucide-react';
import type { AnalysisDecision } from '../lib/types';

interface AnalysisContentProps {
  analysis: AnalysisDecision;
  onRemarksUpdate?: (recordId: string, newRemarks: string) => void;
  className?: string;
}

type TabType = 'analysis' | 'prompt' | 'decision' | 'remarks';

export function AnalysisContent({ analysis, onRemarksUpdate, className = '' }: AnalysisContentProps) {
  const [activeTab, setActiveTab] = useState<TabType>('analysis');
  const [isEditingRemarks, setIsEditingRemarks] = useState(false);
  const [remarksText, setRemarksText] = useState(analysis.Remarks || '');

  // Reset to 'analysis' tab whenever a new analysis is loaded
  useEffect(() => {
    setActiveTab('analysis');
    setRemarksText(analysis.Remarks || '');
  }, [analysis.Analysis_Id, analysis.Remarks]);

  const handleSaveRemarks = () => {
    if (onRemarksUpdate) {
      onRemarksUpdate(analysis.Analysis_Id, remarksText);
    }
    setIsEditingRemarks(false);
  };

  const handleCancelRemarks = () => {
    setRemarksText(analysis.Remarks || '');
    setIsEditingRemarks(false);
  };

  return (
    <div className={`bg-white rounded-lg shadow-sm flex flex-col overflow-hidden ${className}`}>
      {/* Tab Headers */}
      <div className="border-b border-gray-200 flex-shrink-0">
        <nav className="flex -mb-px overflow-x-auto">
          <button
            className={`py-3 px-4 sm:py-4 sm:px-6 border-b-2 font-medium text-sm whitespace-nowrap flex-shrink-0 ${
              activeTab === 'analysis'
                ? 'border-blue-500 text-blue-600'
                : 'border-transparent text-gray-500 hover:text-gray-700 hover:border-gray-300'
            }`}
            onClick={() => setActiveTab('analysis')}
          >
            Analysis
          </button>
          <button
            className={`py-3 px-4 sm:py-4 sm:px-6 border-b-2 font-medium text-sm whitespace-nowrap flex-shrink-0 ${
              activeTab === 'prompt'
                ? 'border-blue-500 text-blue-600'
                : 'border-transparent text-gray-500 hover:text-gray-700 hover:border-gray-300'
            }`}
            onClick={() => setActiveTab('prompt')}
          >
            Analysis Prompt
          </button>
          <button
            className={`py-3 px-4 sm:py-4 sm:px-6 border-b-2 font-medium text-sm whitespace-nowrap flex-shrink-0 ${
              activeTab === 'decision'
                ? 'border-blue-500 text-blue-600'
                : 'border-transparent text-gray-500 hover:text-gray-700 hover:border-gray-300'
            }`}
            onClick={() => setActiveTab('decision')}
          >
            Decision
          </button>
          <button
            className={`py-3 px-4 sm:py-4 sm:px-6 border-b-2 font-medium text-sm whitespace-nowrap flex-shrink-0 ${
              activeTab === 'remarks'
                ? 'border-blue-500 text-blue-600'
                : 'border-transparent text-gray-500 hover:text-gray-700 hover:border-gray-300'
            }`}
            onClick={() => setActiveTab('remarks')}
          >
            Remarks
          </button>
        </nav>
      </div>

      {/* Tab Content - Scrollable on desktop, no scrollbar on mobile */}
      <div className="flex-1 overflow-y-auto hidden-scrollbar-mobile">
        <div className="p-4">
          {/* Analysis Tab */}
          {activeTab === 'analysis' && (
            <div className="space-y-4">
              {analysis.Analysis ? (
                <div className="prose prose-sm max-w-none text-gray-900">
                  <div className="whitespace-pre-wrap leading-relaxed">
                    {analysis.Analysis}
                  </div>
                </div>
              ) : (
                <div className="text-gray-500 text-sm">No analysis content available.</div>
              )}
            </div>
          )}

          {/* Analysis Prompt Tab */}
          {activeTab === 'prompt' && (
            <div className="space-y-4">
              {analysis.Analysis_Prompt ? (
                <div className="prose prose-sm max-w-none text-gray-900">
                  <div className="whitespace-pre-wrap leading-relaxed">
                    {analysis.Analysis_Prompt}
                  </div>
                </div>
              ) : (
                <div className="text-gray-500 text-sm">No analysis prompt available.</div>
              )}
            </div>
          )}

          {/* Decision Tab */}
          {activeTab === 'decision' && (
            <div className="space-y-4">
              {analysis.Decision ? (
                <div className="bg-gray-50 p-4 rounded-lg border border-gray-200">
                  <pre className="text-xs text-gray-900 overflow-x-auto whitespace-pre-wrap font-mono">
                    {JSON.stringify(analysis.Decision, null, 2)}
                  </pre>
                </div>
              ) : (
                <div className="text-gray-500 text-sm">No decision data available.</div>
              )}
            </div>
          )}

          {/* Remarks Tab */}
          {activeTab === 'remarks' && (
            <div className="space-y-4">
              <div className="flex items-center justify-between mb-2">
                <h4 className="text-sm font-medium text-gray-700">Remarks</h4>
                {!isEditingRemarks && (
                  <button
                    onClick={() => setIsEditingRemarks(true)}
                    className="text-sm text-blue-600 hover:text-blue-700 flex items-center gap-1"
                  >
                    <Edit2 className="w-4 h-4" />
                    Edit
                  </button>
                )}
              </div>

              {isEditingRemarks ? (
                <div className="space-y-2">
                  <textarea
                    value={remarksText}
                    onChange={(e) => setRemarksText(e.target.value)}
                    rows={8}
                    className="w-full px-3 py-2 border border-gray-300 rounded-lg focus:outline-none focus:ring-2 focus:ring-blue-500"
                    placeholder="Add your remarks here..."
                  />
                  <div className="flex gap-2">
                    <button
                      onClick={handleSaveRemarks}
                      className="inline-flex items-center px-3 py-1.5 bg-blue-600 text-white text-sm rounded-md hover:bg-blue-700 gap-1"
                    >
                      <Save className="w-4 h-4" />
                      Save
                    </button>
                    <button
                      onClick={handleCancelRemarks}
                      className="inline-flex items-center px-3 py-1.5 bg-gray-200 text-gray-700 text-sm rounded-md hover:bg-gray-300 gap-1"
                    >
                      <X className="w-4 h-4" />
                      Cancel
                    </button>
                  </div>
                </div>
              ) : (
                <div className="bg-gray-50 p-4 rounded-lg border border-gray-200 min-h-[120px]">
                  <p className="text-sm text-gray-900 whitespace-pre-wrap">
                    {analysis.Remarks || 'No remarks added yet.'}
                  </p>
                </div>
              )}
            </div>
          )}
        </div>
      </div>
    </div>
  );
}
