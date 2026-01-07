---
stepsCompleted: [1]
inputDocuments:
  - '_bmad-output/planning-artifacts/prd.md'
  - '_bmad-output/analysis/product-brief-2026-01-05.md'
  - '_bmad-output/analysis/research-technical-2026-01-05.md'
  - '_bmad-output/analysis/brainstorming-session-2026-01-05.md'
workflowType: 'architecture'
project_name: 'trend-monitor'
user_name: 'dave'
date: '2026-01-05'
---

# Architecture Decision Document - trend-monitor

**Project:** trend-monitor (Quantified Trend Monitoring System)
**Author:** dave
**Date:** 2026-01-05
**Status:** In Progress

_This document captures architectural decisions for the trend-monitor system, optimized for AI agent implementation consistency._

---

## Executive Summary

**System Purpose:** Quantified trend monitoring system that predicts high-impact content opportunities through cross-platform signal convergence, enabling content teams to act on trends during Phase 2-3 (niche-to-mainstream transition).

**Architectural Approach:** Event-driven data collection system with batch processing, normalized scoring engine, and web-based dashboard for visualization.

**Key Design Principles:**
1. **API-First Design:** Modular API integrations allow easy addition of new data sources
2. **Offline-First Data Collection:** Twice-weekly batch collection decouples data gathering from user experience
3. **Score Transparency:** All scoring calculations are deterministic and auditable
4. **Fail-Safe Operations:** System degrades gracefully when individual APIs fail
5. **Cost Optimization:** Stay within free tier limits through caching and quota management

---

## System Context

### Problem Statement
Content teams arrive late to trends because manual platform monitoring is slow and subjective. By the time a trend "feels big" across multiple platforms, it's already saturated. The system must detect cross-platform signal convergence to predict "big ding" moments 12-48 hours before mainstream saturation.

### Solution Overview
Multi-API data collection system that:
- Collects trend signals from Reddit, YouTube, Google Trends, SimilarWeb, NewsAPI
- Normalizes disparate metrics into comparable scores
- Calculates Cross-Platform Momentum Score based on signal convergence
- Assigns confidence levels (🔥⚡👀) to guide content decisions
- Presents Top 10 trends via web dashboard with AI-generated briefs

### Success Criteria
- 70%+ hit rate on high-confidence (🔥) trends reaching >1M impressions within 72 hours
- Meeting prep time reduction from 2 hours to 15 minutes
- Data collection completes in <30 minutes per run
- Dashboard loads in <2 seconds

---

## Architectural Decisions

### AD-1: Three-Tier Architecture with Batch Processing

**Decision:** Adopt three-tier architecture (Presentation → Application → Data) with batch-oriented data processing rather than real-time streaming.

**Context:**
- MVP requires twice-weekly data collection (not real-time)
- User accesses dashboard intermittently (before content meetings)
- API rate limits favor batch collection over continuous polling
- Cost optimization critical (free tier APIs)

**Options Considered:**
1. **Real-time streaming architecture** - WebSockets, continuous API polling
   - ❌ Exceeds API rate limits
   - ❌ Higher infrastructure costs
   - ❌ Over-engineered for twice-weekly use case

2. **Three-tier batch architecture** - Scheduled batch jobs, cached results
   - ✅ Aligns with twice-weekly meeting cadence
   - ✅ Stays within API free tiers
   - ✅ Simpler implementation
   - ✅ Lower infrastructure costs

3. **Serverless event-driven** - Lambda functions triggered on schedule
   - ⚡ Good for Phase 2 (automated scheduling)
   - ❌ More complex for MVP
   - ❌ Cold start latency issues

**Decision Rationale:**
- Batch processing perfectly aligns with twice-weekly content meeting workflow
- Significantly simpler than real-time alternatives
- Enables aggressive caching to stay within free tier API limits
- Dashboard can serve cached data with <2sec load time

**Implementation:**
```
┌──────────────────┐
│  Presentation    │  React/Next.js Frontend
│  Layer           │  (Web Dashboard)
└────────┬─────────┘
         │ HTTPS/REST
┌────────▼─────────┐
│  Application     │  FastAPI Backend
│  Layer           │  • API orchestration
│                  │  • Score calculation
│                  │  • Business logic
└────────┬─────────┘
         │
┌────────▼─────────┐
│  Data Layer      │  PostgreSQL Database
│                  │  • Trend storage
│                  │  • Historical data
└──────────────────┘
```

**Consequences:**
- ✅ Simple, maintainable architecture
- ✅ Cost-efficient (free tier compatible)
- ✅ Easy to test and debug
- ⚠️ Not real-time (acceptable per requirements)
- ⚠️ Phase 2 automation requires job scheduling addition

**Alternatives for Phase 2:**
- Add APScheduler or Celery for automated twice-weekly jobs
- Consider serverless (AWS Lambda) if scaling beyond single user

---

### AD-2: Python Backend with FastAPI

**Decision:** Use Python 3.10+ with FastAPI framework for backend services.

**Context:**
- Need to integrate 5 different APIs (Reddit, YouTube, Google Trends, SimilarWeb, NewsAPI)
- Complex scoring algorithm requires clear, maintainable code
- Python has excellent libraries for all target APIs
- FastAPI provides modern async support for parallel API calls

**Options Considered:**
1. **Node.js/Express**
   - ❌ Weaker API client libraries for Reddit/YouTube
   - ❌ Less mature scientific computing ecosystem for scoring algorithms
   - ✅ Good frontend/backend language consistency

2. **Python/Flask**
   - ✅ Excellent API libraries (praw, google-api-python-client, pytrends)
   - ✅ Strong for data processing and algorithms
   - ⚠️ Flask lacks native async support (important for parallel API calls)

3. **Python/FastAPI** (CHOSEN)
   - ✅ Excellent API libraries (praw, google-api-python-client, pytrends)
   - ✅ Native async/await for parallel API calls
   - ✅ Automatic API documentation (OpenAPI/Swagger)
   - ✅ Fast development velocity
   - ✅ Type hints improve code quality

**Decision Rationale:**
- Python has best-in-class libraries for all 5 APIs
- FastAPI's async support critical for parallel data collection (<30min requirement)
- Automatic API docs helpful for future expansion
- Strong typing reduces bugs in complex scoring logic

**Implementation Details:**
```python
# Tech Stack
- Python 3.10+
- FastAPI (web framework)
- praw (Reddit API wrapper)
- google-api-python-client (YouTube API)
- pytrends (Google Trends - unofficial)
- requests (SimilarWeb, NewsAPI, Claude API)
- SQLAlchemy (ORM for PostgreSQL)
- asyncio (parallel API calls)
- pydantic (data validation)
```

**Consequences:**
- ✅ Rapid development with mature libraries
- ✅ Parallel API calls via asyncio meet <30min collection requirement
- ✅ Type safety via pydantic models
- ⚠️ Python performance adequate for MVP scale, may need optimization at 100+ users

---

### AD-3: PostgreSQL for Data Persistence

**Decision:** Use PostgreSQL as primary database for trend data and application state.

**Context:**
- Need to store structured trend data with relationships
- Historical data tracking for future analytics
- ACID compliance for data integrity
- Support future multi-user expansion

**Options Considered:**
1. **MongoDB/NoSQL**
   - ❌ Overkill for structured relational data
   - ❌ Less mature Python ecosystem
   - ❌ Harder to query for analytics

2. **SQLite**
   - ✅ Simple setup, file-based
   - ❌ Doesn't scale beyond single user
   - ❌ Concurrent write limitations
   - ❌ Blocks Phase 2 multi-user expansion

3. **PostgreSQL** (CHOSEN)
   - ✅ Mature, reliable, well-documented
   - ✅ Excellent Python support (SQLAlchemy)
   - ✅ JSONB column type for flexible metadata
   - ✅ Supports future scaling (multi-user, analytics)
   - ✅ Managed services available (Railway, AWS RDS)

**Decision Rationale:**
- Structured relational data with clear relationships (trends, collections, users)
- JSONB columns provide flexibility for API response metadata
- Supports Phase 2 expansion without migration
- Managed services (Railway, AWS RDS) eliminate ops burden

**Schema Design:**
```sql
-- Core Tables
CREATE TABLE trends (
    id UUID PRIMARY KEY,
    title VARCHAR(500),
    collection_id UUID REFERENCES data_collections(id),
    created_at TIMESTAMP DEFAULT NOW(),

    -- Platform Metrics (raw)
    reddit_score INTEGER,
    reddit_comments INTEGER,
    reddit_upvote_ratio FLOAT,
    reddit_subreddit VARCHAR(100),

    youtube_views INTEGER,
    youtube_likes INTEGER,
    youtube_channel VARCHAR(200),

    google_trends_interest INTEGER,
    google_trends_related_queries JSONB,

    similarweb_traffic INTEGER,
    similarweb_sources JSONB,

    newsapi_article_count INTEGER,
    newsapi_top_sources JSONB,

    -- Normalized Scores
    reddit_velocity_score FLOAT,
    youtube_traction_score FLOAT,
    google_trends_spike_score FLOAT,
    similarweb_bonus_applied BOOLEAN,

    -- Composite Score
    momentum_score FLOAT,
    confidence_level VARCHAR(10) CHECK (confidence_level IN ('high', 'medium', 'low')),

    -- AI Generated
    ai_brief TEXT,
    ai_brief_generated_at TIMESTAMP,

    INDEX idx_momentum_score (momentum_score DESC),
    INDEX idx_created_at (created_at DESC),
    INDEX idx_confidence_level (confidence_level)
);

CREATE TABLE data_collections (
    id UUID PRIMARY KEY,
    started_at TIMESTAMP DEFAULT NOW(),
    completed_at TIMESTAMP,
    status VARCHAR(20) CHECK (status IN ('in_progress', 'completed', 'failed')),
    errors JSONB,

    -- Collection Metadata
    reddit_api_calls INTEGER,
    youtube_api_quota_used INTEGER,
    google_trends_api_calls INTEGER,

    INDEX idx_started_at (started_at DESC)
);

CREATE TABLE users (
    id UUID PRIMARY KEY,
    username VARCHAR(100) UNIQUE,
    password_hash VARCHAR(255),
    created_at TIMESTAMP DEFAULT NOW(),
    last_login TIMESTAMP
);
```

**Consequences:**
- ✅ Supports complex queries for future analytics
- ✅ JSONB flexibility for evolving API response structures
- ✅ Scales to Phase 2 multi-user without migration
- ✅ Managed services eliminate database operations burden
- ⚠️ Slightly more complex than SQLite for MVP

---

### AD-4: Modular API Integration Pattern

**Decision:** Implement each API integration as independent, async-capable module with standardized interface.

**Context:**
- 5 different APIs with different patterns and rate limits
- APIs may fail independently - system must gracefully degrade
- Future expansion requires easy addition of new sources (Sprout Social in Phase 2)
- Parallel collection critical for <30min requirement

**Pattern Design:**
```python
# Base Interface
class DataCollector(ABC):
    @abstractmethod
    async def collect(self, topics: List[str]) -> CollectionResult:
        """Collect data for given topics"""
        pass

    @abstractmethod
    async def health_check(self) -> bool:
        """Check if API is accessible"""
        pass

    @abstractmethod
    def get_rate_limit_info(self) -> RateLimitInfo:
        """Return current rate limit status"""
        pass

# Implementations
class RedditCollector(DataCollector):
    def __init__(self, client_id: str, client_secret: str):
        self.client = praw.Reddit(...)
        self.rate_limiter = RateLimiter(60, window=60)  # 60 req/min

    async def collect(self, topics: List[str]) -> CollectionResult:
        results = []
        for topic in topics:
            await self.rate_limiter.acquire()
            # Collect from Reddit with retry logic
            try:
                data = await self._fetch_reddit_data(topic)
                results.append(data)
            except RedditAPIError as e:
                logger.error(f"Reddit API error for {topic}: {e}")
                results.append(None)  # Graceful degradation
        return CollectionResult(source='reddit', data=results)

# Similar implementations for:
# - YouTubeCollector
# - GoogleTrendsCollector
# - SimilarWebCollector
# - NewsAPICollector

# Orchestration
class CollectionOrchestrator:
    def __init__(self, collectors: List[DataCollector]):
        self.collectors = collectors

    async def collect_all(self, topics: List[str]) -> Dict[str, CollectionResult]:
        """Collect from all sources in parallel"""
        tasks = [
            collector.collect(topics)
            for collector in self.collectors
        ]
        results = await asyncio.gather(*tasks, return_exceptions=True)

        # Handle failures gracefully
        return {
            collector.name: result
            for collector, result in zip(self.collectors, results)
            if not isinstance(result, Exception)
        }
```

**Key Features:**
1. **Standardized Interface:** All collectors implement DataCollector ABC
2. **Async-First:** Native async/await for parallel collection
3. **Rate Limiting:** Built-in rate limiters per API requirements
4. **Retry Logic:** Exponential backoff for transient failures
5. **Graceful Degradation:** System works even if 1-2 APIs fail
6. **Observable:** Rate limit info exposed for monitoring

**Decision Rationale:**
- Parallel collection via asyncio.gather meets <30min requirement
- Independent modules isolate API-specific logic
- Easy to add new collectors (Sprout Social in Phase 2)
- Standardized interface enables testing with mocks

**Consequences:**
- ✅ Parallel collection achieves <30min target
- ✅ System resilient to individual API failures
- ✅ Easy to add new sources in Phase 2
- ✅ Testable with mock collectors
- ⚠️ Async complexity requires careful error handling

---

### AD-5: Scoring Algorithm as Pure Functions

**Decision:** Implement all scoring and normalization logic as pure, deterministic functions separate from data collection.

**Context:**
- Scoring algorithm is core product differentiator
- Must be testable, auditable, and tunable
- Should evolve based on real-world hit rate data
- AI agents need clear scoring rules for consistency

**Architecture:**
```python
# scoring/normalizer.py
def normalize_reddit_score(
    score: int,
    hours_since_post: float,
    subreddit_size: int
) -> float:
    """Normalize Reddit score to 0-100 scale

    Formula: (score / hours_since_post) × log(subreddit_size)
    Normalized using empirical max values from historical data
    """
    velocity = score / max(hours_since_post, 1)
    authority_weight = math.log10(max(subreddit_size, 1))
    raw_score = velocity * authority_weight

    # Normalize to 0-100 using empirical max (tunable)
    MAX_REDDIT_VELOCITY = 10000  # Based on historical data
    normalized = min(100, (raw_score / MAX_REDDIT_VELOCITY) * 100)

    return normalized

def normalize_youtube_traction(
    views: int,
    hours_since_publish: float,
    likes: int,
    channel_subs: int
) -> float:
    """Normalize YouTube metrics to 0-100 scale

    Formula: (views / hours) × (engagement_rate) × log(channel_subs)
    """
    velocity = views / max(hours_since_publish, 1)
    engagement_rate = likes / max(views, 1)
    authority_weight = math.log10(max(channel_subs, 1))
    raw_score = velocity * engagement_rate * authority_weight

    MAX_YOUTUBE_TRACTION = 50000  # Tunable
    normalized = min(100, (raw_score / MAX_YOUTUBE_TRACTION) * 100)

    return normalized

def calculate_google_trends_spike(
    current_interest: int,
    seven_day_history: List[int]
) -> float:
    """Calculate spike score using z-score

    Formula: (current - mean) / stddev
    Already 0-100 scale from Google Trends
    """
    if len(seven_day_history) < 2:
        return current_interest  # Not enough history

    mean = statistics.mean(seven_day_history)
    stddev = statistics.stdev(seven_day_history)

    if stddev == 0:
        return current_interest

    z_score = (current_interest - mean) / stddev

    # Convert z-score to 0-100 scale (z-score typically -3 to +3)
    normalized = min(100, max(0, (z_score + 3) / 6 * 100))

    return normalized

# scoring/momentum.py
def calculate_momentum_score(
    reddit_velocity: float,
    youtube_traction: float,
    google_trends_spike: float,
    similarweb_traffic_spike: bool
) -> Tuple[float, str]:
    """Calculate Cross-Platform Momentum Score

    Returns: (momentum_score, confidence_level)
    """
    # Base score (all inputs already normalized 0-100)
    base_score = (
        reddit_velocity * 0.33 +
        youtube_traction * 0.33 +
        google_trends_spike * 0.34
    )

    # Apply SimilarWeb bonus if traffic spike detected
    if similarweb_traffic_spike:
        base_score *= 1.5

    # Determine confidence level based on signal convergence
    signals_present = sum([
        reddit_velocity > 50,
        youtube_traction > 50,
        google_trends_spike > 50,
        similarweb_traffic_spike
    ])

    if signals_present >= 4:
        confidence = 'high'  # 🔥 All signals aligned
    elif signals_present >= 2:
        confidence = 'medium'  # ⚡ 2-3 signals
    else:
        confidence = 'low'  # 👀 1 signal

    return (base_score, confidence)
```

**Decision Rationale:**
- Pure functions are testable with unit tests
- Deterministic output allows auditing and debugging
- Easy to tune thresholds based on real-world hit rate data
- Clear separation of concerns (data collection vs. scoring)
- AI agents can reference these functions for consistency

**Tuning Strategy:**
- Start with initial thresholds based on research
- Track actual hit rates for each confidence level
- Adjust normalization constants (MAX_REDDIT_VELOCITY, etc.) based on real data
- Version scoring algorithm (v1, v2, etc.) to compare performance

**Consequences:**
- ✅ Highly testable with unit tests
- ✅ Deterministic and auditable
- ✅ Easy to tune based on real-world data
- ✅ Clear documentation for AI agents
- ⚠️ Initial thresholds are estimates, will need tuning

---

### AD-6: React/Next.js Frontend with Server-Side Rendering

**Decision:** Use Next.js (React framework) with server-side rendering for the dashboard frontend.

**Context:**
- Need simple, fast-loading dashboard (<2sec requirement)
- Single-page application sufficient (no complex navigation)
- Server-side rendering improves initial load time
- TypeScript for type safety

**Options Considered:**
1. **Pure React SPA**
   - ✅ Simple, well-understood
   - ❌ Client-side rendering slower initial load
   - ❌ No SEO benefits (not critical for authenticated dashboard)

2. **Next.js** (CHOSEN)
   - ✅ Server-side rendering for fast initial load (<2sec requirement)
   - ✅ Built-in routing and API routes
   - ✅ Excellent TypeScript support
   - ✅ Easy deployment to Vercel/Netlify
   - ✅ Image optimization built-in

3. **Vue.js/Nuxt**
   - ✅ Similar benefits to Next.js
   - ❌ Less familiar to most developers
   - ❌ Smaller ecosystem than React

**Architecture:**
```
trend-monitor/
├── frontend/                # Next.js Application
│   ├── pages/
│   │   ├── index.tsx       # Dashboard (Trending Now)
│   │   ├── trend/[id].tsx  # Trend Detail View
│   │   └── api/            # Next.js API routes (proxy to backend)
│   ├── components/
│   │   ├── TrendCard.tsx   # Individual trend display
│   │   ├── TrendList.tsx   # Top 10 list
│   │   ├── ConfidenceBadge.tsx  # 🔥⚡👀 indicators
│   │   └── DataCollectionButton.tsx
│   ├── lib/
│   │   ├── api.ts          # Backend API client
│   │   └── types.ts        # TypeScript interfaces
│   └── styles/
│       └── globals.css     # TailwindCSS
```

**Component Design:**
```typescript
// components/TrendCard.tsx
interface TrendCardProps {
  trend: {
    id: string;
    title: string;
    confidence: 'high' | 'medium' | 'low';
    reddit_score: number;
    youtube_views: number;
    google_trends_interest: number;
    similarweb_traffic_change: number;
    momentum_score: number;
    created_at: string;
  };
  onExplain: (trendId: string) => void;
}

export const TrendCard: React.FC<TrendCardProps> = ({ trend, onExplain }) => {
  return (
    <div className="trend-card">
      <ConfidenceBadge level={trend.confidence} />
      <h3>{trend.title}</h3>
      <div className="metrics">
        <span>Reddit: {formatNumber(trend.reddit_score)}</span>
        <span>YouTube: {formatNumber(trend.youtube_views)}</span>
        <span>Google Trends: {trend.google_trends_interest}</span>
        <span>SimilarWeb: {formatPercent(trend.similarweb_traffic_change)}</span>
      </div>
      <button onClick={() => onExplain(trend.id)}>
        Explain This Trend
      </button>
    </div>
  );
};
```

**Decision Rationale:**
- Next.js SSR meets <2sec load time requirement
- TypeScript prevents runtime errors with complex trend data
- Component-based architecture easy to maintain
- TailwindCSS for rapid UI development

**Consequences:**
- ✅ Fast initial page load (<2sec)
- ✅ Type-safe frontend code
- ✅ Easy to deploy (Vercel/Netlify)
- ⚠️ Slightly more complex than pure React (acceptable trade-off)

---

### AD-7: Authentication via JWT with Single-User Bootstrap

**Decision:** Implement JWT-based authentication with hardcoded single-user credentials for MVP, database-backed for Phase 2.

**Context:**
- MVP requires single user (dave) only
- Phase 2 expansion needs multi-user support
- Must be secure (HTTPS, password hashing)
- Simple implementation for MVP

**Architecture:**
```python
# auth/jwt_handler.py
from jose import jwt, JWTError
from passlib.context import CryptContext
from datetime import datetime, timedelta

SECRET_KEY = os.getenv("JWT_SECRET_KEY")  # From env
ALGORITHM = "HS256"
ACCESS_TOKEN_EXPIRE_DAYS = 7

pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")

def verify_password(plain_password: str, hashed_password: str) -> bool:
    return pwd_context.verify(plain_password, hashed_password)

def create_access_token(data: dict) -> str:
    to_encode = data.copy()
    expire = datetime.utcnow() + timedelta(days=ACCESS_TOKEN_EXPIRE_DAYS)
    to_encode.update({"exp": expire})
    encoded_jwt = jwt.encode(to_encode, SECRET_KEY, algorithm=ALGORITHM)
    return encoded_jwt

def decode_access_token(token: str) -> dict:
    try:
        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
        return payload
    except JWTError:
        raise InvalidTokenException()

# auth/users.py (MVP - single user)
USERS_DB = {
    "dave": {
        "username": "dave",
        "hashed_password": pwd_context.hash(os.getenv("INITIAL_PASSWORD")),
        "user_id": "user_1"
    }
}

async def authenticate_user(username: str, password: str) -> Optional[User]:
    user = USERS_DB.get(username)
    if not user:
        return None
    if not verify_password(password, user["hashed_password"]):
        return None
    return User(**user)

# FastAPI routes
@app.post("/auth/login")
async def login(credentials: LoginCredentials):
    user = await authenticate_user(credentials.username, credentials.password)
    if not user:
        raise HTTPException(status_code=401, detail="Invalid credentials")

    access_token = create_access_token({"sub": user.username, "user_id": user.user_id})
    return {"access_token": access_token, "token_type": "bearer"}

@app.get("/auth/me")
async def get_current_user(token: str = Depends(oauth2_scheme)):
    payload = decode_access_token(token)
    username = payload.get("sub")
    if not username or username not in USERS_DB:
        raise HTTPException(status_code=401, detail="Invalid token")
    return User(**USERS_DB[username])
```

**Phase 2 Migration Path:**
```python
# Replace USERS_DB dict with database queries
async def authenticate_user(username: str, password: str) -> Optional[User]:
    user = await db.get_user_by_username(username)
    if not user:
        return None
    if not verify_password(password, user.hashed_password):
        return None
    return user
```

**Decision Rationale:**
- JWT tokens enable stateless authentication (scalable)
- 7-day token expiration balances convenience and security
- Hardcoded user for MVP simplifies initial deployment
- Easy migration path to database-backed users in Phase 2

**Security Measures:**
- HTTPS enforced for all communication
- Bcrypt for password hashing
- JWT secret stored in environment variable
- Token expiration (7 days)
- CORS configured for frontend origin only

**Consequences:**
- ✅ Secure authentication for MVP
- ✅ Stateless (JWT) scales to multi-user
- ✅ Simple MVP implementation
- ⚠️ Requires environment variable management
- ⚠️ Phase 2 requires user table + registration flow

---

### AD-8: Deployment on Railway with Managed PostgreSQL

**Decision:** Deploy to Railway platform with managed PostgreSQL database.

**Context:**
- Need simple, low-cost deployment for MVP (<$50/month)
- Managed database eliminates ops burden
- Easy CI/CD integration
- Room to scale in Phase 2

**Options Considered:**
1. **Heroku**
   - ✅ Simple deployment
   - ❌ Expensive compared to alternatives
   - ❌ Postgres add-on costs add up

2. **AWS (Elastic Beanstalk + RDS)**
   - ✅ Industry standard, scalable
   - ❌ Complex setup for MVP
   - ❌ Requires AWS expertise
   - ⚠️ Cost can escalate quickly

3. **Railway** (CHOSEN)
   - ✅ Simple deployment (git push)
   - ✅ Managed PostgreSQL included
   - ✅ Affordable ($5-20/month for MVP)
   - ✅ Built-in CI/CD
   - ✅ Environment variable management
   - ✅ Easy scaling path

4. **DigitalOcean App Platform**
   - ✅ Similar to Railway
   - ⚠️ Slightly more complex than Railway
   - ✅ Good alternative if Railway insufficient

**Railway Architecture:**
```
Railway Project: trend-monitor
├── Backend Service (Python/FastAPI)
│   ├── Auto-deploy from GitHub main branch
│   ├── Environment variables (API keys, JWT secret)
│   └── Health check endpoint: /health
├── Frontend Service (Next.js)
│   ├── Auto-deploy from GitHub main branch
│   ├── Environment variables (BACKEND_URL)
│   └── Static site optimization
└── PostgreSQL Database
    ├── Managed by Railway
    ├── Automatic backups
    └── CONNECTION_STRING env variable
```

**Deployment Workflow:**
1. Push code to GitHub main branch
2. Railway auto-detects changes
3. Builds Docker containers (or uses buildpacks)
4. Deploys to production
5. Health checks confirm deployment
6. Rollback available if deployment fails

**Cost Estimate (MVP):**
- Backend compute: $5-10/month
- Frontend static hosting: $0-5/month (or use Vercel)
- PostgreSQL: $5-10/month
- **Total: $10-25/month**

**Decision Rationale:**
- Railway's simplicity perfect for MVP (non-technical user)
- Managed Postgres eliminates database ops
- Built-in CI/CD from GitHub
- Cost well under $50/month budget
- Easy migration to AWS/GCP if needed in future

**Alternative for Frontend:**
- Consider deploying Next.js to Vercel (free tier) for even lower costs
- Backend on Railway, Frontend on Vercel

**Consequences:**
- ✅ Simple deployment process (git push)
- ✅ Managed database (no ops burden)
- ✅ Cost-efficient (~$20/month)
- ✅ Built-in monitoring and logs
- ⚠️ Vendor lock-in to Railway (mitigated by containerization)
- ⚠️ May need migration to AWS for 100+ users (future concern)

---

### AD-9: Error Handling and Graceful Degradation

**Decision:** Implement comprehensive error handling with graceful degradation when individual APIs fail.

**Context:**
- 5 external APIs, any of which may fail temporarily
- System must remain useful even if 1-2 APIs are down
- User should see clear error messages, not crashes
- Momentum score calculation must adapt to missing data

**Strategy:**

**1. API-Level Error Handling:**
```python
class RedditCollector(DataCollector):
    async def collect(self, topics: List[str]) -> CollectionResult:
        results = []
        for topic in topics:
            try:
                await self.rate_limiter.acquire()
                data = await self._fetch_with_retry(topic, max_retries=3)
                results.append(data)
            except RateLimitExceeded:
                logger.warning(f"Reddit rate limit exceeded for {topic}")
                results.append(None)
                await asyncio.sleep(60)  # Back off
            except RedditAPIError as e:
                logger.error(f"Reddit API error for {topic}: {e}")
                results.append(None)  # Graceful degradation
            except Exception as e:
                logger.exception(f"Unexpected error for {topic}: {e}")
                results.append(None)

        return CollectionResult(
            source='reddit',
            data=results,
            success_rate=len([r for r in results if r]) / len(results)
        )

    async def _fetch_with_retry(
        self,
        topic: str,
        max_retries: int = 3
    ) -> Optional[Dict]:
        """Retry with exponential backoff"""
        for attempt in range(max_retries):
            try:
                return await self._fetch_reddit_data(topic)
            except TransientError:
                if attempt < max_retries - 1:
                    wait_time = 2 ** attempt  # Exponential backoff
                    await asyncio.sleep(wait_time)
                else:
                    raise
```

**2. Score Calculation with Missing Data:**
```python
def calculate_momentum_score_safe(
    reddit_velocity: Optional[float],
    youtube_traction: Optional[float],
    google_trends_spike: Optional[float],
    similarweb_traffic_spike: Optional[bool]
) -> Tuple[float, str]:
    """Calculate score even with missing platform data"""

    # Collect available scores
    available_scores = []
    if reddit_velocity is not None:
        available_scores.append(reddit_velocity)
    if youtube_traction is not None:
        available_scores.append(youtube_traction)
    if google_trends_spike is not None:
        available_scores.append(google_trends_spike)

    if not available_scores:
        # No data at all - cannot calculate
        return (0.0, 'unknown')

    # Calculate with available data
    base_score = sum(available_scores) / len(available_scores)

    if similarweb_traffic_spike:
        base_score *= 1.5

    # Adjust confidence based on available signals
    signals_present = len(available_scores)
    if similarweb_traffic_spike:
        signals_present += 1

    if signals_present >= 4:
        confidence = 'high'
    elif signals_present >= 2:
        confidence = 'medium'
    else:
        confidence = 'low'

    return (base_score, confidence)
```

**3. User-Facing Error Messages:**
```typescript
// Frontend error display
interface CollectionStatus {
  reddit: 'success' | 'partial' | 'failed';
  youtube: 'success' | 'partial' | 'failed';
  google_trends: 'success' | 'partial' | 'failed';
  similarweb: 'success' | 'partial' | 'failed';
  newsapi: 'success' | 'partial' | 'failed';
}

const CollectionStatusDisplay: React.FC<{ status: CollectionStatus }> = ({ status }) => {
  const hasFailures = Object.values(status).some(s => s === 'failed');

  if (!hasFailures) return null;

  return (
    <div className="alert alert-warning">
      <h4>Data Collection Issues</h4>
      <ul>
        {status.reddit === 'failed' && <li>Reddit API unavailable - Reddit data not included</li>}
        {status.youtube === 'failed' && <li>YouTube API unavailable - YouTube data not included</li>}
        {status.google_trends === 'failed' && <li>Google Trends unavailable - Search data not included</li>}
        {status.similarweb === 'failed' && <li>SimilarWeb unavailable - Traffic data not included</li>}
        {status.newsapi === 'failed' && <li>NewsAPI unavailable - News data not included</li>}
      </ul>
      <p>Momentum scores calculated with available data. Results may be less accurate.</p>
    </div>
  );
};
```

**Decision Rationale:**
- System remains functional even with 1-2 API failures
- Users see clear, actionable error messages
- Retry logic handles transient failures automatically
- Logging enables debugging and monitoring

**Consequences:**
- ✅ Resilient to individual API failures
- ✅ Clear error communication to users
- ✅ Automated retry for transient errors
- ✅ Comprehensive logging for debugging
- ⚠️ Reduced confidence scores when data missing (acceptable trade-off)

---

### AD-10: Observability and Monitoring Strategy

**Decision:** Implement lightweight observability for MVP with structured logging and basic metrics, expanding to full APM in Phase 2.

**Context:**
- Need to monitor API quota usage (critical for cost control)
- Track collection success rates
- Debug production issues
- MVP budget cannot support expensive APM tools

**MVP Observability Stack:**

**1. Structured Logging:**
```python
# logging_config.py
import logging
import json
from datetime import datetime

class StructuredLogger:
    def __init__(self, name: str):
        self.logger = logging.getLogger(name)
        self.logger.setLevel(logging.INFO)

        handler = logging.StreamHandler()
        handler.setFormatter(JsonFormatter())
        self.logger.addHandler(handler)

    def log_api_call(
        self,
        api_name: str,
        success: bool,
        duration_ms: float,
        quota_used: Optional[int] = None
    ):
        self.logger.info(json.dumps({
            "event": "api_call",
            "timestamp": datetime.utcnow().isoformat(),
            "api": api_name,
            "success": success,
            "duration_ms": duration_ms,
            "quota_used": quota_used
        }))

    def log_collection_complete(
        self,
        collection_id: str,
        duration_minutes: float,
        trends_found: int,
        api_failures: List[str]
    ):
        self.logger.info(json.dumps({
            "event": "collection_complete",
            "timestamp": datetime.utcnow().isoformat(),
            "collection_id": collection_id,
            "duration_minutes": duration_minutes,
            "trends_found": trends_found,
            "api_failures": api_failures
        }))
```

**2. API Quota Tracking:**
```python
class QuotaTracker:
    def __init__(self, db: Database):
        self.db = db

    async def record_youtube_quota_usage(self, units_used: int):
        """Track YouTube API quota usage"""
        await self.db.execute("""
            INSERT INTO api_quota_usage (api_name, date, units_used)
            VALUES ('youtube', CURRENT_DATE, $1)
            ON CONFLICT (api_name, date)
            DO UPDATE SET units_used = api_quota_usage.units_used + $1
        """, units_used)

    async def get_daily_youtube_quota() -> int:
        """Check current day's YouTube quota usage"""
        result = await self.db.fetch_one("""
            SELECT units_used FROM api_quota_usage
            WHERE api_name = 'youtube' AND date = CURRENT_DATE
        """)
        return result['units_used'] if result else 0

    async def alert_if_quota_high(self, threshold: float = 0.8):
        """Alert if approaching quota limit"""
        used = await self.get_daily_youtube_quota()
        limit = 10000  # YouTube free tier

        if used / limit > threshold:
            logger.warning(f"YouTube quota at {used}/{limit} ({used/limit*100:.1f}%)")
            # Send alert (email, Slack, etc.)
```

**3. Basic Metrics Dashboard:**
```python
# metrics/dashboard.py
@app.get("/metrics/collection-stats")
async def get_collection_stats(days: int = 7):
    """Return collection statistics for monitoring"""
    stats = await db.fetch_all("""
        SELECT
            DATE(started_at) as date,
            COUNT(*) as total_collections,
            AVG(EXTRACT(EPOCH FROM (completed_at - started_at))/60) as avg_duration_minutes,
            SUM(CASE WHEN status = 'failed' THEN 1 ELSE 0 END) as failures
        FROM data_collections
        WHERE started_at > NOW() - INTERVAL '{days} days'
        GROUP BY DATE(started_at)
        ORDER BY date DESC
    """)
    return stats

@app.get("/metrics/api-health")
async def get_api_health():
    """Return recent API success rates"""
    health = await db.fetch_all("""
        SELECT
            api_name,
            COUNT(*) as total_calls,
            SUM(CASE WHEN success THEN 1 ELSE 0 END) as successful_calls,
            AVG(duration_ms) as avg_duration_ms
        FROM api_call_logs
        WHERE timestamp > NOW() - INTERVAL '24 hours'
        GROUP BY api_name
    """)
    return health
```

**4. Simple Uptime Monitoring:**
- Use UptimeRobot (free tier) to monitor /health endpoint
- Alert via email if endpoint down >5 minutes

**Phase 2 Upgrades:**
- Add Sentry for error tracking ($26/month)
- Add DataDog or New Relic for APM
- Dashboard for visualizing metrics

**Decision Rationale:**
- Structured logging sufficient for MVP debugging
- Quota tracking critical for cost control
- Basic metrics expose operational health
- Free/low-cost tools keep within budget
- Easy upgrade path to full APM in Phase 2

**Consequences:**
- ✅ Adequate observability for MVP
- ✅ Quota tracking prevents cost overruns
- ✅ Structured logs enable debugging
- ✅ Low cost (~$0/month for MVP)
- ⚠️ Manual log analysis required (no APM dashboard)
- ⚠️ Phase 2 should add Sentry/DataDog

---

## Data Flow Diagrams

### Overall System Data Flow

```
┌─────────────────────────────────────────────────────────────┐
│                     User (dave)                             │
│              Opens Dashboard Browser                         │
└────────────┬────────────────────────────────────────────────┘
             │ HTTPS
             ▼
┌────────────────────────────────────────────────────────────┐
│          Next.js Frontend (Presentation Layer)              │
│  • Dashboard UI (Trending Now)                             │
│  • Trend Detail Views                                       │
│  • Data Collection Trigger Button                           │
└────────────┬───────────────────────────────────────────────┘
             │ REST API (HTTPS)
             ▼
┌────────────────────────────────────────────────────────────┐
│        FastAPI Backend (Application Layer)                  │
│                                                             │
│  ┌──────────────────────────────────────────────────────┐ │
│  │  API Endpoints:                                      │ │
│  │  • GET /trends (retrieve Top 10)                     │ │
│  │  • POST /collect (trigger data collection)          │ │
│  │  • POST /trends/{id}/explain (generate AI brief)    │ │
│  │  • POST /auth/login (authenticate)                   │ │
│  └──────────────────────────────────────────────────────┘ │
│                                                             │
│  ┌──────────────────────────────────────────────────────┐ │
│  │  Collection Orchestrator (Async Parallel)           │ │
│  │  ┌────────────────────────────────────────────────┐ │ │
│  │  │  Data Collectors (Async, Independent Modules)  │ │ │
│  │  │  • RedditCollector                             │ │ │
│  │  │  • YouTubeCollector                            │ │ │
│  │  │  • GoogleTrendsCollector                       │ │ │
│  │  │  • SimilarWebCollector                         │ │ │
│  │  │  • NewsAPICollector                            │ │ │
│  │  └────────────────────────────────────────────────┘ │ │
│  └───┬──────────────────────────────────────────────────┘ │
│      │                                                     │
│  ┌───▼──────────────────────────────────────────────────┐ │
│  │  Scoring Engine (Pure Functions)                    │ │
│  │  • normalize_reddit_score()                         │ │
│  │  • normalize_youtube_traction()                     │ │
│  │  • calculate_google_trends_spike()                  │ │
│  │  • calculate_momentum_score()                       │ │
│  └──────────────────────────────────────────────────────┘ │
│                                                             │
│  ┌──────────────────────────────────────────────────────┐ │
│  │  AI Brief Generator                                  │ │
│  │  • Calls Claude API                                  │ │
│  │  • Generates 3-sentence summaries                    │ │
│  └──────────────────────────────────────────────────────┘ │
└────────────┬───────────────────────────────────────────────┘
             │
             ▼
┌────────────────────────────────────────────────────────────┐
│         PostgreSQL Database (Data Layer)                    │
│  • trends table                                            │
│  • data_collections table                                   │
│  • users table                                              │
│  • api_quota_usage table                                    │
└────────────────────────────────────────────────────────────┘

External APIs (called by Collectors):
┌────────────┐  ┌─────────────┐  ┌───────────────┐
│ Reddit API │  │ YouTube API │  │ Google Trends │
└────────────┘  └─────────────┘  └───────────────┘
┌──────────────┐  ┌──────────┐  ┌────────────┐
│ SimilarWeb   │  │ NewsAPI  │  │ Claude API │
└──────────────┘  └──────────┘  └────────────┘
```

### Data Collection Flow (Detailed)

```
User clicks "Collect Latest Trends" button
│
▼
Frontend sends POST /collect
│
▼
Backend: CollectionOrchestrator.collect_all()
│
├─────────── Parallel Async Collection ────────────┐
│                                                   │
▼                  ▼                 ▼             ▼
RedditCollector  YouTubeCollector  GoogleTrends  SimilarWeb
    │                │                  │             │
    │ Rate Limit     │ Quota Check      │ Delay       │
    │ (60 req/min)   │ (10K units/day)  │ (60s)       │
    │                │                  │             │
    ▼                ▼                  ▼             ▼
Reddit API      YouTube API       Google (web)   SimilarWeb API
    │                │                  │             │
    │ Retry logic    │ Retry logic      │ Retry       │ Retry
    │ (3 attempts)   │ (3 attempts)     │ (3x)        │ (3x)
    │                │                  │             │
    ▼                ▼                  ▼             ▼
  Results          Results            Results       Results
    │                │                  │             │
    └────────────────┴──────────────────┴─────────────┘
                         │
                         ▼
              asyncio.gather() combines results
                         │
                         ▼
        Store raw data in database (trends table)
                         │
                         ▼
             For each trend, calculate scores:
             • normalize_reddit_score()
             • normalize_youtube_traction()
             • calculate_google_trends_spike()
             • calculate_momentum_score()
                         │
                         ▼
          Update trends table with scores & confidence
                         │
                         ▼
               Return Top 10 to Frontend
                         │
                         ▼
           Frontend displays Trending Now list
```

### AI Brief Generation Flow

```
User clicks "Explain This Trend" button on trend #3
│
▼
Frontend sends POST /trends/{id}/explain
│
▼
Backend: Retrieve trend data from database
│
▼
Backend: Build prompt for Claude API
    • Trend title
    • Platform metrics (Reddit score, YouTube views, etc.)
    • Why it's trending (velocity, convergence signals)
    • Where it's big (geographic data if available)
│
▼
Backend: Call Claude API (Anthropic)
    Request:
    {
      "model": "claude-3-5-sonnet-20241022",
      "max_tokens": 150,
      "messages": [{
        "role": "user",
        "content": "Explain this trend in 3 sentences: {prompt}"
      }]
    }
│
▼
Claude API returns 3-sentence summary
│
▼
Backend: Store AI brief in trends table (ai_brief column)
│
▼
Backend: Return AI brief to Frontend
│
▼
Frontend: Display AI brief inline below trend
```

---

## Technology Stack Summary

### Backend
- **Language:** Python 3.10+
- **Framework:** FastAPI
- **ORM:** SQLAlchemy
- **API Clients:**
  - `praw` (Reddit API wrapper)
  - `google-api-python-client` (YouTube Data API)
  - `pytrends` (Google Trends - unofficial)
  - `requests` (SimilarWeb API, NewsAPI, Claude API)
- **Auth:** `python-jose` (JWT), `passlib` (password hashing)
- **Async:** `asyncio`, `aiohttp`
- **Testing:** `pytest`, `pytest-asyncio`

### Frontend
- **Framework:** Next.js 14+ (React 18+)
- **Language:** TypeScript
- **Styling:** TailwindCSS
- **State Management:** React Context API or Zustand
- **HTTP Client:** `axios` or `fetch`
- **Testing:** Jest, React Testing Library

### Database
- **Database:** PostgreSQL 14+
- **ORM:** SQLAlchemy (Python)
- **Migrations:** Alembic
- **Hosting:** Railway managed PostgreSQL

### Infrastructure
- **Hosting:** Railway (backend + database)
- **Frontend Hosting:** Vercel or Railway
- **CI/CD:** GitHub Actions → Railway auto-deploy
- **Monitoring:** Railway logs + UptimeRobot
- **Secrets Management:** Railway environment variables

### External APIs
- **Reddit API:** OAuth 2.0, 60 req/min free
- **YouTube Data API v3:** API key, 10K units/day free
- **Google Trends:** PyTrends (unofficial), throttled
- **SimilarWeb API:** Existing subscription (paid)
- **NewsAPI:** API key, Developer tier free (testing), Business tier $449/mo (production)
- **Claude API:** Anthropic API key, pay-per-use

---

## Security Architecture

### Threat Model

**Assets to Protect:**
1. API keys (Reddit, YouTube, SimilarWeb, NewsAPI, Claude)
2. User credentials (dave's password, JWT secret)
3. Trend data (proprietary scoring algorithm results)
4. System availability (prevent DoS)

**Threat Actors:**
1. External attackers (trying to steal API keys, access data)
2. Malicious users (if system expands beyond dave in Phase 2)

**Threats & Mitigations:**

| Threat | Mitigation |
|--------|-----------|
| **API key exposure** | • Store in environment variables<br>• Never commit to git (.gitignore)<br>• Never log keys<br>• Rotate keys if compromised |
| **Password compromise** | • Bcrypt hashing (salted)<br>• HTTPS only<br>• JWT expiration (7 days)<br>• No password reset in MVP (dave only) |
| **SQL injection** | • SQLAlchemy ORM (parameterized queries)<br>• Input validation via Pydantic models<br>• Principle of least privilege (db user permissions) |
| **XSS attacks** | • React escapes output by default<br>• Content Security Policy headers<br>• Sanitize user input (if Phase 2 adds user-generated content) |
| **CSRF attacks** | • JWT tokens in headers (not cookies)<br>• SameSite cookie attributes if using cookies in future |
| **DoS attacks** | • Rate limiting on backend endpoints (10 req/min per IP)<br>• Railway platform DDoS protection<br>• Cloudflare in Phase 2 if needed |
| **Man-in-the-middle** | • HTTPS enforced<br>• HSTS headers<br>• Certificate pinning (Phase 2) |

### Security Headers

```python
# FastAPI middleware
from fastapi.middleware.cors import CORSMiddleware
from fastapi.middleware.httpsredirect import HTTPSRedirectMiddleware

app.add_middleware(HTTPSRedirectMiddleware)

app.add_middleware(
    CORSMiddleware,
    allow_origins=[os.getenv("FRONTEND_URL")],  # Specific origin, not "*"
    allow_credentials=True,
    allow_methods=["GET", "POST"],
    allow_headers=["Authorization", "Content-Type"],
)

# Security headers
@app.middleware("http")
async def add_security_headers(request, call_next):
    response = await call_next(request)
    response.headers["X-Content-Type-Options"] = "nosniff"
    response.headers["X-Frame-Options"] = "DENY"
    response.headers["X-XSS-Protection"] = "1; mode=block"
    response.headers["Strict-Transport-Security"] = "max-age=31536000; includeSubDomains"
    response.headers["Content-Security-Policy"] = "default-src 'self'; script-src 'self' 'unsafe-inline'; style-src 'self' 'unsafe-inline';"
    return response
```

### Secrets Management

**MVP Approach:**
- Store secrets in Railway environment variables
- Load via `os.getenv()` in application code
- Never commit `.env` files to git

**Environment Variables:**
```bash
# Database
DATABASE_URL=postgresql://user:pass@host:port/dbname

# Authentication
JWT_SECRET_KEY=<random 256-bit key>
INITIAL_PASSWORD=<dave's initial password hash>

# API Keys
REDDIT_CLIENT_ID=<reddit app client id>
REDDIT_CLIENT_SECRET=<reddit app secret>
YOUTUBE_API_KEY=<google cloud api key>
SIMILARWEB_API_KEY=<similarweb api key>
NEWSAPI_KEY=<newsapi.org key>
ANTHROPIC_API_KEY=<claude api key>

# Frontend
FRONTEND_URL=https://trend-monitor.railway.app
```

**Phase 2 Upgrade:**
- Migrate to AWS Secrets Manager or HashiCorp Vault
- Implement key rotation
- Add audit logging for secret access

---

## Testing Strategy

### MVP Testing Approach

**Philosophy:** Pragmatic testing for MVP - focus on critical paths, expand in Phase 2.

**Test Pyramid:**
```
        ┌──────────────────────────────┐
        │  E2E Tests (Few)            │  Manual testing for MVP
        │  • Login flow                │
        │  • Data collection → dashboard│
        └──────────────────────────────┘
                    △
        ┌────────────────────────────────────┐
        │  Integration Tests (Some)          │  API integration tests
        │  • API collectors                   │
        │  • Database operations              │
        │  • Score calculation with real data │
        └────────────────────────────────────┘
                    △
        ┌────────────────────────────────────────────┐
        │  Unit Tests (Many)                         │
        │  • Scoring algorithm functions             │
        │  • Normalization functions                 │
        │  • Error handling                          │
        │  • JWT token generation/validation         │
        └────────────────────────────────────────────┘
```

**Priority Tests for MVP:**

1. **Scoring Algorithm (High Priority):**
```python
# tests/test_scoring.py
import pytest
from scoring.normalizer import (
    normalize_reddit_score,
    normalize_youtube_traction,
    calculate_momentum_score
)

def test_normalize_reddit_score():
    # Test with typical values
    score = normalize_reddit_score(
        score=5000,
        hours_since_post=2.0,
        subreddit_size=1000000
    )
    assert 0 <= score <= 100
    assert score > 50  # Should be high for viral post

def test_normalize_reddit_score_edge_cases():
    # Zero hours (just posted)
    score = normalize_reddit_score(score=100, hours_since_post=0.1, subreddit_size=10000)
    assert score > 0

    # Very old post
    score = normalize_reddit_score(score=100, hours_since_post=1000, subreddit_size=10000)
    assert score < 1  # Should decay

def test_momentum_score_all_signals():
    score, confidence = calculate_momentum_score(
        reddit_velocity=80,
        youtube_traction=75,
        google_trends_spike=85,
        similarweb_traffic_spike=True
    )
    assert confidence == 'high'  # All 4 signals present
    assert score > 100  # SimilarWeb bonus applied

def test_momentum_score_missing_data():
    score, confidence = calculate_momentum_score(
        reddit_velocity=80,
        youtube_traction=None,  # Missing YouTube data
        google_trends_spike=75,
        similarweb_traffic_spike=False
    )
    assert confidence == 'medium'  # Only 2 signals
    assert 0 <= score <= 100
```

2. **API Collector Integration Tests:**
```python
# tests/test_collectors.py
import pytest
from collectors.reddit import RedditCollector

@pytest.mark.asyncio
async def test_reddit_collector_real_api():
    """Test with real Reddit API (requires credentials)"""
    collector = RedditCollector(
        client_id=os.getenv("REDDIT_CLIENT_ID"),
        client_secret=os.getenv("REDDIT_CLIENT_SECRET")
    )

    result = await collector.collect(["python", "programming"])

    assert result.source == "reddit"
    assert len(result.data) == 2
    assert result.success_rate > 0.5  # At least 50% success

@pytest.mark.asyncio
async def test_reddit_collector_handles_rate_limit():
    """Test rate limiting behavior"""
    collector = RedditCollector(...)

    # Make 100 requests rapidly
    tasks = [collector.collect(["test"]) for _ in range(100)]
    results = await asyncio.gather(*tasks)

    # Should complete without errors (rate limiter prevents exceeding limit)
    assert all(r.success_rate > 0 for r in results)
```

3. **Error Handling Tests:**
```python
# tests/test_error_handling.py
import pytest
from collectors.reddit import RedditCollector, RedditAPIError

@pytest.mark.asyncio
async def test_collector_graceful_degradation():
    """Test that collector handles API failures gracefully"""
    collector = RedditCollector(...)

    # Mock Reddit API to fail
    with mock.patch.object(collector, '_fetch_reddit_data', side_effect=RedditAPIError("API down")):
        result = await collector.collect(["test"])

        # Should return result with None data, not crash
        assert result.data == [None]
        assert result.success_rate == 0.0

def test_momentum_score_with_all_missing_data():
    """Test score calculation when all APIs fail"""
    score, confidence = calculate_momentum_score_safe(
        reddit_velocity=None,
        youtube_traction=None,
        google_trends_spike=None,
        similarweb_traffic_spike=None
    )

    assert score == 0.0
    assert confidence == 'unknown'
```

**Manual Testing Checklist for MVP:**
- [ ] Login flow works
- [ ] "Collect Latest Trends" button triggers collection
- [ ] Collection completes in <30 minutes
- [ ] Dashboard displays Top 10 trends
- [ ] Confidence badges (🔥⚡👀) display correctly
- [ ] "Explain This Trend" generates AI brief
- [ ] Dashboard loads in <2 seconds
- [ ] Error messages display when APIs fail
- [ ] System works with 1-2 APIs unavailable

**Phase 2 Testing Expansion:**
- Add E2E tests with Playwright/Cypress
- Add performance tests (load testing)
- Add security scanning (OWASP ZAP)
- CI/CD runs tests on every commit

---

## Performance Optimization Strategy

### Performance Targets

| Metric | Target | Current Estimate | Optimization Strategy |
|--------|---------|------------------|----------------------|
| Dashboard load time | <2 seconds | 1-2 seconds | • Server-side rendering (Next.js)<br>• Database query optimization<br>• CDN for static assets |
| Data collection time | <30 minutes | 20-30 minutes | • Parallel API calls (asyncio)<br>• Aggressive caching<br>• Reduce monitored topics if needed |
| Momentum score calculation | <5 seconds | <1 second | • Pure function optimization<br>• Batch processing |
| AI brief generation | <3 seconds | 2-3 seconds | • Claude API latency dependent<br>• Cache generated briefs |

### Optimization Techniques

**1. Database Query Optimization:**
```sql
-- Efficient query for Top 10 trends
CREATE INDEX idx_momentum_confidence ON trends (momentum_score DESC, confidence_level);

SELECT
    id, title, confidence_level, momentum_score,
    reddit_score, youtube_views, google_trends_interest, similarweb_traffic_change,
    created_at
FROM trends
WHERE collection_id = (
    SELECT id FROM data_collections
    WHERE status = 'completed'
    ORDER BY completed_at DESC
    LIMIT 1
)
ORDER BY momentum_score DESC
LIMIT 10;
```

**2. API Response Caching:**
```python
# Cache channel/subreddit metadata (rarely changes)
from functools import lru_cache
from cachetools import TTLCache

# In-memory cache with 1-hour TTL
metadata_cache = TTLCache(maxsize=1000, ttl=3600)

@lru_cache(maxsize=100)
def get_subreddit_metadata(subreddit_name: str) -> dict:
    """Cache subreddit subscriber count"""
    if subreddit_name in metadata_cache:
        return metadata_cache[subreddit_name]

    metadata = fetch_from_reddit_api(subreddit_name)
    metadata_cache[subreddit_name] = metadata
    return metadata
```

**3. Lazy AI Brief Generation:**
```python
# Generate AI briefs on-demand, not during collection
@app.get("/trends/{trend_id}")
async def get_trend_detail(trend_id: str):
    trend = await db.get_trend(trend_id)

    # Check if AI brief already generated
    if not trend.ai_brief:
        # Generate on first access
        brief = await generate_ai_brief(trend)
        await db.update_trend(trend_id, ai_brief=brief)
        trend.ai_brief = brief

    return trend
```

**4. Frontend Performance:**
```typescript
// Next.js Server-Side Rendering
export async function getServerSideProps() {
  const trends = await fetch(`${BACKEND_URL}/trends`).then(r => r.json());

  return {
    props: { trends }  // Pre-rendered on server
  };
}

// React.memo for expensive components
export const TrendCard = React.memo<TrendCardProps>(({ trend }) => {
  // Only re-renders if trend data changes
  return <div>...</div>;
});

// Virtualization for long lists (Phase 2)
import { FixedSizeList } from 'react-window';
```

**Monitoring Performance:**
```python
# Track slow operations
import time
from functools import wraps

def track_performance(operation_name: str):
    def decorator(func):
        @wraps(func)
        async def wrapper(*args, **kwargs):
            start = time.time()
            result = await func(*args, **kwargs)
            duration_ms = (time.time() - start) * 1000

            logger.info(f"Performance: {operation_name} took {duration_ms:.2f}ms")

            if duration_ms > 5000:  # Warn if >5 seconds
                logger.warning(f"Slow operation: {operation_name} took {duration_ms:.2f}ms")

            return result
        return wrapper
    return decorator

@track_performance("reddit_collection")
async def collect_reddit_data(topics: List[str]):
    # ...
```

---

## Migration and Deployment Plan

### Initial Deployment (MVP Launch)

**Prerequisites:**
1. Railway account created
2. GitHub repository set up
3. Environment variables configured in Railway
4. Database initialized with schema

**Step-by-Step Deployment:**

1. **Database Setup:**
```bash
# Run database migrations locally first (test)
alembic upgrade head

# Railway automatically creates PostgreSQL database
# Apply migrations via Railway CLI or startup script
railway run alembic upgrade head
```

2. **Backend Deployment:**
```bash
# Railway auto-detects Python app
# railway.json configuration:
{
  "build": {
    "builder": "NIXPACKS",
    "buildCommand": "pip install -r requirements.txt"
  },
  "deploy": {
    "startCommand": "uvicorn main:app --host 0.0.0.0 --port $PORT",
    "healthcheckPath": "/health",
    "restartPolicyType": "ON_FAILURE"
  }
}

# Push to GitHub main branch
git push origin main

# Railway auto-deploys
```

3. **Frontend Deployment:**
```bash
# Option A: Deploy to Railway
railway up

# Option B: Deploy to Vercel (free tier)
vercel deploy --prod
```

4. **Verification:**
```bash
# Check health endpoint
curl https://trend-monitor-backend.railway.app/health

# Test login
curl -X POST https://trend-monitor-backend.railway.app/auth/login \
  -H "Content-Type: application/json" \
  -d '{"username":"dave","password":"..."}'

# Test data collection
curl -X POST https://trend-monitor-backend.railway.app/collect \
  -H "Authorization: Bearer <token>"
```

### Phase 2 Migration Plan

**When scaling beyond MVP:**

1. **Multi-User Support:**
   - Add user registration endpoint
   - Migrate from hardcoded user to database users table
   - Add email verification (optional)

2. **Automated Scheduling:**
   - Add APScheduler or Celery for twice-weekly auto-collection
   - Configure cron jobs in Railway

3. **Enhanced Monitoring:**
   - Add Sentry for error tracking
   - Add DataDog or New Relic for APM
   - Create operations dashboard

4. **Sprout Social Integration:**
   - Add new collector module (SproutSocialCollector)
   - Update momentum score algorithm to include Twitter/X data
   - No architectural changes required (modular design)

5. **Scaling Infrastructure:**
   - Evaluate Railway performance under load
   - Consider migration to AWS/GCP if >100 users
   - Add Redis for caching if needed
   - Implement CDN (Cloudflare) for frontend assets

---

## Risks and Open Questions

### Technical Risks

| Risk | Severity | Mitigation | Status |
|------|----------|------------|--------|
| **PyTrends reliability** | HIGH | Apply for official Google Trends API alpha; build scraping fallback | Mitigated |
| **YouTube quota exceeded** | MEDIUM | Use video list endpoint (1 unit) vs search (100 units); aggressive caching | Mitigated |
| **NewsAPI production cost** | LOW | Budget $449/month; evaluate alternatives (NewsData.io) | Accepted |
| **Scoring algorithm accuracy** | HIGH | Track hit rates, iterate based on real data, allow manual tuning | Requires validation |
| **Data collection >30min** | MEDIUM | Parallel API calls (asyncio), reduce topics if needed | Mitigated |
| **Railway scaling limits** | LOW | Monitor performance, migrate to AWS/GCP if needed in Phase 2 | Accepted for MVP |

### Open Questions

1. **Which subreddits to monitor?**
   - **Decision needed:** Define default list of 10-20 subreddits relevant to dave's content
   - **Recommendation:** Start with r/all, r/popular, r/videos, r/movies, r/television, r/music, r/news, r/technology, r/gaming, r/sports
   - **Tuning:** Adjust based on dave's actual content focus areas

2. **How to define "topics" for monitoring?**
   - **Option A:** Monitor trending posts/videos globally, extract topics dynamically
   - **Option B:** Define fixed list of 50 topics/keywords to track
   - **Recommendation:** Option A for MVP (more discovery-oriented)

3. **How often to run data collection after MVP?**
   - **MVP:** Manual trigger (twice weekly before meetings)
   - **Phase 2:** Automated scheduling (e.g., Sunday 6pm, Wednesday 6pm)
   - **Future:** Daily collection with historical trending

4. **Should AI briefs be generated during collection or on-demand?**
   - **Decision:** On-demand (lazy generation) to reduce collection time and Claude API costs
   - **Trade-off:** First-time clicks take 2-3 seconds; subsequent clicks instant (cached)

5. **How to handle time zones?**
   - **MVP:** All timestamps stored in UTC in database
   - **Frontend:** Display in user's local time zone (browser time zone)
   - **Phase 2:** User preference for time zone

---

## Conclusion

This architecture document captures the key decisions for building the trend-monitor MVP. The architecture prioritizes:

1. **Simplicity** - Three-tier architecture, modular design, clear separation of concerns
2. **Resilience** - Graceful degradation, retry logic, comprehensive error handling
3. **Cost Efficiency** - Free tier APIs, Railway hosting (~$20/month), pay-per-use Claude API
4. **Maintainability** - Pure functions, typed code (Python type hints, TypeScript), clear interfaces
5. **Scalability** - Database-backed, modular collectors, easy to add new sources in Phase 2

**Next Steps:**
1. ✅ Architecture document complete
2. **Next:** Create Epics & Stories (break down into implementation tasks)
3. **Then:** Implementation Readiness Check
4. **Then:** Sprint Planning → Development begins

**Estimated MVP Development:** 2-3 weeks from start to deployed system

---

**Document Status:** COMPLETE
**Last Updated:** 2026-01-05
**Author:** dave
**Reviewers:** TBD