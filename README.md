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

### In Progress 🚧

**Phase C: Authentication**
- Firebase Auth integration (Google OAuth)
- Token verification middleware
- Protected API routes

### Planned 📋

- Phase 2: Core Roadmap Features (create, view, AI generation)
- Phase 3: Progress & Notes (session tracking, notes editor)
- Phase 4: AI Assistant & Polish (contextual chat, mobile responsive)

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
│   │   └── models/
│   │       └── user.py         # User document model
│   ├── venv/                   # Python virtual environment
│   ├── requirements.txt
│   └── .env                    # Environment variables (not committed)
├── client/                     # React frontend (not yet created)
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

## Development

See [CLAUDE.md](CLAUDE.md) for detailed development instructions, conventions, and commands.

### Key Commands

```bash
# Backend
cd server && ./venv/bin/uvicorn app.main:app --reload    # Run dev server
cd server && ./venv/bin/pytest                            # Run tests
cd server && ./venv/bin/ruff check app/                   # Lint code

# Frontend (when implemented)
cd client && npm run dev                                  # Run dev server
cd client && npm test                                     # Run tests
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
