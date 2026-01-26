"""Researcher agents for creating session content."""

from google import genai
from pydantic import BaseModel, Field

from app.agents.base import BaseAgent
from app.agents.prompts import (
    CONCEPT_RESEARCHER_PROMPT,
    PRACTICE_RESEARCHER_PROMPT,
    PROJECT_RESEARCHER_PROMPT,
    RESEARCHER_BASE_PROMPT,
    REVIEW_RESEARCHER_PROMPT,
    TUTORIAL_RESEARCHER_PROMPT,
    get_language_instruction,
)
from app.agents.state import (
    InterviewContext,
    ResearchedSession,
    SessionOutlineItem,
    SessionType,
)


class ResearchResponse(BaseModel):
    """Response schema for researcher output."""

    content: str
    key_concepts: list[str] = Field(default_factory=list)
    resources: list[str] = Field(default_factory=list)
    exercises: list[str] = Field(default_factory=list)


class ResearcherAgent(BaseAgent):
    """Base researcher agent - subclass for specialized session types."""

    name = "researcher"
    model_config_key = "researcher"
    session_type: SessionType = SessionType.CONCEPT

    def get_system_prompt(self) -> str:
        return RESEARCHER_BASE_PROMPT

    async def research_session(
        self,
        outline_item: SessionOutlineItem,
        interview_context: InterviewContext,
        previous_sessions: list[ResearchedSession],
        language: str = "en",
    ) -> ResearchedSession:
        """Create detailed content for a single session."""
        # Build context from previous sessions
        prev_context = (
            "\n".join(
                [f"- {s.title}: {', '.join(s.key_concepts[:3])}" for s in previous_sessions[-3:]]
            )
            if previous_sessions
            else "None yet"
        )

        language_instruction = get_language_instruction(language)
        prompt = f"""{language_instruction}Create detailed content for this learning session:

Session: {outline_item.title}
Type: {outline_item.session_type.value}
Objective: {outline_item.objective}
Duration: ~{outline_item.estimated_duration_minutes} minutes

Learning Topic: {interview_context.topic}

Previous sessions covered:
{prev_context}

Create comprehensive, engaging content appropriate for self-directed learning.

Output JSON:
{{
  "content": "Full markdown content for the session...",
  "key_concepts": ["concept1", "concept2"],
  "resources": ["url or book reference"],
  "exercises": ["exercise description if applicable"]
}}"""

        response = await self.generate_structured(
            prompt=prompt,
            response_model=ResearchResponse,
        )

        return ResearchedSession(
            outline_id=outline_item.id,
            title=outline_item.title,
            session_type=outline_item.session_type,
            order=outline_item.order,
            content=response.content,
            key_concepts=response.key_concepts,
            resources=response.resources,
            exercises=response.exercises,
        )


class ConceptResearcher(ResearcherAgent):
    """Specialized researcher for concept sessions."""

    name = "concept_researcher"
    session_type = SessionType.CONCEPT

    def get_system_prompt(self) -> str:
        return CONCEPT_RESEARCHER_PROMPT


class TutorialResearcher(ResearcherAgent):
    """Specialized researcher for tutorial sessions."""

    name = "tutorial_researcher"
    session_type = SessionType.TUTORIAL

    def get_system_prompt(self) -> str:
        return TUTORIAL_RESEARCHER_PROMPT


class PracticeResearcher(ResearcherAgent):
    """Specialized researcher for practice sessions."""

    name = "practice_researcher"
    session_type = SessionType.PRACTICE

    def get_system_prompt(self) -> str:
        return PRACTICE_RESEARCHER_PROMPT


class ProjectResearcher(ResearcherAgent):
    """Specialized researcher for project sessions."""

    name = "project_researcher"
    session_type = SessionType.PROJECT

    def get_system_prompt(self) -> str:
        return PROJECT_RESEARCHER_PROMPT


class ReviewResearcher(ResearcherAgent):
    """Specialized researcher for review sessions."""

    name = "review_researcher"
    session_type = SessionType.REVIEW

    def get_system_prompt(self) -> str:
        return REVIEW_RESEARCHER_PROMPT


def get_researcher_for_type(session_type: SessionType, client: genai.Client) -> ResearcherAgent:
    """Factory function to get the appropriate researcher for a session type."""
    researchers: dict[SessionType, type[ResearcherAgent]] = {
        SessionType.CONCEPT: ConceptResearcher,
        SessionType.TUTORIAL: TutorialResearcher,
        SessionType.PRACTICE: PracticeResearcher,
        SessionType.PROJECT: ProjectResearcher,
        SessionType.REVIEW: ReviewResearcher,
    }
    researcher_class = researchers.get(session_type, ConceptResearcher)
    return researcher_class(client)
