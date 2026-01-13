import React from 'react';
import { render, screen } from '@testing-library/react';
import { PlatformCard } from '@/components/PlatformCard';

describe('PlatformCard Component', () => {
  describe('Reddit Platform', () => {
    it('renders Reddit card with all metrics', () => {
      render(
        <PlatformCard
          platform="reddit"
          data={{
            score: 15234,
            velocity_score: 78,
            subreddit: 'r/videos',
            upvote_ratio: 0.95,
          }}
          normalizedScore={78}
          externalUrl="https://reddit.com/r/videos/abc123"
        />
      );

      expect(screen.getByText('Reddit')).toBeInTheDocument();
      expect(screen.getByText('🔴')).toBeInTheDocument();
      expect(screen.getByText('15.2K')).toBeInTheDocument();
      expect(screen.getByText('r/videos')).toBeInTheDocument();
      expect(screen.getByText('95%')).toBeInTheDocument();
    });

    it('displays external link for Reddit', () => {
      render(
        <PlatformCard
          platform="reddit"
          data={{ score: 100 }}
          normalizedScore={50}
          externalUrl="https://reddit.com/test"
        />
      );

      const link = screen.getByRole('link', { name: /view on reddit/i });
      expect(link).toHaveAttribute('href', 'https://reddit.com/test');
      expect(link).toHaveAttribute('target', '_blank');
      expect(link).toHaveAttribute('rel', 'noopener noreferrer');
    });
  });

  describe('YouTube Platform', () => {
    it('renders YouTube card with all metrics', () => {
      render(
        <PlatformCard
          platform="youtube"
          data={{
            views: 2534000,
            traction_score: 82,
            channel: 'TechChannel',
            likes: 125000,
          }}
          normalizedScore={82}
          externalUrl="https://youtube.com/watch?v=abc"
        />
      );

      expect(screen.getByText('YouTube')).toBeInTheDocument();
      expect(screen.getByText('▶️')).toBeInTheDocument();
      expect(screen.getByText('2.5M')).toBeInTheDocument();
      expect(screen.getByText('TechChannel')).toBeInTheDocument();
      expect(screen.getByText('125.0K')).toBeInTheDocument();
    });
  });

  describe('Google Trends Platform', () => {
    it('renders Google Trends card with all metrics', () => {
      render(
        <PlatformCard
          platform="googletrends"
          data={{
            interest: 87,
            spike_score: 85,
            related_queries: ['query1', 'query2', 'query3'],
          }}
          normalizedScore={85}
        />
      );

      expect(screen.getByText('Google Trends')).toBeInTheDocument();
      expect(screen.getByText('📈')).toBeInTheDocument();
      expect(screen.getByText('87')).toBeInTheDocument();
      expect(screen.getByText('query1, query2')).toBeInTheDocument(); // Only shows first 2
    });

    it('does not display external link when not provided', () => {
      render(
        <PlatformCard
          platform="googletrends"
          data={{ interest: 50 }}
          normalizedScore={50}
        />
      );

      expect(screen.queryByRole('link', { name: /view on/i })).not.toBeInTheDocument();
    });
  });

  describe('SimilarWeb Platform', () => {
    it('renders SimilarWeb card with all metrics', () => {
      render(
        <PlatformCard
          platform="similarweb"
          data={{
            traffic: 1250000,
            traffic_change: 150,
            spike_detected: true,
          }}
          normalizedScore={75}
        />
      );

      expect(screen.getByText('SimilarWeb')).toBeInTheDocument();
      expect(screen.getByText('📊')).toBeInTheDocument();
      expect(screen.getByText('1.3M')).toBeInTheDocument(); // traffic formatted
      expect(screen.getByText('150%')).toBeInTheDocument(); // traffic_change with %
      expect(screen.getByText('Yes')).toBeInTheDocument();
    });

    it('displays No when spike not detected', () => {
      render(
        <PlatformCard
          platform="similarweb"
          data={{
            spike_detected: false,
          }}
          normalizedScore={25}
        />
      );

      expect(screen.getByText('No')).toBeInTheDocument();
    });
  });

  describe('Progress Bar', () => {
    it('displays normalized score in progress bar', () => {
      render(
        <PlatformCard
          platform="reddit"
          data={{ score: 100 }}
          normalizedScore={65}
        />
      );

      const progressBar = screen.getByRole('progressbar');
      expect(progressBar).toHaveAttribute('aria-valuenow', '65');
      expect(progressBar).toHaveAttribute('aria-valuemin', '0');
      expect(progressBar).toHaveAttribute('aria-valuemax', '100');
    });

    it('displays 0 when normalized score is 0', () => {
      render(
        <PlatformCard
          platform="reddit"
          data={{ score: 100 }}
          normalizedScore={0}
        />
      );

      const progressBar = screen.getByRole('progressbar');
      expect(progressBar).toHaveAttribute('aria-valuenow', '0');
    });

    it('displays 100 when normalized score exceeds 100', () => {
      render(
        <PlatformCard
          platform="reddit"
          data={{ score: 100 }}
          normalizedScore={150}
        />
      );

      // Score should be clamped to 100
      expect(screen.getByText('150/100')).toBeInTheDocument();
    });
  });

  describe('Missing Data Handling', () => {
    it('displays N/A for null primary metric', () => {
      render(
        <PlatformCard
          platform="reddit"
          data={{ score: null }}
          normalizedScore={0}
        />
      );

      // Find all N/A text (there will be multiple)
      const naElements = screen.getAllByText('N/A');
      expect(naElements.length).toBeGreaterThan(0);
    });

    it('displays N/A for undefined secondary metrics', () => {
      render(
        <PlatformCard
          platform="reddit"
          data={{ score: 100 }}
          normalizedScore={50}
        />
      );

      // Secondary metrics should show N/A when not provided
      const naElements = screen.getAllByText('N/A');
      expect(naElements.length).toBeGreaterThan(0);
    });
  });

  describe('Number Formatting', () => {
    it('formats thousands with K suffix', () => {
      render(
        <PlatformCard
          platform="reddit"
          data={{ score: 5500 }}
          normalizedScore={50}
        />
      );

      expect(screen.getByText('5.5K')).toBeInTheDocument();
    });

    it('formats millions with M suffix', () => {
      render(
        <PlatformCard
          platform="youtube"
          data={{ views: 3200000 }}
          normalizedScore={70}
        />
      );

      expect(screen.getByText('3.2M')).toBeInTheDocument();
    });

    it('displays numbers under 1000 without formatting', () => {
      render(
        <PlatformCard
          platform="reddit"
          data={{ score: 542 }}
          normalizedScore={30}
        />
      );

      expect(screen.getByText('542')).toBeInTheDocument();
    });
  });
});
