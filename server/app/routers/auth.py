"""Authentication routes."""

from fastapi import APIRouter, Depends
from pydantic import BaseModel

from app.middleware.auth import get_current_user
from app.models.user import User

router = APIRouter(prefix="/auth", tags=["auth"])


class UserResponse(BaseModel):
    """User response schema."""

    id: str
    firebase_uid: str
    email: str
    name: str
    picture: str | None

    class Config:
        from_attributes = True


@router.get("/me", response_model=UserResponse)
async def get_me(current_user: User = Depends(get_current_user)) -> UserResponse:
    """Get the current authenticated user.

    Returns the user profile for the authenticated user.
    Creates a new user on first login.
    """
    return UserResponse(
        id=str(current_user.id),
        firebase_uid=current_user.firebase_uid,
        email=current_user.email,
        name=current_user.name,
        picture=current_user.picture,
    )
