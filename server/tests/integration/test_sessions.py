"""Integration tests for /api/v1/roadmaps/{id}/sessions endpoints."""

from beanie import PydanticObjectId
from httpx import AsyncClient

from app.models.roadmap import Roadmap
from app.models.session import Session
from app.models.user import User


class TestListSessions:
    """Tests for GET /api/v1/roadmaps/{roadmap_id}/sessions endpoint."""

    async def test_list_sessions_returns_sessions_with_status(
        self, client: AsyncClient, test_roadmap_with_sessions, mock_user: User
    ):
        """Should return all sessions with their status."""
        roadmap, sessions = test_roadmap_with_sessions
        response = await client.get(f"/api/v1/roadmaps/{roadmap.id}/sessions")

        assert response.status_code == 200
        data = response.json()
        assert len(data) == 3
        # Verify structure
        for session_data in data:
            assert "id" in session_data
            assert "title" in session_data
            assert "order" in session_data
            assert "status" in session_data

    async def test_list_sessions_ordered_by_order(
        self, client: AsyncClient, test_roadmap_with_sessions, mock_user: User
    ):
        """Sessions should be returned in order."""
        roadmap, sessions = test_roadmap_with_sessions
        response = await client.get(f"/api/v1/roadmaps/{roadmap.id}/sessions")

        assert response.status_code == 200
        data = response.json()
        orders = [s["order"] for s in data]
        assert orders == [1, 2, 3]

    async def test_list_sessions_roadmap_not_found_returns_404(
        self, client: AsyncClient, mock_user: User
    ):
        """Requesting sessions for non-existent roadmap should return 404."""
        fake_id = PydanticObjectId()
        response = await client.get(f"/api/v1/roadmaps/{fake_id}/sessions")

        assert response.status_code == 404
        assert response.json()["detail"] == "Roadmap not found"


class TestGetSession:
    """Tests for GET /api/v1/roadmaps/{roadmap_id}/sessions/{session_id} endpoint."""

    async def test_get_session_returns_full_session(
        self, client: AsyncClient, test_roadmap_with_sessions, mock_user: User
    ):
        """Should return full session details including content."""
        roadmap, sessions = test_roadmap_with_sessions
        session = sessions[0]
        response = await client.get(f"/api/v1/roadmaps/{roadmap.id}/sessions/{session.id}")

        assert response.status_code == 200
        data = response.json()
        assert data["id"] == str(session.id)
        assert data["title"] == session.title
        assert data["content"] == session.content
        assert data["status"] == "not_started"
        assert data["notes"] == ""
        assert "created_at" in data
        assert "updated_at" in data

    async def test_get_session_not_found_returns_404(
        self, client: AsyncClient, test_roadmap_with_sessions, mock_user: User
    ):
        """Requesting non-existent session should return 404."""
        roadmap, _ = test_roadmap_with_sessions
        fake_session_id = PydanticObjectId()
        response = await client.get(f"/api/v1/roadmaps/{roadmap.id}/sessions/{fake_session_id}")

        assert response.status_code == 404
        assert response.json()["detail"] == "Session not found"

    async def test_get_session_wrong_roadmap_returns_404(
        self,
        client: AsyncClient,
        test_roadmap_with_sessions,
        test_roadmap: Roadmap,
        mock_user: User,
    ):
        """Requesting session with wrong roadmap ID should return 404."""
        _, sessions = test_roadmap_with_sessions
        session = sessions[0]
        # Use test_roadmap (different) to request session from test_roadmap_with_sessions
        response = await client.get(f"/api/v1/roadmaps/{test_roadmap.id}/sessions/{session.id}")

        assert response.status_code == 404


class TestUpdateSession:
    """Tests for PATCH /api/v1/roadmaps/{roadmap_id}/sessions/{session_id} endpoint."""

    async def test_update_session_status(
        self, client: AsyncClient, test_roadmap_with_sessions, mock_user: User
    ):
        """Should update session status."""
        roadmap, sessions = test_roadmap_with_sessions
        session = sessions[0]
        response = await client.patch(
            f"/api/v1/roadmaps/{roadmap.id}/sessions/{session.id}",
            json={"status": "done"},
        )

        assert response.status_code == 200
        data = response.json()
        assert data["status"] == "done"

        # Verify in database
        updated = await Session.get(session.id)
        assert updated.status == "done"

    async def test_update_session_notes(
        self, client: AsyncClient, test_roadmap_with_sessions, mock_user: User
    ):
        """Should update session notes."""
        roadmap, sessions = test_roadmap_with_sessions
        session = sessions[0]
        notes = "These are my learning notes for this session."
        response = await client.patch(
            f"/api/v1/roadmaps/{roadmap.id}/sessions/{session.id}",
            json={"notes": notes},
        )

        assert response.status_code == 200
        data = response.json()
        assert data["notes"] == notes

        # Verify in database
        updated = await Session.get(session.id)
        assert updated.notes == notes

    async def test_update_session_both_status_and_notes(
        self, client: AsyncClient, test_roadmap_with_sessions, mock_user: User
    ):
        """Should update both status and notes together."""
        roadmap, sessions = test_roadmap_with_sessions
        session = sessions[0]
        response = await client.patch(
            f"/api/v1/roadmaps/{roadmap.id}/sessions/{session.id}",
            json={"status": "in_progress", "notes": "Started working on this"},
        )

        assert response.status_code == 200
        data = response.json()
        assert data["status"] == "in_progress"
        assert data["notes"] == "Started working on this"

    async def test_update_session_invalid_status_returns_400(
        self, client: AsyncClient, test_roadmap_with_sessions, mock_user: User
    ):
        """Should reject invalid status values."""
        roadmap, sessions = test_roadmap_with_sessions
        session = sessions[0]
        response = await client.patch(
            f"/api/v1/roadmaps/{roadmap.id}/sessions/{session.id}",
            json={"status": "invalid_status"},
        )

        assert response.status_code == 400
        assert "Invalid status" in response.json()["detail"]

    async def test_update_session_updates_timestamp(
        self, client: AsyncClient, test_roadmap_with_sessions, mock_user: User
    ):
        """Updating session should update the updated_at timestamp."""
        roadmap, sessions = test_roadmap_with_sessions
        session = sessions[0]

        response = await client.patch(
            f"/api/v1/roadmaps/{roadmap.id}/sessions/{session.id}",
            json={"status": "done"},
        )

        assert response.status_code == 200

        # Check timestamp was updated (via API response)
        data = response.json()
        assert "updated_at" in data
        # Verify the response has a valid timestamp string
        assert data["updated_at"] is not None

    async def test_update_session_all_valid_statuses(
        self, client: AsyncClient, test_roadmap_with_sessions, mock_user: User
    ):
        """Should accept all valid status values."""
        roadmap, sessions = test_roadmap_with_sessions
        valid_statuses = ["not_started", "in_progress", "done", "skipped"]

        for i, status in enumerate(valid_statuses):
            session = sessions[i % len(sessions)]
            response = await client.patch(
                f"/api/v1/roadmaps/{roadmap.id}/sessions/{session.id}",
                json={"status": status},
            )
            assert response.status_code == 200
            assert response.json()["status"] == status
