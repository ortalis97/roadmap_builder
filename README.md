# Learning Roadmap App

A focused tool for self-directed learners to turn messy learning plans into clear, trackable roadmaps with an AI assistant embedded directly into the learning flow.

## Overview

Paste a messy learning plan → Get a structured roadmap → Track your progress → Get contextual AI help — all in one place.

See [PRD.md](PRD.md) for the complete product vision, user stories, and detailed requirements.

## Current Status

### Implemented

**Phase A: Backend Skeleton**
- FastAPI application with health endpoint
- Pydantic BaseSettings configuration
- Structured logging with structlog
- CORS middleware configured

**Phase B: Database Integration**
- MongoDB connection via Motor (async driver)
- Beanie ODM for document models
- User model with firebase_uid index
- Database lifecycle management (init/close)

**Phase C: Authentication**
- Firebase Admin SDK for token verification
- Auth middleware with `get_current_user` dependency
- `/api/v1/auth/me` endpoint (returns/creates user)
- Graceful degradation when Firebase not configured

**Phase 2: Basic UI & Roadmap Storage**
- Roadmap, Session Beanie document models
- `/api/v1/roadmaps` endpoints (list, get, delete)
- React + Vite + TypeScript + Tailwind frontend
- Firebase client-side auth (Google OAuth)
- Dashboard showing user's roadmaps
- Roadmap detail view with delete

**Phase 3: AI-Powered Roadmap Creation**
- Multi-agent pipeline for intelligent roadmap generation:
  - **Interviewer Agent**: Asks clarifying questions about learning goals
  - **Architect Agent**: Designs session structure and generates descriptive title
  - **Researcher Agents**: Creates detailed content for each session type
  - **Validator Agent**: Checks for gaps, overlaps, and coherence
- Simplified "What do you want to learn?" chat-like input
- AI-generated roadmap titles with user confirmation
- Server-Sent Events (SSE) for real-time progress streaming
- Validation review step before saving

**Phase 4: Progress & Notes**
- Session status tracking (not_started, in_progress, done, skipped)
- Progress percentage calculation
- Notes editor per session

**Phase 5: AI Assistant**
- Contextual AI chat assistant per session
- Chat history persistence
- Real-time AI responses with context awareness

### Planned

**High Priority:**
- **Better YouTube video grounding** - Current Gemini-based search returns non-existing videos frequently. Integrate Tavily API or similar search tool for reliable video discovery with URL verification.
- **Mobile support (iOS/Android)** - Responsive design optimizations for phone screens. Ensure touch-friendly interactions, proper viewport handling, and mobile navigation patterns.
- **Improved Hebrew RTL support** - Interview question option buttons don't align correctly for Hebrew text. Apply RTL layout detection to interview components similar to session list fix.

**Future:**
- Markdown rendering for session content (content is generated with markdown but not rendered)
- Export/import functionality
- Sharing roadmaps

## Tech Stack

| Layer | Technology |
|-------|------------|
| **Frontend** | React 18, Vite, TypeScript, Tailwind CSS, TanStack Query |
| **Backend** | Python 3.11+, FastAPI, Pydantic, Uvicorn |
| **Database** | MongoDB Atlas, Motor, Beanie ODM |
| **Auth** | Firebase Auth (Google OAuth) |
| **AI** | Gemini API |

## Project Structure

```
roadmap_builder/
├── server/                     # Python FastAPI backend
│   ├── app/
│   │   ├── main.py             # FastAPI app entry point
│   │   ├── config.py           # Pydantic settings
│   │   ├── database.py         # MongoDB connection
│   │   ├── middleware/
│   │   │   └── auth.py         # Firebase token verification
│   │   ├── routers/
│   │   │   ├── auth.py         # Auth endpoints (/auth/me)
│   │   │   ├── roadmaps.py     # Roadmap/session endpoints
│   │   │   ├── roadmaps_create.py # Multi-agent creation pipeline
│   │   │   └── chat.py         # AI chat endpoints
│   │   ├── agents/             # Multi-agent pipeline
│   │   │   ├── base.py         # Base agent class
│   │   │   ├── interviewer.py  # Interview question generation
│   │   │   ├── architect.py    # Session structure design
│   │   │   ├── researcher.py   # Session content creation
│   │   │   ├── validator.py    # Quality validation
│   │   │   ├── orchestrator.py # Pipeline coordination
│   │   │   ├── prompts.py      # Agent prompts
│   │   │   └── state.py        # Pipeline state models
│   │   ├── models/
│   │   │   ├── user.py         # User document model
│   │   │   ├── roadmap.py      # Roadmap document model
│   │   │   ├── session.py      # Session document model
│   │   │   ├── chat_history.py # Chat history model
│   │   │   └── agent_trace.py  # Agent trace model
│   │   └── services/
│   │       └── ai_service.py   # Gemini API integration
│   ├── tests/                  # Test suite
│   ├── venv/                   # Python virtual environment
│   ├── requirements.txt
│   └── .env                    # Environment variables (not committed)
├── client/                     # React frontend
│   ├── src/
│   │   ├── components/         # Reusable UI components
│   │   │   ├── creation/       # Roadmap creation components
│   │   │   └── layout/         # Layout components
│   │   ├── context/            # React context (AuthContext)
│   │   ├── hooks/              # Custom hooks
│   │   ├── pages/              # Route pages
│   │   ├── services/           # API client, Firebase, SSE
│   │   └── types/              # TypeScript types
│   ├── package.json
│   └── .env                    # Firebase config (not committed)
├── PRD.md                      # Product requirements document
├── CLAUDE.md                   # Development instructions
└── README.md                   # This file
```

## Quick Start

### Prerequisites

- Python 3.11+
- Docker (for local MongoDB) or MongoDB Atlas account
- Node.js 18+ (for frontend, when implemented)

### Backend Setup

```bash
# Navigate to server directory
cd server

# Create and activate virtual environment
python3 -m venv venv
source venv/bin/activate  # or ./venv/bin/activate

# Install dependencies
./venv/bin/pip install -r requirements.txt

# Copy environment template and configure
cp .env.example .env
# Edit .env with your MongoDB URI

# Start development server
./venv/bin/uvicorn app.main:app --reload --port 8000
```

### Local MongoDB (Docker)

```bash
# Start MongoDB container
docker run -d --name mongodb-test -p 27017:27017 mongo:7

# Use this connection string in .env
MONGODB_URI=mongodb://localhost:27017/roadmap_builder
```

### Verify Installation

```bash
# Health check
curl http://localhost:8000/health
# Expected: {"status":"healthy","environment":"development"}

# API docs
open http://localhost:8000/docs
```

### Frontend Setup

```bash
# Navigate to client directory
cd client

# Install dependencies (using bun)
~/.bun/bin/bun install

# Copy environment template and configure with Firebase credentials
cp .env.example .env
# Edit .env with your Firebase project config

# Start development server
~/.bun/bin/bun run dev
```

**Firebase Configuration Required:**
1. Create a Firebase project at https://console.firebase.google.com
2. Enable Google sign-in in Authentication > Sign-in method
3. Configure OAuth consent screen in Google Cloud Console
4. Add web app and copy config values to `client/.env`
5. Ensure `localhost` is in Authentication > Settings > Authorized domains

## Development

See [CLAUDE.md](CLAUDE.md) for detailed development instructions, conventions, and commands.

### Key Commands

```bash
# Backend
cd server && ./venv/bin/uvicorn app.main:app --reload         # Run dev server
cd server && ./venv/bin/pytest                                 # Run tests
cd server && ./venv/bin/ruff check app/                        # Lint code

# Frontend (using bun)
cd client && ~/.bun/bin/bun run dev                            # Run dev server
cd client && ~/.bun/bin/bun run build                          # Build for production
cd client && ~/.bun/bin/bun run lint                           # Lint code
```

---

## Claude Code Commands

This project uses Claude Code slash commands for development workflow:

### Planning & Execution
| Command | Description |
|---------|-------------|
| `/core_piv_loop:prime` | Load project context and codebase understanding |
| `/core_piv_loop:plan-feature` | Create comprehensive implementation plan |
| `/core_piv_loop:execute` | Execute an implementation plan step-by-step |

### Validation
| Command | Description |
|---------|-------------|
| `/validation:validate` | Run full validation: tests, linting, coverage |
| `/validation:code-review` | Technical code review on changed files |
| `/commit` | Create atomic commit with appropriate tag |

See `.claude/commands/` for all available commands.
