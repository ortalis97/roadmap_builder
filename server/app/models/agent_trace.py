"""AgentTrace document model for logging agent execution."""

from datetime import UTC, datetime
from typing import Any, Literal

from beanie import Document, Indexed
from pydantic import BaseModel, Field


def utc_now() -> datetime:
    """Return current UTC time as timezone-aware datetime."""
    return datetime.now(UTC)


class AgentSpan(BaseModel):
    """A single agent execution span within a pipeline trace."""

    span_id: str
    agent_name: str
    operation: str  # e.g., "generate_questions", "create_outline"
    started_at: datetime
    ended_at: datetime | None = None
    duration_ms: int | None = None
    status: Literal["running", "success", "error"] = "running"

    # Input/output tracking
    input_summary: str | None = None  # Brief description of input
    input_tokens: int | None = None  # Estimated input tokens
    output_summary: str | None = None  # Brief description of output
    output_tokens: int | None = None  # Estimated output tokens

    # Error tracking
    error_type: str | None = None
    error_message: str | None = None

    # Model info
    model_name: str = "gemini-2.0-flash"
    temperature: float = 0.7

    # Custom metadata
    metadata: dict[str, Any] = Field(default_factory=dict)


class AgentTrace(Document):
    """Document tracking a complete pipeline execution for debugging.

    Each document represents a single roadmap creation pipeline run.
    Contains spans for each agent operation within the pipeline.
    """

    pipeline_id: Indexed(str)  # type: ignore[valid-type]
    user_id: Indexed(str)  # type: ignore[valid-type]

    # Pipeline info
    initial_topic: str
    initial_title: str

    # Spans for each agent call
    spans: list[AgentSpan] = Field(default_factory=list)

    # Pipeline result
    final_status: Literal["running", "success", "error", "abandoned"] = "running"
    roadmap_id: str | None = None

    # Aggregate metrics
    total_duration_ms: int | None = None
    total_input_tokens: int | None = None
    total_output_tokens: int | None = None
    total_agent_calls: int = 0

    # Timestamps
    created_at: datetime = Field(default_factory=utc_now)
    updated_at: datetime = Field(default_factory=utc_now)
    completed_at: datetime | None = None

    class Settings:
        name = "agent_traces"

    def add_span(self, span: AgentSpan) -> None:
        """Add a span and update aggregates."""
        self.spans.append(span)
        self.total_agent_calls = len(self.spans)
        if span.input_tokens:
            self.total_input_tokens = (self.total_input_tokens or 0) + span.input_tokens
        if span.output_tokens:
            self.total_output_tokens = (self.total_output_tokens or 0) + span.output_tokens
        self.updated_at = utc_now()

    async def complete(
        self,
        status: Literal["success", "error"],
        roadmap_id: str | None = None,
    ) -> None:
        """Mark the trace as completed and save."""
        self.final_status = status
        self.roadmap_id = roadmap_id
        self.completed_at = utc_now()
        if self.spans:
            first_span = self.spans[0]
            if first_span.started_at and self.completed_at:
                duration = (self.completed_at - first_span.started_at).total_seconds()
                self.total_duration_ms = int(duration * 1000)
        await self.save()
