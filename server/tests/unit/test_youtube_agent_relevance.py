"""Unit tests for YouTube agent relevance improvements."""

from unittest.mock import AsyncMock, MagicMock, patch

import pytest

from app.agents.state import ResearchedSession, SessionType, VideoResource
from app.agents.youtube import (
    QueryGenerationResponse,
    RerankResponse,
    SelectedVideo,
    YouTubeAgent,
)


@pytest.fixture
def mock_gemini_client():
    """Create a mock Gemini client."""
    client = MagicMock()
    # Mock the generate_structured method on the client wrapper, 
    # but strictly speaking strict mocking of the agent class is easier.
    return client


@pytest.fixture
def sample_session():
    """Create a sample session for testing."""
    return ResearchedSession(
        outline_id="test_001",
        title="Python Decorators",
        session_type=SessionType.CONCEPT,
        order=1,
        content="Learn how to use decorators in Python.",
        key_concepts=["decorators", "higher-order functions", "@wraps"],
        resources=[],
        exercises=[],
    )


class TestYouTubeAgentRelevance:
    """Tests for the new Candidate & Re-rank relevance logic."""

    @pytest.mark.asyncio
    async def test_generate_search_queries(self, mock_gemini_client, sample_session):
        """Test that _generate_search_queries calls Gemini and returns queries."""
        agent = YouTubeAgent(mock_gemini_client)
        
        # Mock generate_structured
        mock_response = QueryGenerationResponse(
            queries=[
                "python decorators tutorial",
                "advanced python decorators",
                "python @wraps explained"
            ]
        )
        
        with patch.object(
            agent, "generate_structured", new_callable=AsyncMock
        ) as mock_gen:
            mock_gen.return_value = mock_response
            
            queries = await agent._generate_search_queries(sample_session)
            
            mock_gen.assert_called_once()
            assert len(queries) == 3
            assert "python decorators tutorial" in queries
            assert "advanced python decorators" in queries

    @pytest.mark.asyncio
    async def test_fetch_candidate_videos(self, mock_gemini_client):
        """Test fetching and enriching candidate videos."""
        agent = YouTubeAgent(mock_gemini_client)
        
        # Mock search_videos to return different results for different queries
        async def mock_search(query, **kwargs):
            if "query1" in query:
                return [{"id": {"videoId": "v1"}, "snippet": {"title": "V1"}}]
            elif "query2" in query:
                return [{"id": {"videoId": "v2"}, "snippet": {"title": "V2"}}]
            return []

        # Mock get_video_details
        mock_details = {
            "v1": {
                "title": "Video 1 Full",
                "channel": "Channel 1",
                "description": "Desc 1",
                "thumbnail_url": "thumb1",
                "published_at": "2023-01-01",
                "view_count": 1000,
                "duration_iso": "PT10M",
            },
            "v2": {
                "title": "Video 2 Full",
                "channel": "Channel 2",
                "description": "Desc 2",
                "thumbnail_url": "thumb2",
                "published_at": "2023-01-02",
                "view_count": 2000,
                "duration_iso": "PT5M",
            }
        }

        with patch.object(
            agent.youtube_service, "search_videos", side_effect=mock_search
        ) as mock_search_svc:
            with patch.object(
                agent.youtube_service, "get_video_details", new_callable=AsyncMock
            ) as mock_get_details:
                mock_get_details.return_value = mock_details
                
                queries = ["query1", "query2"]
                candidates = await agent._fetch_candidate_videos(queries, language="en")
                
                assert mock_search_svc.call_count == 2
                mock_get_details.assert_called_once()
                
                assert len(candidates) == 2
                
                # Check enrichment and parsing
                c1 = next(c for c in candidates if c["video_id"] == "v1")
                assert c1["view_count"] == 1000
                assert c1["duration_minutes"] == 10
                
                c2 = next(c for c in candidates if c["video_id"] == "v2")
                assert c2["view_count"] == 2000
                assert c2["duration_minutes"] == 5

    @pytest.mark.asyncio
    async def test_rerank_videos(self, mock_gemini_client, sample_session):
        """Test re-ranking candidates using Gemini."""
        agent = YouTubeAgent(mock_gemini_client)
        
        candidates = [
            {"video_id": "v1", "title": "Bad Video", "channel": "C1", "view_count": 100, "duration_minutes": 2, "url": "u1", "thumbnail_url": "t1", "description": "d1"},
            {"video_id": "v2", "title": "Good Video", "channel": "C2", "view_count": 10000, "duration_minutes": 10, "url": "u2", "thumbnail_url": "t2", "description": "d2"},
            {"video_id": "v3", "title": "Ok Video", "channel": "C3", "view_count": 5000, "duration_minutes": 8, "url": "u3", "thumbnail_url": "t3", "description": "d3"},
        ]
        
        # Mock Gemini selecting the best video (index 1 -> v2)
        mock_response = RerankResponse(
            selected_videos=[
                SelectedVideo(index=1, reason="High quality"),
                SelectedVideo(index=2, reason="Decent backup"),
            ]
        )
        
        with patch.object(
            agent, "generate_structured", new_callable=AsyncMock
        ) as mock_gen:
            mock_gen.return_value = mock_response
            
            selected = await agent._rerank_videos(sample_session, candidates, max_videos=2)
            
            mock_gen.assert_called_once()
            assert len(selected) == 2
            assert selected[0].title == "Good Video"
            assert selected[1].title == "Ok Video"

    @pytest.mark.asyncio
    async def test_find_videos_fallback_flow(self, mock_gemini_client, sample_session):
        """Test full flow falls back to simple query if generation fails."""
        agent = YouTubeAgent(mock_gemini_client)
        
        # Mock query generation failure
        with patch.object(agent, "_generate_search_queries", new_callable=AsyncMock) as mock_gen_queries:
            mock_gen_queries.return_value = []  # Fail to generate
            
            # Mock candidate fetch to expect simple query
            with patch.object(agent, "_fetch_candidate_videos", new_callable=AsyncMock) as mock_fetch:
                mock_fetch.return_value = []
                
                await agent._find_videos_via_api(sample_session, max_videos=3)
                
                mock_gen_queries.assert_called_once()
                mock_fetch.assert_called_once()
                
                # Verify fallback query was used
                call_args = mock_fetch.call_args
                queries_arg = call_args[1]["queries"] if "queries" in call_args[1] else call_args[0]
                assert len(queries_arg) == 1
                assert sample_session.title in queries_arg[0]
