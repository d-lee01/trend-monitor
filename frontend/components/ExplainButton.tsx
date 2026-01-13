'use client';

import { useState } from 'react';
import { api, APIError } from '@/lib/api';
import { BriefResponse } from '@/lib/types';
import { useRouter } from 'next/navigation';

/**
 * ExplainButton Component (Story 4.2)
 * Interactive button that triggers AI brief generation for a trend
 * Features:
 * - Sparkles icon (✨)
 * - Loading state with spinner
 * - Toggle text: "Explain This Trend" → "Hide Explanation"
 * - Hover effect
 * - Error handling with user-friendly messages
 */

interface ExplainButtonProps {
  trendId: string;
  token: string;
  isExpanded: boolean;
  onBriefGenerated: (brief: BriefResponse) => void;
  onError: (error: string) => void;
  onToggleHide: () => void;
}

export function ExplainButton({
  trendId,
  token,
  isExpanded,
  onBriefGenerated,
  onError,
  onToggleHide
}: ExplainButtonProps) {
  const [loading, setLoading] = useState(false);
  const router = useRouter();

  const handleClick = async () => {
    // If already expanded, just toggle hide
    if (isExpanded) {
      onToggleHide();
      return;
    }

    // Otherwise, generate brief
    setLoading(true);

    try {
      onError(''); // Clear any previous errors
      const brief = await api.generateTrendBrief(token, trendId);
      onBriefGenerated(brief);
    } catch (error) {
      if (error instanceof APIError) {
        if (error.status === 401) {
          // Session expired - redirect to login (don't call onError)
          router.push('/?message=Session expired. Please log in again.');
        } else {
          // Show error message
          onError(error.message);
        }
      } else {
        // Unexpected error
        onError('An unexpected error occurred. Please try again.');
      }
    } finally {
      setLoading(false);
    }
  };

  return (
    <button
      onClick={handleClick}
      disabled={loading}
      aria-label={isExpanded ? "Hide explanation" : "Explain this trend"}
      aria-expanded={isExpanded}
      className={`
        inline-flex items-center px-4 py-2 rounded-lg font-medium text-sm
        transition-all duration-200
        ${loading ? 'bg-gray-100 text-gray-500 cursor-not-allowed' :
          'bg-blue-50 text-blue-700 hover:bg-blue-100 active:bg-blue-200'}
        focus:outline-none focus:ring-2 focus:ring-blue-500 focus:ring-offset-2
      `}
    >
      {loading ? (
        <span className="flex items-center" aria-live="polite" aria-busy="true">
          {/* Spinner Icon */}
          <svg
            className="animate-spin -ml-1 mr-2 h-4 w-4 text-blue-700"
            xmlns="http://www.w3.org/2000/svg"
            fill="none"
            viewBox="0 0 24 24"
            aria-hidden="true"
          >
            <circle
              className="opacity-25"
              cx="12"
              cy="12"
              r="10"
              stroke="currentColor"
              strokeWidth="4"
            />
            <path
              className="opacity-75"
              fill="currentColor"
              d="M4 12a8 8 0 018-8V0C5.373 0 0 5.373 0 12h4zm2 5.291A7.962 7.962 0 014 12H0c0 3.042 1.135 5.824 3 7.938l3-2.647z"
            />
          </svg>
          Generating explanation...
        </span>
      ) : isExpanded ? (
        <>
          {/* Chevron Up Icon */}
          <svg
            className="w-4 h-4 mr-2"
            fill="none"
            stroke="currentColor"
            viewBox="0 0 24 24"
            aria-hidden="true"
          >
            <path
              strokeLinecap="round"
              strokeLinejoin="round"
              strokeWidth={2}
              d="M5 15l7-7 7 7"
            />
          </svg>
          Hide Explanation
        </>
      ) : (
        <>
          {/* Sparkles Icon ✨ */}
          <svg
            className="w-4 h-4 mr-2"
            fill="none"
            stroke="currentColor"
            viewBox="0 0 24 24"
            aria-hidden="true"
          >
            <path
              strokeLinecap="round"
              strokeLinejoin="round"
              strokeWidth={2}
              d="M5 3v4M3 5h4M6 17v4m-2-2h4m5-16l2.286 6.857L21 12l-5.714 2.143L13 21l-2.286-6.857L5 12l5.714-2.143L13 3z"
            />
          </svg>
          Explain This Trend
        </>
      )}
    </button>
  );
}
