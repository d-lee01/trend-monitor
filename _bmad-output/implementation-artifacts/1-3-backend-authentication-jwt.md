# Story 1.3: Backend Authentication with JWT

**Status:** in-progress
**Epic:** 1 - Foundation & Authentication
**Story ID:** 1.3
**Created:** 2026-01-08

---

## Story

As **dave (content planning lead)**,
I want **to log into the system with username/password and receive a JWT token**,
So that **I can access protected API endpoints securely for 7 days**.

## Acceptance Criteria

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

---

## Developer Context & Implementation Guide

### 🎯 Epic Context

This story is the **third story** in Epic 1: Foundation & Authentication. It implements JWT-based authentication enabling secure access to protected API endpoints.

**Epic Goal:** Establish secure, deployed infrastructure with authentication, database, and foundational backend/frontend architecture.

**User Outcome:** dave can log into the trend-monitor dashboard securely with username/password, and the system is deployed on Railway with PostgreSQL database, FastAPI backend, and Next.js frontend operational.

**Dependencies:**
- ✅ **Story 1.1 (Project Setup & Railway Deployment)** - COMPLETE
  - FastAPI backend deployed
  - Environment variables configured (JWT_SECRET_KEY already set)
  - python-jose[cryptography]==3.3.0 and passlib[bcrypt]==1.7.4 installed
- ✅ **Story 1.2 (Database Schema Creation)** - COMPLETE
  - Users table created with id, username, password_hash, created_at, last_login
  - Database connection available via asyncpg

**Dependent Stories (blocked by this story):**
- **Story 1.4 (Frontend Setup with Login UI)** - Needs /auth/login and /auth/me endpoints
- **Story 2.6 (Manual Data Collection Trigger)** - Needs JWT authentication middleware
- **All future API endpoints** - Will require JWT authentication

---

## Technical Requirements

### Architecture Decision References

This story implements **AD-7: Authentication via JWT**:

#### Authentication Technology Stack
- **JWT Library:** python-jose[cryptography] 3.3.0 (with HS256 algorithm)
- **Password Hashing:** passlib[bcrypt] 1.7.4 (minimum 12 rounds)
- **Token Expiration:** 7 days (configured in JWT_EXPIRATION_DAYS environment variable)
- **HTTP Authentication:** OAuth2 Password Bearer pattern
- **Session Management:** Stateless JWT tokens (no server-side session storage)

#### Security Requirements (from Architecture Document)

**From AD-7 (Authentication via JWT):**
- JWT tokens with 7-day expiration
- Secure password hashing (bcrypt with at least 12 rounds)
- JWT secret stored in environment variables (never in code)
- Token validation on every protected endpoint

**From AD-4 (Security-First Design):**
- HTTPS enforced (already handled by Railway)
- Security headers configured (already in main.py middleware)
- Protection against common vulnerabilities (SQL injection via SQLAlchemy ORM, XSS via FastAPI auto-escaping)
- JWT secret key managed via Railway environment variables

**From AD-9 (Error Handling):**
- Clear error messages for authentication failures (401 Unauthorized)
- Distinguishable errors: "Token expired", "Invalid token", "Not authenticated"
- No information leakage in error messages (don't reveal if user exists)

---

## Implementation Tasks

### Task 1: Create Authentication Schemas

**Acceptance Criteria:** AC #2 (login request/response structure), AC #6 (user profile structure)

**Subtasks:**
- [x] Create `backend/app/schemas/__init__.py` module
- [x] Create `backend/app/schemas/auth.py` with Pydantic models:
  ```python
  from pydantic import BaseModel, Field

  class LoginRequest(BaseModel):
      username: str = Field(..., min_length=3, max_length=100)
      password: str = Field(..., min_length=8)

  class TokenResponse(BaseModel):
      access_token: str
      token_type: str = "bearer"

  class UserProfile(BaseModel):
      username: str
      user_id: str

      class Config:
          from_attributes = True  # SQLAlchemy 2.0 compatibility
  ```
- [x] Import schemas in `backend/app/schemas/__init__.py`

### Task 2: Implement Password Hashing Utilities

**Acceptance Criteria:** AC #3 (bcrypt password verification), AC #11 (12+ rounds)

**Subtasks:**
- [x] Create `backend/app/core/__init__.py` module
- [x] Create `backend/app/core/security.py` with password utilities:
  ```python
  from passlib.context import CryptContext

  # bcrypt with 12 rounds (default is 12, can configure up to 14 for extra security)
  pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto", bcrypt__rounds=12)

  def verify_password(plain_password: str, hashed_password: str) -> bool:
      """Verify plain password against hashed password using bcrypt."""
      return pwd_context.verify(plain_password, hashed_password)

  def get_password_hash(password: str) -> str:
      """Hash password using bcrypt with 12 rounds."""
      return pwd_context.hash(password)
  ```
- [x] Test password hashing is working: `get_password_hash("test123")` should return different hash each time but `verify_password()` should match

### Task 3: Implement JWT Token Creation and Validation

**Acceptance Criteria:** AC #4 (JWT generation with HS256), AC #7 (token expiration check)

**Subtasks:**
- [x] Add JWT utilities to `backend/app/core/security.py`:
  ```python
  from datetime import datetime, timedelta
  from typing import Optional
  from jose import jwt, JWTError
  from app.config import settings

  def create_access_token(data: dict, expires_delta: Optional[timedelta] = None) -> str:
      """Create JWT access token with expiration."""
      to_encode = data.copy()
      if expires_delta:
          expire = datetime.utcnow() + expires_delta
      else:
          expire = datetime.utcnow() + timedelta(days=settings.jwt_expiration_days)

      to_encode.update({"exp": expire})
      encoded_jwt = jwt.encode(to_encode, settings.jwt_secret_key, algorithm=settings.jwt_algorithm)
      return encoded_jwt

  def decode_access_token(token: str) -> Optional[dict]:
      """Decode and validate JWT token. Returns payload or None if invalid."""
      try:
          payload = jwt.decode(token, settings.jwt_secret_key, algorithms=[settings.jwt_algorithm])
          return payload
      except JWTError:
          return None
  ```
- [x] Verify JWT_SECRET_KEY and JWT_ALGORITHM are in config.py (already configured from Story 1.1)
- [x] Test token creation and decoding locally

### Task 4: Create Authentication Dependency for Protected Routes

**Acceptance Criteria:** AC #6 (decode JWT and return user), AC #8-9 (error handling for expired/invalid tokens)

**Subtasks:**
- [x] Create `backend/app/core/dependencies.py`:
  ```python
  from fastapi import Depends, HTTPException, status
  from fastapi.security import OAuth2PasswordBearer
  from sqlalchemy.ext.asyncio import AsyncSession
  from sqlalchemy import select

  from app.core.security import decode_access_token
  from app.database import get_db
  from app.models.user import User

  oauth2_scheme = OAuth2PasswordBearer(tokenUrl="/auth/login")

  async def get_current_user(
      token: str = Depends(oauth2_scheme),
      db: AsyncSession = Depends(get_db)
  ) -> User:
      """Dependency to get current authenticated user from JWT token."""
      credentials_exception = HTTPException(
          status_code=status.HTTP_401_UNAUTHORIZED,
          detail="Invalid token",
          headers={"WWW-Authenticate": "Bearer"},
      )

      payload = decode_access_token(token)
      if payload is None:
          raise credentials_exception

      username: str = payload.get("sub")
      if username is None:
          raise credentials_exception

      # Check if token expired (jose library handles this in decode, but explicit check for custom message)
      exp = payload.get("exp")
      if exp and datetime.utcnow().timestamp() > exp:
          raise HTTPException(
              status_code=status.HTTP_401_UNAUTHORIZED,
              detail="Token expired",
              headers={"WWW-Authenticate": "Bearer"},
          )

      # Fetch user from database
      result = await db.execute(select(User).where(User.username == username))
      user = result.scalar_one_or_none()

      if user is None:
          raise credentials_exception

      return user
  ```

### Task 5: Create Authentication API Endpoints

**Acceptance Criteria:** AC #2 (POST /auth/login), AC #6 (GET /auth/me)

**Subtasks:**
- [x] Create `backend/app/api/auth.py` router:
  ```python
  from datetime import datetime
  from fastapi import APIRouter, Depends, HTTPException, status
  from fastapi.security import OAuth2PasswordRequestForm
  from sqlalchemy.ext.asyncio import AsyncSession
  from sqlalchemy import select

  from app.database import get_db
  from app.models.user import User
  from app.schemas.auth import TokenResponse, UserProfile
  from app.core.security import verify_password, create_access_token
  from app.core.dependencies import get_current_user

  router = APIRouter(prefix="/auth", tags=["authentication"])

  @router.post("/login", response_model=TokenResponse)
  async def login(
      form_data: OAuth2PasswordRequestForm = Depends(),
      db: AsyncSession = Depends(get_db)
  ):
      """Authenticate user and return JWT access token."""
      # Query user by username
      result = await db.execute(select(User).where(User.username == form_data.username))
      user = result.scalar_one_or_none()

      # Verify user exists and password matches
      if not user or not verify_password(form_data.password, user.password_hash):
          raise HTTPException(
              status_code=status.HTTP_401_UNAUTHORIZED,
              detail="Invalid username or password",
              headers={"WWW-Authenticate": "Bearer"},
          )

      # Update last_login
      user.last_login = datetime.utcnow()
      await db.commit()

      # Create JWT token with username in 'sub' claim
      access_token = create_access_token(data={"sub": user.username})

      return TokenResponse(access_token=access_token, token_type="bearer")

  @router.get("/me", response_model=UserProfile)
  async def get_current_user_profile(
      current_user: User = Depends(get_current_user)
  ):
      """Get current authenticated user profile."""
      return UserProfile(
          username=current_user.username,
          user_id=str(current_user.id)
      )
  ```
- [x] Register auth router in `backend/app/main.py`:
  ```python
  from app.api import auth

  app.include_router(auth.router)
  ```

### Task 6: Create Bootstrap User Script

**Acceptance Criteria:** AC #2 (user "dave" can login with password)

**Subtasks:**
- [x] Create `backend/scripts/create_user.py`:
  ```python
  """Create bootstrap user 'dave' with secure password."""
  import asyncio
  from app.database import AsyncSessionLocal
  from app.models.user import User
  from app.core.security import get_password_hash
  from sqlalchemy import select

  async def create_bootstrap_user():
      """Create user 'dave' if doesn't exist."""
      async with AsyncSessionLocal() as session:
          # Check if user exists
          result = await session.execute(select(User).where(User.username == "dave"))
          existing_user = result.scalar_one_or_none()

          if existing_user:
              print("User 'dave' already exists")
              return

          # Create new user
          # NOTE: Replace this password with actual secure password
          password = "changeme123"  # TODO: Get from environment or user input
          hashed_password = get_password_hash(password)

          user = User(
              username="dave",
              password_hash=hashed_password
          )

          session.add(user)
          await session.commit()
          print(f"Created user 'dave' with password '{password}'")
          print("⚠️  IMPORTANT: Change this password immediately after first login!")

  if __name__ == "__main__":
      asyncio.run(create_bootstrap_user())
  ```
- [x] Run script locally: `cd backend && python scripts/create_user.py`
- [x] Run script on Railway after deployment: `railway run python scripts/create_user.py`
- [x] Verify user created: Check database or test login endpoint

### Task 7: Update Dockerfile to Create Bootstrap User on Deployment

**Acceptance Criteria:** Ensure user exists on Railway deployment

**Subtasks:**
- [x] Update `Dockerfile` CMD to create user before starting app:
  ```dockerfile
  CMD python scripts/create_user.py && alembic upgrade head || echo "Migration failed - starting app anyway..." && uvicorn app.main:app --host 0.0.0.0 --port ${PORT:-8000}
  ```
- [x] Test on Railway deployment - verify user 'dave' exists after deploy

### Task 8: Test Authentication Flow End-to-End

**Acceptance Criteria:** All ACs verified

**Subtasks:**
- [ ] Test POST /auth/login with valid credentials:
  ```bash
  curl -X POST https://trend-monitor-production.up.railway.app/auth/login \
    -H "Content-Type: application/x-www-form-urlencoded" \
    -d "username=dave&password=changeme123"
  # Should return: {"access_token": "<jwt>", "token_type": "bearer"}
  ```
- [ ] Test GET /auth/me with valid token:
  ```bash
  curl https://trend-monitor-production.up.railway.app/auth/me \
    -H "Authorization: Bearer <jwt_token>"
  # Should return: {"username": "dave", "user_id": "<uuid>"}
  ```
- [ ] Test GET /auth/me with missing Authorization header:
  ```bash
  curl https://trend-monitor-production.up.railway.app/auth/me
  # Should return 401: {"detail": "Not authenticated"}
  ```
- [ ] Test GET /auth/me with invalid token:
  ```bash
  curl https://trend-monitor-production.up.railway.app/auth/me \
    -H "Authorization: Bearer invalid_token"
  # Should return 401: {"detail": "Invalid token"}
  ```
- [ ] Test POST /auth/login with wrong password:
  ```bash
  curl -X POST https://trend-monitor-production.up.railway.app/auth/login \
    -H "Content-Type: application/x-www-form-urlencoded" \
    -d "username=dave&password=wrongpassword"
  # Should return 401: {"detail": "Invalid username or password"}
  ```
- [ ] Verify token expiration (wait 7 days or manually test with modified expiration time)

---

## Architecture Compliance

### Security Requirements (REQUIRED)

✅ **JWT Secret Key Management:**
- JWT_SECRET_KEY stored in Railway environment variables
- Already configured in Story 1.1 with: `openssl rand -hex 32`
- Never hardcoded in source code

✅ **Password Hashing:**
- bcrypt algorithm with 12 rounds minimum
- Passwords never stored in plain text
- Password verification uses constant-time comparison (handled by passlib)

✅ **Token Security:**
- HS256 algorithm (HMAC with SHA-256)
- 7-day expiration (configurable via JWT_EXPIRATION_DAYS)
- Stateless tokens (no server-side session storage)

✅ **Error Handling:**
- 401 Unauthorized for authentication failures
- Clear error messages without information leakage
- Distinguishable errors: "Token expired", "Invalid token", "Not authenticated"

✅ **API Security:**
- Protected endpoints use `Depends(get_current_user)` dependency
- OAuth2 Password Bearer pattern (industry standard)
- HTTPS enforced by Railway (already configured)

### Database Queries

- Use SQLAlchemy ORM for all database queries (prevents SQL injection)
- Async/await pattern with AsyncSession from Story 1.2
- Example: `await db.execute(select(User).where(User.username == username))`

---

## Library & Framework Requirements

### Python Version
- **Required:** Python 3.10+
- Railway uses Python 3.10-slim (from Dockerfile)

### Key Dependencies & Versions

| Library | Version | Purpose | Already Installed? |
|---------|---------|---------|-------------------|
| python-jose[cryptography] | 3.3.0 | JWT token encoding/decoding | ✅ Yes (Story 1.1) |
| passlib[bcrypt] | 1.7.4 | Password hashing with bcrypt | ✅ Yes (Story 1.1) |
| python-multipart | 0.0.6 | Form data parsing (OAuth2PasswordRequestForm) | ✅ Yes (Story 1.1) |
| fastapi | 0.104.1 | Web framework with OAuth2 support | ✅ Yes (Story 1.1) |
| sqlalchemy | 2.0.23 | ORM for database queries | ✅ Yes (Story 1.1) |

### Why These Versions?

**python-jose 3.3.0:**
- Mature, stable JWT library for Python
- Supports multiple algorithms (HS256, RS256, ES256)
- Handles token expiration automatically
- **Note:** FastAPI docs now recommend PyJWT, but python-jose is already installed and fully compatible

**passlib 1.7.4 with bcrypt:**
- Industry-standard password hashing
- bcrypt is specifically designed for passwords (slow, resistant to brute-force)
- 12 rounds = 2^12 iterations = good balance of security vs performance
- **Note:** Modern recommendation is Argon2id (via pwdlib), but bcrypt is excellent for MVP

---

## File Structure Requirements

### New Files to Create

```
backend/
├── app/
│   ├── api/
│   │   ├── __init__.py      (already exists)
│   │   └── auth.py          ← CREATE: Authentication endpoints
│   ├── core/
│   │   ├── __init__.py      ← CREATE: Core utilities module
│   │   ├── security.py      ← CREATE: Password hashing, JWT utilities
│   │   └── dependencies.py  ← CREATE: FastAPI dependencies (get_current_user)
│   ├── schemas/
│   │   ├── __init__.py      ← CREATE: Pydantic schemas module
│   │   └── auth.py          ← CREATE: LoginRequest, TokenResponse, UserProfile
│   ├── models/
│   │   └── user.py          (already exists from Story 1.2)
│   ├── main.py              ← MODIFY: Register auth router
│   ├── config.py            (already exists with JWT settings)
│   └── database.py          (already exists with async session)
├── scripts/
│   └── create_user.py       ← CREATE: Bootstrap user creation script
└── Dockerfile               ← MODIFY: Add user creation to CMD
```

### Existing Files to Modify

**backend/app/main.py:**
- Add `from app.api import auth`
- Add `app.include_router(auth.router)`

**Dockerfile:**
- Update CMD to run `python scripts/create_user.py` before starting app

---

## Testing Requirements

### Manual Testing Checklist (MVP)

- [ ] POST /auth/login returns JWT token with valid credentials
- [ ] POST /auth/login returns 401 with invalid credentials
- [ ] GET /auth/me returns user profile with valid token
- [ ] GET /auth/me returns 401 with missing token
- [ ] GET /auth/me returns 401 with invalid token
- [ ] GET /auth/me returns 401 with expired token (test manually)
- [ ] JWT_SECRET_KEY loaded from environment variable
- [ ] Password hashed with bcrypt (12 rounds minimum)
- [ ] Bootstrap user 'dave' exists in database after deployment

### Automated Testing (Optional for MVP, Recommended)

Consider adding pytest tests (optional for this story, can be deferred):
```python
# backend/tests/test_auth.py (OPTIONAL)
import pytest
from httpx import AsyncClient
from app.main import app

@pytest.mark.asyncio
async def test_login_success():
    async with AsyncClient(app=app, base_url="http://test") as client:
        response = await client.post(
            "/auth/login",
            data={"username": "dave", "password": "changeme123"}
        )
        assert response.status_code == 200
        data = response.json()
        assert "access_token" in data
        assert data["token_type"] == "bearer"

@pytest.mark.asyncio
async def test_login_invalid_credentials():
    async with AsyncClient(app=app, base_url="http://test") as client:
        response = await client.post(
            "/auth/login",
            data={"username": "dave", "password": "wrongpassword"}
        )
        assert response.status_code == 401
        assert "Invalid username or password" in response.json()["detail"]
```

---

## Previous Story Intelligence

### Learnings from Story 1.2 (Database Schema Creation)

**✅ Successful Patterns:**
1. **SQLAlchemy 2.0 Async Patterns:**
   - Use `Mapped[type]` with `mapped_column()` for type-safe columns
   - Use `AsyncAttrs` mixin for async relationship loading
   - Use `async with AsyncSessionLocal() as session:` pattern

2. **Alembic Migrations:**
   - Auto-generate migrations work well: `alembic revision --autogenerate -m "message"`
   - Test migrations locally before deploying
   - Migrations run automatically on Railway via Dockerfile CMD

3. **Railway Deployment:**
   - DATABASE_URL automatically converted to asyncpg format in config.py
   - Graceful error handling allows app to start even if migrations fail
   - Use `railway run` for one-time scripts (like user creation)

**⚠️ Blockers from Story 1.2:**
- **RESOLVED:** Railway deployment was failing due to strict error handling in alembic/env.py
  - **Solution:** Made error handling graceful - app now starts even if migrations fail
  - **Lesson:** Allow app to start with degraded functionality for easier debugging

**🔍 Files Modified in Previous Stories:**
- backend/app/models/user.py (User model with password_hash field exists)
- backend/app/config.py (JWT_SECRET_KEY already configured)
- backend/app/database.py (AsyncSession pattern established)
- backend/app/main.py (FastAPI app setup, middleware, security headers)

**🎯 Patterns to Follow:**
1. Create modular structure: separate schemas, core utilities, API routes
2. Use async/await throughout (consistency with existing codebase)
3. Follow SQLAlchemy 2.0 patterns (not legacy query API)
4. Test locally before deploying to Railway
5. Use Railway environment variables for secrets (JWT_SECRET_KEY already set)

---

## Git Intelligence Summary

**Recent Commits Analysis:**
- `b760c28`: Added Alembic migrations for database schema
- `f39d30a`: Converted Railway PostgreSQL URL to asyncpg format
- `a6b02c9`: Handled missing DATABASE_URL gracefully
- `9843894`: Code review fixes - config system, error handling, tests

**Key Patterns Observed:**
1. **Error Handling Priority:** Multiple commits focused on graceful degradation
2. **Railway-Specific Fixes:** URL format conversion, environment handling
3. **Testing Added:** pytest and httpx added for testing
4. **Configuration Management:** Settings imported and used throughout app

**Code Conventions Established:**
- F-strings for string formatting
- Type hints with `Mapped[type]` (SQLAlchemy 2.0)
- Async/await for all I/O operations
- Structured logging with print statements (JSON logging not yet implemented)
- Environment variables via pydantic_settings

---

## Latest Technical Information (2026 Best Practices)

### Modern JWT Best Practices

**Current Recommendations:**
- **FastAPI Evolution:** FastAPI documentation now recommends PyJWT over python-jose for 2026
  - However, python-jose is already installed and fully compatible
  - **Decision:** Use existing python-jose 3.3.0 for MVP (avoid unnecessary changes)
  - **Future:** Consider migrating to PyJWT in Phase 2

**Security Best Practices:**
- **Secret Key:** Use cryptographically secure random strings (already done: `openssl rand -hex 32`)
- **Token Expiration:** 7 days is reasonable for content planning tool (not financial/medical)
- **Algorithm:** HS256 is appropriate for single-server deployments
  - RS256 (asymmetric) only needed for multi-service architectures
  - **Decision:** Use HS256 as specified in architecture

**Password Hashing Evolution:**
- **Current Trend:** Argon2id is now recommended over bcrypt (via pwdlib library)
- **bcrypt Status:** Still excellent choice, widely used, proven secure
- **Decision:** Use bcrypt with 12 rounds as specified (already installed)
  - 12 rounds = ~250ms per hash = good security/performance balance
  - **Future:** Consider Argon2id in Phase 2 for enhanced security

**Token Management:**
- **Refresh Tokens:** Not needed for MVP (7-day expiration is acceptable)
- **Token Revocation:** Not needed for MVP (single user, stateless tokens)
- **Sliding Expiration:** Not needed for MVP (simple re-login after 7 days)

### FastAPI OAuth2 Patterns (2026)

**OAuth2PasswordBearer:**
- Use `OAuth2PasswordBearer(tokenUrl="/auth/login")` for token_url specification
- FastAPI automatically generates OpenAPI docs with "Authorize" button
- Form-based login (`OAuth2PasswordRequestForm`) follows OAuth2 spec

**Dependency Injection:**
- Use `Depends(get_current_user)` on all protected routes
- FastAPI handles token extraction from Authorization header automatically
- Clear 401 errors with WWW-Authenticate header (OAuth2 standard)

### Security Considerations for Production

**Environment Variables:**
- ✅ JWT_SECRET_KEY already in Railway (from Story 1.1)
- ✅ JWT_ALGORITHM and JWT_EXPIRATION_DAYS in config.py
- ⚠️ Consider adding JWT_REFRESH_ENABLED for Phase 2

**HTTPS Requirements:**
- ✅ Railway enforces HTTPS at edge (already configured)
- ✅ HSTS header already added in main.py middleware
- ✅ No need for additional SSL configuration

**Common Vulnerabilities to Avoid:**
- ✅ SQL Injection: Prevented by SQLAlchemy ORM parameterized queries
- ✅ XSS: FastAPI auto-escapes JSON responses
- ✅ CSRF: Not applicable for JWT bearer tokens (no cookies)
- ⚠️ Ensure passwords never logged (add filter to logging in Phase 2)

---

## Project Context Reference

**Project:** trend-monitor
**Project Type:** Quantified trend monitoring system with multi-API data collection
**User:** dave (content planning lead, non-technical)
**Goal:** Enable data-driven content planning decisions by detecting cross-platform trend momentum

**Authentication Requirements:**
- Single user (dave) for MVP
- Simple username/password login
- 7-day session via JWT tokens
- Secure but not overly complex (not a financial/medical app)

**Success Criteria for This Story:**
- dave can log in with username/password
- JWT token returned and usable for 7 days
- All API endpoints can require authentication via Depends(get_current_user)
- Clear error messages for authentication failures

---

## Definition of Done

This story is **DONE** when:

1. ✅ POST /auth/login endpoint accepts username/password
2. ✅ System verifies password using bcrypt (12+ rounds)
3. ✅ System generates JWT token with 7-day expiration (HS256)
4. ✅ System returns {"access_token": "<jwt>", "token_type": "bearer"}
5. ✅ GET /auth/me endpoint returns user profile with valid token
6. ✅ Expired tokens return 401 "Token expired"
7. ✅ Invalid tokens return 401 "Invalid token"
8. ✅ Missing Authorization header returns 401 "Not authenticated"
9. ✅ JWT_SECRET_KEY loaded from environment (already in Railway)
10. ✅ Bootstrap user 'dave' exists in database
11. ✅ All manual tests pass on Railway deployment
12. ✅ Authentication endpoints documented in FastAPI auto-generated docs

---

## References

**Source Documents:**
- [PRD: FR-6.1, FR-6.2] - Authentication requirements
- [Architecture: AD-7] - JWT authentication pattern
- [Architecture: AD-4] - Security-first design principles
- [Epics: Story 1.3] - Detailed acceptance criteria
- [Story 1.1] - Environment variable configuration
- [Story 1.2] - Database schema with users table

**External Documentation:**
- [FastAPI OAuth2 with JWT](https://fastapi.tiangolo.com/tutorial/security/oauth2-jwt/)
- [python-jose Documentation](https://python-jose.readthedocs.io/)
- [passlib bcrypt Documentation](https://passlib.readthedocs.io/en/stable/lib/passlib.hash.bcrypt.html)
- [Better Stack: FastAPI Authentication Guide](https://betterstack.com/community/guides/scaling-python/authentication-fastapi/)
- [TestDriven.io: FastAPI JWT Auth](https://testdriven.io/blog/fastapi-jwt-auth/)

---

## Dev Notes

### Key Implementation Points

1. **Use OAuth2PasswordRequestForm for login:**
   - Requires Content-Type: application/x-www-form-urlencoded
   - Standard OAuth2 pattern expected by FastAPI
   - Form fields: username, password

2. **JWT Payload Structure:**
   - Store username in "sub" (subject) claim
   - "exp" (expiration) automatically added by jose.jwt.encode
   - Keep payload small (just username, no sensitive data)

3. **Token Validation Flow:**
   - Extract token from Authorization header (handled by OAuth2PasswordBearer)
   - Decode JWT with jose.jwt.decode (validates signature and expiration)
   - Fetch user from database by username
   - Return User object to route handler

4. **Password Security:**
   - Never log passwords (not even in debug mode)
   - Use constant-time comparison (handled by passlib.verify)
   - Hash new passwords before storing
   - Don't reveal if username exists in error messages

5. **Bootstrap User Creation:**
   - Run scripts/create_user.py after deployment
   - Use Railway CLI: `railway run python scripts/create_user.py`
   - Consider environment variable for initial password
   - Change default password after first login

### Testing Strategy

**Local Testing:**
1. Start local server: `uvicorn app.main:app --reload`
2. Test with curl commands (see Task 8)
3. Check FastAPI docs: http://localhost:8000/docs
4. Use "Authorize" button in docs to test full flow

**Railway Testing:**
1. Deploy via git push (automatic)
2. Run user creation: `railway run python scripts/create_user.py`
3. Test endpoints with Railway URL
4. Verify JWT_SECRET_KEY environment variable set

### Common Issues & Solutions

**Issue:** "Invalid token" even with fresh token
- **Solution:** Check JWT_SECRET_KEY matches between token creation and validation
- **Check:** Verify environment variable loaded correctly

**Issue:** "Token expired" immediately
- **Solution:** Check system clock (JWT uses UTC timestamps)
- **Check:** Verify JWT_EXPIRATION_DAYS in config

**Issue:** OAuth2PasswordRequestForm expects form data, not JSON
- **Solution:** Use Content-Type: application/x-www-form-urlencoded
- **Format:** `username=dave&password=changeme123`

**Issue:** User login updates don't persist
- **Solution:** Call `await db.commit()` after updating last_login
- **Check:** Async transaction handling

---

## Dev Agent Record

### Agent Model Used

Claude Sonnet 4.5 (claude-sonnet-4-5-20250929)

### Debug Log References

(To be filled during implementation)

### Completion Notes List

(To be filled during implementation)

### File List

(To be filled during implementation)

## Dev Agent Record

### Agent Model Used

{{agent_model_name_version}}

### Debug Log References

### Completion Notes List

### File List
