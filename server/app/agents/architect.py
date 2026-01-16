"""Architect agent for creating session outlines."""

import uuid

from pydantic import BaseModel, Field

from app.agents.base import BaseAgent
from app.agents.prompts import ARCHITECT_SYSTEM_PROMPT
from app.agents.state import (
    InterviewContext,
    SessionOutline,
    SessionOutlineItem,
    SessionType,
)


class SessionItemResponse(BaseModel):
    """Schema for a single session in the architect response."""

    title: str
    objective: str
    session_type: str
    estimated_duration_minutes: int = 60
    prerequisites: list[int] = Field(default_factory=list)


class ArchitectResponse(BaseModel):
    """Response schema for architect output."""

    title: str  # AI-generated roadmap title
    sessions: list[SessionItemResponse]
    learning_path_summary: str
    total_estimated_hours: float


class ArchitectAgent(BaseAgent):
    """Agent that creates the session structure for a learning roadmap."""

    name = "architect"

    def get_system_prompt(self) -> str:
        return ARCHITECT_SYSTEM_PROMPT

    async def create_outline(
        self,
        interview_context: InterviewContext,
    ) -> tuple[str, SessionOutline]:
        """Create a session outline based on interview context.

        Returns:
            A tuple of (suggested_title, session_outline)
        """
        # Build Q&A context string
        qa_context = "\n".join([f"Q: {q}\nA: {a}" for q, a in interview_context.qa_pairs])

        prompt = f"""Create a learning session outline for:

Topic: {interview_context.topic}

Learner Context (from interview):
{qa_context if qa_context else "No additional context provided"}

Create 5-15 sessions with varied types (concept, tutorial, practice, project, review).
For prerequisites, use the index (0-based) of sessions that must come first.

Also generate a descriptive, engaging title for this roadmap (3-8 words).

Output JSON:
{{
  "title": "Descriptive Roadmap Title",
  "sessions": [
    {{
      "title": "Session title",
      "objective": "What the learner will achieve",
      "session_type": "concept|tutorial|practice|project|review",
      "estimated_duration_minutes": 60,
      "prerequisites": []
    }}
  ],
  "learning_path_summary": "2-3 sentence overview of the learning journey",
  "total_estimated_hours": 10.5
}}"""

        response = await self.generate_structured(
            prompt=prompt,
            response_model=ArchitectResponse,
        )

        # Convert to our state models with unique IDs
        sessions = []
        for i, s in enumerate(response.sessions):
            session_id = f"session_{uuid.uuid4().hex[:8]}"

            # Map string type to enum
            try:
                session_type = SessionType(s.session_type.lower())
            except ValueError:
                session_type = SessionType.CONCEPT

            sessions.append(
                SessionOutlineItem(
                    id=session_id,
                    title=s.title,
                    objective=s.objective,
                    session_type=session_type,
                    estimated_duration_minutes=s.estimated_duration_minutes,
                    prerequisites=[
                        sessions[idx].id for idx in s.prerequisites if idx < len(sessions)
                    ],
                    order=i + 1,
                )
            )

        outline = SessionOutline(
            sessions=sessions,
            learning_path_summary=response.learning_path_summary,
            total_estimated_hours=response.total_estimated_hours,
        )

        return response.title, outline
