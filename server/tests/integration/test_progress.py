"""Integration tests for /api/v1/roadmaps/{id}/progress endpoint."""

import pytest
from beanie import PydanticObjectId
from httpx import AsyncClient

from app.models.roadmap import Roadmap, SessionSummary
from app.models.session import Session
from app.models.user import User


async def create_roadmap_with_sessions(
    user: User, session_statuses: list[str]
) -> tuple[Roadmap, list[Session]]:
    """Helper to create a roadmap with sessions of specific statuses."""
    roadmap = Roadmap(
        user_id=user.id,
        title="Test Roadmap",
        summary="Test summary",
        sessions=[],
    )
    await roadmap.insert()

    sessions = []
    for order, status in enumerate(session_statuses, start=1):
        session = Session(
            roadmap_id=roadmap.id,
            order=order,
            title=f"Session {order}",
            content=f"Content for session {order}",
            status=status,
        )
        await session.insert()
        sessions.append(session)

    roadmap.sessions = [SessionSummary(id=s.id, title=s.title, order=s.order) for s in sessions]
    await roadmap.save()

    return roadmap, sessions


class TestGetProgress:
    """Tests for GET /api/v1/roadmaps/{roadmap_id}/progress endpoint."""

    async def test_progress_all_not_started(self, client: AsyncClient, mock_user: User):
        """All sessions not_started should show 0% progress."""
        roadmap, _ = await create_roadmap_with_sessions(
            mock_user, ["not_started", "not_started", "not_started"]
        )

        response = await client.get(f"/api/v1/roadmaps/{roadmap.id}/progress")

        assert response.status_code == 200
        data = response.json()
        assert data["percentage"] == 0.0
        assert data["total"] == 3
        assert data["not_started"] == 3
        assert data["done"] == 0
        assert data["in_progress"] == 0
        assert data["skipped"] == 0

    async def test_progress_partial_done(self, client: AsyncClient, mock_user: User):
        """Partial completion should calculate correct percentage."""
        roadmap, _ = await create_roadmap_with_sessions(
            mock_user, ["done", "done", "not_started", "not_started"]
        )

        response = await client.get(f"/api/v1/roadmaps/{roadmap.id}/progress")

        assert response.status_code == 200
        data = response.json()
        assert data["percentage"] == 50.0
        assert data["total"] == 4
        assert data["done"] == 2
        assert data["not_started"] == 2

    async def test_progress_all_done(self, client: AsyncClient, mock_user: User):
        """All sessions done should show 100% progress."""
        roadmap, _ = await create_roadmap_with_sessions(mock_user, ["done", "done", "done"])

        response = await client.get(f"/api/v1/roadmaps/{roadmap.id}/progress")

        assert response.status_code == 200
        data = response.json()
        assert data["percentage"] == 100.0
        assert data["done"] == 3

    async def test_progress_with_skipped(self, client: AsyncClient, mock_user: User):
        """Skipped sessions should not count towards completion."""
        roadmap, _ = await create_roadmap_with_sessions(
            mock_user, ["done", "skipped", "not_started"]
        )

        response = await client.get(f"/api/v1/roadmaps/{roadmap.id}/progress")

        assert response.status_code == 200
        data = response.json()
        # Only 1 of 3 is done, skipped doesn't count
        assert data["percentage"] == pytest.approx(33.3, rel=0.1)
        assert data["done"] == 1
        assert data["skipped"] == 1

    async def test_progress_counts_correct(self, client: AsyncClient, mock_user: User):
        """All status counts should be accurate."""
        roadmap, _ = await create_roadmap_with_sessions(
            mock_user,
            ["done", "done", "in_progress", "skipped", "not_started"],
        )

        response = await client.get(f"/api/v1/roadmaps/{roadmap.id}/progress")

        assert response.status_code == 200
        data = response.json()
        assert data["total"] == 5
        assert data["done"] == 2
        assert data["in_progress"] == 1
        assert data["skipped"] == 1
        assert data["not_started"] == 1
        assert data["percentage"] == 40.0  # 2/5 = 40%

    async def test_progress_empty_roadmap(self, client: AsyncClient, mock_user: User):
        """Roadmap with no sessions should show 0% progress."""
        roadmap, _ = await create_roadmap_with_sessions(mock_user, [])

        response = await client.get(f"/api/v1/roadmaps/{roadmap.id}/progress")

        assert response.status_code == 200
        data = response.json()
        assert data["percentage"] == 0.0
        assert data["total"] == 0

    async def test_progress_roadmap_not_found_returns_404(
        self, client: AsyncClient, mock_user: User
    ):
        """Requesting progress for non-existent roadmap should return 404."""
        fake_id = PydanticObjectId()
        response = await client.get(f"/api/v1/roadmaps/{fake_id}/progress")

        assert response.status_code == 404
        assert response.json()["detail"] == "Roadmap not found"

    async def test_progress_rounding(self, client: AsyncClient, mock_user: User):
        """Progress percentage should be rounded to one decimal place."""
        # 1/3 = 33.333...% should round to 33.3
        roadmap, _ = await create_roadmap_with_sessions(
            mock_user, ["done", "not_started", "not_started"]
        )

        response = await client.get(f"/api/v1/roadmaps/{roadmap.id}/progress")

        assert response.status_code == 200
        data = response.json()
        # Check it's a float with at most 1 decimal place
        assert data["percentage"] == round(data["percentage"], 1)
