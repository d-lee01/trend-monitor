# Product Brief: Quantified Trend Monitoring System

**Date:** 2026-01-05
**Product Owner:** dave
**Status:** Discovery Complete
**Target Launch:** MVP in 2-3 weeks

---

## Executive Summary

A trend monitoring system that predicts "big ding" content opportunities through cross-platform signal convergence, enabling content teams to act on trends during Phase 2-3 (niche-to-mainstream transition) rather than arriving late to saturated topics.

**Core Innovation:** Cross-Platform Momentum Score that quantifies trend velocity across Reddit, YouTube, Google Trends, and SimilarWeb to identify breakout moments 12-48 hours before mainstream saturation.

---

## Vision & Goals

### Vision Statement

**"Stop guessing what content will perform. Start making data-backed bets that maximize reach."**

The tool transforms content planning from reactive scrolling (monitoring what's already viral) to proactive opportunity hunting (catching trends as they cross from niche to mainstream).

### Product Goals

1. **Reduce meeting prep time** from 2 hours → 15 minutes for twice-weekly content planning
2. **Increase hit rate** on high-performing content by catching trends at optimal timing
3. **Provide confidence** through quantified metrics rather than gut-feel decisions
4. **Enable speed** through AI-powered summaries and content angle suggestions

### Jobs-to-be-Done

**When** dave's content team prepares for their twice-weekly planning meeting,
**They want to** confidently identify which trends to act on this week,
**So they can** create content that rides momentum waves instead of arriving late to saturated topics.

---

## Users & Personas

### Primary User: Content Planning Lead (dave)

**Role:** Runs twice-weekly content strategy meetings

**Current Workflow:**
- Manually scrolls Reddit, YouTube, Twitter/X, news sites
- Takes 1-2 hours per meeting to gather intel
- Makes decisions based on gut feel + anecdotal signals
- Often picks trends that are already saturated

**Pain Points:**
1. **Time waste:** Manual scrolling across platforms is inefficient
2. **Timing miss:** By the time they notice a trend, it's too late
3. **No confidence:** Gut-feel decisions lack data backing
4. **No quantification:** Can't say "this trend is 3x bigger than that one"

**Desired Outcomes:**
- Meeting prep in 15 minutes, not 2 hours
- Data-backed confidence in trend selection
- Catch trends before competitors
- Actual numbers to justify content bets

**Success Criteria:**
- "I can walk into the meeting with 3-5 high-confidence opportunities, each with real numbers backing why we should act NOW."

---

### Secondary User: Content Creators (team)

**Role:** Execute content based on planning meeting decisions

**Current Workflow:**
- Receive trend topics from planning meeting
- Research the trend manually to find angles
- Create content (video, article, social posts)
- Hope it's still relevant by publish time

**Pain Points:**
1. **Stale by ship time:** Trends peak before content goes live
2. **No angles:** Just told "make content about X" without context
3. **No data to cite:** Can't reference real numbers in content
4. **Competitor saturation:** Everyone's covering the same angle

**Desired Outcomes:**
- Clear content angles suggested automatically
- Real numbers to cite in content ("This trend has 2.5M views in 12 hours")
- Early enough timing that content feels fresh

**Success Criteria:**
- "I can create content that feels timely and includes data that makes it credible."

---

## Success Metrics

### Primary Metrics (Validate Core Hypothesis)

1. **Lead Time**
   - **Definition:** Hours between tool flagging a trend as "high confidence" and mainstream media coverage saturation
   - **Target:** 12-48 hours ahead of mainstream
   - **Measurement:** Track time delta between tool alert and major news outlet coverage

2. **Hit Rate**
   - **Definition:** % of "high confidence" (🔥) trends that reach >1M impressions within 72 hours
   - **Target:** >70% hit rate
   - **Measurement:** Track flagged trends and measure actual reach 72 hours later

3. **Time Saved**
   - **Definition:** Meeting prep time reduction
   - **Target:** 2 hours → 15 minutes (87.5% reduction)
   - **Measurement:** User self-report + session analytics

### Secondary Metrics (UX & Engagement)

4. **Tool Usage Frequency**
   - **Target:** 2x per week minimum (aligned with meeting cadence)
   - **Measurement:** Session analytics

5. **Confidence Score Correlation**
   - **Target:** High confidence (🔥) trends perform 3x better than low confidence (👀)
   - **Measurement:** Correlation analysis between confidence score and actual reach

6. **Content Performance Lift**
   - **Definition:** Content based on tool recommendations vs. gut-feel selections
   - **Target:** 50% increase in avg. engagement
   - **Measurement:** A/B comparison over 4-week period

---

## Core Problem

**Content teams arrive late to trends because manual platform monitoring is slow and subjective.**

By the time a trend "feels big" across multiple platforms, it's already saturated. Early signals exist (Reddit spikes, YouTube traction), but correlating them manually is impossible at speed.

**The result:** Content feels stale, competitors got there first, and opportunities are missed.

---

## Solution Approach

### Core Innovation: Cross-Platform Momentum Score

**The Insight:** Single-platform metrics don't predict "big ding" impact. **Convergence** across independent platforms does.

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

**The Output:** Confidence scores (🔥⚡👀) that tell you when to act:
- 🔥 **High Confidence:** All signals aligned - Act NOW
- ⚡ **Medium Confidence:** 2-3 signals - Monitor closely
- 👀 **Low Confidence:** 1 signal - Watch and wait

---

## Solution Components

### MVP Feature Set (Phase 1)

**Must-Have (Core Hypothesis Validation):**

1. **Cross-Platform Momentum Score Engine**
   - Collect data from Reddit, YouTube, Google Trends, SimilarWeb
   - Normalize metrics across platforms
   - Calculate composite momentum score
   - Assign confidence levels (🔥⚡👀)

2. **Trending Now Dashboard**
   - Top 10 trends ranked by momentum score
   - Display THE actual numbers for each (views, upvotes, search interest)
   - Show confidence score prominently
   - Update twice-weekly (automated collection)

3. **AI-Powered Trend Brief**
   - One-click "Explain this trend in 3 sentences"
   - Context: What is it? Why is it trending? Where is it big?
   - Auto-generated via Claude API

**Nice-to-Have (Can Wait for Phase 2):**

4. **Rising Stars Watch**
   - Trends showing consistent 3-day growth
   - Early warning system for next week's opportunities

5. **Fading Fast Alert**
   - Trends that peaked and are declining
   - Save team from late-to-party embarrassment

6. **Content Angle Suggester**
   - AI-generated content angle ideas
   - "Here are 5 ways you could spin this trend"

7. **Competitor Watch**
   - Track which competitors are covering what trends
   - Identify white space opportunities

8. **MCP Server Integration**
   - Natural language queries via Claude
   - "What memes are trending this week?"
   - "Show me TV shows with rising search interest"

### Phase 2+ (Post-MVP Validation)

9. **Historical Trend Archive**
   - Review past trends and their momentum scores
   - Learn from what worked/didn't

10. **Custom Alerts**
    - Slack/email notifications for high-confidence trends
    - Automated twice-weekly reports

11. **Trend Forecasting**
    - ML model to predict which Phase 1 trends will hit Phase 3
    - "This Reddit surge has 80% chance of going mainstream"

---

## Scope Definition

### In Scope (MVP)

✅ Reddit API integration (trend velocity)
✅ YouTube Data API integration (view velocity)
✅ Google Trends integration (search spikes)
✅ SimilarWeb API integration (traffic confirmation)
✅ Cross-Platform Momentum Score calculation
✅ Trending Now Dashboard (top 10)
✅ Confidence scores (🔥⚡👀)
✅ AI-powered trend briefs (3-sentence summaries)
✅ Twice-weekly automated data collection
✅ Basic web UI (dashboard view)

### Out of Scope (MVP)

❌ Twitter/X integration (too expensive, evaluate later)
❌ Instagram/Facebook integration (via Sprout Social in Phase 2)
❌ Real-time monitoring (twice-weekly is sufficient for MVP)
❌ Mobile app (web only for MVP)
❌ Multi-user accounts (single user for MVP)
❌ Custom alert configuration (fixed twice-weekly)
❌ Historical trend archive (focus on current trends)
❌ Competitor tracking (Phase 2)
❌ Content angle suggester (Phase 2)
❌ MCP server (Phase 2)

### Future Considerations

- **Sprout Social Integration:** If Twitter/X data proves critical, integrate via Sprout Social API (~$800/mo) instead of direct X API ($5K/mo)
- **Scaling to Teams:** Multi-user support, role-based access
- **Advanced ML:** Predictive models for trend forecasting
- **Content Performance Tracking:** Close the loop by tracking content performance based on tool recommendations

---

## Technical Constraints

### API Rate Limits
- Reddit: 60 req/min (sufficient)
- YouTube: 10K units/day (requires optimization)
- NewsAPI: Developer free tier for testing, $449/mo for production
- Google Trends: Unofficial API with throttling (60s delays)

### Data Collection Cadence
- **MVP:** Twice-weekly manual trigger
- **Phase 2:** Automated scheduled collection

### Infrastructure
- **Hosting:** Cloud-based (AWS/GCP/Railway)
- **Database:** PostgreSQL for trend data storage
- **Frontend:** Simple web dashboard (React or Next.js)
- **Backend:** Python for API integrations + scoring engine

---

## Risks & Mitigation

### High Risk: Google Trends API Reliability
- **Risk:** PyTrends is unofficial and could break
- **Mitigation:** Apply for official Google Trends API alpha; build scraping fallback

### Medium Risk: YouTube Quota Limits
- **Risk:** Could exceed 10K daily quota without optimization
- **Mitigation:** Aggressive caching, use video list endpoint (1 unit) vs search (100 units)

### Low Risk: API Changes
- **Risk:** Reddit/YouTube APIs could change unexpectedly
- **Mitigation:** Standard API versioning and monitoring

### User Adoption Risk: "Another Dashboard"
- **Risk:** Tool becomes just another dashboard dave forgets to check
- **Mitigation:** Make it FAST (15 min meeting prep), actionable (confidence scores), and habit-forming (twice-weekly cadence matches existing workflow)

---

## Success Definition

### MVP is successful if:

1. **Dave uses it twice per week for 4 consecutive weeks** (validates habit formation)
2. **70%+ of 🔥 trends reach >1M impressions within 72 hours** (validates scoring accuracy)
3. **Meeting prep time drops from 2hrs → 15 min** (validates efficiency gain)
4. **Dave says:** "I can't run content planning without this anymore" (validates indispensability)

### MVP fails if:

1. Confidence scores don't correlate with actual trend performance
2. Data collection takes >30 minutes per run (not scalable)
3. Dave stops using it after 2 weeks (not habit-forming)

---

## Go-to-Market Strategy

### Phase 1: Single User Validation (Week 1-4)
- Build for dave's team exclusively
- Iterate based on real usage feedback
- Validate core hypothesis (confidence scores predict impact)

### Phase 2: Beta Users (Week 5-8)
- Invite 3-5 similar content teams
- Refine based on diverse use cases
- Build multi-user support

### Phase 3: Productization (Month 3+)
- Add self-service signup
- Build subscription pricing model
- Scale infrastructure

**For MVP:** Focus exclusively on Phase 1 - validate with dave before expanding.

---

## Next Steps

1. ✅ **Discovery Complete** (Brainstorm, Research, Product Brief)
2. **Create PRD** - Detailed functional requirements
3. **Create Architecture** - Technical system design
4. **Create Epics & Stories** - Break into implementation tasks
5. **Build MVP** - 2-3 week development sprint

---

## Appendices

### Related Documents
- [Brainstorming Session Results](/Users/david.lee/trend-monitor/_bmad-output/analysis/brainstorming-session-2026-01-05.md)
- [Technical Research: API Validation](/Users/david.lee/trend-monitor/_bmad-output/analysis/research-technical-2026-01-05.md)

### Key Stakeholders
- **Product Owner:** dave
- **Primary User:** dave (Content Planning Lead)
- **Secondary Users:** Content creation team

### Budget
- **MVP Development:** $0 (internal development)
- **API Costs:** $0-449/mo (depends on NewsAPI tier)
- **Infrastructure:** ~$20-50/mo (hosting, database)
- **Total Year 1:** ~$1,000-6,000

---

**Product Brief Created By:** Multi-agent collaboration (John PM, Mary Analyst, Victor Innovation Strategist)
**Date:** 2026-01-05
**Status:** Ready for PRD Development
