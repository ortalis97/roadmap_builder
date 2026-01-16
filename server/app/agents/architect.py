"""Architect agent for creating session outlines."""

import asyncio
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
    """Schema for a single session in the architect response (legacy single-call)."""

    title: str
    objective: str
    session_type: str
    estimated_duration_minutes: int = 60
    prerequisites: list[int] = Field(default_factory=list)


class ArchitectResponse(BaseModel):
    """Response schema for architect output (legacy single-call)."""

    title: str  # AI-generated roadmap title
    sessions: list[SessionItemResponse]
    learning_path_summary: str
    total_estimated_hours: float


# Phase 1 models (fast, minimal)
class SessionOutlineMinimal(BaseModel):
    """Minimal session info for Phase 1 (fast)."""

    title: str = Field(description="Clear, descriptive session title")
    session_type: str = Field(description="One of: concept, tutorial, practice, project, review")


class ArchitectPhase1Response(BaseModel):
    """Phase 1 response: title and minimal session list."""

    title: str = Field(description="Descriptive roadmap title (3-8 words)")
    sessions: list[SessionOutlineMinimal] = Field(
        description="List of sessions with titles and types"
    )
    learning_path_summary: str = Field(description="2-3 sentence overview of the learning journey")


# Phase 2 model (detailed, per-session)
class SessionDetailResponse(BaseModel):
    """Phase 2 response: detailed info for a single session."""

    objective: str = Field(description="What the learner will achieve (1-2 sentences)")
    estimated_duration_minutes: int = Field(
        default=60, description="Time to complete (30-180 minutes)"
    )
    prerequisites: list[int] = Field(
        default_factory=list, description="0-based indices of prerequisite sessions"
    )


class ArchitectAgent(BaseAgent):
    """Agent that creates the session structure for a learning roadmap."""

    name = "architect"

    def get_system_prompt(self) -> str:
        return ARCHITECT_SYSTEM_PROMPT

    async def create_outline_phase1(
        self,
        interview_context: InterviewContext,
    ) -> ArchitectPhase1Response:
        """Phase 1: Get roadmap title and session structure (fast).

        Returns minimal session info for quick response.
        """
        qa_context = "\n".join([f"Q: {q}\nA: {a}" for q, a in interview_context.qa_pairs])

        prompt = f"""Create a learning roadmap structure for:

Topic: {interview_context.topic}

Learner Context:
{qa_context if qa_context else "No additional context provided"}

Create 5-15 sessions. For each session, specify only:
- title: Clear session title
- session_type: One of concept, tutorial, practice, project, review

Also provide:
- title: Descriptive roadmap title (3-8 words)
- learning_path_summary: 2-3 sentence overview"""

        return await self.generate_structured(
            prompt=prompt,
            response_model=ArchitectPhase1Response,
        )

    async def get_session_details(
        self,
        session_title: str,
        session_type: str,
        session_index: int,
        all_session_titles: list[str],
        topic: str,
    ) -> SessionDetailResponse:
        """Phase 2: Get detailed info for a single session.

        Args:
            session_title: Title of this session
            session_type: Type of session (concept, tutorial, etc.)
            session_index: 0-based index of this session
            all_session_titles: List of all session titles for context
            topic: Main learning topic
        """
        sessions_context = "\n".join(f"{i}. {title}" for i, title in enumerate(all_session_titles))

        prompt = f"""For this learning session, provide:

Session: {session_title}
Type: {session_type}
Position: Session {session_index + 1} of {len(all_session_titles)}

Topic: {topic}

All sessions in order:
{sessions_context}

Provide:
- objective: What the learner will achieve (1-2 sentences)
- estimated_duration_minutes: Realistic time to complete (30-180)
- prerequisites: List of session indices (0-based) that must come before this one"""

        return await self.generate_structured(
            prompt=prompt,
            response_model=SessionDetailResponse,
        )

    async def create_outline(
        self,
        interview_context: InterviewContext,
    ) -> tuple[str, SessionOutline]:
        """Create a session outline based on interview context.

        Uses two-phase approach:
        1. Fast call to get title + session structure
        2. Parallel calls to get details for each session

        Returns:
            A tuple of (suggested_title, session_outline)
        """
        # Phase 1: Get structure quickly
        phase1 = await self.create_outline_phase1(interview_context)

        # Phase 2: Get details for each session in parallel
        all_titles = [s.title for s in phase1.sessions]

        async def get_details(idx: int, session: SessionOutlineMinimal) -> SessionDetailResponse:
            return await self.get_session_details(
                session_title=session.title,
                session_type=session.session_type,
                session_index=idx,
                all_session_titles=all_titles,
                topic=interview_context.topic,
            )

        tasks = [get_details(i, s) for i, s in enumerate(phase1.sessions)]
        details_list = await asyncio.gather(*tasks)

        # Combine into SessionOutline
        sessions = []
        for i, (minimal, details) in enumerate(zip(phase1.sessions, details_list)):
            session_id = f"session_{uuid.uuid4().hex[:8]}"

            try:
                session_type = SessionType(minimal.session_type.lower())
            except ValueError:
                session_type = SessionType.CONCEPT

            sessions.append(
                SessionOutlineItem(
                    id=session_id,
                    title=minimal.title,
                    objective=details.objective,
                    session_type=session_type,
                    estimated_duration_minutes=details.estimated_duration_minutes,
                    prerequisites=[
                        sessions[idx].id for idx in details.prerequisites if idx < len(sessions)
                    ],
                    order=i + 1,
                )
            )

        # Calculate total hours
        total_minutes = sum(s.estimated_duration_minutes for s in sessions)
        total_hours = round(total_minutes / 60, 1)

        outline = SessionOutline(
            sessions=sessions,
            learning_path_summary=phase1.learning_path_summary,
            total_estimated_hours=total_hours,
        )

        return phase1.title, outline
