"""Base agent class for all specialized agents."""

import asyncio
import json
import uuid
from abc import ABC, abstractmethod
from datetime import UTC, datetime
from functools import partial
from typing import TypeVar

import structlog
from google import genai
from google.genai import types
from pydantic import BaseModel

from app.models.agent_trace import AgentSpan

logger = structlog.get_logger()

T = TypeVar("T", bound=BaseModel)


class BaseAgent(ABC):
    """Abstract base class for all agents in the pipeline."""

    name: str = "base_agent"
    default_temperature: float = 0.7
    default_max_tokens: int = 8192

    def __init__(self, client: genai.Client):
        self.client = client
        self.logger = structlog.get_logger().bind(agent=self.name)

    @abstractmethod
    def get_system_prompt(self) -> str:
        """Return the system prompt for this agent."""

    def _generate_sync(
        self,
        prompt: str,
        system_prompt: str,
        temperature: float | None = None,
        max_tokens: int | None = None,
    ) -> str:
        """Synchronous Gemini API call."""
        response = self.client.models.generate_content(
            model="gemini-2.0-flash",
            contents=prompt,
            config=types.GenerateContentConfig(
                system_instruction=system_prompt,
                temperature=temperature or self.default_temperature,
                max_output_tokens=max_tokens or self.default_max_tokens,
            ),
        )
        return response.text

    async def generate(
        self,
        prompt: str,
        system_prompt: str | None = None,
        temperature: float | None = None,
        max_tokens: int | None = None,
    ) -> str:
        """Async wrapper for Gemini API call."""
        loop = asyncio.get_event_loop()
        return await loop.run_in_executor(
            None,
            partial(
                self._generate_sync,
                prompt,
                system_prompt or self.get_system_prompt(),
                temperature,
                max_tokens,
            ),
        )

    async def generate_structured(
        self,
        prompt: str,
        response_model: type[T],
        system_prompt: str | None = None,
        max_retries: int = 2,
    ) -> T:
        """Generate and parse structured output into a Pydantic model."""
        last_error: Exception | None = None

        for attempt in range(max_retries + 1):
            try:
                response_text = await self.generate(
                    prompt=prompt,
                    system_prompt=system_prompt,
                )

                # Clean markdown code blocks
                cleaned = response_text.strip()
                if cleaned.startswith("```json"):
                    cleaned = cleaned[7:]
                if cleaned.startswith("```"):
                    cleaned = cleaned[3:]
                if cleaned.endswith("```"):
                    cleaned = cleaned[:-3]
                cleaned = cleaned.strip()

                data = json.loads(cleaned)
                return response_model.model_validate(data)

            except (json.JSONDecodeError, ValueError) as e:
                last_error = e
                self.logger.warning(
                    "Failed to parse response",
                    attempt=attempt + 1,
                    error=str(e),
                )

        raise ValueError(f"Failed after {max_retries + 1} attempts: {last_error}")

    def create_span(self, operation: str) -> AgentSpan:
        """Create a new span for tracking this operation."""
        return AgentSpan(
            span_id=str(uuid.uuid4()),
            agent_name=self.name,
            operation=operation,
            started_at=datetime.now(UTC),
        )

    def complete_span(
        self,
        span: AgentSpan,
        status: str = "success",
        output_summary: str | None = None,
        error: Exception | None = None,
    ) -> AgentSpan:
        """Complete a span with timing and status."""
        span.ended_at = datetime.now(UTC)
        if span.started_at:
            span.duration_ms = int((span.ended_at - span.started_at).total_seconds() * 1000)
        span.status = status  # type: ignore[assignment]
        span.output_summary = output_summary

        if error:
            span.status = "error"
            span.error_type = type(error).__name__
            span.error_message = str(error)

        return span
