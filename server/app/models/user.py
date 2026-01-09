"""User document model."""

from datetime import UTC, datetime

from beanie import Document, Indexed
from pydantic import EmailStr, Field


def utc_now() -> datetime:
    """Return current UTC time as timezone-aware datetime."""
    return datetime.now(UTC)


class User(Document):
    """User document stored in MongoDB.

    Users are created on first login via Firebase authentication.
    The firebase_uid is the primary identifier from Firebase Auth.
    """

    firebase_uid: Indexed(str, unique=True)  # type: ignore[valid-type]
    email: EmailStr
    name: str
    picture: str | None = None
    created_at: datetime = Field(default_factory=utc_now)
    updated_at: datetime = Field(default_factory=utc_now)

    class Settings:
        name = "users"

    async def update_last_seen(self) -> None:
        """Update the updated_at timestamp on login."""
        self.updated_at = utc_now()
        await self.save()
