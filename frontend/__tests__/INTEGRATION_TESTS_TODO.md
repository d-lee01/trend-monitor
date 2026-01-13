# Integration Tests - TODO

## Current Status
✅ **Unit tests complete** - All components and pages have comprehensive unit test coverage with mocked dependencies.

❌ **Integration tests missing** - No tests validating actual API integration or end-to-end user flows.

## Required Integration Tests

### 1. API Integration Tests
Test real API contract with backend:
- Verify `/api/trends/:id` endpoint returns correct TrendDetail schema
- Test authentication flow with real JWT tokens
- Validate error responses (401, 404, 500)
- Test timeout handling with slow API responses

### 2. End-to-End User Flows
Test complete user journeys:
- Dashboard → Click trend card → View detail page
- Invalid trend ID → See 404 page
- Expired token → Redirect to login
- Network error → Redirect to dashboard with error message

### 3. Performance Tests
Validate AC-6 requirement:
- Page loads in <2 seconds with real API data
- SSR performance metrics
- First Contentful Paint (FCP) < 1.5s

## Recommended Tools
- **Integration**: Jest with MSW (Mock Service Worker) or real API test environment
- **E2E**: Playwright or Cypress
- **Performance**: Lighthouse CI or WebPageTest

## Priority
**MEDIUM** - Current unit tests provide good coverage, but integration tests needed before production release to catch API contract changes and real-world errors.

## Related Story
Story 3.6 - Trend Detail View (Code Review Finding #6)
