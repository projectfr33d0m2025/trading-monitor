import { useState, useEffect } from 'react';
import { Edit2, Save, X } from 'lucide-react';
import type { AnalysisDecision } from '../lib/types';
import ReactMarkdown from 'react-markdown';
import remarkGfm from 'remark-gfm';
import type { Components } from 'react-markdown';

interface AnalysisContentProps {
  analysis: AnalysisDecision;
  onRemarksUpdate?: (recordId: string, newRemarks: string) => void;
  className?: string;
}

type TabType = 'analysis' | 'prompt' | 'decision' | 'remarks';

// Custom components for ReactMarkdown
const markdownComponents: Components = {
  h1: ({children}) => (
    <h1 className="text-2xl font-bold mb-6 text-gray-900">
      {children}
    </h1>
  ),
  h2: ({children}) => (
    <h2 className="text-xl font-semibold mt-6 mb-4 text-gray-800">
      {children}
    </h2>
  ),
  h3: ({children}) => (
    <h3 className="text-lg font-semibold mt-4 mb-3 text-gray-800">
      {children}
    </h3>
  ),
  p: ({children}) => (
    <p className="mb-4 text-gray-700 leading-relaxed">
      {children}
    </p>
  ),
  ul: ({children}) => (
    <ul className="mb-4 ml-6 list-disc space-y-1">
      {children}
    </ul>
  ),
  ol: ({children}) => (
    <ol className="mb-4 ml-6 list-decimal space-y-1">
      {children}
    </ol>
  ),
  li: ({children}) => (
    <li className="text-gray-700 leading-relaxed">
      {children}
    </li>
  ),
  strong: ({children}) => (
    <strong className="font-semibold text-gray-900">
      {children}
    </strong>
  ),
  em: ({children}) => (
    <em className="italic">
      {children}
    </em>
  ),
  blockquote: ({children}) => (
    <blockquote className="border-l-4 border-gray-300 pl-4 my-4 italic text-gray-600">
      {children}
    </blockquote>
  ),
  code: ({className, children, ...props}) => {
    const match = /language-(\w+)/.exec(className || '');
    const isInline = !match;

    if (isInline) {
      return (
        <code className="bg-gray-100 rounded px-1.5 py-0.5 text-sm font-mono text-gray-800">
          {children}
        </code>
      );
    }

    return (
      <code className={className} {...props}>
        {children}
      </code>
    );
  },
  pre: ({children}) => (
    <pre className="bg-gray-100 rounded p-4 overflow-x-auto mb-4 text-sm font-mono">
      {children}
    </pre>
  ),
  hr: () => (
    <hr className="my-8 border-t border-gray-300" />
  ),
  table: ({children}) => (
    <div className="overflow-x-auto mb-4">
      <table className="min-w-full border-collapse border border-gray-300">
        {children}
      </table>
    </div>
  ),
  thead: ({children}) => (
    <thead className="bg-gray-50">
      {children}
    </thead>
  ),
  tbody: ({children}) => (
    <tbody>
      {children}
    </tbody>
  ),
  tr: ({children}) => (
    <tr className="border-b border-gray-200 hover:bg-gray-50">
      {children}
    </tr>
  ),
  th: ({children}) => (
    <th className="text-left font-semibold text-gray-900 p-3 border border-gray-300 bg-gray-100">
      {children}
    </th>
  ),
  td: ({children}) => (
    <td className="p-3 border border-gray-300 text-gray-700">
      {children}
    </td>
  ),
};

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
                <div className="max-w-none">
                  <ReactMarkdown components={markdownComponents} remarkPlugins={[remarkGfm]}>
                    {analysis.Analysis}
                  </ReactMarkdown>
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
                <div className="max-w-none">
                  <ReactMarkdown components={markdownComponents} remarkPlugins={[remarkGfm]}>
                    {analysis.Analysis_Prompt}
                  </ReactMarkdown>
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
