---
stepsCompleted: [1, 2, 3, 4, 5, 6, 7, 8, 9, 10, 11]
inputDocuments:
  - '_bmad-output/analysis/product-brief-2026-01-05.md'
  - '_bmad-output/analysis/research-technical-2026-01-05.md'
  - '_bmad-output/analysis/brainstorming-session-2026-01-05.md'
workflowType: 'prd'
lastStep: 11
briefCount: 1
researchCount: 1
brainstormingCount: 1
projectDocsCount: 0
projectType: 'web_app'
domain: 'general'
complexity: 'low'
status: 'complete'
---

# Product Requirements Document - trend-monitor

**Author:** dave
**Date:** 2026-01-05

## Executive Summary

**trend-monitor** is a quantified trend monitoring system that predicts high-impact content opportunities through cross-platform signal convergence. The system enables content planning teams to act on trends during Phase 2-3 (niche-to-mainstream transition) rather than arriving late to saturated topics.

**Vision:** "Stop guessing what content will perform. Start making data-backed bets that maximize reach."

The tool transforms content planning from reactive scrolling (monitoring what's already viral) to proactive opportunity hunting (catching trends as they cross from niche to mainstream). By providing quantified metrics and confidence scores, it reduces meeting prep time from 2 hours to 15 minutes and enables data-backed content decisions.

**Target Users:**
- **Primary:** Content Planning Lead (dave) - Runs twice-weekly content strategy meetings
- **Secondary:** Content Creators - Execute content based on planning decisions

**Core Problem Solved:**
Content teams arrive late to trends because manual platform monitoring is slow and subjective. By the time a trend "feels big" across multiple platforms, it's already saturated. Early signals exist (Reddit spikes, YouTube traction), but correlating them manually is impossible at speed.

### What Makes This Special

**Cross-Platform Momentum Score** - The system's core innovation is detecting signal convergence across independent platforms (Reddit, YouTube, Google Trends, SimilarWeb) to predict "big ding" impact 12-48 hours before mainstream saturation.

**The Key Insight:** Single-platform metrics don't predict impact - **CONVERGENCE** across platforms does.

**The Pattern:**
1. **Phase 1:** Niche Ignition (Reddit surge)
2. **Phase 2:** Cross-Platform Jump (YouTube picks it up) ← **ACT HERE**
3. **Phase 3:** Search Explosion (Google Trends spike) ← **ACT HERE**
4. **Phase 4:** Mainstream Traffic (News coverage, too late)

**The Formula:**
```
Cross-Platform Momentum Score =
(Reddit_Velocity × YouTube_Traction × Google_Trends_Spike) + SimilarWeb_Bonus
```

**Confidence Scoring System:**
- 🔥 **High Confidence:** All signals aligned - Act NOW (>70% hit rate target)
- ⚡ **Medium Confidence:** 2-3 signals - Monitor closely
- 👀 **Low Confidence:** 1 signal - Watch and wait

This enables content teams to make confident, data-backed decisions about which trends to act on, catching opportunities at optimal timing for maximum reach.

## Project Classification

**Technical Type:** Web Application (Dashboard)
**Domain:** General / Content & Media
**Complexity:** Low
**Project Context:** Greenfield - new project

**Technical Characteristics:**
- Web-based dashboard (SPA)
- Data visualization and trend analysis
- API integrations (Reddit, YouTube, Google Trends, SimilarWeb, NewsAPI)
- AI-powered summarization (Claude API)
- Twice-weekly data collection cadence
- Single-user MVP, multi-user future consideration

**Technology Approach:**
- **Frontend:** Web dashboard (React or Next.js)
- **Backend:** Python for API integrations + scoring engine
- **Database:** PostgreSQL for trend data storage
- **Hosting:** Cloud-based (AWS/GCP/Railway)
- **APIs:** Reddit, YouTube Data API v3, NewsAPI, Google Trends (PyTrends), SimilarWeb

## Success Criteria

### User Success

**Primary User (Content Planning Lead - dave):**
- **Time Efficiency:** Meeting prep time reduces from 2 hours to 15 minutes (87.5% reduction)
- **Confident Decision-Making:** Can walk into twice-weekly content planning meetings with 3-5 high-confidence opportunities, each backed by real numbers
- **Data-Backed Justification:** Can articulate "why now" for each trend with quantified metrics (views, upvotes, search interest, traffic)
- **Habit Formation:** Uses tool consistently 2x per week for 4+ consecutive weeks

**Success Moment:** When dave says "I can't run content planning without this anymore"

**Secondary Users (Content Creators):**
- **Timely Content:** Create content that feels fresh and relevant (not arriving late to saturated trends)
- **Credible Data:** Can reference real numbers in content ("This trend has 2.5M views in 12 hours")
- **Clear Angles:** Receive specific content angles automatically suggested, not just "make content about X"

**Success Moment:** When content creators say "I can create content that feels timely and includes data that makes it credible"

### Business Success

**MVP Success Validation (Week 1-4):**
1. **Lead Time Achievement:** Tool flags high-confidence trends 12-48 hours before mainstream media coverage saturation
2. **Hit Rate Validation:** 70%+ of 🔥 (high-confidence) trends reach >1M impressions within 72 hours
3. **Consistent Usage:** Dave uses the tool twice per week for 4 consecutive weeks without dropping off
4. **Efficiency Gain:** Meeting prep time demonstrably drops from 2hrs to 15 min

**Phase 2 Success (Month 2-3):**
- **Confidence Score Accuracy:** High confidence (🔥) trends perform 3x better than low confidence (👀) trends
- **Content Performance Lift:** Content based on tool recommendations shows 50% increase in average engagement vs. gut-feel selections
- **User Retention:** Dave continues using after initial 4-week validation period

**Long-Term Success (Month 3+):**
- **Beta User Validation:** 3-5 similar content teams adopt and validate the core hypothesis
- **Monetization Readiness:** Product-market fit validated, ready for subscription model consideration

**MVP Fails If:**
- Confidence scores don't correlate with actual trend performance (invalidates core hypothesis)
- Data collection takes >30 minutes per run (not scalable)
- Dave stops using it after 2 weeks (not habit-forming)

### Technical Success

**Data Collection Performance:**
- Twice-weekly data collection completes in <30 minutes per run
- All API integrations remain within free tier limits (or <$449/mo NewsAPI)
- Cross-Platform Momentum Score calculation completes in <5 seconds per trend

**System Reliability:**
- Dashboard loads in <2 seconds
- No data loss between collection runs
- API rate limits handled gracefully with retry logic
- 95%+ uptime (cloud hosting)

**Data Quality:**
- API integrations return valid, complete data 95%+ of the time
- Normalization layer correctly compares metrics across platforms
- Confidence scores (🔥⚡👀) assigned consistently based on signal convergence

**Scalability Readiness:**
- Database schema supports future multi-user expansion
- API integration patterns allow adding new data sources (e.g., Sprout Social in Phase 2)
- Scoring algorithm can handle 100+ trending topics without performance degradation

### Measurable Outcomes

**Week 1-2 (MVP Launch):**
- Tool successfully collects data from all 5 APIs (Reddit, YouTube, NewsAPI, Google Trends, SimilarWeb)
- Trending Now Dashboard displays Top 10 trends with quantified metrics
- Dave runs first 2 content planning meetings using the tool
- Initial hit rate measured for 🔥 trends

**Week 3-4 (Validation):**
- 70%+ hit rate achieved on high-confidence trends
- Meeting prep time consistently 15 minutes or less
- Dave reports confidence in data-backed decisions
- No critical bugs or data collection failures

**Week 5-8 (Iteration):**
- Confidence score accuracy validated (🔥 trends perform 3x better than 👀)
- Content performance lift measurable (50%+ increase in engagement)
- Dave says "this is indispensable"
- Ready for beta user expansion

## Product Scope

### MVP - Minimum Viable Product

**Core Hypothesis Validation Features (Ship in 2-3 weeks):**

1. **Cross-Platform Momentum Score Engine**
   - Data collection from Reddit API, YouTube Data API, Google Trends (PyTrends), SimilarWeb API, NewsAPI
   - Metric normalization layer (convert different scales to comparable scores)
   - Composite score calculation: `(Reddit_Velocity × YouTube_Traction × Google_Trends_Spike) + SimilarWeb_Bonus`
   - Confidence level assignment (🔥 High / ⚡ Medium / 👀 Low) based on signal convergence

2. **Trending Now Dashboard**
   - Display Top 10 trends ranked by Cross-Platform Momentum Score
   - Show THE actual numbers for each trend (views, upvotes, search interest, traffic)
   - Display confidence score prominently with visual indicators (🔥⚡👀)
   - Update twice-weekly via manual trigger (automated scheduling in Phase 2)

3. **AI-Powered Trend Brief**
   - One-click "Explain this trend" functionality
   - Generate 3-sentence summaries via Claude API
   - Context: What is it? Why is it trending? Where is it big?

**MVP Non-Negotiables:**
- Single-user access (dave only)
- Twice-weekly data collection (not real-time)
- Web dashboard only (no mobile app)
- Basic UI/UX (functional over beautiful)

**Success Gate:** MVP is successful if dave uses it 2x/week for 4 weeks AND 70%+ hit rate on 🔥 trends AND meeting prep drops to 15 min.

### Growth Features (Post-MVP)

**Phase 2 (Month 2-3) - If MVP Validates:**

4. **Rising Stars Watch**
   - Trends showing consistent growth over 3+ days
   - Early warning system for next week's opportunities
   - Momentum trajectory visualization

5. **Fading Fast Alert**
   - Trends that peaked and are now declining
   - Save team from "late to the party" embarrassment
   - Historical peak data comparison

6. **Content Angle Suggester**
   - AI-generated content angle ideas (5 ways to spin each trend)
   - Competitor gap analysis
   - Audience-specific angle recommendations

7. **Competitor Watch**
   - Track which competitors are covering which trends
   - Identify white space opportunities
   - Time-to-market comparison

8. **Automated Scheduling**
   - Twice-weekly automated data collection (no manual trigger)
   - Email/Slack notifications for high-confidence trends
   - Scheduled report delivery before meetings

9. **Multi-User Support**
   - Team accounts with role-based access
   - Collaborative trend annotation and notes
   - Shared meeting prep workspace

**Phase 2 Success Gate:** Beta users (3-5 teams) validate the tool and report similar success metrics.

### Vision (Future - Month 3+)

10. **Sprout Social Integration**
    - Add Twitter/X data via Sprout Social API (~$800/mo vs $5K/mo direct X API)
    - Instagram and Facebook listening data
    - Unified cross-platform confidence scoring

11. **MCP Server Integration**
    - Natural language queries via Claude: "What memes are trending this week?"
    - Conversational trend exploration
    - AI-powered meeting prep assistant

12. **Historical Trend Archive**
    - Review past trends and their momentum scores
    - Learn from what worked/didn't work
    - Pattern recognition over time

13. **Trend Forecasting (ML Model)**
    - Predict which Phase 1 trends will hit Phase 3
    - "This Reddit surge has 80% chance of going mainstream"
    - Probability-based recommendations

14. **Content Performance Tracking**
    - Close the loop: track performance of content created based on tool recommendations
    - A/B comparison: tool-recommended vs. gut-feel content
    - ROI validation and optimization

**Vision Success:** Product becomes the industry standard for data-driven content planning, with subscription revenue model and 100+ teams using it.

## User Journeys

### Primary Journey: Twice-Weekly Content Planning Meeting Prep

**Actor:** dave (Content Planning Lead)

**Trigger:** Twice-weekly content planning meeting approaching (e.g., Monday 9am, Thursday 2pm)

**Goal:** Prepare for content planning meeting with 3-5 high-confidence trend opportunities backed by data

**Journey Steps:**

1. **Access Dashboard**
   - dave opens trend-monitor web dashboard
   - System loads within 2 seconds
   - Dashboard displays last data collection timestamp

2. **Trigger Data Collection** (if needed)
   - dave clicks "Collect Latest Trends" button
   - System initiates API calls to Reddit, YouTube, Google Trends, SimilarWeb, NewsAPI
   - Progress indicator shows collection status
   - Collection completes in <30 minutes

3. **Review Trending Now**
   - dave sees Top 10 trends ranked by Cross-Platform Momentum Score
   - Each trend shows:
     - Confidence score (🔥⚡👀)
     - Key metrics: Reddit score, YouTube views, Google Trends interest, SimilarWeb traffic
     - Trend title/topic
     - Time detected (how long trend has been active)

4. **Explore High-Confidence Trends**
   - dave clicks on a 🔥 high-confidence trend
   - System displays detailed view:
     - Breakdown of metrics across all platforms
     - Cross-Platform Momentum Score calculation
     - Trend trajectory (rising/stable/declining)

5. **Generate AI Brief**
   - dave clicks "Explain This Trend" button
   - System calls Claude API
   - AI generates 3-sentence summary:
     - What is it?
     - Why is it trending?
     - Where is it big?
   - Brief displays in <3 seconds

6. **Select Trends for Meeting**
   - dave reviews 3-5 high-confidence trends
   - Makes mental notes or copies data for meeting presentation
   - Total time: 15 minutes (down from 2 hours manual scrolling)

7. **Present in Meeting**
   - dave walks into content planning meeting
   - Presents 3-5 trends with quantified metrics
   - Team makes data-backed decisions on which trends to act on

**Success Outcome:** Meeting prep completed in 15 minutes with confident, data-backed trend recommendations.

**Pain Points Eliminated:**
- No more manual scrolling across Reddit, YouTube, news sites (2 hours saved)
- No more gut-feel decisions without data backing
- No more arriving late to saturated trends

### Secondary Journey: Content Creator Using Tool Output

**Actor:** Content Creator (team member)

**Trigger:** Content planning meeting concludes with trend assignments

**Goal:** Create timely content with credible data references

**Journey Steps:**

1. **Receive Trend Assignment**
   - Content creator is assigned to create content on a specific trend flagged by tool
   - Has access to the trend's detailed metrics from dashboard

2. **Reference Quantified Data**
   - Includes real numbers in content: "This trend has 2.5M YouTube views in 12 hours"
   - Cites cross-platform presence: "Trending on Reddit (15K upvotes), YouTube (2.5M views), Google search spiking"

3. **Create Timely Content**
   - Content feels fresh because trend was caught in Phase 2-3 (not Phase 4 saturation)
   - Publishes within trend's momentum window

**Success Outcome:** Content feels timely, includes credible data, and rides the trend wave at optimal timing.

## Functional Requirements

### FR-1: Cross-Platform Data Collection

**Priority:** P0 (MVP Critical)

#### FR-1.1: Reddit API Integration
- System SHALL authenticate with Reddit API using OAuth 2.0
- System SHALL collect the following metrics per post:
  - Post score (upvotes - downvotes)
  - Comment count
  - Upvote ratio
  - Post age (timestamp)
  - Subreddit subscriber count
  - Crosspost count
- System SHALL monitor trending posts from configurable subreddits (default: 10 subreddits)
- System SHALL handle Reddit rate limits (60 req/min authenticated)
- System SHALL retry failed requests with exponential backoff

#### FR-1.2: YouTube Data API Integration
- System SHALL authenticate with YouTube Data API v3
- System SHALL collect the following metrics per video:
  - View count
  - Like count
  - Comment count
  - Channel subscriber count
  - Publication date/time
  - Video title and description
- System SHALL monitor trending videos from configurable channels (default: 20 channels)
- System SHALL stay within 10,000 units/day quota by using video list endpoint (1 unit) instead of search (100 units)
- System SHALL implement caching to reduce API calls by 50-80%

#### FR-1.3: Google Trends Integration
- System SHALL use PyTrends library for Google Trends data
- System SHALL collect Interest Over Time data (0-100 scale)
- System SHALL detect search interest spikes
- System SHALL monitor configurable keywords/topics (default: 50 topics)
- System SHALL handle rate limiting with 60-second delays between requests
- System SHALL gracefully handle PyTrends failures and log errors

#### FR-1.4: SimilarWeb API Integration
- System SHALL authenticate with existing SimilarWeb subscription
- System SHALL collect the following metrics per website:
  - Total traffic (visitor count)
  - Traffic sources breakdown
  - Engagement metrics (bounce rate, pages/visit)
  - Geographic distribution
- System SHALL detect traffic spikes indicating mainstream pickup

#### FR-1.5: NewsAPI Integration
- System SHALL authenticate with NewsAPI (Developer tier for MVP, Business tier for production)
- System SHALL collect article metadata:
  - Source name
  - Title and description
  - Publication date
  - Article URL
- System SHALL search for articles by trending topics
- System SHALL infer source authority from publication reputation

### FR-2: Cross-Platform Momentum Score Calculation

**Priority:** P0 (MVP Critical)

#### FR-2.1: Metric Normalization
- System SHALL normalize Reddit scores to 0-100 scale using log scaling
- System SHALL normalize YouTube view counts to 0-100 scale using log scaling
- System SHALL use Google Trends interest (already 0-100) directly
- System SHALL normalize SimilarWeb traffic to 0-100 scale using log scaling
- System SHALL make normalized scores comparable across platforms

#### FR-2.2: Velocity Calculation
- System SHALL calculate Reddit velocity as: `(score / hours_since_post) × log(subreddit_size)`
- System SHALL calculate YouTube traction as: `(views / hours_since_publish) × (engagement_rate) × log(channel_subs)`
- System SHALL calculate Google Trends spike as: `(current_interest - 7day_avg) / 7day_stddev`

#### FR-2.3: Composite Score
- System SHALL calculate Cross-Platform Momentum Score as:
  ```
  Score = (Reddit_Velocity × YouTube_Traction × Google_Trends_Spike) + SimilarWeb_Bonus
  ```
- System SHALL apply SimilarWeb Bonus (multiply by 1.5) if traffic spike detected
- System SHALL calculate scores in <5 seconds per trend

#### FR-2.4: Confidence Level Assignment
- System SHALL assign 🔥 High Confidence if all 4 platform signals align (Reddit + YouTube + Google Trends + SimilarWeb)
- System SHALL assign ⚡ Medium Confidence if 2-3 platform signals align
- System SHALL assign 👀 Low Confidence if only 1 platform signal present
- System SHALL store confidence level with each trend record

### FR-3: Trending Now Dashboard

**Priority:** P0 (MVP Critical)

#### FR-3.1: Dashboard Display
- System SHALL display Top 10 trends ranked by Cross-Platform Momentum Score
- System SHALL show for each trend:
  - Trend title/topic
  - Confidence score with visual indicator (🔥⚡👀)
  - Key metrics: Reddit score, YouTube views, Google Trends interest, SimilarWeb traffic (actual numbers)
  - Time detected (hours/days since first detection)
  - Trend status (rising/stable/declining)
- System SHALL load dashboard in <2 seconds
- System SHALL update dashboard display in real-time when new data collected

#### FR-3.2: Manual Data Collection Trigger
- System SHALL provide "Collect Latest Trends" button
- System SHALL display progress indicator during collection
- System SHALL show completion status and timestamp of last collection
- System SHALL complete collection in <30 minutes

#### FR-3.3: Trend Detail View
- System SHALL allow users to click on any trend to see detailed view
- System SHALL display breakdown of metrics across all platforms
- System SHALL show Cross-Platform Momentum Score calculation components
- System SHALL display trend trajectory chart (if historical data available)

### FR-4: AI-Powered Trend Brief

**Priority:** P0 (MVP Critical)

#### FR-4.1: Brief Generation
- System SHALL provide "Explain This Trend" button for each trend
- System SHALL call Claude API to generate 3-sentence summary
- System SHALL include in prompt:
  - Trend topic/title
  - Platform metrics
  - Why it's trending (based on data)
  - Where it's big (platforms, geographies)
- System SHALL display brief in <3 seconds

#### FR-4.2: Brief Content Structure
- System SHALL generate summary with this structure:
  - Sentence 1: What is it?
  - Sentence 2: Why is it trending?
  - Sentence 3: Where is it big?
- System SHALL keep summaries concise (3 sentences maximum)

### FR-5: Data Storage

**Priority:** P0 (MVP Critical)

#### FR-5.1: Database Schema
- System SHALL use PostgreSQL database
- System SHALL store trend records with:
  - Trend ID (unique identifier)
  - Trend title/topic
  - Collection timestamp
  - Platform-specific metrics (Reddit, YouTube, Google Trends, SimilarWeb, NewsAPI)
  - Normalized scores per platform
  - Cross-Platform Momentum Score
  - Confidence level
  - AI-generated brief (if generated)
- System SHALL support future multi-user expansion through schema design

#### FR-5.2: Data Persistence
- System SHALL persist all collected data between runs
- System SHALL maintain historical trend data for future analytics
- System SHALL prevent data loss through database backups

### FR-6: Authentication & Access Control

**Priority:** P0 (MVP Critical)

#### FR-6.1: Single-User Access (MVP)
- System SHALL require login with username/password
- System SHALL support single user (dave) only in MVP
- System SHALL maintain session for 7 days
- System SHALL log out user after 30 days of inactivity

#### FR-6.2: API Key Management
- System SHALL securely store API keys for all integrated services (Reddit, YouTube, Google Trends, SimilarWeb, NewsAPI)
- System SHALL use environment variables or secure key management service
- System SHALL never expose API keys in client-side code or logs

## Non-Functional Requirements

### NFR-1: Performance

**Priority:** P0 (MVP Critical)

- **NFR-1.1:** Dashboard SHALL load in <2 seconds on standard broadband connection (10 Mbps+)
- **NFR-1.2:** Data collection SHALL complete in <30 minutes for all 5 APIs and ~50 trending topics
- **NFR-1.3:** Cross-Platform Momentum Score calculation SHALL complete in <5 seconds per trend
- **NFR-1.4:** AI brief generation SHALL complete in <3 seconds per trend
- **NFR-1.5:** Database queries SHALL return results in <500ms for dashboard views

### NFR-2: Reliability

**Priority:** P0 (MVP Critical)

- **NFR-2.1:** System SHALL achieve 95%+ uptime (allowing ~36 hours downtime per month)
- **NFR-2.2:** System SHALL handle API failures gracefully with retry logic and exponential backoff
- **NFR-2.3:** System SHALL return valid data 95%+ of the time (excluding external API failures)
- **NFR-2.4:** System SHALL not lose collected data between runs (database persistence)

### NFR-3: Scalability

**Priority:** P1 (Post-MVP)

- **NFR-3.1:** System SHOULD support monitoring 100+ trending topics without performance degradation
- **NFR-3.2:** System SHOULD support future multi-user expansion (3-5 users initially, 100+ eventually)
- **NFR-3.3:** Database schema SHOULD allow adding new data sources (e.g., Sprout Social in Phase 2)

### NFR-4: Security

**Priority:** P0 (MVP Critical)

- **NFR-4.1:** System SHALL encrypt API keys at rest
- **NFR-4.2:** System SHALL use HTTPS for all client-server communication
- **NFR-4.3:** System SHALL not log sensitive information (API keys, passwords)
- **NFR-4.4:** System SHALL implement secure password hashing (bcrypt/Argon2)
- **NFR-4.5:** System SHALL protect against common web vulnerabilities (XSS, CSRF, SQL injection)

### NFR-5: Maintainability

**Priority:** P1 (Important)

- **NFR-5.1:** Code SHALL follow Python PEP 8 style guidelines for backend
- **NFR-5.2:** Code SHALL follow React/TypeScript best practices for frontend
- **NFR-5.3:** System SHALL include logging for debugging and monitoring
- **NFR-5.4:** API integration patterns SHALL be modular and allow easy addition of new sources

### NFR-6: Cost Efficiency

**Priority:** P0 (MVP Critical)

- **NFR-6.1:** System SHALL stay within free tier limits for Reddit API (60 req/min)
- **NFR-6.2:** System SHALL stay within free tier limits for YouTube API (10K units/day)
- **NFR-6.3:** System SHALL use NewsAPI Developer tier (free) for MVP testing
- **NFR-6.4:** Total monthly cost SHALL not exceed $500 for MVP ($0 for testing, up to $449 for production NewsAPI + ~$50 infrastructure)

### NFR-7: Usability

**Priority:** P1 (Important)

- **NFR-7.1:** Dashboard SHALL be intuitive for non-technical users (dave is non-technical)
- **NFR-7.2:** Visual indicators (🔥⚡👀) SHALL be immediately understandable
- **NFR-7.3:** System SHALL provide clear error messages when data collection fails
- **NFR-7.4:** System SHALL work on standard web browsers (Chrome, Firefox, Safari, Edge)

## User Experience Requirements

### UX-1: Dashboard Layout

**Priority:** P0 (MVP Critical)

#### Visual Hierarchy
- **Primary Focus:** Trending Now list (Top 10) prominently displayed
- **Secondary Focus:** Confidence scores with large, clear visual indicators (🔥⚡👀)
- **Tertiary Focus:** Actual metrics (numbers) for each trend
- **Supporting Elements:** Data collection trigger button, last updated timestamp

#### Layout Structure
```
+------------------------------------------+
| trend-monitor                Last Updated: 2h ago |
|                              [Collect Latest Trends] |
+------------------------------------------+
| Trending Now - Top 10                  |
|                                        |
| 🔥 #1: [Trend Title]                   |
|    Reddit: 15.2K | YouTube: 2.5M       |
|    Google Trends: 87 | SimilarWeb: +150% |
|    [Explain This Trend]                |
|                                        |
| 🔥 #2: [Trend Title]                   |
|    Reddit: 12.8K | YouTube: 1.8M       |
|    ...                                 |
|                                        |
| ⚡ #3: [Trend Title]                   |
|    ...                                 |
+------------------------------------------+
```

### UX-2: Interaction Patterns

**Priority:** P0 (MVP Critical)

- **Click on Trend:** Expand to detailed view with full metrics breakdown
- **Hover on Confidence Score:** Tooltip explains what the score means and which signals are present
- **Click "Explain This Trend":** AI brief appears inline below trend (no navigation required)
- **Click "Collect Latest Trends":** Progress modal shows collection status, dismisses on completion

### UX-3: Visual Design

**Priority:** P1 (Nice to Have)

- **Design Philosophy:** Functional over beautiful for MVP
- **Color Scheme:** Simple, high-contrast for readability
- **Confidence Indicators:**
  - 🔥 High Confidence: Red/orange visual treatment, prominent
  - ⚡ Medium Confidence: Yellow/amber visual treatment, moderate prominence
  - 👀 Low Confidence: Blue/gray visual treatment, subdued
- **Typography:** Clear, readable fonts (system defaults acceptable for MVP)

### UX-4: Responsive Design

**Priority:** P1 (Post-MVP)

- **MVP:** Desktop web only (no mobile optimization required)
- **Post-MVP:** Responsive design for tablet/mobile access

### UX-5: Error Handling

**Priority:** P0 (MVP Critical)

- **API Failures:** Display clear error messages: "Unable to collect Reddit data. Retrying..."
- **Network Issues:** Display connectivity error with retry option
- **No Data:** Display message: "No trends collected yet. Click 'Collect Latest Trends' to begin."

## Technical Considerations

### Tech Stack

**Frontend:**
- **Framework:** React or Next.js (recommend Next.js for server-side rendering)
- **Language:** TypeScript for type safety
- **UI Library:** Minimal (use native HTML/CSS or lightweight library like TailwindCSS)
- **State Management:** React Context API or Zustand (avoid Redux for simplicity)

**Backend:**
- **Language:** Python 3.10+
- **Framework:** FastAPI (for API endpoints) or Flask (simpler alternative)
- **API Integration Libraries:**
  - `praw` (Python Reddit API Wrapper)
  - `google-api-python-client` (YouTube Data API)
  - `pytrends` (Google Trends)
  - `requests` (SimilarWeb API, NewsAPI, Claude API)
- **Database ORM:** SQLAlchemy (Python ORM for PostgreSQL)
- **Task Scheduling:** APScheduler or Celery (for future automated collection)

**Database:**
- **Database:** PostgreSQL 14+
- **Hosting:** Managed PostgreSQL service (e.g., AWS RDS, Railway, Supabase)

**Hosting & Infrastructure:**
- **Platform:** Railway, AWS (Elastic Beanstalk), or GCP (App Engine)
- **Cost:** ~$20-50/month for hosting + database
- **CI/CD:** GitHub Actions for automated deployments

### Architecture Patterns

**System Architecture:**
```
┌─────────────┐
│   Browser   │ (React/Next.js Frontend)
└──────┬──────┘
       │ HTTPS
       ▼
┌─────────────┐
│  FastAPI    │ (Python Backend)
│  Backend    │
└──────┬──────┘
       │
       ├──────► PostgreSQL Database
       │
       ├──────► Reddit API
       ├──────► YouTube API
       ├──────► Google Trends (PyTrends)
       ├──────► SimilarWeb API
       ├──────► NewsAPI
       └──────► Claude API (for AI briefs)
```

**Data Flow:**
1. User clicks "Collect Latest Trends" in frontend
2. Frontend sends request to FastAPI backend
3. Backend triggers data collection jobs (parallel API calls)
4. Backend collects and stores raw data in PostgreSQL
5. Backend calculates normalized scores and Cross-Platform Momentum Score
6. Backend assigns confidence levels
7. Backend returns Top 10 trends to frontend
8. Frontend displays Trending Now dashboard

**API Integration Pattern:**
- Use async/await for parallel API calls (Python `asyncio`)
- Implement retry logic with exponential backoff for all API calls
- Cache API responses where appropriate (YouTube channel info, subreddit metadata)
- Log all API failures for debugging

### Data Storage Schema

**Tables:**

**trends**
- id (UUID, primary key)
- title (VARCHAR)
- created_at (TIMESTAMP)
- reddit_score (INTEGER)
- reddit_comments (INTEGER)
- youtube_views (INTEGER)
- youtube_likes (INTEGER)
- google_trends_interest (INTEGER)
- similarweb_traffic (INTEGER)
- momentum_score (FLOAT)
- confidence_level (ENUM: high, medium, low)
- ai_brief (TEXT, nullable)

**data_collections**
- id (UUID, primary key)
- started_at (TIMESTAMP)
- completed_at (TIMESTAMP)
- status (ENUM: in_progress, completed, failed)
- errors (JSONB, nullable)

### Security Considerations

- **API Key Management:** Use environment variables, never commit keys to git
- **Authentication:** JWT tokens for session management
- **HTTPS:** Enforce HTTPS for all client-server communication
- **Input Validation:** Sanitize all user inputs to prevent XSS/SQL injection
- **Rate Limiting:** Implement rate limiting on backend endpoints to prevent abuse

### Testing Strategy

**MVP Testing (Minimal):**
- Manual testing of core workflows (data collection, dashboard display, AI briefs)
- Smoke tests for API integrations
- Basic error handling tests

**Post-MVP Testing:**
- Unit tests for scoring algorithm
- Integration tests for API collectors
- End-to-end tests for critical user journeys

### Deployment Strategy

**MVP Deployment:**
- Deploy backend to Railway or AWS Elastic Beanstalk
- Deploy frontend to Vercel or Netlify (static hosting)
- Use managed PostgreSQL service (Railway, AWS RDS)
- Manual deployment initially, GitHub Actions CI/CD later

### Monitoring & Observability

**MVP Monitoring (Minimal):**
- Application logs (stdout/stderr)
- Error logging to file or cloud logging service
- Basic uptime monitoring (e.g., UptimeRobot)

**Post-MVP Monitoring:**
- Application Performance Monitoring (APM) tool (e.g., Sentry, DataDog)
- API quota usage tracking
- User analytics (dashboard views, trend clicks)

## Risks & Mitigation

### Risk 1: Google Trends API Reliability (PyTrends)

**Risk Level:** HIGH
**Impact:** PyTrends is unofficial and could break if Google changes their website structure
**Likelihood:** MEDIUM (Google occasionally changes structure)

**Mitigation:**
- Apply for official Google Trends API alpha access (now accepting testers)
- Implement fallback scraping mechanism if PyTrends fails
- Log all PyTrends failures and monitor error rates
- Build system to gracefully handle missing Google Trends data (calculate momentum score with 3 platforms instead of 4)

### Risk 2: YouTube API Quota Limits

**Risk Level:** MEDIUM
**Impact:** Could exceed 10,000 units/day free quota, requiring paid tier or limiting data collection
**Likelihood:** MEDIUM (if not optimized)

**Mitigation:**
- Use video list endpoint (1 unit) instead of search endpoint (100 units)
- Implement aggressive caching for channel metadata and video data
- Monitor daily quota usage and alert if approaching limit
- Optimize queries to request only necessary fields
- Reduce number of monitored channels if needed (start with 10 instead of 20)

### Risk 3: NewsAPI Production Cost

**Risk Level:** LOW
**Impact:** NewsAPI requires $449/month for production use (Developer tier is testing only)
**Likelihood:** HIGH (will need to upgrade)

**Mitigation:**
- Use Developer tier for MVP testing (free)
- Budget $449/month for production deployment
- Evaluate alternative news APIs (NewsData.io, NewsCatcher) for better pricing
- Consider deprioritizing NewsAPI in momentum score calculation (use Reddit + YouTube + Google Trends + SimilarWeb only)

### Risk 4: User Adoption - "Another Dashboard" Syndrome

**Risk Level:** MEDIUM
**Impact:** Tool becomes just another dashboard dave forgets to check
**Likelihood:** MEDIUM (common problem with new tools)

**Mitigation:**
- Make tool FAST (15 min meeting prep vs 2 hours)
- Make it ACTIONABLE (confidence scores guide decisions)
- Align with existing workflow (twice-weekly content meetings)
- Deliver immediate value (quantified metrics dave can't get elsewhere)
- Consider future Slack/email notifications for high-confidence trends

### Risk 5: Confidence Score Accuracy

**Risk Level:** HIGH
**Impact:** If confidence scores don't correlate with actual trend performance, core hypothesis fails
**Likelihood:** MEDIUM (scoring algorithm needs validation)

**Mitigation:**
- Track actual outcomes: measure whether 🔥 trends reach >1M impressions within 72 hours
- Iterate on scoring algorithm based on real-world performance
- Allow manual feedback: let dave mark trends as "hit" or "miss" to tune algorithm
- Start conservative: require all 4 platform signals for 🔥 high confidence
- Build analytics dashboard to visualize hit rate over time

### Risk 6: API Changes or Deprecation

**Risk Level:** LOW
**Impact:** Reddit/YouTube/SimilarWeb APIs could change or be deprecated
**Likelihood:** LOW (these are stable, well-documented APIs)

**Mitigation:**
- Use official API client libraries where available (praw for Reddit, google-api-python-client for YouTube)
- Monitor API changelogs and deprecation notices
- Implement version pinning and gradual upgrades
- Build system to gracefully handle missing data from one source

### Risk 7: Data Collection Performance

**Risk Level:** MEDIUM
**Impact:** Data collection takes >30 minutes, making twice-weekly usage impractical
**Likelihood:** MEDIUM (depends on implementation efficiency)

**Mitigation:**
- Implement parallel API calls using Python `asyncio`
- Use aggressive caching to reduce redundant API calls
- Optimize database queries for fast writes
- Monitor collection time and optimize bottlenecks
- Consider running data collection as background job (user doesn't wait)

### Risk 8: Cost Overruns

**Risk Level:** LOW
**Impact:** Monthly costs exceed budget
**Likelihood:** LOW (most APIs are free tier)

**Mitigation:**
- Monitor API usage daily and set up alerts for quota approaching limits
- Implement cost controls (e.g., cap max API calls per collection)
- Use free tier NewsAPI for MVP testing
- Budget $500/month maximum ($449 NewsAPI + $50 infrastructure)

## Dependencies & Assumptions

### External Dependencies

**Critical (MVP Blockers):**
1. **Reddit API Access** - Requires OAuth 2.0 app registration
2. **YouTube Data API Access** - Requires Google Cloud project and API key
3. **Google Trends (PyTrends)** - Unofficial library, no registration required
4. **SimilarWeb API Access** - dave already has subscription
5. **NewsAPI Access** - Requires free Developer account registration
6. **Claude API Access** - Requires Anthropic API key for AI briefs
7. **PostgreSQL Database** - Requires managed database service (Railway, AWS RDS)
8. **Hosting Platform** - Requires cloud hosting account (Railway, AWS, GCP)

**Non-Critical (Can Work Without):**
- Slack/Email integration (Phase 2)
- Sprout Social integration (Phase 2)

### Assumptions

**Technical Assumptions:**
1. **API Stability:** Assume Reddit, YouTube, and SimilarWeb APIs remain stable during MVP development
2. **PyTrends Reliability:** Assume PyTrends continues to work for Google Trends data (acknowledge risk, have mitigation)
3. **Free Tier Sufficiency:** Assume free tier API quotas are sufficient for twice-weekly collection of ~50 trends
4. **Cloud Hosting:** Assume cloud hosting platforms (Railway, AWS) provide adequate performance for <$50/month
5. **Database Performance:** Assume managed PostgreSQL can handle write load from data collection and read load from dashboard

**User Assumptions:**
1. **Consistent Usage:** Assume dave will use tool consistently 2x/week for at least 4 weeks to validate MVP
2. **Meeting Cadence:** Assume twice-weekly content planning meetings continue as current workflow
3. **Browser Access:** Assume dave has access to modern web browser (Chrome, Firefox, Safari, Edge)
4. **Broadband Connection:** Assume dave has stable internet connection (10 Mbps+ for dashboard loading)

**Business Assumptions:**
1. **Budget Approval:** Assume $449/month NewsAPI production tier approved when moving beyond MVP testing
2. **Single User MVP:** Assume dave is the only user for MVP (no multi-user requirements)
3. **Content Team Structure:** Assume content team structure remains stable (dave as planning lead, creators as secondary users)
4. **Success Metric Validity:** Assume 70%+ hit rate on 🔥 trends is achievable and validates core hypothesis

**Domain Assumptions:**
1. **Trend Lifecycle:** Assume trends follow Phase 1-4 pattern (Niche → Cross-Platform → Search Explosion → Mainstream)
2. **Signal Convergence:** Assume cross-platform signal convergence predicts "big ding" impact better than single-platform metrics
3. **Timing Window:** Assume 12-48 hour lead time is valuable for content planning (not too early, not too late)
4. **Content Types:** Assume tool applies to various content types (videos, articles, social posts)

### Known Constraints

**Time Constraints:**
- MVP target: Ship in 2-3 weeks from PRD approval

**Cost Constraints:**
- MVP budget: $0/month (testing phase)
- Production budget: <$500/month ($449 NewsAPI + ~$50 infrastructure)

**Resource Constraints:**
- Single developer (non-technical user, dave)
- No dedicated QA or design resources for MVP

**Technical Constraints:**
- Python backend (developer's primary language)
- Web-only (no mobile app for MVP)
- Single-user access (no multi-tenancy for MVP)

## Appendices

### Glossary

- **Cross-Platform Momentum Score:** Composite metric calculating trend impact based on convergence of signals across Reddit, YouTube, Google Trends, and SimilarWeb
- **Confidence Score:** Classification of trends into 🔥 High (all signals), ⚡ Medium (2-3 signals), or 👀 Low (1 signal) based on platform signal convergence
- **Phase 2-3:** Optimal timing window for acting on trends (cross-platform jump and search explosion phases)
- **Big Ding:** High-impact viral moment that generates significant reach and engagement
- **Velocity:** Rate of growth for a trend metric (e.g., upvotes per hour, views per hour)

### Related Documents

- Product Brief: `_bmad-output/analysis/product-brief-2026-01-05.md`
- Technical Research: `_bmad-output/analysis/research-technical-2026-01-05.md`
- Brainstorming Session: `_bmad-output/analysis/brainstorming-session-2026-01-05.md`

### API Documentation References

- Reddit API: https://www.reddit.com/dev/api/
- YouTube Data API v3: https://developers.google.com/youtube/v3
- PyTrends (Google Trends): https://github.com/GeneralMills/pytrends
- SimilarWeb API: https://developer.similarweb.com/
- NewsAPI: https://newsapi.org/docs
- Claude API: https://docs.anthropic.com/

---

## Document Approval

**PRD Status:** COMPLETE
**Created:** 2026-01-05
**Last Updated:** 2026-01-05
**Author:** dave
**Approval Required From:** dave (Product Owner)

**Next Steps:**
1. Review and approve PRD
2. Create Architecture Document (system design)
3. Create Epics & Stories (break down into implementation tasks)
4. Implementation Readiness Check
5. Sprint Planning → Development begins
