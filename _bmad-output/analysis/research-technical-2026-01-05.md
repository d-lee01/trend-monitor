# Technical Research: Trend Monitoring APIs

**Date:** 2026-01-05
**Research Type:** Technical Validation
**Purpose:** Validate API capabilities, rate limits, and costs for quantified trend monitoring system

---

## Executive Summary

All planned APIs are viable for the trend monitoring system. Key findings:
- **Reddit API:** ✅ Provides all needed metrics, 60 req/min free
- **YouTube Data API:** ✅ Rich metrics, 10K units/day free (sufficient)
- **NewsAPI:** ⚠️ Limited metadata, requires paid plan for production
- **Google Trends:** ✅ Free via PyTrends, rate limits manageable
- **SimilarWeb:** ✅ Already subscribed

**Estimated Monthly Cost:** $0-$449 (depends on NewsAPI tier choice)

---

## API Validation Details

### 1. Reddit API

**Status:** ✅ Fully Viable

**Available Metrics:**
- Post score (upvotes - downvotes)
- Comment count (num_comments)
- Upvote ratio
- Post age (for velocity calculation)
- Subreddit subscriber count
- Crosspost count (amplification indicator)

**Rate Limits:**
- **Authenticated (OAuth):** 60 requests/minute (rolling average)
- **Unauthenticated:** 10 requests/minute
- Pagination: 100 items per request, 1000 max total

**Response Headers:**
- `X-Ratelimit-Used`: Requests used in current period
- `X-Ratelimit-Remaining`: Requests remaining
- `X-Ratelimit-Reset`: When rate limit resets

**Cost:** FREE

**Authentication:** OAuth 2.0 required

**Recommendation:** Use authenticated requests for 60 req/min. Sufficient for twice-weekly data collection across multiple subreddits.

---

### 2. YouTube Data API v3

**Status:** ✅ Fully Viable

**Available Metrics:**
- View count
- Like/dislike count
- Comment count
- Channel subscriber count (authority signal)
- Publication date (for velocity calculation)
- Video category, tags, description

**Quota System:**
- **Default:** 10,000 units/day (FREE)
- Read operations: 1 unit per request
- Search requests: 100 units per search
- Write operations: 50 units
- Video upload: 1,600 units

**Quota Optimization:**
- Request only necessary fields (reduces response size)
- Implement caching (can reduce usage 50-80%)
- Use GZIP compression
- Most developers stay within free tier with optimization

**Cost:** FREE (default quota sufficient for twice-weekly trend monitoring)

**Quota Extension:** Available via audit form if needed (unlikely for this use case)

**Recommendation:** 10K units/day = 100 searches/day or 10K video metadata reads/day. More than enough for trend monitoring.

---

### 3. NewsAPI

**Status:** ⚠️ Viable with Limitations

**Endpoints:**
- `/v2/everything`: Search 150K+ sources, 5 years historical
- `/v2/top-headlines`: Breaking news by country/category
- `/v2/top-headlines/sources`: Publisher information

**Article Metadata:**
- Source ID and name
- Title and description (snippet)
- URL and image URL
- Publication date (UTC)
- Content (truncated to 200 characters)

**Limitations:**
- No engagement metrics (views, shares, comments)
- Truncated content (200 chars)
- Developer plan: testing only, NOT for production

**Pricing:**
- **Developer:** FREE (testing only)
- **Business:** ~$449/month (production use)
- Each HTTP request = 1 request counted

**Recommendation:**
- Start with FREE Developer plan for MVP testing
- Upgrade to Business ($449/mo) for production
- **Alternative:** Consider NewsData.io or NewsCatcher API for better pricing

---

### 4. Google Trends

**Status:** ✅ Viable (Unofficial API)

**Method:** PyTrends (unofficial Python library)

**Available Data:**
- Interest Over Time (historical indexed data, 0-100 scale)
- Multirange Interest Over Time (multiple date ranges)
- Historical Hourly Interest (hourly granularity)
- Trending Searches (by country)
- Realtime Trending Searches
- Related Queries

**Rate Limiting:**
- No official limits, but throttling occurs
- Recommendation: 60 seconds between requests when rate-limited
- Manageable for twice-weekly collection

**Installation:**
```bash
pip install pytrends
```

**Limitations:**
- Unofficial API (could break if Google changes)
- Cannot access dynamically rendered content
- Notoriously unreliable at times

**Official Google Trends API (Alpha):**
- Now accepting alpha testers
- Allows comparing dozens of terms (vs 5 in UI)
- More reliable than PyTrends
- **Recommendation:** Apply for alpha access as backup

**Cost:** FREE

**Recommendation:** Use PyTrends for MVP. Apply for official API alpha as long-term solution.

---

### 5. SimilarWeb API

**Status:** ✅ Confirmed (Already Subscribed)

**Available Metrics:**
- Website traffic (absolute visitor numbers)
- Traffic sources breakdown
- Engagement metrics (bounce rate, pages/visit, avg visit duration)
- Geographic distribution
- Referral sources
- Top pages

**Cost:** Already subscribed (no additional cost)

**Recommendation:** Leverage existing subscription for mainstream traffic confirmation signal.

---

## Cross-Platform Data Integration

### Normalization Challenge

Each API returns data in different formats and scales:
- Reddit: Absolute scores (upvotes)
- YouTube: Absolute views
- Google Trends: Relative interest (0-100)
- SimilarWeb: Absolute traffic

**Solution:** Build normalization layer to create comparable scores across platforms.

### Composite Metric Calculation

**Cross-Platform Momentum Score:**
```
Score = (Reddit_Velocity × YouTube_Traction × Google_Trends_Spike) + SimilarWeb_Bonus
```

Where:
- **Reddit_Velocity** = (score / hours_since_post) × log(subreddit_size)
- **YouTube_Traction** = (views / hours_since_publish) × (engagement_rate) × log(channel_subs)
- **Google_Trends_Spike** = (current_interest - 7day_avg) / 7day_stddev
- **SimilarWeb_Bonus** = if traffic spike detected, multiply by 1.5

---

## Rate Limit Analysis for Twice-Weekly Collection

**Assumptions:**
- Collect data twice per week (2x/week)
- Monitor ~50 trending topics per collection
- 10 subreddits, 20 YouTube channels, 50 news queries

**Reddit:**
- 50 topics × 10 subreddits = 500 requests
- At 60 req/min = ~8.3 minutes
- ✅ Well within limits

**YouTube:**
- 50 topics × 20 channels = 1,000 searches = 100,000 quota units
- Exceeds daily quota (10K units)
- **Solution:** Cache aggressively, search only trending channels (reduce to ~10), use video list endpoint (1 unit) instead of search (100 units)
- Optimized: 50 video list calls = 50 units ✅

**NewsAPI:**
- 50 topics = 50 requests
- ✅ Well within any tier limits

**Google Trends:**
- 50 topics = 50 requests (with 60s delays = 50 minutes)
- ✅ Manageable for twice-weekly

**Total Collection Time:** ~1-2 hours per twice-weekly run (mostly Google Trends delays)

---

## Cost Summary

| API | Cost | Notes |
|-----|------|-------|
| Reddit | FREE | OAuth authentication required |
| YouTube | FREE | Stay within 10K daily quota with optimization |
| NewsAPI | $0-449/mo | FREE for testing, $449/mo for production |
| Google Trends | FREE | Unofficial API via PyTrends |
| SimilarWeb | $0 | Already subscribed |
| **Total** | **$0-449/mo** | Depends on NewsAPI tier |

**Recommendation for MVP:** Start with $0/month (use NewsAPI Developer for testing), upgrade to $449/mo when moving to production.

---

## Risk Assessment

### High Risk
- **Google Trends (PyTrends):** Unofficial API could break
  - **Mitigation:** Apply for official API alpha, build fallback scraping

### Medium Risk
- **YouTube Quota:** Could exceed if not optimized
  - **Mitigation:** Aggressive caching, use video list instead of search

### Low Risk
- **Reddit, NewsAPI, SimilarWeb:** Stable, well-documented APIs

---

## Alternative APIs Considered

### NewsAPI Alternatives:
1. **NewsData.io** - Better pricing, more metadata
2. **NewsCatcher API** - 60 hits/min, better rate limits
3. **AYLIEN News API** - Full-text content, higher cost

**Recommendation:** Evaluate NewsData.io if NewsAPI Business tier ($449/mo) is too expensive.

---

## Technical Recommendations

1. **Start with Free Tier:** All APIs except NewsAPI production
2. **Build Caching Layer:** Reduce API calls by 50-80%
3. **Implement Retry Logic:** Handle rate limits gracefully
4. **Monitor Quota Usage:** Track daily quota consumption
5. **Apply for Google Trends API Alpha:** Long-term reliability

---

## Sources

- [Reddit API Rate Limits Guide](https://painonsocial.com/blog/reddit-api-rate-limits-guide)
- [Reddit API Limitations Complete Guide](https://painonsocial.com/blog/reddit-api-limitations)
- [YouTube Data API Quota Calculator](https://developers.google.com/youtube/v3/determine_quota_cost)
- [YouTube API Limits and Costs](https://www.getphyllo.com/post/youtube-api-limits-how-to-calculate-api-usage-cost-and-fix-exceeded-api-quota)
- [NewsAPI Pricing](https://newsapi.org/pricing)
- [NewsAPI Documentation](https://newsapi.org/docs/endpoints)
- [PyTrends GitHub](https://github.com/GeneralMills/pytrends)
- [Google Trends API Guide](https://lazarinastoy.com/the-ultimate-guide-to-pytrends-google-trends-api-with-python/)
