# Feature: Phase 2 - Basic UI with Draft & Roadmap Creation

The following plan should be complete, but it's important that you validate documentation and codebase patterns and task sanity before you start implementing.

Pay special attention to naming of existing utils, types, and models. Import from the right files etc.

## Feature Description

Build a React frontend that enables users to:
1. Sign in with Google (Firebase Auth)
2. View a dashboard of their roadmaps
3. Create a new roadmap by pasting raw text (stored as Draft)
4. View individual roadmaps

This phase establishes the full-stack foundation without AI features. The raw text is stored in a `Draft` document, and a `Roadmap` references it. Sessions will be added in a later phase when AI parsing is implemented.

## User Story

As a self-directed learner
I want to paste my learning plan and save it as a roadmap
So that I can organize my learning journey and track it over time

## Problem Statement

Users have messy learning plans in text form but no structured way to store, view, and manage them. The current backend has authentication but no frontend or roadmap storage.

## Solution Statement

Create a React + Vite + TypeScript frontend with:
- Firebase client-side auth (Google OAuth)
- Protected routes requiring authentication
- Dashboard showing user's roadmaps
- "Create Roadmap" flow: paste text → save Draft → create Roadmap
- Roadmap detail view showing raw text (sessions come later)

Backend additions:
- Draft, Roadmap, Session Beanie document models
- CRUD endpoints for drafts and roadmaps
- Proper user isolation (users only see their own data)

## Feature Metadata

**Feature Type**: New Capability
**Estimated Complexity**: High
**Primary Systems Affected**: Frontend (new), Backend (models, routers)
**Dependencies**: Firebase JS SDK, React Router, TanStack Query, Tailwind CSS

---

## CONTEXT REFERENCES

### Relevant Codebase Files - IMPORTANT: YOU MUST READ THESE FILES BEFORE IMPLEMENTING!

**Backend Patterns:**
- `server/app/main.py` (lines 1-84) - App creation, lifespan, router registration pattern
- `server/app/config.py` (lines 1-36) - Settings pattern with Pydantic
- `server/app/database.py` (lines 1-60) - MongoDB init, Beanie setup, model registration
- `server/app/models/user.py` (lines 1-34) - Beanie Document model pattern
- `server/app/routers/auth.py` (lines 1-38) - Router pattern, response models
- `server/app/middleware/auth.py` (lines 1-131) - Firebase verification, get_current_user dependency

**Reference Documentation:**
- `.claude/reference/react-frontend-best-practices.md` - React patterns, TanStack Query, routing
- `.claude/reference/fastapi-best-practices.md` - API patterns, error handling

### New Files to Create

**Backend:**
- `server/app/models/draft.py` - Draft document model
- `server/app/models/roadmap.py` - Roadmap document model (with SessionSummary)
- `server/app/models/session.py` - Session document model
- `server/app/routers/drafts.py` - Draft CRUD endpoints
- `server/app/routers/roadmaps.py` - Roadmap CRUD endpoints

**Frontend:**
- `client/` - Entire React application (Vite scaffold)
- `client/src/services/firebase.ts` - Firebase initialization
- `client/src/services/api.ts` - API client with auth headers
- `client/src/context/AuthContext.tsx` - Auth state management
- `client/src/pages/LoginPage.tsx` - Login with Google
- `client/src/pages/DashboardPage.tsx` - Roadmap list
- `client/src/pages/CreateRoadmapPage.tsx` - Paste text, create draft/roadmap
- `client/src/pages/RoadmapDetailPage.tsx` - View roadmap
- `client/src/components/layout/Layout.tsx` - App shell with header
- `client/src/components/layout/ProtectedRoute.tsx` - Auth guard
- `client/src/hooks/useRoadmaps.ts` - TanStack Query hooks

### Relevant Documentation - YOU SHOULD READ THESE BEFORE IMPLEMENTING!

- [Vite Getting Started](https://vitejs.dev/guide/) - Project scaffolding
- [TanStack Query Quick Start](https://tanstack.com/query/latest/docs/react/quick-start) - Data fetching setup
- [Firebase Web Auth](https://firebase.google.com/docs/auth/web/google-signin) - Google sign-in
- [React Router Tutorial](https://reactrouter.com/en/main/start/tutorial) - Routing setup
- [Tailwind with Vite](https://tailwindcss.com/docs/guides/vite) - CSS setup
- [Beanie ODM Docs](https://beanie-odm.dev/) - MongoDB document models

### Patterns to Follow

**Backend - Beanie Document Model (from user.py:14-34):**
```python
from datetime import UTC, datetime
from beanie import Document, Indexed
from pydantic import Field

def utc_now() -> datetime:
    return datetime.now(UTC)

class ModelName(Document):
    """Docstring."""

    field_name: Indexed(str)  # type: ignore[valid-type]
    optional_field: str | None = None
    created_at: datetime = Field(default_factory=utc_now)

    class Settings:
        name = "collection_name"
```

**Backend - Router Pattern (from routers/auth.py:9-38):**
```python
from fastapi import APIRouter, Depends, status
from pydantic import BaseModel

router = APIRouter(prefix="/resource", tags=["resource"])

class ResourceResponse(BaseModel):
    id: str
    # fields...

    class Config:
        from_attributes = True

@router.get("/", response_model=list[ResourceResponse])
async def list_resources(current_user: User = Depends(get_current_user)):
    # Implementation
    pass
```

**Backend - Error Handling (from middleware/auth.py:61-88):**
```python
from fastapi import HTTPException, status

raise HTTPException(
    status_code=status.HTTP_404_NOT_FOUND,
    detail="Resource not found",
)
```

**Frontend - TanStack Query Hook Pattern:**
```typescript
import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query';

export function useRoadmaps() {
  return useQuery({
    queryKey: ['roadmaps'],
    queryFn: fetchRoadmaps,
  });
}

export function useCreateRoadmap() {
  const queryClient = useQueryClient();
  return useMutation({
    mutationFn: createRoadmap,
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['roadmaps'] });
    },
  });
}
```

**Frontend - Protected Route Pattern:**
```typescript
function ProtectedRoute({ children }: { children: React.ReactNode }) {
  const { user, loading } = useAuth();
  if (loading) return <div>Loading...</div>;
  if (!user) return <Navigate to="/login" replace />;
  return <>{children}</>;
}
```

---

## IMPLEMENTATION PLAN

### Phase 1: Backend Data Models

Create Beanie document models for Draft, Roadmap, and Session following existing User model patterns.

**Tasks:**
- Create Draft model with user_id and raw_text
- Create Roadmap model with draft_id reference and sessions array
- Create Session model with roadmap_id reference
- Register all models in database.py init_beanie call

### Phase 2: Backend API Endpoints

Add CRUD endpoints for drafts and roadmaps following existing auth router patterns.

**Tasks:**
- Create drafts router with POST (create) and GET (retrieve)
- Create roadmaps router with GET (list), POST (create), GET/:id (detail), DELETE/:id
- Register routers in main.py
- All endpoints require authentication via get_current_user

### Phase 3: Frontend Setup

Scaffold React + Vite + TypeScript project with Tailwind CSS.

**Tasks:**
- Create Vite project with React + TypeScript template
- Install dependencies (TanStack Query, React Router, Firebase, Tailwind)
- Configure Tailwind CSS
- Set up environment variables for Firebase config and API URL

### Phase 4: Frontend Auth

Implement Firebase client-side authentication with Google OAuth.

**Tasks:**
- Initialize Firebase with config from environment
- Create AuthContext for auth state management
- Implement Google sign-in flow
- Create ProtectedRoute component
- Create LoginPage with sign-in button

### Phase 5: Frontend Core Features

Build dashboard and roadmap creation flow.

**Tasks:**
- Create API client with auth token injection
- Create TanStack Query hooks for roadmaps
- Build DashboardPage showing roadmap list
- Build CreateRoadmapPage with text input form
- Build RoadmapDetailPage showing roadmap info

### Phase 6: Integration & Polish

Connect all pieces and add finishing touches.

**Tasks:**
- Create Layout component with header and navigation
- Set up React Router with all routes
- Add loading states and error handling
- Test full flow: login → create → view

---

## STEP-BY-STEP TASKS

IMPORTANT: Execute every task in order, top to bottom. Each task is atomic and independently testable.

---

### Phase 1: Backend Data Models

#### 1.1 CREATE `server/app/models/draft.py`

- **IMPLEMENT**: Draft document model with user_id and raw_text
- **PATTERN**: Mirror `server/app/models/user.py` structure
- **IMPORTS**: `datetime`, `beanie.Document`, `pydantic.Field`, `beanie.PydanticObjectId`
- **FIELDS**:
  - `user_id: PydanticObjectId` (reference to User)
  - `raw_text: str` (the pasted learning plan)
  - `created_at: datetime` (with default factory)
- **GOTCHA**: Use `Indexed()` for user_id since we'll query by it
- **VALIDATE**: `cd server && ./venv/bin/python -c "from app.models.draft import Draft; print('Draft model OK')"`

#### 1.2 CREATE `server/app/models/roadmap.py`

- **IMPLEMENT**: Roadmap document with SessionSummary embedded model
- **PATTERN**: Mirror `server/app/models/user.py` structure
- **IMPORTS**: `datetime`, `beanie.Document`, `beanie.PydanticObjectId`, `pydantic.BaseModel`, `pydantic.Field`
- **MODELS**:
  - `SessionSummary(BaseModel)`: id (PydanticObjectId), title (str), order (int)
  - `Roadmap(Document)`: user_id, draft_id, title, summary (optional), sessions (list[SessionSummary]), created_at, updated_at
- **GOTCHA**: SessionSummary is a Pydantic BaseModel, NOT a Document (it's embedded)
- **VALIDATE**: `cd server && ./venv/bin/python -c "from app.models.roadmap import Roadmap, SessionSummary; print('Roadmap model OK')"`

#### 1.3 CREATE `server/app/models/session.py`

- **IMPLEMENT**: Session document for individual learning sessions
- **PATTERN**: Mirror `server/app/models/user.py` structure
- **IMPORTS**: `datetime`, `typing.Literal`, `beanie.Document`, `beanie.PydanticObjectId`, `pydantic.Field`
- **FIELDS**:
  - `roadmap_id: PydanticObjectId` (Indexed)
  - `order: int` (session number 1, 2, 3...)
  - `title: str`
  - `content: str` (markdown content)
  - `status: Literal["not_started", "in_progress", "done", "skipped"]` = "not_started"
  - `notes: str` = "" (user's notes)
  - `created_at`, `updated_at`: datetime
- **VALIDATE**: `cd server && ./venv/bin/python -c "from app.models.session import Session; print('Session model OK')"`

#### 1.4 UPDATE `server/app/models/__init__.py`

- **IMPLEMENT**: Export all models for easy importing
- **ADD**: Exports for Draft, Roadmap, SessionSummary, Session
- **VALIDATE**: `cd server && ./venv/bin/python -c "from app.models import User, Draft, Roadmap, Session; print('All models OK')"`

#### 1.5 UPDATE `server/app/database.py`

- **IMPLEMENT**: Register new models with Beanie
- **PATTERN**: Line 35-40 shows how to register models
- **ADD**: Import Draft, Roadmap, Session in init_db function
- **ADD**: Add to `document_models` list in `init_beanie()` call
- **GOTCHA**: Import inside function to avoid circular imports
- **VALIDATE**: `cd server && timeout 5 ./venv/bin/uvicorn app.main:app --port 8001 2>&1 | grep -E "(Database initialized|error)" || echo "Server started OK"`

---

### Phase 2: Backend API Endpoints

#### 2.1 CREATE `server/app/routers/drafts.py`

- **IMPLEMENT**: Draft creation endpoint
- **PATTERN**: Mirror `server/app/routers/auth.py` structure
- **ENDPOINTS**:
  - `POST /drafts` - Create draft from raw_text, return draft with id
  - `GET /drafts/{draft_id}` - Get draft by id (verify ownership)
- **SCHEMAS**:
  - `DraftCreate(BaseModel)`: raw_text (str, required)
  - `DraftResponse(BaseModel)`: id, user_id, raw_text, created_at
- **AUTH**: Use `Depends(get_current_user)` on all endpoints
- **GOTCHA**: Verify user owns draft before returning in GET
- **VALIDATE**: `cd server && ./venv/bin/python -c "from app.routers.drafts import router; print('Drafts router OK')"`

#### 2.2 CREATE `server/app/routers/roadmaps.py`

- **IMPLEMENT**: Roadmap CRUD endpoints
- **PATTERN**: Mirror `server/app/routers/auth.py` structure
- **ENDPOINTS**:
  - `GET /roadmaps` - List user's roadmaps (return list with session counts)
  - `POST /roadmaps` - Create roadmap from draft_id + title
  - `GET /roadmaps/{roadmap_id}` - Get roadmap detail (verify ownership)
  - `DELETE /roadmaps/{roadmap_id}` - Delete roadmap (verify ownership)
- **SCHEMAS**:
  - `RoadmapCreate(BaseModel)`: draft_id (str), title (str)
  - `RoadmapListItem(BaseModel)`: id, title, session_count, created_at
  - `RoadmapResponse(BaseModel)`: id, draft_id, title, summary, sessions, created_at, updated_at
- **AUTH**: Use `Depends(get_current_user)` on all endpoints
- **GOTCHA**: Convert PydanticObjectId to str in responses
- **VALIDATE**: `cd server && ./venv/bin/python -c "from app.routers.roadmaps import router; print('Roadmaps router OK')"`

#### 2.3 UPDATE `server/app/routers/__init__.py`

- **IMPLEMENT**: Export new routers
- **ADD**: Exports for drafts and roadmaps routers
- **VALIDATE**: `cd server && ./venv/bin/python -c "from app.routers import drafts, roadmaps; print('Routers OK')"`

#### 2.4 UPDATE `server/app/main.py`

- **IMPLEMENT**: Register new routers with app
- **PATTERN**: Line 79 shows router registration
- **ADD**: Import drafts and roadmaps routers
- **ADD**: `app.include_router(drafts.router, prefix="/api/v1")`
- **ADD**: `app.include_router(roadmaps.router, prefix="/api/v1")`
- **VALIDATE**: `cd server && timeout 5 ./venv/bin/uvicorn app.main:app --port 8001 2>&1 | grep -E "(error|Error)" || echo "Server started OK"`

#### 2.5 VALIDATE Backend API

- **TEST**: Start server and verify endpoints appear in OpenAPI docs
- **VALIDATE**: `cd server && timeout 5 ./venv/bin/uvicorn app.main:app --port 8001 & sleep 2 && curl -s http://localhost:8001/docs | grep -o "roadmaps\|drafts" | head -2 && kill %1 2>/dev/null`

---

### Phase 3: Frontend Setup

#### 3.1 CREATE Vite Project

- **IMPLEMENT**: Scaffold React + TypeScript project
- **COMMAND**: `cd /Users/talis1/Documents/personal_projects/roadmap_builder && npm create vite@latest client -- --template react-ts`
- **VALIDATE**: `ls client/package.json && echo "Vite project created"`

#### 3.2 INSTALL Dependencies

- **IMPLEMENT**: Install all required packages
- **COMMAND**: `cd client && npm install @tanstack/react-query react-router-dom firebase && npm install -D tailwindcss postcss autoprefixer @types/react-router-dom`
- **VALIDATE**: `cd client && cat package.json | grep -E "tanstack|firebase|tailwind" | head -3`

#### 3.3 CONFIGURE Tailwind CSS

- **IMPLEMENT**: Initialize and configure Tailwind
- **COMMAND**: `cd client && npx tailwindcss init -p`
- **UPDATE** `client/tailwind.config.js`:
  ```javascript
  /** @type {import('tailwindcss').Config} */
  export default {
    content: [
      "./index.html",
      "./src/**/*.{js,ts,jsx,tsx}",
    ],
    theme: {
      extend: {},
    },
    plugins: [],
  }
  ```
- **UPDATE** `client/src/index.css`:
  ```css
  @tailwind base;
  @tailwind components;
  @tailwind utilities;
  ```
- **VALIDATE**: `cat client/tailwind.config.js | grep content`

#### 3.4 CREATE Environment Files

- **CREATE** `client/.env.example`:
  ```
  VITE_FIREBASE_API_KEY=
  VITE_FIREBASE_AUTH_DOMAIN=
  VITE_FIREBASE_PROJECT_ID=
  VITE_API_BASE_URL=http://localhost:8000
  ```
- **CREATE** `client/.env` with actual Firebase config (ask user for values)
- **GOTCHA**: Never commit .env, only .env.example
- **VALIDATE**: `ls client/.env.example && echo "Env template created"`

#### 3.5 UPDATE .gitignore

- **IMPLEMENT**: Ensure client/.env is ignored
- **UPDATE** root `.gitignore`: Add `client/.env` and `client/node_modules/`
- **VALIDATE**: `grep "client/.env" .gitignore`

---

### Phase 4: Frontend Auth

#### 4.1 CREATE `client/src/services/firebase.ts`

- **IMPLEMENT**: Firebase initialization
- **IMPORTS**: `firebase/app`, `firebase/auth`
- **EXPORTS**: `auth`, `googleProvider`
- **PATTERN**: Use `import.meta.env.VITE_*` for config
- **VALIDATE**: `cat client/src/services/firebase.ts | grep initializeApp`

#### 4.2 CREATE `client/src/context/AuthContext.tsx`

- **IMPLEMENT**: Auth state management with React Context
- **FEATURES**:
  - Track current user and loading state
  - `signInWithGoogle()` function
  - `signOut()` function
  - `getIdToken()` for API calls
- **PATTERN**: Use `onAuthStateChanged` listener
- **EXPORTS**: `AuthProvider`, `useAuth` hook
- **VALIDATE**: `cat client/src/context/AuthContext.tsx | grep useAuth`

#### 4.3 CREATE `client/src/components/layout/ProtectedRoute.tsx`

- **IMPLEMENT**: Route guard component
- **LOGIC**: If loading → show spinner; if no user → redirect to /login; else → render children
- **IMPORTS**: `useAuth`, `Navigate` from react-router-dom
- **VALIDATE**: `cat client/src/components/layout/ProtectedRoute.tsx | grep Navigate`

#### 4.4 CREATE `client/src/pages/LoginPage.tsx`

- **IMPLEMENT**: Login page with Google sign-in button
- **FEATURES**:
  - "Sign in with Google" button
  - Redirect to dashboard after successful login
  - Show error if login fails
- **STYLING**: Centered card with Tailwind
- **VALIDATE**: `cat client/src/pages/LoginPage.tsx | grep signInWithGoogle`

---

### Phase 5: Frontend Core Features

#### 5.1 CREATE `client/src/services/api.ts`

- **IMPLEMENT**: API client with auth token injection
- **FEATURES**:
  - Base URL from environment
  - `request()` function that adds Authorization header
  - Error handling (throw on non-2xx)
- **PATTERN**: Get token via `auth.currentUser?.getIdToken()`
- **EXPORTS**: `fetchRoadmaps`, `createDraft`, `createRoadmap`, `fetchRoadmap`, `deleteRoadmap`
- **VALIDATE**: `cat client/src/services/api.ts | grep Authorization`

#### 5.2 CREATE `client/src/hooks/useRoadmaps.ts`

- **IMPLEMENT**: TanStack Query hooks for roadmaps
- **HOOKS**:
  - `useRoadmaps()` - fetch list
  - `useRoadmap(id)` - fetch single
  - `useCreateRoadmap()` - mutation
  - `useDeleteRoadmap()` - mutation
- **PATTERN**: Invalidate queries on mutations
- **VALIDATE**: `cat client/src/hooks/useRoadmaps.ts | grep useQuery`

#### 5.3 CREATE `client/src/pages/DashboardPage.tsx`

- **IMPLEMENT**: Dashboard showing roadmap list
- **FEATURES**:
  - Header with user info and logout button
  - "Create New Roadmap" button
  - List of roadmaps as cards (title, session count, date)
  - Empty state if no roadmaps
  - Loading and error states
- **STYLING**: Grid layout with Tailwind
- **VALIDATE**: `cat client/src/pages/DashboardPage.tsx | grep useRoadmaps`

#### 5.4 CREATE `client/src/pages/CreateRoadmapPage.tsx`

- **IMPLEMENT**: Form to create roadmap from pasted text
- **FEATURES**:
  - Title input field
  - Large textarea for pasting raw text
  - Submit button (creates Draft, then Roadmap)
  - Cancel button (back to dashboard)
  - Loading state during submission
- **FLOW**:
  1. User fills form
  2. POST /drafts with raw_text → get draft_id
  3. POST /roadmaps with draft_id + title → get roadmap
  4. Navigate to roadmap detail or dashboard
- **VALIDATE**: `cat client/src/pages/CreateRoadmapPage.tsx | grep createDraft`

#### 5.5 CREATE `client/src/pages/RoadmapDetailPage.tsx`

- **IMPLEMENT**: View single roadmap
- **FEATURES**:
  - Back button to dashboard
  - Roadmap title and metadata
  - Raw text display (from draft - fetch separately or include in response)
  - Delete button with confirmation
  - Placeholder for sessions (coming later)
- **STYLING**: Clean layout with Tailwind
- **VALIDATE**: `cat client/src/pages/RoadmapDetailPage.tsx | grep useRoadmap`

---

### Phase 6: Integration & Polish

#### 6.1 CREATE `client/src/components/layout/Layout.tsx`

- **IMPLEMENT**: App shell with header
- **FEATURES**:
  - Header with app name, user avatar, logout
  - Main content area (Outlet)
  - Consistent padding and max-width
- **VALIDATE**: `cat client/src/components/layout/Layout.tsx | grep Outlet`

#### 6.2 UPDATE `client/src/App.tsx`

- **IMPLEMENT**: Main app with routing
- **SETUP**:
  - QueryClientProvider for TanStack Query
  - AuthProvider
  - BrowserRouter with Routes
- **ROUTES**:
  - `/login` → LoginPage
  - `/` → ProtectedRoute → Layout → DashboardPage
  - `/create` → ProtectedRoute → Layout → CreateRoadmapPage
  - `/roadmaps/:id` → ProtectedRoute → Layout → RoadmapDetailPage
- **VALIDATE**: `cat client/src/App.tsx | grep BrowserRouter`

#### 6.3 UPDATE `client/src/main.tsx`

- **IMPLEMENT**: Entry point with providers
- **ENSURE**: Import index.css for Tailwind
- **VALIDATE**: `cat client/src/main.tsx | grep index.css`

#### 6.4 CREATE `client/src/types/index.ts`

- **IMPLEMENT**: TypeScript types for API responses
- **TYPES**:
  - `Draft`: id, user_id, raw_text, created_at
  - `RoadmapListItem`: id, title, session_count, created_at
  - `Roadmap`: id, draft_id, title, summary, sessions, created_at, updated_at
  - `SessionSummary`: id, title, order
- **VALIDATE**: `cat client/src/types/index.ts | grep Roadmap`

#### 6.5 CLEANUP Default Files

- **REMOVE**: Default Vite files not needed
  - `client/src/App.css` (using Tailwind)
  - `client/src/assets/react.svg` (not used)
- **UPDATE**: Remove default content from `client/src/index.css` except Tailwind directives
- **VALIDATE**: `ls client/src/App.css 2>/dev/null || echo "Cleanup done"`

#### 6.6 UPDATE `server/app/config.py`

- **IMPLEMENT**: Add client origin to CORS
- **UPDATE**: Change default `cors_origins` to include `["http://localhost:5173", "http://localhost:3000"]`
- **VALIDATE**: `grep "5173" server/app/config.py`

---

## TESTING STRATEGY

### Unit Tests (Backend)

- Test Draft model creation
- Test Roadmap model with SessionSummary
- Test Session model with status literals
- Test router response schemas

### Integration Tests (Backend)

- Test POST /drafts creates draft and returns id
- Test POST /roadmaps creates roadmap with draft reference
- Test GET /roadmaps returns only user's roadmaps
- Test GET /roadmaps/:id returns 404 for other user's roadmap
- Test DELETE /roadmaps/:id removes roadmap

### Manual Testing (Frontend)

- Login flow: Click Google sign-in → redirect to dashboard
- Create flow: Fill form → submit → see roadmap in list
- View flow: Click roadmap → see detail page
- Delete flow: Click delete → confirm → roadmap removed
- Logout flow: Click logout → redirect to login

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
cd client && npm run lint

# Frontend type checking
cd client && npx tsc --noEmit
```

### Level 2: Backend Tests

```bash
cd server && ./venv/bin/pytest
```

### Level 3: Server Startup

```bash
# Verify backend starts without errors
cd server && timeout 5 ./venv/bin/uvicorn app.main:app --port 8001 2>&1 | grep -E "(error|Error)" || echo "Backend OK"

# Verify frontend builds
cd client && npm run build
```

### Level 4: Manual Validation

1. Start backend: `cd server && ./venv/bin/uvicorn app.main:app --reload`
2. Start frontend: `cd client && npm run dev`
3. Open http://localhost:5173
4. Test login with Google
5. Create a roadmap with test text
6. View the roadmap
7. Delete the roadmap
8. Logout

---

## ACCEPTANCE CRITERIA

- [ ] Backend models (Draft, Roadmap, Session) created and registered with Beanie
- [ ] API endpoints for drafts and roadmaps work with authentication
- [ ] React frontend scaffolded with Vite + TypeScript + Tailwind
- [ ] Firebase Google sign-in works
- [ ] Dashboard shows user's roadmaps
- [ ] Create roadmap form saves draft and creates roadmap
- [ ] Roadmap detail page displays roadmap info
- [ ] Delete roadmap works with confirmation
- [ ] Protected routes redirect unauthenticated users to login
- [ ] All validation commands pass with zero errors
- [ ] Code follows project conventions and patterns

---

## COMPLETION CHECKLIST

- [ ] All tasks completed in order
- [ ] Each task validation passed immediately
- [ ] All validation commands executed successfully
- [ ] Full test suite passes
- [ ] No linting or type checking errors
- [ ] Manual testing confirms feature works
- [ ] Acceptance criteria all met
- [ ] README.md updated with current status
- [ ] CLAUDE.md updated if new patterns introduced

---

## NOTES

### Data Model Decisions

The data model was designed based on user discussion:
- **Draft** stores raw pasted text, used once for parsing, kept separate to avoid bloating Roadmap
- **Roadmap** contains lightweight `sessions[]` array with just id, title, order for quick listing
- **Session** is a separate collection with full content, notes, status - accessed independently

### Deferred Features

- AI parsing of Draft → Sessions (Phase 3)
- Session status updates and notes editing
- Progress tracking and visualization
- AI chat assistant

### Firebase Configuration Required

Before running the frontend, the user must:
1. Create a Firebase project at https://console.firebase.google.com
2. Enable Google sign-in in Authentication
3. Add web app and copy config values to `client/.env`
4. Add `http://localhost:5173` to authorized domains

### API Design

All endpoints require authentication. User isolation is enforced:
- Drafts: filtered by user_id
- Roadmaps: filtered by user_id
- Sessions: accessed via roadmap which is filtered by user_id
