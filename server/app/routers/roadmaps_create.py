"""Routes for multi-agent roadmap creation with SSE streaming."""

import json

import structlog
from fastapi import APIRouter, Depends, HTTPException, status
from pydantic import BaseModel, Field
from sse_starlette.sse import EventSourceResponse

from app.agents.orchestrator import PipelineOrchestrator
from app.agents.state import InterviewAnswer
from app.middleware.auth import get_current_user
from app.models.user import User
from app.services.ai_service import is_gemini_configured

logger = structlog.get_logger()

router = APIRouter(prefix="/roadmaps/create", tags=["roadmap-creation"])

# In-memory storage for active pipelines
# Note: For production, use Redis or similar
_active_pipelines: dict[str, PipelineOrchestrator] = {}


def get_gemini_client():
    """Get the initialized Gemini client."""
    # Import here to avoid circular import
    from app.services.ai_service import _client

    if _client is None:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="AI service not configured",
        )
    return _client


class ExampleOptionResponse(BaseModel):
    """Schema for example option in interview question."""

    label: str
    text: str


class InterviewQuestionResponse(BaseModel):
    """Schema for interview question in response."""

    id: str
    question: str
    purpose: str
    example_options: list[ExampleOptionResponse]
    allows_freeform: bool


class StartCreationRequest(BaseModel):
    """Request schema for starting roadmap creation."""

    topic: str  # What the user wants to learn


class StartCreationResponse(BaseModel):
    """Response schema for start creation endpoint."""

    pipeline_id: str
    questions: list[InterviewQuestionResponse]


class InterviewAnswerRequest(BaseModel):
    """Schema for a single interview answer."""

    question_id: str
    answer: str


class SubmitInterviewRequest(BaseModel):
    """Request schema for submitting interview answers."""

    pipeline_id: str
    answers: list[InterviewAnswerRequest]


class ReviewDecisionRequest(BaseModel):
    """Request schema for review decision after validation."""

    pipeline_id: str
    accept_as_is: bool = False
    issues_to_fix: list[str] = Field(default_factory=list)
    confirmed_title: str | None = None  # User-confirmed title for the roadmap


@router.post("/start", response_model=StartCreationResponse)
async def start_creation(
    request: StartCreationRequest,
    current_user: User = Depends(get_current_user),
) -> StartCreationResponse:
    """Start the roadmap creation pipeline.

    Creates a new pipeline and returns interview questions.
    """
    # Check AI service
    if not is_gemini_configured():
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="AI service not configured",
        )

    client = get_gemini_client()

    # Create pipeline with topic
    pipeline = PipelineOrchestrator(client=client, user_id=current_user.id)
    await pipeline.initialize(
        topic=request.topic,
    )

    # Generate interview questions
    questions = await pipeline.generate_interview_questions(
        topic=request.topic,
        max_questions=5,
    )

    # Store pipeline for later use
    _active_pipelines[pipeline.pipeline_id] = pipeline

    logger.info(
        "Roadmap creation started",
        pipeline_id=pipeline.pipeline_id,
        user_id=str(current_user.id),
        questions=len(questions),
    )

    return StartCreationResponse(
        pipeline_id=pipeline.pipeline_id,
        questions=[
            InterviewQuestionResponse(
                id=q.id,
                question=q.question,
                purpose=q.purpose,
                example_options=[
                    ExampleOptionResponse(label=opt.label, text=opt.text)
                    for opt in q.example_options
                ],
                allows_freeform=q.allows_freeform,
            )
            for q in questions
        ],
    )


@router.post("/interview")
async def submit_interview(
    request: SubmitInterviewRequest,
    current_user: User = Depends(get_current_user),
):
    """Submit interview answers and start the pipeline.

    Returns an SSE stream with progress updates.
    """
    pipeline = _active_pipelines.get(request.pipeline_id)
    if pipeline is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Pipeline not found. Please start creation again.",
        )

    # Verify ownership
    if str(pipeline.user_id) != str(current_user.id):
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Pipeline not found",
        )

    # Store answers
    answers = [InterviewAnswer(question_id=a.question_id, answer=a.answer) for a in request.answers]
    pipeline.add_interview_answers(answers)

    logger.info(
        "Interview answers submitted",
        pipeline_id=request.pipeline_id,
        answers=len(answers),
    )

    async def event_generator():
        try:
            async for event in pipeline.run_pipeline():
                yield {
                    "event": event.event,
                    "data": json.dumps(event.data),
                }
        except Exception as e:
            logger.exception("Pipeline error", error=str(e))
            yield {
                "event": "error",
                "data": f'{{"message": "{str(e)}"}}',
            }
        finally:
            # Clean up if complete or error
            if pipeline.state and pipeline.state.stage.value in ("complete", "error"):
                _active_pipelines.pop(request.pipeline_id, None)

    return EventSourceResponse(event_generator())


@router.post("/review")
async def submit_review(
    request: ReviewDecisionRequest,
    current_user: User = Depends(get_current_user),
):
    """Submit review decision after validation.

    Returns an SSE stream with final progress updates.
    """
    pipeline = _active_pipelines.get(request.pipeline_id)
    if pipeline is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Pipeline not found. Please start creation again.",
        )

    # Verify ownership
    if str(pipeline.user_id) != str(current_user.id):
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Pipeline not found",
        )

    logger.info(
        "Review decision submitted",
        pipeline_id=request.pipeline_id,
        accept_as_is=request.accept_as_is,
        issues_to_fix=len(request.issues_to_fix),
        confirmed_title=request.confirmed_title,
    )

    async def event_generator():
        try:
            async for event in pipeline.proceed_after_review(
                accept_as_is=request.accept_as_is,
                issues_to_fix=request.issues_to_fix,
                confirmed_title=request.confirmed_title,
            ):
                yield {
                    "event": event.event,
                    "data": json.dumps(event.data),
                }
        except Exception as e:
            logger.exception("Review processing error", error=str(e))
            yield {
                "event": "error",
                "data": f'{{"message": "{str(e)}"}}',
            }
        finally:
            # Clean up after completion
            _active_pipelines.pop(request.pipeline_id, None)

    return EventSourceResponse(event_generator())


@router.delete("/{pipeline_id}")
async def cancel_creation(
    pipeline_id: str,
    current_user: User = Depends(get_current_user),
) -> dict:
    """Cancel an in-progress pipeline."""
    pipeline = _active_pipelines.get(pipeline_id)
    if pipeline is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Pipeline not found",
        )

    # Verify ownership
    if str(pipeline.user_id) != str(current_user.id):
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Pipeline not found",
        )

    # Update trace if exists
    if pipeline.trace:
        pipeline.trace.final_status = "abandoned"
        await pipeline.trace.save()

    _active_pipelines.pop(pipeline_id, None)

    logger.info(
        "Pipeline cancelled",
        pipeline_id=pipeline_id,
        user_id=str(current_user.id),
    )

    return {"status": "cancelled"}
