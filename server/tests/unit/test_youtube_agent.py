"""Unit tests for YouTube agent."""

from unittest.mock import AsyncMock, MagicMock, patch

import pytest

from app.agents.state import ResearchedSession, SessionType, VideoResource
from app.agents.youtube import YouTubeAgent
from app.services.youtube_service import QuotaExhaustedError


@pytest.fixture
def mock_gemini_client():
    """Create a mock Gemini client."""
    return MagicMock()


@pytest.fixture
def sample_session():
    """Create a sample session for testing."""
    return ResearchedSession(
        outline_id="test_001",
        title="Introduction to Python",
        session_type=SessionType.CONCEPT,
        order=1,
        content="Learn the basics of Python programming.",
        key_concepts=["variables", "data types", "syntax"],
        resources=[],
        exercises=[],
    )


@pytest.fixture(autouse=True)
def reset_quota_flag():
    """Reset the quota exhausted flag before each test."""
    YouTubeAgent._quota_exhausted = False
    yield
    YouTubeAgent._quota_exhausted = False


class TestYouTubeAgent:
    """Tests for the YouTubeAgent basic functionality and Gemini fallback path."""

    def test_agent_name(self, mock_gemini_client):
        """Test agent has correct name."""
        agent = YouTubeAgent(mock_gemini_client)
        assert agent.name == "youtube_agent"

    def test_agent_temperature_is_low(self, mock_gemini_client):
        """Test agent uses low temperature for factual search."""
        agent = YouTubeAgent(mock_gemini_client)
        assert agent.default_temperature == 0.3

    @pytest.mark.asyncio
    async def test_gemini_fallback_returns_videos(self, mock_gemini_client):
        """Test that Gemini fallback returns parsed video list with oEmbed verification."""
        # Set quota exhausted to force Gemini fallback path
        YouTubeAgent._quota_exhausted = True

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

            # Mock oEmbed to return verified data for all videos
            async def mock_verify(url):
                if "abc123" in url:
                    return {
                        "title": "Learn Python Basics",
                        "author_name": "Programming Academy",
                        "thumbnail_url": "https://example.com/thumb1.jpg",
                    }
                elif "def456" in url:
                    return {
                        "title": "Python Variables Tutorial",
                        "author_name": "Code School",
                        "thumbnail_url": "https://example.com/thumb2.jpg",
                    }
                return None

            with patch.object(
                agent.youtube_service, "verify_video_exists", side_effect=mock_verify
            ):
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
                assert videos[1].url == "https://www.youtube.com/watch?v=def456"

    @pytest.mark.asyncio
    async def test_gemini_fallback_handles_empty_response(self, mock_gemini_client):
        """Test graceful handling of empty video results in Gemini fallback."""
        YouTubeAgent._quota_exhausted = True
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
    async def test_gemini_fallback_handles_error_gracefully(self, mock_gemini_client):
        """Test graceful degradation on Gemini API error."""
        YouTubeAgent._quota_exhausted = True
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
    async def test_gemini_filters_non_youtube_urls(self, mock_gemini_client):
        """Test that videos with non-YouTube URLs are filtered out in Gemini suggestions."""
        YouTubeAgent._quota_exhausted = True
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

            # Mock oEmbed verification
            async def mock_verify(url):
                if "valid123" in url:
                    return {"title": "Valid Video", "author_name": "Channel"}
                return None

            with patch.object(
                agent.youtube_service, "verify_video_exists", side_effect=mock_verify
            ):
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
    async def test_gemini_handles_markdown_wrapped_json(self, mock_gemini_client):
        """Test parsing JSON wrapped in markdown code blocks."""
        YouTubeAgent._quota_exhausted = True
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

            # Mock oEmbed verification
            async def mock_verify(url):
                return {"title": "Test Video", "author_name": "Test Channel"}

            with patch.object(
                agent.youtube_service, "verify_video_exists", side_effect=mock_verify
            ):
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
    async def test_gemini_fallback_limits_to_max_videos(self, mock_gemini_client):
        """Test that Gemini fallback respects max_videos parameter."""
        YouTubeAgent._quota_exhausted = True
        mock_response = """{
            "videos": [
                {
                    "url": "https://www.youtube.com/watch?v=1",
                    "title": "Video 1",
                    "channel": "C1",
                    "thumbnail_url": "url1",
                    "duration_minutes": 10,
                    "description": "D1"
                },
                {
                    "url": "https://www.youtube.com/watch?v=2",
                    "title": "Video 2",
                    "channel": "C2",
                    "thumbnail_url": "url2",
                    "duration_minutes": 10,
                    "description": "D2"
                },
                {
                    "url": "https://www.youtube.com/watch?v=3",
                    "title": "Video 3",
                    "channel": "C3",
                    "thumbnail_url": "url3",
                    "duration_minutes": 10,
                    "description": "D3"
                },
                {
                    "url": "https://www.youtube.com/watch?v=4",
                    "title": "Video 4",
                    "channel": "C4",
                    "thumbnail_url": "url4",
                    "duration_minutes": 10,
                    "description": "D4"
                }
            ]
        }"""

        agent = YouTubeAgent(mock_gemini_client)

        with patch.object(
            agent, "generate_with_grounding", new_callable=AsyncMock
        ) as mock_generate:
            mock_generate.return_value = mock_response

            # Mock oEmbed to verify all videos
            async def mock_verify(url):
                return {"title": "Video", "author_name": "Channel"}

            with patch.object(
                agent.youtube_service, "verify_video_exists", side_effect=mock_verify
            ):
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


class TestYouTubeAgentAPIIntegration:
    """Tests for YouTube API integration and fallback behavior."""

    @pytest.mark.asyncio
    async def test_find_videos_uses_api_first(self, mock_gemini_client, sample_session):
        """Test that find_videos uses YouTube API as primary source."""
        agent = YouTubeAgent(mock_gemini_client)

        mock_api_response = [
            {
                "id": {"videoId": "api123"},
                "snippet": {
                    "title": "API Video",
                    "channelTitle": "API Channel",
                    "description": "From API",
                    "thumbnails": {"high": {"url": "https://example.com/thumb.jpg"}},
                },
            }
        ]

        with patch.object(
            agent.youtube_service, "search_videos", new_callable=AsyncMock
        ) as mock_search:
            mock_search.return_value = mock_api_response

            videos = await agent.find_videos(sample_session)

            mock_search.assert_called_once()
            assert len(videos) == 1
            assert videos[0].url == "https://www.youtube.com/watch?v=api123"
            assert videos[0].title == "API Video"
            assert videos[0].channel == "API Channel"

    @pytest.mark.asyncio
    async def test_fallback_on_quota_exhausted(self, mock_gemini_client, sample_session):
        """Test fallback to Gemini+oEmbed when API quota is exhausted."""
        agent = YouTubeAgent(mock_gemini_client)

        # Mock API to raise quota error
        with patch.object(
            agent.youtube_service, "search_videos", new_callable=AsyncMock
        ) as mock_search:
            mock_search.side_effect = QuotaExhaustedError("Quota exhausted")

            # Mock the Gemini fallback
            with patch.object(
                agent,
                "_find_videos_via_gemini_with_verification",
                new_callable=AsyncMock,
            ) as mock_fallback:
                mock_fallback.return_value = [
                    VideoResource(
                        url="https://www.youtube.com/watch?v=fallback123",
                        title="Fallback Video",
                        channel="Fallback Channel",
                        thumbnail_url="https://example.com/thumb.jpg",
                    )
                ]

                videos = await agent.find_videos(sample_session)

                # Should have switched to fallback
                mock_fallback.assert_called_once()
                assert len(videos) == 1
                assert "fallback123" in videos[0].url

    @pytest.mark.asyncio
    async def test_quota_flag_persists_across_calls(self, mock_gemini_client, sample_session):
        """Test that quota exhausted flag persists and skips API on subsequent calls."""
        # Set flag as if quota was already exhausted
        YouTubeAgent._quota_exhausted = True

        agent = YouTubeAgent(mock_gemini_client)

        with patch.object(
            agent.youtube_service, "search_videos", new_callable=AsyncMock
        ) as mock_search:
            with patch.object(
                agent,
                "_find_videos_via_gemini_with_verification",
                new_callable=AsyncMock,
            ) as mock_fallback:
                mock_fallback.return_value = []

                await agent.find_videos(sample_session)

                # API should NOT be called when quota flag is set
                mock_search.assert_not_called()
                # Fallback should be called directly
                mock_fallback.assert_called_once()

    @pytest.mark.asyncio
    async def test_fallback_on_api_not_configured(self, mock_gemini_client, sample_session):
        """Test fallback when YouTube API key is not configured."""
        agent = YouTubeAgent(mock_gemini_client)

        with patch.object(
            agent.youtube_service, "search_videos", new_callable=AsyncMock
        ) as mock_search:
            mock_search.side_effect = ValueError("YouTube API key not configured")

            with patch.object(
                agent,
                "_find_videos_via_gemini_with_verification",
                new_callable=AsyncMock,
            ) as mock_fallback:
                mock_fallback.return_value = []

                await agent.find_videos(sample_session)

                # Should switch to fallback on ValueError
                mock_fallback.assert_called_once()
                # Quota flag should be set
                assert YouTubeAgent._quota_exhausted is True

    @pytest.mark.asyncio
    async def test_oembed_filters_invalid_videos_in_fallback(
        self, mock_gemini_client, sample_session
    ):
        """Test that oEmbed verification filters out invalid videos in fallback mode."""
        YouTubeAgent._quota_exhausted = True
        agent = YouTubeAgent(mock_gemini_client)

        # Mock Gemini returning some videos (some valid, some not)
        gemini_videos = [
            VideoResource(
                url="https://www.youtube.com/watch?v=valid1",
                title="Valid Video 1",
                channel="Channel 1",
                thumbnail_url="",
            ),
            VideoResource(
                url="https://www.youtube.com/watch?v=invalid",
                title="Invalid Video",
                channel="Channel 2",
                thumbnail_url="",
            ),
            VideoResource(
                url="https://www.youtube.com/watch?v=valid2",
                title="Valid Video 2",
                channel="Channel 3",
                thumbnail_url="",
            ),
        ]

        with patch.object(
            agent, "_get_gemini_video_suggestions", new_callable=AsyncMock
        ) as mock_gemini:
            mock_gemini.return_value = gemini_videos

            # Mock oEmbed verification - only valid1 and valid2 exist
            async def mock_verify(url):
                if "valid1" in url:
                    return {"title": "Verified 1", "author_name": "Author 1"}
                elif "valid2" in url:
                    return {"title": "Verified 2", "author_name": "Author 2"}
                return None  # invalid video

            with patch.object(
                agent.youtube_service, "verify_video_exists", side_effect=mock_verify
            ):
                videos = await agent.find_videos(sample_session, max_videos=3)

                # Only the 2 valid videos should be returned
                assert len(videos) == 2
                assert videos[0].title == "Verified 1"
                assert videos[1].title == "Verified 2"

    @pytest.mark.asyncio
    async def test_api_builds_correct_search_query(self, mock_gemini_client, sample_session):
        """Test that API search query is built from session context."""
        agent = YouTubeAgent(mock_gemini_client)

        with patch.object(
            agent.youtube_service, "search_videos", new_callable=AsyncMock
        ) as mock_search:
            mock_search.return_value = []

            await agent.find_videos(sample_session, max_videos=3)

            # Check the query includes session title and key concepts
            call_args = mock_search.call_args
            query = call_args[1]["query"] if "query" in call_args[1] else call_args[0][0]
            assert "Introduction to Python" in query
            assert "tutorial" in query

    @pytest.mark.asyncio
    async def test_api_respects_language_parameter(self, mock_gemini_client):
        """Test that API search respects session language."""
        agent = YouTubeAgent(mock_gemini_client)

        session = ResearchedSession(
            outline_id="test_he",
            title="מבוא לפייתון",
            session_type=SessionType.CONCEPT,
            order=1,
            content="למד יסודות תכנות פייתון",
            key_concepts=["משתנים"],
            resources=[],
            exercises=[],
            language="he",
        )

        with patch.object(
            agent.youtube_service, "search_videos", new_callable=AsyncMock
        ) as mock_search:
            mock_search.return_value = []

            await agent.find_videos(session)

            # Check language parameter was passed
            call_args = mock_search.call_args
            assert call_args[1].get("language") == "he" or (
                len(call_args[0]) >= 3 and call_args[0][2] == "he"
            )
