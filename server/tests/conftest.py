"""Shared test fixtures for integration tests."""

import pytest
from beanie import PydanticObjectId, init_beanie
from httpx import ASGITransport, AsyncClient
from mongomock_motor import AsyncMongoMockClient

from app.main import create_app
from app.middleware.auth import get_current_user
from app.models.agent_trace import AgentTrace
from app.models.chat_history import ChatHistory
from app.models.roadmap import Roadmap
from app.models.session import Session
from app.models.user import User


@pytest.fixture
def mock_user_data() -> dict:
    """Return mock Firebase token data for a test user."""
    return {
        "uid": "test-firebase-uid-123",
        "email": "test@example.com",
        "name": "Test User",
        "picture": "https://example.com/picture.jpg",
    }


@pytest.fixture
def other_user_data() -> dict:
    """Return mock Firebase token data for a different user."""
    return {
        "uid": "other-firebase-uid-456",
        "email": "other@example.com",
        "name": "Other User",
        "picture": None,
    }


@pytest.fixture
async def mock_user(init_test_db, mock_user_data: dict) -> User:
    """Create and return a test user in the database."""
    user = User(
        firebase_uid=mock_user_data["uid"],
        email=mock_user_data["email"],
        name=mock_user_data["name"],
        picture=mock_user_data["picture"],
    )
    await user.insert()
    return user


@pytest.fixture
async def other_user(init_test_db, other_user_data: dict) -> User:
    """Create and return a different test user in the database."""
    user = User(
        firebase_uid=other_user_data["uid"],
        email=other_user_data["email"],
        name=other_user_data["name"],
        picture=other_user_data["picture"],
    )
    await user.insert()
    return user


@pytest.fixture
async def init_test_db():
    """Initialize Beanie with mongomock for testing.

    This fixture sets up an in-memory MongoDB mock and initializes
    all Beanie document models. It runs before each test to ensure
    a clean database state.
    """
    client = AsyncMongoMockClient()
    database = client.get_database("test_roadmap_builder")

    await init_beanie(
        database=database,
        document_models=[AgentTrace, ChatHistory, Roadmap, Session, User],
    )

    yield database

    # Cleanup: drop all collections after test
    for collection_name in await database.list_collection_names():
        await database.drop_collection(collection_name)


@pytest.fixture
def test_app(mock_user: User):
    """Create FastAPI app with mocked authentication.

    Overrides the get_current_user dependency to return the mock user
    without requiring actual Firebase authentication.
    """
    app = create_app()

    async def override_get_current_user():
        return mock_user

    app.dependency_overrides[get_current_user] = override_get_current_user

    yield app

    app.dependency_overrides.clear()


@pytest.fixture
async def client(test_app, init_test_db) -> AsyncClient:
    """Create an async HTTP client for testing API endpoints.

    Uses ASGITransport to make requests directly to the FastAPI app
    without needing a running server.
    """
    transport = ASGITransport(app=test_app)
    async with AsyncClient(transport=transport, base_url="http://test") as ac:
        yield ac


@pytest.fixture
def app_no_auth(init_test_db):
    """Create FastAPI app without auth override for testing auth failures."""
    app = create_app()
    yield app
    app.dependency_overrides.clear()


@pytest.fixture
async def client_no_auth(app_no_auth, init_test_db) -> AsyncClient:
    """Create a client without auth for testing unauthenticated requests."""
    transport = ASGITransport(app=app_no_auth)
    async with AsyncClient(transport=transport, base_url="http://test") as ac:
        yield ac


# Helper fixtures for creating test data


@pytest.fixture
async def test_roadmap(mock_user: User, init_test_db) -> Roadmap:
    """Create a test roadmap in the database."""
    roadmap = Roadmap(
        user_id=mock_user.id,
        title="Learn Python",
        summary="A comprehensive Python learning journey",
        sessions=[],
    )
    await roadmap.insert()
    return roadmap


@pytest.fixture
async def test_roadmap_with_sessions(
    mock_user: User, init_test_db
) -> tuple[Roadmap, list[Session]]:
    """Create a test roadmap with sessions in the database."""
    from app.models.roadmap import SessionSummary

    # Create roadmap first
    roadmap = Roadmap(
        user_id=mock_user.id,
        title="Learn Python",
        summary="A comprehensive Python learning journey",
        sessions=[],
    )
    await roadmap.insert()

    # Create sessions
    sessions = []
    session_data = [
        ("Introduction to Python", "Learn Python basics and setup"),
        ("Variables and Types", "Understand Python data types"),
        ("Functions", "Learn to write functions"),
    ]

    for order, (title, content) in enumerate(session_data, start=1):
        session = Session(
            roadmap_id=roadmap.id,
            order=order,
            title=title,
            content=content,
            status="not_started",
        )
        await session.insert()
        sessions.append(session)

    # Update roadmap with session summaries
    roadmap.sessions = [SessionSummary(id=s.id, title=s.title, order=s.order) for s in sessions]
    await roadmap.save()

    return roadmap, sessions


@pytest.fixture
async def other_user_roadmap(other_user: User, init_test_db) -> Roadmap:
    """Create a roadmap belonging to a different user."""
    roadmap = Roadmap(
        user_id=other_user.id,
        title="Learn JavaScript",
        summary="A JavaScript learning journey",
        sessions=[],
    )
    await roadmap.insert()
    return roadmap


def make_object_id() -> PydanticObjectId:
    """Generate a new random ObjectId for testing."""
    return PydanticObjectId()
