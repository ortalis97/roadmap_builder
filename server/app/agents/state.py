"""Pydantic state models for multi-agent roadmap creation pipeline."""

from __future__ import annotations

from datetime import datetime
from enum import Enum
from typing import Literal

from pydantic import BaseModel, Field

# ============= Session Type Enum =============


class SessionType(str, Enum):
    """Types of learning sessions that map to specialized researchers."""

    CONCEPT = "concept"  # Theory, definitions, mental models
    TUTORIAL = "tutorial"  # Step-by-step guided learning
    PRACTICE = "practice"  # Exercises, challenges, drills
    PROJECT = "project"  # Hands-on building projects
    REVIEW = "review"  # Recap, assessment, reflection


# ============= Interview Models =============


class ExampleOption(BaseModel):
    """Example answer option for an interview question."""

    label: str  # e.g., "A", "B", "C"
    text: str  # The example answer text


class InterviewQuestion(BaseModel):
    """A clarifying question from the interviewer agent."""

    id: str  # Unique ID for tracking
    question: str  # The question text
    purpose: str  # Why we're asking (shown to user)
    example_options: list[ExampleOption] = Field(default_factory=list)
    allows_freeform: bool = True  # User can type their own answer


class InterviewAnswer(BaseModel):
    """User's answer to an interview question."""

    question_id: str
    answer: str  # User's response (freeform or selected example)


class InterviewContext(BaseModel):
    """Accumulated context from the interview phase."""

    topic: str  # Main learning topic / what the user wants to learn
    questions: list[InterviewQuestion] = Field(default_factory=list)
    answers: list[InterviewAnswer] = Field(default_factory=list)

    @property
    def qa_pairs(self) -> list[tuple[str, str]]:
        """Return question-answer pairs for context building."""
        answer_map = {a.question_id: a.answer for a in self.answers}
        return [
            (q.question, answer_map.get(q.id, "")) for q in self.questions if q.id in answer_map
        ]


# ============= Architecture Models =============


class SessionOutlineItem(BaseModel):
    """A session outline from the architect agent."""

    id: str  # Unique ID for this session
    title: str  # Session title
    objective: str  # Learning objective
    session_type: SessionType  # Type determines which researcher handles it
    estimated_duration_minutes: int = 60
    prerequisites: list[str] = Field(default_factory=list)  # IDs of prerequisite sessions
    order: int  # Position in the sequence


class SessionOutline(BaseModel):
    """Complete session outline from architect agent."""

    sessions: list[SessionOutlineItem]
    learning_path_summary: str  # Overview of the learning journey
    total_estimated_hours: float


# ============= Research Models =============


class ResearchedSession(BaseModel):
    """A fully researched session with content."""

    outline_id: str  # Reference to SessionOutlineItem.id
    title: str
    session_type: SessionType
    order: int
    content: str  # Full markdown content
    key_concepts: list[str] = Field(default_factory=list)
    resources: list[str] = Field(default_factory=list)  # URLs, book references
    exercises: list[str] = Field(default_factory=list)  # Optional practice items
    videos: list[VideoResource] = Field(default_factory=list)  # YouTube video recommendations
    language: str = "en"  # Language code for video search relevance


class VideoResource(BaseModel):
    """YouTube video resource for a learning session."""

    url: str = Field(description="Full YouTube video URL")
    title: str = Field(description="Video title")
    channel: str = Field(description="YouTube channel name")
    thumbnail_url: str = Field(description="Video thumbnail image URL")
    duration_minutes: int | None = Field(default=None, description="Video duration in minutes")
    description: str | None = Field(default=None, description="Brief description of video content")


# ============= Validation Models =============


class ValidationIssueType(str, Enum):
    """Types of issues the validator can find."""

    OVERLAP = "overlap"  # Content repeated across sessions
    GAP = "gap"  # Missing prerequisite content
    ORDERING = "ordering"  # Sessions in wrong order
    COHERENCE = "coherence"  # Content doesn't flow well
    DEPTH = "depth"  # Too shallow or too deep


class ValidationIssue(BaseModel):
    """A single issue found during validation."""

    id: str  # Unique issue ID
    issue_type: ValidationIssueType
    severity: Literal["low", "medium", "high"]
    description: str  # Human-readable description
    affected_session_ids: list[str]  # Which sessions are affected
    suggested_fix: str  # AI's suggestion for fixing


class ValidationResult(BaseModel):
    """Complete validation result."""

    is_valid: bool  # True if no high-severity issues
    issues: list[ValidationIssue] = Field(default_factory=list)
    overall_score: float  # 0-100 quality score
    summary: str  # Brief assessment


# ============= Pipeline State =============


class PipelineStage(str, Enum):
    """Stages of the creation pipeline."""

    INITIALIZED = "initialized"
    INTERVIEWING = "interviewing"
    ARCHITECTING = "architecting"
    RESEARCHING = "researching"
    VALIDATING = "validating"
    USER_REVIEW = "user_review"
    REVISING = "revising"
    SAVING = "saving"
    COMPLETE = "complete"
    ERROR = "error"


class PipelineState(BaseModel):
    """Full state of the roadmap creation pipeline."""

    # Identity
    pipeline_id: str  # UUID for this pipeline run
    user_id: str  # User's MongoDB ObjectId as string
    topic: str  # What the user wants to learn
    language: str = "en"  # Detected language: "en" or "he"

    # Current stage
    stage: PipelineStage = PipelineStage.INITIALIZED
    stage_started_at: datetime | None = None

    # Interview phase
    interview_questions: list[InterviewQuestion] = Field(default_factory=list)
    interview_answers: list[InterviewAnswer] = Field(default_factory=list)
    interview_context: InterviewContext | None = None

    # Architecture phase
    suggested_title: str | None = None  # AI-generated title
    confirmed_title: str | None = None  # User-confirmed title
    session_outline: SessionOutline | None = None

    # Research phase
    researched_sessions: list[ResearchedSession] = Field(default_factory=list)
    research_progress: int = 0  # Number of sessions researched
    research_total: int = 0  # Total sessions to research

    # Validation phase
    validation_result: ValidationResult | None = None
    user_selected_issues: list[str] = Field(default_factory=list)  # Issue IDs to fix

    # Final output
    roadmap_id: str | None = None  # Created roadmap ID

    # Error tracking
    error_message: str | None = None

    # Timestamps
    created_at: datetime = Field(default_factory=datetime.utcnow)
    updated_at: datetime = Field(default_factory=datetime.utcnow)
