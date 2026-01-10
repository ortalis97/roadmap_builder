# Learning Roadmap App

A focused tool for self-directed learners to turn messy learning plans into clear, trackable roadmaps with an AI assistant embedded directly into the learning flow.

## Overview

Paste a messy learning plan → Get a structured roadmap → Track your progress → Get contextual AI help — all in one place.

See [PRD.md](PRD.md) for the complete product vision, user stories, and detailed requirements.

## Current Status

### Implemented ✅

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
- Draft, Roadmap, Session Beanie document models
- `/api/v1/drafts` endpoint (create, get)
- `/api/v1/roadmaps` endpoints (list, create, get, delete)
- React + Vite + TypeScript + Tailwind frontend
- Firebase client-side auth (Google OAuth)
- Dashboard showing user's roadmaps
- Create roadmap form (paste raw text)
- Roadmap detail view with delete

### Planned 📋

- Phase 3: AI Session Parsing (parse draft into structured sessions)
- Phase 4: Progress & Notes (session tracking, notes editor)
- Phase 5: AI Assistant & Polish (contextual chat, mobile responsive)

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
│   │   │   ├── drafts.py       # Draft endpoints
│   │   │   └── roadmaps.py     # Roadmap endpoints
│   │   └── models/
│   │       ├── user.py         # User document model
│   │       ├── draft.py        # Draft document model
│   │       ├── roadmap.py      # Roadmap document model
│   │       └── session.py      # Session document model
│   ├── venv/                   # Python virtual environment
│   ├── requirements.txt
│   └── .env                    # Environment variables (not committed)
├── client/                     # React frontend
│   ├── src/
│   │   ├── components/         # Reusable UI components
│   │   ├── context/            # React context (AuthContext)
│   │   ├── hooks/              # Custom hooks (useRoadmaps)
│   │   ├── pages/              # Route pages
│   │   ├── services/           # API client, Firebase
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
