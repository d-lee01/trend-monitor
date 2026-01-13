import React from 'react';
import { render, screen } from '@testing-library/react';
import { redirect, notFound } from 'next/navigation';
import { cookies } from 'next/headers';
import { api, APIError } from '@/lib/api';
import TrendDetailPage, { generateMetadata } from '@/app/trend/[id]/page';
import { TrendDetail } from '@/lib/types';

// Mock Next.js modules
// Note: redirect() and notFound() throw errors in Next.js to stop execution
jest.mock('next/navigation', () => ({
  redirect: jest.fn((url: string) => {
    throw new Error(`NEXT_REDIRECT: ${url}`);
  }),
  notFound: jest.fn(() => {
    throw new Error('NEXT_NOT_FOUND');
  }),
}));

jest.mock('next/headers', () => ({
  cookies: jest.fn(),
}));

// Mock API
jest.mock('@/lib/api', () => ({
  api: {
    getTrendById: jest.fn(),
  },
  APIError: class APIError extends Error {
    constructor(public status: number, message: string) {
      super(message);
      this.name = 'APIError';
    }
  },
}));

// Mock Next.js Link component
jest.mock('next/link', () => {
  return ({ children, href }: { children: React.ReactNode; href: string }) => {
    return <a href={href}>{children}</a>;
  };
});

describe('TrendDetailPage', () => {
  const mockTrendDetail: TrendDetail = {
    id: 'test-id-123',
    title: 'Test Trend Title',
    confidence_level: 'high',
    momentum_score: 87.5,
    created_at: '2026-01-12T07:45:00Z',

    // Reddit
    reddit_score: 15234,
    reddit_velocity_score: 78,
    reddit_subreddit: 'r/videos',
    reddit_url: 'https://reddit.com/r/videos/abc123',
    reddit_upvote_ratio: 0.95,

    // YouTube
    youtube_views: 2534000,
    youtube_traction_score: 82,
    youtube_channel: 'TechChannel',
    youtube_likes: 125000,
    youtube_channel_subscribers: 500000,
    youtube_url: 'https://youtube.com/watch?v=abc',

    // Google Trends
    google_trends_interest: 87,
    google_trends_spike_score: 85,
    google_trends_related_queries: ['query1', 'query2'],

    // SimilarWeb
    similarweb_traffic: 1250000,
    similarweb_traffic_change: 150,
    similarweb_spike_detected: true,
  };

  beforeEach(() => {
    jest.clearAllMocks();

    // Default mock: authenticated user
    (cookies as jest.Mock).mockReturnValue({
      get: jest.fn().mockReturnValue({ value: 'test-token' }),
    });
  });

  it('renders trend detail page with all sections', async () => {
    (api.getTrendById as jest.Mock).mockResolvedValue(mockTrendDetail);

    const page = await TrendDetailPage({ params: { id: 'test-id-123' } });
    render(page);

    // Check title and badge
    expect(screen.getByText('Test Trend Title')).toBeInTheDocument();
    expect(screen.getByText('🔥')).toBeInTheDocument();

    // Check sections exist
    expect(screen.getByText('Platform Breakdown')).toBeInTheDocument();
    expect(screen.getByText('Momentum Score Calculation')).toBeInTheDocument();

    // Check "Back to Dashboard" link
    expect(screen.getByText('Back to Dashboard')).toBeInTheDocument();
  });

  it('redirects to login when no auth token', async () => {
    (cookies as jest.Mock).mockReturnValue({
      get: jest.fn().mockReturnValue(undefined),
    });

    await expect(TrendDetailPage({ params: { id: 'test-id-123' } })).rejects.toThrow('NEXT_REDIRECT');
    expect(redirect).toHaveBeenCalledWith('/?message=Please log in');
  });

  it('redirects to login on 401 error', async () => {
    (api.getTrendById as jest.Mock).mockRejectedValue(new APIError(401, 'Unauthorized'));

    await expect(TrendDetailPage({ params: { id: 'test-id-123' } })).rejects.toThrow('NEXT_REDIRECT');
    expect(redirect).toHaveBeenCalledWith('/?message=Session expired. Please log in again.');
  });

  it('calls notFound on 404 error', async () => {
    (api.getTrendById as jest.Mock).mockRejectedValue(new APIError(404, 'Not found'));

    await expect(TrendDetailPage({ params: { id: 'test-id-123' } })).rejects.toThrow('NEXT_NOT_FOUND');
    expect(notFound).toHaveBeenCalled();
  });

  it('redirects to dashboard on other errors', async () => {
    (api.getTrendById as jest.Mock).mockRejectedValue(new Error('Server error'));

    await expect(TrendDetailPage({ params: { id: 'test-id-123' } })).rejects.toThrow('NEXT_REDIRECT');
    expect(redirect).toHaveBeenCalledWith('/dashboard?message=Failed to load trend details');
  });

  it('fetches trend with correct token and ID', async () => {
    (api.getTrendById as jest.Mock).mockResolvedValue(mockTrendDetail);

    await TrendDetailPage({ params: { id: 'test-id-123' } });

    expect(api.getTrendById).toHaveBeenCalledWith('test-token', 'test-id-123');
  });

  it('displays all platform cards', async () => {
    (api.getTrendById as jest.Mock).mockResolvedValue(mockTrendDetail);

    const page = await TrendDetailPage({ params: { id: 'test-id-123' } });
    render(page);

    // Check for platform card headers (multiple matches expected due to ScoreBreakdown)
    expect(screen.getAllByText('Reddit').length).toBeGreaterThan(0);
    expect(screen.getAllByText('YouTube').length).toBeGreaterThan(0);
    expect(screen.getByText('Google Trends')).toBeInTheDocument();
    expect(screen.getByText('SimilarWeb')).toBeInTheDocument();
  });

  it('displays score breakdown with correct values', async () => {
    (api.getTrendById as jest.Mock).mockResolvedValue(mockTrendDetail);

    const page = await TrendDetailPage({ params: { id: 'test-id-123' } });
    render(page);

    expect(screen.getByText('78.0')).toBeInTheDocument(); // Reddit velocity
    expect(screen.getByText('82.0')).toBeInTheDocument(); // YouTube traction
    expect(screen.getByText('85.0')).toBeInTheDocument(); // Google spike
    expect(screen.getByText('87.5')).toBeInTheDocument(); // Final score
  });

  describe('generateMetadata', () => {
    it('generates metadata with trend title on success', async () => {
      (api.getTrendById as jest.Mock).mockResolvedValue(mockTrendDetail);

      const metadata = await generateMetadata({ params: { id: 'test-id-123' } });

      expect(metadata.title).toContain('Test Trend Title');
      expect(metadata.description).toContain('Test Trend Title');
    });

    it('re-throws redirect errors from generateMetadata', async () => {
      // Mock getTrendById to fail, causing getTrendDetail to redirect
      (api.getTrendById as jest.Mock).mockRejectedValue(new APIError(404, 'Not found'));

      // generateMetadata should re-throw the redirect error
      await expect(generateMetadata({ params: { id: 'test-id-123' } })).rejects.toThrow('NEXT_NOT_FOUND');
    });
  });
});
