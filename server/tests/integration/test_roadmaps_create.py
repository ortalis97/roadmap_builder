"""Integration tests for roadmap creation endpoints."""

from unittest.mock import AsyncMock, MagicMock, patch

import pytest

from app.agents.state import ExampleOption, InterviewQuestion


class TestRoadmapsCreateEndpoints:
    """Tests for the /api/v1/roadmaps/create/* endpoints."""

    @pytest.mark.asyncio
    async def test_start_creation_success(self, client):
        """Test starting creation with topic returns interview questions."""
        # Create mock questions that match the expected structure
        mock_questions = [
            InterviewQuestion(
                id="q_1234",
                question="What is your experience level?",
                purpose="To calibrate the roadmap",
                example_options=[
                    ExampleOption(label="A", text="Beginner"),
                    ExampleOption(label="B", text="Intermediate"),
                ],
                allows_freeform=True,
            )
        ]

        # Mock the orchestrator class
        mock_orchestrator = MagicMock()
        mock_orchestrator.pipeline_id = "pipeline_test123"
        mock_orchestrator.initialize = AsyncMock()
        mock_orchestrator.generate_interview_questions = AsyncMock(
            return_value=mock_questions
        )

        with patch("app.routers.roadmaps_create.is_gemini_configured", return_value=True):
            with patch("app.routers.roadmaps_create.get_gemini_client") as mock_client:
                mock_client.return_value = MagicMock()

                with patch(
                    "app.routers.roadmaps_create.PipelineOrchestrator",
                    return_value=mock_orchestrator,
                ):
                    response = await client.post(
                        "/api/v1/roadmaps/create/start",
                        json={"topic": "I want to learn Python programming"},
                    )

        assert response.status_code == 200
        data = response.json()
        assert "pipeline_id" in data
        assert data["pipeline_id"] == "pipeline_test123"
        assert "questions" in data
        assert len(data["questions"]) == 1
        assert data["questions"][0]["question"] == "What is your experience level?"

    @pytest.mark.asyncio
    async def test_start_creation_ai_not_configured(self, client):
        """Test starting creation without AI configured returns 503."""
        with patch("app.routers.roadmaps_create.is_gemini_configured", return_value=False):
            response = await client.post(
                "/api/v1/roadmaps/create/start",
                json={"topic": "Learn Python"},
            )

        assert response.status_code == 503
        assert "AI service not configured" in response.json()["detail"]

    @pytest.mark.asyncio
    async def test_interview_submit_pipeline_not_found(self, client):
        """Test submitting interview to non-existent pipeline returns 404."""
        response = await client.post(
            "/api/v1/roadmaps/create/interview",
            json={
                "pipeline_id": "pipeline_nonexistent",
                "answers": [{"question_id": "q_1", "answer": "Beginner"}],
            },
        )

        assert response.status_code == 404
        assert "Pipeline not found" in response.json()["detail"]

    @pytest.mark.asyncio
    async def test_review_submit_pipeline_not_found(self, client):
        """Test submitting review to non-existent pipeline returns 404."""
        response = await client.post(
            "/api/v1/roadmaps/create/review",
            json={
                "pipeline_id": "pipeline_nonexistent",
                "accept_as_is": True,
            },
        )

        assert response.status_code == 404
        assert "Pipeline not found" in response.json()["detail"]

    @pytest.mark.asyncio
    async def test_review_submit_with_confirmed_title(self, client):
        """Test submitting review with confirmed title to non-existent pipeline returns 404."""
        response = await client.post(
            "/api/v1/roadmaps/create/review",
            json={
                "pipeline_id": "pipeline_nonexistent",
                "accept_as_is": True,
                "confirmed_title": "My Custom Title",
            },
        )

        assert response.status_code == 404
        assert "Pipeline not found" in response.json()["detail"]

    @pytest.mark.asyncio
    async def test_cancel_creation_not_found(self, client):
        """Test cancelling non-existent pipeline returns 404."""
        response = await client.delete("/api/v1/roadmaps/create/pipeline_nonexistent")

        assert response.status_code == 404
        assert "Pipeline not found" in response.json()["detail"]
