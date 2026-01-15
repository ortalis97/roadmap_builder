"""Integration tests for /api/v1/drafts endpoints."""

from beanie import PydanticObjectId
from httpx import AsyncClient

from app.models.draft import Draft
from app.models.user import User


class TestCreateDraft:
    """Tests for POST /api/v1/drafts endpoint."""

    async def test_create_draft_returns_201(self, client: AsyncClient, mock_user: User):
        """Creating a draft should return 201 status."""
        response = await client.post(
            "/api/v1/drafts/",
            json={"raw_text": "Learn React: components, hooks, state, routing"},
        )

        assert response.status_code == 201

    async def test_create_draft_stores_raw_text(self, client: AsyncClient, mock_user: User):
        """Created draft should contain the submitted raw_text."""
        raw_text = "Learn Vue.js: basics, composition API, Pinia, routing"
        response = await client.post(
            "/api/v1/drafts/",
            json={"raw_text": raw_text},
        )

        assert response.status_code == 201
        data = response.json()
        assert data["raw_text"] == raw_text
        assert data["user_id"] == str(mock_user.id)
        assert "id" in data
        assert "created_at" in data

    async def test_create_draft_returns_valid_id(self, client: AsyncClient, mock_user: User):
        """Created draft should have a valid ObjectId."""
        response = await client.post(
            "/api/v1/drafts/",
            json={"raw_text": "Learn TypeScript"},
        )

        assert response.status_code == 201
        data = response.json()
        # Verify the ID is a valid ObjectId format
        assert len(data["id"]) == 24  # MongoDB ObjectId is 24 hex chars

    async def test_create_draft_empty_text_returns_422(self, client: AsyncClient, mock_user: User):
        """Empty raw_text should still be accepted (no validation on content)."""
        response = await client.post(
            "/api/v1/drafts/",
            json={"raw_text": ""},
        )
        # Empty string is still valid - no content validation
        assert response.status_code == 201


class TestGetDraft:
    """Tests for GET /api/v1/drafts/{draft_id} endpoint."""

    async def test_get_draft_returns_draft(
        self, client: AsyncClient, test_draft: Draft, mock_user: User
    ):
        """Retrieving an existing draft should return its data."""
        response = await client.get(f"/api/v1/drafts/{test_draft.id}")

        assert response.status_code == 200
        data = response.json()
        assert data["id"] == str(test_draft.id)
        assert data["raw_text"] == test_draft.raw_text
        assert data["user_id"] == str(mock_user.id)

    async def test_get_draft_not_found_returns_404(self, client: AsyncClient, mock_user: User):
        """Requesting non-existent draft should return 404."""
        fake_id = PydanticObjectId()
        response = await client.get(f"/api/v1/drafts/{fake_id}")

        assert response.status_code == 404
        assert response.json()["detail"] == "Draft not found"

    async def test_get_draft_wrong_user_returns_404(
        self, client: AsyncClient, other_user_draft: Draft, mock_user: User
    ):
        """Requesting another user's draft should return 404."""
        response = await client.get(f"/api/v1/drafts/{other_user_draft.id}")

        assert response.status_code == 404
        assert response.json()["detail"] == "Draft not found"

    async def test_get_draft_invalid_id_returns_400(self, client: AsyncClient, mock_user: User):
        """Requesting with invalid ObjectId format should return 400."""
        response = await client.get("/api/v1/drafts/invalid-id-format")

        assert response.status_code == 400
        assert response.json()["detail"] == "Invalid draft ID format"
