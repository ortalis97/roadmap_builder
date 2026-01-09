# Feature: Phase B - MongoDB + Beanie ODM + User Model

The following plan should be complete, but it's important that you validate documentation and codebase patterns and task sanity before you start implementing.

Pay special attention to naming of existing utils, types, and models. Import from the right files, etc.

## Feature Description

Add MongoDB database connectivity using Motor (async driver) and Beanie ODM, along with the User document model. This builds on the minimal skeleton from Phase A and prepares for authentication in Phase C.

## User Story

As a developer
I want the backend to connect to MongoDB and have a User model
So that I can store and retrieve user data when authentication is added

## Problem Statement

The backend skeleton has no database connectivity. We need to add MongoDB support with an async ODM before we can implement user authentication and store roadmap data.

## Solution Statement

Add MongoDB integration with:
- Beanie ODM for async document operations with Pydantic integration
- Motor as the async MongoDB driver
- User document model matching the PRD specification
- Database initialization in the FastAPI lifespan
- Updated configuration for MongoDB connection string

## Feature Metadata

**Feature Type**: New Capability (Database Layer)
**Estimated Complexity**: Low-Medium
**Primary Systems Affected**: Backend (database layer)
**Dependencies**:
- MongoDB Atlas account with connection string
- motor, beanie packages (already in requirements.txt from Phase 1 plan)

---

## CONTEXT REFERENCES

### Relevant Codebase Files IMPORTANT: YOU MUST READ THESE FILES BEFORE IMPLEMENTING!

- `server/app/config.py` - Existing settings (add mongodb_uri)
- `server/app/main.py` - Existing FastAPI app (add database init to lifespan)
- `server/requirements.txt` - Dependencies (add motor, beanie)
- `CLAUDE.md` - Project conventions
- `PRD.md` (lines 718-729) - User model specification

### New Files to Create

```
server/app/
├── database.py             # MongoDB connection setup
└── models/
    ├── __init__.py         # Models package with exports
    └── user.py             # User document model
```

### Files to Modify

```
server/
├── requirements.txt        # Add motor, beanie
└── app/
    ├── config.py           # Ensure mongodb_uri is required for non-dev
    └── main.py             # Add database init/close to lifespan
```

### Relevant Documentation

- [Beanie ODM Documentation](https://beanie-odm.dev/)
  - Getting Started section
  - Document models section
- [Motor Documentation](https://motor.readthedocs.io/)
  - AsyncIO tutorial
- [MongoDB Atlas](https://www.mongodb.com/atlas)
  - Connection string format

### Patterns to Follow

**Naming Conventions (from existing code):**
- Python: `snake_case` for functions/variables, `PascalCase` for classes
- Async functions for all database operations

**Configuration Pattern (from `config.py`):**
```python
class Settings(BaseSettings):
    mongodb_uri: str = ""  # Required in production
```

**Logging Pattern (from `main.py`):**
```python
import structlog
logger = structlog.get_logger()
logger.info("Database connected", database="roadmap_builder")
```

**Beanie Document Pattern:**
```python
from beanie import Document, Indexed
from pydantic import Field

class User(Document):
    firebase_uid: Indexed(str, unique=True)
    email: str

    class Settings:
        name = "users"  # Collection name
```

---

## IMPLEMENTATION PLAN

### Phase 1: Update Dependencies

Add motor and beanie to requirements.txt.

**Tasks:**
- Add motor>=3.3.0 and beanie>=1.25.0 to requirements.txt
- Install updated dependencies

### Phase 2: Database Connection

Create the database module with connection management.

**Tasks:**
- Create database.py with init_db and close_db functions
- Use Motor AsyncIOMotorClient for connection
- Use Beanie init_beanie for ODM setup

### Phase 3: User Model

Create the User document model.

**Tasks:**
- Create models/ directory structure
- Create User model matching PRD specification
- Add indexes for firebase_uid (unique)

### Phase 4: Integration

Integrate database into the FastAPI app lifecycle.

**Tasks:**
- Update main.py lifespan to call init_db/close_db
- Add error handling for database connection failures
- Test the integration

---

## STEP-BY-STEP TASKS

IMPORTANT: Execute every task in order, top to bottom. Each task is atomic and independently testable.

---

### Task 1: UPDATE `server/requirements.txt`

- **IMPLEMENT**: Add motor and beanie dependencies
- **PATTERN**: Match existing dependency format
- **GOTCHA**: beanie requires motor, but list both explicitly

Add these lines after `python-dotenv`:
```
motor>=3.3.0
beanie>=1.25.0
```

- **VALIDATE**: `cat server/requirements.txt | grep -E "motor|beanie"`

---

### Task 2: INSTALL updated dependencies

- **IMPLEMENT**: Install new packages in venv
- **VALIDATE**: `./venv/bin/pip install -r requirements.txt && ./venv/bin/python -c "import motor; import beanie; print('OK')"`

---

### Task 3: CREATE `server/app/models/__init__.py`

- **IMPLEMENT**: Models package with exports
- **PATTERN**: Mirror app/__init__.py style

```python
"""Pydantic and Beanie document models."""

from app.models.user import User

__all__ = ["User"]
```

- **VALIDATE**: `cat server/app/models/__init__.py`

---

### Task 4: CREATE `server/app/models/user.py`

- **IMPLEMENT**: User document model per PRD specification
- **PATTERN**: See PRD.md lines 718-729
- **IMPORTS**: beanie, pydantic
- **GOTCHA**: Use `Indexed(str, unique=True)` for firebase_uid

```python
"""User document model."""

from datetime import datetime

from beanie import Document, Indexed
from pydantic import EmailStr, Field


class User(Document):
    """User document stored in MongoDB.

    Users are created on first login via Firebase authentication.
    The firebase_uid is the primary identifier from Firebase Auth.
    """

    firebase_uid: Indexed(str, unique=True)  # type: ignore[valid-type]
    email: EmailStr
    name: str
    picture: str | None = None
    created_at: datetime = Field(default_factory=datetime.utcnow)
    updated_at: datetime = Field(default_factory=datetime.utcnow)

    class Settings:
        name = "users"

    async def update_last_seen(self) -> None:
        """Update the updated_at timestamp on login."""
        self.updated_at = datetime.utcnow()
        await self.save()
```

- **VALIDATE**: `./venv/bin/python -c "from app.models.user import User; print(f'User model OK: {User.Settings.name}')"`

---

### Task 5: CREATE `server/app/database.py`

- **IMPLEMENT**: MongoDB connection management with Beanie
- **PATTERN**: Async context pattern for connections
- **IMPORTS**: motor, beanie, structlog
- **GOTCHA**: Must pass all document models to init_beanie

```python
"""MongoDB database connection using Motor and Beanie ODM."""

import structlog
from beanie import init_beanie
from motor.motor_asyncio import AsyncIOMotorClient

from app.config import get_settings

logger = structlog.get_logger()

# Global client reference
_client: AsyncIOMotorClient | None = None


async def init_db() -> None:
    """Initialize MongoDB connection and Beanie ODM.

    Must be called during application startup.
    """
    global _client

    settings = get_settings()

    if not settings.mongodb_uri:
        logger.warning("No MongoDB URI configured, skipping database initialization")
        return

    logger.info("Connecting to MongoDB...")
    _client = AsyncIOMotorClient(settings.mongodb_uri)

    # Get database name from URI or use default
    database = _client.get_default_database()

    # Import models here to avoid circular imports
    from app.models.user import User

    await init_beanie(
        database=database,
        document_models=[User],
    )

    logger.info("Database initialized", database=database.name)


async def close_db() -> None:
    """Close MongoDB connection.

    Must be called during application shutdown.
    """
    global _client

    if _client is not None:
        _client.close()
        logger.info("Database connection closed")
        _client = None


def get_client() -> AsyncIOMotorClient | None:
    """Get the current MongoDB client instance."""
    return _client
```

- **VALIDATE**: `./venv/bin/python -c "from app.database import init_db, close_db; print('Database module OK')"`

---

### Task 6: UPDATE `server/app/main.py`

- **IMPLEMENT**: Add database initialization to lifespan
- **PATTERN**: Follow existing lifespan structure
- **GOTCHA**: Handle case where MongoDB URI is not configured (development mode)

Update the lifespan function to include database calls:

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

    # Initialize database
    await init_db()

    yield

    # Cleanup
    await close_db()
    logger.info("Application shutdown complete")
```

Also add the import at the top:
```python
from app.database import init_db, close_db
```

- **VALIDATE**: `./venv/bin/python -c "from app.main import app; print('Main app with DB OK')"`

---

### Task 7: UPDATE `server/.env.example`

- **IMPLEMENT**: Uncomment and document the MongoDB URI
- **PATTERN**: Follow existing format

Update to show MongoDB as primary configuration:
```
# MongoDB (required for database features)
MONGODB_URI=mongodb+srv://username:password@cluster.mongodb.net/roadmap_builder?retryWrites=true&w=majority

# Server
PORT=8000
ENVIRONMENT=development
CORS_ORIGINS=["http://localhost:5173"]

# These will be added in future phases:
# GOOGLE_APPLICATION_CREDENTIALS=./firebase-service-account.json
# GEMINI_API_KEY=...
```

- **VALIDATE**: `cat server/.env.example`

---

### Task 8: CREATE `server/app/models/` directory

- **IMPLEMENT**: Ensure the models directory exists
- **VALIDATE**: `ls -la server/app/models/`

```bash
mkdir -p server/app/models
```

---

## TESTING STRATEGY

### Manual Testing (No MongoDB)

Without a MongoDB connection, verify:
1. Server starts without errors (warns about missing MongoDB URI)
2. Health endpoint still works
3. All imports resolve correctly

### Manual Testing (With MongoDB)

With a MongoDB Atlas connection:
1. Set MONGODB_URI in .env
2. Start server, verify "Database initialized" log
3. Stop server, verify "Database connection closed" log

### Future Integration Tests

In Phase C, integration tests will:
- Create test users
- Query users by firebase_uid
- Update user timestamps

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
from app.main import app
print('All imports OK')
"
```

### Level 3: Server Start (No MongoDB)

```bash
cd server && timeout 5 ./venv/bin/uvicorn app.main:app --port 8000 2>&1 | head -20
# Should see: "No MongoDB URI configured, skipping database initialization"
```

### Level 4: Health Check

```bash
# Start server in background
cd server && ./venv/bin/uvicorn app.main:app --port 8000 &
sleep 2
curl http://localhost:8000/health
kill %1
# Expected: {"status":"healthy","environment":"development"}
```

### Level 5: With MongoDB (Optional)

```bash
# Only if you have MongoDB Atlas configured
cd server
cp .env.example .env
# Edit .env with your MongoDB URI
./venv/bin/uvicorn app.main:app --port 8000
# Should see: "Database initialized" in logs
```

---

## ACCEPTANCE CRITERIA

- [ ] motor and beanie added to requirements.txt
- [ ] Dependencies install without errors
- [ ] User model created with correct fields and indexes
- [ ] database.py has init_db and close_db functions
- [ ] main.py lifespan calls database init/close
- [ ] Server starts without MongoDB URI (with warning)
- [ ] Server starts with MongoDB URI and connects
- [ ] Health endpoint still works
- [ ] All imports resolve correctly
- [ ] Ruff linting passes

---

## COMPLETION CHECKLIST

- [ ] All 8 tasks completed in order
- [ ] Each task validation passed
- [ ] Server runs without database (warning mode)
- [ ] Ruff linting passes
- [ ] Ready for Phase C (Firebase authentication)

---

## NOTES

### Design Decisions

1. **Optional MongoDB in development**: The server should start even without MongoDB configured, allowing frontend development and health checks
2. **Global client reference**: Simple pattern for accessing the client; could be refactored to dependency injection later
3. **Indexed firebase_uid**: Unique index ensures fast lookups and prevents duplicate users

### What This Does NOT Include

- Firebase authentication (Phase C)
- API endpoints for users (Phase C)
- Roadmap model (separate phase)
- Integration tests (will add with actual endpoints)

### MongoDB Atlas Setup

Before running with database:
1. Create a free MongoDB Atlas cluster
2. Create a database user
3. Whitelist your IP (or use 0.0.0.0/0 for development)
4. Get connection string from Atlas UI
5. Replace the placeholder in .env

### Connection String Format

```
mongodb+srv://<username>:<password>@<cluster>.mongodb.net/<database>?retryWrites=true&w=majority
```

The database name in the URI will be used as the default database.
