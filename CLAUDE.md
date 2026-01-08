# Learning Roadmap App

A focused tool for self-directed learners to turn messy learning plans into clear, trackable roadmaps with an AI assistant embedded directly into the learning flow.

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
├── client/                     # React frontend
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
│   │   ├── routers/            # API route handlers
│   │   │   ├── auth.py
│   │   │   ├── roadmaps.py
│   │   │   └── ai.py
│   │   ├── models/             # Pydantic + Beanie models
│   │   │   ├── user.py
│   │   │   ├── roadmap.py
│   │   │   └── chat.py
│   │   ├── services/           # Business logic
│   │   │   ├── ai_service.py
│   │   │   └── roadmap_service.py
│   │   ├── middleware/         # Auth verification, CORS
│   │   └── utils/
│   ├── tests/
│   ├── requirements.txt
│   └── pyproject.toml
├── docs/
├── PRD.md                      # Product requirements document
└── CLAUDE.md                   # This file
```

## Commands

```bash
# Backend - Install dependencies
cd server && pip install -r requirements.txt

# Backend - Run development server
cd server && uvicorn app.main:app --reload --port 8000

# Backend - Run tests
cd server && pytest

# Backend - Lint/format
cd server && ruff check . && ruff format .

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
| `PRD.md` | Understanding requirements, features, user stories, API spec |
| `initial_thoughts.txt` | Original product vision and core concepts |

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
