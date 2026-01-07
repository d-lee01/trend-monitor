---
stepsCompleted: [1, 2]
inputDocuments: []
session_topic: 'Building a quantified trend monitoring system'
session_goals: '1. Attach real numbers to trends (views, engagement, reach, velocity), 2. Features that surface highest-impact opportunities with data, 3. Make decisions based on measurable signals'
selected_approach: 'AI-Recommended Techniques'
techniques_used: ['First Principles Thinking', 'Morphological Analysis', 'Resource Constraints']
ideas_generated: []
context_file: ''
---

# Brainstorming Session Results

**Facilitator:** dave
**Date:** 2026-01-05

## Session Overview

**Topic:** Building a quantified trend monitoring system

**Goals:**
1. Attach real numbers to trends (views, engagement, reach, velocity)
2. Features that surface the highest-impact opportunities with data to back it up
3. Make "big ding" decisions based on measurable signals, not gut feel

### Session Setup

We're focusing on creating a trend monitoring tool that goes beyond just listing "what's trending" to providing quantifiable metrics. The key insight is being able to say "This TV show has 5M viewers" or "This soundbite got 20M impressions in 24 hours" - real numbers that enable fast, confident decision-making for content planning.

## Technique Selection

**Approach:** AI-Recommended Techniques

**Recommended Techniques:**
1. **First Principles Thinking** - Strip away assumptions about data sources and rebuild from fundamental truths
2. **Morphological Analysis** - Systematically map what we can quantify across different dimensions
3. **Resource Constraints** - Focus on highest-impact features for non-technical fast execution

**AI Rationale:** This sequence moves from data discovery → quantification framework → feature prioritization, designed for rapid practical insights.

---

## Phase 1: First Principles Thinking - Multi-Agent Debate Results

**Participants:** Winston (Architect), Mary (Analyst), John (PM), Victor (Innovation Strategist)

### API Metrics Available:

**Reddit API:**
- Post score (upvotes - downvotes)
- Comment count and velocity
- Subreddit subscriber count
- Post age (for velocity calculation)
- Crossposts (amplification indicator)

**YouTube Data API:**
- View count and view velocity
- Like/dislike ratio
- Comment count
- Channel subscriber count (authority signal)

**NewsAPI:**
- Article count by topic (limited - no engagement metrics)
- Publication source for authority inference

**Google Trends:**
- Relative search interest (0-100 scale)
- Interest over time (spike detection)
- Geographic distribution
- Related queries

**SimilarWeb:**
- Website traffic (absolute numbers)
- Traffic sources
- Engagement metrics (bounce rate, pages/visit)
- Geographic data

### The "Big Ding" Predictor Discovery:

**CORE INSIGHT:** Single metrics don't predict impact - **CONVERGENCE** across platforms does.

**Cross-Platform Momentum Score Formula:**
`(Reddit Velocity × YouTube Traction × Google Trends Spike) + SimilarWeb Mainstream Bonus`

**The Pattern:**
1. **Phase 1:** Niche Ignition (Reddit/niche communities)
2. **Phase 2:** Cross-Platform Jump (YouTube picks it up) ← **YOUR WINDOW**
3. **Phase 3:** Search Explosion (Google Trends spike) ← **YOUR WINDOW**
4. **Phase 4:** Mainstream Traffic (SimilarWeb confirms)

**Act in Phase 2-3 for maximum "big ding" impact.**

### Indispensable Features Identified:

**For Twice-Weekly Meetings, Answer 3 Questions:**
1. What should we talk about THIS WEEK?
2. What's gaining momentum for NEXT WEEK?
3. What just died? (avoid being late)

**Priority Features:**
1. **Trending Now Dashboard** - Top 10 cross-platform surges with THE actual numbers
2. **Rising Stars Watch** - Consistent growth over 3+ days (early signal)
3. **Fading Fast Alert** - Peaked and declining (save from embarrassment)
4. **Confidence Scores** - 🔥 High (all signals) / ⚡ Medium (2-3 signals) / 👀 Low (1 signal)
5. **One-Click AI Brief** - Explain trend in 3 sentences
6. **Content Angle Suggester** - "How could we spin this?"
7. **Competitor Watch** - "Who's already covering this?"

### Technical Approach:
- Build normalization layer for cross-platform metric comparison
- Calculate composite velocity scores
- Detect signal convergence across multiple platforms
- Authority-weighted reach (big channel vs small channel)

**Key Principle:** Not just collecting numbers - finding CONVERGENCE. When multiple independent signals align → that's your "big ding" predictor.
