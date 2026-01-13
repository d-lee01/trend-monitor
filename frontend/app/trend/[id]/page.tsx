import { cookies } from 'next/headers';
import { redirect, notFound } from 'next/navigation';
import Link from 'next/link';
import { api, APIError } from '@/lib/api';
import { ConfidenceBadge } from '@/components/ConfidenceBadge';
import { PlatformCard } from '@/components/PlatformCard';
import { ScoreBreakdown } from '@/components/ScoreBreakdown';

/**
 * Trend Detail Page - Server Component with SSR
 * Displays comprehensive trend analysis with platform breakdown
 * Must load in <2 seconds per performance requirements (AC-6)
 *
 * TODO: Add performance monitoring to verify <2s load time requirement
 * - Consider using Next.js Analytics or custom performance tracking
 * - Monitor server-side render time and API response time
 * - Set up alerts if page load exceeds threshold
 */

interface PageProps {
  params: {
    id: string;
  };
}

async function getTrendDetail(id: string) {
  const cookieStore = cookies();
  const token = cookieStore.get('auth_token')?.value;

  if (!token) {
    redirect('/?message=Please log in');
  }

  try {
    const trend = await api.getTrendById(token, id);
    return trend;
  } catch (error) {
    // Only log errors in development to avoid exposing sensitive info in production
    if (process.env.NODE_ENV === 'development') {
      console.error('Failed to fetch trend detail:', error);
    }

    // Handle 401: Session expired - redirect to login
    if (error instanceof APIError && error.status === 401) {
      redirect('/?message=Session expired. Please log in again.');
    }

    // Handle 404: Trend not found
    if (error instanceof APIError && error.status === 404) {
      notFound(); // This will trigger Next.js 404 page
    }

    // For other errors, redirect to dashboard with error message
    redirect('/dashboard?message=Failed to load trend details');
  }
}

// Generate metadata for SEO
export async function generateMetadata({ params }: PageProps) {
  try {
    const trend = await getTrendDetail(params.id);
    return {
      title: `${trend.title} - Trend Detail | trend-monitor`,
      description: `Detailed analysis of trending topic: ${trend.title}`,
    };
  } catch (error) {
    // Re-throw Next.js redirect/notFound errors to allow proper navigation
    if (error instanceof Error && (error.message.includes('NEXT_REDIRECT') || error.message.includes('NEXT_NOT_FOUND'))) {
      throw error;
    }
    // For other errors, return default metadata
    return {
      title: 'Trend Detail | trend-monitor',
      description: 'View detailed trend analysis',
    };
  }
}

export default async function TrendDetailPage({ params }: PageProps) {
  const trend = await getTrendDetail(params.id);

  return (
    <div className="min-h-screen bg-gray-50">
      {/* Header */}
      <header className="bg-white shadow">
        <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-4">
          <Link
            href="/dashboard"
            className="inline-flex items-center text-blue-600 hover:text-blue-800 transition-colors font-medium"
          >
            <svg className="w-5 h-5 mr-2" fill="none" stroke="currentColor" viewBox="0 0 24 24">
              <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M15 19l-7-7 7-7" />
            </svg>
            Back to Dashboard
          </Link>
        </div>
      </header>

      {/* Main Content */}
      <main className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-8">
        {/* Trend Title and Confidence Badge */}
        <div className="flex items-center gap-4 mb-8">
          <h1 className="text-3xl font-bold text-gray-900">{trend.title}</h1>
          <ConfidenceBadge confidenceLevel={trend.confidence_level} size="large" />
        </div>

        {/* Platform Breakdown Section */}
        <section className="mb-8">
          <h2 className="text-2xl font-bold text-gray-900 mb-4">Platform Breakdown</h2>
          <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
            {/* Reddit Card */}
            <PlatformCard
              platform="reddit"
              data={{
                score: trend.reddit_score,
                velocity_score: trend.reddit_velocity_score,
                subreddit: trend.reddit_subreddit,
                upvote_ratio: trend.reddit_upvote_ratio,
              }}
              normalizedScore={trend.reddit_velocity_score ?? 0}
              externalUrl={trend.reddit_url ?? undefined}
            />

            {/* YouTube Card */}
            <PlatformCard
              platform="youtube"
              data={{
                views: trend.youtube_views,
                traction_score: trend.youtube_traction_score,
                channel: trend.youtube_channel,
                likes: trend.youtube_likes,
              }}
              normalizedScore={trend.youtube_traction_score ?? 0}
              externalUrl={trend.youtube_url ?? undefined}
            />

            {/* Google Trends Card */}
            <PlatformCard
              platform="googletrends"
              data={{
                interest: trend.google_trends_interest,
                spike_score: trend.google_trends_spike_score,
                related_queries: trend.google_trends_related_queries,
              }}
              normalizedScore={trend.google_trends_spike_score ?? 0}
              externalUrl={undefined}
            />

            {/* SimilarWeb Card */}
            <PlatformCard
              platform="similarweb"
              data={{
                traffic: trend.similarweb_traffic,
                traffic_change: trend.similarweb_traffic_change,
                spike_detected: trend.similarweb_spike_detected,
              }}
              normalizedScore={trend.similarweb_traffic_change ? Math.min(100, trend.similarweb_traffic_change) : 0}
              externalUrl={undefined}
            />
          </div>
        </section>

        {/* Momentum Score Calculation Section */}
        <section>
          <ScoreBreakdown
            redditVelocity={trend.reddit_velocity_score}
            youtubeTraction={trend.youtube_traction_score}
            googleTrendsSpike={trend.google_trends_spike_score}
            similarwebBonus={trend.similarweb_spike_detected ?? false}
            finalScore={trend.momentum_score}
          />
        </section>
      </main>
    </div>
  );
}
