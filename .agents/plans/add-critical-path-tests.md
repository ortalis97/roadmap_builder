# Feature: Critical Path Integration Tests

The following plan should be complete, but it's important that you validate documentation and codebase patterns and task sanity before you start implementing.

Pay special attention to naming of existing utils, types, and models. Import from the right files etc.

## Feature Description

Add critical path integration tests for the Learning Roadmap App backend. These tests will cover the core API endpoints that form the primary user journey: authentication, draft creation, roadmap generation, session management, and progress tracking. Tests will use pytest-asyncio with a test MongoDB database and mocked Firebase authentication.

## User Story

As a developer
I want comprehensive integration tests for critical API paths
So that I can confidently make changes without breaking core functionality

## Problem Statement

The backend has no test files despite having pytest configured. Any code changes carry risk of regression since there's no automated verification of API behavior. The critical user journey (auth → create draft → generate roadmap → track sessions → use chat) is untested.

## Solution Statement

Implement integration tests using pytest-asyncio and httpx's AsyncClient with FastAPI. Tests will:
1. Use an in-memory or test MongoDB instance via mongomock or real test database
2. Mock Firebase token verification to test authenticated endpoints
3. Mock the Gemini AI service to avoid external API calls
4. Cover all critical CRUD operations and edge cases
5. Follow existing project patterns (structlog, Pydantic, async)

## Feature Metadata

**Feature Type**: New Capability
**Estimated Complexity**: Medium
**Primary Systems Affected**: Backend test infrastructure, all routers
**Dependencies**: pytest, pytest-asyncio, httpx (already in requirements.txt)

---

## CONTEXT REFERENCES

### Relevant Codebase Files IMPORTANT: YOU MUST READ THESE FILES BEFORE IMPLEMENTING!

- `server/pyproject.toml` (lines 30-33) - Why: pytest configuration with asyncio_mode="auto"
- `server/app/main.py` (lines 1-95) - Why: FastAPI app creation pattern needed for test client
- `server/app/database.py` (lines 1-65) - Why: Database initialization pattern to replicate for tests
- `server/app/middleware/auth.py` (lines 1-132) - Why: Auth dependency to mock (`get_current_user`)
- `server/app/routers/auth.py` (lines 1-39) - Why: Auth endpoint to test
- `server/app/routers/drafts.py` (lines 1-95) - Why: Draft CRUD to test
- `server/app/routers/roadmaps.py` (lines 1-499) - Why: Main roadmap/session endpoints to test
- `server/app/routers/chat.py` (lines 1-289) - Why: Chat endpoints to test
- `server/app/models/user.py` (lines 1-35) - Why: User model for test fixtures
- `server/app/models/draft.py` (lines 1-28) - Why: Draft model for test fixtures
- `server/app/models/roadmap.py` (lines 1-48) - Why: Roadmap model for test fixtures
- `server/app/models/session.py` (lines 1-41) - Why: Session model for test fixtures
- `server/app/services/ai_service.py` (lines 1-353) - Why: AI service to mock
- `.claude/reference/testing-and-logging.md` (lines 406-510) - Why: FastAPI integration testing patterns

### New Files to Create

- `server/tests/__init__.py` - Package marker
- `server/tests/conftest.py` - Shared fixtures (test client, mock auth, test db)
- `server/tests/integration/__init__.py` - Package marker
- `server/tests/integration/test_auth.py` - Auth endpoint tests
- `server/tests/integration/test_drafts.py` - Draft CRUD tests
- `server/tests/integration/test_roadmaps.py` - Roadmap CRUD tests
- `server/tests/integration/test_sessions.py` - Session CRUD tests
- `server/tests/integration/test_chat.py` - Chat endpoint tests
- `server/tests/integration/test_progress.py` - Progress endpoint tests

### Relevant Documentation

- FastAPI Testing: https://fastapi.tiangolo.com/tutorial/testing/
  - Specific section: Testing with dependency overrides
  - Why: Shows how to override `get_current_user` dependency
- pytest-asyncio: https://pytest-asyncio.readthedocs.io/
  - Specific section: async fixtures
  - Why: Required for async test fixtures with Beanie
- Beanie Testing: https://beanie-odm.dev/tutorial/testing/
  - Specific section: Using init_beanie in tests
  - Why: Shows proper async initialization for test database

### Patterns to Follow

**Naming Conventions:**
- Test files: `test_<module>.py`
- Test classes: `class Test<Feature>:`
- Test functions: `def test_<action>_<expected_outcome>()` or `async def test_<action>_<expected_outcome>()`

**Error Handling Pattern (from routers):**
```python
raise HTTPException(
    status_code=status.HTTP_404_NOT_FOUND,
    detail="Roadmap not found",
)
```

**Logging Pattern (from routers):**
```python
import structlog
logger = structlog.get_logger()
logger.info("Action completed", key=value)
```

**Model Creation Pattern (from models):**
```python
from datetime import UTC, datetime
def utc_now() -> datetime:
    return datetime.now(UTC)
```

**Async Test Pattern (from reference docs):**
```python
@pytest.mark.asyncio
async def test_something():
    # pytest-asyncio handles the event loop
    pass
```

**Note:** With `asyncio_mode = "auto"` in pyproject.toml, the `@pytest.mark.asyncio` decorator is optional.

---

## IMPLEMENTATION PLAN

### Phase 1: Test Infrastructure Setup

Set up the foundational test infrastructure including:
- Test database initialization with Beanie
- Mock Firebase authentication
- Mock AI service
- Async test client fixture

### Phase 2: Core CRUD Tests

Implement tests for the fundamental CRUD operations:
- Auth endpoint (/auth/me)
- Drafts (create, get)
- Roadmaps (list, create, get, delete)

### Phase 3: Session & Progress Tests

Implement tests for session management:
- Session listing
- Session retrieval
- Session updates (status, notes)
- Progress calculation

### Phase 4: Chat Tests

Implement tests for AI chat functionality:
- Chat message sending (with mocked AI)
- Chat history retrieval
- Chat history clearing

---

## STEP-BY-STEP TASKS

### Task 1: CREATE `server/tests/__init__.py`

- **IMPLEMENT**: Empty package marker file
- **PATTERN**: Standard Python package
- **IMPORTS**: None
- **GOTCHA**: File must exist for pytest to discover tests
- **VALIDATE**: `ls server/tests/__init__.py`

### Task 2: CREATE `server/tests/conftest.py`

- **IMPLEMENT**: Shared test fixtures for all integration tests

  Required fixtures:
  1. `mock_user` - Creates a test User document
  2. `mock_firebase_token` - Returns mock token data dict
  3. `override_get_current_user` - Dependency override returning mock user
  4. `test_app` - FastAPI app with overridden dependencies
  5. `client` - httpx.AsyncClient for making test requests
  6. `init_test_db` - Initialize Beanie with test MongoDB (use mongomock-motor or real test db)

- **PATTERN**: Mirror `app/database.py:15-46` for Beanie initialization
- **IMPORTS**:
  ```python
  import pytest
  from httpx import AsyncClient, ASGITransport
  from beanie import init_beanie, PydanticObjectId
  from mongomock_motor import AsyncMongoMockClient
  from unittest.mock import AsyncMock, patch

  from app.main import create_app
  from app.middleware.auth import get_current_user
  from app.models.user import User
  from app.models.draft import Draft
  from app.models.roadmap import Roadmap, SessionSummary
  from app.models.session import Session
  from app.models.chat_history import ChatHistory
  ```
- **GOTCHA**:
  - Must use `mongomock-motor` for in-memory MongoDB (add to requirements.txt if needed)
  - Alternative: Use environment variable for test MongoDB URI
  - Must initialize Beanie before creating documents
  - Use `ASGITransport` with `AsyncClient` for async testing
- **VALIDATE**: `cd server && ./venv/bin/pytest tests/conftest.py --collect-only`

### Task 3: UPDATE `server/requirements.txt`

- **IMPLEMENT**: Add mongomock-motor for in-memory test database
- **PATTERN**: Follow existing format
- **ADD**:
  ```
  mongomock-motor>=0.0.30
  ```
- **GOTCHA**: Place in development dependencies section if separated
- **VALIDATE**: `cd server && ./venv/bin/pip install -r requirements.txt`

### Task 4: CREATE `server/tests/integration/__init__.py`

- **IMPLEMENT**: Empty package marker file
- **PATTERN**: Standard Python package
- **IMPORTS**: None
- **VALIDATE**: `ls server/tests/integration/__init__.py`

### Task 5: CREATE `server/tests/integration/test_auth.py`

- **IMPLEMENT**: Tests for `/api/v1/auth/me` endpoint

  Test cases:
  1. `test_get_me_returns_user_profile` - Authenticated user gets their profile
  2. `test_get_me_creates_user_on_first_login` - New firebase_uid creates user
  3. `test_get_me_without_token_returns_401` - Missing auth returns 401

- **PATTERN**: Mirror `app/routers/auth.py:25-38` for expected response
- **IMPORTS**:
  ```python
  import pytest
  from httpx import AsyncClient
  ```
- **GOTCHA**: The auth middleware is already mocked in conftest, so focus on response validation
- **VALIDATE**: `cd server && ./venv/bin/pytest tests/integration/test_auth.py -v`

### Task 6: CREATE `server/tests/integration/test_drafts.py`

- **IMPLEMENT**: Tests for `/api/v1/drafts` endpoints

  Test cases:
  1. `test_create_draft_returns_201` - Valid draft creation
  2. `test_create_draft_stores_raw_text` - Verify raw_text is saved
  3. `test_get_draft_returns_draft` - Retrieve existing draft
  4. `test_get_draft_not_found_returns_404` - Non-existent draft
  5. `test_get_draft_wrong_user_returns_404` - Accessing another user's draft
  6. `test_get_draft_invalid_id_returns_400` - Invalid ObjectId format

- **PATTERN**: Mirror `app/routers/drafts.py:34-54` for create, `app/routers/drafts.py:57-94` for get
- **IMPORTS**:
  ```python
  import pytest
  from httpx import AsyncClient
  from beanie import PydanticObjectId
  from app.models.draft import Draft
  ```
- **GOTCHA**: Create drafts directly in DB for "get" tests, use API for "create" tests
- **VALIDATE**: `cd server && ./venv/bin/pytest tests/integration/test_drafts.py -v`

### Task 7: CREATE `server/tests/integration/test_roadmaps.py`

- **IMPLEMENT**: Tests for `/api/v1/roadmaps` endpoints

  Test cases:
  1. `test_list_roadmaps_empty` - No roadmaps returns empty list
  2. `test_list_roadmaps_returns_user_roadmaps` - List user's roadmaps
  3. `test_list_roadmaps_excludes_other_users` - User isolation
  4. `test_create_roadmap_returns_201` - With mocked AI, creates roadmap with sessions
  5. `test_create_roadmap_invalid_draft_returns_404` - Non-existent draft
  6. `test_create_roadmap_wrong_user_draft_returns_404` - Another user's draft
  7. `test_get_roadmap_returns_roadmap` - Retrieve with sessions
  8. `test_get_roadmap_not_found_returns_404` - Non-existent roadmap
  9. `test_get_roadmap_wrong_user_returns_404` - Another user's roadmap
  10. `test_delete_roadmap_returns_204` - Successful deletion
  11. `test_delete_roadmap_not_found_returns_404` - Non-existent roadmap

- **PATTERN**: Mirror `app/routers/roadmaps.py:132-230` for create, needs AI mock
- **IMPORTS**:
  ```python
  import pytest
  from unittest.mock import patch, AsyncMock
  from httpx import AsyncClient
  from beanie import PydanticObjectId
  from app.models.draft import Draft
  from app.models.roadmap import Roadmap, SessionSummary
  from app.models.session import Session
  from app.services.ai_service import GeneratedRoadmap, GeneratedSession
  ```
- **GOTCHA**:
  - Must mock `generate_sessions_from_draft` for create tests
  - Must mock `is_gemini_configured` to return True
  - Create test data directly in DB for get/delete tests
- **VALIDATE**: `cd server && ./venv/bin/pytest tests/integration/test_roadmaps.py -v`

### Task 8: CREATE `server/tests/integration/test_sessions.py`

- **IMPLEMENT**: Tests for `/api/v1/roadmaps/{id}/sessions` endpoints

  Test cases:
  1. `test_list_sessions_returns_sessions_with_status` - List all sessions
  2. `test_list_sessions_ordered_by_order` - Verify ordering
  3. `test_get_session_returns_full_session` - Full session with content
  4. `test_get_session_not_found_returns_404` - Non-existent session
  5. `test_update_session_status` - Update status to "done"
  6. `test_update_session_notes` - Update notes
  7. `test_update_session_both` - Update status and notes together
  8. `test_update_session_invalid_status_returns_400` - Invalid status value
  9. `test_update_session_updates_timestamp` - Verify updated_at changes

- **PATTERN**: Mirror `app/routers/roadmaps.py:319-458` for session endpoints
- **IMPORTS**:
  ```python
  import pytest
  from httpx import AsyncClient
  from beanie import PydanticObjectId
  from app.models.roadmap import Roadmap, SessionSummary
  from app.models.session import Session
  ```
- **GOTCHA**:
  - Create roadmap and sessions directly in DB for these tests
  - Session must reference correct roadmap_id
  - Valid statuses: "not_started", "in_progress", "done", "skipped"
- **VALIDATE**: `cd server && ./venv/bin/pytest tests/integration/test_sessions.py -v`

### Task 9: CREATE `server/tests/integration/test_progress.py`

- **IMPLEMENT**: Tests for `/api/v1/roadmaps/{id}/progress` endpoint

  Test cases:
  1. `test_progress_all_not_started` - 0% progress
  2. `test_progress_partial_done` - Calculate correct percentage
  3. `test_progress_all_done` - 100% progress
  4. `test_progress_with_skipped` - Skipped doesn't count as done
  5. `test_progress_counts_correct` - Verify each status count
  6. `test_progress_empty_roadmap` - Roadmap with no sessions (edge case)

- **PATTERN**: Mirror `app/routers/roadmaps.py:461-498` for progress endpoint
- **IMPORTS**:
  ```python
  import pytest
  from httpx import AsyncClient
  from beanie import PydanticObjectId
  from app.models.roadmap import Roadmap, SessionSummary
  from app.models.session import Session
  ```
- **GOTCHA**: Create sessions with specific statuses to test calculations
- **VALIDATE**: `cd server && ./venv/bin/pytest tests/integration/test_progress.py -v`

### Task 10: CREATE `server/tests/integration/test_chat.py`

- **IMPLEMENT**: Tests for `/api/v1/chat` endpoints

  Test cases:
  1. `test_send_message_creates_conversation` - New conversation created
  2. `test_send_message_returns_both_messages` - User and assistant messages returned
  3. `test_send_message_continues_conversation` - Using existing conversation_id
  4. `test_send_message_invalid_roadmap_returns_404` - Non-existent roadmap
  5. `test_send_message_invalid_session_returns_404` - Non-existent session
  6. `test_get_chat_history_returns_messages` - Retrieve existing history
  7. `test_get_chat_history_empty_returns_none` - No history returns null
  8. `test_clear_chat_history_returns_204` - Successful deletion

- **PATTERN**: Mirror `app/routers/chat.py:58-189` for chat endpoint, needs AI mock
- **IMPORTS**:
  ```python
  import pytest
  from unittest.mock import patch, AsyncMock
  from httpx import AsyncClient
  from beanie import PydanticObjectId
  from app.models.roadmap import Roadmap, SessionSummary
  from app.models.session import Session
  from app.models.chat_history import ChatHistory
  ```
- **GOTCHA**:
  - Must mock `generate_chat_response` for send message tests
  - Must mock `is_gemini_configured` to return True
  - Create roadmap and session in DB before testing chat
- **VALIDATE**: `cd server && ./venv/bin/pytest tests/integration/test_chat.py -v`

---

## TESTING STRATEGY

### Unit Tests

Not in scope for this plan - focusing on integration tests only.

### Integration Tests

All tests in this plan are integration tests that:
- Use a real (mocked) MongoDB database via mongomock-motor
- Test full request/response cycle through FastAPI
- Mock external dependencies (Firebase, Gemini AI)
- Verify database state changes

### Edge Cases

Each test file covers edge cases including:
- Invalid ObjectId formats (400 errors)
- Non-existent resources (404 errors)
- Unauthorized access to other users' data (404 errors - not 403 to avoid info leakage)
- Invalid input data (422 validation errors)
- Empty collections / zero results

---

## VALIDATION COMMANDS

Execute every command to ensure zero regressions and 100% feature correctness.

### Level 1: Syntax & Style

```bash
cd server && ./venv/bin/ruff check tests/
cd server && ./venv/bin/ruff format tests/
```

### Level 2: Collect Tests

```bash
cd server && ./venv/bin/pytest tests/ --collect-only
```

### Level 3: Run All Tests

```bash
cd server && ./venv/bin/pytest tests/ -v
```

### Level 4: Run Tests with Coverage

```bash
cd server && ./venv/bin/pytest tests/ -v --tb=short
```

### Level 5: Run Specific Test Files

```bash
cd server && ./venv/bin/pytest tests/integration/test_auth.py -v
cd server && ./venv/bin/pytest tests/integration/test_drafts.py -v
cd server && ./venv/bin/pytest tests/integration/test_roadmaps.py -v
cd server && ./venv/bin/pytest tests/integration/test_sessions.py -v
cd server && ./venv/bin/pytest tests/integration/test_progress.py -v
cd server && ./venv/bin/pytest tests/integration/test_chat.py -v
```

---

## ACCEPTANCE CRITERIA

- [ ] All test files created in `server/tests/integration/`
- [ ] `conftest.py` provides working fixtures for all tests
- [ ] All 40+ test cases pass
- [ ] Tests run in isolation (no test order dependencies)
- [ ] Tests use mocked MongoDB (mongomock-motor)
- [ ] Tests use mocked Firebase authentication
- [ ] Tests use mocked Gemini AI service
- [ ] Ruff linting passes with zero errors
- [ ] Tests complete in under 30 seconds total
- [ ] No actual external API calls made during tests

---

## COMPLETION CHECKLIST

- [ ] All tasks completed in order
- [ ] Each task validation passed immediately
- [ ] All validation commands executed successfully
- [ ] Full test suite passes
- [ ] No linting or type checking errors
- [ ] Test coverage includes all critical endpoints
- [ ] Code follows project conventions and patterns

---

## NOTES

### Design Decisions

1. **mongomock-motor over real MongoDB**: Faster tests, no external dependencies, runs in CI without setup

2. **Mocking auth at dependency level**: Override `get_current_user` rather than mocking Firebase SDK - cleaner and tests the actual endpoint logic

3. **Mocking AI at function level**: Patch `generate_sessions_from_draft` and `generate_chat_response` rather than the entire service - allows testing integration logic

4. **Not testing 503 errors**: The "service not configured" errors are startup issues, not runtime - no need to test in integration

### Alternative Approaches Considered

- **Using a real test MongoDB**: Would require Docker/external service, slower, but more realistic
- **Using pytest-mongo**: Less common, mongomock-motor is more widely used
- **End-to-end with real Firebase**: Would require test Firebase project, complex setup

### Dependencies to Install

```bash
cd server && ./venv/bin/pip install mongomock-motor
```

If mongomock-motor causes issues, alternative is to use environment variable `TEST_MONGODB_URI` pointing to a real test database.

### Test Data Factory Pattern (Optional Enhancement)

If tests become verbose, consider adding a `tests/factories.py` with helper functions:

```python
async def create_test_user(**kwargs) -> User:
    user = User(firebase_uid="test-uid", email="test@example.com", name="Test User", **kwargs)
    await user.insert()
    return user

async def create_test_roadmap(user: User, **kwargs) -> Roadmap:
    # ... etc
```

This is optional for MVP tests but recommended if test code becomes repetitive.
