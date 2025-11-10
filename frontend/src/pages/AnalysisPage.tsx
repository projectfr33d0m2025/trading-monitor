import React, { useEffect, useState } from 'react';
import { useSearchParams } from 'react-router-dom';
import { DateSelector } from '../components/DateSelector';
import { SymbolDropdown } from '../components/SymbolDropdown';
import { AnalysisDetails } from '../components/AnalysisDetails';
import { AnalysisContent } from '../components/AnalysisContent';
import { ChartView } from '../components/ChartView';
import type { AnalysisDecision } from '../lib/types';
import { api } from '../lib/api';
import { fetchAnalysesByDate, formatDateForAPI, getImageUrl } from '../utils/api';
import { ChevronDown, ChevronUp, Filter } from 'lucide-react';
import '../styles/analysis.css';

export default function AnalysisPage() {
  const [searchParams] = useSearchParams();
  const [selectedDate, setSelectedDate] = useState<Date | null>(null);
  const [analyses, setAnalyses] = useState<AnalysisDecision[]>([]);
  const [selectedSymbol, setSelectedSymbol] = useState<string | null>(null);
  const [currentAnalysis, setCurrentAnalysis] = useState<AnalysisDecision | null>(null);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [activeChartTab, setActiveChartTab] = useState<'3month' | '1year'>('3month');
  const [filtersCollapsed, setFiltersCollapsed] = useState(false);

  const handleDateSelect = async (date: Date) => {
    setSelectedDate(date);
    setSelectedSymbol(null);
    setCurrentAnalysis(null);
    setError(null);

    setLoading(true);

    try {
      const formattedDate = formatDateForAPI(date);
      const fetchedAnalyses = await fetchAnalysesByDate(formattedDate);
      setAnalyses(fetchedAnalyses);
    } catch (err) {
      console.error('Error fetching analyses:', err);
      setError(err instanceof Error ? err.message : 'Failed to fetch analyses');
      setAnalyses([]);
    } finally {
      setLoading(false);
    }
  };

  const handleSymbolSelect = (symbol: string) => {
    setSelectedSymbol(symbol);
    const analysis = analyses.find(a => a.Ticker === symbol);
    if (analysis) {
      setCurrentAnalysis(analysis);
    }
  };

  const handleRemarksUpdate = (analysisId: string, newRemarks: string) => {
    setAnalyses(prevAnalyses =>
      prevAnalyses.map(a =>
        a.Analysis_Id === analysisId
          ? { ...a, Remarks: newRemarks }
          : a
      )
    );

    if (currentAnalysis && currentAnalysis.Analysis_Id === analysisId) {
      setCurrentAnalysis({
        ...currentAnalysis, Remarks: newRemarks
      });
    }
  };

  useEffect(() => {
    const initializePage = async () => {
      // Check for URL parameters
      const urlAnalysisId = searchParams.get('analysisId');
      const urlSymbol = searchParams.get('symbol');
      const urlDate = searchParams.get('date');

      // Priority 1: Direct analysis ID lookup
      if (urlAnalysisId) {
        setLoading(true);
        setError(null);

        try {
          const analysis = await api.getAnalysis(urlAnalysisId);
          setCurrentAnalysis(analysis);

          // Extract and set the date from the analysis
          const analysisDate = new Date(analysis.Date_time || analysis.Date || new Date());
          setSelectedDate(analysisDate);

          // Fetch all analyses for that date to populate the dropdown
          const formattedDate = formatDateForAPI(analysisDate);
          const fetchedAnalyses = await fetchAnalysesByDate(formattedDate);
          setAnalyses(fetchedAnalyses);

          // Set the selected symbol (use full ticker format to match dropdown)
          setSelectedSymbol(analysis.Ticker);
        } catch (err) {
          console.error('Error fetching analysis by ID:', err);
          setError(err instanceof Error ? err.message : 'Failed to fetch analysis');
        } finally {
          setLoading(false);
        }
        return;
      }

      // Priority 2: Date + Symbol lookup (legacy/manual navigation)
      if (urlDate) {
        // Parse the date from URL (format: YYYY-MM-DD)
        const date = new Date(urlDate);
        if (!isNaN(date.getTime())) {
          setSelectedDate(date);
          setLoading(true);
          setError(null);

          try {
            const formattedDate = formatDateForAPI(date);
            const fetchedAnalyses = await fetchAnalysesByDate(formattedDate);
            setAnalyses(fetchedAnalyses);

            // If symbol is also provided, auto-select it (normalize symbol comparison)
            if (urlSymbol) {
              const analysis = fetchedAnalyses.find(a =>
                a.Ticker.split(':')[0] === urlSymbol.split(':')[0]
              );
              if (analysis) {
                setSelectedSymbol(analysis.Ticker);
                setCurrentAnalysis(analysis);
              }
            }
          } catch (err) {
            console.error('Error fetching analyses:', err);
            setError(err instanceof Error ? err.message : 'Failed to fetch analyses');
            setAnalyses([]);
          } finally {
            setLoading(false);
          }
          return;
        }
      }

      // Fallback to today if no valid URL params
      if (!selectedDate) {
        const today = new Date();
        handleDateSelect(today);
      }
    };

    initializePage();
  }, []);

  return (
    <div className="h-screen flex flex-col lg:h-screen lg:flex lg:flex-col">
      <div className="lg:contents">
        <div className="px-3 sm:px-4 lg:px-6 py-2 sm:py-4 bg-white shadow-sm border-b analysis-main-content lg:flex-shrink-0">
          <div className="flex items-center justify-between mb-2 sm:mb-4">
            <h2 className="text-lg sm:text-2xl font-bold ml-10 sm:ml-0">Analysis & Decision</h2>
            <button
              onClick={() => setFiltersCollapsed(!filtersCollapsed)}
              className="sm:hidden p-1.5 hover:bg-gray-100 rounded-md transition-colors flex items-center gap-1 text-sm text-gray-600"
              aria-label={filtersCollapsed ? "Show filters" : "Hide filters"}
            >
              <Filter size={16} />
              {filtersCollapsed ? <ChevronDown size={16} /> : <ChevronUp size={16} />}
            </button>
          </div>

          <div className={`${filtersCollapsed ? 'hidden' : 'flex'} sm:flex flex-row gap-2 sm:gap-4 analysis-selectors w-full transition-all duration-200`}>
            <div className="flex-1 min-w-0">
              <DateSelector
                value={selectedDate || undefined}
                onDateSelect={handleDateSelect}
                inline
              />
            </div>
            <div className="flex-1 min-w-0">
              <SymbolDropdown
                analyses={analyses}
                selectedSymbol={selectedSymbol}
                onSymbolSelect={handleSymbolSelect}
                inline
              />
            </div>
          </div>
        </div>

        <div className="p-3 sm:p-4 lg:p-6 lg:flex-1 lg:min-h-0 lg:overflow-hidden">
          {loading && (
            <div className="flex items-center justify-center p-8 lg:h-full">
              <div className="flex flex-col items-center">
                <div className="animate-spin rounded-full h-12 w-12 border-b-2 border-blue-500"></div>
                <p className="mt-4 text-gray-600">Loading analyses...</p>
              </div>
            </div>
          )}

          {error && (
            <div className="bg-red-50 p-4 rounded-lg border border-red-200">
              <div className="flex">
                <div className="flex-shrink-0">
                  <svg className="h-5 w-5 text-red-400" xmlns="http://www.w3.org/2000/svg" viewBox="0 0 20 20" fill="currentColor">
                    <path fillRule="evenodd" d="M10 18a8 8 0 100-16 8 8 0 000 16zM8.707 7.293a1 1 0 00-1.414 1.414L8.586 10l-1.293 1.293a1 1 0 101.414 1.414L10 11.414l1.293 1.293a1 1 0 001.414-1.414L11.414 10l1.293-1.293a1 1 0 00-1.414-1.414L10 8.586 8.707 7.293z" clipRule="evenodd" />
                  </svg>
                </div>
                <div className="ml-3">
                  <h3 className="text-sm font-medium text-red-800">Error loading data</h3>
                  <div className="mt-2 text-sm text-red-700">
                    <p>{error}</p>
                  </div>
                </div>
              </div>
            </div>
          )}

          {currentAnalysis && (
            <div className="lg:flex lg:flex-col lg:h-full lg:overflow-hidden">
              <AnalysisDetails analysis={currentAnalysis} className="mb-3 sm:mb-4 lg:flex-shrink-0" />

              <div className="hidden lg:grid grid-cols-2 gap-6 flex-1 min-h-0 analysis-grid">
                <div className="flex flex-col min-h-0">
                  <AnalysisContent
                    analysis={currentAnalysis}
                    onRemarksUpdate={handleRemarksUpdate}
                    className="flex-1"
                  />
                </div>
                <div className="flex flex-col min-h-0">
                  <div className="bg-white rounded-lg shadow-sm flex flex-col h-full overflow-hidden">
                    <div className="border-b border-gray-200 flex-shrink-0 overflow-x-auto chart-tabs">
                      <nav className="flex -mb-px min-w-max">
                        <button
                          className={`py-3 px-4 sm:py-4 sm:px-6 border-b-2 font-medium text-sm whitespace-nowrap flex-shrink-0 ${
                            activeChartTab === '3month'
                              ? 'border-blue-500 text-blue-600'
                              : 'border-transparent text-gray-500 hover:text-gray-700 hover:border-gray-300'
                          }`}
                          onClick={() => setActiveChartTab('3month')}
                        >
                          3 Month Chart
                        </button>
                        <button
                          className={`py-3 px-4 sm:py-4 sm:px-6 border-b-2 font-medium text-sm whitespace-nowrap flex-shrink-0 ${
                            activeChartTab === '1year'
                              ? 'border-blue-500 text-blue-600'
                              : 'border-transparent text-gray-500 hover:text-gray-700 hover:border-gray-300'
                          }`}
                          onClick={() => setActiveChartTab('1year')}
                        >
                          1 Year Chart
                        </button>
                      </nav>
                    </div>

                    <div className="p-4 flex-1 min-h-0 flex flex-col">
                      <div className="flex-1 min-h-0 relative">
                        {activeChartTab === '3month' && (
                          <div className="h-full chart-image-container">
                            {currentAnalysis["3_Month_Chart"] || currentAnalysis.Chart ? (
                              <>
                                <img
                                  src={getImageUrl(currentAnalysis["3_Month_Chart"] || currentAnalysis.Chart!)}
                                  alt="3 Month Chart"
                                  className="w-full h-full rounded-lg chart-image"
                                  onError={(e) => {
                                    const target = e.currentTarget;
                                    target.style.display = 'none';
                                    const fallback = target.nextElementSibling;
                                    if (fallback) {
                                      (fallback as HTMLElement).style.display = 'block';
                                    }
                                  }}
                                />
                                <div className="hidden bg-gray-100 rounded-lg p-8 text-center text-gray-500">
                                  <svg className="mx-auto h-12 w-12 text-gray-400" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                                    <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M4 16l4.586-4.586a2 2 0 012.828 0L16 16m-2-2l1.586-1.586a2 2 0 012.828 0L20 14m-6-6h.01M6 20h12a2 2 0 002-2V6a2 2 0 00-2-2H6a2 2 0 00-2 2v12a2 2 0 002 2z" />
                                  </svg>
                                  <p className="mt-2">3 Month Chart unavailable</p>
                                </div>
                              </>
                            ) : (
                              <ChartView symbol={currentAnalysis.Ticker} />
                            )}
                          </div>
                        )}

                        {activeChartTab === '1year' && (
                          <div className="h-full chart-image-container">
                            {currentAnalysis.Chart ? (
                              <>
                                <img
                                  src={getImageUrl(currentAnalysis.Chart)}
                                  alt="1 Year Chart"
                                  className="w-full h-full rounded-lg chart-image"
                                  onError={(e) => {
                                    const target = e.currentTarget;
                                    target.style.display = 'none';
                                    const fallback = target.nextElementSibling;
                                    if (fallback) {
                                      (fallback as HTMLElement).style.display = 'block';
                                    }
                                  }}
                                />
                                <div className="hidden bg-gray-100 rounded-lg p-8 text-center text-gray-500">
                                  <svg className="mx-auto h-12 w-12 text-gray-400" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                                    <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M4 16l4.586-4.586a2 2 0 012.828 0L16 16m-2-2l1.586-1.586a2 2 0 012.828 0L20 14m-6-6h.01M6 20h12a2 2 0 002-2V6a2 2 0 00-2-2H6a2 2 0 00-2 2v12a2 2 0 002 2z" />
                                  </svg>
                                  <p className="mt-2">1 Year Chart unavailable</p>
                                </div>
                              </>
                            ) : (
                              <ChartView symbol={currentAnalysis.Ticker} />
                            )}
                          </div>
                        )}
                      </div>
                    </div>
                  </div>
                </div>
              </div>

              <div className="lg:hidden">
                <div className="pb-4">
                  <AnalysisContent
                    analysis={currentAnalysis}
                    onRemarksUpdate={handleRemarksUpdate}
                    className="min-h-[300px]"
                  />
                </div>

                <div className="bg-white rounded-lg shadow-sm p-3 sm:p-4 mb-4">
                  <div className="border-b border-gray-200 mb-3 sm:mb-4">
                    <nav className="flex -mb-px">
                      <button
                        className={`py-2 px-3 sm:py-3 sm:px-4 border-b-2 font-medium text-sm transition-colors ${
                          activeChartTab === '3month'
                            ? 'border-blue-500 text-blue-600'
                            : 'border-transparent text-gray-500 hover:text-gray-700 hover:border-gray-300'
                        }`}
                        onClick={() => setActiveChartTab('3month')}
                      >
                        3 Month
                      </button>
                      <button
                        className={`py-2 px-3 sm:py-3 sm:px-4 border-b-2 font-medium text-sm transition-colors ${
                          activeChartTab === '1year'
                            ? 'border-blue-500 text-blue-600'
                            : 'border-transparent text-gray-500 hover:text-gray-700 hover:border-gray-300'
                        }`}
                        onClick={() => setActiveChartTab('1year')}
                      >
                        1 Year
                      </button>
                    </nav>
                  </div>

                  <div className="h-[300px] overflow-hidden">
                    {activeChartTab === '3month' && (currentAnalysis["3_Month_Chart"] || currentAnalysis.Chart) && (
                      <img
                        src={getImageUrl(currentAnalysis["3_Month_Chart"] || currentAnalysis.Chart!)}
                        alt="3 Month Chart"
                        className="w-full h-full object-contain rounded-lg"
                      />
                    )}
                    {activeChartTab === '1year' && currentAnalysis.Chart && (
                      <img
                        src={getImageUrl(currentAnalysis.Chart)}
                        alt="1 Year Chart"
                        className="w-full h-full object-contain rounded-lg"
                      />
                    )}
                    {!currentAnalysis["3_Month_Chart"] && !currentAnalysis.Chart && (
                      <ChartView symbol={currentAnalysis.Ticker} />
                    )}
                  </div>
                </div>
              </div>
            </div>
          )}

          {!loading && !currentAnalysis && analyses.length > 0 && (
            <div className="bg-blue-50 p-4 rounded-lg border border-blue-200 text-blue-700">
              <div className="flex">
                <div className="flex-shrink-0">
                  <svg className="h-5 w-5 text-blue-400" xmlns="http://www.w3.org/2000/svg" viewBox="0 0 20 20" fill="currentColor">
                    <path fillRule="evenodd" d="M18 10a8 8 0 11-16 0 8 8 0 0116 0zm-7-4a1 1 0 11-2 0 1 1 0 012 0zM9 9a1 1 0 000 2v3a1 1 0 001 1h1a1 1 0 100-2v-3a1 1 0 00-1-1H9z" clipRule="evenodd" />
                  </svg>
                </div>
                <div className="ml-3">
                  <p className="text-sm">Please select a symbol from the dropdown to view analysis details.</p>
                </div>
              </div>
            </div>
          )}

          {!loading && !currentAnalysis && analyses.length === 0 && selectedDate && !error && (
            <div className="bg-gray-50 p-8 rounded-lg text-center">
              <svg className="mx-auto h-12 w-12 text-gray-400" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M9 12h6m-6 4h6m2 5H7a2 2 0 01-2-2V5a2 2 0 012-2h5.586a1 1 0 01.707.293l5.414 5.414a1 1 0 01.293.707V19a2 2 0 01-2 2z" />
              </svg>
              <h3 className="mt-2 text-sm font-medium text-gray-900">No analyses found</h3>
              <p className="mt-1 text-sm text-gray-500">
                No analyses available for {selectedDate.toLocaleDateString()}.
              </p>
              <p className="mt-1 text-sm text-gray-500">
                Try selecting a different date.
              </p>
            </div>
          )}

          {!loading && !selectedDate && (
            <div className="bg-gray-50 p-8 rounded-lg text-center">
              <svg className="mx-auto h-12 w-12 text-gray-400" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M8 7V3m8 4V3m-9 8h10M5 21h14a2 2 0 002-2V7a2 2 0 00-2-2H5a2 2 0 00-2 2v12a2 2 0 002 2z" />
              </svg>
              <h3 className="mt-2 text-sm font-medium text-gray-900">Select a date</h3>
              <p className="mt-1 text-sm text-gray-500">
                Please select a date to view analyses.
              </p>
            </div>
          )}
        </div>
      </div>
    </div>
  );
}
