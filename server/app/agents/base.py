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

from app.model_config import get_model_config
from app.models.agent_trace import AgentSpan

logger = structlog.get_logger()

T = TypeVar("T", bound=BaseModel)


class BaseAgent(ABC):
    """Abstract base class for all agents in the pipeline."""

    name: str = "base_agent"
    model_config_key: str = "researcher"  # Default, subclasses override

    def __init__(self, client: genai.Client):
        self.client = client
        self._model_config = get_model_config(self.model_config_key)
        self.logger = structlog.get_logger().bind(agent=self.name)

    @property
    def model(self) -> str:
        """Get the model name for this agent."""
        return self._model_config.model.value

    @property
    def default_temperature(self) -> float:
        """Get the default temperature for this agent."""
        return self._model_config.temperature

    @property
    def default_max_tokens(self) -> int:
        """Get the default max tokens for this agent."""
        return self._model_config.max_tokens

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
            model=self.model,
            contents=prompt,
            config=types.GenerateContentConfig(
                system_instruction=system_prompt,
                temperature=temperature or self.default_temperature,
                max_output_tokens=max_tokens or self.default_max_tokens,
            ),
        )
        return response.text

    def _add_property_ordering(self, schema: dict) -> dict:
        """Add propertyOrdering to schema for Gemini 2.0 compatibility.

        Gemini 2.0 requires explicit propertyOrdering to ensure consistent output order.
        """
        schema = schema.copy()
        if "properties" in schema:
            schema["propertyOrdering"] = list(schema["properties"].keys())
            # Recursively add to nested objects
            for key, prop_schema in schema["properties"].items():
                if isinstance(prop_schema, dict):
                    if prop_schema.get("type") == "object":
                        schema["properties"][key] = self._add_property_ordering(prop_schema)
                    elif prop_schema.get("type") == "array" and "items" in prop_schema:
                        items = prop_schema["items"]
                        if isinstance(items, dict) and items.get("type") == "object":
                            prop_schema = prop_schema.copy()
                            prop_schema["items"] = self._add_property_ordering(items)
                            schema["properties"][key] = prop_schema
        return schema

    def _generate_structured_sync(
        self,
        prompt: str,
        system_prompt: str,
        response_schema: dict,
        temperature: float | None = None,
        max_tokens: int | None = None,
    ) -> str:
        """Synchronous Gemini API call with schema-constrained output."""
        # Add propertyOrdering for Gemini compatibility
        schema_with_ordering = self._add_property_ordering(response_schema)

        response = self.client.models.generate_content(
            model=self.model,
            contents=prompt,
            config={
                "system_instruction": system_prompt,
                "temperature": temperature or self.default_temperature,
                "max_output_tokens": max_tokens or self.default_max_tokens,
                "response_mime_type": "application/json",
                "response_json_schema": schema_with_ordering,
            },
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
        use_schema_output: bool = True,
    ) -> T:
        """Generate and parse structured output into a Pydantic model.

        Args:
            prompt: The user prompt
            response_model: Pydantic model class to validate against
            system_prompt: Optional system prompt override
            max_retries: Number of retry attempts
            use_schema_output: If True, use Gemini's response_json_schema for guaranteed JSON
        """
        last_error: Exception | None = None

        for attempt in range(max_retries + 1):
            try:
                if use_schema_output:
                    # Get JSON schema from Pydantic model
                    json_schema = response_model.model_json_schema()

                    # Use schema-constrained output
                    loop = asyncio.get_event_loop()
                    response_text = await loop.run_in_executor(
                        None,
                        partial(
                            self._generate_structured_sync,
                            prompt,
                            system_prompt or self.get_system_prompt(),
                            json_schema,
                        ),
                    )

                    # Parse directly with Pydantic (simpler than json.loads + validate)
                    return response_model.model_validate_json(response_text)
                else:
                    # Fallback to manual parsing (legacy path)
                    response_text = await self.generate(
                        prompt=prompt,
                        system_prompt=system_prompt,
                    )

                    # Clean markdown code blocks if present
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
                    use_schema_output=use_schema_output,
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
