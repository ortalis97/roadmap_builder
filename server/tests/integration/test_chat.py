"""Integration tests for /api/v1/chat endpoints."""

from unittest.mock import AsyncMock, patch

from beanie import PydanticObjectId
from httpx import AsyncClient

from app.models.chat_history import ChatHistory
from app.models.user import User


class TestSendChatMessage:
    """Tests for POST /api/v1/chat endpoint."""

    async def test_send_message_creates_conversation(
        self, client: AsyncClient, test_roadmap_with_sessions, mock_user: User
    ):
        """Sending a message without conversation_id should create new conversation."""
        roadmap, sessions = test_roadmap_with_sessions
        session = sessions[0]

        with (
            patch(
                "app.routers.chat.generate_chat_response",
                new_callable=AsyncMock,
                return_value="This is the AI response.",
            ),
            patch("app.routers.chat.is_gemini_configured", return_value=True),
        ):
            response = await client.post(
                "/api/v1/chat/",
                json={
                    "roadmap_id": str(roadmap.id),
                    "session_id": str(session.id),
                    "message": "What is Python?",
                },
            )

        assert response.status_code == 200
        data = response.json()
        assert "conversation_id" in data
        assert len(data["conversation_id"]) > 0

    async def test_send_message_returns_both_messages(
        self, client: AsyncClient, test_roadmap_with_sessions, mock_user: User
    ):
        """Response should contain both user and assistant messages."""
        roadmap, sessions = test_roadmap_with_sessions
        session = sessions[0]
        user_message = "Explain functions in Python"
        ai_response = "Functions are reusable blocks of code..."

        with (
            patch(
                "app.routers.chat.generate_chat_response",
                new_callable=AsyncMock,
                return_value=ai_response,
            ),
            patch("app.routers.chat.is_gemini_configured", return_value=True),
        ):
            response = await client.post(
                "/api/v1/chat/",
                json={
                    "roadmap_id": str(roadmap.id),
                    "session_id": str(session.id),
                    "message": user_message,
                },
            )

        assert response.status_code == 200
        data = response.json()

        assert data["user_message"]["role"] == "user"
        assert data["user_message"]["content"] == user_message
        assert "timestamp" in data["user_message"]

        assert data["assistant_message"]["role"] == "assistant"
        assert data["assistant_message"]["content"] == ai_response
        assert "timestamp" in data["assistant_message"]

    async def test_send_message_continues_conversation(
        self, client: AsyncClient, test_roadmap_with_sessions, mock_user: User
    ):
        """Sending with existing conversation_id should continue conversation."""
        roadmap, sessions = test_roadmap_with_sessions
        session = sessions[0]

        # First message to create conversation
        with (
            patch(
                "app.routers.chat.generate_chat_response",
                new_callable=AsyncMock,
                return_value="First response",
            ),
            patch("app.routers.chat.is_gemini_configured", return_value=True),
        ):
            first_response = await client.post(
                "/api/v1/chat/",
                json={
                    "roadmap_id": str(roadmap.id),
                    "session_id": str(session.id),
                    "message": "First question",
                },
            )

        conversation_id = first_response.json()["conversation_id"]

        # Second message with same conversation_id
        with (
            patch(
                "app.routers.chat.generate_chat_response",
                new_callable=AsyncMock,
                return_value="Second response",
            ),
            patch("app.routers.chat.is_gemini_configured", return_value=True),
        ):
            second_response = await client.post(
                "/api/v1/chat/",
                json={
                    "roadmap_id": str(roadmap.id),
                    "session_id": str(session.id),
                    "message": "Follow-up question",
                    "conversation_id": conversation_id,
                },
            )

        assert second_response.status_code == 200
        assert second_response.json()["conversation_id"] == conversation_id

        # Verify history has 4 messages (2 user + 2 assistant)
        chat_history = await ChatHistory.find_one(ChatHistory.conversation_id == conversation_id)
        assert chat_history is not None
        assert len(chat_history.messages) == 4

    async def test_send_message_invalid_roadmap_returns_404(
        self, client: AsyncClient, test_roadmap_with_sessions, mock_user: User
    ):
        """Sending message with invalid roadmap ID should return 404."""
        _, sessions = test_roadmap_with_sessions
        session = sessions[0]
        fake_roadmap_id = PydanticObjectId()

        with patch("app.routers.chat.is_gemini_configured", return_value=True):
            response = await client.post(
                "/api/v1/chat/",
                json={
                    "roadmap_id": str(fake_roadmap_id),
                    "session_id": str(session.id),
                    "message": "Hello",
                },
            )

        assert response.status_code == 404
        assert response.json()["detail"] == "Roadmap not found"

    async def test_send_message_invalid_session_returns_404(
        self, client: AsyncClient, test_roadmap_with_sessions, mock_user: User
    ):
        """Sending message with invalid session ID should return 404."""
        roadmap, _ = test_roadmap_with_sessions
        fake_session_id = PydanticObjectId()

        with patch("app.routers.chat.is_gemini_configured", return_value=True):
            response = await client.post(
                "/api/v1/chat/",
                json={
                    "roadmap_id": str(roadmap.id),
                    "session_id": str(fake_session_id),
                    "message": "Hello",
                },
            )

        assert response.status_code == 404
        assert response.json()["detail"] == "Session not found"


class TestGetChatHistory:
    """Tests for GET /api/v1/chat/roadmaps/{roadmap_id}/sessions/{session_id} endpoint."""

    async def test_get_chat_history_returns_messages(
        self, client: AsyncClient, test_roadmap_with_sessions, mock_user: User
    ):
        """Should return existing chat history."""
        roadmap, sessions = test_roadmap_with_sessions
        session = sessions[0]

        # Create a conversation first
        with (
            patch(
                "app.routers.chat.generate_chat_response",
                new_callable=AsyncMock,
                return_value="AI response",
            ),
            patch("app.routers.chat.is_gemini_configured", return_value=True),
        ):
            await client.post(
                "/api/v1/chat/",
                json={
                    "roadmap_id": str(roadmap.id),
                    "session_id": str(session.id),
                    "message": "Test message",
                },
            )

        # Get history
        response = await client.get(f"/api/v1/chat/roadmaps/{roadmap.id}/sessions/{session.id}")

        assert response.status_code == 200
        data = response.json()
        assert "conversation_id" in data
        assert "messages" in data
        assert len(data["messages"]) == 2
        assert data["messages"][0]["role"] == "user"
        assert data["messages"][1]["role"] == "assistant"

    async def test_get_chat_history_empty_returns_none(
        self, client: AsyncClient, test_roadmap_with_sessions, mock_user: User
    ):
        """Should return null when no chat history exists."""
        roadmap, sessions = test_roadmap_with_sessions
        session = sessions[0]

        response = await client.get(f"/api/v1/chat/roadmaps/{roadmap.id}/sessions/{session.id}")

        assert response.status_code == 200
        assert response.json() is None

    async def test_get_chat_history_wrong_roadmap_returns_404(
        self, client: AsyncClient, mock_user: User
    ):
        """Should return 404 for non-existent roadmap."""
        fake_roadmap_id = PydanticObjectId()
        fake_session_id = PydanticObjectId()

        response = await client.get(
            f"/api/v1/chat/roadmaps/{fake_roadmap_id}/sessions/{fake_session_id}"
        )

        assert response.status_code == 404


class TestClearChatHistory:
    """Tests for DELETE /api/v1/chat/roadmaps/{roadmap_id}/sessions/{session_id} endpoint."""

    async def test_clear_chat_history_returns_204(
        self, client: AsyncClient, test_roadmap_with_sessions, mock_user: User
    ):
        """Clearing chat history should return 204."""
        roadmap, sessions = test_roadmap_with_sessions
        session = sessions[0]

        # Create a conversation first
        with (
            patch(
                "app.routers.chat.generate_chat_response",
                new_callable=AsyncMock,
                return_value="AI response",
            ),
            patch("app.routers.chat.is_gemini_configured", return_value=True),
        ):
            await client.post(
                "/api/v1/chat/",
                json={
                    "roadmap_id": str(roadmap.id),
                    "session_id": str(session.id),
                    "message": "Test message",
                },
            )

        # Clear history
        response = await client.delete(f"/api/v1/chat/roadmaps/{roadmap.id}/sessions/{session.id}")

        assert response.status_code == 204

        # Verify history is cleared
        history = await ChatHistory.find_one(ChatHistory.session_id == session.id)
        assert history is None

    async def test_clear_chat_history_no_history_returns_204(
        self, client: AsyncClient, test_roadmap_with_sessions, mock_user: User
    ):
        """Clearing non-existent history should still return 204."""
        roadmap, sessions = test_roadmap_with_sessions
        session = sessions[0]

        response = await client.delete(f"/api/v1/chat/roadmaps/{roadmap.id}/sessions/{session.id}")

        assert response.status_code == 204

    async def test_clear_chat_history_wrong_roadmap_returns_404(
        self, client: AsyncClient, mock_user: User
    ):
        """Clearing history for non-existent roadmap should return 404."""
        fake_roadmap_id = PydanticObjectId()
        fake_session_id = PydanticObjectId()

        response = await client.delete(
            f"/api/v1/chat/roadmaps/{fake_roadmap_id}/sessions/{fake_session_id}"
        )

        assert response.status_code == 404
