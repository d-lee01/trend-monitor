---
stepsCompleted: [1, 2, 3]
inputDocuments:
  - '_bmad-output/planning-artifacts/prd.md'
  - '_bmad-output/planning-artifacts/architecture.md'
---

# trend-monitor - Epic Breakdown

## Overview

This document provides the complete epic and story breakdown for trend-monitor, decomposing the requirements from the PRD and Architecture into implementable stories.

## Requirements Inventory

### Functional Requirements

**FR-1: Cross-Platform Data Collection (4 Sources)**

- **FR-1.1: Reddit API Integration**
  - System SHALL authenticate with Reddit API using OAuth 2.0
  - System SHALL collect: post score, comment count, upvote ratio, post age, subreddit subscriber count, crosspost count
  - System SHALL monitor trending posts from configurable subreddits (default: 10 subreddits)
  - System SHALL handle Reddit rate limits (60 req/min authenticated)
  - System SHALL retry failed requests with exponential backoff

- **FR-1.2: YouTube Data API Integration**
  - System SHALL authenticate with YouTube Data API v3
  - System SHALL collect: view count, like count, comment count, channel subscriber count, publication date, video title/description
  - System SHALL monitor trending videos from configurable channels (default: 20 channels)
  - System SHALL stay within 10,000 units/day quota by using video list endpoint (1 unit) instead of search (100 units)
  - System SHALL implement caching to reduce API calls by 50-80%

- **FR-1.3: Google Trends Integration**
  - System SHALL use PyTrends library for Google Trends data
  - System SHALL collect Interest Over Time data (0-100 scale)
  - System SHALL detect search interest spikes
  - System SHALL monitor configurable keywords/topics (default: 50 topics)
  - System SHALL handle rate limiting with 60-second delays between requests
  - System SHALL gracefully handle PyTrends failures and log errors

- **FR-1.4: SimilarWeb API Integration**
  - System SHALL authenticate with existing SimilarWeb subscription
  - System SHALL collect: total traffic, traffic sources breakdown, engagement metrics, geographic distribution
  - System SHALL detect traffic spikes indicating mainstream pickup

- **FR-1.5: Automated Scheduling**
  - System SHALL automatically trigger data collection at 7:30 AM daily
  - System SHALL use APScheduler (Python) for scheduled jobs
  - System SHALL log all scheduled collection runs
  - Manual "Collect Latest Trends" button SHALL remain available for on-demand collection
  - System SHALL handle timezone configuration (7:30 AM in user's local timezone)

**FR-2: Cross-Platform Momentum Score Calculation**

- **FR-2.1: Metric Normalization**
  - System SHALL normalize Reddit scores to 0-100 scale using log scaling
  - System SHALL normalize YouTube view counts to 0-100 scale using log scaling
  - System SHALL use Google Trends interest (already 0-100) directly
  - System SHALL normalize SimilarWeb traffic to 0-100 scale using log scaling
  - System SHALL make normalized scores comparable across platforms

- **FR-2.2: Velocity Calculation**
  - System SHALL calculate Reddit velocity as: `(score / hours_since_post) × log(subreddit_size)`
  - System SHALL calculate YouTube traction as: `(views / hours_since_publish) × (engagement_rate) × log(channel_subs)`
  - System SHALL calculate Google Trends spike as: `(current_interest - 7day_avg) / 7day_stddev`

- **FR-2.3: Composite Score**
  - System SHALL calculate Cross-Platform Momentum Score as: `(Reddit_Velocity × YouTube_Traction × Google_Trends_Spike) + SimilarWeb_Bonus`
  - System SHALL apply SimilarWeb Bonus (multiply by 1.5) if traffic spike detected
  - System SHALL calculate scores in <5 seconds per trend

- **FR-2.4: Confidence Level Assignment**
  - System SHALL assign 🔥 High Confidence if all 4 platform signals align (Reddit + YouTube + Google Trends + SimilarWeb)
  - System SHALL assign ⚡ Medium Confidence if 2-3 platform signals align
  - System SHALL assign 👀 Low Confidence if only 1 platform signal present
  - System SHALL store confidence level with each trend record

**FR-3: Trending Now Dashboard**

- **FR-3.1: Dashboard Display**
  - System SHALL display Top 10 trends ranked by Cross-Platform Momentum Score
  - System SHALL show for each trend: title, confidence score (🔥⚡👀), key metrics (Reddit score, YouTube views, Google Trends interest, SimilarWeb traffic), time detected, trend status
  - System SHALL load dashboard in <2 seconds
  - System SHALL update dashboard display in real-time when new data collected

- **FR-3.2: Manual Data Collection Trigger**
  - System SHALL provide "Collect Latest Trends" button
  - System SHALL display progress indicator during collection
  - System SHALL show completion status and timestamp of last collection
  - System SHALL complete collection in <30 minutes

- **FR-3.3: Trend Detail View**
  - System SHALL allow users to click on any trend to see detailed view
  - System SHALL display breakdown of metrics across all platforms
  - System SHALL show Cross-Platform Momentum Score calculation components
  - System SHALL display trend trajectory chart (if historical data available)

**FR-4: AI-Powered Trend Brief**

- **FR-4.1: Brief Generation**
  - System SHALL provide "Explain This Trend" button for each trend
  - System SHALL call Claude API to generate 3-sentence summary
  - System SHALL include in prompt: trend topic, platform metrics, why it's trending, where it's big
  - System SHALL display brief in <3 seconds

- **FR-4.2: Brief Content Structure**
  - System SHALL generate summary with structure: Sentence 1 (What is it?), Sentence 2 (Why is it trending?), Sentence 3 (Where is it big?)
  - System SHALL keep summaries concise (3 sentences maximum)

**FR-5: Data Storage**

- **FR-5.1: Database Schema**
  - System SHALL use PostgreSQL database
  - System SHALL store trend records with: trend ID, title, collection timestamp, platform-specific metrics (Reddit, YouTube, Google Trends, SimilarWeb), normalized scores per platform, Cross-Platform Momentum Score, confidence level, AI-generated brief
  - System SHALL support future multi-user expansion through schema design

- **FR-5.2: Data Persistence**
  - System SHALL persist all collected data between runs
  - System SHALL maintain historical trend data for future analytics
  - System SHALL prevent data loss through database backups

**FR-6: Authentication & Access Control**

- **FR-6.1: Single-User Access (MVP)**
  - System SHALL require login with username/password
  - System SHALL support single user (dave) only in MVP
  - System SHALL maintain session for 7 days
  - System SHALL log out user after 30 days of inactivity

- **FR-6.2: API Key Management**
  - System SHALL securely store API keys for all integrated services (Reddit, YouTube, Google Trends, SimilarWeb, Claude API)
  - System SHALL use environment variables or secure key management service
  - System SHALL never expose API keys in client-side code or logs

### Non-Functional Requirements

**NFR-1: Performance**
- NFR-1.1: Dashboard SHALL load in <2 seconds on standard broadband connection (10 Mbps+)
- NFR-1.2: Data collection SHALL complete in <30 minutes for all 4 APIs and ~50 trending topics
- NFR-1.3: Cross-Platform Momentum Score calculation SHALL complete in <5 seconds per trend
- NFR-1.4: AI brief generation SHALL complete in <3 seconds per trend
- NFR-1.5: Database queries SHALL return results in <500ms for dashboard views

**NFR-2: Reliability**
- NFR-2.1: System SHALL achieve 95%+ uptime (allowing ~36 hours downtime per month)
- NFR-2.2: System SHALL handle API failures gracefully with retry logic and exponential backoff
- NFR-2.3: System SHALL return valid data 95%+ of the time (excluding external API failures)
- NFR-2.4: System SHALL not lose collected data between runs (database persistence)

**NFR-3: Scalability**
- NFR-3.1: System SHOULD support monitoring 100+ trending topics without performance degradation
- NFR-3.2: System SHOULD support future multi-user expansion (3-5 users initially, 100+ eventually)
- NFR-3.3: Database schema SHOULD allow adding new data sources (e.g., Twitter via Sprout Social in Phase 2)

**NFR-4: Security**
- NFR-4.1: System SHALL encrypt API keys at rest
- NFR-4.2: System SHALL use HTTPS for all client-server communication
- NFR-4.3: System SHALL not log sensitive information (API keys, passwords)
- NFR-4.4: System SHALL implement secure password hashing (bcrypt/Argon2)
- NFR-4.5: System SHALL protect against common web vulnerabilities (XSS, CSRF, SQL injection)

**NFR-5: Maintainability**
- NFR-5.1: Code SHALL follow Python PEP 8 style guidelines for backend
- NFR-5.2: Code SHALL follow React/TypeScript best practices for frontend
- NFR-5.3: System SHALL include logging for debugging and monitoring
- NFR-5.4: API integration patterns SHALL be modular and allow easy addition of new sources

**NFR-6: Cost Efficiency**
- NFR-6.1: System SHALL stay within free tier limits for Reddit API (60 req/min)
- NFR-6.2: System SHALL stay within free tier limits for YouTube API (10K units/day)
- NFR-6.3: Total monthly cost SHALL not exceed $50 for MVP ($0 for APIs + ~$20-25 infrastructure)

**NFR-7: Usability**
- NFR-7.1: Dashboard SHALL be intuitive for non-technical users
- NFR-7.2: Visual indicators (🔥⚡👀) SHALL be immediately understandable
- NFR-7.3: System SHALL provide clear error messages when data collection fails
- NFR-7.4: System SHALL work on standard web browsers (Chrome, Firefox, Safari, Edge)

### Additional Requirements

**Technical Architecture Requirements (from Architecture Document):**

**Infrastructure & Deployment:**
- Deploy to Railway platform with managed PostgreSQL
- Backend: Python 3.10+ with FastAPI framework
- Frontend: Next.js with TypeScript and TailwindCSS
- Target cost: ~$20-25/month for MVP

**Architectural Patterns:**
- Three-tier architecture (Presentation → Application → Data)
- Batch-oriented data processing (twice-weekly manual trigger)
- Modular API integration with standardized DataCollector interface pattern
- Pure function scoring algorithms (testable, auditable, deterministic)
- JWT authentication with bcrypt password hashing
- Graceful degradation when individual APIs fail

**API Integration Requirements:**
- Async/await parallel API collection using Python asyncio
- Rate limiters per API (Reddit 60 req/min, YouTube quota tracking with alerts)
- Retry logic with exponential backoff (3 attempts) for all APIs
- Health check methods for each API collector
- Structured logging with JSON format for API calls

**Database Requirements:**
- PostgreSQL 14+ with managed hosting (Railway)
- Tables: trends, data_collections, users, api_quota_usage
- Indexes on: momentum_score DESC, confidence_level, created_at DESC
- JSONB columns for flexible API response metadata
- Database migrations managed with Alembic

**Security Requirements:**
- HTTPS enforced with HSTS headers
- Security headers: X-Content-Type-Options, X-Frame-Options, X-XSS-Protection, CSP
- CORS configured for frontend origin only
- JWT tokens with 7-day expiration
- Environment variables for all secrets (Railway management)

**Observability Requirements:**
- Structured JSON logging for all API calls (api_name, success, duration_ms, quota_used)
- Quota tracking and alerting when approaching limits (80% threshold)
- Collection metrics: duration, trends found, API failures
- Basic health endpoint for uptime monitoring (UptimeRobot)

**Greenfield Setup Requirements:**
- No existing starter template - full stack setup from scratch
- GitHub repository with Railway auto-deploy on push to main
- Environment variable configuration in Railway dashboard
- Initial database schema setup with Alembic migrations
- Single-user bootstrap with hardcoded credentials (dave)

### FR Coverage Map

**Epic 1: Foundation & Authentication**
- FR-5.1: Database Schema (PostgreSQL with all required tables)
- FR-6.1: Single-User Access (login, session management)
- FR-6.2: API Key Management (secure environment variable storage)

**Epic 2: Multi-Source Data Collection Pipeline**
- FR-1.1: Reddit API Integration
- FR-1.2: YouTube Data API Integration
- FR-1.3: Google Trends Integration
- FR-1.4: SimilarWeb API Integration
- FR-1.5: Automated Scheduling (daily 7:30 AM + manual trigger)
- FR-5.2: Data Persistence

**Epic 3: Trend Analysis & Dashboard**
- FR-2.1: Metric Normalization (all platforms to 0-100 scale)
- FR-2.2: Velocity Calculation (Reddit, YouTube, Google Trends formulas)
- FR-2.3: Composite Score (Cross-Platform Momentum Score)
- FR-2.4: Confidence Level Assignment (🔥⚡👀)
- FR-3.1: Dashboard Display (Top 10 trends, <2sec load)
- FR-3.2: Manual Data Collection Trigger (button + progress)
- FR-3.3: Trend Detail View (expanded breakdown)

**Epic 4: AI-Powered Insights**
- FR-4.1: Brief Generation (Claude API integration)
- FR-4.2: Brief Content Structure (3-sentence format)

**✅ All functional requirements mapped to epics - complete coverage**

## Epic List

### Epic 1: Foundation & Authentication

**Epic Goal:** Establish secure, deployed infrastructure with authentication, database, and foundational backend/frontend architecture.

**User Outcome:** dave can log into the trend-monitor dashboard securely with username/password, and the system is deployed on Railway with PostgreSQL database, FastAPI backend, and Next.js frontend operational.

**FRs Covered:** FR-5.1 (Database Schema), FR-6.1 (Single-User Access), FR-6.2 (API Key Management)

**Technical Implementation:**
- Deploy Railway project with managed PostgreSQL
- Setup FastAPI backend with JWT authentication
- Setup Next.js frontend with TypeScript and TailwindCSS
- Create database schema (trends, data_collections, users, api_quota_usage tables)
- Configure environment variables for API keys and secrets
- Implement login flow with 7-day session tokens

---

### Epic 2: Multi-Source Data Collection Pipeline

**Epic Goal:** Build robust data collection system that automatically gathers trend data from 4 platforms daily, with manual trigger option and graceful error handling.

**User Outcome:** dave can click "Collect Latest Trends" button OR rely on automatic 7:30 AM daily collection to gather data from Reddit, YouTube, Google Trends, and SimilarWeb. Collection completes in <30 minutes with retry logic, rate limiting, and graceful degradation when APIs fail. Raw collected data is stored in PostgreSQL.

**FRs Covered:** FR-1.1 (Reddit), FR-1.2 (YouTube), FR-1.3 (Google Trends), FR-1.4 (SimilarWeb), FR-1.5 (Automated Scheduling), FR-5.2 (Data Persistence)

**Technical Implementation:**
- Implement modular DataCollector interface pattern
- Build 4 API collectors (RedditCollector, YouTubeCollector, GoogleTrendsCollector, SimilarWebCollector)
- Implement async parallel collection with asyncio
- Add rate limiters (Reddit 60/min, YouTube quota tracking)
- Implement retry logic with exponential backoff
- Add APScheduler for daily 7:30 AM automated collection
- Create CollectionOrchestrator for parallel coordination
- Store raw collected data in trends table
- Implement quota tracking and alerting

---

### Epic 3: Trend Analysis & Dashboard

**Epic Goal:** Transform collected data into actionable trend insights with Cross-Platform Momentum Scores, confidence indicators, and interactive dashboard visualization.

**User Outcome:** dave can view Trending Now dashboard showing Top 10 trends ranked by Cross-Platform Momentum Score. Each trend displays confidence level (🔥 High, ⚡ Medium, 👀 Low), actual metrics (Reddit score, YouTube views, Google Trends interest, SimilarWeb traffic), and time detected. Dashboard loads in <2 seconds. dave can click any trend to see detailed platform breakdown and scoring calculation components.

**FRs Covered:** FR-2.1 (Normalization), FR-2.2 (Velocity Calculation), FR-2.3 (Composite Score), FR-2.4 (Confidence Assignment), FR-3.1 (Dashboard Display), FR-3.2 (Manual Collection Trigger), FR-3.3 (Trend Detail View)

**Technical Implementation:**
- Implement pure function scoring algorithms (normalize_reddit_score, normalize_youtube_traction, calculate_google_trends_spike)
- Build calculate_momentum_score() with signal convergence logic
- Create confidence level assignment (4 signals = 🔥, 2-3 signals = ⚡, 1 signal = 👀)
- Build Next.js dashboard pages (index.tsx for Trending Now, trend/[id].tsx for details)
- Create React components (TrendCard, TrendList, ConfidenceBadge, DataCollectionButton)
- Implement server-side rendering for <2sec load time
- Build FastAPI endpoints (GET /trends, POST /collect)
- Optimize database queries with indexes

---

### Epic 4: AI-Powered Insights

**Epic Goal:** Enhance trend understanding with instant AI-generated explanations for any trend.

**User Outcome:** dave can click "Explain This Trend" button on any trend to receive a 3-sentence AI-generated summary in <3 seconds explaining what the trend is, why it's trending, and where it's big. AI briefs are cached for instant subsequent views.

**FRs Covered:** FR-4.1 (Brief Generation), FR-4.2 (Brief Content Structure)

**Technical Implementation:**
- Integrate Claude API (Anthropic)
- Build POST /trends/{id}/explain endpoint
- Implement prompt engineering for 3-sentence structure (What/Why/Where)
- Add lazy generation (on-demand, not during collection)
- Cache generated briefs in trends.ai_brief column
- Display briefs inline in frontend with loading states

---

## Epic 1: Foundation & Authentication

**Epic Goal:** Establish secure, deployed infrastructure with authentication, database, and foundational backend/frontend architecture.

**User Outcome:** dave can log into the trend-monitor dashboard securely with username/password, and the system is deployed on Railway with PostgreSQL database, FastAPI backend, and Next.js frontend operational.

### Story 1.1: Project Setup & Railway Deployment

As a **system administrator**,
I want **the trend-monitor application deployed to Railway with managed PostgreSQL and environment variable configuration**,
So that **the foundational infrastructure is operational and accessible via HTTPS**.

**Acceptance Criteria:**

**Given** Railway account is configured
**When** code is pushed to GitHub main branch
**Then** Railway automatically deploys FastAPI backend service
**And** Railway provisions managed PostgreSQL database
**And** Environment variables are configured (DATABASE_URL, JWT_SECRET_KEY, REDDIT_CLIENT_ID, REDDIT_CLIENT_SECRET, YOUTUBE_API_KEY, SIMILARWEB_API_KEY, ANTHROPIC_API_KEY)
**And** Backend health endpoint `/health` returns 200 OK
**And** HTTPS is enforced with security headers (HSTS, CSP, X-Frame-Options, X-Content-Type-Options, X-XSS-Protection)
**And** CORS is configured for frontend origin only

### Story 1.2: Database Schema Creation

As a **system**,
I want **PostgreSQL database tables created with proper indexes and relationships**,
So that **trend data, collections, users, and quota tracking can be persisted**.

**Acceptance Criteria:**

**Given** Railway PostgreSQL database is provisioned
**When** Alembic migrations are executed
**Then** `trends` table is created with columns: id (UUID PRIMARY KEY), title (VARCHAR 500), collection_id (UUID FK), created_at (TIMESTAMP), reddit_score (INTEGER), reddit_comments (INTEGER), reddit_upvote_ratio (FLOAT), reddit_subreddit (VARCHAR 100), youtube_views (INTEGER), youtube_likes (INTEGER), youtube_channel (VARCHAR 200), google_trends_interest (INTEGER), google_trends_related_queries (JSONB), similarweb_traffic (INTEGER), similarweb_sources (JSONB), reddit_velocity_score (FLOAT), youtube_traction_score (FLOAT), google_trends_spike_score (FLOAT), similarweb_bonus_applied (BOOLEAN), momentum_score (FLOAT), confidence_level (VARCHAR 10), ai_brief (TEXT), ai_brief_generated_at (TIMESTAMP)
**And** `data_collections` table is created with: id (UUID PRIMARY KEY), started_at (TIMESTAMP), completed_at (TIMESTAMP), status (VARCHAR 20), errors (JSONB), reddit_api_calls (INTEGER), youtube_api_quota_used (INTEGER), google_trends_api_calls (INTEGER)
**And** `users` table is created with: id (UUID PRIMARY KEY), username (VARCHAR 100 UNIQUE), password_hash (VARCHAR 255), created_at (TIMESTAMP), last_login (TIMESTAMP)
**And** `api_quota_usage` table is created with: id (SERIAL PRIMARY KEY), api_name (VARCHAR 50), date (DATE), units_used (INTEGER), UNIQUE(api_name, date)
**And** Indexes are created on: trends.momentum_score DESC, trends.confidence_level, trends.created_at DESC, data_collections.started_at DESC
**And** Foreign key relationship created: trends.collection_id → data_collections.id
**And** Check constraint on trends.confidence_level IN ('high', 'medium', 'low')
**And** Check constraint on data_collections.status IN ('in_progress', 'completed', 'failed')

### Story 1.3: Backend Authentication with JWT

As **dave (content planning lead)**,
I want **to log into the system with username/password and receive a JWT token**,
So that **I can access protected API endpoints securely for 7 days**.

**Acceptance Criteria:**

**Given** backend is deployed and database is initialized
**When** I send POST /auth/login with credentials {"username": "dave", "password": "<password>"}
**Then** system verifies password using bcrypt hashing
**And** system generates JWT token with 7-day expiration using HS256 algorithm
**And** system returns {"access_token": "<jwt>", "token_type": "bearer"}
**And** I can access GET /auth/me with Authorization header "Bearer <jwt>"
**And** system decodes JWT and returns my user profile: {"username": "dave", "user_id": "<id>"}
**And** expired tokens (>7 days) return 401 Unauthorized with message "Token expired"
**And** invalid tokens return 401 Unauthorized with message "Invalid token"
**And** missing Authorization header returns 401 Unauthorized with message "Not authenticated"
**And** JWT secret key is stored in JWT_SECRET_KEY environment variable (never in code)
**And** passwords are hashed with bcrypt using at least 12 rounds

### Story 1.4: Frontend Setup with Login UI

As **dave (content planning lead)**,
I want **a Next.js web application with a login page**,
So that **I can authenticate and access the dashboard**.

**Acceptance Criteria:**

**Given** Next.js frontend is deployed (Railway or Vercel)
**When** I navigate to the root URL
**Then** I see a login page with username field, password field (type=password), and "Login" button
**And** I enter valid credentials and click "Login"
**And** frontend sends POST /auth/login to backend API
**And** frontend receives JWT token and stores it in localStorage as "auth_token"
**And** frontend redirects to /dashboard
**And** unauthorized access to /dashboard redirects to login page with message "Please log in"
**And** dashboard page includes "Logout" button in top-right corner
**And** clicking "Logout" clears localStorage token and redirects to login page
**And** invalid credentials show error message: "Invalid username or password"
**And** page loads in <2 seconds
**And** page uses TailwindCSS for styling
**And** page is responsive (works on desktop browsers: Chrome, Firefox, Safari, Edge)

---

## Epic 2: Multi-Source Data Collection Pipeline

**Epic Goal:** Build robust data collection system that automatically gathers trend data from 4 platforms daily, with manual trigger option and graceful error handling.

**User Outcome:** dave can click "Collect Latest Trends" button OR rely on automatic 7:30 AM daily collection to gather data from Reddit, YouTube, Google Trends, and SimilarWeb. Collection completes in <30 minutes with retry logic, rate limiting, and graceful degradation when APIs fail. Raw collected data is stored in PostgreSQL.

### Story 2.1: API Collector Infrastructure

As a **developer**,
I want **a modular DataCollector interface pattern with async/parallel orchestration**,
So that **I can easily add multiple API collectors that run in parallel with retry logic and graceful degradation**.

**Acceptance Criteria:**

**Given** backend FastAPI is operational
**When** I create the base collector infrastructure
**Then** DataCollector abstract base class exists with methods: collect(topics: List[str]) -> CollectionResult, health_check() -> bool, get_rate_limit_info() -> RateLimitInfo
**And** CollectionOrchestrator class exists with method: collect_all(topics: List[str]) -> Dict[str, CollectionResult]
**And** CollectionOrchestrator uses asyncio.gather() to run all collectors in parallel
**And** RateLimiter classes exist: RequestsPerMinuteRateLimiter(limit: int, window: int), DailyQuotaRateLimiter(limit: int)
**And** retry_with_backoff() decorator exists with exponential backoff: 2s, 4s, 8s (max 3 attempts)
**And** CollectionResult dataclass exists with fields: source (str), data (List[Optional[Dict]]), success_rate (float)
**And** Failed API calls return None in data list instead of crashing (graceful degradation)
**And** All async functions use proper exception handling with try/except blocks
**And** Structured JSON logging implemented for all API calls: {"event": "api_call", "api": "reddit", "success": true, "duration_ms": 234.5}

### Story 2.2: Reddit Data Collection

As **dave (content planning lead)**,
I want **to collect trending posts from Reddit with rate limiting and retry logic**,
So that **Reddit trend data is gathered and stored in the database**.

**Acceptance Criteria:**

**Given** DataCollector infrastructure exists
**When** RedditCollector.collect() is called
**Then** system authenticates with Reddit API using OAuth 2.0 with credentials from environment variables (REDDIT_CLIENT_ID, REDDIT_CLIENT_SECRET)
**And** system uses praw library (Python Reddit API Wrapper)
**And** system monitors default 10 subreddits: r/all, r/popular, r/videos, r/movies, r/television, r/music, r/news, r/technology, r/gaming, r/sports
**And** system collects top 5 trending posts per subreddit
**And** system collects for each post: score, num_comments, upvote_ratio, created_utc, subreddit.subscribers, num_crossposts, title, permalink
**And** system calculates hours_since_post from created_utc
**And** system respects 60 requests/minute rate limit using RateLimiter
**And** system retries failed requests 3 times with exponential backoff (2s, 4s, 8s)
**And** system stores raw data in trends table columns: reddit_score, reddit_comments, reddit_upvote_ratio, reddit_subreddit, title
**And** system logs all API calls: {"event": "api_call", "api": "reddit", "topic": "r/all", "success": true, "duration_ms": 345}
**And** if Reddit API fails after 3 retries, collector returns None for that topic and continues with others

### Story 2.3: YouTube Data Collection

As **dave (content planning lead)**,
I want **to collect trending videos from YouTube with quota tracking and caching**,
So that **YouTube trend data is gathered without exceeding the 10,000 units/day free tier**.

**Acceptance Criteria:**

**Given** DataCollector infrastructure exists
**When** YouTubeCollector.collect() is called
**Then** system authenticates with YouTube Data API v3 using API key from YOUTUBE_API_KEY environment variable
**And** system uses google-api-python-client library
**And** system monitors default 20 trending channels
**And** system uses videos.list endpoint (1 unit/call) instead of search.list (100 units/call)
**And** system collects for each video: view_count, like_count, comment_count, published_at, channel_subscriber_count, video_title, video_id
**And** system calculates hours_since_publish from published_at
**And** system caches channel metadata (subscriber count) in-memory for 1 hour using TTLCache to reduce API calls
**And** system tracks quota usage by incrementing api_quota_usage table: INSERT INTO api_quota_usage (api_name, date, units_used) VALUES ('youtube', CURRENT_DATE, 1) ON CONFLICT (api_name, date) DO UPDATE SET units_used = units_used + 1
**And** system queries current daily quota: SELECT units_used FROM api_quota_usage WHERE api_name='youtube' AND date=CURRENT_DATE
**And** system logs warning when daily quota exceeds 8,000 units (80% threshold): "YouTube quota at 8,234/10,000 (82.3%)"
**And** system stores raw data in trends table: youtube_views, youtube_likes, youtube_channel, title
**And** system retries failed requests 3 times with exponential backoff
**And** if quota exceeded, collector skips remaining topics and logs error

### Story 2.4: Google Trends Data Collection

As **dave (content planning lead)**,
I want **to collect search interest data from Google Trends with spike detection**,
So that **Google search trend data is gathered and stored**.

**Acceptance Criteria:**

**Given** DataCollector infrastructure exists
**When** GoogleTrendsCollector.collect() is called
**Then** system uses PyTrends library (unofficial Google Trends API)
**And** system initializes: pytrend = TrendReq(hl='en-US', tz=360)
**And** system collects Interest Over Time data (0-100 scale) for default 50 topics
**And** system collects 7-day historical data using: pytrend.interest_over_time()
**And** system calculates current interest (most recent day value)
**And** system implements 60-second delay between requests using asyncio.sleep(60) to avoid rate limiting
**And** system gracefully handles PyTrends failures with try/except PyTrendsException
**And** if PyTrends fails, system logs error: {"event": "api_call", "api": "google_trends", "success": false, "error": "Rate limit exceeded"} and returns None
**And** system stores raw data in trends table: google_trends_interest, google_trends_related_queries (JSONB)
**And** system stores 7-day history for spike calculation in later epic
**And** system logs all API calls with success/failure status

### Story 2.5: SimilarWeb Data Collection

As **dave (content planning lead)**,
I want **to collect website traffic data from SimilarWeb to detect mainstream pickup**,
So that **traffic spike signals are included in momentum scoring**.

**Acceptance Criteria:**

**Given** DataCollector infrastructure exists and SIMILARWEB_API_KEY exists in environment
**When** SimilarWebCollector.collect() is called
**Then** system authenticates with SimilarWeb API using existing subscription key
**And** system uses requests library to call SimilarWeb API endpoints
**And** system collects for trending topics/websites: total_visits, traffic_sources, engagement_rate, geography
**And** system collects 7-day historical traffic data for spike comparison
**And** system calculates traffic_change_percentage: (current_traffic - 7day_avg) / 7day_avg * 100
**And** system sets similarweb_traffic_spike boolean flag True when traffic_change > 50%
**And** system stores raw data in trends table: similarweb_traffic, similarweb_sources (JSONB), similarweb_bonus_applied
**And** system retries failed requests 3 times with exponential backoff
**And** system logs all API calls with duration and success status
**And** if SimilarWeb API fails, collector returns None and continues with other APIs

### Story 2.6: Manual Data Collection Trigger

As **dave (content planning lead)**,
I want **to click "Collect Latest Trends" button and see collection progress**,
So that **I can manually trigger data collection before my content meetings**.

**Acceptance Criteria:**

**Given** all 4 API collectors are implemented (Reddit, YouTube, Google Trends, SimilarWeb)
**When** I send POST /collect request from frontend (with JWT authentication)
**Then** backend creates new record in data_collections table: INSERT INTO data_collections (id, started_at, status) VALUES (uuid_generate_v4(), NOW(), 'in_progress')
**And** CollectionOrchestrator.collect_all() runs all 4 collectors in parallel using asyncio.gather(*tasks, return_exceptions=True)
**And** system collects top 50 trending topics across all platforms
**And** collection completes in <30 minutes (target: 20-25 minutes with parallel execution)
**And** system stores collected data in trends table with collection_id foreign key
**And** system calculates API success rates: reddit_success_rate = successful_calls / total_calls
**And** system updates data_collections record: UPDATE data_collections SET status='completed', completed_at=NOW(), reddit_api_calls=X, youtube_api_quota_used=Y WHERE id=<collection_id>
**And** system returns JSON response: {"collection_id": "<uuid>", "trends_found": 47, "duration_minutes": 22.5, "api_success_rates": {"reddit": 0.98, "youtube": 1.0, "google_trends": 0.92, "similarweb": 1.0}}
**And** if any API fails completely, collection still completes with remaining APIs (graceful degradation)
**And** system logs detailed collection metrics: {"event": "collection_complete", "collection_id": "<uuid>", "duration_minutes": 22.5, "trends_found": 47, "api_failures": ["google_trends"]}
**And** if collection is already in progress, return 409 Conflict: "Collection already in progress"

### Story 2.7: Automated Daily Collection at 7:30 AM

As **dave (content planning lead)**,
I want **the system to automatically collect trend data at 7:30 AM every day**,
So that **fresh data is ready when I check the dashboard in the morning**.

**Acceptance Criteria:**

**Given** manual collection trigger (Story 2.6) works and APScheduler is installed
**When** FastAPI backend starts
**Then** APScheduler BackgroundScheduler is initialized and started
**And** scheduler adds daily job: scheduler.add_job(trigger_collection, 'cron', hour=7, minute=30, timezone='America/Los_Angeles')
**And** trigger_collection() function calls POST /collect internally (same logic as manual trigger)
**And** scheduled collection runs automatically at 7:30 AM daily in user's timezone
**And** system logs all scheduled collection runs: {"event": "scheduled_collection_start", "timestamp": "2026-01-06T07:30:00"}
**And** if scheduled collection fails, system retries once after 30 minutes
**And** manual "Collect Latest Trends" button remains available for on-demand collection anytime
**And** system prevents duplicate collections by checking: SELECT status FROM data_collections WHERE status='in_progress'
**And** if previous collection still in progress, scheduled job skips and logs: "Skipped scheduled collection - previous collection still in progress"
**And** Railway backend service is configured with "Always On" (keep-alive) to ensure scheduler runs 24/7
**And** system sends email/log alert if scheduled collection fails 2 days in a row

---

## Epic 3: Trend Analysis & Dashboard

**Epic Goal:** Transform collected data into actionable trend insights with Cross-Platform Momentum Scores, confidence indicators, and interactive dashboard visualization.

**User Outcome:** dave can view Trending Now dashboard showing Top 10 trends ranked by Cross-Platform Momentum Score. Each trend displays confidence level (🔥 High, ⚡ Medium, 👀 Low), actual metrics (Reddit score, YouTube views, Google Trends interest, SimilarWeb traffic), and time detected. Dashboard loads in <2 seconds. dave can click any trend to see detailed platform breakdown and scoring calculation components.

### Story 3.1: Scoring Algorithm Implementation

As a **developer**,
I want **pure function scoring algorithms for normalizing and calculating momentum scores**,
So that **trend data can be scored consistently and the algorithms can be tested and tuned**.

**Acceptance Criteria:**

**Given** trend data exists in database with raw platform metrics
**When** scoring functions are implemented in scoring/normalizer.py module
**Then** normalize_reddit_score(score: int, hours_since_post: float, subreddit_size: int) -> float function exists
**And** reddit normalization uses formula: velocity = score / max(hours_since_post, 1); authority_weight = log10(max(subreddit_size, 1)); raw_score = velocity * authority_weight; normalized = min(100, (raw_score / 10000) * 100)
**And** normalize_youtube_traction(views: int, hours_since_publish: float, likes: int, channel_subs: int) -> float function exists
**And** youtube normalization uses formula: velocity = views / max(hours_since_publish, 1); engagement_rate = likes / max(views, 1); authority_weight = log10(max(channel_subs, 1)); raw_score = velocity * engagement_rate * authority_weight; normalized = min(100, (raw_score / 50000) * 100)
**And** calculate_google_trends_spike(current_interest: int, seven_day_history: List[int]) -> float function exists
**And** google trends uses z-score formula: mean = statistics.mean(seven_day_history); stddev = statistics.stdev(seven_day_history); z_score = (current_interest - mean) / stddev; normalized = min(100, max(0, (z_score + 3) / 6 * 100))
**And** calculate_momentum_score(reddit_velocity: float, youtube_traction: float, google_trends_spike: float, similarweb_traffic_spike: bool) -> Tuple[float, str] function exists
**And** momentum score formula: base_score = (reddit_velocity * 0.33 + youtube_traction * 0.33 + google_trends_spike * 0.34); if similarweb_traffic_spike: base_score *= 1.5
**And** confidence logic: signals_present = count of [reddit_velocity > 50, youtube_traction > 50, google_trends_spike > 50, similarweb_traffic_spike]; if signals >= 4: 'high'; elif signals >= 2: 'medium'; else: 'low'
**And** all functions are pure (no side effects, deterministic output)
**And** functions handle missing data: calculate_momentum_score_safe() accepts Optional[float] for each platform and calculates with available data
**And** if all platforms missing, return (0.0, 'unknown')
**And** all functions include docstrings with formula explanations

### Story 3.2: Score Calculation Integration

As **dave (content planning lead)**,
I want **collected trend data to be automatically scored and ranked**,
So that **I can see which trends have the highest momentum**.

**Acceptance Criteria:**

**Given** scoring algorithms exist and data collection completes storing raw data
**When** POST /collect finishes storing trends
**Then** system automatically calls scoring functions for each trend
**And** system calculates reddit_velocity_score using normalize_reddit_score(reddit_score, hours_since_post, subreddit_subscribers)
**And** system calculates youtube_traction_score using normalize_youtube_traction(youtube_views, hours_since_publish, youtube_likes, channel_subscribers)
**And** system calculates google_trends_spike_score using calculate_google_trends_spike(google_trends_interest, seven_day_history)
**And** system calls calculate_momentum_score(reddit_velocity_score, youtube_traction_score, google_trends_spike_score, similarweb_bonus_applied)
**And** system updates trends table: UPDATE trends SET reddit_velocity_score=X, youtube_traction_score=Y, google_trends_spike_score=Z, momentum_score=M, confidence_level=C WHERE id=<trend_id>
**And** scoring completes in <5 seconds per trend
**And** system handles missing API data (e.g., if YouTube failed, scores using remaining 3 platforms with calculate_momentum_score_safe())
**And** system logs scoring completion: {"event": "scoring_complete", "trends_scored": 47, "duration_seconds": 3.2}
**And** trends with momentum_score > 0 are considered valid

### Story 3.3: Trends API Endpoints

As a **frontend developer**,
I want **backend API endpoints to retrieve ranked trends**,
So that **the dashboard can display Top 10 trends and trend details**.

**Acceptance Criteria:**

**Given** scored trends exist in database
**When** FastAPI endpoints are implemented
**Then** GET /trends endpoint exists requiring JWT authentication
**And** GET /trends returns Top 10 trends: SELECT id, title, confidence_level, momentum_score, reddit_score, youtube_views, google_trends_interest, similarweb_traffic, created_at FROM trends WHERE collection_id = (SELECT id FROM data_collections WHERE status='completed' ORDER BY completed_at DESC LIMIT 1) ORDER BY momentum_score DESC LIMIT 10
**And** response format: [{"id": "<uuid>", "title": "...", "confidence_level": "high", "momentum_score": 87.5, "reddit_score": 15234, "youtube_views": 2534000, "google_trends_interest": 87, "similarweb_traffic_change": 150.5, "created_at": "2026-01-06T07:45:00"}]
**And** GET /trends/{id} endpoint exists returning detailed trend data
**And** GET /trends/{id} returns: SELECT * FROM trends WHERE id=<id>
**And** GET /collections/latest endpoint exists returning: SELECT id, started_at, completed_at, status, (SELECT COUNT(*) FROM trends WHERE collection_id = data_collections.id) as trends_found FROM data_collections WHERE status='completed' ORDER BY completed_at DESC LIMIT 1
**And** all endpoints return 401 Unauthorized if JWT token missing or invalid
**And** database queries use indexes (idx_momentum_score, idx_created_at) for performance
**And** query response time <500ms measured with logging
**And** endpoints return 404 Not Found if trend ID doesn't exist

### Story 3.4: Dashboard UI - Trending Now List

As **dave (content planning lead)**,
I want **to see a dashboard displaying Top 10 trends with confidence scores and key metrics**,
So that **I can quickly identify high-priority trends for content planning**.

**Acceptance Criteria:**

**Given** backend GET /trends endpoint exists and returns scored trends
**When** I navigate to /dashboard after successful login
**Then** page displays "trend-monitor" logo/title in top-left
**And** page displays "Last Updated: 2h ago" timestamp (calculated from data_collections.completed_at)
**And** page displays "Collect Latest Trends" button in top-right corner
**And** page displays "Trending Now - Top 10" heading
**And** page shows 10 trend cards ranked by momentum score (highest first)
**And** each trend card displays: confidence badge (🔥 red/orange for 'high', ⚡ yellow/amber for 'medium', 👀 blue/gray for 'low'), trend title (truncated to 100 chars with "..."), metrics row: "Reddit: 15.2K | YouTube: 2.5M | Google Trends: 87 | SimilarWeb: +150%"
**And** numbers formatted: 15234 → "15.2K", 2534000 → "2.5M", percentages with + sign
**And** page loads in <2 seconds using Next.js getServerSideProps() for server-side rendering
**And** page fetches trends on server: const trends = await fetch(`${BACKEND_URL}/trends`, {headers: {Authorization: `Bearer ${token}`}})
**And** page uses TailwindCSS for styling with responsive grid
**And** page is responsive and works on Chrome, Firefox, Safari, Edge (desktop)
**And** each trend card is clickable (hover shows pointer cursor)
**And** clicking trend card navigates to /trend/{id}

### Story 3.5: Manual Collection Trigger UI

As **dave (content planning lead)**,
I want **to click "Collect Latest Trends" button and see collection progress**,
So that **I can trigger on-demand data collection before meetings**.

**Acceptance Criteria:**

**Given** dashboard page is displayed with "Collect Latest Trends" button
**When** I click "Collect Latest Trends" button
**Then** frontend sends POST /collect with Authorization: Bearer <jwt_token>
**And** button immediately shows loading state: text changes to "Collecting...", spinner icon appears, button is disabled (opacity 50%, cursor not-allowed)
**And** frontend polls GET /collections/latest every 10 seconds to check status
**And** if collection succeeds (status='completed'): button returns to normal "Collect Latest Trends", dashboard auto-refreshes trends list, toast notification appears: "✓ Collection complete! Found 47 trends"
**And** if collection fails (status='failed'): button returns to normal, error toast appears: "⚠ Collection failed. Some APIs unavailable. Showing partial results."
**And** if collection still in progress after 30 minutes, show warning: "Collection taking longer than expected. You can navigate away and return later."
**And** collection progress doesn't block navigation (user can click trends, navigate away, return)
**And** page automatically refreshes trends list when collection completes (detected via polling)
**And** toast notifications auto-dismiss after 5 seconds
**And** if API returns 409 Conflict, show message: "Collection already in progress. Please wait."

### Story 3.6: Trend Detail View

As **dave (content planning lead)**,
I want **to click on any trend to see detailed platform breakdown and scoring calculation**,
So that **I can understand why a trend is scored the way it is**.

**Acceptance Criteria:**

**Given** dashboard displays trending list with clickable trend cards
**When** I click on a trend card
**Then** page navigates to /trend/{id} detail view
**And** detail page displays trend title prominently in h1 heading
**And** confidence badge (🔥⚡👀) is displayed next to title with size large
**And** confidence badge has hover tooltip: "High Confidence: All 4 platform signals aligned" (or "Medium: 2-3 signals" or "Low: 1 signal")
**And** "Platform Breakdown" section displays 4 cards: Reddit (score: 15,234, velocity score: 78/100, subreddit: r/videos, upvotes: 95%, external link: "View on Reddit"), YouTube (views: 2.5M, traction score: 82/100, channel: "TechChannel", likes: 125K, external link: "Watch on YouTube"), Google Trends (interest: 87/100, spike score: 85/100, related queries: ["query1", "query2"]), SimilarWeb (traffic change: +150%, spike detected: Yes)
**And** each platform card shows normalized score as progress bar (0-100 scale)
**And** "Momentum Score Calculation" section shows formula breakdown: "Reddit Velocity (78) × YouTube Traction (82) × Google Trends Spike (85) = Base Score (245); SimilarWeb Bonus Applied (×1.5) = Final Momentum Score: 87.5"
**And** "Back to Dashboard" link in top-left returns to /dashboard
**And** detail page loads in <2 seconds using Next.js getServerSideProps()
**And** detail page fetches: const trend = await fetch(`${BACKEND_URL}/trends/${id}`, {headers: {Authorization: `Bearer ${token}`}})
**And** if trend not found (404), show error: "Trend not found" with link back to dashboard

---

## Epic 4: AI-Powered Insights

**Epic Goal:** Enhance trend understanding with instant AI-generated explanations for any trend.

**User Outcome:** dave can click "Explain This Trend" button on any trend to receive a 3-sentence AI-generated summary in <3 seconds explaining what the trend is, why it's trending, and where it's big. AI briefs are cached for instant subsequent views.

### Story 4.1: Claude API Integration for Trend Briefs

As **dave (content planning lead)**,
I want **the backend to generate 3-sentence AI summaries using Claude API**,
So that **I can quickly understand what a trend is, why it's trending, and where it's big**.

**Acceptance Criteria:**

**Given** trends exist with scored data and ANTHROPIC_API_KEY in environment
**When** POST /trends/{id}/explain endpoint is called with JWT authentication
**Then** system retrieves trend data from database: SELECT title, reddit_score, youtube_views, google_trends_interest, similarweb_traffic, momentum_score, confidence_level FROM trends WHERE id=<id>
**And** system checks if ai_brief already exists: if trends.ai_brief IS NOT NULL, return cached brief immediately (no API call)
**And** if brief doesn't exist, system builds Claude API prompt: "Explain this trend in exactly 3 sentences using this structure:\n\nSentence 1: What is '{title}'?\nSentence 2: Why is it trending? (Include these metrics: Reddit score {reddit_score}, YouTube views {youtube_views}, Google Trends interest {google_trends_interest})\nSentence 3: Where is it big? (Based on platform data)\n\nBe concise and factual."
**And** system calls Claude API: POST https://api.anthropic.com/v1/messages with headers: {"x-api-key": ANTHROPIC_API_KEY, "anthropic-version": "2023-06-01", "content-type": "application/json"}, body: {"model": "claude-3-5-sonnet-20241022", "max_tokens": 150, "messages": [{"role": "user", "content": prompt}]}
**And** system receives response and extracts text from response.content[0].text
**And** system validates response has exactly 3 sentences (split on ". " and count)
**And** system stores AI brief: UPDATE trends SET ai_brief=<response>, ai_brief_generated_at=NOW() WHERE id=<id>
**And** system returns JSON: {"ai_brief": "Sentence 1. Sentence 2. Sentence 3.", "generated_at": "2026-01-06T14:23:45", "cached": false}
**And** API response time is <3 seconds (Claude API latency + database)
**And** if Claude API fails (timeout, error), return 503 Service Unavailable: {"error": "AI brief generation unavailable. Try again later."}
**And** system logs all Claude API calls with token usage: {"event": "claude_api_call", "trend_id": "<id>", "tokens_used": 142, "duration_ms": 2345, "success": true}
**And** if brief exists, return time <100ms (cached)

### Story 4.2: Explain This Trend Button UI

As **dave (content planning lead)**,
I want **to click "Explain This Trend" on any trend and see an instant AI summary**,
So that **I can understand trends without manual research**.

**Acceptance Criteria:**

**Given** dashboard or trend detail page displays trends
**When** I see a trend card
**Then** "Explain This Trend" button is visible below the metrics row with icon (✨ or 🤖)
**And** button has hover effect (background color change)
**And** when I click the button, button shows loading state: "Generating explanation..." with spinner icon, button disabled
**And** frontend sends POST /trends/{id}/explain with Authorization: Bearer <jwt_token>
**And** within <3 seconds, AI brief appears inline below the trend card in a highlighted box (light blue/purple background, border, padding)
**And** AI brief displays 3 sentences with clear paragraph formatting
**And** brief includes footer text: "Generated by Claude AI" with small gray text
**And** brief remains visible (doesn't disappear when interacting with other trends)
**And** button text changes to "Hide Explanation" after brief is shown (click to toggle show/hide)
**And** clicking "Hide Explanation" collapses the brief box (slide up animation)
**And** if brief was previously generated (cached), brief loads instantly <100ms (no loading state needed)
**And** if API returns 503 error, error message displays inline: "⚠ Unable to generate explanation. Please try again later." with red background
**And** error message has "Try Again" button to retry API call
**And** multiple trends can have briefs expanded simultaneously (independent state)
