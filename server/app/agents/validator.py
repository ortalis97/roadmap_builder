"""Validator agent for checking roadmap quality."""

import uuid

from pydantic import BaseModel, Field

from app.agents.base import BaseAgent
from app.agents.prompts import VALIDATOR_SYSTEM_PROMPT
from app.agents.state import (
    ResearchedSession,
    SessionOutline,
    ValidationIssue,
    ValidationIssueType,
    ValidationResult,
)


class IssueResponse(BaseModel):
    """Schema for a single validation issue."""

    issue_type: str
    severity: str
    description: str
    affected_session_indices: list[int]
    suggested_fix: str


class ValidatorResponse(BaseModel):
    """Response schema for validator output."""

    is_valid: bool
    issues: list[IssueResponse] = Field(default_factory=list)
    overall_score: float
    summary: str


class ValidatorAgent(BaseAgent):
    """Agent that validates the complete roadmap for quality issues."""

    name = "validator"
    model_config_key = "validator"

    def get_system_prompt(self) -> str:
        return VALIDATOR_SYSTEM_PROMPT

    async def validate(
        self,
        outline: SessionOutline,
        researched_sessions: list[ResearchedSession],
    ) -> ValidationResult:
        """Validate the complete roadmap and identify issues."""
        # Build session summaries for validation
        session_summaries = []
        for s in researched_sessions:
            summary = f"""Session {s.order}: {s.title}
Type: {s.session_type.value}
Key Concepts: {", ".join(s.key_concepts[:5])}
Content Preview: {s.content[:500]}..."""
            session_summaries.append(summary)

        sessions_text = "\n\n---\n\n".join(session_summaries)

        prompt = f"""Validate this learning roadmap for quality issues:

Learning Path Summary: {outline.learning_path_summary}
Total Sessions: {len(researched_sessions)}
Estimated Hours: {outline.total_estimated_hours}

Sessions:
{sessions_text}

Check for overlaps, gaps, ordering issues, coherence problems, and depth issues.
Be constructive - identify real issues but acknowledge when quality is good.

Output JSON:
{{
  "is_valid": true,
  "issues": [
    {{
      "issue_type": "overlap|gap|ordering|coherence|depth",
      "severity": "low|medium|high",
      "description": "Clear description of the issue",
      "affected_session_indices": [0, 2],
      "suggested_fix": "Specific suggestion to fix"
    }}
  ],
  "overall_score": 85.0,
  "summary": "Brief overall assessment"
}}"""

        response = await self.generate_structured(
            prompt=prompt,
            response_model=ValidatorResponse,
        )

        # Convert to our state models
        issues = []
        for issue in response.issues:
            try:
                issue_type = ValidationIssueType(issue.issue_type.lower())
            except ValueError:
                issue_type = ValidationIssueType.COHERENCE

            severity = issue.severity.lower()
            if severity not in ("low", "medium", "high"):
                severity = "medium"

            # Map indices to session IDs
            affected_ids = [
                researched_sessions[idx].outline_id
                for idx in issue.affected_session_indices
                if idx < len(researched_sessions)
            ]

            issues.append(
                ValidationIssue(
                    id=f"issue_{uuid.uuid4().hex[:8]}",
                    issue_type=issue_type,
                    severity=severity,  # type: ignore[arg-type]
                    description=issue.description,
                    affected_session_ids=affected_ids,
                    suggested_fix=issue.suggested_fix,
                )
            )

        # Only consider valid if no high-severity issues
        has_high_severity = any(i.severity == "high" for i in issues)

        return ValidationResult(
            is_valid=not has_high_severity,
            issues=issues,
            overall_score=response.overall_score,
            summary=response.summary,
        )
