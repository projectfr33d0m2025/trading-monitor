import { api } from '../lib/api';
import type { AnalysisDecision } from '../lib/types';

/**
 * Format a Date object to API-compatible date string (YYYY-MM-DD)
 */
export function formatDateForAPI(date: Date): string {
  const year = date.getFullYear();
  const month = String(date.getMonth() + 1).padStart(2, '0');
  const day = String(date.getDate()).padStart(2, '0');
  return `${year}-${month}-${day}`;
}

/**
 * Fetch analyses by date
 * Filters all analyses to only those matching the selected date
 */
export async function fetchAnalysesByDate(dateString: string): Promise<AnalysisDecision[]> {
  // Get all analyses (you may want to add pagination handling here)
  const response = await api.getAnalyses({ page_size: 100 });

  // Filter by date
  const targetDate = new Date(dateString);
  const analyses = response.data.filter(analysis => {
    if (!analysis.Date_time && !analysis.Date) return false;

    const analysisDate = new Date(analysis.Date_time || analysis.Date!);
    return (
      analysisDate.getFullYear() === targetDate.getFullYear() &&
      analysisDate.getMonth() === targetDate.getMonth() &&
      analysisDate.getDate() === targetDate.getDate()
    );
  });

  return analyses;
}

/**
 * Get image URL - handles both relative and absolute URLs
 */
export function getImageUrl(url: string): string {
  // If it's already a full URL (http/https), return as is
  if (url.startsWith('http://') || url.startsWith('https://')) {
    return url;
  }

  // If it's a relative URL, prepend the API base URL
  const API_BASE = 'http://localhost:8000';
  return `${API_BASE}${url.startsWith('/') ? url : '/' + url}`;
}
