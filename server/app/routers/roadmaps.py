"""Roadmap routes."""

from datetime import datetime

from beanie import PydanticObjectId
from fastapi import APIRouter, Depends, HTTPException, status
from pydantic import BaseModel

from app.middleware.auth import get_current_user
from app.models.draft import Draft
from app.models.roadmap import Roadmap
from app.models.user import User

router = APIRouter(prefix="/roadmaps", tags=["roadmaps"])


class RoadmapCreate(BaseModel):
    """Schema for creating a roadmap."""

    draft_id: str
    title: str


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
    created_at: datetime

    class Config:
        from_attributes = True


class RoadmapResponse(BaseModel):
    """Schema for full roadmap response."""

    id: str
    draft_id: str
    title: str
    summary: str | None
    sessions: list[SessionSummaryResponse]
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True


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
            created_at=roadmap.created_at,
        )
        for roadmap in roadmaps
    ]


@router.post("/", response_model=RoadmapResponse, status_code=status.HTTP_201_CREATED)
async def create_roadmap(
    roadmap_data: RoadmapCreate,
    current_user: User = Depends(get_current_user),
) -> RoadmapResponse:
    """Create a new roadmap from a draft.

    The draft must exist and belong to the current user.
    """
    # Validate draft_id format
    try:
        draft_object_id = PydanticObjectId(roadmap_data.draft_id)
    except Exception:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Invalid draft ID format",
        )

    # Verify draft exists and belongs to user
    draft = await Draft.get(draft_object_id)
    if draft is None or draft.user_id != current_user.id:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Draft not found",
        )

    roadmap = Roadmap(
        user_id=current_user.id,
        draft_id=draft_object_id,
        title=roadmap_data.title,
        sessions=[],
    )
    await roadmap.insert()

    return RoadmapResponse(
        id=str(roadmap.id),
        draft_id=str(roadmap.draft_id),
        title=roadmap.title,
        summary=roadmap.summary,
        sessions=[],
        created_at=roadmap.created_at,
        updated_at=roadmap.updated_at,
    )


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
        draft_id=str(roadmap.draft_id),
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
