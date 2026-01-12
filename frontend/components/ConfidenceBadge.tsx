'use client';

/**
 * Confidence Badge Component
 * Displays confidence level for trends with emoji indicators:
 * - 🔥 High: All 4 signals aligned
 * - ⚡ Medium: 2-3 signals present
 * - 👀 Low: 1 signal present
 */

interface ConfidenceBadgeProps {
  level: 'high' | 'medium' | 'low';
}

export function ConfidenceBadge({ level }: ConfidenceBadgeProps) {
  const config = {
    high: {
      emoji: '🔥',
      bg: 'bg-red-100',
      text: 'text-red-800',
      border: 'border-red-300',
      tooltip: 'High confidence - All 4 signals aligned'
    },
    medium: {
      emoji: '⚡',
      bg: 'bg-yellow-100',
      text: 'text-yellow-800',
      border: 'border-yellow-300',
      tooltip: 'Medium confidence - 2-3 signals present'
    },
    low: {
      emoji: '👀',
      bg: 'bg-blue-100',
      text: 'text-blue-800',
      border: 'border-blue-300',
      tooltip: 'Low confidence - 1 signal present'
    }
  };

  const { emoji, bg, text, border, tooltip } = config[level];

  return (
    <span
      className={`inline-flex items-center px-2 py-1 rounded-full text-xs font-medium border ${bg} ${text} ${border}`}
      title={tooltip}
    >
      <span className="mr-1">{emoji}</span>
      {level.toUpperCase()}
    </span>
  );
}
