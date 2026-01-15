"""Integration tests for /api/v1/roadmaps endpoints."""

from unittest.mock import AsyncMock, patch

from beanie import PydanticObjectId
from httpx import AsyncClient

from app.models.draft import Draft
from app.models.roadmap import Roadmap
from app.models.session import Session
from app.models.user import User
from app.services.ai_service import GeneratedRoadmap, GeneratedSession


class TestListRoadmaps:
    """Tests for GET /api/v1/roadmaps endpoint."""

    async def test_list_roadmaps_empty(self, client: AsyncClient, mock_user: User):
        """Empty list when user has no roadmaps."""
        response = await client.get("/api/v1/roadmaps/")

        assert response.status_code == 200
        assert response.json() == []

    async def test_list_roadmaps_returns_user_roadmaps(
        self, client: AsyncClient, test_roadmap: Roadmap, mock_user: User
    ):
        """User should see their own roadmaps."""
        response = await client.get("/api/v1/roadmaps/")

        assert response.status_code == 200
        data = response.json()
        assert len(data) == 1
        assert data[0]["id"] == str(test_roadmap.id)
        assert data[0]["title"] == test_roadmap.title
        assert data[0]["session_count"] == 0

    async def test_list_roadmaps_excludes_other_users(
        self,
        client: AsyncClient,
        test_roadmap: Roadmap,
        other_user_roadmap: Roadmap,
        mock_user: User,
    ):
        """User should not see other users' roadmaps."""
        response = await client.get("/api/v1/roadmaps/")

        assert response.status_code == 200
        data = response.json()
        # Only see own roadmap
        assert len(data) == 1
        assert data[0]["id"] == str(test_roadmap.id)


class TestCreateRoadmap:
    """Tests for POST /api/v1/roadmaps endpoint."""

    async def test_create_roadmap_returns_201(
        self, client: AsyncClient, test_draft: Draft, mock_user: User
    ):
        """Creating a roadmap should return 201 with mocked AI."""
        mock_generated = GeneratedRoadmap(
            summary="A Python learning journey",
            sessions=[
                GeneratedSession(title="Python Basics", content="Learn Python fundamentals"),
                GeneratedSession(title="Functions", content="Learn to write functions"),
            ],
        )

        with (
            patch(
                "app.routers.roadmaps.generate_sessions_from_draft",
                new_callable=AsyncMock,
                return_value=mock_generated,
            ),
            patch("app.routers.roadmaps.is_gemini_configured", return_value=True),
        ):
            response = await client.post(
                "/api/v1/roadmaps/",
                json={"draft_id": str(test_draft.id), "title": "Learn Python"},
            )

        assert response.status_code == 201
        data = response.json()
        assert data["title"] == "Learn Python"
        assert data["summary"] == "A Python learning journey"
        assert len(data["sessions"]) == 2

    async def test_create_roadmap_creates_sessions(
        self, client: AsyncClient, test_draft: Draft, mock_user: User
    ):
        """Creating a roadmap should also create session documents."""
        mock_generated = GeneratedRoadmap(
            summary="Test summary",
            sessions=[
                GeneratedSession(title="Session 1", content="Content 1"),
                GeneratedSession(title="Session 2", content="Content 2"),
            ],
        )

        with (
            patch(
                "app.routers.roadmaps.generate_sessions_from_draft",
                new_callable=AsyncMock,
                return_value=mock_generated,
            ),
            patch("app.routers.roadmaps.is_gemini_configured", return_value=True),
        ):
            response = await client.post(
                "/api/v1/roadmaps/",
                json={"draft_id": str(test_draft.id), "title": "Test Roadmap"},
            )

        assert response.status_code == 201
        data = response.json()

        # Verify sessions were created in database
        for session_summary in data["sessions"]:
            session = await Session.get(PydanticObjectId(session_summary["id"]))
            assert session is not None
            assert session.roadmap_id == PydanticObjectId(data["id"])

    async def test_create_roadmap_invalid_draft_returns_404(
        self, client: AsyncClient, mock_user: User
    ):
        """Creating roadmap with non-existent draft should return 404."""
        fake_draft_id = PydanticObjectId()

        with patch("app.routers.roadmaps.is_gemini_configured", return_value=True):
            response = await client.post(
                "/api/v1/roadmaps/",
                json={"draft_id": str(fake_draft_id), "title": "Test"},
            )

        assert response.status_code == 404
        assert response.json()["detail"] == "Draft not found"

    async def test_create_roadmap_wrong_user_draft_returns_404(
        self, client: AsyncClient, other_user_draft: Draft, mock_user: User
    ):
        """Creating roadmap with another user's draft should return 404."""
        with patch("app.routers.roadmaps.is_gemini_configured", return_value=True):
            response = await client.post(
                "/api/v1/roadmaps/",
                json={"draft_id": str(other_user_draft.id), "title": "Test"},
            )

        assert response.status_code == 404
        assert response.json()["detail"] == "Draft not found"

    async def test_create_roadmap_invalid_draft_id_format_returns_400(
        self, client: AsyncClient, mock_user: User
    ):
        """Creating roadmap with invalid draft ID format should return 400."""
        response = await client.post(
            "/api/v1/roadmaps/",
            json={"draft_id": "invalid-id", "title": "Test"},
        )

        assert response.status_code == 400
        assert response.json()["detail"] == "Invalid draft ID format"


class TestGetRoadmap:
    """Tests for GET /api/v1/roadmaps/{roadmap_id} endpoint."""

    async def test_get_roadmap_returns_roadmap(
        self, client: AsyncClient, test_roadmap: Roadmap, mock_user: User
    ):
        """Retrieving an existing roadmap should return its data."""
        response = await client.get(f"/api/v1/roadmaps/{test_roadmap.id}")

        assert response.status_code == 200
        data = response.json()
        assert data["id"] == str(test_roadmap.id)
        assert data["title"] == test_roadmap.title
        assert data["summary"] == test_roadmap.summary

    async def test_get_roadmap_with_sessions(
        self, client: AsyncClient, test_roadmap_with_sessions, mock_user: User
    ):
        """Roadmap should include session summaries."""
        roadmap, sessions = test_roadmap_with_sessions
        response = await client.get(f"/api/v1/roadmaps/{roadmap.id}")

        assert response.status_code == 200
        data = response.json()
        assert len(data["sessions"]) == 3
        assert data["sessions"][0]["title"] == "Introduction to Python"

    async def test_get_roadmap_not_found_returns_404(self, client: AsyncClient, mock_user: User):
        """Requesting non-existent roadmap should return 404."""
        fake_id = PydanticObjectId()
        response = await client.get(f"/api/v1/roadmaps/{fake_id}")

        assert response.status_code == 404
        assert response.json()["detail"] == "Roadmap not found"

    async def test_get_roadmap_wrong_user_returns_404(
        self, client: AsyncClient, other_user_roadmap: Roadmap, mock_user: User
    ):
        """Requesting another user's roadmap should return 404."""
        response = await client.get(f"/api/v1/roadmaps/{other_user_roadmap.id}")

        assert response.status_code == 404
        assert response.json()["detail"] == "Roadmap not found"

    async def test_get_roadmap_invalid_id_returns_400(self, client: AsyncClient, mock_user: User):
        """Requesting with invalid ObjectId format should return 400."""
        response = await client.get("/api/v1/roadmaps/invalid-id")

        assert response.status_code == 400
        assert response.json()["detail"] == "Invalid roadmap ID format"


class TestDeleteRoadmap:
    """Tests for DELETE /api/v1/roadmaps/{roadmap_id} endpoint."""

    async def test_delete_roadmap_returns_204(
        self, client: AsyncClient, test_roadmap: Roadmap, mock_user: User
    ):
        """Deleting a roadmap should return 204."""
        response = await client.delete(f"/api/v1/roadmaps/{test_roadmap.id}")

        assert response.status_code == 204

        # Verify roadmap is deleted
        deleted = await Roadmap.get(test_roadmap.id)
        assert deleted is None

    async def test_delete_roadmap_not_found_returns_404(self, client: AsyncClient, mock_user: User):
        """Deleting non-existent roadmap should return 404."""
        fake_id = PydanticObjectId()
        response = await client.delete(f"/api/v1/roadmaps/{fake_id}")

        assert response.status_code == 404
        assert response.json()["detail"] == "Roadmap not found"

    async def test_delete_roadmap_wrong_user_returns_404(
        self, client: AsyncClient, other_user_roadmap: Roadmap, mock_user: User
    ):
        """Deleting another user's roadmap should return 404."""
        response = await client.delete(f"/api/v1/roadmaps/{other_user_roadmap.id}")

        assert response.status_code == 404
        assert response.json()["detail"] == "Roadmap not found"
