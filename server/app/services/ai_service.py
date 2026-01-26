"""AI service for generating learning sessions using Google Gemini."""

import asyncio
import json
from functools import partial

import structlog
from google import genai
from google.genai import types
from pydantic import BaseModel, ValidationError

from app.config import get_settings
from app.model_config import get_model_config

logger = structlog.get_logger()

# Gemini client instance
_client: genai.Client | None = None


class GeneratedSession(BaseModel):
    """Schema for AI-generated session."""

    title: str
    content: str


class GeneratedRoadmap(BaseModel):
    """Schema for AI-generated roadmap with sessions."""

    summary: str
    sessions: list[GeneratedSession]


SYSTEM_PROMPT = """You are a learning roadmap architect. Given a learning goal or plan,
create a structured roadmap with sessions.

Output valid JSON matching this schema:
{
  "summary": "2-3 sentence overview of the learning journey",
  "sessions": [
    {
      "title": "Session title",
      "content": "Detailed learning content with objectives, key concepts, etc."
    }
  ]
}

Rules:
- Create 5-15 sessions depending on scope
- Each session should be completable in 1-3 hours
- Progress from fundamentals to advanced
- Include practical exercises where relevant
- Content should be educational and actionable, use markdown formatting
- Do NOT include an index or table of contents as a session
- DO include intro/overview sessions and summary/resources sessions
- Output ONLY valid JSON, no markdown code blocks or other text
"""


CHAT_SYSTEM_PROMPT = """You are a knowledgeable and supportive learning assistant \
embedded in a learning roadmap application.

Your role is to help the learner understand the current session's content, \
answer questions, provide examples, clarify concepts, and guide them through \
their learning journey.

Context provided to you:
- The roadmap title and summary (overall learning goal)
- All session titles (to understand the learning path)
- The current session's title and full content
- The learner's personal notes for this session
- Previous conversation history (if any)

Guidelines:
- Be encouraging and supportive
- Provide clear, accurate explanations
- Use examples when helpful
- Reference specific parts of the session content when relevant
- Acknowledge and build upon the learner's notes if they exist
- Keep responses focused and concise unless detail is requested
- If asked about topics outside the session scope, relate back to the learning journey
- Format responses in markdown for better readability
"""


def init_gemini() -> None:
    """Initialize Gemini client.

    Call this once during application startup.
    Skips initialization if API key not configured.
    """
    global _client

    if _client is not None:
        return  # Already initialized

    settings = get_settings()

    if not settings.gemini_api_key:
        logger.warning("Gemini API key not configured, AI features will be disabled")
        return

    try:
        _client = genai.Client(api_key=settings.gemini_api_key)
        logger.info("Gemini client initialized")
    except Exception as e:
        logger.error("Failed to initialize Gemini client", error=str(e))
        raise


def is_gemini_configured() -> bool:
    """Check if Gemini client is initialized."""
    return _client is not None


def _generate_content_sync(prompt: str) -> str:
    """Synchronous Gemini API call (runs in thread pool)."""
    if _client is None:
        raise RuntimeError("Gemini client not initialized")

    config = get_model_config("roadmap_generation")
    response = _client.models.generate_content(
        model=config.model.value,
        contents=prompt,
        config=types.GenerateContentConfig(
            system_instruction=SYSTEM_PROMPT,
            temperature=config.temperature,
            max_output_tokens=config.max_tokens,
        ),
    )

    return response.text


async def generate_sessions_from_draft(
    raw_text: str,
    title: str,
    max_retries: int = 2,
) -> GeneratedRoadmap:
    """Generate structured sessions from raw learning plan text.

    Args:
        raw_text: The raw learning plan pasted by user
        title: The roadmap title provided by user
        max_retries: Number of retry attempts on parse failure

    Returns:
        GeneratedRoadmap with summary and sessions

    Raises:
        ValueError: If AI response cannot be parsed after retries
        RuntimeError: If Gemini client is not initialized
    """
    if _client is None:
        raise RuntimeError("Gemini client not initialized")

    user_prompt = f"""Create a learning roadmap for the following:

Title: {title}

Learning Plan:
{raw_text}

Remember to output ONLY valid JSON matching the required schema."""

    last_error: Exception | None = None

    for attempt in range(max_retries + 1):
        try:
            logger.info(
                "Calling Gemini API",
                attempt=attempt + 1,
                title=title,
                input_length=len(raw_text),
            )

            # Run synchronous API call in thread pool
            loop = asyncio.get_event_loop()
            response_text = await loop.run_in_executor(
                None,
                partial(_generate_content_sync, user_prompt),
            )

            logger.debug("Gemini response received", response_length=len(response_text))

            # Clean up response - remove markdown code blocks if present
            cleaned_response = response_text.strip()
            if cleaned_response.startswith("```json"):
                cleaned_response = cleaned_response[7:]
            if cleaned_response.startswith("```"):
                cleaned_response = cleaned_response[3:]
            if cleaned_response.endswith("```"):
                cleaned_response = cleaned_response[:-3]
            cleaned_response = cleaned_response.strip()

            # Parse JSON and validate with Pydantic
            data = json.loads(cleaned_response)
            result = GeneratedRoadmap.model_validate(data)

            logger.info(
                "Sessions generated successfully",
                session_count=len(result.sessions),
            )

            return result

        except json.JSONDecodeError as e:
            last_error = e
            logger.warning(
                "Failed to parse AI response as JSON",
                attempt=attempt + 1,
                error=str(e),
            )
        except ValidationError as e:
            last_error = e
            logger.warning(
                "AI response failed schema validation",
                attempt=attempt + 1,
                error=str(e),
            )
        except Exception as e:
            last_error = e
            logger.error(
                "Gemini API call failed",
                attempt=attempt + 1,
                error=str(e),
            )

    # All retries exhausted
    raise ValueError(
        f"Failed to generate valid sessions after {max_retries + 1} attempts: {last_error}"
    )


def _generate_chat_response_sync(
    system_prompt: str,
    conversation_history: list[dict],
    user_message: str,
) -> str:
    """Synchronous Gemini chat call (runs in thread pool).

    Args:
        system_prompt: System instruction with context
        conversation_history: List of previous messages with role and content
        user_message: Current user message

    Returns:
        AI-generated response text
    """
    if _client is None:
        raise RuntimeError("Gemini client not initialized")

    # Build the contents array with conversation history
    contents = []
    for msg in conversation_history:
        role = "user" if msg["role"] == "user" else "model"
        contents.append(types.Content(role=role, parts=[types.Part(text=msg["content"])]))

    # Add current user message
    contents.append(types.Content(role="user", parts=[types.Part(text=user_message)]))

    config = get_model_config("chat")
    response = _client.models.generate_content(
        model=config.model.value,
        contents=contents,
        config=types.GenerateContentConfig(
            system_instruction=system_prompt,
            temperature=config.temperature,
            max_output_tokens=config.max_tokens,
        ),
    )

    return response.text


async def generate_chat_response(
    roadmap_title: str,
    roadmap_summary: str | None,
    all_session_titles: list[str],
    current_session_title: str,
    current_session_content: str,
    user_notes: str,
    conversation_history: list[dict],
    user_message: str,
) -> str:
    """Generate an AI response for the chat assistant.

    Args:
        roadmap_title: Title of the learning roadmap
        roadmap_summary: Summary of the roadmap (can be None)
        all_session_titles: List of all session titles in order
        current_session_title: Title of the current session
        current_session_content: Full content of the current session
        user_notes: User's personal notes for this session
        conversation_history: Previous messages in the conversation
        user_message: The new message from the user

    Returns:
        AI-generated response string

    Raises:
        RuntimeError: If Gemini client is not initialized
    """
    if _client is None:
        raise RuntimeError("Gemini client not initialized")

    # Build context section
    context_parts = [
        f"## Roadmap: {roadmap_title}",
        f"Summary: {roadmap_summary or 'No summary provided'}",
        "",
        "## Learning Path (All Sessions):",
        "\n".join(f"- {title}" for title in all_session_titles),
        "",
        f"## Current Session: {current_session_title}",
        "",
        "### Session Content:",
        current_session_content,
    ]

    if user_notes.strip():
        context_parts.extend(
            [
                "",
                "### Learner's Notes:",
                user_notes,
            ]
        )

    context = "\n".join(context_parts)
    full_system_prompt = f"{CHAT_SYSTEM_PROMPT}\n\n---\n\n# Current Context\n\n{context}"

    logger.info(
        "Generating chat response",
        roadmap_title=roadmap_title,
        session_title=current_session_title,
        history_length=len(conversation_history),
        message_length=len(user_message),
    )

    loop = asyncio.get_event_loop()
    response_text = await loop.run_in_executor(
        None,
        partial(
            _generate_chat_response_sync,
            full_system_prompt,
            conversation_history,
            user_message,
        ),
    )

    logger.debug("Chat response generated", response_length=len(response_text))

    return response_text
