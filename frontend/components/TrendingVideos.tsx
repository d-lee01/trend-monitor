import { api } from '@/lib/api';
import { VideoCard } from './VideoCard';
import { YouTubeVideo } from '@/lib/types';

/**
 * Trending Videos Section - Server Component
 * Fetches and displays YouTube videos from latest collection
 * Shows top 12 videos sorted by engagement rate
 */

interface TrendingVideosProps {
  token: string;
}

async function getYouTubeVideos(token: string): Promise<YouTubeVideo[]> {
  try {
    return await api.getYouTubeVideos(token, 12);
  } catch (error) {
    console.error('Failed to fetch YouTube videos:', error);
    return [];
  }
}

export async function TrendingVideos({ token }: TrendingVideosProps) {
  const videos = await getYouTubeVideos(token);

  return (
    <section className="mt-12">
      <div className="flex items-center justify-between mb-6">
        <h2 className="text-3xl font-bold text-gray-900">
          Trending Videos
        </h2>
        <span className="text-sm text-gray-600">
          {videos.length} videos found
        </span>
      </div>

      {videos.length === 0 ? (
        <div className="text-center py-12 bg-white rounded-lg border border-gray-200">
          <p className="text-gray-600 text-lg">
            No trending videos available yet. Click "Collect Latest Trends" to discover videos.
          </p>
        </div>
      ) : (
        <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-3 xl:grid-cols-4 gap-6">
          {videos.map((video) => (
            <VideoCard key={video.id} video={video} />
          ))}
        </div>
      )}
    </section>
  );
}
