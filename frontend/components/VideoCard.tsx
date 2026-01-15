'use client';

import { YouTubeVideo } from '@/lib/types';
import { formatNumber } from '@/lib/formatters';
import Image from 'next/image';

/**
 * Video Card Component
 * Displays a single YouTube video with:
 * - Video thumbnail (clickable to YouTube)
 * - Video title (truncated to 80 chars)
 * - Channel name
 * - Topic badge
 * - View count, likes, engagement rate
 * - Published date (relative time)
 */

interface VideoCardProps {
  video: YouTubeVideo;
}

export function VideoCard({ video }: VideoCardProps) {
  // Truncate title to 80 chars with ellipsis
  const truncatedTitle = video.video_title.length > 80
    ? video.video_title.substring(0, 77) + '...'
    : video.video_title;

  // Format published date as relative time
  const publishedDate = new Date(video.published_at);
  const now = new Date();
  const diffInDays = Math.floor((now.getTime() - publishedDate.getTime()) / (1000 * 60 * 60 * 24));
  const relativeTime = diffInDays === 0
    ? 'Today'
    : diffInDays === 1
    ? 'Yesterday'
    : `${diffInDays} days ago`;

  // Format engagement rate as percentage
  const engagementPercent = (video.engagement_rate * 100).toFixed(1);

  // YouTube watch URL
  const youtubeUrl = `https://www.youtube.com/watch?v=${video.video_id}`;

  return (
    <div className="block bg-white border border-gray-200 rounded-lg shadow hover:shadow-lg transition-all overflow-hidden">
      {/* Thumbnail - clickable to YouTube */}
      <a
        href={youtubeUrl}
        target="_blank"
        rel="noopener noreferrer"
        className="block relative aspect-video bg-gray-100"
      >
        <Image
          src={video.thumbnail_url}
          alt={video.video_title}
          fill
          className="object-cover"
          sizes="(max-width: 768px) 100vw, (max-width: 1200px) 50vw, 33vw"
        />
        {/* Play button overlay */}
        <div className="absolute inset-0 flex items-center justify-center bg-black bg-opacity-0 hover:bg-opacity-20 transition-all">
          <svg
            className="w-16 h-16 text-white opacity-80"
            fill="currentColor"
            viewBox="0 0 24 24"
          >
            <path d="M8 5v14l11-7z" />
          </svg>
        </div>
      </a>

      {/* Video info */}
      <div className="p-4">
        {/* Topic badge */}
        <span className="inline-block px-2 py-1 text-xs font-medium text-blue-700 bg-blue-100 rounded-full mb-2">
          {video.topic}
        </span>

        {/* Title - clickable to YouTube */}
        <a
          href={youtubeUrl}
          target="_blank"
          rel="noopener noreferrer"
          className="block group"
        >
          <h3 className="text-base font-semibold text-gray-900 mb-2 group-hover:text-blue-600 transition-colors">
            {truncatedTitle}
          </h3>
        </a>

        {/* Channel */}
        <p className="text-sm text-gray-600 mb-3">
          {video.channel}
        </p>

        {/* Metrics */}
        <div className="flex flex-wrap gap-3 text-xs text-gray-600">
          <span title="View count">
            👁️ {formatNumber(video.views)}
          </span>
          <span title="Like count">
            👍 {formatNumber(video.likes)}
          </span>
          <span title="Engagement rate (likes/views)">
            📊 {engagementPercent}%
          </span>
        </div>

        {/* Published date */}
        <p className="text-xs text-gray-500 mt-2">
          Published {relativeTime}
        </p>
      </div>
    </div>
  );
}
