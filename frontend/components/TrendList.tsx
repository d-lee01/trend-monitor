'use client';

import { Trend } from '@/lib/types';
import { formatNumber, timeAgo } from '@/lib/formatters';
import { useState } from 'react';

interface TrendListProps {
  trends: Trend[];
  token: string;
}

export function TrendList({ trends, token }: TrendListProps) {
  const [expandedId, setExpandedId] = useState<string | null>(null);

  // Sort by momentum score
  const sortedTrends = [...trends].sort((a, b) => b.momentum_score - a.momentum_score);

  // Determine which source(s) a trend comes from
  const getSourceBadges = (trend: Trend) => {
    const sources = [];
    if (trend.youtube_views !== null && trend.youtube_views > 0) sources.push('YouTube');
    if (trend.reddit_score !== null && trend.reddit_score > 0) sources.push('Reddit');
    if (trend.google_trends_interest !== null && trend.google_trends_interest > 0) sources.push('Google');
    if (trend.similarweb_traffic !== null && trend.similarweb_traffic > 0) sources.push('SimilarWeb');
    return sources;
  };

  // Get metrics for display
  const getMetrics = (trend: Trend) => {
    const metrics: Array<{ icon: string; label: string; value: number | string }> = [];

    if (trend.youtube_views !== null && trend.youtube_views > 0) {
      metrics.push({ icon: '👁️', label: 'YouTube views', value: formatNumber(trend.youtube_views) });
    }
    if (trend.reddit_score !== null && trend.reddit_score > 0) {
      metrics.push({ icon: '⬆️', label: 'Reddit score', value: formatNumber(trend.reddit_score) });
    }
    if (trend.google_trends_interest !== null && trend.google_trends_interest > 0) {
      metrics.push({ icon: '📈', label: 'Google interest', value: trend.google_trends_interest });
    }
    if (trend.similarweb_traffic !== null && trend.similarweb_traffic > 0) {
      metrics.push({ icon: '🌐', label: 'SimilarWeb traffic', value: formatNumber(trend.similarweb_traffic) });
    }

    return metrics;
  };

  return (
    <div className="space-y-3">
      {sortedTrends.map((trend) => {
        const sources = getSourceBadges(trend);
        const metrics = getMetrics(trend);

        return (
          <div
            key={trend.id}
            className="border border-gray-200 rounded-lg p-4 hover:border-[#542E91] transition-colors cursor-pointer"
            onClick={() => setExpandedId(expandedId === trend.id ? null : trend.id)}
            style={{ fontFamily: 'Arial, sans-serif' }}
          >
            <div className="flex items-start justify-between">
              {/* Left side - Trend info */}
              <div className="flex-1">
                <h4 className="font-bold text-gray-900 text-lg mb-2">
                  {trend.title}
                </h4>

                {/* Metrics */}
                <div className="flex flex-wrap gap-4 text-sm text-gray-600 mb-3">
                  <span className="flex items-center gap-1">
                    📊 Score: <span className="font-bold text-[#542E91]">{trend.momentum_score.toFixed(1)}</span>
                  </span>

                  {metrics.map((metric, idx) => (
                    <span key={idx} className="flex items-center gap-1" title={metric.label}>
                      {metric.icon} {metric.value}
                    </span>
                  ))}
                </div>

                {/* Source badges and confidence */}
                <div className="flex items-center gap-3 text-xs">
                  <span
                    className="px-2 py-1 rounded-full font-bold text-white"
                    style={{
                      backgroundColor: trend.confidence_level === 'high' ? '#542E91' : trend.confidence_level === 'medium' ? '#6B3AAF' : '#9CA3AF'
                    }}
                  >
                    {trend.confidence_level} confidence
                  </span>

                  {sources.map((source) => (
                    <span key={source} className="px-2 py-1 bg-gray-100 text-gray-700 rounded-full">
                      {source}
                    </span>
                  ))}

                  <span className="text-gray-500">{timeAgo(trend.created_at)}</span>
                </div>
              </div>

              {/* Right side - Expand indicator */}
              <div className="ml-4">
                <span className="text-gray-400 text-xl">
                  {expandedId === trend.id ? '▼' : '▶'}
                </span>
              </div>
            </div>

            {/* Expanded details */}
            {expandedId === trend.id && (
              <div className="mt-4 pt-4 border-t border-gray-200">
                <div className="grid grid-cols-1 md:grid-cols-2 gap-4 text-sm">
                  {/* YouTube details */}
                  {trend.youtube_views !== null && trend.youtube_views > 0 && (
                    <div className="space-y-1">
                      <h5 className="font-bold text-gray-900">YouTube</h5>
                      <p className="text-gray-600">Views: {formatNumber(trend.youtube_views)}</p>
                    </div>
                  )}

                  {/* Reddit details */}
                  {trend.reddit_score !== null && trend.reddit_score > 0 && (
                    <div className="space-y-1">
                      <h5 className="font-bold text-gray-900">Reddit</h5>
                      <p className="text-gray-600">Score: {formatNumber(trend.reddit_score)}</p>
                    </div>
                  )}

                  {/* Google Trends details */}
                  {trend.google_trends_interest !== null && trend.google_trends_interest > 0 && (
                    <div className="space-y-1">
                      <h5 className="font-bold text-gray-900">Google Trends</h5>
                      <p className="text-gray-600">Interest: {trend.google_trends_interest}</p>
                    </div>
                  )}

                  {/* SimilarWeb details */}
                  {trend.similarweb_traffic !== null && trend.similarweb_traffic > 0 && (
                    <div className="space-y-1">
                      <h5 className="font-bold text-gray-900">SimilarWeb</h5>
                      <p className="text-gray-600">Traffic: {formatNumber(trend.similarweb_traffic)}</p>
                    </div>
                  )}
                </div>
              </div>
            )}
          </div>
        );
      })}
    </div>
  );
}
