# Learning Roadmap App

A focused tool for self-directed learners to turn messy learning plans into clear, trackable roadmaps with an AI assistant embedded directly into the learning flow.

## Important: Keep Documentation Updated

**After completing each implementation phase, update these files:**

1. **`README.md`** — Update the "Current Status" section to reflect what's implemented
2. **`CLAUDE.md`** — Update project structure if new directories/files are added

This ensures the documentation stays in sync with the actual codebase.

## Tech Stack

- **Backend**: Python 3.11+, FastAPI, Beanie ODM, Motor (async MongoDB)
- **Frontend**: React 18, Vite, TypeScript, Tailwind CSS, TanStack Query
- **Database**: MongoDB Atlas
- **Auth**: Firebase Auth (Google OAuth)
- **AI**: Gemini API (google-generativeai)
- **Testing**: pytest (backend), Vitest (frontend), Playwright (E2E)

## Project Structure

```
roadmap_builder/
├── client/                     # React frontend (not yet created)
│   ├── src/
│   │   ├── components/         # Reusable UI components
│   │   ├── pages/              # Route-level components
│   │   ├── hooks/              # Custom React hooks
│   │   ├── services/           # API client functions
│   │   ├── context/            # React context providers
│   │   ├── types/              # TypeScript types
│   │   └── utils/              # Helper functions
│   ├── public/
│   ├── index.html
│   └── package.json
├── server/                     # Python FastAPI backend
│   ├── app/
│   │   ├── __init__.py
│   │   ├── main.py             # FastAPI app entry point
│   │   ├── config.py           # Settings (Pydantic BaseSettings)
│   │   ├── database.py         # MongoDB connection (Motor + Beanie)
│   │   ├── models/             # Pydantic + Beanie models
│   │   │   ├── __init__.py
│   │   │   └── user.py         # User document model
│   │   ├── routers/            # API route handlers (to be added)
│   │   ├── services/           # Business logic (to be added)
│   │   ├── middleware/         # Auth verification (to be added)
│   │   └── utils/
│   ├── venv/                   # Python virtual environment
│   ├── tests/
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

# Frontend - Install dependencies
cd client && npm install

# Frontend - Run development server
cd client && npm run dev

# Frontend - Run tests
cd client && npm test

# Frontend - Build for production
cd client && npm run build

# Frontend - Lint
cd client && npm run lint
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

## Reference Documentation

| Document | When to Read |
|----------|--------------|
| `README.md` | Current implementation status, quick start guide |
| `PRD.md` | Understanding requirements, features, user stories, API spec |
| `.claude/reference/` | Best practices for FastAPI, React, testing |

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
Roadmap(user_id, title, summary, sessions[], created_at, updated_at, last_accessed_at)

# Session - embedded in Roadmap
Session(id, title, content, status, notes, order)

# ChatHistory - separate collection
ChatHistory(roadmap_id, session_id, messages[])
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
