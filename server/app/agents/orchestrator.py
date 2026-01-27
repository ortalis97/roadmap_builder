"""Pipeline orchestrator for multi-agent roadmap creation."""

import asyncio
import uuid
from collections.abc import AsyncGenerator
from typing import Any

import structlog
from beanie import PydanticObjectId
from google import genai

from app.agents.architect import ArchitectAgent
from app.agents.interviewer import InterviewerAgent
from app.agents.researcher import get_researcher_for_type
from app.agents.state import (
    InterviewAnswer,
    InterviewContext,
    InterviewQuestion,
    PipelineStage,
    PipelineState,
    ResearchedSession,
    SessionOutline,
    ValidationResult,
)
from app.agents.validator import ValidatorAgent
from app.agents.youtube import YouTubeAgent
from app.model_config import MAX_CONCURRENT_API_CALLS
from app.models.agent_trace import AgentSpan, AgentTrace
from app.models.roadmap import Roadmap, SessionSummary
from app.models.session import Session
from app.services.sse_service import SSEEvent
from app.utils.language import detect_language

logger = structlog.get_logger()

# Semaphore to limit concurrent Gemini API calls
_api_semaphore: asyncio.Semaphore | None = None


def get_api_semaphore() -> asyncio.Semaphore:
    """Get or create the API concurrency semaphore.

    Created lazily to ensure it's created in the right event loop.
    """
    global _api_semaphore
    if _api_semaphore is None:
        _api_semaphore = asyncio.Semaphore(MAX_CONCURRENT_API_CALLS)
    return _api_semaphore


class PipelineOrchestrator:
    """Orchestrates the multi-agent roadmap creation pipeline."""

    def __init__(self, client: genai.Client, user_id: PydanticObjectId):
        self.client = client
        self.user_id = user_id
        self.pipeline_id = f"pipeline_{uuid.uuid4().hex[:12]}"
        self.state: PipelineState | None = None
        self.trace: AgentTrace | None = None
        self.logger = structlog.get_logger().bind(pipeline_id=self.pipeline_id)

    async def initialize(
        self,
        topic: str,
    ) -> None:
        """Initialize the pipeline state and trace."""
        # Detect language from topic
        detected_language = detect_language(topic)

        self.state = PipelineState(
            pipeline_id=self.pipeline_id,
            user_id=str(self.user_id),
            topic=topic,
            language=detected_language,
            stage=PipelineStage.INITIALIZED,
        )

        self.trace = AgentTrace(
            pipeline_id=self.pipeline_id,
            user_id=str(self.user_id),
            initial_topic=topic,
            initial_title=topic[:100],  # Use topic as initial title for trace
        )
        await self.trace.insert()

        self.logger.info(
            "Pipeline initialized",
            topic=topic[:100],
            language=detected_language,
        )

    async def generate_interview_questions(
        self,
        topic: str,
        max_questions: int = 5,
    ) -> list[InterviewQuestion]:
        """Generate interview questions using the interviewer agent."""
        if not self.state or not self.trace:
            raise ValueError("Pipeline not initialized")

        self.state.stage = PipelineStage.INTERVIEWING

        interviewer = InterviewerAgent(self.client)
        span = interviewer.create_span("generate_questions")

        try:
            questions = await interviewer.generate_questions(
                topic=topic,
                raw_input=topic,  # Use topic as raw_input
                title=topic[:50],  # Use topic as title
                max_questions=max_questions,
                language=self.state.language,
            )
            self.state.interview_questions = questions

            interviewer.complete_span(
                span,
                status="success",
                output_summary=f"Generated {len(questions)} questions",
            )
            self.trace.spans.append(span)
            await self.trace.save()

            self.logger.info("Interview questions generated", count=len(questions))
            return questions

        except Exception as e:
            interviewer.complete_span(span, error=e)
            self.trace.spans.append(span)
            await self.trace.save()
            raise

    def add_interview_answers(self, answers: list[InterviewAnswer]) -> None:
        """Store interview answers in state."""
        if not self.state:
            raise ValueError("Pipeline not initialized")

        self.state.interview_answers = answers
        self.logger.info("Interview answers stored", count=len(answers))

    async def run_pipeline(self) -> AsyncGenerator[SSEEvent, None]:
        """Run the full pipeline, yielding SSE events for progress updates."""
        if not self.state or not self.trace:
            raise ValueError("Pipeline not initialized")

        try:
            # Build interview context from Q&A
            qa_pairs = []
            for q, a in zip(
                self.state.interview_questions,
                self.state.interview_answers,
                strict=False,
            ):
                qa_pairs.append((q.question, a.answer))

            interview_context = InterviewContext(
                topic=self.state.topic,
            )
            interview_context.questions = self.state.interview_questions
            interview_context.answers = self.state.interview_answers

            # Run architect
            yield SSEEvent(
                event="stage_update",
                data={"stage": "architecting", "message": "Creating session outline..."},
            )
            suggested_title, outline = await self._run_architect(interview_context)
            self.state.suggested_title = suggested_title

            # Emit title suggestion for user confirmation
            yield SSEEvent(
                event="title_suggestion",
                data={"suggested_title": suggested_title},
            )

            # Run researchers in parallel
            yield SSEEvent(
                event="stage_update",
                data={
                    "stage": "researching",
                    "message": f"Researching {len(outline.sessions)} sessions...",
                },
            )
            researched_sessions = await self._run_researchers_parallel(outline, interview_context)

            # Yield progress for each session
            for i, session in enumerate(researched_sessions, 1):
                yield SSEEvent(
                    event="session_progress",
                    data={
                        "current": i,
                        "total": len(researched_sessions),
                        "session_title": session.title,
                    },
                )

            # Run YouTube agent to find videos
            yield SSEEvent(
                event="stage_update",
                data={
                    "stage": "finding_videos",
                    "message": "Finding educational videos...",
                },
            )
            await self._run_youtube_agent(researched_sessions)

            # Run validator
            yield SSEEvent(
                event="stage_update",
                data={"stage": "validating", "message": "Validating roadmap quality..."},
            )
            validation_result = await self._run_validator(outline, researched_sessions)

            # Check if user review needed
            if not validation_result.is_valid:
                self.state.stage = PipelineStage.USER_REVIEW
                self.state.validation_result = validation_result
                yield SSEEvent(
                    event="validation_result",
                    data={
                        "is_valid": validation_result.is_valid,
                        "issues": [
                            {
                                "id": issue.id,
                                "issue_type": issue.issue_type.value,
                                "severity": issue.severity,
                                "description": issue.description,
                                "suggested_fix": issue.suggested_fix,
                            }
                            for issue in validation_result.issues
                        ],
                        "score": validation_result.overall_score,
                        "summary": validation_result.summary,
                    },
                )
                return  # Wait for user review decision

            # No issues - proceed to title confirmation
            self.state.stage = PipelineStage.USER_REVIEW
            yield SSEEvent(
                event="validation_result",
                data={
                    "is_valid": True,
                    "issues": [],
                    "score": validation_result.overall_score,
                    "summary": validation_result.summary,
                },
            )
            # Wait for user to confirm title before saving

        except Exception as e:
            self.state.stage = PipelineStage.ERROR
            self.state.error_message = str(e)
            self.trace.final_status = "error"
            await self.trace.save()

            self.logger.exception("Pipeline failed", error=str(e))
            yield SSEEvent(
                event="error",
                data={"message": str(e)},
            )

    async def _run_architect(
        self,
        interview_context: InterviewContext,
    ) -> tuple[str, SessionOutline]:
        """Run the architect agent to create session outline.

        Returns:
            A tuple of (suggested_title, session_outline)
        """
        architect = ArchitectAgent(self.client)
        span = architect.create_span("create_outline")

        try:
            self.state.stage = PipelineStage.ARCHITECTING
            suggested_title, outline = await architect.create_outline(
                interview_context,
                language=self.state.language,
            )
            self.state.session_outline = outline

            architect.complete_span(
                span,
                status="success",
                output_summary=f"Created {len(outline.sessions)} sessions",
            )
            self.trace.spans.append(span)
            await self.trace.save()

            self.logger.info(
                "Outline created",
                sessions=len(outline.sessions),
                hours=outline.total_estimated_hours,
                title=suggested_title,
            )
            return suggested_title, outline

        except Exception as e:
            architect.complete_span(span, error=e)
            self.trace.spans.append(span)
            await self.trace.save()
            raise

    async def _run_researchers_parallel(
        self,
        outline: SessionOutline,
        interview_context: InterviewContext,
    ) -> list[ResearchedSession]:
        """Run researchers in parallel for all sessions with concurrency limiting."""
        self.state.stage = PipelineStage.RESEARCHING
        researched_sessions: list[ResearchedSession] = []
        spans: list[AgentSpan] = []

        self.logger.info(
            "Starting parallel research",
            total_sessions=len(outline.sessions),
            max_concurrent=MAX_CONCURRENT_API_CALLS,
        )

        async def research_session(
            outline_item: Any,
            all_outlines: list[Any],
        ) -> tuple[ResearchedSession, AgentSpan]:
            researcher = get_researcher_for_type(outline_item.session_type, self.client)
            span = researcher.create_span(f"research_{outline_item.session_type.value}")

            semaphore = get_api_semaphore()

            try:
                # Log if we need to wait for semaphore
                if semaphore.locked():
                    self.logger.debug(
                        "Waiting for API slot",
                        session_order=outline_item.order,
                        session_title=outline_item.title[:50],
                    )

                async with semaphore:
                    self.logger.debug(
                        "Acquired API slot, starting research",
                        session_order=outline_item.order,
                        session_title=outline_item.title[:50],
                    )

                    session = await researcher.research_session(
                        outline_item=outline_item,
                        interview_context=interview_context,
                        all_session_outlines=all_outlines,
                        language=self.state.language,
                    )

                researcher.complete_span(
                    span,
                    status="success",
                    output_summary=f"Researched: {session.title}",
                )
                return session, span

            except Exception as e:
                researcher.complete_span(span, error=e)
                raise

        # Run all researchers in parallel with full outline context
        tasks = [
            research_session(outline_item, outline.sessions) for outline_item in outline.sessions
        ]
        results = await asyncio.gather(*tasks, return_exceptions=True)

        for result in results:
            if isinstance(result, Exception):
                self.logger.error(
                    "Research failed",
                    error=str(result),
                    error_type=type(result).__name__,
                )
                raise result
            session, span = result
            researched_sessions.append(session)
            spans.append(span)

        # Sort by order (parallel doesn't guarantee order)
        researched_sessions.sort(key=lambda s: s.order)

        # Add all spans to trace
        self.trace.spans.extend(spans)
        await self.trace.save()

        self.state.researched_sessions = researched_sessions
        self.logger.info("All sessions researched", count=len(researched_sessions))
        return researched_sessions

    async def _run_youtube_agent(
        self,
        researched_sessions: list[ResearchedSession],
    ) -> list[ResearchedSession]:
        """Run the YouTube agent to find videos for all sessions in parallel.

        Videos are added in-place to each ResearchedSession.
        On failure, sessions proceed without videos (graceful degradation).
        """
        youtube_agent = YouTubeAgent(self.client)
        spans: list[AgentSpan] = []

        self.logger.info(
            "Starting parallel video search",
            total_sessions=len(researched_sessions),
            max_concurrent=MAX_CONCURRENT_API_CALLS,
        )

        async def find_videos_for_session(session: ResearchedSession) -> None:
            """Find videos for a single session."""
            span = youtube_agent.create_span(f"find_videos_{session.order}")

            semaphore = get_api_semaphore()

            try:
                # Log if we need to wait for semaphore
                if semaphore.locked():
                    self.logger.debug(
                        "Waiting for API slot (videos)",
                        session_order=session.order,
                        session_title=session.title[:50],
                    )

                async with semaphore:
                    self.logger.debug(
                        "Acquired API slot, starting video search",
                        session_order=session.order,
                        session_title=session.title[:50],
                    )

                    videos = await youtube_agent.find_videos(session, max_videos=3)
                    session.videos = videos

                youtube_agent.complete_span(
                    span,
                    status="success",
                    output_summary=f"Found {len(videos)} videos",
                )

            except Exception as e:
                youtube_agent.complete_span(span, error=e)
                session.videos = []  # Proceed without videos

            spans.append(span)

        # Run all YouTube searches in parallel
        await asyncio.gather(
            *[find_videos_for_session(session) for session in researched_sessions],
            return_exceptions=True,
        )

        self.trace.spans.extend(spans)
        await self.trace.save()

        found_count = sum(len(s.videos) for s in researched_sessions)
        self.logger.info(
            "YouTube agent complete",
            total_videos=found_count,
            sessions_with_videos=sum(1 for s in researched_sessions if s.videos),
        )

        return researched_sessions

    async def _run_validator(
        self,
        outline: SessionOutline,
        researched_sessions: list[ResearchedSession],
    ) -> ValidationResult:
        """Run the validator agent to check roadmap quality."""
        self.state.stage = PipelineStage.VALIDATING
        validator = ValidatorAgent(self.client)
        span = validator.create_span("validate")

        try:
            result = await validator.validate(outline, researched_sessions)
            self.state.validation_result = result

            validator.complete_span(
                span,
                status="success",
                output_summary=(f"Score: {result.overall_score}, Issues: {len(result.issues)}"),
            )
            self.trace.spans.append(span)
            await self.trace.save()

            self.logger.info(
                "Validation complete",
                is_valid=result.is_valid,
                score=result.overall_score,
                issues=len(result.issues),
            )
            return result

        except Exception as e:
            validator.complete_span(span, error=e)
            self.trace.spans.append(span)
            await self.trace.save()
            raise

    async def _save_roadmap(
        self,
        outline: SessionOutline,
        researched_sessions: list[ResearchedSession],
    ) -> Roadmap:
        """Save the roadmap and sessions to the database."""
        self.state.stage = PipelineStage.SAVING

        # Use confirmed title, or fall back to suggested, or fall back to topic
        title = self.state.confirmed_title or self.state.suggested_title or self.state.topic[:100]

        # Create roadmap document
        roadmap = Roadmap(
            user_id=self.user_id,
            title=title,
            summary=outline.learning_path_summary,
            language=self.state.language,
        )
        await roadmap.insert()

        # Update trace with final title
        self.trace.initial_title = title
        await self.trace.save()

        # Create session documents
        session_summaries: list[SessionSummary] = []
        for rs in researched_sessions:
            session = Session(
                roadmap_id=roadmap.id,
                order=rs.order,
                title=rs.title,
                content=rs.content,
                videos=rs.videos,
            )
            await session.insert()

            session_summaries.append(
                SessionSummary(
                    id=session.id,
                    title=session.title,
                    order=session.order,
                )
            )

        # Update roadmap with session summaries
        roadmap.sessions = session_summaries
        await roadmap.save()

        self.state.roadmap_id = str(roadmap.id)
        self.logger.info(
            "Roadmap saved",
            roadmap_id=str(roadmap.id),
            sessions=len(session_summaries),
        )
        return roadmap

    async def proceed_after_review(
        self,
        accept_as_is: bool = False,
        issues_to_fix: list[str] | None = None,
        confirmed_title: str | None = None,
    ) -> AsyncGenerator[SSEEvent, None]:
        """Continue pipeline after user review.

        Args:
            accept_as_is: Whether to accept the roadmap as-is
            issues_to_fix: List of issue IDs to fix (not yet implemented)
            confirmed_title: User-confirmed title for the roadmap
        """
        if not self.state or not self.trace:
            raise ValueError("Pipeline not initialized")

        if self.state.stage != PipelineStage.USER_REVIEW:
            raise ValueError("Pipeline not in user review stage")

        # Store confirmed title if provided
        if confirmed_title:
            self.state.confirmed_title = confirmed_title

        try:
            if accept_as_is or not issues_to_fix:
                # User accepted, proceed to save
                yield SSEEvent(
                    event="stage_update",
                    data={"stage": "saving", "message": "Saving your roadmap..."},
                )

                roadmap = await self._save_roadmap(
                    self.state.session_outline,
                    self.state.researched_sessions,
                )

                self.state.stage = PipelineStage.COMPLETE
                self.trace.final_status = "success"
                await self.trace.save()

                yield SSEEvent(
                    event="complete",
                    data={
                        "roadmap_id": str(roadmap.id),
                        "message": "Roadmap created successfully!",
                    },
                )
            else:
                # Future: handle revision of specific issues
                # For now, just save anyway
                yield SSEEvent(
                    event="stage_update",
                    data={"stage": "saving", "message": "Saving your roadmap..."},
                )

                roadmap = await self._save_roadmap(
                    self.state.session_outline,
                    self.state.researched_sessions,
                )

                self.state.stage = PipelineStage.COMPLETE
                self.trace.final_status = "success"
                await self.trace.save()

                yield SSEEvent(
                    event="complete",
                    data={
                        "roadmap_id": str(roadmap.id),
                        "message": "Roadmap created successfully!",
                    },
                )

        except Exception as e:
            self.state.stage = PipelineStage.ERROR
            self.state.error_message = str(e)
            self.trace.final_status = "error"
            await self.trace.save()

            self.logger.exception("Pipeline failed after review", error=str(e))
            yield SSEEvent(
                event="error",
                data={"message": str(e)},
            )
