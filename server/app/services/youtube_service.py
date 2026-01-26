"""YouTube Data API v3 client service."""

import asyncio
from functools import partial
from typing import Any

import httpx
import structlog

from app.config import get_settings

logger = structlog.get_logger()

YOUTUBE_API_BASE = "https://www.googleapis.com/youtube/v3"
OEMBED_URL = "https://www.youtube.com/oembed"


class QuotaExhaustedError(Exception):
    """Raised when YouTube API quota is exhausted."""

    pass


class YouTubeService:
    """Service for interacting with YouTube Data API v3."""

    def __init__(self) -> None:
        self.settings = get_settings()
        self.logger = logger.bind(service="youtube")

    def _search_sync(
        self,
        query: str,
        max_results: int = 3,
        language: str = "en",
    ) -> list[dict[str, Any]]:
        """Synchronous YouTube search API call."""
        if not self.settings.youtube_api_key:
            raise ValueError("YouTube API key not configured")

        params = {
            "part": "snippet",
            "q": query,
            "type": "video",
            "maxResults": max_results,
            "videoDuration": "medium",  # 4-20 minutes
            "relevanceLanguage": language[:2],  # e.g., "en", "he"
            "key": self.settings.youtube_api_key,
        }

        with httpx.Client(timeout=10.0) as client:
            response = client.get(f"{YOUTUBE_API_BASE}/search", params=params)

            if response.status_code == 403:
                error_data = response.json()
                if "quotaExceeded" in str(error_data):
                    raise QuotaExhaustedError("YouTube API quota exhausted")
                raise Exception(f"YouTube API error: {error_data}")

            response.raise_for_status()
            return response.json().get("items", [])

    async def search_videos(
        self,
        query: str,
        max_results: int = 3,
        language: str = "en",
    ) -> list[dict[str, Any]]:
        """Search for videos using YouTube Data API v3.

        Args:
            query: Search query string
            max_results: Maximum number of results (default 3)
            language: ISO language code for relevance (default "en")

        Returns:
            List of video items from API response

        Raises:
            QuotaExhaustedError: When daily quota is exceeded
        """
        loop = asyncio.get_event_loop()
        return await loop.run_in_executor(
            None,
            partial(self._search_sync, query, max_results, language),
        )

    def _verify_video_sync(self, video_url: str) -> dict[str, Any] | None:
        """Verify a video exists using oEmbed API (synchronous)."""
        try:
            with httpx.Client(timeout=5.0) as client:
                response = client.get(
                    OEMBED_URL,
                    params={"url": video_url, "format": "json"},
                )
                if response.status_code == 200:
                    return response.json()
                return None
        except Exception:
            return None

    async def verify_video_exists(self, video_url: str) -> dict[str, Any] | None:
        """Verify a YouTube video exists using oEmbed.

        Args:
            video_url: Full YouTube video URL

        Returns:
            oEmbed data dict if video exists, None otherwise
        """
        loop = asyncio.get_event_loop()
        return await loop.run_in_executor(
            None,
            partial(self._verify_video_sync, video_url),
        )

    async def verify_videos_batch(
        self,
        video_urls: list[str],
    ) -> list[tuple[str, dict[str, Any] | None]]:
        """Verify multiple videos exist in parallel.

        Returns:
            List of (url, oembed_data) tuples. oembed_data is None if invalid.
        """
        tasks = [self.verify_video_exists(url) for url in video_urls]
        results = await asyncio.gather(*tasks)
        return list(zip(video_urls, results, strict=True))

    def _get_video_details_sync(
        self,
        video_ids: list[str],
    ) -> dict[str, dict[str, Any]]:
        """Synchronous call to get video details (statistics, contentDetails)."""
        if not self.settings.youtube_api_key:
            raise ValueError("YouTube API key not configured")

        if not video_ids:
            return {}

        # API accepts up to 50 video IDs per request
        params = {
            "part": "snippet,statistics,contentDetails",
            "id": ",".join(video_ids[:50]),
            "key": self.settings.youtube_api_key,
        }

        with httpx.Client(timeout=10.0) as client:
            response = client.get(f"{YOUTUBE_API_BASE}/videos", params=params)

            if response.status_code == 403:
                error_data = response.json()
                if "quotaExceeded" in str(error_data):
                    raise QuotaExhaustedError("YouTube API quota exhausted")
                raise Exception(f"YouTube API error: {error_data}")

            response.raise_for_status()
            items = response.json().get("items", [])

        # Build a dict keyed by video ID
        details = {}
        for item in items:
            video_id = item.get("id")
            if not video_id:
                continue

            snippet = item.get("snippet", {})
            statistics = item.get("statistics", {})
            content_details = item.get("contentDetails", {})

            details[video_id] = {
                "title": snippet.get("title", ""),
                "channel": snippet.get("channelTitle", ""),
                "description": snippet.get("description", ""),
                "thumbnail_url": snippet.get("thumbnails", {}).get("high", {}).get("url", ""),
                "published_at": snippet.get("publishedAt", ""),
                "view_count": int(statistics.get("viewCount", 0)),
                "like_count": int(statistics.get("likeCount", 0)),
                "duration_iso": content_details.get("duration", ""),  # ISO 8601 format
            }

        return details

    async def get_video_details(
        self,
        video_ids: list[str],
    ) -> dict[str, dict[str, Any]]:
        """Get detailed metadata for a list of video IDs.

        Args:
            video_ids: List of YouTube video IDs

        Returns:
            Dict mapping video_id to metadata dict containing:
            - title, channel, description, thumbnail_url
            - published_at (ISO timestamp)
            - view_count, like_count (integers)
            - duration_iso (ISO 8601 duration string)

        Raises:
            QuotaExhaustedError: When daily quota is exceeded
        """
        loop = asyncio.get_event_loop()
        return await loop.run_in_executor(
            None,
            partial(self._get_video_details_sync, video_ids),
        )

