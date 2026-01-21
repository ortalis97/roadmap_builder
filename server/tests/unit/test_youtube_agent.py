"""Unit tests for YouTube agent."""

from unittest.mock import AsyncMock, MagicMock, patch

import pytest

from app.agents.state import ResearchedSession, SessionType
from app.agents.youtube import YouTubeAgent


@pytest.fixture
def mock_gemini_client():
    """Create a mock Gemini client."""
    return MagicMock()


class TestYouTubeAgent:
    """Tests for the YouTubeAgent."""

    def test_agent_name(self, mock_gemini_client):
        """Test agent has correct name."""
        agent = YouTubeAgent(mock_gemini_client)
        assert agent.name == "youtube_agent"

    def test_agent_temperature_is_low(self, mock_gemini_client):
        """Test agent uses low temperature for factual search."""
        agent = YouTubeAgent(mock_gemini_client)
        assert agent.default_temperature == 0.3

    @pytest.mark.asyncio
    async def test_find_videos_returns_videos(self, mock_gemini_client):
        """Test that find_videos returns parsed video list."""
        mock_response = """{
            "videos": [
                {
                    "url": "https://www.youtube.com/watch?v=abc123",
                    "title": "Learn Python Basics",
                    "channel": "Programming Academy",
                    "thumbnail_url": "https://img.youtube.com/vi/abc123/maxresdefault.jpg",
                    "duration_minutes": 15,
                    "description": "Introduction to Python programming"
                },
                {
                    "url": "https://www.youtube.com/watch?v=def456",
                    "title": "Python Variables Tutorial",
                    "channel": "Code School",
                    "thumbnail_url": "https://img.youtube.com/vi/def456/maxresdefault.jpg",
                    "duration_minutes": 22,
                    "description": "Understanding variables in Python"
                }
            ]
        }"""

        agent = YouTubeAgent(mock_gemini_client)

        with patch.object(
            agent, "generate_with_grounding", new_callable=AsyncMock
        ) as mock_generate:
            mock_generate.return_value = mock_response

            session = ResearchedSession(
                outline_id="test_001",
                title="Introduction to Python",
                session_type=SessionType.CONCEPT,
                order=1,
                content="Learn the basics of Python programming.",
                key_concepts=["variables", "data types", "syntax"],
                resources=[],
                exercises=[],
            )

            videos = await agent.find_videos(session)

            assert len(videos) == 2
            assert videos[0].url == "https://www.youtube.com/watch?v=abc123"
            assert videos[0].title == "Learn Python Basics"
            assert videos[0].channel == "Programming Academy"
            assert videos[0].duration_minutes == 15
            assert videos[1].url == "https://www.youtube.com/watch?v=def456"

    @pytest.mark.asyncio
    async def test_find_videos_handles_empty_response(self, mock_gemini_client):
        """Test graceful handling of empty video results."""
        mock_response = '{"videos": []}'

        agent = YouTubeAgent(mock_gemini_client)

        with patch.object(
            agent, "generate_with_grounding", new_callable=AsyncMock
        ) as mock_generate:
            mock_generate.return_value = mock_response

            session = ResearchedSession(
                outline_id="test_002",
                title="Obscure Topic",
                session_type=SessionType.CONCEPT,
                order=1,
                content="Very niche content.",
                key_concepts=[],
                resources=[],
                exercises=[],
            )

            videos = await agent.find_videos(session)
            assert len(videos) == 0

    @pytest.mark.asyncio
    async def test_find_videos_handles_error_gracefully(self, mock_gemini_client):
        """Test graceful degradation on API error."""
        agent = YouTubeAgent(mock_gemini_client)

        with patch.object(
            agent, "generate_with_grounding", new_callable=AsyncMock
        ) as mock_generate:
            mock_generate.side_effect = Exception("API Error")

            session = ResearchedSession(
                outline_id="test_003",
                title="Test Session",
                session_type=SessionType.CONCEPT,
                order=1,
                content="Test content",
                key_concepts=[],
                resources=[],
                exercises=[],
            )

            # Should not raise, should return empty list
            videos = await agent.find_videos(session)
            assert len(videos) == 0

    @pytest.mark.asyncio
    async def test_find_videos_filters_invalid_urls(self, mock_gemini_client):
        """Test that videos with invalid URLs are filtered out."""
        mock_response = """{
            "videos": [
                {
                    "url": "https://www.youtube.com/watch?v=valid123",
                    "title": "Valid Video",
                    "channel": "Channel",
                    "thumbnail_url": "https://img.youtube.com/vi/valid123/maxresdefault.jpg",
                    "duration_minutes": 10,
                    "description": "Valid"
                },
                {
                    "url": "https://vimeo.com/invalid",
                    "title": "Invalid Video",
                    "channel": "Channel",
                    "thumbnail_url": "url",
                    "duration_minutes": 10,
                    "description": "Invalid"
                }
            ]
        }"""

        agent = YouTubeAgent(mock_gemini_client)

        with patch.object(
            agent, "generate_with_grounding", new_callable=AsyncMock
        ) as mock_generate:
            mock_generate.return_value = mock_response

            session = ResearchedSession(
                outline_id="test_004",
                title="Test",
                session_type=SessionType.CONCEPT,
                order=1,
                content="Content",
                key_concepts=[],
                resources=[],
                exercises=[],
            )

            videos = await agent.find_videos(session)

            # Only the YouTube video should be included
            assert len(videos) == 1
            assert "youtube.com" in videos[0].url

    @pytest.mark.asyncio
    async def test_find_videos_handles_markdown_wrapped_json(self, mock_gemini_client):
        """Test parsing JSON wrapped in markdown code blocks."""
        mock_response = """```json
{
    "videos": [
        {
            "url": "https://www.youtube.com/watch?v=test123",
            "title": "Test Video",
            "channel": "Test Channel",
            "thumbnail_url": "https://img.youtube.com/vi/test123/maxresdefault.jpg",
            "duration_minutes": 10,
            "description": "Test"
        }
    ]
}
```"""

        agent = YouTubeAgent(mock_gemini_client)

        with patch.object(
            agent, "generate_with_grounding", new_callable=AsyncMock
        ) as mock_generate:
            mock_generate.return_value = mock_response

            session = ResearchedSession(
                outline_id="test_005",
                title="Test",
                session_type=SessionType.CONCEPT,
                order=1,
                content="Content",
                key_concepts=[],
                resources=[],
                exercises=[],
            )

            videos = await agent.find_videos(session)
            assert len(videos) == 1
            assert videos[0].title == "Test Video"

    @pytest.mark.asyncio
    async def test_find_videos_limits_to_max_videos(self, mock_gemini_client):
        """Test that find_videos respects max_videos parameter."""
        mock_response = """{
            "videos": [
                {"url": "https://www.youtube.com/watch?v=1", "title": "Video 1", "channel": "C1", "thumbnail_url": "url1", "duration_minutes": 10, "description": "D1"},
                {"url": "https://www.youtube.com/watch?v=2", "title": "Video 2", "channel": "C2", "thumbnail_url": "url2", "duration_minutes": 10, "description": "D2"},
                {"url": "https://www.youtube.com/watch?v=3", "title": "Video 3", "channel": "C3", "thumbnail_url": "url3", "duration_minutes": 10, "description": "D3"},
                {"url": "https://www.youtube.com/watch?v=4", "title": "Video 4", "channel": "C4", "thumbnail_url": "url4", "duration_minutes": 10, "description": "D4"}
            ]
        }"""

        agent = YouTubeAgent(mock_gemini_client)

        with patch.object(
            agent, "generate_with_grounding", new_callable=AsyncMock
        ) as mock_generate:
            mock_generate.return_value = mock_response

            session = ResearchedSession(
                outline_id="test_006",
                title="Test",
                session_type=SessionType.CONCEPT,
                order=1,
                content="Content",
                key_concepts=[],
                resources=[],
                exercises=[],
            )

            # Request only 2 videos
            videos = await agent.find_videos(session, max_videos=2)
            assert len(videos) == 2
