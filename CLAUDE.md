# Learning Roadmap App

A focused tool for self-directed learners to turn messy learning plans into clear, trackable roadmaps with an AI assistant embedded directly into the learning flow.

## Important: Keep Documentation Updated

**After completing each implementation phase, update these files:**

1. **`README.md`** — Update the "Current Status" section to reflect what's implemented
2. **`CLAUDE.md`** — Update project structure if new directories/files are added

This ensures the documentation stays in sync with the actual codebase.

## Documentation Maintenance

**Keep learnings and best practices organized:**

1. **Implementation learnings** should go in `.claude/reference/` files, NOT inline in CLAUDE.md
   - General patterns reusable across projects → dedicated reference file
   - Project-specific quirks → can stay in CLAUDE.md briefly, then move to reference
2. **CLAUDE.md should focus on** project-specific instructions: structure, commands, conventions
3. **Reference files** should be self-contained guides that work independently

When you discover a reusable pattern or workaround:
1. Create or update the appropriate `.claude/reference/*.md` file
2. Add the file to the Reference Documentation table below
3. Keep CLAUDE.md lean and focused on this project

## Important: Ask for Required Information

**When implementing features that require external configuration or credentials:**

1. **DO NOT** complete implementation with warnings or graceful degradation
2. **DO** actively ask the user for the required information before marking complete
3. **DO** wait for the user to provide credentials/config, then validate with it working
4. **DO** help guide the user through obtaining what's needed (e.g., step-by-step instructions)

Examples:
- Firebase Auth → Ask for service account JSON before validation
- MongoDB → Ask for connection string before validation
- API keys → Ask user to provide them before testing

**Only mark a feature complete when it's fully validated and working.**

## Important: Ask Clarifying Questions One by One

**When gathering requirements or clarifying ambiguities before implementation:**

1. **DO NOT** dump all questions at once — it overwhelms and leads to incomplete answers
2. **DO** ask questions one at a time, waiting for the user's response before the next
3. **DO** use the previous answer to inform follow-up questions
4. **DO** summarize collected answers before proceeding to implementation

This creates a conversational flow that produces better, more thoughtful requirements.

## Tech Stack

- **Backend**: Python 3.11+, FastAPI, Beanie ODM, Motor (async MongoDB)
- **Frontend**: React 18, Vite, TypeScript, Tailwind CSS, TanStack Query
- **Database**: MongoDB Atlas
- **Auth**: Firebase Auth (Google OAuth)
- **AI**: Gemini API (google-genai SDK)
- **Testing**: pytest (backend), Vitest (frontend), Playwright (E2E)

## Project Structure

```
roadmap_builder/
├── client/                     # React frontend
│   ├── src/
│   │   ├── components/         # Reusable UI components
│   │   │   ├── layout/         # Layout, ProtectedRoute
│   │   │   └── creation/       # Roadmap creation flow components
│   │   ├── pages/              # Route-level components
│   │   ├── hooks/              # Custom React hooks
│   │   ├── services/           # API client, Firebase, SSE client
│   │   ├── context/            # React context (AuthContext)
│   │   ├── types/              # TypeScript types
│   │   ├── App.tsx             # Main app with routing
│   │   └── main.tsx            # Entry point
│   ├── public/
│   ├── index.html
│   ├── package.json
│   └── .env.example
├── server/                     # Python FastAPI backend
│   ├── app/
│   │   ├── __init__.py
│   │   ├── main.py             # FastAPI app entry point
│   │   ├── config.py           # Settings (Pydantic BaseSettings)
│   │   ├── model_config.py     # LLM model assignments per agent
│   │   ├── database.py         # MongoDB connection (Motor + Beanie)
│   │   ├── models/             # Pydantic + Beanie models
│   │   │   ├── __init__.py
│   │   │   ├── user.py         # User document model
│   │   │   ├── roadmap.py      # Roadmap document model
│   │   │   ├── session.py      # Session document model
│   │   │   ├── chat_history.py # Chat history model
│   │   │   └── agent_trace.py  # Agent trace for debugging
│   │   ├── routers/            # API route handlers
│   │   │   ├── __init__.py
│   │   │   ├── auth.py         # Auth endpoints (/auth/me)
│   │   │   ├── roadmaps.py     # Roadmap/session endpoints
│   │   │   ├── roadmaps_create.py # Multi-agent creation pipeline
│   │   │   └── chat.py         # AI chat endpoints
│   │   ├── agents/             # Multi-agent pipeline
│   │   │   ├── __init__.py
│   │   │   ├── base.py         # Base agent class
│   │   │   ├── interviewer.py  # Interview question generation
│   │   │   ├── architect.py    # Session structure design
│   │   │   ├── researcher.py   # Session content creation
│   │   │   ├── validator.py    # Quality validation
│   │   │   ├── orchestrator.py # Pipeline coordination
│   │   │   ├── prompts.py      # Agent prompts
│   │   │   └── state.py        # Pipeline state models
│   │   ├── services/           # Business logic
│   │   │   ├── __init__.py
│   │   │   └── ai_service.py   # Gemini AI integration
│   │   ├── middleware/         # Auth verification
│   │   │   ├── __init__.py
│   │   │   └── auth.py         # Firebase token verification
│   │   └── utils/
│   ├── venv/                   # Python virtual environment
│   ├── tests/
│   │   ├── unit/               # Unit tests
│   │   ├── integration/        # Integration tests
│   │   └── conftest.py         # Test fixtures
│   ├── requirements.txt
│   ├── pyproject.toml
│   └── .env.example
├── .agents/plans/              # Implementation plans
├── PRD.md                      # Product requirements document
├── README.md                   # Project overview and status
└── CLAUDE.md                   # This file
```

## Virtual Environment Setup

**IMPORTANT**: Always use a virtual environment for Python dependencies.

```bash
# Create venv (one-time setup)
cd server && python3 -m venv venv

# Activate venv (do this before running any Python commands)
source server/venv/bin/activate

# Or use venv binaries directly without activating
./server/venv/bin/python
./server/venv/bin/pip
./server/venv/bin/uvicorn
./server/venv/bin/ruff
```

## Commands

```bash
# Backend - Install dependencies (using venv)
cd server && ./venv/bin/pip install -r requirements.txt

# Backend - Run development server
cd server && ./venv/bin/uvicorn app.main:app --reload --port 8000

# Backend - Run tests
cd server && ./venv/bin/pytest

# Backend - Lint/format
cd server && ./venv/bin/ruff check app/ && ./venv/bin/ruff format app/

# Frontend - Install dependencies (using bun)
cd client && ~/.bun/bin/bun install

# Frontend - Run development server
cd client && ~/.bun/bin/bun run dev

# Frontend - Run tests
cd client && ~/.bun/bin/bun test

# Frontend - Build for production
cd client && ~/.bun/bin/bun run build

# Frontend - Lint
cd client && ~/.bun/bin/bun run lint
```

## MCP Servers

**Playwright MCP** is available for browser automation and E2E testing:
```bash
claude mcp add playwright npx @playwright/mcp@latest
```

Use Playwright MCP for:
- E2E testing of user flows (login, create roadmap, track progress)
- Visual regression testing
- Cross-browser testing

## Tool Restrictions

**DO NOT use Meta-specific tools or plugins in this project:**
- Do NOT use `mcp__plugin_meta_*` tools (meta_devmate, meta_www, etc.)
- Do NOT use `meta:code_search` agent type
- Use standard tools instead: `Read`, `Grep`, `Glob`, `WebSearch`, `WebFetch`, `Explore` agent

## Reference Documentation

| Document | When to Read |
|----------|--------------|
| `README.md` | Current implementation status, quick start guide |
| `PRD.md` | Understanding requirements, features, user stories, API spec |
| `.claude/reference/fastapi-best-practices.md` | FastAPI patterns, Pydantic, async, testing |
| `.claude/reference/react-frontend-best-practices.md` | React, TypeScript, Tailwind, TanStack Query |
| `.claude/reference/gemini-api-best-practices.md` | Gemini SDK, structured output, Pydantic integration |
| `.claude/reference/bun-package-manager.md` | Bun commands, Playwright setup (npm restricted) |
| `.claude/reference/testing-and-logging.md` | pytest, Vitest, logging patterns |

## Code Conventions

### Backend (Python)
- Use type hints for all function signatures
- Pydantic models for request/response validation
- Async functions for all I/O operations (database, external APIs)
- Routers grouped by domain (auth, roadmaps, ai)
- Services contain business logic, routers are thin
- Use `ruff` for linting and formatting
- Environment variables via Pydantic `BaseSettings`

### Frontend (React/TypeScript)
- Functional components with hooks
- TanStack Query for server state (no manual fetch/useState for API data)
- Tailwind CSS for styling (no CSS modules or styled-components)
- TypeScript strict mode enabled
- Components organized by feature in `pages/`, reusable pieces in `components/`
- API calls abstracted in `services/` directory

### API Design
- RESTful endpoints under `/api/v1`
- Firebase ID token in `Authorization: Bearer <token>` header
- Pydantic models for request validation and response serialization
- Consistent error response format: `{ "detail": "error message" }`
- Use HTTP status codes correctly (201 for create, 204 for delete, etc.)

## Logging

### Backend
- Use Python's `logging` module
- Log levels: DEBUG (dev), INFO (prod)
- Log all API requests with timing
- Log AI service calls (input length, response time, success/failure)
- Sensitive data (tokens, API keys) must never be logged

### Frontend
- Console logging in development only
- Error boundary for catching React errors
- Report errors to console with context (component, action)

## Database

### MongoDB Atlas
- Connection via Motor (async driver) + Beanie ODM
- Collections: `users`, `roadmaps`, `chat_histories`
- Sessions embedded in Roadmap documents (accessed together)
- Chat history in separate collection (can grow large)
- Indexes: `users.firebase_uid` (unique), `roadmaps.user_id`

### Models
```python
# User - created on first login
User(firebase_uid, email, name, picture, created_at, updated_at)

# Roadmap - main learning journey
Roadmap(user_id, title, summary, sessions[], created_at, updated_at)

# Session - separate collection, linked to roadmap
Session(roadmap_id, order, title, content, status, notes, created_at, updated_at)

# ChatHistory - separate collection
ChatHistory(roadmap_id, session_id, messages[])

# AgentTrace - for debugging pipeline runs
AgentTrace(pipeline_id, user_id, initial_topic, initial_title, events[], started_at, completed_at)
```

## Testing Strategy

### Testing Pyramid
- **Unit tests**: Business logic in services, utility functions, Pydantic models
- **Integration tests**: API endpoints with test database, Firebase token mocking
- **E2E tests**: Full user flows via Playwright (login → create roadmap → complete session)

### Test Organization
```
server/tests/
├── unit/
│   ├── test_ai_service.py
│   └── test_roadmap_service.py
├── integration/
│   ├── test_roadmaps_api.py
│   └── test_auth_api.py
└── conftest.py              # Fixtures, test database setup

client/src/
├── __tests__/               # Component tests with Vitest
└── e2e/                     # Playwright E2E tests
```

### Testing Notes
- Backend: Use pytest-asyncio for async tests
- Mock Firebase token verification in integration tests
- Mock Gemini API calls in unit tests (don't hit real API)
- E2E tests run against local dev servers
- Use Playwright MCP for E2E test development and debugging

## Implementation Learnings

**For reusable patterns and best practices, see the reference files in `.claude/reference/`.**

When learning approaches that don't work well during development:
1. Check if there's an existing reference file for the topic
2. Add to the appropriate `.claude/reference/*.md` file
3. Update the Reference Documentation table above
