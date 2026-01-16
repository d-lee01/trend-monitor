import { cookies } from 'next/headers';
import { redirect } from 'next/navigation';
import { DashboardClient } from '@/components/DashboardClient';
import { CollectionButton } from '@/components/CollectionButton';
import { api } from '@/lib/api';
import { timeAgo } from '@/lib/formatters';

/**
 * Dashboard Page - Hero Card Tab Interface
 * Holiday Extras branded dashboard with data source selection
 */

// Cache dashboard data for 5 minutes (300 seconds)
export const revalidate = 300;

async function getDashboardData() {
  const cookieStore = cookies();
  const token = cookieStore.get('auth_token')?.value;

  if (!token) {
    redirect('/?message=Please log in');
  }

  try {
    const [trends, videos, collection] = await Promise.all([
      api.getTrends(token),
      api.getYouTubeVideos(token, 50),
      api.getLatestCollection(token)
    ]);

    return {
      trends,
      videos,
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
      videos: [],
      lastUpdated: null
    };
  }
}

export default async function DashboardPage() {
  const { trends, videos, lastUpdated } = await getDashboardData();

  // Get auth token for client components
  const cookieStore = cookies();
  const token = cookieStore.get('auth_token')?.value || '';

  return (
    <div className="min-h-screen bg-gray-50" style={{ fontFamily: 'Arial, sans-serif' }}>
      {/* Header - Holiday Extras branded */}
      <header className="bg-white shadow">
        <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-6">
          <div className="flex flex-col sm:flex-row sm:items-center sm:justify-between gap-4">
            {/* Branding */}
            <div>
              <h1 className="text-3xl font-bold" style={{ color: '#542E91' }}>
                Trend Monitor
              </h1>
              <p className="text-sm text-gray-600 italic mt-1">
                Less hassle. More holiday.
              </p>
            </div>

            {/* Actions */}
            <div className="flex items-center gap-4">
              {lastUpdated && (
                <span className="text-sm text-gray-600">
                  Updated: {timeAgo(lastUpdated)}
                </span>
              )}
              <CollectionButton token={token} />
            </div>
          </div>
        </div>
      </header>

      {/* Main Content */}
      <main className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-8">
        <DashboardClient
          token={token}
          initialTrends={trends}
          initialVideos={videos}
        />
      </main>
    </div>
  );
}
