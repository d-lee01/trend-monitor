'use client';

import { useState } from 'react';

/**
 * Confidence Badge Component
 * Displays confidence level for trends with emoji indicators and hover tooltip:
 * - 🔥 High: All 4 platform signals aligned
 * - ⚡ Medium: 2-3 signals
 * - 👀 Low: 1 signal
 *
 * Supports two sizes: small (text-2xl) for cards, large (text-4xl) for detail page
 */

interface ConfidenceBadgeProps {
  confidenceLevel: 'high' | 'medium' | 'low';
  size?: 'small' | 'large';
}

export function ConfidenceBadge({ confidenceLevel, size = 'small' }: ConfidenceBadgeProps) {
  const [showTooltip, setShowTooltip] = useState(false);

  // Map confidence level to emoji
  const getEmoji = () => {
    switch (confidenceLevel) {
      case 'high':
        return '🔥';
      case 'medium':
        return '⚡';
      case 'low':
        return '👀';
      default:
        return '👀';
    }
  };

  // Map confidence level to tooltip text
  const getTooltipText = () => {
    switch (confidenceLevel) {
      case 'high':
        return 'High Confidence: All 4 platform signals aligned';
      case 'medium':
        return 'Medium: 2-3 signals';
      case 'low':
        return 'Low: 1 signal';
      default:
        return 'Low: 1 signal';
    }
  };

  // Map confidence level to color classes
  const getColorClass = () => {
    switch (confidenceLevel) {
      case 'high':
        return 'text-orange-500';
      case 'medium':
        return 'text-amber-500';
      case 'low':
        return 'text-gray-500';
      default:
        return 'text-gray-500';
    }
  };

  // Map size to text size class
  const getSizeClass = () => {
    return size === 'large' ? 'text-4xl' : 'text-2xl';
  };

  return (
    <div className="relative inline-block">
      <span
        className={`${getSizeClass()} ${getColorClass()} cursor-help transition-transform hover:scale-110`}
        onMouseEnter={() => setShowTooltip(true)}
        onMouseLeave={() => setShowTooltip(false)}
        role="img"
        aria-label={`Confidence level: ${confidenceLevel}`}
      >
        {getEmoji()}
      </span>

      {/* Tooltip */}
      {showTooltip && (
        <div
          className="absolute left-1/2 -translate-x-1/2 bottom-full mb-2 px-3 py-2 bg-gray-900 text-white text-sm rounded-lg whitespace-nowrap z-10 shadow-lg"
          role="tooltip"
        >
          {getTooltipText()}
          {/* Tooltip arrow */}
          <div className="absolute left-1/2 -translate-x-1/2 top-full w-0 h-0 border-l-8 border-r-8 border-t-8 border-l-transparent border-r-transparent border-t-gray-900"></div>
        </div>
      )}
    </div>
  );
}
