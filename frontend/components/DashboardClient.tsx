'use client';

import { useState } from 'react';
import { Trend, YouTubeVideo } from '@/lib/types';
import { DataSourceCard } from './DataSourceCard';
import { TrendList } from './TrendList';
import { VideoList } from './VideoList';

interface DashboardClientProps {
  token: string;
  initialTrends: Trend[];
  initialVideos: YouTubeVideo[];
}

type DataSource = 'youtube' | 'reddit' | 'google' | 'similarweb';

interface SourceConfig {
  id: DataSource;
  name: string;
  logo: string;
  color: string;
  count: number;
}

export function DashboardClient({ token, initialTrends, initialVideos }: DashboardClientProps) {
  const [activeSource, setActiveSource] = useState<DataSource>('youtube');

  // Calculate counts per source based on populated fields
  // A trend belongs to a source if that source's primary metric is non-null
  const youtubeTrends = initialTrends.filter(t => t.youtube_views !== null && t.youtube_views > 0);
  const redditTrends = initialTrends.filter(t => t.reddit_score !== null && t.reddit_score > 0);
  const googleTrends = initialTrends.filter(t => t.google_trends_interest !== null && t.google_trends_interest > 0);
  const similarwebTrends = initialTrends.filter(t => t.similarweb_traffic !== null && t.similarweb_traffic > 0);

  const dataSources: SourceConfig[] = [
    {
      id: 'youtube',
      name: 'YouTube',
      logo: '/logos/youtube.svg',
      color: '#FF0000',
      count: initialVideos.length
    },
    {
      id: 'reddit',
      name: 'Reddit',
      logo: '/logos/reddit.svg',
      color: '#FF4500',
      count: redditTrends.length
    },
    {
      id: 'google',
      name: 'Google Trends',
      logo: '/logos/google.svg',
      color: '#4285F4',
      count: googleTrends.length
    },
    {
      id: 'similarweb',
      name: 'SimilarWeb',
      logo: '/logos/similarweb.svg',
      color: '#2563EB',
      count: similarwebTrends.length
    }
  ];

  // Get data for active source
  const getActiveData = () => {
    switch (activeSource) {
      case 'youtube':
        return { type: 'videos' as const, data: initialVideos };
      case 'reddit':
        return { type: 'trends' as const, data: redditTrends };
      case 'google':
        return { type: 'trends' as const, data: googleTrends };
      case 'similarweb':
        return { type: 'trends' as const, data: similarwebTrends };
    }
  };

  const activeData = getActiveData();

  return (
    <div className="space-y-8">
      {/* Hero Cards Section */}
      <div>
        <h2 className="text-2xl font-bold text-gray-900 mb-6" style={{ fontFamily: 'Arial, sans-serif' }}>
          Select Your Data Source
        </h2>

        <div className="grid grid-cols-2 md:grid-cols-4 gap-4">
          {dataSources.map((source) => (
            <DataSourceCard
              key={source.id}
              source={source}
              isActive={activeSource === source.id}
              onClick={() => setActiveSource(source.id)}
            />
          ))}
        </div>
      </div>

      {/* Data Display Section */}
      <div className="bg-white rounded-lg shadow-sm border border-gray-200 p-6">
        <div className="flex items-center justify-between mb-6">
          <h3 className="text-xl font-bold text-gray-900" style={{ fontFamily: 'Arial, sans-serif' }}>
            {dataSources.find(s => s.id === activeSource)?.name} Data
          </h3>
          <span className="text-sm text-gray-600">
            {activeData.data.length} items
          </span>
        </div>

        {activeData.data.length === 0 ? (
          <div className="text-center py-12">
            <p className="text-gray-600">
              No data available yet. Click "Collect Latest Trends" to gather fresh data.
            </p>
          </div>
        ) : activeData.type === 'videos' ? (
          <VideoList videos={activeData.data as YouTubeVideo[]} />
        ) : (
          <TrendList trends={activeData.data as Trend[]} token={token} />
        )}
      </div>
    </div>
  );
}
