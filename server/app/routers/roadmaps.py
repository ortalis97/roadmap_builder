"""Roadmap routes."""

from datetime import datetime

import structlog
from beanie import PydanticObjectId
from fastapi import APIRouter, Depends, HTTPException, status
from pydantic import BaseModel

from app.middleware.auth import get_current_user
from app.models.roadmap import Roadmap
from app.models.session import Session
from app.models.user import User

logger = structlog.get_logger()

router = APIRouter(prefix="/roadmaps", tags=["roadmaps"])


class SessionSummaryResponse(BaseModel):
    """Schema for session summary in responses."""

    id: str
    title: str
    order: int


class RoadmapListItem(BaseModel):
    """Schema for roadmap in list view."""

    id: str
    title: str
    session_count: int
    language: str = "en"
    created_at: datetime

    class Config:
        from_attributes = True


class RoadmapResponse(BaseModel):
    """Schema for full roadmap response."""

    id: str
    title: str
    summary: str | None
    sessions: list[SessionSummaryResponse]
    language: str = "en"
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True


class SessionResponse(BaseModel):
    """Schema for full session response."""

    id: str
    roadmap_id: str
    order: int
    title: str
    content: str
    status: str
    notes: str
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True


class SessionUpdate(BaseModel):
    """Schema for updating a session."""

    status: str | None = None
    notes: str | None = None


class SessionSummaryWithStatus(BaseModel):
    """Schema for session summary with status."""

    id: str
    title: str
    order: int
    status: str

    class Config:
        from_attributes = True


class RoadmapProgress(BaseModel):
    """Schema for roadmap progress stats."""

    total: int
    done: int
    in_progress: int
    skipped: int
    not_started: int
    percentage: float


@router.get("/", response_model=list[RoadmapListItem])
async def list_roadmaps(
    current_user: User = Depends(get_current_user),
) -> list[RoadmapListItem]:
    """List all roadmaps for the current user.

    Returns a simplified view with session counts.
    """
    roadmaps = await Roadmap.find(Roadmap.user_id == current_user.id).to_list()

    return [
        RoadmapListItem(
            id=str(roadmap.id),
            title=roadmap.title,
            session_count=len(roadmap.sessions),
            language=roadmap.language,
            created_at=roadmap.created_at,
        )
        for roadmap in roadmaps
    ]


@router.get("/{roadmap_id}", response_model=RoadmapResponse)
async def get_roadmap(
    roadmap_id: str,
    current_user: User = Depends(get_current_user),
) -> RoadmapResponse:
    """Get a roadmap by ID.

    Only returns roadmaps owned by the current user.
    """
    try:
        object_id = PydanticObjectId(roadmap_id)
    except Exception:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Invalid roadmap ID format",
        )

    roadmap = await Roadmap.get(object_id)

    if roadmap is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Roadmap not found",
        )

    # Verify ownership
    if roadmap.user_id != current_user.id:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Roadmap not found",
        )

    return RoadmapResponse(
        id=str(roadmap.id),
        title=roadmap.title,
        summary=roadmap.summary,
        sessions=[
            SessionSummaryResponse(
                id=str(session.id),
                title=session.title,
                order=session.order,
            )
            for session in roadmap.sessions
        ],
        language=roadmap.language,
        created_at=roadmap.created_at,
        updated_at=roadmap.updated_at,
    )


@router.delete("/{roadmap_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_roadmap(
    roadmap_id: str,
    current_user: User = Depends(get_current_user),
) -> None:
    """Delete a roadmap by ID.

    Only deletes roadmaps owned by the current user.
    Note: This does not delete associated sessions (handled separately).
    """
    try:
        object_id = PydanticObjectId(roadmap_id)
    except Exception:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Invalid roadmap ID format",
        )

    roadmap = await Roadmap.get(object_id)

    if roadmap is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Roadmap not found",
        )

    # Verify ownership
    if roadmap.user_id != current_user.id:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Roadmap not found",
        )

    await roadmap.delete()


@router.get("/{roadmap_id}/sessions", response_model=list[SessionSummaryWithStatus])
async def list_sessions(
    roadmap_id: str,
    current_user: User = Depends(get_current_user),
) -> list[SessionSummaryWithStatus]:
    """List all sessions for a roadmap with status."""
    try:
        object_id = PydanticObjectId(roadmap_id)
    except Exception:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Invalid roadmap ID format",
        )

    roadmap = await Roadmap.get(object_id)
    if roadmap is None or roadmap.user_id != current_user.id:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Roadmap not found",
        )

    sessions = await Session.find(Session.roadmap_id == object_id).sort("+order").to_list()

    return [
        SessionSummaryWithStatus(
            id=str(session.id),
            title=session.title,
            order=session.order,
            status=session.status,
        )
        for session in sessions
    ]


@router.get("/{roadmap_id}/sessions/{session_id}", response_model=SessionResponse)
async def get_session(
    roadmap_id: str,
    session_id: str,
    current_user: User = Depends(get_current_user),
) -> SessionResponse:
    """Get a session by ID."""
    try:
        roadmap_object_id = PydanticObjectId(roadmap_id)
        session_object_id = PydanticObjectId(session_id)
    except Exception:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Invalid ID format",
        )

    roadmap = await Roadmap.get(roadmap_object_id)
    if roadmap is None or roadmap.user_id != current_user.id:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Roadmap not found",
        )

    session = await Session.get(session_object_id)
    if session is None or session.roadmap_id != roadmap_object_id:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Session not found",
        )

    return SessionResponse(
        id=str(session.id),
        roadmap_id=str(session.roadmap_id),
        order=session.order,
        title=session.title,
        content=session.content,
        status=session.status,
        notes=session.notes,
        created_at=session.created_at,
        updated_at=session.updated_at,
    )


@router.patch("/{roadmap_id}/sessions/{session_id}", response_model=SessionResponse)
async def update_session(
    roadmap_id: str,
    session_id: str,
    update_data: SessionUpdate,
    current_user: User = Depends(get_current_user),
) -> SessionResponse:
    """Update a session's status or notes."""
    try:
        roadmap_object_id = PydanticObjectId(roadmap_id)
        session_object_id = PydanticObjectId(session_id)
    except Exception:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Invalid ID format",
        )

    roadmap = await Roadmap.get(roadmap_object_id)
    if roadmap is None or roadmap.user_id != current_user.id:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Roadmap not found",
        )

    session = await Session.get(session_object_id)
    if session is None or session.roadmap_id != roadmap_object_id:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Session not found",
        )

    valid_statuses = {"not_started", "in_progress", "done", "skipped"}
    if update_data.status is not None and update_data.status not in valid_statuses:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Invalid status. Must be one of: {', '.join(valid_statuses)}",
        )

    if update_data.status is not None:
        session.status = update_data.status
    if update_data.notes is not None:
        session.notes = update_data.notes

    await session.update_timestamp()

    logger.info(
        "Session updated",
        session_id=session_id,
        roadmap_id=roadmap_id,
        status=session.status,
    )

    return SessionResponse(
        id=str(session.id),
        roadmap_id=str(session.roadmap_id),
        order=session.order,
        title=session.title,
        content=session.content,
        status=session.status,
        notes=session.notes,
        created_at=session.created_at,
        updated_at=session.updated_at,
    )


@router.get("/{roadmap_id}/progress", response_model=RoadmapProgress)
async def get_roadmap_progress(
    roadmap_id: str,
    current_user: User = Depends(get_current_user),
) -> RoadmapProgress:
    """Get progress statistics for a roadmap."""
    try:
        object_id = PydanticObjectId(roadmap_id)
    except Exception:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Invalid roadmap ID format",
        )

    roadmap = await Roadmap.get(object_id)
    if roadmap is None or roadmap.user_id != current_user.id:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Roadmap not found",
        )

    sessions = await Session.find(Session.roadmap_id == object_id).to_list()

    counts = {"not_started": 0, "in_progress": 0, "done": 0, "skipped": 0}
    for session in sessions:
        counts[session.status] = counts.get(session.status, 0) + 1

    total = len(sessions)
    percentage = (counts["done"] / total * 100) if total > 0 else 0.0

    return RoadmapProgress(
        total=total,
        done=counts["done"],
        in_progress=counts["in_progress"],
        skipped=counts["skipped"],
        not_started=counts["not_started"],
        percentage=round(percentage, 1),
    )
