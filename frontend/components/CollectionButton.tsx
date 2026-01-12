'use client';

import { useState, useEffect, useCallback } from 'react';
import { useRouter } from 'next/navigation';
import { api, APIError } from '@/lib/api';
import { useToast } from '@/lib/toast';

interface CollectionButtonProps {
  token: string;
}

type CollectionStatus = 'idle' | 'collecting' | 'success' | 'error';

const MAX_DURATION = 30 * 60 * 1000; // 30 minutes in milliseconds
const POLL_INTERVAL = 10000; // 10 seconds

export function CollectionButton({ token }: CollectionButtonProps) {
  const [collectionStatus, setCollectionStatus] = useState<CollectionStatus>('idle');
  const [collectionId, setCollectionId] = useState<string | null>(null);
  const [startTime, setStartTime] = useState<number>(0);
  const router = useRouter();
  const { showToast } = useToast();

  // Cleanup polling on unmount
  useEffect(() => {
    let pollingInterval: NodeJS.Timeout | null = null;

    if (collectionStatus === 'collecting' && collectionId) {
      pollingInterval = setInterval(() => {
        checkCollectionStatus();
      }, POLL_INTERVAL);
    }

    return () => {
      if (pollingInterval) {
        clearInterval(pollingInterval);
      }
    };
  }, [collectionStatus, collectionId]);

  const checkCollectionStatus = useCallback(async () => {
    if (!collectionId) return;

    try {
      const status = await api.getCollectionStatus(token, collectionId);

      // Check for timeout (30 minutes)
      const elapsedTime = Date.now() - startTime;
      if (elapsedTime > MAX_DURATION && status.status === 'in_progress') {
        showToast({
          type: 'warning',
          message: 'Collection taking longer than expected. You can navigate away and return later.',
          duration: 10000, // Show for 10 seconds
        });
        setCollectionStatus('idle');
        setCollectionId(null);
        return;
      }

      if (status.status === 'completed') {
        setCollectionStatus('success');
        setCollectionId(null);
        showToast({
          type: 'success',
          message: `✓ Collection complete! Found ${status.trends_found} trends`,
        });
        // Trigger Next.js revalidation to refresh dashboard data
        router.refresh();
      } else if (status.status === 'failed') {
        setCollectionStatus('error');
        setCollectionId(null);
        showToast({
          type: 'error',
          message: '⚠ Collection failed. Some APIs unavailable. Showing partial results.',
        });
        // Still refresh to show partial results
        router.refresh();
      }
    } catch (error) {
      if (error instanceof APIError && error.status === 401) {
        // Session expired - redirect to login
        window.location.href = '/?message=Session expired. Please log in again.';
        return;
      }
      console.error('Error checking collection status:', error);
    }
  }, [collectionId, token, startTime, router, showToast]);

  const handleCollect = async () => {
    // Prevent double-submit
    if (collectionStatus === 'collecting') return;

    setCollectionStatus('collecting');
    setStartTime(Date.now());

    try {
      const response = await api.triggerCollection(token);
      setCollectionId(response.collection_id);

      // Polling will start automatically via useEffect
    } catch (error) {
      setCollectionStatus('idle');

      if (error instanceof APIError) {
        if (error.status === 409) {
          // Collection already in progress
          showToast({
            type: 'warning',
            message: 'Collection already in progress. Please wait.',
          });
        } else if (error.status === 401) {
          // Unauthorized - redirect to login
          window.location.href = '/?message=Session expired. Please log in again.';
        } else {
          showToast({
            type: 'error',
            message: error.message || 'Failed to start collection.',
          });
        }
      } else {
        showToast({
          type: 'error',
          message: 'Failed to start collection. Please try again.',
        });
      }
    }
  };

  const isLoading = collectionStatus === 'collecting';

  return (
    <button
      onClick={handleCollect}
      disabled={isLoading}
      className="px-4 py-2 bg-blue-600 text-white rounded-lg hover:bg-blue-700 transition-colors disabled:opacity-50 disabled:cursor-not-allowed flex items-center gap-2"
      aria-busy={isLoading}
      aria-label={isLoading ? 'Collection in progress' : 'Collect latest trends'}
    >
      {isLoading && (
        <svg
          className="animate-spin h-4 w-4"
          xmlns="http://www.w3.org/2000/svg"
          fill="none"
          viewBox="0 0 24 24"
          role="status"
          aria-label="Loading"
        >
          <circle
            className="opacity-25"
            cx="12"
            cy="12"
            r="10"
            stroke="currentColor"
            strokeWidth="4"
          ></circle>
          <path
            className="opacity-75"
            fill="currentColor"
            d="M4 12a8 8 0 018-8V0C5.373 0 0 5.373 0 12h4zm2 5.291A7.962 7.962 0 014 12H0c0 3.042 1.135 5.824 3 7.938l3-2.647z"
          ></path>
        </svg>
      )}
      {isLoading ? 'Collecting...' : 'Collect Latest Trends'}
    </button>
  );
}
