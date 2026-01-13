"""Chat history document model for AI assistant conversations."""

from datetime import UTC, datetime
from typing import Literal
from uuid import uuid4

from beanie import Document, Indexed, PydanticObjectId
from pydantic import BaseModel, Field


def utc_now() -> datetime:
    """Return current UTC time as timezone-aware datetime."""
    return datetime.now(UTC)


def generate_conversation_id() -> str:
    """Generate a new conversation ID."""
    return str(uuid4())


MessageRole = Literal["user", "assistant"]


class ChatMessage(BaseModel):
    """Individual chat message within a conversation."""

    role: MessageRole
    content: str
    timestamp: datetime = Field(default_factory=utc_now)


class ChatHistory(Document):
    """Chat history document for AI assistant conversations.

    Each document represents a conversation within a session.
    Multiple conversations per session are supported via conversation_id.
    """

    conversation_id: Indexed(str) = Field(default_factory=generate_conversation_id)  # type: ignore[valid-type]
    session_id: Indexed(PydanticObjectId)  # type: ignore[valid-type]
    roadmap_id: Indexed(PydanticObjectId)  # type: ignore[valid-type]
    user_id: Indexed(PydanticObjectId)  # type: ignore[valid-type]
    messages: list[ChatMessage] = Field(default_factory=list)
    created_at: datetime = Field(default_factory=utc_now)
    updated_at: datetime = Field(default_factory=utc_now)

    class Settings:
        name = "chat_histories"

    async def add_message(self, role: MessageRole, content: str) -> ChatMessage:
        """Add a message to the conversation and save."""
        message = ChatMessage(role=role, content=content)
        self.messages.append(message)
        self.updated_at = utc_now()
        await self.save()
        return message
