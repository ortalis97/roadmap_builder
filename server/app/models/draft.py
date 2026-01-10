"""Draft document model."""

from datetime import UTC, datetime

from beanie import Document, Indexed, PydanticObjectId
from pydantic import Field


def utc_now() -> datetime:
    """Return current UTC time as timezone-aware datetime."""
    return datetime.now(UTC)


class Draft(Document):
    """Draft document storing raw pasted learning plan text.

    Drafts are created when a user pastes their learning plan.
    The raw text is stored separately from the Roadmap to keep
    production documents lean.
    """

    user_id: Indexed(PydanticObjectId)  # type: ignore[valid-type]
    raw_text: str
    created_at: datetime = Field(default_factory=utc_now)

    class Settings:
        name = "drafts"
