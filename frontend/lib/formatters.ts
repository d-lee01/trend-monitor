// Number formatting utilities for Trend Monitor

/**
 * Format large numbers with K/M notation
 * @param num - Number to format (can be null)
 * @returns Formatted string (e.g., "15.2K", "2.5M", or "N/A")
 * @example
 * formatNumber(15234) // "15.2K"
 * formatNumber(2534000) // "2.5M"
 * formatNumber(null) // "N/A"
 */
export function formatNumber(num: number | null): string {
  if (num === null) return 'N/A';

  if (num >= 1_000_000) {
    return `${(num / 1_000_000).toFixed(1)}M`;
  }
  if (num >= 1_000) {
    return `${(num / 1_000).toFixed(1)}K`;
  }
  return num.toString();
}

/**
 * Format percentages with sign
 * @param num - Number to format (can be null)
 * @returns Formatted string with + or - sign (e.g., "+150%", "-25%", or "N/A")
 * @example
 * formatPercent(150.5) // "+150%"
 * formatPercent(-25.3) // "-25%"
 * formatPercent(null) // "N/A"
 */
export function formatPercent(num: number | null): string {
  if (num === null) return 'N/A';
  const sign = num >= 0 ? '+' : '';
  return `${sign}${num.toFixed(0)}%`;
}

/**
 * Calculate relative time from ISO datetime string
 * @param isoDate - ISO 8601 datetime string
 * @returns Human-readable relative time (e.g., "2h ago", "5m ago", "3d ago")
 * @example
 * timeAgo("2026-01-12T10:00:00Z") // "2h ago" (if current time is 12:00)
 */
export function timeAgo(isoDate: string): string {
  const now = new Date();
  const date = new Date(isoDate);
  const diffMs = now.getTime() - date.getTime();
  const diffMins = Math.floor(diffMs / 60000);

  if (diffMins < 60) return `${diffMins}m ago`;

  const diffHours = Math.floor(diffMins / 60);
  if (diffHours < 24) return `${diffHours}h ago`;

  const diffDays = Math.floor(diffHours / 24);
  return `${diffDays}d ago`;
}
