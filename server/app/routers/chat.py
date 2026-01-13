"""Chat routes for AI assistant."""

from datetime import datetime
from uuid import uuid4

import structlog
from beanie import PydanticObjectId
from fastapi import APIRouter, Depends, HTTPException, status
from pydantic import BaseModel

from app.middleware.auth import get_current_user
from app.models.chat_history import ChatHistory
from app.models.roadmap import Roadmap
from app.models.session import Session
from app.models.user import User
from app.services.ai_service import generate_chat_response, is_gemini_configured

logger = structlog.get_logger()

router = APIRouter(prefix="/chat", tags=["chat"])


# Request/Response schemas
class ChatMessageRequest(BaseModel):
    """Request schema for sending a chat message."""

    session_id: str
    roadmap_id: str
    message: str
    conversation_id: str | None = None  # None = start new conversation


class ChatMessageResponse(BaseModel):
    """Response schema for a chat message."""

    role: str
    content: str
    timestamp: datetime


class ChatResponse(BaseModel):
    """Response schema for chat endpoint."""

    conversation_id: str
    user_message: ChatMessageResponse
    assistant_message: ChatMessageResponse


class ChatHistoryResponse(BaseModel):
    """Response schema for chat history."""

    conversation_id: str
    messages: list[ChatMessageResponse]
    created_at: datetime
    updated_at: datetime


@router.post("/", response_model=ChatResponse)
async def send_chat_message(
    chat_data: ChatMessageRequest,
    current_user: User = Depends(get_current_user),
) -> ChatResponse:
    """Send a message to the AI assistant and get a response.

    Creates a new conversation if conversation_id is not provided.
    Logs user prompt and AI response to database.
    """
    # Validate IDs
    try:
        roadmap_object_id = PydanticObjectId(chat_data.roadmap_id)
        session_object_id = PydanticObjectId(chat_data.session_id)
    except Exception:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Invalid roadmap or session ID format",
        )

    # Verify roadmap exists and belongs to user
    roadmap = await Roadmap.get(roadmap_object_id)
    if roadmap is None or roadmap.user_id != current_user.id:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Roadmap not found",
        )

    # Verify session exists and belongs to roadmap
    session = await Session.get(session_object_id)
    if session is None or session.roadmap_id != roadmap_object_id:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Session not found",
        )

    # Check AI service availability
    if not is_gemini_configured():
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="AI service not configured",
        )

    # Get or create chat history
    if chat_data.conversation_id:
        chat_history = await ChatHistory.find_one(
            ChatHistory.conversation_id == chat_data.conversation_id,
            ChatHistory.session_id == session_object_id,
            ChatHistory.user_id == current_user.id,
        )
        if chat_history is None:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Conversation not found",
            )
    else:
        # Create new conversation
        conversation_id = str(uuid4())
        chat_history = ChatHistory(
            conversation_id=conversation_id,
            session_id=session_object_id,
            roadmap_id=roadmap_object_id,
            user_id=current_user.id,
            messages=[],
        )
        await chat_history.insert()
        logger.info(
            "New chat conversation started",
            conversation_id=conversation_id,
            session_id=str(session_object_id),
            user_id=str(current_user.id),
        )

    # Build conversation history for AI
    conversation_history = [
        {"role": msg.role, "content": msg.content}
        for msg in chat_history.messages
        if msg.role in ("user", "assistant")
    ]

    # Get all session titles for context
    all_sessions = (
        await Session.find(Session.roadmap_id == roadmap_object_id).sort("+order").to_list()
    )
    all_session_titles = [s.title for s in all_sessions]

    try:
        # Generate AI response
        ai_response = await generate_chat_response(
            roadmap_title=roadmap.title,
            roadmap_summary=roadmap.summary,
            all_session_titles=all_session_titles,
            current_session_title=session.title,
            current_session_content=session.content,
            user_notes=session.notes,
            conversation_history=conversation_history,
            user_message=chat_data.message,
        )
    except Exception as e:
        logger.error("AI chat generation failed", error=str(e))
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to generate AI response. Please try again.",
        )

    # Log user message to database
    user_msg = await chat_history.add_message("user", chat_data.message)

    # Log AI response to database
    assistant_msg = await chat_history.add_message("assistant", ai_response)

    logger.info(
        "Chat message processed",
        conversation_id=chat_history.conversation_id,
        session_id=str(session_object_id),
        user_message_length=len(chat_data.message),
        response_length=len(ai_response),
    )

    return ChatResponse(
        conversation_id=chat_history.conversation_id,
        user_message=ChatMessageResponse(
            role=user_msg.role,
            content=user_msg.content,
            timestamp=user_msg.timestamp,
        ),
        assistant_message=ChatMessageResponse(
            role=assistant_msg.role,
            content=assistant_msg.content,
            timestamp=assistant_msg.timestamp,
        ),
    )


@router.get(
    "/roadmaps/{roadmap_id}/sessions/{session_id}",
    response_model=ChatHistoryResponse | None,
)
async def get_chat_history(
    roadmap_id: str,
    session_id: str,
    current_user: User = Depends(get_current_user),
) -> ChatHistoryResponse | None:
    """Get the current chat history for a session.

    Returns the most recent conversation, or None if no conversation exists.
    """
    try:
        roadmap_object_id = PydanticObjectId(roadmap_id)
        session_object_id = PydanticObjectId(session_id)
    except Exception:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Invalid ID format",
        )

    # Verify ownership
    roadmap = await Roadmap.get(roadmap_object_id)
    if roadmap is None or roadmap.user_id != current_user.id:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Roadmap not found",
        )

    # Get most recent conversation for this session
    chat_history = await ChatHistory.find_one(
        ChatHistory.session_id == session_object_id,
        ChatHistory.user_id == current_user.id,
        sort=[("updated_at", -1)],  # Most recent first
    )

    if chat_history is None:
        return None

    return ChatHistoryResponse(
        conversation_id=chat_history.conversation_id,
        messages=[
            ChatMessageResponse(
                role=msg.role,
                content=msg.content,
                timestamp=msg.timestamp,
            )
            for msg in chat_history.messages
        ],
        created_at=chat_history.created_at,
        updated_at=chat_history.updated_at,
    )


@router.delete(
    "/roadmaps/{roadmap_id}/sessions/{session_id}",
    status_code=status.HTTP_204_NO_CONTENT,
)
async def clear_chat_history(
    roadmap_id: str,
    session_id: str,
    current_user: User = Depends(get_current_user),
) -> None:
    """Clear chat history for a session (enables starting a new conversation).

    Deletes all conversations for the session.
    """
    try:
        roadmap_object_id = PydanticObjectId(roadmap_id)
        session_object_id = PydanticObjectId(session_id)
    except Exception:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Invalid ID format",
        )

    # Verify ownership
    roadmap = await Roadmap.get(roadmap_object_id)
    if roadmap is None or roadmap.user_id != current_user.id:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Roadmap not found",
        )

    # Delete all conversations for this session
    result = await ChatHistory.find(
        ChatHistory.session_id == session_object_id,
        ChatHistory.user_id == current_user.id,
    ).delete()

    logger.info(
        "Chat history cleared",
        session_id=session_id,
        user_id=str(current_user.id),
        deleted_count=result.deleted_count if result else 0,
    )
