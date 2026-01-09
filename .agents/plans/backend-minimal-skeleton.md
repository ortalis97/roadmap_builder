# Feature: Backend Minimal Skeleton

The following plan should be complete, but it's important that you validate documentation and codebase patterns and task sanity before you start implementing.

## Feature Description

Create the minimal FastAPI backend skeleton with project configuration, environment settings, and a health check endpoint. This establishes the foundation for all future backend development with zero external dependencies (no database, no Firebase yet).

## User Story

As a developer
I want a running FastAPI server with proper project structure
So that I can incrementally add features on a solid foundation

## Problem Statement

The project has no backend code yet. We need the basic scaffolding before adding database, authentication, or any features.

## Solution Statement

Create a minimal Python/FastAPI project with:
- `pyproject.toml` for project metadata and dependencies
- `requirements.txt` for pip installation
- Pydantic BaseSettings for typed configuration
- FastAPI app with CORS and a `/health` endpoint
- Proper project structure for future expansion

## Feature Metadata

**Feature Type**: New Capability (Project Foundation)
**Estimated Complexity**: Low
**Primary Systems Affected**: Backend only
**Dependencies**: FastAPI, Pydantic, Uvicorn, structlog (all pip-installable, no external services)

---

## CONTEXT REFERENCES

### Relevant Codebase Files IMPORTANT: YOU MUST READ THESE FILES BEFORE IMPLEMENTING!

- `CLAUDE.md` - Project conventions and tech stack requirements
- `.claude/reference/fastapi-best-practices.md` - FastAPI patterns (sections 1, 2, 10, 11)

### New Files to Create

```
server/
├── pyproject.toml          # Project configuration
├── requirements.txt        # Dependencies
├── .env.example            # Environment template
└── app/
    ├── __init__.py         # Package init
    ├── config.py           # Pydantic settings
    └── main.py             # FastAPI app
```

### Relevant Documentation

- [FastAPI Documentation](https://fastapi.tiangolo.com/)
- [Pydantic Settings](https://docs.pydantic.dev/latest/concepts/pydantic_settings/)
- [structlog Documentation](https://www.structlog.org/)

### Patterns to Follow

**Naming Conventions:**
- Python: `snake_case` for functions/variables, `PascalCase` for classes
- Files: lowercase with underscores

**Configuration Pattern:**
```python
from functools import lru_cache
from pydantic_settings import BaseSettings

@lru_cache
def get_settings() -> Settings:
    return Settings()
```

**Logging Pattern:**
```python
import structlog
logger = structlog.get_logger()
logger.info("Server started", port=8000)
```

---

## IMPLEMENTATION PLAN

### Phase 1: Project Setup

Create the directory structure and configuration files.

**Tasks:**
- Create server directory structure
- Add pyproject.toml with dependencies
- Add requirements.txt

### Phase 2: Core Application

Create the FastAPI application with configuration.

**Tasks:**
- Create config.py with Pydantic settings
- Create main.py with FastAPI app and health endpoint

---

## STEP-BY-STEP TASKS

IMPORTANT: Execute every task in order, top to bottom. Each task is atomic and independently testable.

---

### Task 1: CREATE directory structure

- **IMPLEMENT**: Create the server/app directory structure
- **VALIDATE**: `ls -la server/app`

```bash
mkdir -p server/app
```

---

### Task 2: CREATE `server/pyproject.toml`

- **IMPLEMENT**: Python project configuration with minimal dependencies
- **PATTERN**: Standard pyproject.toml for FastAPI projects
- **GOTCHA**: Use Python 3.11+ as specified in PRD

```toml
[project]
name = "roadmap-builder-server"
version = "0.1.0"
description = "Learning Roadmap App Backend"
requires-python = ">=3.11"
dependencies = [
    "fastapi>=0.109.0",
    "uvicorn[standard]>=0.27.0",
    "pydantic>=2.0.0",
    "pydantic-settings>=2.0.0",
    "structlog>=24.1.0",
    "python-dotenv>=1.0.0",
]

[project.optional-dependencies]
dev = [
    "pytest>=8.0.0",
    "pytest-asyncio>=0.23.0",
    "httpx>=0.26.0",
    "ruff>=0.2.0",
]

[tool.ruff]
line-length = 100
target-version = "py311"

[tool.ruff.lint]
select = ["E", "F", "I", "N", "W", "UP"]

[tool.pytest.ini_options]
asyncio_mode = "auto"
testpaths = ["tests"]
```

- **VALIDATE**: `cat server/pyproject.toml`

---

### Task 3: CREATE `server/requirements.txt`

- **IMPLEMENT**: Pinned dependencies for pip install
- **PATTERN**: Match pyproject.toml dependencies

```
fastapi>=0.109.0
uvicorn[standard]>=0.27.0
pydantic>=2.0.0
pydantic-settings>=2.0.0
structlog>=24.1.0
python-dotenv>=1.0.0

# Development
pytest>=8.0.0
pytest-asyncio>=0.23.0
httpx>=0.26.0
ruff>=0.2.0
```

- **VALIDATE**: `cat server/requirements.txt`

---

### Task 4: CREATE `server/.env.example`

- **IMPLEMENT**: Environment variables template (minimal for now)
- **GOTCHA**: Never commit actual .env file

```
# Server
PORT=8000
ENVIRONMENT=development
CORS_ORIGINS=["http://localhost:5173"]

# These will be added in future phases:
# MONGODB_URI=mongodb+srv://...
# GOOGLE_APPLICATION_CREDENTIALS=./firebase-service-account.json
# GEMINI_API_KEY=...
```

- **VALIDATE**: `cat server/.env.example`

---

### Task 5: CREATE `server/app/__init__.py`

- **IMPLEMENT**: Package init file

```python
"""Learning Roadmap App Backend."""
```

- **VALIDATE**: `cat server/app/__init__.py`

---

### Task 6: CREATE `server/app/config.py`

- **IMPLEMENT**: Pydantic BaseSettings for typed configuration
- **PATTERN**: See `.claude/reference/fastapi-best-practices.md` section 10
- **IMPORTS**: pydantic_settings
- **GOTCHA**: Use @lru_cache for singleton settings

```python
"""Application configuration using Pydantic BaseSettings."""

from functools import lru_cache

from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    """Application settings loaded from environment variables."""

    # Server
    port: int = 8000
    environment: str = "development"
    cors_origins: list[str] = ["http://localhost:5173"]

    # Placeholders for future phases
    mongodb_uri: str = ""
    google_application_credentials: str = ""
    gemini_api_key: str = ""

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        case_sensitive=False,
    )

    @property
    def is_development(self) -> bool:
        """Check if running in development mode."""
        return self.environment == "development"


@lru_cache
def get_settings() -> Settings:
    """Get cached settings instance."""
    return Settings()
```

- **VALIDATE**: `cd server && python -c "from app.config import get_settings; s = get_settings(); print(f'Port: {s.port}, Env: {s.environment}')"`

---

### Task 7: CREATE `server/app/main.py`

- **IMPLEMENT**: FastAPI application with health endpoint
- **PATTERN**: See `.claude/reference/fastapi-best-practices.md` lifespan section
- **IMPORTS**: fastapi, structlog
- **GOTCHA**: Configure CORS before adding routers

```python
"""FastAPI application entry point."""

from contextlib import asynccontextmanager

import structlog
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.config import get_settings

# Configure structured logging
structlog.configure(
    processors=[
        structlog.processors.TimeStamper(fmt="iso"),
        structlog.processors.add_log_level,
        structlog.dev.ConsoleRenderer(colors=True),
    ],
    wrapper_class=structlog.make_filtering_bound_logger(20),  # INFO level
    context_class=dict,
    logger_factory=structlog.PrintLoggerFactory(),
    cache_logger_on_first_use=True,
)

logger = structlog.get_logger()


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Application lifespan: startup and shutdown."""
    settings = get_settings()
    logger.info(
        "Starting application",
        environment=settings.environment,
        port=settings.port,
    )
    yield
    logger.info("Application shutdown complete")


def create_app() -> FastAPI:
    """Create and configure FastAPI application."""
    settings = get_settings()

    app = FastAPI(
        title="Learning Roadmap API",
        description="API for the Learning Roadmap App",
        version="0.1.0",
        lifespan=lifespan,
    )

    # CORS middleware
    app.add_middleware(
        CORSMiddleware,
        allow_origins=settings.cors_origins,
        allow_credentials=True,
        allow_methods=["GET", "POST", "PUT", "PATCH", "DELETE"],
        allow_headers=["Authorization", "Content-Type"],
    )

    @app.get("/health")
    async def health_check():
        """Health check endpoint."""
        return {"status": "healthy", "environment": settings.environment}

    return app


app = create_app()
```

- **VALIDATE**: `cd server && python -c "from app.main import app; print(f'App created: {app.title}')"`

---

### Task 8: INSTALL dependencies and test server

- **IMPLEMENT**: Install dependencies and run the server
- **VALIDATE**:
  1. `cd server && pip install -r requirements.txt`
  2. `cd server && uvicorn app.main:app --host 0.0.0.0 --port 8000 &`
  3. `curl http://localhost:8000/health`
  4. Kill the background server when done

---

## TESTING STRATEGY

### Manual Testing

For this minimal skeleton, manual testing is sufficient:
1. Server starts without errors
2. Health endpoint returns expected JSON
3. Logs appear in console with structured format

### Future Tests

Test infrastructure will be added in subsequent phases when there's actual business logic to test.

---

## VALIDATION COMMANDS

Execute every command to ensure zero regressions and 100% feature correctness.

### Level 1: Syntax & Style

```bash
cd server && pip install ruff && ruff check . && ruff format --check .
```

### Level 2: Import Check

```bash
cd server && python -c "from app.main import app; from app.config import get_settings; print('All imports OK')"
```

### Level 3: Server Start

```bash
cd server && timeout 5 uvicorn app.main:app --host 0.0.0.0 --port 8000 || true
```

### Level 4: Health Check

```bash
# In one terminal:
cd server && uvicorn app.main:app --port 8000

# In another terminal:
curl http://localhost:8000/health
# Expected: {"status":"healthy","environment":"development"}
```

---

## ACCEPTANCE CRITERIA

- [x] `server/` directory structure exists
- [x] `pyproject.toml` defines project and dependencies
- [x] `requirements.txt` allows `pip install -r requirements.txt`
- [x] `config.py` loads settings from environment
- [x] `main.py` creates FastAPI app with CORS
- [x] `/health` endpoint returns `{"status": "healthy", "environment": "..."}`
- [x] Server starts with `uvicorn app.main:app --reload`
- [x] Structured logging outputs to console
- [x] No linting errors with ruff

---

## COMPLETION CHECKLIST

- [ ] All 8 tasks completed in order
- [ ] Each task validation passed
- [ ] Server runs and health check works
- [ ] Ruff linting passes
- [ ] Ready for Phase B (database integration)

---

## NOTES

### What This Does NOT Include (Intentionally)

- No MongoDB/Beanie (Phase B)
- No Firebase authentication (Phase C)
- No User model (Phase B)
- No API routes beyond health check (Phase C)
- No tests directory (will add with actual logic)

### Next Steps After This Plan

1. **Phase B**: Add MongoDB with Beanie ODM and User model
2. **Phase C**: Add Firebase auth middleware and `/auth/me` endpoint

### Quick Start After Implementation

```bash
cd server
pip install -r requirements.txt
cp .env.example .env
uvicorn app.main:app --reload
# Visit http://localhost:8000/health
# Visit http://localhost:8000/docs for Swagger UI
```
