import { cookies } from 'next/headers';
import { redirect } from 'next/navigation';
import { TrendCard } from '@/components/TrendCard';
import { CollectionButton } from '@/components/CollectionButton';
import { api } from '@/lib/api';
import { timeAgo } from '@/lib/formatters';
import { Trend } from '@/lib/types';

/**
 * Dashboard Page - Server Component with SSR
 * Fetches trends data on server for <2 second load time
 * Displays Top 10 trends ranked by momentum score
 */

// Cache dashboard data for 5 minutes (300 seconds)
// Reduces backend load and improves performance
export const revalidate = 300;

async function getDashboardData() {
  const cookieStore = cookies();
  const token = cookieStore.get('auth_token')?.value;

  if (!token) {
    redirect('/?message=Please log in');
  }

  try {
    const [trends, collection] = await Promise.all([
      api.getTrends(token),
      api.getLatestCollection(token)
    ]);

    return {
      trends,
      lastUpdated: collection?.completed_at || null
    };
  } catch (error) {
    console.error('Failed to fetch dashboard data:', error);

    // Handle auth failures by redirecting to login
    if (error instanceof Error && 'status' in error && (error as any).status === 401) {
      redirect('/?message=Session expired. Please log in again.');
    }

    // For other errors, return empty state
    return {
      trends: [],
      lastUpdated: null
    };
  }
}

export default async function DashboardPage() {
  const { trends, lastUpdated } = await getDashboardData();

  // Get auth token for CollectionButton
  const cookieStore = cookies();
  const token = cookieStore.get('auth_token')?.value || '';

  return (
    <div className="min-h-screen bg-gray-50">
      {/* Header */}
      <header className="bg-white shadow">
        <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-4 flex justify-between items-center">
          <h1 className="text-2xl font-bold text-gray-900">trend-monitor</h1>

          <div className="flex items-center gap-4">
            {lastUpdated && (
              <span className="text-sm text-gray-600">
                Last Updated: {timeAgo(lastUpdated)}
              </span>
            )}
            <CollectionButton token={token} />
          </div>
        </div>
      </header>

      {/* Main Content */}
      <main className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-8">
        <h2 className="text-3xl font-bold text-gray-900 mb-6">
          Trending Now - Top 10
        </h2>

        {trends.length === 0 ? (
          <div className="text-center py-12">
            <p className="text-gray-600 text-lg">
              No trends available yet. Click "Collect Latest Trends" to start data collection.
            </p>
          </div>
        ) : (
          <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
            {trends.map((trend) => (
              <TrendCard key={trend.id} trend={trend} token={token} />
            ))}
          </div>
        )}
      </main>
    </div>
  );
}
