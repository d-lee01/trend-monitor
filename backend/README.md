# trend-monitor Backend

FastAPI backend for the trend-monitor system.

## Tech Stack

- **Framework:** FastAPI 0.104.1
- **Language:** Python 3.10+
- **Database:** PostgreSQL 14+ with asyncpg driver
- **ORM:** SQLAlchemy 2.0 (async)
- **Migrations:** Alembic
- **Authentication:** JWT with 7-day expiration

## Getting Started

### Prerequisites

- Python 3.10+ installed
- PostgreSQL database (Railway managed)
- Reddit API credentials (for data collection)

### Installation

1. Install dependencies:
```bash
pip install -r requirements.txt
```

2. Create `.env` file:
```bash
cp .env.example .env
```

3. Configure environment variables (see Configuration section below)

4. Run database migrations:
```bash
alembic upgrade head
```

5. Start the server:
```bash
uvicorn app.main:app --reload
```

The API will be available at http://localhost:8000

## Configuration

### Required Environment Variables

```env
# Database
DATABASE_URL=postgresql://user:password@host:5432/dbname

# JWT Authentication
JWT_SECRET_KEY=your_secret_key_here

# Reddit API (Required for Story 2.2+)
REDDIT_CLIENT_ID=your_reddit_client_id
REDDIT_CLIENT_SECRET=your_reddit_client_secret

# YouTube Data API v3 (Required for Story 2.3+)
YOUTUBE_API_KEY=your_youtube_api_key_here

# Google Trends (PyTrends) - No API key required (Story 2.4+)
# Uses unofficial web scraping library - no credentials needed

# SimilarWeb API (Required for Story 2.5+)
SIMILARWEB_API_KEY=your_similarweb_api_key_here
```

### Reddit API Setup

The Reddit collector requires OAuth 2.0 credentials:

1. Go to https://www.reddit.com/prefs/apps
2. Click "create app" or "create another app"
3. Fill in the form:
   - **Name:** trend-monitor
   - **App type:** Select "script"
   - **Description:** Trend monitoring system
   - **About URL:** (leave blank)
   - **Redirect URI:** http://localhost:8000
4. Click "create app"
5. Copy the credentials:
   - **Client ID:** The string under the app name (e.g., "abc123xyz")
   - **Client Secret:** The "secret" field
6. Add to your `.env` file:
   ```env
   REDDIT_CLIENT_ID=abc123xyz
   REDDIT_CLIENT_SECRET=your_secret_here
   ```

**For Railway Deployment:**
1. Go to Railway project → Variables
2. Add the environment variables:
   - `REDDIT_CLIENT_ID`
   - `REDDIT_CLIENT_SECRET`
3. Redeploy the service

### YouTube Data API v3 Setup

The YouTube collector uses Google's Data API v3 with an API key:

1. Go to https://console.cloud.google.com/
2. Create a new project or select an existing project
3. Enable "YouTube Data API v3":
   - Click "Enable APIs and Services"
   - Search for "YouTube Data API v3"
   - Click "Enable"
4. Create API key credentials:
   - Go to "Credentials" → "Create Credentials" → "API Key"
   - Copy the generated API key
5. (Optional but recommended) Restrict API key:
   - Click "Edit API key"
   - **Application restrictions:** Set to "HTTP referrers" or "IP addresses" for production
   - **API restrictions:** Select "Restrict key" → "YouTube Data API v3"
6. Add to your `.env` file:
   ```env
   YOUTUBE_API_KEY=AIza...your_key_here
   ```

**Quota Monitoring:**
- Default quota: 10,000 units/day (free tier)
- `videos.list`: 1 unit per call (efficient)
- `search.list`: 100 units per call (avoid)
- Monitor usage in Google Cloud Console: APIs & Services → Dashboard
- The collector will log warnings at 80% quota (8,000 units)

**For Railway Deployment:**
1. Go to Railway project → Variables
2. Add the environment variable:
   - `YOUTUBE_API_KEY`
3. Redeploy the service

### Google Trends Data Collection (PyTrends)

The Google Trends collector uses the unofficial PyTrends library to scrape Google Trends data.

**IMPORTANT:** PyTrends is an unofficial library that web-scrapes Google Trends. It's subject to breaking changes if Google modifies their website structure.

**Setup:**
1. **No API key required** - PyTrends uses web scraping
2. **Rate limiting enforced:** 60-second delays between requests (built into collector)
3. **Collection time:** ~50 minutes for 50 topics (1 min per topic)

**How It Works:**
- Collects "Interest Over Time" data (0-100 normalized scale)
- 7-day historical data for spike detection
- Z-score calculation to detect trending topics
- No authentication required

**Monitoring:**
- Watch logs for `TooManyRequestsError` (rate limit warnings)
- Check for PyTrends library errors in structured logs
- System gracefully degrades if PyTrends unavailable (other collectors continue working)

**Troubleshooting:**

**Problem:** Rate limit errors (TooManyRequestsError)
- **Solution:** Increase delay to 90-120 seconds in `google_trends_collector.py` (line 789: change `if elapsed < 60:` to `if elapsed < 90:`)

**Problem:** PyTrends library breaks (Google changed their website)
- **Solution:** Check PyPI for updates: `pip install --upgrade pytrends`
- **Workaround:** System continues working without Google Trends data (graceful degradation)

**Problem:** Collection takes too long (50 minutes)
- **Solution:** Reduce `DEFAULT_TOPICS` count in `google_trends_collector.py` (change from 50 to 30 topics)

**For Railway Deployment:**
- No configuration needed
- PyTrends package automatically installed from `requirements.txt`
- No environment variables required

### SimilarWeb API Setup

The SimilarWeb collector requires an existing SimilarWeb API subscription.

**Setup:**
1. **Obtain API key** from SimilarWeb subscription portal
2. **Rate limits** vary by subscription tier
3. **No free tier** - requires paid subscription

**Configuration:**
1. Add to `.env` file:
   ```env
   SIMILARWEB_API_KEY=your_key_here
   ```

**Monitoring:**
- Watch logs for HTTP 429 (rate limit) errors
- Monitor API usage in SimilarWeb portal
- System gracefully degrades if SimilarWeb unavailable

**Troubleshooting:**

**Problem:** 401 Unauthorized
- **Solution:** Verify SIMILARWEB_API_KEY is correct and active

**Problem:** 429 Rate Limit Exceeded
- **Solution:** Check subscription tier limits in SimilarWeb portal
- **Workaround:** Reduce DEFAULT_DOMAINS count

**Problem:** 404 Domain Not Found
- **Solution:** Domain not tracked by SimilarWeb (too small/new)
- **Behavior:** Collector logs warning and continues with other domains

**For Railway Deployment:**
1. Go to Railway project → Variables
2. Add environment variable:
   - `SIMILARWEB_API_KEY`
3. Redeploy the service

## Automated Daily Collection (APScheduler)

The system automatically collects trend data every day at **7:30 AM Pacific time** using APScheduler.

### How It Works

1. **Scheduler starts automatically** when FastAPI backend starts
2. **Daily cron job** triggers at 7:30 AM Pacific (configured in `app/scheduler.py`)
3. **Reuses same logic** as manual POST /collect endpoint
4. **Prevents duplicates** - skips if previous collection still in progress
5. **Retry logic** - retries once after 30 minutes if collection fails
6. **Failure alerting** - logs CRITICAL alert if collection fails 2 days in a row

### Scheduler Configuration

APScheduler is configured with:
- **Type:** BackgroundScheduler (non-blocking, separate thread)
- **Timezone:** America/Los_Angeles (Pacific)
- **Schedule:** Daily at 7:30 AM
- **Max instances:** 1 (prevents overlapping runs)
- **Misfire grace time:** 15 minutes

### Health Check Endpoint

The `/health` endpoint includes scheduler status:

```bash
curl http://localhost:8000/health
```

**Response:**
```json
{
  "status": "healthy",
  "service": "trend-monitor-api",
  "version": "1.0.0",
  "scheduler": {
    "running": true,
    "jobs_count": 1,
    "next_run": "2026-01-13T15:30:00+00:00"
  }
}
```

### Railway "Always On" Configuration

For scheduled jobs to work 24/7 on Railway, the service must not sleep:

**Option 1: Enable "Always On" (Recommended)**
1. Go to Railway dashboard: https://railway.app
2. Select "trend-monitor" project → backend service
3. Click "Settings" tab
4. Scroll to "Service Settings"
5. Enable "Always On" (keeps service running 24/7)
6. Save changes

**Note:** "Always On" may require Railway Pro plan ($5/month)

**Option 2: UptimeRobot Keep-Alive (Free Alternative)**

If Railway "Always On" is unavailable, use UptimeRobot to ping the service:

1. Sign up at https://uptimerobot.com (free tier)
2. Create new monitor:
   - **Monitor Type:** HTTP(s)
   - **Friendly Name:** trend-monitor-backend
   - **URL:** https://your-app.railway.app/health
   - **Monitoring Interval:** 5 minutes
3. UptimeRobot pings /health every 5 minutes, keeping Railway service awake

### Verification Script

Verify the scheduler is running:

```bash
cd backend
python scripts/verify_scheduler.py
```

**Example Output:**
```
============================================================
Scheduler Health Check
============================================================
Status: healthy
Service: trend-monitor-api
Version: 1.0.0

Scheduler Info:
  Running: True
  Jobs Count: 1
  Next Run: 2026-01-13T15:30:00+00:00
============================================================
✅ Scheduler is healthy and jobs are scheduled!
```

### Troubleshooting

**Problem:** Scheduler not running (jobs_count: 0)
- **Solution:** Check logs for scheduler initialization errors
- **Verify:** `scheduler.py` imports correctly with `python -c "from app.scheduler import scheduler"`

**Problem:** Railway service sleeping (scheduler stops)
- **Solution:** Enable "Always On" in Railway dashboard OR configure UptimeRobot

**Problem:** Collection fails 2 days in a row
- **Check logs** for CRITICAL alert: "ALERT: Scheduled collection failed 2 days in a row"
- **Investigate:** API credentials, rate limits, or service availability
- **Fix:** Resolve underlying issue and verify next scheduled run

**Problem:** Scheduled job runs late (after 7:30 AM)
- **Normal behavior:** Misfire grace time allows up to 15 minutes late start
- **If consistently late:** Check Railway service health and resource usage

### Manual Override

The manual POST /collect endpoint remains available for on-demand collection:

```bash
curl -X POST http://localhost:8000/collect \
  -H "Authorization: Bearer <your_jwt_token>"
```

Both scheduled and manual collections use the same underlying logic and prevent duplicates.

## Project Structure

```
backend/
├── app/
│   ├── __init__.py
│   ├── main.py                      # FastAPI application
│   ├── config.py                    # Settings and environment variables
│   ├── database.py                  # Database connection
│   ├── collectors/                  # Data collection infrastructure
│   │   ├── __init__.py
│   │   ├── base.py                  # DataCollector ABC
│   │   ├── orchestrator.py          # CollectionOrchestrator
│   │   ├── rate_limiters.py         # Rate limiting classes
│   │   ├── retry.py                 # Retry decorator
│   │   └── reddit_collector.py      # Reddit API collector
│   ├── core/                        # Core utilities
│   │   ├── security.py              # JWT functions
│   │   └── logging_config.py        # JSON logging
│   ├── models/                      # SQLAlchemy models
│   │   ├── base.py
│   │   ├── trend.py
│   │   ├── data_collection.py
│   │   ├── user.py
│   │   └── api_quota_usage.py
│   ├── api/                         # API routes
│   │   ├── auth.py
│   │   └── admin.py
│   └── schemas/                     # Pydantic schemas
│       └── auth.py
├── alembic/                         # Database migrations
│   ├── versions/
│   └── env.py
├── tests/                           # Test suite
│   ├── conftest.py
│   ├── test_models.py
│   └── test_collectors/
├── scripts/                         # Utility scripts
├── requirements.txt
└── README.md
```

## API Documentation

Once the server is running, visit:
- **Swagger UI:** http://localhost:8000/docs
- **ReDoc:** http://localhost:8000/redoc

## Authentication

The API uses JWT tokens for authentication:

1. **Login:** POST `/auth/login` with username/password
2. **Response:** Returns `access_token`
3. **Usage:** Include token in Authorization header:
   ```
   Authorization: Bearer <token>
   ```

### Bootstrap User

**Username:** `dave`
**Password:** `changeme123`

## Manual Data Collection

### POST /collect

Manually trigger data collection from all 4 APIs (Reddit, YouTube, Google Trends, SimilarWeb).

**Authentication:** Requires JWT token

**Request:**
```bash
curl -X POST http://localhost:8000/collect \
  -H "Authorization: Bearer <your_jwt_token>"
```

**Response (202 Accepted):**
```json
{
  "collection_id": "550e8400-e29b-41d4-a716-446655440000",
  "status": "in_progress",
  "started_at": "2026-01-09T10:30:00Z",
  "message": "Collection started. This will take approximately 20-25 minutes."
}
```

**Errors:**
- **401 Unauthorized:** Missing or invalid JWT token
- **409 Conflict:** Collection already in progress

### GET /collections/{collection_id}

Check the status of a running or completed collection.

**Authentication:** Requires JWT token

**Request:**
```bash
curl -X GET http://localhost:8000/collections/{collection_id} \
  -H "Authorization: Bearer <your_jwt_token>"
```

**Response (200 OK):**
```json
{
  "collection_id": "550e8400-e29b-41d4-a716-446655440000",
  "status": "completed",
  "started_at": "2026-01-09T10:30:00Z",
  "completed_at": "2026-01-09T10:52:00Z",
  "trends_found": 47,
  "duration_minutes": 22.5,
  "errors": null
}
```

**Status Values:**
- `in_progress` - Collection is running
- `completed` - Collection finished successfully
- `failed` - Collection encountered an error

**Errors:**
- **401 Unauthorized:** Missing or invalid JWT token
- **404 Not Found:** Collection ID doesn't exist

### Integration Testing Script

Test the collection endpoint manually:

```bash
cd backend
python -m scripts.test_manual_collection
```

This script will:
1. Login with test credentials
2. Trigger a collection
3. Poll status every 30 seconds
4. Display final results

## Testing

Run the test suite:
```bash
pytest
```

Run specific test file:
```bash
pytest tests/test_collectors/test_reddit_collector.py -v
```

Run with coverage:
```bash
pytest --cov=app tests/
```

## Database Migrations

Create a new migration:
```bash
alembic revision --autogenerate -m "Description of changes"
```

Apply migrations:
```bash
alembic upgrade head
```

Rollback migration:
```bash
alembic downgrade -1
```

## Development

### Code Style

- Follow PEP 8 style guide
- Use type hints for all function signatures
- Add docstrings to all classes and public methods
- Use async/await for all I/O operations

### Adding a New API Collector

1. Create new file in `app/collectors/` (e.g., `youtube_collector.py`)
2. Inherit from `DataCollector` ABC
3. Implement required methods:
   - `async def collect(topics: List[str]) -> CollectionResult`
   - `async def health_check() -> bool`
   - `async def get_rate_limit_info() -> RateLimitInfo`
4. Use `RequestsPerMinuteRateLimiter` or `DailyQuotaRateLimiter`
5. Decorate API calls with `@retry_with_backoff`
6. Add tests in `tests/test_collectors/`

## Deployment

The backend is deployed on Railway:

1. **Push to main branch:** Triggers automatic deployment
2. **Environment variables:** Managed in Railway dashboard
3. **Database:** PostgreSQL plugin automatically provisioned
4. **Health check:** Railway monitors `/health` endpoint

## Troubleshooting

### Database Connection Issues

If you see "database connection failed":
1. Check `DATABASE_URL` is set correctly
2. Verify PostgreSQL is running
3. Check network connectivity to database host

### Reddit API Authentication Errors

If Reddit collector fails with "invalid_grant" or "unauthorized":
1. Verify `REDDIT_CLIENT_ID` and `REDDIT_CLIENT_SECRET` are correct
2. Check Reddit app type is "script" (not "web app")
3. Ensure redirect URI is set to http://localhost:8000

### Rate Limiting Issues

If you hit rate limits:
1. Reddit: 60 requests/minute with OAuth (wait 60 seconds)
2. Check logs for rate limit warnings
3. Adjust collection frequency if needed

## Contributing

1. Create a feature branch
2. Make your changes
3. Add tests for new functionality
4. Ensure all tests pass: `pytest`
5. Commit with descriptive message
6. Push and create pull request

## License

Proprietary - Internal use only
