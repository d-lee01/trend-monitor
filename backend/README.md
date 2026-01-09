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
