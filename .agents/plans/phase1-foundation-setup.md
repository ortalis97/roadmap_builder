# Feature: Phase 1 - Foundation Setup

The following plan should be complete, but it's important that you validate documentation and codebase patterns and task sanity before you start implementing.

Pay special attention to naming of existing utils, types, and models. Import from the right files, etc.

## Feature Description

Set up the complete project foundation including React frontend with Vite/TypeScript/Tailwind, Python FastAPI backend with Beanie ODM for MongoDB, Firebase Authentication integration on both client and server, and protected routes. This creates the scaffolding required for all subsequent feature development.

## User Story

As a learner
I want to sign in with my Google account and see my personal dashboard
So that I can securely access my learning roadmaps

## Problem Statement

The Learning Roadmap App currently has no code implementation - only documentation and planning files exist. We need to create the complete project infrastructure before any features can be built.

## Solution Statement

Create a full-stack application skeleton with:
- React + Vite + TypeScript frontend with Tailwind CSS styling
- FastAPI + Beanie ODM backend with async MongoDB support
- Firebase Authentication for Google OAuth
- Protected API routes that verify Firebase tokens
- Protected frontend routes that require authentication
- Basic User model and authentication flow

## Feature Metadata

**Feature Type**: New Capability (Project Foundation)
**Estimated Complexity**: High
**Primary Systems Affected**: All (frontend, backend, database, authentication)
**Dependencies**:
- MongoDB Atlas account and connection string
- Firebase project with Google OAuth enabled
- Gemini API key (for future phases)

---

## CONTEXT REFERENCES

### Relevant Codebase Files IMPORTANT: YOU MUST READ THESE FILES BEFORE IMPLEMENTING!

- `CLAUDE.md` - Project conventions, tech stack, and code standards
- `PRD.md` - Data models (User, Roadmap, Session, ChatHistory), API spec, and architecture
- `.claude/reference/fastapi-best-practices.md` - FastAPI patterns to follow
- `.claude/reference/react-frontend-best-practices.md` - React/Vite patterns to follow
- `.claude/reference/testing-and-logging.md` - Testing and logging standards

### New Files to Create

**Backend (`server/`):**
- `server/pyproject.toml` - Python project configuration
- `server/requirements.txt` - Python dependencies
- `server/app/__init__.py` - Package init
- `server/app/main.py` - FastAPI app entry point
- `server/app/config.py` - Pydantic BaseSettings configuration
- `server/app/database.py` - MongoDB/Beanie connection setup
- `server/app/models/__init__.py` - Models package
- `server/app/models/user.py` - User Beanie document model
- `server/app/routers/__init__.py` - Routers package
- `server/app/routers/auth.py` - Authentication endpoints
- `server/app/middleware/__init__.py` - Middleware package
- `server/app/middleware/auth.py` - Firebase token verification
- `server/tests/__init__.py` - Tests package
- `server/tests/conftest.py` - Pytest fixtures

**Frontend (`client/`):**
- `client/package.json` - Node dependencies
- `client/tsconfig.json` - TypeScript configuration
- `client/tsconfig.node.json` - Node TypeScript config
- `client/vite.config.ts` - Vite configuration
- `client/tailwind.config.js` - Tailwind configuration
- `client/postcss.config.js` - PostCSS configuration
- `client/index.html` - HTML entry point
- `client/.env.example` - Environment variables template
- `client/src/main.tsx` - React entry point
- `client/src/App.tsx` - Main App component with routing
- `client/src/index.css` - Global styles with Tailwind
- `client/src/vite-env.d.ts` - Vite type declarations
- `client/src/config/firebase.ts` - Firebase initialization
- `client/src/context/AuthContext.tsx` - Auth context provider
- `client/src/services/api.ts` - API client with auth
- `client/src/hooks/useAuth.ts` - Auth hook
- `client/src/components/ProtectedRoute.tsx` - Route guard
- `client/src/components/Layout.tsx` - App layout with header
- `client/src/pages/LoginPage.tsx` - Login page
- `client/src/pages/DashboardPage.tsx` - Dashboard (empty state)
- `client/src/types/index.ts` - TypeScript types

**Root:**
- `server/.env.example` - Backend environment template

### Relevant Documentation YOU SHOULD READ THESE BEFORE IMPLEMENTING!

- [Beanie ODM Documentation](https://beanie-odm.dev/) - Async MongoDB ODM
- [FastAPI Documentation](https://fastapi.tiangolo.com/) - Web framework
- [Firebase Admin Python SDK](https://firebase.google.com/docs/admin/setup) - Token verification
- [Firebase JS SDK](https://firebase.google.com/docs/web/setup) - Client-side auth
- [Vite Documentation](https://vitejs.dev/) - Build tool
- [TanStack Query](https://tanstack.com/query/latest) - Server state management

### Patterns to Follow

**Naming Conventions:**
- Python: `snake_case` for functions/variables, `PascalCase` for classes
- TypeScript: `camelCase` for functions/variables, `PascalCase` for components/types
- Files: `kebab-case` for multi-word filenames, `PascalCase` for React components

**Error Handling (Backend):**
```python
from fastapi import HTTPException, status

raise HTTPException(
    status_code=status.HTTP_401_UNAUTHORIZED,
    detail="Invalid authentication credentials"
)
```

**Error Response Format:**
```json
{ "detail": "error message" }
```

**Logging Pattern (Backend):**
```python
import structlog
logger = structlog.get_logger()
logger.info("User authenticated", user_id=user.id)
```

**API Client Pattern (Frontend):**
```typescript
async function request<T>(endpoint: string, options?: RequestInit): Promise<T> {
  const token = await auth.currentUser?.getIdToken();
  const response = await fetch(`${API_BASE}${endpoint}`, {
    headers: {
      'Content-Type': 'application/json',
      ...(token && { Authorization: `Bearer ${token}` }),
    },
    ...options,
  });
  if (!response.ok) throw new Error((await response.json()).detail);
  return response.json();
}
```

---

## IMPLEMENTATION PLAN

### Phase 1: Backend Foundation

Set up the Python FastAPI project with proper structure, configuration, and database connection.

**Tasks:**
- Create project structure and configuration files
- Set up Pydantic BaseSettings for environment variables
- Configure MongoDB connection with Beanie ODM
- Create User document model
- Set up FastAPI app with CORS and lifespan events

### Phase 2: Backend Authentication

Implement Firebase token verification and authentication endpoints.

**Tasks:**
- Create Firebase Admin SDK initialization
- Create authentication middleware for token verification
- Create `/auth/me` endpoint to get current user
- Create dependency for getting authenticated user
- Handle user creation on first login

### Phase 3: Frontend Foundation

Set up the React + Vite + TypeScript project with Tailwind CSS.

**Tasks:**
- Initialize Vite project with React and TypeScript
- Configure Tailwind CSS
- Set up project structure (components, pages, hooks, services, etc.)
- Create base API client
- Set up React Router

### Phase 4: Frontend Authentication

Implement Firebase Auth client and protected routes.

**Tasks:**
- Initialize Firebase in the frontend
- Create AuthContext for managing auth state
- Create useAuth hook
- Implement Google sign-in flow
- Create ProtectedRoute component
- Build Login and Dashboard pages

### Phase 5: Integration & Testing

Connect frontend to backend and verify the complete auth flow.

**Tasks:**
- Test Google OAuth flow end-to-end
- Verify token passes to backend correctly
- Confirm user creation on first login
- Add basic error handling

---

## STEP-BY-STEP TASKS

IMPORTANT: Execute every task in order, top to bottom. Each task is atomic and independently testable.

---

### Task 1: CREATE `server/pyproject.toml`

- **IMPLEMENT**: Python project configuration with dependencies and tool settings
- **PATTERN**: Standard pyproject.toml for FastAPI projects
- **IMPORTS**: N/A (configuration file)
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
    "motor>=3.3.0",
    "beanie>=1.25.0",
    "firebase-admin>=6.4.0",
    "google-generativeai>=0.3.0",
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

- **VALIDATE**: `cd server && cat pyproject.toml`

---

### Task 2: CREATE `server/requirements.txt`

- **IMPLEMENT**: Pinned dependencies for reproducible installs
- **PATTERN**: Match pyproject.toml dependencies
- **IMPORTS**: N/A

```
fastapi>=0.109.0
uvicorn[standard]>=0.27.0
pydantic>=2.0.0
pydantic-settings>=2.0.0
motor>=3.3.0
beanie>=1.25.0
firebase-admin>=6.4.0
google-generativeai>=0.3.0
structlog>=24.1.0
python-dotenv>=1.0.0

# Development
pytest>=8.0.0
pytest-asyncio>=0.23.0
httpx>=0.26.0
ruff>=0.2.0
```

- **VALIDATE**: `cd server && cat requirements.txt`

---

### Task 3: CREATE `server/.env.example`

- **IMPLEMENT**: Environment variables template
- **PATTERN**: Document all required environment variables
- **GOTCHA**: Never commit actual .env file

```
# MongoDB
MONGODB_URI=mongodb+srv://username:password@cluster.mongodb.net/roadmap_builder?retryWrites=true&w=majority

# Firebase - path to service account JSON file
GOOGLE_APPLICATION_CREDENTIALS=./firebase-service-account.json

# Gemini AI
GEMINI_API_KEY=your_gemini_api_key

# Server
PORT=8000
ENVIRONMENT=development
CORS_ORIGINS=["http://localhost:5173"]
```

- **VALIDATE**: `cat server/.env.example`

---

### Task 4: CREATE `server/app/__init__.py`

- **IMPLEMENT**: Empty package init
- **PATTERN**: Standard Python package

```python
"""Learning Roadmap App Backend."""
```

- **VALIDATE**: `cat server/app/__init__.py`

---

### Task 5: CREATE `server/app/config.py`

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

    # MongoDB
    mongodb_uri: str

    # Firebase
    google_application_credentials: str

    # Gemini AI
    gemini_api_key: str = ""

    # Server
    port: int = 8000
    environment: str = "development"
    cors_origins: list[str] = ["http://localhost:5173"]

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        case_sensitive=False,
    )

    @property
    def is_development(self) -> bool:
        return self.environment == "development"


@lru_cache
def get_settings() -> Settings:
    """Get cached settings instance."""
    return Settings()
```

- **VALIDATE**: `cd server && python -c "from app.config import get_settings; print('Config OK')"`

---

### Task 6: CREATE `server/app/database.py`

- **IMPLEMENT**: MongoDB connection with Beanie ODM
- **PATTERN**: Async initialization in lifespan context
- **IMPORTS**: motor, beanie
- **GOTCHA**: Must call init_beanie with all document models

```python
"""MongoDB database connection using Motor and Beanie ODM."""

from beanie import init_beanie
from motor.motor_asyncio import AsyncIOMotorClient

from app.config import get_settings

# Will be populated after init
client: AsyncIOMotorClient | None = None


async def init_db() -> None:
    """Initialize MongoDB connection and Beanie ODM."""
    global client

    settings = get_settings()
    client = AsyncIOMotorClient(settings.mongodb_uri)

    # Import models here to avoid circular imports
    from app.models.user import User

    await init_beanie(
        database=client.get_default_database(),
        document_models=[User],
    )


async def close_db() -> None:
    """Close MongoDB connection."""
    global client
    if client:
        client.close()
```

- **VALIDATE**: `cd server && python -c "from app.database import init_db; print('Database module OK')"`

---

### Task 7: CREATE `server/app/models/__init__.py`

- **IMPLEMENT**: Models package with exports
- **PATTERN**: Barrel exports for clean imports

```python
"""Pydantic and Beanie models."""

from app.models.user import User

__all__ = ["User"]
```

- **VALIDATE**: `cat server/app/models/__init__.py`

---

### Task 8: CREATE `server/app/models/user.py`

- **IMPLEMENT**: User Beanie document model
- **PATTERN**: See PRD.md Appendix for User model spec
- **IMPORTS**: beanie, pydantic
- **GOTCHA**: Use firebase_uid as unique identifier, not MongoDB _id

```python
"""User document model."""

from datetime import datetime

from beanie import Document, Indexed
from pydantic import EmailStr, Field


class User(Document):
    """User document stored in MongoDB."""

    firebase_uid: Indexed(str, unique=True)  # type: ignore[valid-type]
    email: EmailStr
    name: str
    picture: str | None = None
    created_at: datetime = Field(default_factory=datetime.utcnow)
    updated_at: datetime = Field(default_factory=datetime.utcnow)

    class Settings:
        name = "users"

    async def update_last_login(self) -> None:
        """Update the updated_at timestamp."""
        self.updated_at = datetime.utcnow()
        await self.save()
```

- **VALIDATE**: `cd server && python -c "from app.models.user import User; print('User model OK')"`

---

### Task 9: CREATE `server/app/middleware/__init__.py`

- **IMPLEMENT**: Middleware package init

```python
"""Middleware components."""
```

- **VALIDATE**: `cat server/app/middleware/__init__.py`

---

### Task 10: CREATE `server/app/middleware/auth.py`

- **IMPLEMENT**: Firebase token verification middleware and dependencies
- **PATTERN**: FastAPI Depends pattern for auth
- **IMPORTS**: firebase_admin, fastapi
- **GOTCHA**: Initialize Firebase Admin only once; handle token expiration

```python
"""Firebase authentication middleware and dependencies."""

import firebase_admin
from firebase_admin import auth, credentials
from fastapi import Depends, HTTPException, status
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer

from app.config import get_settings
from app.models.user import User

# Initialize Firebase Admin SDK
_firebase_app: firebase_admin.App | None = None


def init_firebase() -> None:
    """Initialize Firebase Admin SDK."""
    global _firebase_app
    if _firebase_app is None:
        settings = get_settings()
        cred = credentials.Certificate(settings.google_application_credentials)
        _firebase_app = firebase_admin.initialize_app(cred)


# Security scheme for Bearer token
security = HTTPBearer()


async def verify_firebase_token(
    credentials: HTTPAuthorizationCredentials = Depends(security),
) -> dict:
    """Verify Firebase ID token and return decoded claims."""
    try:
        token = credentials.credentials
        decoded_token = auth.verify_id_token(token)
        return decoded_token
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail=f"Invalid authentication credentials: {str(e)}",
            headers={"WWW-Authenticate": "Bearer"},
        )


async def get_current_user(
    token_data: dict = Depends(verify_firebase_token),
) -> User:
    """Get or create user from Firebase token."""
    firebase_uid = token_data.get("uid")
    if not firebase_uid:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid token: missing uid",
        )

    # Try to find existing user
    user = await User.find_one(User.firebase_uid == firebase_uid)

    if user is None:
        # Create new user on first login
        user = User(
            firebase_uid=firebase_uid,
            email=token_data.get("email", ""),
            name=token_data.get("name", token_data.get("email", "User")),
            picture=token_data.get("picture"),
        )
        await user.insert()
    else:
        # Update last login
        await user.update_last_login()

    return user
```

- **VALIDATE**: `cd server && python -c "from app.middleware.auth import verify_firebase_token, get_current_user; print('Auth middleware OK')"`

---

### Task 11: CREATE `server/app/routers/__init__.py`

- **IMPLEMENT**: Routers package init

```python
"""API route handlers."""
```

- **VALIDATE**: `cat server/app/routers/__init__.py`

---

### Task 12: CREATE `server/app/routers/auth.py`

- **IMPLEMENT**: Authentication endpoints
- **PATTERN**: See `.claude/reference/fastapi-best-practices.md` section 2
- **IMPORTS**: fastapi, app.middleware.auth
- **GOTCHA**: /auth/me returns the current user; logout is client-side only

```python
"""Authentication routes."""

from fastapi import APIRouter, Depends
from pydantic import BaseModel

from app.middleware.auth import get_current_user
from app.models.user import User

router = APIRouter(prefix="/auth", tags=["auth"])


class UserResponse(BaseModel):
    """User response schema."""

    id: str
    firebase_uid: str
    email: str
    name: str
    picture: str | None

    class Config:
        from_attributes = True


@router.get("/me", response_model=UserResponse)
async def get_me(current_user: User = Depends(get_current_user)) -> UserResponse:
    """Get the current authenticated user."""
    return UserResponse(
        id=str(current_user.id),
        firebase_uid=current_user.firebase_uid,
        email=current_user.email,
        name=current_user.name,
        picture=current_user.picture,
    )
```

- **VALIDATE**: `cd server && python -c "from app.routers.auth import router; print('Auth router OK')"`

---

### Task 13: CREATE `server/app/main.py`

- **IMPLEMENT**: FastAPI application entry point with lifespan
- **PATTERN**: See `.claude/reference/fastapi-best-practices.md` lifespan section
- **IMPORTS**: fastapi, contextlib
- **GOTCHA**: Order matters: CORS before routers; init Firebase before DB

```python
"""FastAPI application entry point."""

from contextlib import asynccontextmanager

import structlog
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.config import get_settings
from app.database import close_db, init_db
from app.middleware.auth import init_firebase
from app.routers import auth

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
    # Startup
    logger.info("Starting application...")
    init_firebase()
    await init_db()
    logger.info("Application started successfully")
    yield
    # Shutdown
    logger.info("Shutting down application...")
    await close_db()
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

    # Include routers
    app.include_router(auth.router, prefix="/api/v1")

    @app.get("/health")
    async def health_check():
        """Health check endpoint."""
        return {"status": "healthy"}

    return app


app = create_app()
```

- **VALIDATE**: `cd server && python -c "from app.main import app; print('Main app OK')"`

---

### Task 14: CREATE `server/tests/__init__.py`

- **IMPLEMENT**: Tests package init

```python
"""Test suite for Learning Roadmap App."""
```

- **VALIDATE**: `cat server/tests/__init__.py`

---

### Task 15: CREATE `server/tests/conftest.py`

- **IMPLEMENT**: Pytest fixtures for testing
- **PATTERN**: See `.claude/reference/testing-and-logging.md`
- **IMPORTS**: pytest, httpx, fastapi

```python
"""Pytest fixtures and configuration."""

import pytest
from httpx import ASGITransport, AsyncClient

from app.main import app


@pytest.fixture
async def client():
    """Create async test client."""
    async with AsyncClient(
        transport=ASGITransport(app=app),
        base_url="http://test",
    ) as ac:
        yield ac


@pytest.fixture
def mock_firebase_token():
    """Return a mock Firebase token payload."""
    return {
        "uid": "test-firebase-uid-123",
        "email": "test@example.com",
        "name": "Test User",
        "picture": "https://example.com/photo.jpg",
    }
```

- **VALIDATE**: `cat server/tests/conftest.py`

---

### Task 16: CREATE `client/package.json`

- **IMPLEMENT**: Frontend package.json with all dependencies
- **PATTERN**: Vite + React + TypeScript + Tailwind stack
- **GOTCHA**: Match versions from PRD tech stack

```json
{
  "name": "roadmap-builder-client",
  "private": true,
  "version": "0.1.0",
  "type": "module",
  "scripts": {
    "dev": "vite",
    "build": "tsc -b && vite build",
    "lint": "eslint .",
    "preview": "vite preview",
    "test": "vitest"
  },
  "dependencies": {
    "@tanstack/react-query": "^5.17.0",
    "firebase": "^10.7.0",
    "react": "^18.3.0",
    "react-dom": "^18.3.0",
    "react-router-dom": "^6.21.0"
  },
  "devDependencies": {
    "@eslint/js": "^9.17.0",
    "@testing-library/jest-dom": "^6.4.0",
    "@testing-library/react": "^14.2.0",
    "@types/react": "^18.3.0",
    "@types/react-dom": "^18.3.0",
    "@vitejs/plugin-react": "^4.3.0",
    "autoprefixer": "^10.4.17",
    "eslint": "^9.17.0",
    "eslint-plugin-react-hooks": "^5.1.0",
    "eslint-plugin-react-refresh": "^0.4.16",
    "globals": "^15.14.0",
    "postcss": "^8.4.33",
    "tailwindcss": "^3.4.1",
    "typescript": "~5.6.0",
    "typescript-eslint": "^8.18.0",
    "vite": "^6.0.0",
    "vitest": "^2.1.0"
  }
}
```

- **VALIDATE**: `cat client/package.json`

---

### Task 17: CREATE `client/tsconfig.json`

- **IMPLEMENT**: TypeScript configuration with strict mode
- **PATTERN**: Vite React TypeScript template

```json
{
  "compilerOptions": {
    "target": "ES2020",
    "useDefineForClassFields": true,
    "lib": ["ES2020", "DOM", "DOM.Iterable"],
    "module": "ESNext",
    "skipLibCheck": true,

    "moduleResolution": "bundler",
    "allowImportingTsExtensions": true,
    "isolatedModules": true,
    "moduleDetection": "force",
    "noEmit": true,
    "jsx": "react-jsx",

    "strict": true,
    "noUnusedLocals": true,
    "noUnusedParameters": true,
    "noFallthroughCasesInSwitch": true,
    "noUncheckedSideEffectImports": true,

    "baseUrl": ".",
    "paths": {
      "@/*": ["src/*"]
    }
  },
  "include": ["src"]
}
```

- **VALIDATE**: `cat client/tsconfig.json`

---

### Task 18: CREATE `client/tsconfig.node.json`

- **IMPLEMENT**: Node TypeScript config for Vite config file

```json
{
  "compilerOptions": {
    "target": "ES2022",
    "lib": ["ES2023"],
    "module": "ESNext",
    "skipLibCheck": true,

    "moduleResolution": "bundler",
    "allowImportingTsExtensions": true,
    "isolatedModules": true,
    "moduleDetection": "force",
    "noEmit": true,

    "strict": true,
    "noUnusedLocals": true,
    "noUnusedParameters": true,
    "noFallthroughCasesInSwitch": true,
    "noUncheckedSideEffectImports": true
  },
  "include": ["vite.config.ts"]
}
```

- **VALIDATE**: `cat client/tsconfig.node.json`

---

### Task 19: CREATE `client/vite.config.ts`

- **IMPLEMENT**: Vite configuration with React plugin and path aliases
- **PATTERN**: See `.claude/reference/react-frontend-best-practices.md`

```typescript
import { defineConfig } from 'vite';
import react from '@vitejs/plugin-react';
import path from 'path';

export default defineConfig({
  plugins: [react()],
  resolve: {
    alias: {
      '@': path.resolve(__dirname, './src'),
    },
  },
  server: {
    port: 5173,
    proxy: {
      '/api': {
        target: 'http://localhost:8000',
        changeOrigin: true,
      },
    },
  },
});
```

- **VALIDATE**: `cat client/vite.config.ts`

---

### Task 20: CREATE `client/tailwind.config.js`

- **IMPLEMENT**: Tailwind CSS configuration
- **PATTERN**: Standard Tailwind setup with custom colors

```javascript
/** @type {import('tailwindcss').Config} */
export default {
  content: ['./index.html', './src/**/*.{js,ts,jsx,tsx}'],
  theme: {
    extend: {
      colors: {
        primary: {
          50: '#f0fdf4',
          100: '#dcfce7',
          200: '#bbf7d0',
          300: '#86efac',
          400: '#4ade80',
          500: '#22c55e',
          600: '#16a34a',
          700: '#15803d',
          800: '#166534',
          900: '#14532d',
        },
      },
    },
  },
  plugins: [],
};
```

- **VALIDATE**: `cat client/tailwind.config.js`

---

### Task 21: CREATE `client/postcss.config.js`

- **IMPLEMENT**: PostCSS configuration for Tailwind

```javascript
export default {
  plugins: {
    tailwindcss: {},
    autoprefixer: {},
  },
};
```

- **VALIDATE**: `cat client/postcss.config.js`

---

### Task 22: CREATE `client/index.html`

- **IMPLEMENT**: HTML entry point

```html
<!DOCTYPE html>
<html lang="en">
  <head>
    <meta charset="UTF-8" />
    <link rel="icon" type="image/svg+xml" href="/vite.svg" />
    <meta name="viewport" content="width=device-width, initial-scale=1.0" />
    <title>Learning Roadmap</title>
  </head>
  <body>
    <div id="root"></div>
    <script type="module" src="/src/main.tsx"></script>
  </body>
</html>
```

- **VALIDATE**: `cat client/index.html`

---

### Task 23: CREATE `client/.env.example`

- **IMPLEMENT**: Frontend environment variables template

```
VITE_API_URL=http://localhost:8000/api/v1
VITE_FIREBASE_API_KEY=your_firebase_api_key
VITE_FIREBASE_AUTH_DOMAIN=your-project.firebaseapp.com
VITE_FIREBASE_PROJECT_ID=your-project-id
VITE_FIREBASE_STORAGE_BUCKET=your-project.appspot.com
VITE_FIREBASE_MESSAGING_SENDER_ID=123456789
VITE_FIREBASE_APP_ID=1:123456789:web:abc123
```

- **VALIDATE**: `cat client/.env.example`

---

### Task 24: CREATE `client/src/index.css`

- **IMPLEMENT**: Global styles with Tailwind directives

```css
@tailwind base;
@tailwind components;
@tailwind utilities;

body {
  @apply bg-gray-50 text-gray-900 antialiased;
}
```

- **VALIDATE**: `cat client/src/index.css`

---

### Task 25: CREATE `client/src/vite-env.d.ts`

- **IMPLEMENT**: Vite type declarations

```typescript
/// <reference types="vite/client" />

interface ImportMetaEnv {
  readonly VITE_API_URL: string;
  readonly VITE_FIREBASE_API_KEY: string;
  readonly VITE_FIREBASE_AUTH_DOMAIN: string;
  readonly VITE_FIREBASE_PROJECT_ID: string;
  readonly VITE_FIREBASE_STORAGE_BUCKET: string;
  readonly VITE_FIREBASE_MESSAGING_SENDER_ID: string;
  readonly VITE_FIREBASE_APP_ID: string;
}

interface ImportMeta {
  readonly env: ImportMetaEnv;
}
```

- **VALIDATE**: `cat client/src/vite-env.d.ts`

---

### Task 26: CREATE `client/src/types/index.ts`

- **IMPLEMENT**: Shared TypeScript types

```typescript
export interface User {
  id: string;
  firebase_uid: string;
  email: string;
  name: string;
  picture: string | null;
}

export interface Roadmap {
  id: string;
  title: string;
  summary: string;
  sessions: Session[];
  progress: number;
  created_at: string;
  updated_at: string;
}

export interface Session {
  id: string;
  title: string;
  content: string;
  status: 'not_started' | 'in_progress' | 'done' | 'skipped';
  notes: string;
  order: number;
}

export interface ApiError {
  detail: string;
}
```

- **VALIDATE**: `cat client/src/types/index.ts`

---

### Task 27: CREATE `client/src/config/firebase.ts`

- **IMPLEMENT**: Firebase initialization
- **PATTERN**: Singleton Firebase app
- **GOTCHA**: Use environment variables for config

```typescript
import { initializeApp } from 'firebase/app';
import { getAuth, GoogleAuthProvider } from 'firebase/auth';

const firebaseConfig = {
  apiKey: import.meta.env.VITE_FIREBASE_API_KEY,
  authDomain: import.meta.env.VITE_FIREBASE_AUTH_DOMAIN,
  projectId: import.meta.env.VITE_FIREBASE_PROJECT_ID,
  storageBucket: import.meta.env.VITE_FIREBASE_STORAGE_BUCKET,
  messagingSenderId: import.meta.env.VITE_FIREBASE_MESSAGING_SENDER_ID,
  appId: import.meta.env.VITE_FIREBASE_APP_ID,
};

const app = initializeApp(firebaseConfig);
export const auth = getAuth(app);
export const googleProvider = new GoogleAuthProvider();
```

- **VALIDATE**: `cat client/src/config/firebase.ts`

---

### Task 28: CREATE `client/src/services/api.ts`

- **IMPLEMENT**: API client with authentication
- **PATTERN**: See `.claude/reference/react-frontend-best-practices.md` section 4

```typescript
import { auth } from '@/config/firebase';
import type { User } from '@/types';

const API_BASE = import.meta.env.VITE_API_URL || '/api/v1';

class ApiError extends Error {
  constructor(
    message: string,
    public status: number
  ) {
    super(message);
    this.name = 'ApiError';
  }
}

async function request<T>(endpoint: string, options: RequestInit = {}): Promise<T> {
  const token = await auth.currentUser?.getIdToken();

  const response = await fetch(`${API_BASE}${endpoint}`, {
    ...options,
    headers: {
      'Content-Type': 'application/json',
      ...(token && { Authorization: `Bearer ${token}` }),
      ...options.headers,
    },
  });

  if (!response.ok) {
    const error = await response.json().catch(() => ({ detail: 'An error occurred' }));
    throw new ApiError(error.detail || 'An error occurred', response.status);
  }

  if (response.status === 204) {
    return null as T;
  }

  return response.json();
}

export const api = {
  auth: {
    getMe: () => request<User>('/auth/me'),
  },
};
```

- **VALIDATE**: `cat client/src/services/api.ts`

---

### Task 29: CREATE `client/src/context/AuthContext.tsx`

- **IMPLEMENT**: React context for authentication state
- **PATTERN**: See `.claude/reference/react-frontend-best-practices.md` section 3
- **GOTCHA**: Handle loading state during auth check

```tsx
import { createContext, useContext, useEffect, useState, type ReactNode } from 'react';
import { onAuthStateChanged, signInWithPopup, signOut, type User as FirebaseUser } from 'firebase/auth';
import { auth, googleProvider } from '@/config/firebase';
import type { User } from '@/types';
import { api } from '@/services/api';

interface AuthContextType {
  user: User | null;
  firebaseUser: FirebaseUser | null;
  loading: boolean;
  error: string | null;
  signInWithGoogle: () => Promise<void>;
  logout: () => Promise<void>;
}

const AuthContext = createContext<AuthContextType | null>(null);

export function AuthProvider({ children }: { children: ReactNode }) {
  const [user, setUser] = useState<User | null>(null);
  const [firebaseUser, setFirebaseUser] = useState<FirebaseUser | null>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    const unsubscribe = onAuthStateChanged(auth, async (fbUser) => {
      setFirebaseUser(fbUser);

      if (fbUser) {
        try {
          const userData = await api.auth.getMe();
          setUser(userData);
          setError(null);
        } catch (err) {
          console.error('Failed to fetch user data:', err);
          setError('Failed to load user data');
          setUser(null);
        }
      } else {
        setUser(null);
      }

      setLoading(false);
    });

    return () => unsubscribe();
  }, []);

  const signInWithGoogle = async () => {
    try {
      setError(null);
      await signInWithPopup(auth, googleProvider);
    } catch (err) {
      console.error('Google sign-in failed:', err);
      setError('Failed to sign in with Google');
      throw err;
    }
  };

  const logout = async () => {
    try {
      await signOut(auth);
      setUser(null);
    } catch (err) {
      console.error('Logout failed:', err);
      setError('Failed to log out');
      throw err;
    }
  };

  return (
    <AuthContext.Provider
      value={{
        user,
        firebaseUser,
        loading,
        error,
        signInWithGoogle,
        logout,
      }}
    >
      {children}
    </AuthContext.Provider>
  );
}

export function useAuth() {
  const context = useContext(AuthContext);
  if (!context) {
    throw new Error('useAuth must be used within an AuthProvider');
  }
  return context;
}
```

- **VALIDATE**: `cat client/src/context/AuthContext.tsx`

---

### Task 30: CREATE `client/src/hooks/useAuth.ts`

- **IMPLEMENT**: Re-export useAuth hook for cleaner imports

```typescript
export { useAuth } from '@/context/AuthContext';
```

- **VALIDATE**: `cat client/src/hooks/useAuth.ts`

---

### Task 31: CREATE `client/src/components/ProtectedRoute.tsx`

- **IMPLEMENT**: Route guard component
- **PATTERN**: Redirect to login if not authenticated

```tsx
import { Navigate, useLocation } from 'react-router-dom';
import { useAuth } from '@/hooks/useAuth';

interface ProtectedRouteProps {
  children: React.ReactNode;
}

export function ProtectedRoute({ children }: ProtectedRouteProps) {
  const { user, loading } = useAuth();
  const location = useLocation();

  if (loading) {
    return (
      <div className="flex min-h-screen items-center justify-center">
        <div className="h-8 w-8 animate-spin rounded-full border-4 border-primary-500 border-t-transparent"></div>
      </div>
    );
  }

  if (!user) {
    return <Navigate to="/login" state={{ from: location }} replace />;
  }

  return <>{children}</>;
}
```

- **VALIDATE**: `cat client/src/components/ProtectedRoute.tsx`

---

### Task 32: CREATE `client/src/components/Layout.tsx`

- **IMPLEMENT**: App layout with header and navigation
- **PATTERN**: Outlet for nested routes

```tsx
import { Outlet, Link } from 'react-router-dom';
import { useAuth } from '@/hooks/useAuth';

export function Layout() {
  const { user, logout } = useAuth();

  return (
    <div className="min-h-screen bg-gray-50">
      <header className="bg-white shadow-sm">
        <nav className="mx-auto flex max-w-7xl items-center justify-between px-4 py-4">
          <Link to="/" className="text-xl font-bold text-primary-600">
            Learning Roadmap
          </Link>

          {user && (
            <div className="flex items-center gap-4">
              <div className="flex items-center gap-2">
                {user.picture && (
                  <img
                    src={user.picture}
                    alt={user.name}
                    className="h-8 w-8 rounded-full"
                  />
                )}
                <span className="text-sm text-gray-700">{user.name}</span>
              </div>
              <button
                onClick={() => logout()}
                className="text-sm text-gray-500 hover:text-gray-700"
              >
                Sign out
              </button>
            </div>
          )}
        </nav>
      </header>

      <main className="mx-auto max-w-7xl px-4 py-8">
        <Outlet />
      </main>
    </div>
  );
}
```

- **VALIDATE**: `cat client/src/components/Layout.tsx`

---

### Task 33: CREATE `client/src/pages/LoginPage.tsx`

- **IMPLEMENT**: Login page with Google sign-in
- **PATTERN**: Redirect to dashboard after login

```tsx
import { useEffect } from 'react';
import { useNavigate, useLocation } from 'react-router-dom';
import { useAuth } from '@/hooks/useAuth';

export function LoginPage() {
  const { user, loading, error, signInWithGoogle } = useAuth();
  const navigate = useNavigate();
  const location = useLocation();

  const from = (location.state as { from?: Location })?.from?.pathname || '/';

  useEffect(() => {
    if (user && !loading) {
      navigate(from, { replace: true });
    }
  }, [user, loading, navigate, from]);

  const handleGoogleSignIn = async () => {
    try {
      await signInWithGoogle();
    } catch {
      // Error is handled in AuthContext
    }
  };

  if (loading) {
    return (
      <div className="flex min-h-screen items-center justify-center">
        <div className="h-8 w-8 animate-spin rounded-full border-4 border-primary-500 border-t-transparent"></div>
      </div>
    );
  }

  return (
    <div className="flex min-h-screen items-center justify-center bg-gray-50">
      <div className="w-full max-w-md space-y-8 rounded-lg bg-white p-8 shadow-md">
        <div className="text-center">
          <h1 className="text-3xl font-bold text-gray-900">Learning Roadmap</h1>
          <p className="mt-2 text-gray-600">
            Turn your learning goals into structured roadmaps
          </p>
        </div>

        {error && (
          <div className="rounded-md bg-red-50 p-4 text-sm text-red-700">
            {error}
          </div>
        )}

        <button
          onClick={handleGoogleSignIn}
          className="flex w-full items-center justify-center gap-3 rounded-lg border border-gray-300 bg-white px-4 py-3 text-gray-700 shadow-sm transition hover:bg-gray-50"
        >
          <svg className="h-5 w-5" viewBox="0 0 24 24">
            <path
              fill="#4285F4"
              d="M22.56 12.25c0-.78-.07-1.53-.2-2.25H12v4.26h5.92c-.26 1.37-1.04 2.53-2.21 3.31v2.77h3.57c2.08-1.92 3.28-4.74 3.28-8.09z"
            />
            <path
              fill="#34A853"
              d="M12 23c2.97 0 5.46-.98 7.28-2.66l-3.57-2.77c-.98.66-2.23 1.06-3.71 1.06-2.86 0-5.29-1.93-6.16-4.53H2.18v2.84C3.99 20.53 7.7 23 12 23z"
            />
            <path
              fill="#FBBC05"
              d="M5.84 14.09c-.22-.66-.35-1.36-.35-2.09s.13-1.43.35-2.09V7.07H2.18C1.43 8.55 1 10.22 1 12s.43 3.45 1.18 4.93l2.85-2.22.81-.62z"
            />
            <path
              fill="#EA4335"
              d="M12 5.38c1.62 0 3.06.56 4.21 1.64l3.15-3.15C17.45 2.09 14.97 1 12 1 7.7 1 3.99 3.47 2.18 7.07l3.66 2.84c.87-2.6 3.3-4.53 6.16-4.53z"
            />
          </svg>
          Sign in with Google
        </button>
      </div>
    </div>
  );
}
```

- **VALIDATE**: `cat client/src/pages/LoginPage.tsx`

---

### Task 34: CREATE `client/src/pages/DashboardPage.tsx`

- **IMPLEMENT**: Dashboard page with empty state
- **PATTERN**: Will show roadmap list in future phases

```tsx
import { useAuth } from '@/hooks/useAuth';

export function DashboardPage() {
  const { user } = useAuth();

  return (
    <div className="space-y-6">
      <div>
        <h1 className="text-2xl font-bold text-gray-900">
          Welcome back, {user?.name?.split(' ')[0]}!
        </h1>
        <p className="text-gray-600">Your learning roadmaps will appear here.</p>
      </div>

      <div className="rounded-lg border-2 border-dashed border-gray-300 p-12 text-center">
        <svg
          className="mx-auto h-12 w-12 text-gray-400"
          fill="none"
          viewBox="0 0 24 24"
          stroke="currentColor"
        >
          <path
            strokeLinecap="round"
            strokeLinejoin="round"
            strokeWidth={2}
            d="M9 5H7a2 2 0 00-2 2v12a2 2 0 002 2h10a2 2 0 002-2V7a2 2 0 00-2-2h-2M9 5a2 2 0 002 2h2a2 2 0 002-2M9 5a2 2 0 012-2h2a2 2 0 012 2"
          />
        </svg>
        <h3 className="mt-4 text-lg font-medium text-gray-900">No roadmaps yet</h3>
        <p className="mt-2 text-gray-500">
          Get started by creating your first learning roadmap.
        </p>
        <button
          className="mt-4 rounded-lg bg-primary-600 px-4 py-2 text-white hover:bg-primary-700"
          disabled
        >
          Create Roadmap (Coming Soon)
        </button>
      </div>
    </div>
  );
}
```

- **VALIDATE**: `cat client/src/pages/DashboardPage.tsx`

---

### Task 35: CREATE `client/src/App.tsx`

- **IMPLEMENT**: Main App component with routing
- **PATTERN**: React Router v6 with layout routes

```tsx
import { BrowserRouter, Routes, Route } from 'react-router-dom';
import { QueryClient, QueryClientProvider } from '@tanstack/react-query';
import { AuthProvider } from '@/context/AuthContext';
import { ProtectedRoute } from '@/components/ProtectedRoute';
import { Layout } from '@/components/Layout';
import { LoginPage } from '@/pages/LoginPage';
import { DashboardPage } from '@/pages/DashboardPage';

const queryClient = new QueryClient({
  defaultOptions: {
    queries: {
      staleTime: 1000 * 60 * 5, // 5 minutes
      retry: 1,
    },
  },
});

function App() {
  return (
    <QueryClientProvider client={queryClient}>
      <BrowserRouter>
        <AuthProvider>
          <Routes>
            <Route path="/login" element={<LoginPage />} />
            <Route
              path="/"
              element={
                <ProtectedRoute>
                  <Layout />
                </ProtectedRoute>
              }
            >
              <Route index element={<DashboardPage />} />
            </Route>
          </Routes>
        </AuthProvider>
      </BrowserRouter>
    </QueryClientProvider>
  );
}

export default App;
```

- **VALIDATE**: `cat client/src/App.tsx`

---

### Task 36: CREATE `client/src/main.tsx`

- **IMPLEMENT**: React entry point

```tsx
import { StrictMode } from 'react';
import { createRoot } from 'react-dom/client';
import App from './App';
import './index.css';

createRoot(document.getElementById('root')!).render(
  <StrictMode>
    <App />
  </StrictMode>
);
```

- **VALIDATE**: `cat client/src/main.tsx`

---

### Task 37: CREATE directory structure

- **IMPLEMENT**: Create all necessary directories
- **VALIDATE**: `find server client -type d | head -30`

```bash
mkdir -p server/app/{models,routers,middleware,services,utils}
mkdir -p server/tests/{unit,integration}
mkdir -p client/src/{components,pages,hooks,services,context,config,types,utils}
mkdir -p client/public
```

---

## TESTING STRATEGY

### Unit Tests

- Test Pydantic model validation
- Test user creation logic
- Test token verification (mocked Firebase)

### Integration Tests

- Test `/health` endpoint returns 200
- Test `/api/v1/auth/me` with mocked token
- Test user creation on first login

### Edge Cases

- Invalid Firebase token
- Expired token
- Missing required fields in token
- Database connection failure

---

## VALIDATION COMMANDS

Execute every command to ensure zero regressions and 100% feature correctness.

### Level 1: Syntax & Style

```bash
# Backend
cd server && ruff check . && ruff format --check .

# Frontend
cd client && npm run lint
```

### Level 2: Type Checking

```bash
# Frontend
cd client && npx tsc --noEmit
```

### Level 3: Unit Tests

```bash
# Backend
cd server && pytest tests/unit -v

# Frontend
cd client && npm test
```

### Level 4: Integration Tests

```bash
# Backend (requires .env with test database)
cd server && pytest tests/integration -v
```

### Level 5: Manual Validation

1. Start backend: `cd server && uvicorn app.main:app --reload`
2. Verify health check: `curl http://localhost:8000/health`
3. Start frontend: `cd client && npm run dev`
4. Open http://localhost:5173
5. Click "Sign in with Google"
6. Verify redirect to dashboard after login
7. Verify user appears in MongoDB `users` collection
8. Verify "Sign out" works

---

## ACCEPTANCE CRITERIA

- [x] Backend server starts without errors
- [x] Frontend builds and runs without errors
- [x] Health check endpoint returns `{"status": "healthy"}`
- [x] Google OAuth sign-in flow completes successfully
- [x] User is created in MongoDB on first login
- [x] Protected routes redirect to login when not authenticated
- [x] Auth token is sent with API requests
- [x] User can sign out successfully
- [x] CORS is properly configured for frontend origin
- [x] All validation commands pass

---

## COMPLETION CHECKLIST

- [ ] All tasks completed in order
- [ ] Each task validation passed immediately
- [ ] All validation commands executed successfully
- [ ] Full test suite passes (unit + integration)
- [ ] No linting or type checking errors
- [ ] Manual testing confirms feature works
- [ ] Acceptance criteria all met
- [ ] Code reviewed for quality and maintainability

---

## NOTES

### Design Decisions

1. **Beanie ODM over raw Motor**: Provides Pydantic integration and cleaner async document operations
2. **Firebase Auth over custom JWT**: Simplifies OAuth implementation and provides secure token verification
3. **TanStack Query setup now**: Even though not used in Phase 1, setting up the infrastructure for future phases
4. **Path aliases (`@/`)**: Cleaner imports as project grows

### Known Limitations (Phase 1)

- No roadmap functionality yet (Phase 2)
- No progress tracking (Phase 3)
- No AI assistant (Phase 4)
- Tests are minimal; will expand in future phases

### Prerequisites

Before running the application:
1. Create MongoDB Atlas cluster and get connection string
2. Create Firebase project and enable Google OAuth
3. Download Firebase service account JSON
4. Copy `.env.example` to `.env` and fill in values

### Potential Issues

- Firebase Admin SDK requires service account file path
- MongoDB Atlas may need IP whitelist configuration
- CORS issues if origins don't match exactly
