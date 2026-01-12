import React from 'react';
import { render, screen } from '@testing-library/react';
import { TrendCard } from '@/components/TrendCard';
import { Trend } from '@/lib/types';

// Mock Next.js Link component
jest.mock('next/link', () => {
  return ({ children, href }: { children: React.ReactNode; href: string }) => {
    return <a href={href}>{children}</a>;
  };
});

describe('TrendCard Component', () => {
  const mockTrend: Trend = {
    id: 'test-id-123',
    title: 'Test Trend Title',
    confidence_level: 'high',
    momentum_score: 87.5,
    reddit_score: 15234,
    youtube_views: 2534000,
    google_trends_interest: 87,
    similarweb_traffic: 1250000,
    created_at: '2026-01-12T07:45:00Z'
  };

  it('renders trend card with all fields', () => {
    render(<TrendCard trend={mockTrend} />);

    // Check title
    expect(screen.getByText('Test Trend Title')).toBeInTheDocument();

    // Check confidence badge
    expect(screen.getByText(/HIGH/i)).toBeInTheDocument();

    // Check metrics are displayed
    expect(screen.getByText(/Reddit:/i)).toBeInTheDocument();
    expect(screen.getByText(/YouTube:/i)).toBeInTheDocument();
    expect(screen.getByText(/Google Trends:/i)).toBeInTheDocument();
    expect(screen.getByText(/SimilarWeb:/i)).toBeInTheDocument();

    // Check momentum score (text is split across elements, use regex)
    expect(screen.getByText(/Momentum Score:/i)).toBeInTheDocument();
    expect(screen.getByText((content, element) => {
      return element?.textContent === 'Momentum Score: 87.5';
    })).toBeInTheDocument();
  });

  it('formats numbers correctly (15234 → "15.2K")', () => {
    render(<TrendCard trend={mockTrend} />);

    // Reddit score should be formatted
    expect(screen.getByText('15.2K')).toBeInTheDocument();
  });

  it('formats large numbers correctly (2534000 → "2.5M")', () => {
    render(<TrendCard trend={mockTrend} />);

    // YouTube views should be formatted
    expect(screen.getByText('2.5M')).toBeInTheDocument();
  });

  it('displays google trends interest without formatting', () => {
    render(<TrendCard trend={mockTrend} />);

    // Google Trends should be displayed as-is
    expect(screen.getByText('87')).toBeInTheDocument();
  });

  it('truncates title at 100 characters', () => {
    const longTrend: Trend = {
      ...mockTrend,
      title: 'A'.repeat(120) // 120 character title
    };

    render(<TrendCard trend={longTrend} />);

    const titleElement = screen.getByText(/A+\.\.\./);
    expect(titleElement.textContent).toHaveLength(100); // 97 chars + "..."
    expect(titleElement.textContent?.endsWith('...')).toBe(true);
  });

  it('does not truncate titles under 100 characters', () => {
    const shortTrend: Trend = {
      ...mockTrend,
      title: 'Short Title'
    };

    render(<TrendCard trend={shortTrend} />);

    const titleElement = screen.getByText('Short Title');
    expect(titleElement.textContent).toBe('Short Title');
  });

  it('links to correct trend detail page', () => {
    const { container } = render(<TrendCard trend={mockTrend} />);

    const link = container.querySelector('a');
    expect(link).toHaveAttribute('href', '/trend/test-id-123');
  });

  it('displays "N/A" for missing reddit_score', () => {
    const trendWithNullReddit: Trend = {
      ...mockTrend,
      reddit_score: null
    };

    render(<TrendCard trend={trendWithNullReddit} />);

    // Should display N/A for null reddit score
    const redditText = screen.getByText(/Reddit:/i).parentElement;
    expect(redditText?.textContent).toContain('N/A');
  });

  it('displays "N/A" for missing youtube_views', () => {
    const trendWithNullYouTube: Trend = {
      ...mockTrend,
      youtube_views: null
    };

    render(<TrendCard trend={trendWithNullYouTube} />);

    // Should display N/A for null youtube views
    const youtubeText = screen.getByText(/YouTube:/i).parentElement;
    expect(youtubeText?.textContent).toContain('N/A');
  });

  it('displays "N/A" for missing google_trends_interest', () => {
    const trendWithNullGoogle: Trend = {
      ...mockTrend,
      google_trends_interest: null
    };

    render(<TrendCard trend={trendWithNullGoogle} />);

    // Should display N/A for null google trends
    const googleText = screen.getByText(/Google Trends:/i).parentElement;
    expect(googleText?.textContent).toContain('N/A');
  });

  it('displays "N/A" for missing similarweb_traffic', () => {
    const trendWithNullSimilarweb: Trend = {
      ...mockTrend,
      similarweb_traffic: null
    };

    render(<TrendCard trend={trendWithNullSimilarweb} />);

    // Should display N/A for null similarweb traffic
    const similarwebText = screen.getByText(/SimilarWeb:/i).parentElement;
    expect(similarwebText?.textContent).toContain('N/A');
  });

  it('applies hover styling classes', () => {
    const { container } = render(<TrendCard trend={mockTrend} />);

    const cardDiv = container.querySelector('.cursor-pointer');
    expect(cardDiv).toHaveClass('hover:shadow-lg');
    expect(cardDiv).toHaveClass('transition-shadow');
  });
});
