// TypeScript interfaces for Trend Monitor API

// Trend interface (matches backend TrendListResponse from Story 3.3)
export interface Trend {
  id: string;
  title: string;
  confidence_level: 'high' | 'medium' | 'low';
  momentum_score: number;
  reddit_score: number | null;
  youtube_views: number | null;
  google_trends_interest: number | null;
  similarweb_traffic: number | null;
  created_at: string;  // ISO 8601 datetime
}

// Collection summary for "Last Updated" timestamp display
export interface CollectionSummary {
  id: string;
  started_at: string;
  completed_at: string | null;
  status: 'pending' | 'running' | 'completed' | 'failed';
  trends_found: number;
}
