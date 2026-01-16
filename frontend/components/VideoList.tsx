'use client';

import { YouTubeVideo } from '@/lib/types';
import { formatNumber } from '@/lib/formatters';
import Image from 'next/image';

interface VideoListProps {
  videos: YouTubeVideo[];
}

interface VideoSectionProps {
  title: string;
  videos: YouTubeVideo[];
  emptyMessage: string;
}

function VideoSection({ title, videos, emptyMessage }: VideoSectionProps) {
  if (videos.length === 0) {
    return (
      <div className="mb-12">
        <h3 className="text-xl font-bold text-gray-900 mb-4 pb-2 border-b-2" style={{ borderColor: '#542E91', fontFamily: 'Arial, sans-serif' }}>
          {title}
        </h3>
        <p className="text-gray-500 text-center py-8">{emptyMessage}</p>
      </div>
    );
  }

  return (
    <div className="mb-12">
      <h3 className="text-xl font-bold text-gray-900 mb-4 pb-2 border-b-2" style={{ borderColor: '#542E91', fontFamily: 'Arial, sans-serif' }}>
        {title} <span className="text-sm font-normal text-gray-600">({videos.length} videos)</span>
      </h3>

      <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4">
        {videos.map((video) => {
          const youtubeUrl = `https://www.youtube.com/watch?v=${video.video_id}`;
          const publishedDate = new Date(video.published_at);
          const daysAgo = Math.floor((Date.now() - publishedDate.getTime()) / (1000 * 60 * 60 * 24));
          const relativeTime = daysAgo === 0 ? 'Today' : daysAgo === 1 ? 'Yesterday' : `${daysAgo} days ago`;
          const engagementPercent = (video.engagement_rate * 100).toFixed(1);

          return (
            <a
              key={video.id}
              href={youtubeUrl}
              target="_blank"
              rel="noopener noreferrer"
              className="block bg-white border border-gray-200 rounded-lg overflow-hidden hover:border-[#542E91] hover:shadow-lg transition-all"
              style={{ fontFamily: 'Arial, sans-serif' }}
            >
              {/* Thumbnail */}
              <div className="relative aspect-video bg-gray-100">
                <Image
                  src={video.thumbnail_url}
                  alt={video.video_title}
                  fill
                  className="object-cover"
                  sizes="(max-width: 768px) 100vw, (max-width: 1200px) 50vw, 33vw"
                />
                {/* Play button overlay */}
                <div className="absolute inset-0 flex items-center justify-center bg-black bg-opacity-0 hover:bg-opacity-20 transition-all group">
                  <div className="w-12 h-12 bg-red-600 rounded-full flex items-center justify-center opacity-80 group-hover:opacity-100 transition-opacity">
                    <svg className="w-6 h-6 text-white ml-1" fill="currentColor" viewBox="0 0 24 24">
                      <path d="M8 5v14l11-7z" />
                    </svg>
                  </div>
                </div>
              </div>

              {/* Video info */}
              <div className="p-4">
                {/* Topic badge */}
                <span className="inline-block px-2 py-1 text-xs font-bold text-white rounded-full mb-2" style={{ backgroundColor: '#542E91' }}>
                  {video.topic}
                </span>

                {/* Title */}
                <h4 className="font-bold text-gray-900 text-sm mb-2 line-clamp-2">
                  {video.video_title}
                </h4>

                {/* Channel */}
                <p className="text-sm text-gray-600 mb-3">{video.channel}</p>

                {/* Metrics */}
                <div className="flex flex-wrap gap-3 text-xs text-gray-600 mb-2">
                  <span title="View count" className="flex items-center gap-1 font-bold">
                    👁️ {formatNumber(video.views)}
                  </span>
                  <span title="Like count" className="flex items-center gap-1">
                    👍 {formatNumber(video.likes)}
                  </span>
                  <span title="Engagement rate" className="flex items-center gap-1 font-bold" style={{ color: '#542E91' }}>
                    📊 {engagementPercent}%
                  </span>
                </div>

                {/* Published date */}
                <p className="text-xs text-gray-500">
                  Published {relativeTime}
                </p>
              </div>
            </a>
          );
        })}
      </div>
    </div>
  );
}

export function VideoList({ videos }: VideoListProps) {
  // Sort all videos by views (descending)
  const sortedByViews = [...videos].sort((a, b) => b.views - a.views);

  // Separate into categories
  const travelVideos = sortedByViews.filter(v => v.category === 'travel');
  const newsVideos = sortedByViews.filter(v => v.category === 'news');

  return (
    <div className="space-y-8">
      {/* All Videos Section */}
      <VideoSection
        title="🔥 All Videos (Highest Views in Last 7 Days)"
        videos={sortedByViews}
        emptyMessage="No videos available yet. Click 'Collect Latest Trends' to discover trending videos."
      />

      {/* Travel Videos Section */}
      <VideoSection
        title="✈️ Travel Videos (Highest Views in Last 7 Days)"
        videos={travelVideos}
        emptyMessage="No travel videos found in the last 7 days."
      />

      {/* News Videos Section */}
      <VideoSection
        title="📰 News Videos (Highest Views in Last 7 Days)"
        videos={newsVideos}
        emptyMessage="No news videos found in the last 7 days."
      />
    </div>
  );
}
