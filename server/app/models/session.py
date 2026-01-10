"""Session document model."""

from datetime import UTC, datetime
from typing import Literal

from beanie import Document, Indexed, PydanticObjectId
from pydantic import Field


def utc_now() -> datetime:
    """Return current UTC time as timezone-aware datetime."""
    return datetime.now(UTC)


SessionStatus = Literal["not_started", "in_progress", "done", "skipped"]


class Session(Document):
    """Session document representing an individual learning session.

    Sessions contain the full content, notes, and status.
    They are stored separately from Roadmap for independent access.
    """

    roadmap_id: Indexed(PydanticObjectId)  # type: ignore[valid-type]
    order: int
    title: str
    content: str
    status: SessionStatus = "not_started"
    notes: str = ""
    created_at: datetime = Field(default_factory=utc_now)
    updated_at: datetime = Field(default_factory=utc_now)

    class Settings:
        name = "sessions"

    async def update_timestamp(self) -> None:
        """Update the updated_at timestamp."""
        self.updated_at = utc_now()
        await self.save()
