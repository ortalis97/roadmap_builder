"""Draft routes."""

from datetime import datetime

from beanie import PydanticObjectId
from fastapi import APIRouter, Depends, HTTPException, status
from pydantic import BaseModel

from app.middleware.auth import get_current_user
from app.models.draft import Draft
from app.models.user import User

router = APIRouter(prefix="/drafts", tags=["drafts"])


class DraftCreate(BaseModel):
    """Schema for creating a draft."""

    raw_text: str


class DraftResponse(BaseModel):
    """Schema for draft response."""

    id: str
    user_id: str
    raw_text: str
    created_at: datetime

    class Config:
        from_attributes = True


@router.post("/", response_model=DraftResponse, status_code=status.HTTP_201_CREATED)
async def create_draft(
    draft_data: DraftCreate,
    current_user: User = Depends(get_current_user),
) -> DraftResponse:
    """Create a new draft from raw text.

    Stores the user's pasted learning plan for later processing.
    """
    draft = Draft(
        user_id=current_user.id,
        raw_text=draft_data.raw_text,
    )
    await draft.insert()

    return DraftResponse(
        id=str(draft.id),
        user_id=str(draft.user_id),
        raw_text=draft.raw_text,
        created_at=draft.created_at,
    )


@router.get("/{draft_id}", response_model=DraftResponse)
async def get_draft(
    draft_id: str,
    current_user: User = Depends(get_current_user),
) -> DraftResponse:
    """Get a draft by ID.

    Only returns drafts owned by the current user.
    """
    try:
        object_id = PydanticObjectId(draft_id)
    except Exception:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Invalid draft ID format",
        )

    draft = await Draft.get(object_id)

    if draft is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Draft not found",
        )

    # Verify ownership
    if draft.user_id != current_user.id:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Draft not found",
        )

    return DraftResponse(
        id=str(draft.id),
        user_id=str(draft.user_id),
        raw_text=draft.raw_text,
        created_at=draft.created_at,
    )
