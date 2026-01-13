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

// Collection response from POST /collect
export interface CollectionResponse {
  collection_id: string;
  status: string;
  started_at: string;
  message: string;
}

// Collection status response from GET /collections/{collection_id}
export interface CollectionStatusResponse {
  collection_id: string;
  status: 'in_progress' | 'completed' | 'failed';
  started_at: string;
  completed_at: string | null;
  trends_found: number;
  duration_minutes: number;
  errors: any[];
}

// Trend Detail interface (for GET /trends/{id} - includes all platform fields)
export interface TrendDetail {
  // Basic fields
  id: string;
  title: string;
  confidence_level: 'high' | 'medium' | 'low';
  momentum_score: number;
  created_at: string;  // ISO 8601 datetime

  // Reddit fields
  reddit_score: number | null;
  reddit_velocity_score: number | null;
  reddit_subreddit: string | null;
  reddit_url: string | null;
  reddit_upvote_ratio: number | null;

  // YouTube fields
  youtube_views: number | null;
  youtube_traction_score: number | null;
  youtube_channel: string | null;
  youtube_likes: number | null;
  youtube_channel_subscribers: number | null;
  youtube_url: string | null;

  // Google Trends fields
  google_trends_interest: number | null;
  google_trends_spike_score: number | null;
  google_trends_related_queries: string[] | null;

  // SimilarWeb fields
  similarweb_traffic: number | null;
  similarweb_traffic_change: number | null;
  similarweb_spike_detected: boolean | null;
}

// Brief Response interface (from POST /trends/{id}/explain - Story 4.2)
export interface BriefResponse {
  ai_brief: string;  // AI-generated 3-sentence explanation
  generated_at: string;  // ISO 8601 timestamp
  cached: boolean;  // True if cached, False if freshly generated
}
