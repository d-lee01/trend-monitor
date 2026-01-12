# Story 3.3: Trends API Endpoints

**Status:** ready-for-dev
**Epic:** 3 - Trend Analysis & Dashboard
**Story ID:** 3.3
**Created:** 2026-01-12

---

## Story

As a **frontend developer**,
I want **backend API endpoints to retrieve ranked trends**,
So that **the dashboard can display Top 10 trends and trend details**.

---

## Acceptance Criteria

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

---

## Tasks / Subtasks

### Task 1: Create Pydantic Response Schemas (AC: All)
- [ ] Create TrendListResponse schema
  - [ ] Include: id, title, confidence_level, momentum_score, platform metrics, created_at
  - [ ] Use proper UUID, datetime, and Optional types
  - [ ] Add field validation and examples
- [ ] Create TrendDetailResponse schema
  - [ ] Include all Trend model fields
  - [ ] Add computed fields for platform availability
  - [ ] Document all fields with descriptions
- [ ] Create CollectionSummaryResponse schema
  - [ ] Include: id, started_at, completed_at, status, trends_found
  - [ ] Add duration calculation
- [ ] Add schemas to `backend/app/schemas/trend.py`

### Task 2: Implement GET /trends Endpoint (AC: Top 10, Auth, Performance)
- [ ] Create `backend/app/api/trends.py` router module
- [ ] Implement GET /trends endpoint
  - [ ] Add JWT authentication dependency
  - [ ] Query latest completed collection
  - [ ] Query top 10 trends by momentum_score DESC
  - [ ] Use select() with specific columns for performance
  - [ ] Return TrendListResponse list
- [ ] Add structured logging with query duration
- [ ] Handle edge case: no completed collections
- [ ] Add router to main.py with /api prefix

### Task 3: Implement GET /trends/{id} Endpoint (AC: Detail, 404)
- [ ] Implement GET /trends/{id} endpoint
  - [ ] Add JWT authentication dependency
  - [ ] Parse UUID from path parameter
  - [ ] Query Trend by id
  - [ ] Raise HTTPException 404 if not found
  - [ ] Return TrendDetailResponse
- [ ] Add structured logging
- [ ] Include all platform metrics in response

### Task 4: Implement GET /collections/latest Endpoint (AC: Latest collection)
- [ ] Implement GET /collections/latest endpoint
  - [ ] Add JWT authentication dependency
  - [ ] Query latest completed collection with ORDER BY completed_at DESC LIMIT 1
  - [ ] Count related trends using func.count()
  - [ ] Calculate duration
  - [ ] Return CollectionSummaryResponse
- [ ] Handle edge case: no completed collections (return 404)
- [ ] Add structured logging

### Task 5: API Integration Tests (AC: All endpoints, auth, errors)
- [ ] Create `backend/tests/test_api/test_trends_endpoints.py`
- [ ] Test GET /trends endpoint
  - [ ] Test successful response with 10 trends
  - [ ] Test response format and field types
  - [ ] Test ordering by momentum_score
  - [ ] Test empty database scenario
  - [ ] Test unauthorized access (no JWT)
  - [ ] Test query performance (<500ms)
- [ ] Test GET /trends/{id} endpoint
  - [ ] Test successful detail retrieval
  - [ ] Test 404 for non-existent ID
  - [ ] Test unauthorized access
  - [ ] Test all fields present in response
- [ ] Test GET /collections/latest endpoint
  - [ ] Test successful response
  - [ ] Test trends_found count accuracy
  - [ ] Test 404 when no collections exist
  - [ ] Test unauthorized access
- [ ] All tests use async fixtures and real database session

---

## Dev Notes

### API Architecture Patterns

**Router Organization:**
- Create new router module: `backend/app/api/trends.py`
- Use APIRouter with tags=["trends"]
- Mount in `main.py` with prefix="/api"

**Authentication Pattern:**
```python
from app.core.dependencies import get_current_user
from app.models.user import User

@router.get("/trends")
async def get_trends(
    current_user: User = Depends(get_current_user)
):
    # Endpoint automatically requires JWT authentication
```

**Database Query Pattern (from Stories 3.1, 3.2):**
```python
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, func
from app.database import get_db

@router.get("/trends")
async def get_trends(
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    # Get latest collection
    collection_stmt = select(DataCollection)\
        .where(DataCollection.status == 'completed')\
        .order_by(DataCollection.completed_at.desc())\
        .limit(1)
    collection_result = await db.execute(collection_stmt)
    collection = collection_result.scalar_one_or_none()

    if not collection:
        raise HTTPException(404, "No completed collections found")

    # Get top 10 trends
    trends_stmt = select(Trend)\
        .where(Trend.collection_id == collection.id)\
        .order_by(Trend.momentum_score.desc())\
        .limit(10)
    trends_result = await db.execute(trends_stmt)
    trends = trends_result.scalars().all()

    return trends
```

**Response Schema Pattern:**
```python
from pydantic import BaseModel, Field
from uuid import UUID
from datetime import datetime
from typing import Optional

class TrendListResponse(BaseModel):
    id: UUID
    title: str
    confidence_level: str = Field(..., description="high, medium, or low")
    momentum_score: float
    reddit_score: Optional[int] = None
    youtube_views: Optional[int] = None
    google_trends_interest: Optional[int] = None
    similarweb_traffic: Optional[int] = None
    created_at: datetime

    class Config:
        from_attributes = True  # Enables ORM mode for SQLAlchemy models
```

**Error Handling Pattern:**
```python
from fastapi import HTTPException, status

# 404 Not Found
if not trend:
    raise HTTPException(
        status_code=status.HTTP_404_NOT_FOUND,
        detail="Trend not found"
    )

# 401 Unauthorized - handled automatically by get_current_user dependency
```

**Structured Logging Pattern (from Story 3.2):**
```python
import logging
logger = logging.getLogger(__name__)

start_time = datetime.now(timezone.utc)
# ... perform query ...
duration = (datetime.now(timezone.utc) - start_time).total_seconds()

logger.info(
    "Trends retrieved",
    extra={
        "event": "trends_retrieved",
        "user": current_user.username,
        "count": len(trends),
        "duration_ms": round(duration * 1000, 2)
    }
)
```

### Database Indexes (Already Exist from Story 1.2)

The following indexes are already created and will optimize queries:
- `idx_momentum_score_desc` on trends.momentum_score DESC
- `idx_created_at_desc` on trends.created_at DESC
- `idx_confidence_level` on trends.confidence_level
- Index on data_collections.completed_at (implicit from queries)
- Index on trends.collection_id (foreign key)

### File Structure

```
backend/
├── app/
│   ├── api/
│   │   ├── __init__.py
│   │   ├── collection.py (exists - from Story 2.6)
│   │   └── trends.py (NEW - create this)
│   ├── schemas/
│   │   ├── __init__.py
│   │   ├── collection.py (exists)
│   │   └── trend.py (NEW - create this)
│   ├── models/
│   │   ├── trend.py (exists)
│   │   └── data_collection.py (exists)
│   └── main.py (modify to add trends router)
└── tests/
    └── test_api/
        ├── __init__.py (exists)
        ├── test_score_integration.py (exists - from Story 3.2)
        └── test_trends_endpoints.py (NEW - create this)
```

### Testing Strategy

**Test Database Setup (from Story 3.2 learnings):**
- Use async test fixtures with real database
- Create test data in setup, clean up in teardown
- Test with actual SQLAlchemy models, not mocks
- Use `pytest.mark.asyncio` for async tests

**Test Coverage Requirements:**
- All endpoints (GET /trends, GET /trends/{id}, GET /collections/latest)
- Success cases with various data scenarios
- Error cases (404, 401, empty database)
- Edge cases (no collections, no trends, invalid UUIDs)
- Performance validation (<500ms query time)
- Response format validation

### Performance Considerations

**Query Optimization:**
1. Use indexes for ORDER BY momentum_score DESC
2. LIMIT 10 to reduce result set size
3. Select only needed columns (not SELECT *)
4. Subquery for latest collection is efficient (single row)
5. Log query durations to monitor performance

**Expected Performance:**
- GET /trends: <200ms (10 rows with index)
- GET /trends/{id}: <50ms (single row by primary key)
- GET /collections/latest: <100ms (single row + count)

### Authentication & Authorization

**JWT Token Validation:**
- All endpoints require `current_user: User = Depends(get_current_user)`
- Token validated automatically by FastAPI dependency
- Returns 401 if token missing, invalid, or expired
- No additional authorization logic needed (single-user MVP)

**Security Headers (already configured in Story 1.1):**
- CORS configured for frontend origin only
- HTTPS enforced
- Security headers: X-Content-Type-Options, X-Frame-Options, X-XSS-Protection

### API Response Examples

**GET /trends (Success 200):**
```json
[
  {
    "id": "a1b2c3d4-...",
    "title": "Viral TikTok Dance Challenge",
    "confidence_level": "high",
    "momentum_score": 87.5,
    "reddit_score": 15234,
    "youtube_views": 2534000,
    "google_trends_interest": 87,
    "similarweb_traffic": 1250000,
    "created_at": "2026-01-12T07:45:00Z"
  },
  // ... 9 more trends
]
```

**GET /trends/{id} (Success 200):**
```json
{
  "id": "a1b2c3d4-...",
  "title": "Viral TikTok Dance Challenge",
  "collection_id": "xyz123...",
  "created_at": "2026-01-12T07:45:00Z",
  "reddit_score": 15234,
  "reddit_comments": 892,
  "reddit_upvote_ratio": 0.95,
  "reddit_subreddit": "videos",
  "youtube_views": 2534000,
  "youtube_likes": 125000,
  "youtube_channel": "DanceVibes",
  "google_trends_interest": 87,
  "google_trends_related_queries": {"queries": ["dance", "challenge"]},
  "similarweb_traffic": 1250000,
  "similarweb_sources": {"social": 0.6, "direct": 0.4},
  "reddit_velocity_score": 78.5,
  "youtube_traction_score": 82.3,
  "google_trends_spike_score": 85.1,
  "similarweb_bonus_applied": true,
  "momentum_score": 87.5,
  "confidence_level": "high",
  "ai_brief": null,
  "ai_brief_generated_at": null
}
```

**GET /collections/latest (Success 200):**
```json
{
  "id": "xyz123...",
  "started_at": "2026-01-12T07:30:00Z",
  "completed_at": "2026-01-12T07:52:34Z",
  "status": "completed",
  "trends_found": 47,
  "duration_minutes": 22.57
}
```

**Error Responses:**

404 Not Found (no collections):
```json
{
  "detail": "No completed collections found"
}
```

404 Not Found (trend not found):
```json
{
  "detail": "Trend not found"
}
```

401 Unauthorized:
```json
{
  "detail": "Not authenticated"
}
```

### Integration with Frontend (Story 3.4)

**API Base URL:**
- Backend: `http://localhost:8000/api` (dev) or `https://<railway-domain>/api` (prod)
- Frontend will use these endpoints in Story 3.4

**Authentication Header:**
```javascript
const token = localStorage.getItem('auth_token');
const response = await fetch(`${API_URL}/trends`, {
  headers: {
    'Authorization': `Bearer ${token}`,
    'Content-Type': 'application/json'
  }
});
```

### Dependencies (Already Installed)

All required dependencies already installed from previous stories:
- `fastapi` - Web framework
- `sqlalchemy[asyncio]` - Database ORM
- `pydantic` - Data validation
- `python-jose[cryptography]` - JWT tokens
- `pytest-asyncio` - Async testing

No new dependencies needed for this story.

### Previous Story Intelligence

**From Story 3.2 (Score Calculation Integration):**

Key Learnings:
1. **Error Handling Pattern**: Added try/except around all database operations to prevent batch failures
2. **Collection Validation**: Always validate collection_id exists before querying related data
3. **Type Hints**: Use specific types like `Dict[str, Union[int, float]]` instead of generic `dict`
4. **Structured Logging**: Use `extra` dict for JSON logging, avoid f-strings in log messages
5. **Database Constraints**: CHECK constraints must be respected (e.g., confidence_level values)
6. **Test Strategy**: Mock-based tests work for logic, but at least one real DB test needed
7. **Performance**: Batch operations with single commit for efficiency

Code Patterns Established:
- Collection validation before related queries
- Comprehensive error handling with specific error messages
- Structured logging with event, duration, counts
- Response dictionaries with typed returns

**From Story 2.6 (Manual Collection Trigger):**

API Patterns:
- Router organization: `backend/app/api/collection.py`
- Background tasks for long-running operations
- 409 Conflict for duplicate operations
- Polling pattern for status checks
- Response schemas in `backend/app/schemas/collection.py`

### Project Context Reference

**Database Schema (from Story 1.2):**
- `trends` table has all necessary columns for API responses
- Foreign key: trends.collection_id → data_collections.id
- Indexes optimize queries by momentum_score and created_at
- CHECK constraint: confidence_level IN ('high', 'medium', 'low')

**Authentication (from Story 1.3):**
- JWT tokens with 7-day expiration
- `get_current_user()` dependency validates tokens
- Returns User object with username and id
- Automatically returns 401 for invalid/missing tokens

**Architecture Decisions (from Architecture Document):**
- Three-tier architecture: Presentation → Application → Data
- FastAPI for REST API with async/await
- SQLAlchemy with AsyncSession for database
- Pydantic for request/response validation
- Structured JSON logging for all API calls
- CORS configured for frontend origin only

---

## Dev Agent Record

### Agent Model Used

Claude Sonnet 4.5 (claude-sonnet-4-5-20250929)

### Completion Notes List

(To be filled during implementation)

### File List

**Files to Create:**
- `backend/app/api/trends.py` - Trends API router
- `backend/app/schemas/trend.py` - Pydantic response schemas
- `backend/tests/test_api/test_trends_endpoints.py` - API endpoint tests

**Files to Modify:**
- `backend/app/main.py` - Add trends router
- `backend/app/schemas/__init__.py` - Export new schemas

**Files Referenced:**
- `backend/app/models/trend.py` - Trend model
- `backend/app/models/data_collection.py` - DataCollection model
- `backend/app/core/dependencies.py` - Authentication dependencies
- `backend/app/database.py` - Database session
