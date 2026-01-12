import React from 'react';
import { render, screen } from '@testing-library/react';
import DashboardPage from '@/app/dashboard/page';
import { api } from '@/lib/api';
import { cookies } from 'next/headers';
import { redirect, useRouter } from 'next/navigation';

// Mock Next.js modules
jest.mock('next/headers', () => ({
  cookies: jest.fn(),
}));

jest.mock('next/navigation', () => ({
  redirect: jest.fn(),
  useRouter: jest.fn(),
}));

// Mock API client
jest.mock('@/lib/api', () => ({
  api: {
    getTrends: jest.fn(),
    getLatestCollection: jest.fn(),
    triggerCollection: jest.fn(),
    getCollectionStatus: jest.fn(),
  },
  APIError: class APIError extends Error {
    constructor(public status: number, message: string) {
      super(message);
      this.name = 'APIError';
    }
  },
}));

// Mock child components
jest.mock('@/components/TrendCard', () => ({
  TrendCard: ({ trend }: { trend: any }) => (
    <div data-testid={`trend-card-${trend.id}`}>
      {trend.title}
    </div>
  ),
}));

jest.mock('@/components/CollectionButton', () => ({
  CollectionButton: ({ token }: { token: string }) => (
    <button>Collect Latest Trends</button>
  ),
}));

describe('Dashboard Page', () => {
  const mockCookies = cookies as jest.MockedFunction<typeof cookies>;
  const mockRedirect = redirect as jest.MockedFunction<typeof redirect>;
  const mockUseRouter = useRouter as jest.Mock;
  const mockGetTrends = api.getTrends as jest.MockedFunction<typeof api.getTrends>;
  const mockGetLatestCollection = api.getLatestCollection as jest.MockedFunction<typeof api.getLatestCollection>;

  const mockRouter = {
    refresh: jest.fn(),
    push: jest.fn(),
    back: jest.fn(),
    forward: jest.fn(),
    prefetch: jest.fn(),
    replace: jest.fn(),
  };

  beforeEach(() => {
    jest.clearAllMocks();
    // By default, redirect doesn't throw (for tests that don't test redirect behavior)
    mockRedirect.mockImplementation(() => {});
    // Mock useRouter for CollectionButton
    mockUseRouter.mockReturnValue(mockRouter);
  });

  it('redirects to login when no auth token present', async () => {
    mockCookies.mockReturnValue({
      get: jest.fn().mockReturnValue(undefined),
    } as any);

    // redirect() throws an error in Next.js to stop execution
    mockRedirect.mockImplementation(() => {
      throw new Error('NEXT_REDIRECT');
    });

    await expect(DashboardPage()).rejects.toThrow('NEXT_REDIRECT');
    expect(mockRedirect).toHaveBeenCalledWith('/?message=Please log in');
  });

  it('renders dashboard with Top 10 trends', async () => {
    const mockToken = 'valid-jwt-token';
    mockCookies.mockReturnValue({
      get: jest.fn().mockReturnValue({ value: mockToken }),
    } as any);

    const mockTrends = [
      {
        id: 'trend-1',
        title: 'Test Trend 1',
        confidence_level: 'high' as const,
        momentum_score: 95.5,
        reddit_score: 15234,
        youtube_views: 2534000,
        google_trends_interest: 87,
        similarweb_traffic: 1250000,
        created_at: '2026-01-12T07:45:00Z',
      },
      {
        id: 'trend-2',
        title: 'Test Trend 2',
        confidence_level: 'medium' as const,
        momentum_score: 82.3,
        reddit_score: 8500,
        youtube_views: 950000,
        google_trends_interest: 65,
        similarweb_traffic: 750000,
        created_at: '2026-01-12T06:30:00Z',
      },
    ];

    mockGetTrends.mockResolvedValue(mockTrends);
    mockGetLatestCollection.mockResolvedValue({
      id: 'collection-1',
      started_at: '2026-01-12T07:00:00Z',
      completed_at: '2026-01-12T07:30:00Z',
      status: 'completed',
      trends_found: 10,
    });

    const result = await DashboardPage();
    const { container } = render(result);

    expect(screen.getByText('trend-monitor')).toBeInTheDocument();
    expect(screen.getByText('Trending Now - Top 10')).toBeInTheDocument();
    expect(screen.getByTestId('trend-card-trend-1')).toBeInTheDocument();
    expect(screen.getByTestId('trend-card-trend-2')).toBeInTheDocument();
  });

  it('displays empty state message when no trends available', async () => {
    const mockToken = 'valid-jwt-token';
    mockCookies.mockReturnValue({
      get: jest.fn().mockReturnValue({ value: mockToken }),
    } as any);

    mockGetTrends.mockResolvedValue([]);
    mockGetLatestCollection.mockResolvedValue(null);

    const result = await DashboardPage();
    render(result);

    expect(screen.getByText(/No trends available yet/i)).toBeInTheDocument();
    expect(screen.getByText(/Click "Collect Latest Trends" to start data collection/i)).toBeInTheDocument();
  });

  it('displays "Last Updated" timestamp when collection exists', async () => {
    const mockToken = 'valid-jwt-token';
    mockCookies.mockReturnValue({
      get: jest.fn().mockReturnValue({ value: mockToken }),
    } as any);

    // Mock current time for consistent test
    jest.useFakeTimers();
    jest.setSystemTime(new Date('2026-01-12T12:00:00Z'));

    mockGetTrends.mockResolvedValue([]);
    mockGetLatestCollection.mockResolvedValue({
      id: 'collection-1',
      started_at: '2026-01-12T10:00:00Z',
      completed_at: '2026-01-12T10:30:00Z',
      status: 'completed',
      trends_found: 0,
    });

    const result = await DashboardPage();
    render(result);

    // Should display "Last Updated: 1h ago" (12:00 - 10:30 = 1.5h = 1h displayed)
    expect(screen.getByText(/Last Updated:/i)).toBeInTheDocument();
    expect(screen.getByText(/1h ago/i)).toBeInTheDocument();

    jest.useRealTimers();
  });

  it('hides "Last Updated" when no collection exists', async () => {
    const mockToken = 'valid-jwt-token';
    mockCookies.mockReturnValue({
      get: jest.fn().mockReturnValue({ value: mockToken }),
    } as any);

    mockGetTrends.mockResolvedValue([]);
    mockGetLatestCollection.mockResolvedValue(null);

    const result = await DashboardPage();
    render(result);

    expect(screen.queryByText(/Last Updated:/i)).not.toBeInTheDocument();
  });

  it('handles API errors gracefully', async () => {
    const mockToken = 'valid-jwt-token';
    mockCookies.mockReturnValue({
      get: jest.fn().mockReturnValue({ value: mockToken }),
    } as any);

    mockGetTrends.mockRejectedValue(new Error('API Error'));
    mockGetLatestCollection.mockRejectedValue(new Error('API Error'));

    const result = await DashboardPage();
    render(result);

    // Should still render page with empty state
    expect(screen.getByText('trend-monitor')).toBeInTheDocument();
    expect(screen.getByText(/No trends available yet/i)).toBeInTheDocument();
  });

  it('displays "Collect Latest Trends" button', async () => {
    const mockToken = 'valid-jwt-token';
    mockCookies.mockReturnValue({
      get: jest.fn().mockReturnValue({ value: mockToken }),
    } as any);

    mockGetTrends.mockResolvedValue([]);
    mockGetLatestCollection.mockResolvedValue(null);

    const result = await DashboardPage();
    const { container } = render(result);

    const button = screen.getByText('Collect Latest Trends');
    expect(button).toBeInTheDocument();
    expect(button).not.toBeDisabled();
  });
});
