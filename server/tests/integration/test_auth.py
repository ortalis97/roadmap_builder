"""Integration tests for /api/v1/auth endpoints."""

from httpx import AsyncClient

from app.models.user import User


class TestAuthMe:
    """Tests for GET /api/v1/auth/me endpoint."""

    async def test_get_me_returns_user_profile(self, client: AsyncClient, mock_user: User):
        """Authenticated user should receive their profile."""
        response = await client.get("/api/v1/auth/me")

        assert response.status_code == 200
        data = response.json()
        assert data["id"] == str(mock_user.id)
        assert data["firebase_uid"] == mock_user.firebase_uid
        assert data["email"] == mock_user.email
        assert data["name"] == mock_user.name
        assert data["picture"] == mock_user.picture

    async def test_get_me_response_has_correct_fields(self, client: AsyncClient, mock_user: User):
        """Response should contain all expected fields."""
        response = await client.get("/api/v1/auth/me")

        assert response.status_code == 200
        data = response.json()

        # Check all required fields are present
        required_fields = {"id", "firebase_uid", "email", "name", "picture"}
        assert set(data.keys()) == required_fields

    async def test_get_me_returns_correct_email(self, client: AsyncClient, mock_user: User):
        """Response should contain the correct email from the user."""
        response = await client.get("/api/v1/auth/me")

        assert response.status_code == 200
        assert response.json()["email"] == "test@example.com"
