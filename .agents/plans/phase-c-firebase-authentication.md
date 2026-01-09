# Feature: Phase C - Firebase Authentication

The following plan should be complete, but it's important that you validate documentation and codebase patterns and task sanity before you start implementing.

Pay special attention to naming of existing utils, types, and models. Import from the right files, etc.

## Feature Description

Add Firebase Authentication to the backend, enabling Google OAuth login. This includes Firebase Admin SDK initialization for token verification, authentication middleware to protect routes, and an `/auth/me` endpoint that returns or creates the current user.

## User Story

As a learner
I want to sign in with my Google account
So that I can securely access my personal learning roadmaps

## Problem Statement

The backend has no authentication. Any request can access any data. We need to verify Firebase ID tokens from the frontend and associate requests with users.

## Solution Statement

Implement Firebase authentication with:
- Firebase Admin SDK for server-side token verification
- Auth middleware that extracts and verifies Bearer tokens
- Dependency injection for getting the current authenticated user
- `/auth/me` endpoint that returns user profile (creating user on first login)
- Protected route pattern for future endpoints

## Feature Metadata

**Feature Type**: New Capability (Authentication)
**Estimated Complexity**: Medium
**Primary Systems Affected**: Backend (middleware, routers)
**Dependencies**:
- Firebase project with Google OAuth enabled
- Firebase service account JSON file
- firebase-admin Python package (already in Phase 1 plan, needs to be added)

---

## CONTEXT REFERENCES

### Relevant Codebase Files IMPORTANT: YOU MUST READ THESE FILES BEFORE IMPLEMENTING!

- `server/app/main.py` - Add auth router, initialize Firebase in lifespan
- `server/app/config.py` - Add Firebase config validation
- `server/app/models/user.py` - Existing User model
- `server/app/database.py` - Database connection pattern
- `PRD.md` (lines 371-381) - Authentication requirements
- `PRD.md` (lines 439-444) - Auth API endpoints
- `.claude/reference/fastapi-best-practices.md` - FastAPI patterns

### New Files to Create

```
server/app/
├── middleware/
│   ├── __init__.py
│   └── auth.py              # Firebase token verification
└── routers/
    ├── __init__.py
    └── auth.py              # Auth endpoints (/auth/me)
```

### Files to Modify

```
server/
├── requirements.txt         # Add firebase-admin
├── .env.example             # Document Firebase config
└── app/
    ├── config.py            # Add Firebase settings
    └── main.py              # Register auth router, init Firebase
```

### Relevant Documentation

- [Firebase Admin Python SDK](https://firebase.google.com/docs/admin/setup)
- [Firebase ID Token Verification](https://firebase.google.com/docs/auth/admin/verify-id-tokens)
- [FastAPI Security](https://fastapi.tiangolo.com/tutorial/security/)
- [FastAPI Dependencies](https://fastapi.tiangolo.com/tutorial/dependencies/)

### Patterns to Follow

**Dependency Injection Pattern (FastAPI):**
```python
from fastapi import Depends

async def get_current_user(token: str = Depends(oauth2_scheme)) -> User:
    # Verify token and return user
    pass

@router.get("/protected")
async def protected_route(user: User = Depends(get_current_user)):
    return {"user": user.name}
```

**HTTPBearer Security Scheme:**
```python
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials

security = HTTPBearer()

async def verify_token(
    credentials: HTTPAuthorizationCredentials = Depends(security)
) -> dict:
    token = credentials.credentials
    # Verify with Firebase Admin SDK
```

**Firebase Token Verification:**
```python
from firebase_admin import auth, credentials, initialize_app

# Initialize once at startup
cred = credentials.Certificate("path/to/service-account.json")
initialize_app(cred)

# Verify token
decoded_token = auth.verify_id_token(id_token)
uid = decoded_token['uid']
```

**Error Response Pattern (from existing code):**
```python
from fastapi import HTTPException, status

raise HTTPException(
    status_code=status.HTTP_401_UNAUTHORIZED,
    detail="Invalid authentication credentials",
    headers={"WWW-Authenticate": "Bearer"},
)
```

---

## IMPLEMENTATION PLAN

### Phase 1: Dependencies & Configuration

Add firebase-admin package and configure settings.

**Tasks:**
- Add firebase-admin to requirements.txt
- Update config.py to include Firebase settings
- Update .env.example with Firebase configuration

### Phase 2: Firebase Initialization

Create middleware module with Firebase Admin SDK setup.

**Tasks:**
- Create middleware directory and __init__.py
- Create auth.py with Firebase initialization
- Add token verification function

### Phase 3: Auth Dependencies

Create FastAPI dependencies for authentication.

**Tasks:**
- Create get_current_user dependency
- Handle user creation on first login
- Handle token verification errors

### Phase 4: Auth Router

Create auth router with /auth/me endpoint.

**Tasks:**
- Create routers directory and __init__.py
- Create auth.py router
- Implement GET /auth/me endpoint

### Phase 5: Integration

Integrate auth into the main application.

**Tasks:**
- Initialize Firebase in main.py lifespan
- Register auth router
- Test authentication flow

---

## STEP-BY-STEP TASKS

IMPORTANT: Execute every task in order, top to bottom. Each task is atomic and independently testable.

---

### Task 1: UPDATE `server/requirements.txt`

- **IMPLEMENT**: Add firebase-admin package
- **PATTERN**: Match existing dependency format

Add after beanie:
```
firebase-admin>=6.4.0
```

- **VALIDATE**: `cat server/requirements.txt | grep firebase`

---

### Task 2: INSTALL updated dependencies

- **IMPLEMENT**: Install firebase-admin in venv
- **VALIDATE**: `cd server && ./venv/bin/pip install --trusted-host pypi.org --trusted-host files.pythonhosted.org -r requirements.txt && ./venv/bin/python -c "import firebase_admin; print('OK')"`

---

### Task 3: UPDATE `server/app/config.py`

- **IMPLEMENT**: Add Firebase configuration settings
- **PATTERN**: Follow existing Settings class pattern
- **GOTCHA**: google_application_credentials can be empty in dev (skip Firebase init)

Add to Settings class:
```python
# Firebase
google_application_credentials: str = ""
```

- **VALIDATE**: `cd server && ./venv/bin/python -c "from app.config import get_settings; print(get_settings().google_application_credentials)"`

---

### Task 4: UPDATE `server/.env.example`

- **IMPLEMENT**: Document Firebase configuration
- **PATTERN**: Follow existing format

Update to include:
```
# Firebase Admin SDK (download from Firebase Console > Project Settings > Service Accounts)
GOOGLE_APPLICATION_CREDENTIALS=./firebase-service-account.json
```

- **VALIDATE**: `cat server/.env.example | grep GOOGLE`

---

### Task 5: CREATE `server/app/middleware/__init__.py`

- **IMPLEMENT**: Middleware package init

```python
"""Middleware components."""
```

- **VALIDATE**: `cat server/app/middleware/__init__.py`

---

### Task 6: CREATE `server/app/middleware/auth.py`

- **IMPLEMENT**: Firebase authentication middleware and dependencies
- **PATTERN**: FastAPI Depends pattern with HTTPBearer
- **IMPORTS**: firebase_admin, fastapi
- **GOTCHA**: Initialize Firebase only once; handle missing credentials gracefully

```python
"""Firebase authentication middleware and dependencies."""

import firebase_admin
from firebase_admin import auth, credentials
from fastapi import Depends, HTTPException, status
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer
import structlog

from app.config import get_settings
from app.models.user import User

logger = structlog.get_logger()

# Firebase app instance
_firebase_app: firebase_admin.App | None = None


def init_firebase() -> None:
    """Initialize Firebase Admin SDK.

    Call this once during application startup.
    Skips initialization if credentials not configured.
    """
    global _firebase_app

    if _firebase_app is not None:
        return  # Already initialized

    settings = get_settings()

    if not settings.google_application_credentials:
        logger.warning("Firebase credentials not configured, auth will be disabled")
        return

    try:
        cred = credentials.Certificate(settings.google_application_credentials)
        _firebase_app = firebase_admin.initialize_app(cred)
        logger.info("Firebase Admin SDK initialized")
    except Exception as e:
        logger.error("Failed to initialize Firebase", error=str(e))
        raise


def is_firebase_initialized() -> bool:
    """Check if Firebase is initialized."""
    return _firebase_app is not None


# Security scheme for Bearer token
security = HTTPBearer(auto_error=False)


async def verify_firebase_token(
    credentials: HTTPAuthorizationCredentials | None = Depends(security),
) -> dict:
    """Verify Firebase ID token and return decoded claims.

    Raises HTTPException if token is invalid or missing.
    """
    if not is_firebase_initialized():
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="Authentication service not configured",
        )

    if credentials is None:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Missing authentication token",
            headers={"WWW-Authenticate": "Bearer"},
        )

    try:
        token = credentials.credentials
        decoded_token = auth.verify_id_token(token)
        return decoded_token
    except auth.ExpiredIdTokenError:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Token has expired",
            headers={"WWW-Authenticate": "Bearer"},
        )
    except auth.InvalidIdTokenError as e:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail=f"Invalid token: {str(e)}",
            headers={"WWW-Authenticate": "Bearer"},
        )
    except Exception as e:
        logger.error("Token verification failed", error=str(e))
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Authentication failed",
            headers={"WWW-Authenticate": "Bearer"},
        )


async def get_current_user(
    token_data: dict = Depends(verify_firebase_token),
) -> User:
    """Get or create user from Firebase token.

    Creates a new user on first login.
    Updates last_seen on subsequent logins.
    """
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
        logger.info("Creating new user", firebase_uid=firebase_uid)
        user = User(
            firebase_uid=firebase_uid,
            email=token_data.get("email", ""),
            name=token_data.get("name", token_data.get("email", "User")),
            picture=token_data.get("picture"),
        )
        await user.insert()
        logger.info("User created", user_id=str(user.id))
    else:
        # Update last seen
        await user.update_last_seen()

    return user
```

- **VALIDATE**: `cd server && ./venv/bin/python -c "from app.middleware.auth import init_firebase, get_current_user, verify_firebase_token; print('Auth middleware OK')"`

---

### Task 7: CREATE `server/app/routers/__init__.py`

- **IMPLEMENT**: Routers package init

```python
"""API route handlers."""
```

- **VALIDATE**: `cat server/app/routers/__init__.py`

---

### Task 8: CREATE `server/app/routers/auth.py`

- **IMPLEMENT**: Authentication router with /auth/me endpoint
- **PATTERN**: See PRD.md for API specification
- **IMPORTS**: fastapi, app.middleware.auth, app.models.user

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
    """Get the current authenticated user.

    Returns the user profile for the authenticated user.
    Creates a new user on first login.
    """
    return UserResponse(
        id=str(current_user.id),
        firebase_uid=current_user.firebase_uid,
        email=current_user.email,
        name=current_user.name,
        picture=current_user.picture,
    )
```

- **VALIDATE**: `cd server && ./venv/bin/python -c "from app.routers.auth import router; print(f'Auth router OK: {router.prefix}')"`

---

### Task 9: UPDATE `server/app/main.py`

- **IMPLEMENT**: Initialize Firebase and register auth router
- **PATTERN**: Follow existing lifespan and router patterns
- **GOTCHA**: Initialize Firebase before database (or after, order doesn't matter for these)

Add import at top:
```python
from app.middleware.auth import init_firebase
from app.routers import auth as auth_router
```

Update lifespan to init Firebase:
```python
@asynccontextmanager
async def lifespan(app: FastAPI):
    """Application lifespan: startup and shutdown."""
    settings = get_settings()
    logger.info(
        "Starting application",
        environment=settings.environment,
        port=settings.port,
    )

    # Initialize Firebase
    init_firebase()

    # Initialize database
    await init_db()

    yield

    # Cleanup
    await close_db()
    logger.info("Application shutdown complete")
```

Add router registration in create_app():
```python
# Include routers
app.include_router(auth_router.router, prefix="/api/v1")
```

- **VALIDATE**: `cd server && ./venv/bin/python -c "from app.main import app; print([r.path for r in app.routes if 'auth' in r.path])"`

---

### Task 10: CREATE directories

- **IMPLEMENT**: Ensure middleware and routers directories exist
- **VALIDATE**: `ls -la server/app/middleware/ server/app/routers/`

```bash
mkdir -p server/app/middleware server/app/routers
```

---

## TESTING STRATEGY

### Manual Testing (No Firebase)

Without Firebase credentials:
1. Server starts with warning about disabled auth
2. `/auth/me` returns 503 "Authentication service not configured"
3. Health endpoint still works

### Manual Testing (With Firebase)

With Firebase service account:
1. Get a Firebase ID token from frontend or Firebase Auth REST API
2. Call `/auth/me` with `Authorization: Bearer <token>`
3. First call creates user, returns user profile
4. Subsequent calls return same user, update last_seen

### Test with curl

```bash
# Without token - should return 401
curl http://localhost:8000/api/v1/auth/me

# With valid token
curl -H "Authorization: Bearer <firebase_id_token>" \
  http://localhost:8000/api/v1/auth/me
```

### Integration Tests (Future)

- Mock Firebase token verification
- Test user creation on first login
- Test existing user retrieval
- Test invalid/expired tokens

---

## VALIDATION COMMANDS

Execute every command to ensure zero regressions and 100% feature correctness.

### Level 1: Syntax & Style

```bash
cd server && ./venv/bin/ruff check app/ && ./venv/bin/ruff format --check app/
```

### Level 2: Import Check

```bash
cd server && ./venv/bin/python -c "
from app.config import get_settings
from app.database import init_db, close_db
from app.models import User
from app.middleware.auth import init_firebase, get_current_user
from app.routers.auth import router
from app.main import app
print('All imports OK')
print(f'Routes: {[r.path for r in app.routes]}')
"
```

### Level 3: Server Start (No Firebase)

```bash
cd server && timeout 5 ./venv/bin/uvicorn app.main:app --port 8000 2>&1 | head -20
# Should see: "Firebase credentials not configured, auth will be disabled"
```

### Level 4: API Test (No Token)

```bash
# Start server in background
cd server && ./venv/bin/uvicorn app.main:app --port 8000 &
sleep 3

# Test endpoints
curl http://localhost:8000/health
curl http://localhost:8000/api/v1/auth/me  # Should return 401 or 503

kill %1
```

### Level 5: With Firebase (Optional)

```bash
# Only if you have Firebase configured
cd server
# Add GOOGLE_APPLICATION_CREDENTIALS to .env
./venv/bin/uvicorn app.main:app --port 8000
# Should see: "Firebase Admin SDK initialized"
```

---

## ACCEPTANCE CRITERIA

- [ ] firebase-admin added to requirements.txt
- [ ] Dependencies install without errors
- [ ] Firebase initialization works (or gracefully skips)
- [ ] Auth middleware verifies tokens correctly
- [ ] `/auth/me` endpoint returns user profile
- [ ] User created on first login
- [ ] User last_seen updated on subsequent logins
- [ ] Missing token returns 401
- [ ] Invalid token returns 401
- [ ] Missing Firebase config returns 503 (graceful degradation)
- [ ] All imports resolve correctly
- [ ] Ruff linting passes

---

## COMPLETION CHECKLIST

- [ ] All 10 tasks completed in order
- [ ] Each task validation passed
- [ ] Server runs with auth disabled (no Firebase config)
- [ ] Ruff linting passes
- [ ] Ready for frontend integration

---

## NOTES

### Design Decisions

1. **Graceful degradation**: Server starts even without Firebase credentials, returning 503 for auth endpoints. This allows health checks and development without Firebase.

2. **User creation on first login**: Simplifies frontend - just call `/auth/me` after Firebase login, backend handles user creation.

3. **HTTPBearer with auto_error=False**: Allows custom error messages instead of default 403.

4. **Separate verify_token and get_current_user**: Allows flexibility for routes that need token data but not full user lookup.

### Firebase Setup Required

Before testing with real authentication:

1. Go to [Firebase Console](https://console.firebase.google.com)
2. Create or select a project
3. Enable Google sign-in (Authentication → Sign-in method → Google)
4. Download service account key:
   - Project Settings → Service Accounts → Generate New Private Key
5. Save as `server/firebase-service-account.json`
6. Add to `.env`: `GOOGLE_APPLICATION_CREDENTIALS=./firebase-service-account.json`

### Security Notes

- Never commit `firebase-service-account.json` to git
- The file is already in `.gitignore`
- In production, use environment variable or secrets manager

### What This Does NOT Include

- Frontend Firebase integration (separate phase)
- Logout endpoint (logout is client-side with Firebase)
- Session management (Firebase handles this)
- Refresh token handling (Firebase SDK handles this)
