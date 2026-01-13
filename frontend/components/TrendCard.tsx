'use client';

import { useState } from 'react';
import Link from 'next/link';
import { Trend, BriefResponse } from '@/lib/types';
import { formatNumber } from '@/lib/formatters';
import { ConfidenceBadge } from './ConfidenceBadge';
import { ExplainButton } from './ExplainButton';
import { BriefDisplay } from './BriefDisplay';

/**
 * Trend Card Component (Story 4.2)
 * Displays a single trend with:
 * - Confidence badge
 * - Trend title (truncated to 100 chars)
 * - Platform metrics (Reddit, YouTube, Google Trends, SimilarWeb)
 * - Momentum score
 * - Clickable link to trend detail page
 * - "Explain This Trend" button with AI brief display
 */

interface TrendCardProps {
  trend: Trend;
  token: string; // JWT token for API calls
}

export function TrendCard({ trend, token }: TrendCardProps) {
  // State for brief functionality (independent per card)
  const [brief, setBrief] = useState<BriefResponse | null>(null);
  const [error, setError] = useState<string>('');

  // Truncate title to 100 chars with ellipsis
  const truncatedTitle = trend.title.length > 100
    ? trend.title.substring(0, 97) + '...'
    : trend.title;

  const handleBriefGenerated = (generatedBrief: BriefResponse) => {
    setBrief(generatedBrief);
    setError('');
  };

  const handleError = (errorMessage: string) => {
    setError(errorMessage);
  };

  const handleToggleHide = () => {
    setBrief(null);
    setError('');
  };

  const handleRetry = () => {
    setError('');
    // Retry will be handled by clicking the button again
  };

  return (
    <div className="block p-6 bg-white border border-gray-200 rounded-lg shadow hover:shadow-lg transition-all">
      {/* Clickable area for navigation */}
      <Link href={`/trend/${trend.id}`} className="block group">
        <div className="flex justify-between items-start mb-3 cursor-pointer">
          <h3 className="text-lg font-semibold text-gray-900 flex-1 mr-2 group-hover:text-blue-600 transition-colors">
            {truncatedTitle}
          </h3>
          <ConfidenceBadge confidenceLevel={trend.confidence_level} size="small" />
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
      </Link>

      {/* Explain button (not wrapped in Link - independent click) */}
      <div className="mt-4" onClick={(e) => e.stopPropagation()}>
        <ExplainButton
          trendId={trend.id}
          token={token}
          isExpanded={!!brief}
          onBriefGenerated={handleBriefGenerated}
          onError={handleError}
          onToggleHide={handleToggleHide}
        />
      </div>

      {/* Error display */}
      {error && (
        <div
          className="mt-4 p-3 bg-red-50 border border-red-200 rounded-lg"
          role="alert"
          onClick={(e) => e.stopPropagation()}
        >
          <p className="text-red-800 text-sm flex items-center">
            <svg
              className="w-4 h-4 mr-2 flex-shrink-0"
              fill="none"
              stroke="currentColor"
              viewBox="0 0 24 24"
              aria-hidden="true"
            >
              <path
                strokeLinecap="round"
                strokeLinejoin="round"
                strokeWidth={2}
                d="M12 9v2m0 4h.01m-6.938 4h13.856c1.54 0 2.502-1.667 1.732-3L13.732 4c-.77-1.333-2.694-1.333-3.464 0L3.34 16c-.77 1.333.192 3 1.732 3z"
              />
            </svg>
            ⚠ {error}
          </p>
          <button
            onClick={handleRetry}
            className="text-red-600 hover:text-red-800 text-sm font-medium mt-2 underline"
          >
            Try Again
          </button>
        </div>
      )}

      {/* Brief display */}
      {brief && (
        <div onClick={(e) => e.stopPropagation()}>
          <BriefDisplay
            brief={brief.ai_brief}
            generatedAt={brief.generated_at}
            cached={brief.cached}
            onClose={handleToggleHide}
          />
        </div>
      )}
    </div>
  );
}
