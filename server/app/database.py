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
    from app.models.agent_trace import AgentTrace
    from app.models.chat_history import ChatHistory
    from app.models.roadmap import Roadmap
    from app.models.session import Session
    from app.models.user import User

    await init_beanie(
        database=database,
        document_models=[AgentTrace, ChatHistory, Roadmap, Session, User],
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
