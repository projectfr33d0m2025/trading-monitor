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
 * Get image URL from NocoDB image format
 * @param imageData - NocoDB image array format: [{"path": "download/...", ...}]
 * @returns Full URL to the image
 */
export function getImageUrl(imageData: Array<{ path: string }>): string {
  if (!imageData || imageData.length === 0 || !imageData[0].path) {
    return '';
  }

  const NOCODB_BASE = import.meta.env.VITE_NOCODB_BASE_URL || 'http://localhost:8080';
  const path = imageData[0].path;

  // Ensure path doesn't start with / since it's already in the correct format
  return `${NOCODB_BASE}/${path.startsWith('/') ? path.substring(1) : path}`;
}
