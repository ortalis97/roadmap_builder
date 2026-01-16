"""Integration tests for /api/v1/roadmaps endpoints."""

from beanie import PydanticObjectId
from httpx import AsyncClient

from app.models.roadmap import Roadmap
from app.models.user import User


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
