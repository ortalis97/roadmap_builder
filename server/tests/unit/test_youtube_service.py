"""Tests for YouTube service."""

from unittest.mock import MagicMock, patch

import pytest

from app.services.youtube_service import (
    QuotaExhaustedError,
    YouTubeService,
)


class TestYouTubeService:
    """Tests for YouTubeService."""

    @pytest.fixture
    def service(self):
        """Create a YouTubeService instance."""
        with patch("app.services.youtube_service.get_settings") as mock_settings:
            mock_settings.return_value.youtube_api_key = "test_api_key"
            yield YouTubeService()

    def test_search_sync_success(self, service):
        """Test successful video search."""
        mock_response = MagicMock()
        mock_response.status_code = 200
        mock_response.json.return_value = {
            "items": [
                {
                    "id": {"videoId": "abc123"},
                    "snippet": {
                        "title": "Test Video",
                        "channelTitle": "Test Channel",
                        "description": "Test description",
                        "thumbnails": {"high": {"url": "https://example.com/thumb.jpg"}},
                    },
                }
            ]
        }

        with patch("httpx.Client") as mock_client:
            mock_client.return_value.__enter__.return_value.get.return_value = mock_response

            items = service._search_sync("python tutorial", max_results=3)

            assert len(items) == 1
            assert items[0]["id"]["videoId"] == "abc123"
            assert items[0]["snippet"]["title"] == "Test Video"

    def test_search_quota_exceeded(self, service):
        """Test quota exceeded error handling."""
        mock_response = MagicMock()
        mock_response.status_code = 403
        mock_response.json.return_value = {"error": {"message": "quotaExceeded"}}

        with patch("httpx.Client") as mock_client:
            mock_client.return_value.__enter__.return_value.get.return_value = mock_response

            with pytest.raises(QuotaExhaustedError):
                service._search_sync("test query")

    def test_search_no_api_key(self):
        """Test error when API key not configured."""
        with patch("app.services.youtube_service.get_settings") as mock_settings:
            mock_settings.return_value.youtube_api_key = ""
            service = YouTubeService()

            with pytest.raises(ValueError, match="YouTube API key not configured"):
                service._search_sync("test query")

    def test_verify_video_exists_success(self, service):
        """Test successful video verification."""
        mock_response = MagicMock()
        mock_response.status_code = 200
        mock_response.json.return_value = {
            "title": "Real Video",
            "author_name": "Real Channel",
            "thumbnail_url": "https://example.com/thumb.jpg",
        }

        with patch("httpx.Client") as mock_client:
            mock_client.return_value.__enter__.return_value.get.return_value = mock_response

            result = service._verify_video_sync("https://youtube.com/watch?v=abc123")

            assert result is not None
            assert result["title"] == "Real Video"
            assert result["author_name"] == "Real Channel"

    def test_verify_video_not_found(self, service):
        """Test video not found returns None."""
        mock_response = MagicMock()
        mock_response.status_code = 404

        with patch("httpx.Client") as mock_client:
            mock_client.return_value.__enter__.return_value.get.return_value = mock_response

            result = service._verify_video_sync("https://youtube.com/watch?v=invalid")

            assert result is None

    def test_verify_video_exception_returns_none(self, service):
        """Test that exceptions during verification return None."""
        with patch("httpx.Client") as mock_client:
            mock_client.return_value.__enter__.return_value.get.side_effect = Exception(
                "Network error"
            )

            result = service._verify_video_sync("https://youtube.com/watch?v=abc123")

            assert result is None


@pytest.mark.asyncio
class TestYouTubeServiceAsync:
    """Async tests for YouTubeService."""

    @pytest.fixture
    def service(self):
        """Create a YouTubeService instance."""
        with patch("app.services.youtube_service.get_settings") as mock_settings:
            mock_settings.return_value.youtube_api_key = "test_api_key"
            yield YouTubeService()

    async def test_search_videos_async(self, service):
        """Test async video search."""
        with patch.object(service, "_search_sync") as mock_search:
            mock_search.return_value = [{"id": {"videoId": "test"}}]

            result = await service.search_videos("test query")

            assert result == [{"id": {"videoId": "test"}}]
            mock_search.assert_called_once_with("test query", 3, "en")

    async def test_search_videos_with_language(self, service):
        """Test async video search with language parameter."""
        with patch.object(service, "_search_sync") as mock_search:
            mock_search.return_value = []

            await service.search_videos("test query", max_results=5, language="he")

            mock_search.assert_called_once_with("test query", 5, "he")

    async def test_verify_video_exists_async(self, service):
        """Test async video verification."""
        with patch.object(service, "_verify_video_sync") as mock_verify:
            mock_verify.return_value = {"title": "Test"}

            result = await service.verify_video_exists("https://youtube.com/watch?v=test")

            assert result == {"title": "Test"}
            mock_verify.assert_called_once()

    async def test_verify_videos_batch(self, service):
        """Test batch video verification."""

        async def mock_verify(url):
            if "valid1" in url or "valid2" in url:
                return {"title": "Valid"}
            return None

        with patch.object(service, "verify_video_exists", side_effect=mock_verify):
            results = await service.verify_videos_batch(
                [
                    "https://youtube.com/watch?v=valid1",
                    "https://youtube.com/watch?v=notfound",
                    "https://youtube.com/watch?v=valid2",
                ]
            )

            assert len(results) == 3
            assert results[0][0] == "https://youtube.com/watch?v=valid1"
            assert results[0][1] is not None
            assert results[1][0] == "https://youtube.com/watch?v=notfound"
            assert results[1][1] is None
            assert results[2][0] == "https://youtube.com/watch?v=valid2"
            assert results[2][1] is not None
