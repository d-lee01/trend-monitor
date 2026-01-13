'use client';

/**
 * Platform Card Component
 * Displays platform-specific trend data with normalized score visualization
 */

type Platform = 'reddit' | 'youtube' | 'googletrends' | 'similarweb';

interface PlatformData {
  // Common
  score?: number | null;
  // Reddit
  velocity_score?: number | null;
  subreddit?: string | null;
  upvote_ratio?: number | null;
  // YouTube
  views?: number | null;
  traction_score?: number | null;
  channel?: string | null;
  likes?: number | null;
  // Google Trends
  interest?: number | null;
  spike_score?: number | null;
  related_queries?: string[] | null;
  // SimilarWeb
  traffic?: number | null;
  traffic_change?: number | null;
  spike_detected?: boolean | null;
}

interface PlatformCardProps {
  platform: Platform;
  data: PlatformData;
  normalizedScore: number;
  externalUrl?: string;
}

export function PlatformCard({ platform, data, normalizedScore, externalUrl }: PlatformCardProps) {
  // Platform-specific configuration
  const getPlatformConfig = () => {
    switch (platform) {
      case 'reddit':
        return {
          name: 'Reddit',
          icon: '🔴',
          bgColor: 'bg-orange-50',
          borderColor: 'border-orange-200',
          primaryMetric: data.score ?? null,
          primaryLabel: 'Score',
          secondaryMetrics: [
            { label: 'Velocity Score', value: data.velocity_score ?? null },
            { label: 'Subreddit', value: data.subreddit ?? null },
            { label: 'Upvote Ratio', value: data.upvote_ratio ? `${(data.upvote_ratio * 100).toFixed(0)}%` : null },
          ],
        };
      case 'youtube':
        return {
          name: 'YouTube',
          icon: '▶️',
          bgColor: 'bg-red-50',
          borderColor: 'border-red-200',
          primaryMetric: data.views ?? null,
          primaryLabel: 'Views',
          secondaryMetrics: [
            { label: 'Traction Score', value: data.traction_score ?? null },
            { label: 'Channel', value: data.channel ?? null },
            { label: 'Likes', value: data.likes ?? null },
          ],
        };
      case 'googletrends':
        return {
          name: 'Google Trends',
          icon: '📈',
          bgColor: 'bg-blue-50',
          borderColor: 'border-blue-200',
          primaryMetric: data.interest ?? null,
          primaryLabel: 'Interest',
          secondaryMetrics: [
            { label: 'Spike Score', value: data.spike_score ?? null },
            { label: 'Related Queries', value: data.related_queries?.slice(0, 2).join(', ') ?? null },
          ],
        };
      case 'similarweb':
        return {
          name: 'SimilarWeb',
          icon: '📊',
          bgColor: 'bg-purple-50',
          borderColor: 'border-purple-200',
          primaryMetric: data.traffic ?? null,
          primaryLabel: 'Traffic',
          secondaryMetrics: [
            { label: 'Traffic Change', value: data.traffic_change !== null && data.traffic_change !== undefined ? `${data.traffic_change.toFixed(0)}%` : null },
            { label: 'Spike Detected', value: data.spike_detected !== null ? (data.spike_detected ? 'Yes' : 'No') : null },
          ],
        };
      default:
        return {
          name: 'Unknown',
          icon: '❓',
          bgColor: 'bg-gray-50',
          borderColor: 'border-gray-200',
          primaryMetric: null,
          primaryLabel: 'N/A',
          secondaryMetrics: [],
        };
    }
  };

  const config = getPlatformConfig();

  // Format numbers for display
  const formatNumber = (value: number | null | undefined): string => {
    if (value === null || value === undefined) return 'N/A';

    if (value >= 1000000) {
      return `${(value / 1000000).toFixed(1)}M`;
    }
    if (value >= 1000) {
      return `${(value / 1000).toFixed(1)}K`;
    }
    return value.toFixed(0);
  };

  // Format metric value
  const formatMetricValue = (value: number | string | null | undefined): string => {
    if (value === null || value === undefined) return 'N/A';
    if (typeof value === 'string') return value;
    return formatNumber(value);
  };

  return (
    <div className={`${config.bgColor} border ${config.borderColor} rounded-lg p-4 shadow-sm`}>
      {/* Platform Header */}
      <div className="flex items-center justify-between mb-3">
        <div className="flex items-center gap-2">
          <span className="text-2xl" aria-hidden="true">{config.icon}</span>
          <h3 className="text-lg font-semibold text-gray-900">{config.name}</h3>
        </div>
      </div>

      {/* Primary Metric */}
      <div className="mb-3">
        <p className="text-sm text-gray-600">{config.primaryLabel}</p>
        <p className="text-2xl font-bold text-gray-900">
          {formatMetricValue(config.primaryMetric)}
        </p>
      </div>

      {/* Normalized Score Progress Bar */}
      <div className="mb-3">
        <div className="flex items-center justify-between text-sm text-gray-600 mb-1">
          <span>Normalized Score</span>
          <span className="font-semibold">{normalizedScore}/100</span>
        </div>
        <div className="w-full bg-gray-200 rounded-full h-2.5">
          <div
            className="bg-gradient-to-r from-blue-500 to-purple-600 h-2.5 rounded-full transition-all duration-300"
            style={{ width: `${Math.min(100, Math.max(0, normalizedScore))}%` }}
            role="progressbar"
            aria-valuenow={Math.min(100, Math.max(0, normalizedScore))}
            aria-valuemin={0}
            aria-valuemax={100}
          ></div>
        </div>
      </div>

      {/* Secondary Metrics */}
      <div className="space-y-1 mb-3">
        {config.secondaryMetrics.map((metric, index) => (
          <div key={index} className="flex items-center justify-between text-sm">
            <span className="text-gray-600">{metric.label}:</span>
            <span className="text-gray-900 font-medium">{formatMetricValue(metric.value)}</span>
          </div>
        ))}
      </div>

      {/* External Link */}
      {externalUrl && (
        <a
          href={externalUrl}
          target="_blank"
          rel="noopener noreferrer"
          className="inline-flex items-center gap-1 text-sm text-blue-600 hover:text-blue-800 transition-colors font-medium"
        >
          View on {config.name}
          <svg className="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
            <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M10 6H6a2 2 0 00-2 2v10a2 2 0 002 2h10a2 2 0 002-2v-4M14 4h6m0 0v6m0-6L10 14" />
          </svg>
        </a>
      )}
    </div>
  );
}
