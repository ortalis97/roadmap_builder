# Feature: Phase 3 - AI Session Parsing with Gemini

The following plan should be complete, but it's important that you validate documentation and codebase patterns and task sanity before you start implementing.

Pay special attention to naming of existing utils, types, and models. Import from the right files etc.

## Feature Description

Integrate Google's Gemini API to parse user-pasted learning plans (stored as Drafts) into structured Sessions. When a user creates a roadmap, the AI will analyze the raw text and generate organized learning sessions with titles, content, and learning objectives.

**Key Design Decisions:**
- **AI Generation, not splitting**: The AI generates new structured content based on the user's intent, rather than splitting the original text verbatim
- **Draft preservation**: Original text is always preserved in the Draft document
- **Session creation**: Sessions are stored in a separate MongoDB collection, with lightweight summaries embedded in the Roadmap
- **Regeneration support**: Users can regenerate sessions if unsatisfied with the AI output

## User Story

As a self-directed learner
I want my pasted learning plan to be automatically parsed into structured sessions
So that I have a clear, organized roadmap without manual work

## Problem Statement

Currently, when users create a roadmap by pasting their learning plan, the roadmap is created with an empty sessions array. Users see "No sessions yet" and a message that AI parsing is coming soon. This defeats the core value proposition of transforming messy plans into structured roadmaps.

## Solution Statement

Integrate Gemini API to:
1. Accept the raw Draft text when creating a roadmap
2. Generate structured sessions with titles and learning content
3. Create Session documents in MongoDB
4. Update Roadmap with session summaries
5. Return the complete roadmap with sessions to the frontend

The flow becomes:
```
User pastes text → Create Draft → Call Gemini API → Generate Sessions → Create Roadmap with Sessions
```

## Feature Metadata

**Feature Type**: New Capability
**Estimated Complexity**: Medium
**Primary Systems Affected**: Backend (new AI service, updated roadmaps router)
**Dependencies**: google-generativeai (Gemini Python SDK)

---

## CONTEXT REFERENCES

### Relevant Codebase Files - IMPORTANT: YOU MUST READ THESE FILES BEFORE IMPLEMENTING!

**Backend Patterns:**
- `server/app/config.py` (lines 1-36) - Settings with `gemini_api_key` placeholder at line 19
- `server/app/main.py` (lines 1-88) - App lifecycle, router registration at lines 81-83
- `server/app/routers/roadmaps.py` (lines 1-209) - Current roadmap creation without AI
- `server/app/routers/drafts.py` (lines 1-95) - Draft creation pattern
- `server/app/models/session.py` (lines 1-41) - Session document model
- `server/app/models/roadmap.py` (lines 1-48) - Roadmap with SessionSummary
- `server/app/models/draft.py` (lines 1-28) - Draft model with raw_text
- `server/app/middleware/auth.py` (lines 1-132) - get_current_user pattern
- `server/app/database.py` (lines 1-64) - Beanie initialization pattern

**Frontend (for understanding current flow):**
- `client/src/hooks/useRoadmaps.ts` (lines 25-45) - useCreateRoadmap creates draft then roadmap
- `client/src/pages/CreateRoadmapPage.tsx` (lines 1-123) - Form submission flow
- `client/src/services/api.ts` (lines 54-62) - createRoadmap API call
- `client/src/types/index.ts` (lines 1-38) - TypeScript types for responses

### New Files to Create

**Backend:**
- `server/app/services/__init__.py` - Services package init
- `server/app/services/ai_service.py` - Gemini API integration and session generation
- `server/app/routers/ai.py` - AI-specific endpoints (generate roadmap from draft)

### Files to Update

**Backend:**
- `server/requirements.txt` - Add google-generativeai
- `server/app/config.py` - Validate gemini_api_key is set
- `server/app/main.py` - Register AI router
- `server/app/routers/roadmaps.py` - Update create_roadmap to call AI service
- `server/.env.example` - Uncomment GEMINI_API_KEY

**Frontend:**
- `client/src/pages/CreateRoadmapPage.tsx` - Update loading message, remove "coming soon" text
- `client/src/pages/RoadmapDetailPage.tsx` - Remove "AI parsing coming soon" placeholder

### Relevant Documentation - YOU SHOULD READ THESE BEFORE IMPLEMENTING!

- [Gemini API Python Quickstart](https://ai.google.dev/gemini-api/docs/quickstart?lang=python)
  - Installation: `pip install google-generativeai`
  - Basic usage pattern with `genai.configure()` and `GenerativeModel`
- [Gemini API Text Generation](https://ai.google.dev/gemini-api/docs/text-generation)
  - How to structure prompts for best results
  - JSON output mode for structured responses
- [Gemini API Models](https://ai.google.dev/gemini-api/docs/models/gemini)
  - Model selection: gemini-1.5-flash for speed/cost, gemini-1.5-pro for quality
- [Beanie ODM Docs](https://beanie-odm.dev/)
  - Document creation and relationships

### Patterns to Follow

**Settings Pattern (from config.py:8-26):**
```python
class Settings(BaseSettings):
    gemini_api_key: str = ""

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        case_sensitive=False,
    )
```

**Router Pattern (from routers/roadmaps.py:59-77):**
```python
@router.post("/", response_model=RoadmapResponse, status_code=status.HTTP_201_CREATED)
async def create_roadmap(
    roadmap_data: RoadmapCreate,
    current_user: User = Depends(get_current_user),
) -> RoadmapResponse:
    # Validation, creation, response
```

**Model Creation Pattern (from routers/roadmaps.py:106-122):**
```python
roadmap = Roadmap(
    user_id=current_user.id,
    draft_id=draft_object_id,
    title=roadmap_data.title,
    sessions=[],
)
await roadmap.insert()
```

**Beanie Document Insert (from models/session.py:18-41):**
```python
class Session(Document):
    roadmap_id: Indexed(PydanticObjectId)
    order: int
    title: str
    content: str
    status: SessionStatus = "not_started"
    notes: str = ""

    class Settings:
        name = "sessions"
```

**Error Handling Pattern (from routers/drafts.py:66-72):**
```python
try:
    object_id = PydanticObjectId(draft_id)
except Exception:
    raise HTTPException(
        status_code=status.HTTP_400_BAD_REQUEST,
        detail="Invalid draft ID format",
    )
```

**Logging Pattern (from middleware/auth.py:12, 118-126):**
```python
import structlog
logger = structlog.get_logger()

logger.info("Creating new user", firebase_uid=firebase_uid)
logger.error("Token verification failed", error=str(e))
```

---

## IMPLEMENTATION PLAN

### Phase 1: Dependencies & Configuration

Set up the Gemini SDK and configure API key access.

**Tasks:**
- Add google-generativeai to requirements.txt
- Update .env.example with GEMINI_API_KEY
- Validate gemini_api_key is available in settings

### Phase 2: AI Service Layer

Create the service layer for Gemini API integration with proper prompt engineering.

**Tasks:**
- Create services directory structure
- Implement ai_service.py with session generation logic
- Design prompt for structured JSON output
- Add validation for AI response schema
- Implement retry logic for API failures

### Phase 3: Backend Integration

Update the roadmap creation flow to use AI service.

**Tasks:**
- Modify create_roadmap to call AI service
- Create Session documents from AI response
- Update Roadmap with SessionSummary array
- Handle AI service errors gracefully
- Add logging for AI operations

### Phase 4: Frontend Updates

Update UI to reflect that AI parsing now works.

**Tasks:**
- Remove "coming soon" placeholders
- Update loading states for longer AI processing
- Ensure session display works correctly

---

## STEP-BY-STEP TASKS

IMPORTANT: Execute every task in order, top to bottom. Each task is atomic and independently testable.

---

### Phase 1: Dependencies & Configuration

#### 1.1 UPDATE `server/requirements.txt`

- **IMPLEMENT**: Add Gemini SDK dependency
- **ADD**: `google-generativeai>=0.8.0` after firebase-admin line
- **VALIDATE**: `cd server && ./venv/bin/pip install -r requirements.txt && ./venv/bin/python -c "import google.generativeai; print('Gemini SDK OK')"`

#### 1.2 UPDATE `server/.env.example`

- **IMPLEMENT**: Uncomment and document GEMINI_API_KEY
- **CHANGE**: Line 14 from `# GEMINI_API_KEY=...` to `GEMINI_API_KEY=your_gemini_api_key_here`
- **ADD**: Comment above explaining how to get the key: `# Get from https://aistudio.google.com/app/apikey`
- **VALIDATE**: `grep "GEMINI_API_KEY" server/.env.example | grep -v "^#"`

#### 1.3 VERIFY User Has GEMINI_API_KEY

- **IMPORTANT**: Before proceeding, ask the user to provide their Gemini API key
- **INSTRUCTION**: User should add `GEMINI_API_KEY=...` to `server/.env`
- **VALIDATE**: `cd server && ./venv/bin/python -c "from app.config import get_settings; s = get_settings(); assert s.gemini_api_key, 'GEMINI_API_KEY not set'; print('API key configured')"`

---

### Phase 2: AI Service Layer

#### 2.1 CREATE `server/app/services/__init__.py`

- **IMPLEMENT**: Empty init file for services package
- **CONTENT**: Just a docstring: `"""Business logic services."""`
- **VALIDATE**: `cd server && ./venv/bin/python -c "from app import services; print('Services package OK')"`

#### 2.2 CREATE `server/app/services/ai_service.py`

- **IMPLEMENT**: Gemini API integration for session generation
- **IMPORTS**:
  ```python
  import json
  import google.generativeai as genai
  import structlog
  from pydantic import BaseModel, ValidationError
  from app.config import get_settings
  ```
- **CLASSES**:
  - `GeneratedSession(BaseModel)`: title (str), content (str) - for validating AI output
  - `GeneratedRoadmap(BaseModel)`: summary (str), sessions (list[GeneratedSession])
- **FUNCTIONS**:
  - `init_gemini() -> None`: Configure genai with API key, call once at startup
  - `is_gemini_configured() -> bool`: Check if API key is set
  - `async generate_sessions_from_draft(raw_text: str, title: str) -> GeneratedRoadmap`: Main generation function
- **PROMPT DESIGN**:
  ```python
  SYSTEM_PROMPT = """You are a learning roadmap architect. Given a learning goal or plan,
  create a structured roadmap with sessions.

  Output valid JSON matching this schema:
  {
    "summary": "2-3 sentence overview of the learning journey",
    "sessions": [
      {
        "title": "Session title",
        "content": "Detailed learning content with objectives, key concepts, and suggested activities. Use markdown formatting."
      }
    ]
  }

  Rules:
  - Create 5-15 sessions depending on scope
  - Each session should be completable in 1-3 hours
  - Progress from fundamentals to advanced
  - Include practical exercises where relevant
  - Content should be educational and actionable
  - Do NOT include an index or table of contents as a session
  - DO include intro/overview sessions and summary/resources sessions
  """
  ```
- **ERROR HANDLING**:
  - Validate JSON response with Pydantic
  - Retry up to 2 times on parse failure
  - Log all API calls with timing
- **GOTCHA**: Use `model.generate_content()` which is synchronous, wrap in executor for async
- **VALIDATE**: `cd server && ./venv/bin/python -c "from app.services.ai_service import GeneratedRoadmap, GeneratedSession; print('AI service models OK')"`

#### 2.3 UPDATE `server/app/main.py`

- **IMPLEMENT**: Initialize Gemini on startup
- **IMPORT**: `from app.services.ai_service import init_gemini`
- **ADD**: Call `init_gemini()` in lifespan after `init_firebase()` (around line 43)
- **PATTERN**: Mirror the init_firebase() call pattern
- **VALIDATE**: `cd server && timeout 5 ./venv/bin/uvicorn app.main:app --port 8001 2>&1 | grep -E "(Gemini|error)" || echo "Startup OK"`

---

### Phase 3: Backend Integration

#### 3.1 UPDATE `server/app/routers/roadmaps.py` - Add Imports

- **IMPLEMENT**: Import AI service and Session model
- **ADD IMPORTS** (after existing imports around line 10):
  ```python
  import structlog
  from app.services.ai_service import generate_sessions_from_draft, is_gemini_configured
  from app.models.session import Session
  from app.models.roadmap import SessionSummary
  ```
- **ADD**: `logger = structlog.get_logger()` after imports
- **VALIDATE**: `cd server && ./venv/bin/python -c "from app.routers.roadmaps import router; print('Imports OK')"`

#### 3.2 UPDATE `server/app/routers/roadmaps.py` - Modify create_roadmap

- **IMPLEMENT**: Call AI service and create sessions in create_roadmap function
- **MODIFY**: The `create_roadmap` function (lines 80-122) to:
  1. After validating draft exists (line 104), call AI service:
     ```python
     # Generate sessions using AI
     if not is_gemini_configured():
         raise HTTPException(
             status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
             detail="AI service not configured",
         )

     try:
         generated = await generate_sessions_from_draft(
             raw_text=draft.raw_text,
             title=roadmap_data.title,
         )
     except Exception as e:
         logger.error("AI generation failed", error=str(e))
         raise HTTPException(
             status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
             detail="Failed to generate sessions. Please try again.",
         )
     ```
  2. Create Roadmap first to get its ID:
     ```python
     roadmap = Roadmap(
         user_id=current_user.id,
         draft_id=draft_object_id,
         title=roadmap_data.title,
         summary=generated.summary,
         sessions=[],  # Will be populated after creating Session documents
     )
     await roadmap.insert()
     ```
  3. Create Session documents and build SessionSummary list:
     ```python
     session_summaries = []
     for order, gen_session in enumerate(generated.sessions, start=1):
         session = Session(
             roadmap_id=roadmap.id,
             order=order,
             title=gen_session.title,
             content=gen_session.content,
         )
         await session.insert()
         session_summaries.append(
             SessionSummary(id=session.id, title=session.title, order=order)
         )

     # Update roadmap with session summaries
     roadmap.sessions = session_summaries
     await roadmap.save()
     ```
  4. Return response with sessions included
- **GOTCHA**: Create Roadmap first, then Sessions, then update Roadmap with session refs
- **VALIDATE**: `cd server && ./venv/bin/ruff check app/routers/roadmaps.py`

#### 3.3 UPDATE `server/app/routers/roadmaps.py` - Add regenerate endpoint (Optional Enhancement)

- **IMPLEMENT**: Add endpoint to regenerate sessions for existing roadmap
- **ENDPOINT**: `POST /roadmaps/{roadmap_id}/regenerate`
- **LOGIC**:
  1. Get roadmap and verify ownership
  2. Get associated draft
  3. Delete existing sessions for this roadmap
  4. Call AI service to generate new sessions
  5. Create new Session documents
  6. Update Roadmap with new session summaries
- **SCHEMA**: Return `RoadmapResponse`
- **VALIDATE**: `cd server && ./venv/bin/python -c "from app.routers.roadmaps import router; print([r.path for r in router.routes])"`

---

### Phase 4: Frontend Updates

#### 4.1 UPDATE `client/src/pages/CreateRoadmapPage.tsx`

- **IMPLEMENT**: Update loading message and remove "coming soon"
- **CHANGE** Line 99-101: Remove or update the helper text
  - FROM: `"This will be saved as your draft. AI parsing into sessions coming soon."`
  - TO: `"Your learning plan will be analyzed by AI to create structured sessions."`
- **CHANGE** Line 110: Update loading text
  - FROM: `'Creating...'`
  - TO: `'Generating sessions...'` (AI processing takes longer)
- **VALIDATE**: `grep -n "coming soon" client/src/pages/CreateRoadmapPage.tsx || echo "Placeholder removed"`

#### 4.2 UPDATE `client/src/pages/RoadmapDetailPage.tsx`

- **IMPLEMENT**: Remove "coming soon" placeholder from empty sessions state
- **CHANGE** Lines 113-119: Update empty state message
  - FROM:
    ```jsx
    <p>No sessions yet.</p>
    <p className="text-sm mt-1">AI parsing of your draft into sessions is coming soon.</p>
    ```
  - TO:
    ```jsx
    <p>No sessions were generated.</p>
    <p className="text-sm mt-1">Try creating a new roadmap with more detailed content.</p>
    ```
- **VALIDATE**: `grep -n "coming soon" client/src/pages/RoadmapDetailPage.tsx || echo "Placeholder removed"`

#### 4.3 BUILD Frontend

- **IMPLEMENT**: Verify frontend builds successfully
- **VALIDATE**: `cd client && ~/.bun/bin/bun run build`

---

## TESTING STRATEGY

### Unit Tests (Backend)

Design tests for the AI service:

```python
# tests/unit/test_ai_service.py

import pytest
from app.services.ai_service import GeneratedSession, GeneratedRoadmap

def test_generated_session_schema():
    """Test GeneratedSession validates correctly."""
    session = GeneratedSession(title="Test", content="Content here")
    assert session.title == "Test"

def test_generated_roadmap_schema():
    """Test GeneratedRoadmap validates correctly."""
    roadmap = GeneratedRoadmap(
        summary="Test summary",
        sessions=[GeneratedSession(title="S1", content="C1")]
    )
    assert len(roadmap.sessions) == 1

def test_generated_roadmap_requires_sessions():
    """Test GeneratedRoadmap requires at least summary and sessions."""
    with pytest.raises(Exception):
        GeneratedRoadmap(summary="")  # Missing sessions
```

### Integration Tests (Backend)

Design tests for the roadmap creation with AI:

```python
# tests/integration/test_roadmaps_ai.py

import pytest
from unittest.mock import patch, AsyncMock

@pytest.mark.asyncio
async def test_create_roadmap_calls_ai_service(
    client, auth_headers, test_draft
):
    """Test that creating roadmap triggers AI generation."""
    with patch('app.routers.roadmaps.generate_sessions_from_draft') as mock_gen:
        mock_gen.return_value = GeneratedRoadmap(
            summary="Test summary",
            sessions=[GeneratedSession(title="Session 1", content="Content")]
        )

        response = await client.post(
            "/api/v1/roadmaps/",
            json={"draft_id": str(test_draft.id), "title": "Test Roadmap"},
            headers=auth_headers,
        )

        assert response.status_code == 201
        assert mock_gen.called
        data = response.json()
        assert len(data["sessions"]) == 1

@pytest.mark.asyncio
async def test_create_roadmap_fails_gracefully_on_ai_error(
    client, auth_headers, test_draft
):
    """Test graceful handling when AI service fails."""
    with patch('app.routers.roadmaps.generate_sessions_from_draft') as mock_gen:
        mock_gen.side_effect = Exception("API Error")

        response = await client.post(
            "/api/v1/roadmaps/",
            json={"draft_id": str(test_draft.id), "title": "Test"},
            headers=auth_headers,
        )

        assert response.status_code == 500
        assert "Failed to generate sessions" in response.json()["detail"]
```

### Manual Testing

1. **Happy Path**:
   - Login to the app
   - Click "Create New Roadmap"
   - Enter title: "Learn Python Basics"
   - Paste: "I want to learn Python programming. Start with syntax, then variables, functions, classes, and file handling. Maybe 2 weeks of learning."
   - Click "Create Roadmap"
   - Verify: Loading state shows, then redirects to roadmap with sessions listed

2. **Edge Cases**:
   - Very short input: "Learn React" (should still generate reasonable sessions)
   - Very long input: Paste a full course curriculum (should handle gracefully)
   - Non-English input: Test with other languages if supported

3. **Error Handling**:
   - Invalid API key: Should show 503 error
   - API timeout: Should show 500 error with retry message

---

## VALIDATION COMMANDS

Execute every command to ensure zero regressions and 100% feature correctness.

### Level 1: Syntax & Style

```bash
# Backend linting
cd server && ./venv/bin/ruff check app/

# Backend formatting
cd server && ./venv/bin/ruff format --check app/

# Frontend linting
cd client && ~/.bun/bin/bun run lint

# Frontend type checking
cd client && npx tsc --noEmit
```

### Level 2: Unit Tests

```bash
cd server && ./venv/bin/pytest tests/unit/ -v
```

### Level 3: Integration Tests

```bash
cd server && ./venv/bin/pytest tests/integration/ -v
```

### Level 4: Server Startup

```bash
# Verify backend starts without errors
cd server && timeout 5 ./venv/bin/uvicorn app.main:app --port 8001 2>&1 | grep -E "(error|Error)" || echo "Backend OK"

# Verify frontend builds
cd client && ~/.bun/bin/bun run build
```

### Level 5: Manual Validation

1. Start backend: `cd server && ./venv/bin/uvicorn app.main:app --reload`
2. Start frontend: `cd client && ~/.bun/bin/bun run dev`
3. Open http://localhost:5173
4. Login with Google
5. Create a roadmap with sample learning plan text
6. Verify sessions are generated and displayed
7. Test with different input lengths and complexities

---

## ACCEPTANCE CRITERIA

- [ ] Gemini SDK installed and configured with API key
- [ ] AI service layer created with proper prompt engineering
- [ ] Roadmap creation triggers AI session generation
- [ ] Sessions are created as separate MongoDB documents
- [ ] Roadmap contains SessionSummary references
- [ ] Errors from AI service are handled gracefully
- [ ] Frontend reflects AI generation (no "coming soon" placeholders)
- [ ] Loading states indicate AI processing
- [ ] All validation commands pass with zero errors
- [ ] Code follows project conventions and patterns

---

## COMPLETION CHECKLIST

- [ ] All tasks completed in order
- [ ] Each task validation passed immediately
- [ ] All validation commands executed successfully
- [ ] Full test suite passes (unit + integration)
- [ ] No linting or type checking errors
- [ ] Manual testing confirms feature works
- [ ] Acceptance criteria all met
- [ ] README.md updated with current status
- [ ] CLAUDE.md updated if new patterns introduced

---

## NOTES

### AI Model Selection

- **Recommended**: `gemini-1.5-flash` for balance of speed, cost, and quality
- **Alternative**: `gemini-1.5-pro` for higher quality on complex inputs (slower, more expensive)
- Can make this configurable via environment variable later

### Prompt Engineering Considerations

The prompt is designed to:
1. Request structured JSON output for reliable parsing
2. Set clear constraints (5-15 sessions, 1-3 hours each)
3. Specify what to include (intro, practical exercises) and exclude (index/TOC)
4. Request markdown formatting for rich content

### Error Handling Strategy

Three types of errors to handle:
1. **Configuration errors** (no API key): Return 503 Service Unavailable
2. **API errors** (rate limit, timeout): Return 500 with retry message
3. **Parse errors** (invalid JSON): Retry up to 2 times, then return 500

### Token Usage Estimation

For a typical learning plan input (2,000-5,000 words):
- Input: ~3,000-7,000 tokens
- Output: ~2,000-5,000 tokens (5-15 sessions with content)
- Cost with Gemini 1.5 Flash: < $0.01 per roadmap

### Future Enhancements (Not in This Phase)

- Regenerate endpoint for existing roadmaps
- User hints (duration, depth, focus areas) to customize generation
- Streaming response for real-time UI updates
- Caching of similar requests

### Required User Action

Before implementation can be validated, the user must:
1. Get a Gemini API key from https://aistudio.google.com/app/apikey
2. Add `GEMINI_API_KEY=...` to `server/.env`
