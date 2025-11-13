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
 * Uses backend date filtering for efficient querying
 */
export async function fetchAnalysesByDate(dateString: string): Promise<AnalysisDecision[]> {
  // Use backend date filtering to get only analyses for the specified date
  const response = await api.getAnalyses({
    date: dateString,
    page_size: 100 // Keep reasonable limit per page for UI performance
  });

  return response.data;
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
  const API_BASE = 'http://localhost:8085';
  return `${API_BASE}${url.startsWith('/') ? url : '/' + url}`;
}
