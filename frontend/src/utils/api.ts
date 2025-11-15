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
 * @param imageData - NocoDB image JSON string: '[{"path": "download/...", ...}]'
 * @returns Full URL to the image
 */
export function getImageUrl(imageData: string): string {
  if (!imageData) {
    return '';
  }

  try {
    const parsedData: Array<{ path: string }> = JSON.parse(imageData);

    if (!parsedData || parsedData.length === 0 || !parsedData[0].path) {
      return '';
    }

    const NOCODB_BASE = import.meta.env.VITE_NOCODB_BASE_URL || 'http://localhost:8080';
    const path = parsedData[0].path;

    // Ensure path doesn't start with / since it's already in the correct format
    return `${NOCODB_BASE}/${path.startsWith('/') ? path.substring(1) : path}`;
  } catch (error) {
    console.error('Failed to parse image data:', error);
    return '';
  }
}
