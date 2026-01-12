'use client';

import Link from 'next/link';
import { Trend } from '@/lib/types';
import { formatNumber } from '@/lib/formatters';
import { ConfidenceBadge } from './ConfidenceBadge';

/**
 * Trend Card Component
 * Displays a single trend with:
 * - Confidence badge
 * - Trend title (truncated to 100 chars)
 * - Platform metrics (Reddit, YouTube, Google Trends, SimilarWeb)
 * - Momentum score
 * - Clickable link to trend detail page
 */

interface TrendCardProps {
  trend: Trend;
}

export function TrendCard({ trend }: TrendCardProps) {
  // Truncate title to 100 chars with ellipsis
  const truncatedTitle = trend.title.length > 100
    ? trend.title.substring(0, 97) + '...'
    : trend.title;

  return (
    <Link href={`/trend/${trend.id}`}>
      <div className="block p-6 bg-white border border-gray-200 rounded-lg shadow hover:shadow-lg transition-shadow cursor-pointer">
        <div className="flex justify-between items-start mb-3">
          <h3 className="text-lg font-semibold text-gray-900 flex-1 mr-2">
            {truncatedTitle}
          </h3>
          <ConfidenceBadge level={trend.confidence_level} />
        </div>

        <div className="flex flex-wrap gap-4 text-sm text-gray-600">
          <span>
            <span className="font-medium">Reddit:</span> {formatNumber(trend.reddit_score)}
          </span>
          <span>
            <span className="font-medium">YouTube:</span> {formatNumber(trend.youtube_views)}
          </span>
          <span>
            <span className="font-medium">Google Trends:</span> {trend.google_trends_interest ?? 'N/A'}
          </span>
          <span>
            <span className="font-medium">SimilarWeb:</span> {formatNumber(trend.similarweb_traffic)}
          </span>
        </div>

        <div className="mt-3 text-xs text-gray-500">
          Momentum Score: {trend.momentum_score.toFixed(1)}
        </div>
      </div>
    </Link>
  );
}
