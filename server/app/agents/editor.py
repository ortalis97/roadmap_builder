"""Editor agent for surgical content fixes."""

from pydantic import BaseModel, Field

from app.agents.base import BaseAgent
from app.agents.prompts import (
    EDITOR_RESEARCH_REQUEST_PROMPT,
    EDITOR_SYSTEM_PROMPT,
    get_language_instruction,
)
from app.agents.state import (
    InterviewContext,
    ResearchedSession,
    SessionOutlineItem,
    ValidationIssue,
)


class EditorResponse(BaseModel):
    """Response schema for editor output."""

    edited_content: str = Field(description="Complete edited session content in markdown")
    needs_research: bool = Field(default=False, description="True if critical gap needs research")
    research_request: str | None = Field(
        default=None, description="What to research if needs_research"
    )


class ResearchSectionResponse(BaseModel):
    """Response schema for gap-filling research."""

    section_content: str = Field(description="The markdown content for this section")
    suggested_heading: str | None = Field(
        default=None, description="Optional heading for this section"
    )


class EditorAgent(BaseAgent):
    """Agent that performs surgical edits to fix validation issues."""

    name = "editor"
    model_config_key = "editor"

    def get_system_prompt(self) -> str:
        return EDITOR_SYSTEM_PROMPT

    async def edit_session(
        self,
        session: ResearchedSession,
        issues: list[ValidationIssue],
        outline_item: SessionOutlineItem,
        interview_context: InterviewContext,
        all_session_outlines: list[SessionOutlineItem],
        language: str = "en",
    ) -> ResearchedSession:
        """Edit a session to fix validation issues.

        Args:
            session: The session to edit
            issues: List of validation issues affecting this session
            outline_item: The session's outline for context
            interview_context: Interview context for research if needed
            all_session_outlines: All session outlines for context
            language: Language code for content

        Returns:
            Edited ResearchedSession with fixed content
        """
        # Build issues description
        issues_text = "\n".join(
            [
                f"- **{issue.issue_type.value.upper()}** ({issue.severity}): {issue.description}\n"
                f"  Suggested fix: {issue.suggested_fix}"
                for issue in issues
            ]
        )

        # Build other sessions context for overlap awareness
        other_sessions = [s for s in all_session_outlines if s.order != outline_item.order]
        sessions_context = (
            "\n".join(
                [f"- Session {s.order}: {s.title} ({s.session_type.value})" for s in other_sessions]
            )
            if other_sessions
            else "This is the only session"
        )

        language_instruction = get_language_instruction(language)

        prompt = f"""{language_instruction}Edit the following learning session content \
to fix the identified issues.

SESSION INFORMATION:
Title: {session.title}
Type: {session.session_type.value}
Objective: {outline_item.objective}
Order in roadmap: {session.order}

OTHER SESSIONS IN ROADMAP:
{sessions_context}

ISSUES TO FIX:
{issues_text}

CURRENT CONTENT:
{session.content}

---

Analyze each issue and make surgical edits to fix them while preserving good content.
Only set needs_research=true if there's a critical knowledge gap that cannot be
addressed with a brief explanation.

Output JSON:
{{
  "edited_content": "Complete edited markdown content...",
  "needs_research": false,
  "research_request": null
}}"""

        response = await self.generate_structured(
            prompt=prompt,
            response_model=EditorResponse,
        )

        edited_content = response.edited_content

        # If research needed, fetch specific section and merge
        if response.needs_research and response.research_request:
            self.logger.info(
                "Editor requesting research for gap",
                session_order=session.order,
                research_request=response.research_request[:100],
            )

            research_section = await self._fetch_research_section(
                research_request=response.research_request,
                session=session,
                outline_item=outline_item,
                interview_context=interview_context,
                language=language,
            )

            # Merge research section into edited content
            if research_section:
                edited_content = self._merge_research(
                    edited_content,
                    research_section,
                )

        # Return updated session with edited content
        return ResearchedSession(
            outline_id=session.outline_id,
            title=session.title,
            session_type=session.session_type,
            order=session.order,
            content=edited_content,
            key_concepts=session.key_concepts,  # Preserve
            resources=session.resources,  # Preserve
            exercises=session.exercises,  # Preserve
            videos=session.videos,  # Preserve videos
            language=language,
        )

    async def _fetch_research_section(
        self,
        research_request: str,
        session: ResearchedSession,
        outline_item: SessionOutlineItem,
        interview_context: InterviewContext,
        language: str,
    ) -> ResearchSectionResponse | None:
        """Fetch a specific section to fill a content gap.

        Uses a lighter model for targeted research.
        """
        # Use the editor_research model config
        original_config_key = self.model_config_key
        self.model_config_key = "editor_research"

        language_instruction = get_language_instruction(language)

        prompt = f"""{language_instruction}Generate content to fill a gap in a learning session.

SESSION CONTEXT:
Title: {session.title}
Type: {session.session_type.value}
Objective: {outline_item.objective}
Topic: {interview_context.topic}

RESEARCH REQUEST:
{research_request}

Generate a focused section of content that addresses this specific gap.
Keep it concise but complete enough to fill the knowledge gap.

Output JSON:
{{
  "section_content": "Markdown content for this section...",
  "suggested_heading": "Optional heading"
}}"""

        try:
            response = await self.generate_structured(
                prompt=prompt,
                response_model=ResearchSectionResponse,
                system_prompt=EDITOR_RESEARCH_REQUEST_PROMPT,
            )
            return response
        except Exception as e:
            self.logger.warning(
                "Research section fetch failed, proceeding without",
                error=str(e),
            )
            return None
        finally:
            self.model_config_key = original_config_key

    def _merge_research(
        self,
        edited_content: str,
        research_section: ResearchSectionResponse,
    ) -> str:
        """Merge researched section into edited content.

        Simple strategy: append at end with heading.
        Future improvement: use AI to find optimal insertion point.
        """
        heading = research_section.suggested_heading or "Additional Information"
        section = f"\n\n## {heading}\n\n{research_section.section_content}"
        return edited_content + section
