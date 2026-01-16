"""Roadmap document model."""

from datetime import UTC, datetime

from beanie import Document, Indexed, PydanticObjectId
from pydantic import BaseModel, Field


def utc_now() -> datetime:
    """Return current UTC time as timezone-aware datetime."""
    return datetime.now(UTC)


class SessionSummary(BaseModel):
    """Lightweight session reference embedded in Roadmap.

    Contains only essential info for quick listing.
    Full session content is in the Session collection.
    """

    id: PydanticObjectId
    title: str
    order: int


class Roadmap(Document):
    """Roadmap document representing a learning journey.

    Contains a lightweight array of session summaries for quick listing.
    """

    user_id: Indexed(PydanticObjectId)  # type: ignore[valid-type]
    title: str
    summary: str | None = None
    sessions: list[SessionSummary] = Field(default_factory=list)
    created_at: datetime = Field(default_factory=utc_now)
    updated_at: datetime = Field(default_factory=utc_now)

    class Settings:
        name = "roadmaps"

    async def update_timestamp(self) -> None:
        """Update the updated_at timestamp."""
        self.updated_at = utc_now()
        await self.save()
