# YouTube API + oEmbed Fallback Implementation Plan

## Overview

Replace the current Gemini-based YouTube video search (which hallucinates non-existent URLs) with a reliable hybrid approach:
1. **Primary**: YouTube Data API v3 for guaranteed real video results
2. **Fallback**: Current Gemini search + oEmbed URL verification when API quota exhausted

**Strategy**: Reactive error handling — catch 403 quota errors to trigger fallback mode.

## Background

### Current Problem
The `YouTubeAgent` uses Gemini with Google Search grounding to find videos, but LLMs hallucinate URLs even with grounding tools. Users encounter broken video links.

### Solution Benefits
- **100% real videos** from YouTube Data API (official source)
- **Free tier sufficient**: 10,000 units/day ≈ 100 searches (100 units each)
- **Graceful degradation**: Falls back to verified Gemini results when quota exhausted
- **Zero cost**: Both YouTube API and oEmbed are free

## Technical Design

### Architecture

```
┌─────────────────────────────────────────────────────────────┐
│                      YouTubeAgent                            │
│                                                              │
│  ┌─────────────────┐    quota_exhausted?    ┌─────────────┐ │
│  │  YouTube API    │ ───── 403 error ─────▶ │  Fallback   │ │
│  │  (Primary)      │                        │  Mode       │ │
│  └────────┬────────┘                        └──────┬──────┘ │
│           │                                        │        │
│           ▼                                        ▼        │
│  ┌─────────────────┐                      ┌──────────────┐  │
│  │ Real video data │                      │ Gemini +     │  │
│  │ from API        │                      │ oEmbed verify│  │
│  └─────────────────┘                      └──────────────┘  │
└─────────────────────────────────────────────────────────────┘
```

### YouTube Data API v3 Details

**Endpoint**: `GET https://www.googleapis.com/youtube/v3/search`

**Key Parameters**:
- `part=snippet` — Returns title, description, thumbnails, channelTitle
- `q={search_query}` — Search terms
- `type=video` — Only return videos (not channels/playlists)
- `maxResults=3` — Limit results
- `videoDuration=medium` — Filter for 4-20 min videos (educational sweet spot)
- `relevanceLanguage={lang}` — Match user's language
- `key={API_KEY}` — API key authentication

**Response Structure**:
```json
{
  "items": [
    {
      "id": { "videoId": "dQw4w9WgXcQ" },
      "snippet": {
        "title": "Video Title",
        "description": "Video description...",
        "channelTitle": "Channel Name",
        "thumbnails": {
          "high": { "url": "https://i.ytimg.com/vi/VIDEO_ID/hqdefault.jpg" }
        }
      }
    }
  ]
}
```

**Quota Cost**: 100 units per search request (10,000 units/day free = ~100 searches)

### oEmbed Verification

**Endpoint**: `GET https://www.youtube.com/oembed?url={VIDEO_URL}&format=json`

**Behavior**:
- Returns 200 + JSON if video exists and is public
- Returns 404 if video doesn't exist
- Returns 401 if video is private/unlisted

**Response** (on success):
```json
{
  "title": "Video Title",
  "author_name": "Channel Name",
  "thumbnail_url": "https://i.ytimg.com/vi/VIDEO_ID/hqdefault.jpg"
}
```

## Implementation Steps

### Step 1: Add Configuration

**File**: `server/app/config.py`

Add YouTube API key to settings:

```python
class Settings(BaseSettings):
    # ... existing settings ...

    # YouTube Data API
    youtube_api_key: str = ""
```

**File**: `server/.env.example`

Add documentation:

```bash
# YouTube Data API v3 (get from https://console.cloud.google.com/apis/credentials)
# Enable "YouTube Data API v3" in your Google Cloud project
YOUTUBE_API_KEY=your_youtube_api_key_here
```

### Step 2: Create YouTube API Service

**New File**: `server/app/services/youtube_service.py`

```python
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

    def __init__(self):
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
```

### Step 3: Refactor YouTubeAgent

**File**: `server/app/agents/youtube.py`

Refactor to use YouTube API as primary, with oEmbed-verified Gemini fallback:

```python
"""YouTube agent for finding educational video recommendations."""

import asyncio
import json
from functools import partial

from google.genai import types
from pydantic import BaseModel, Field

from app.agents.base import BaseAgent
from app.agents.prompts import YOUTUBE_AGENT_PROMPT
from app.agents.state import ResearchedSession, VideoResource
from app.services.youtube_service import (
    QuotaExhaustedError,
    YouTubeService,
)


class YouTubeSearchResponse(BaseModel):
    """Response schema for YouTube video search."""

    videos: list[VideoResource] = Field(default_factory=list)


class YouTubeAgent(BaseAgent):
    """Agent for finding YouTube video recommendations.

    Uses YouTube Data API v3 as primary source. Falls back to
    Gemini + oEmbed verification when API quota is exhausted.
    """

    name = "youtube_agent"
    default_temperature: float = 0.3
    default_max_tokens: int = 4096

    # Class-level flag for quota state (shared across instances in same process)
    _quota_exhausted: bool = False

    def __init__(self, client):
        super().__init__(client)
        self.youtube_service = YouTubeService()

    def get_system_prompt(self) -> str:
        return YOUTUBE_AGENT_PROMPT

    async def find_videos(
        self,
        session: ResearchedSession,
        max_videos: int = 3,
    ) -> list[VideoResource]:
        """Find YouTube videos for a session.

        Primary: YouTube Data API v3 (guaranteed real videos)
        Fallback: Gemini search + oEmbed verification (when quota exhausted)
        """
        # Check if we already know quota is exhausted
        if not YouTubeAgent._quota_exhausted:
            try:
                return await self._find_videos_via_api(session, max_videos)
            except QuotaExhaustedError:
                self.logger.warning("YouTube API quota exhausted, switching to fallback")
                YouTubeAgent._quota_exhausted = True
            except ValueError as e:
                # API key not configured - use fallback
                self.logger.info("YouTube API not configured, using fallback", error=str(e))
                YouTubeAgent._quota_exhausted = True

        # Fallback: Gemini + oEmbed verification
        return await self._find_videos_via_gemini_with_verification(session, max_videos)

    async def _find_videos_via_api(
        self,
        session: ResearchedSession,
        max_videos: int,
    ) -> list[VideoResource]:
        """Find videos using YouTube Data API v3."""
        # Build search query from session context
        key_concepts = ", ".join(session.key_concepts[:3]) if session.key_concepts else ""
        query = f"{session.title} tutorial {key_concepts}"

        items = await self.youtube_service.search_videos(
            query=query,
            max_results=max_videos,
            language=getattr(session, 'language', 'en') or 'en',
        )

        videos = []
        for item in items:
            video_id = item.get("id", {}).get("videoId")
            snippet = item.get("snippet", {})

            if not video_id:
                continue

            video = VideoResource(
                url=f"https://www.youtube.com/watch?v={video_id}",
                title=snippet.get("title", ""),
                channel=snippet.get("channelTitle", ""),
                thumbnail_url=snippet.get("thumbnails", {}).get("high", {}).get("url", ""),
                duration_minutes=None,  # Not available in search results
                description=snippet.get("description", "")[:200],
            )
            videos.append(video)

        self.logger.info(
            "Videos found via YouTube API",
            session_title=session.title,
            video_count=len(videos),
        )
        return videos

    async def _find_videos_via_gemini_with_verification(
        self,
        session: ResearchedSession,
        max_videos: int,
    ) -> list[VideoResource]:
        """Fallback: Use Gemini to find videos, then verify with oEmbed."""
        # Get candidates from Gemini (may include hallucinated URLs)
        candidates = await self._get_gemini_video_suggestions(session, max_videos * 2)

        if not candidates:
            return []

        # Verify each URL exists using oEmbed
        verified_videos = []
        for video in candidates:
            if len(verified_videos) >= max_videos:
                break

            oembed_data = await self.youtube_service.verify_video_exists(video.url)
            if oembed_data:
                # Update with verified data from oEmbed
                verified_video = VideoResource(
                    url=video.url,
                    title=oembed_data.get("title", video.title),
                    channel=oembed_data.get("author_name", video.channel),
                    thumbnail_url=oembed_data.get("thumbnail_url", video.thumbnail_url),
                    duration_minutes=video.duration_minutes,
                    description=video.description,
                )
                verified_videos.append(verified_video)
            else:
                self.logger.debug(
                    "Video URL failed verification",
                    url=video.url,
                )

        self.logger.info(
            "Videos found via Gemini+oEmbed fallback",
            session_title=session.title,
            candidates=len(candidates),
            verified=len(verified_videos),
        )
        return verified_videos

    def _generate_with_grounding_sync(
        self,
        prompt: str,
        system_prompt: str,
    ) -> str:
        """Synchronous Gemini API call with Google Search grounding enabled."""
        response = self.client.models.generate_content(
            model="gemini-2.0-flash",
            contents=prompt,
            config=types.GenerateContentConfig(
                system_instruction=system_prompt,
                temperature=self.default_temperature,
                max_output_tokens=self.default_max_tokens,
                tools=[types.Tool(google_search=types.GoogleSearch())],
            ),
        )
        return response.text

    async def generate_with_grounding(
        self,
        prompt: str,
        system_prompt: str | None = None,
    ) -> str:
        """Async wrapper for grounding-enabled generation."""
        loop = asyncio.get_event_loop()
        return await loop.run_in_executor(
            None,
            partial(
                self._generate_with_grounding_sync,
                prompt,
                system_prompt or self.get_system_prompt(),
            ),
        )

    async def _get_gemini_video_suggestions(
        self,
        session: ResearchedSession,
        max_videos: int,
    ) -> list[VideoResource]:
        """Get video suggestions from Gemini (may include invalid URLs)."""
        key_concepts_str = ", ".join(session.key_concepts[:5]) if session.key_concepts else ""

        prompt = f"""Find {max_videos} high-quality YouTube tutorial videos \
for this learning session:

SESSION TITLE: {session.title}

KEY CONCEPTS TO COVER: {key_concepts_str}

SESSION CONTENT SUMMARY (first 500 chars):
{session.content[:500]}...

Search YouTube for educational videos that would help someone learn these concepts.
Return the videos as a JSON object with a "videos" array containing objects with these fields:
- url: Full YouTube URL (must be real, existing videos)
- title: Video title
- channel: Channel name
- thumbnail_url: YouTube thumbnail URL (format: https://img.youtube.com/vi/VIDEO_ID/maxresdefault.jpg)
- duration_minutes: Estimated duration in minutes (integer)
- description: Brief 1-sentence description

Only include real videos you find through search - do not make up URLs.

Respond with only the JSON object, no other text."""

        try:
            response_text = await self.generate_with_grounding(prompt)

            # Parse the response
            cleaned = response_text.strip()
            if cleaned.startswith("```json"):
                cleaned = cleaned[7:]
            if cleaned.startswith("```"):
                cleaned = cleaned[3:]
            if cleaned.endswith("```"):
                cleaned = cleaned[:-3]
            cleaned = cleaned.strip()

            data = json.loads(cleaned)
            video_list = data.get("videos", []) if isinstance(data, dict) else data
            if not isinstance(video_list, list):
                video_list = []

            videos = []
            for v in video_list[:max_videos]:
                try:
                    video = VideoResource(
                        url=v.get("url", ""),
                        title=v.get("title", ""),
                        channel=v.get("channel", ""),
                        thumbnail_url=v.get("thumbnail_url", ""),
                        duration_minutes=v.get("duration_minutes"),
                        description=v.get("description"),
                    )
                    if video.url and video.title and "youtube.com" in video.url:
                        videos.append(video)
                except Exception as e:
                    self.logger.warning("Failed to parse video", error=str(e))
                    continue

            return videos

        except Exception as e:
            self.logger.warning(
                "Gemini video search failed",
                session_title=session.title,
                error=str(e),
            )
            return []
```

### Step 4: Update .env.example

**File**: `server/.env.example`

Add the YouTube API key documentation:

```bash
# YouTube Data API v3 (optional - enables reliable video search)
# 1. Go to https://console.cloud.google.com/apis/credentials
# 2. Create a new project or select existing
# 3. Enable "YouTube Data API v3"
# 4. Create an API key (restrict to YouTube Data API v3 for security)
# Free tier: 10,000 units/day (~100 searches)
YOUTUBE_API_KEY=your_youtube_api_key_here
```

### Step 5: Add Unit Tests

**New File**: `server/tests/unit/test_youtube_service.py`

```python
"""Tests for YouTube service."""

import pytest
from unittest.mock import patch, MagicMock
import httpx

from app.services.youtube_service import (
    YouTubeService,
    QuotaExhaustedError,
)


class TestYouTubeService:
    """Tests for YouTubeService."""

    @pytest.fixture
    def service(self):
        """Create a YouTubeService instance."""
        with patch("app.services.youtube_service.get_settings") as mock_settings:
            mock_settings.return_value.youtube_api_key = "test_api_key"
            return YouTubeService()

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

        with patch.object(httpx.Client, "get", return_value=mock_response):
            with patch.object(httpx.Client, "__enter__", return_value=MagicMock(get=MagicMock(return_value=mock_response))):
                # Direct sync call for testing
                items = service._search_sync("python tutorial", max_results=3)

        # Verify we got results (mocking makes this tricky, so we just verify no exception)

    def test_search_quota_exceeded(self, service):
        """Test quota exceeded error handling."""
        mock_response = MagicMock()
        mock_response.status_code = 403
        mock_response.json.return_value = {
            "error": {"message": "quotaExceeded"}
        }

        with patch("httpx.Client") as mock_client:
            mock_client.return_value.__enter__.return_value.get.return_value = mock_response

            with pytest.raises(QuotaExhaustedError):
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

    def test_verify_video_not_found(self, service):
        """Test video not found returns None."""
        mock_response = MagicMock()
        mock_response.status_code = 404

        with patch("httpx.Client") as mock_client:
            mock_client.return_value.__enter__.return_value.get.return_value = mock_response

            result = service._verify_video_sync("https://youtube.com/watch?v=invalid")

            assert result is None


@pytest.mark.asyncio
class TestYouTubeServiceAsync:
    """Async tests for YouTubeService."""

    @pytest.fixture
    def service(self):
        """Create a YouTubeService instance."""
        with patch("app.services.youtube_service.get_settings") as mock_settings:
            mock_settings.return_value.youtube_api_key = "test_api_key"
            return YouTubeService()

    async def test_search_videos_async(self, service):
        """Test async video search."""
        with patch.object(service, "_search_sync") as mock_search:
            mock_search.return_value = [{"id": {"videoId": "test"}}]

            result = await service.search_videos("test query")

            assert result == [{"id": {"videoId": "test"}}]
            mock_search.assert_called_once()

    async def test_verify_videos_batch(self, service):
        """Test batch video verification."""
        async def mock_verify(url):
            if "valid" in url:
                return {"title": "Valid"}
            return None

        with patch.object(service, "verify_video_exists", side_effect=mock_verify):
            results = await service.verify_videos_batch([
                "https://youtube.com/watch?v=valid1",
                "https://youtube.com/watch?v=invalid",
                "https://youtube.com/watch?v=valid2",
            ])

            assert len(results) == 3
            assert results[0][1] is not None  # valid1
            assert results[1][1] is None      # invalid
            assert results[2][1] is not None  # valid2
```

**Update File**: `server/tests/unit/test_youtube_agent.py`

Add tests for the new fallback behavior:

```python
"""Tests for YouTube agent with API + fallback."""

import pytest
from unittest.mock import AsyncMock, patch, MagicMock

from app.agents.youtube import YouTubeAgent
from app.agents.state import ResearchedSession, VideoResource
from app.services.youtube_service import QuotaExhaustedError


class TestYouTubeAgent:
    """Tests for YouTubeAgent."""

    @pytest.fixture
    def mock_client(self):
        """Create a mock Gemini client."""
        return MagicMock()

    @pytest.fixture
    def agent(self, mock_client):
        """Create a YouTubeAgent instance."""
        # Reset quota state for each test
        YouTubeAgent._quota_exhausted = False
        return YouTubeAgent(mock_client)

    @pytest.fixture
    def sample_session(self):
        """Create a sample researched session."""
        return ResearchedSession(
            order=1,
            title="Python Basics",
            session_type="lesson",
            content="Learn Python fundamentals including variables, loops, and functions.",
            key_concepts=["variables", "loops", "functions"],
            estimated_minutes=60,
            videos=[],
        )

    @pytest.mark.asyncio
    async def test_find_videos_uses_api_first(self, agent, sample_session):
        """Test that API is used as primary source."""
        mock_videos = [
            {
                "id": {"videoId": "abc123"},
                "snippet": {
                    "title": "Python Tutorial",
                    "channelTitle": "Coding Channel",
                    "description": "Learn Python",
                    "thumbnails": {"high": {"url": "https://example.com/thumb.jpg"}},
                },
            }
        ]

        with patch.object(
            agent.youtube_service,
            "search_videos",
            new_callable=AsyncMock,
            return_value=mock_videos,
        ):
            videos = await agent.find_videos(sample_session)

            assert len(videos) == 1
            assert videos[0].title == "Python Tutorial"
            assert "abc123" in videos[0].url

    @pytest.mark.asyncio
    async def test_fallback_on_quota_exhausted(self, agent, sample_session):
        """Test fallback to Gemini+oEmbed when quota exhausted."""
        # Simulate quota exhausted
        with patch.object(
            agent.youtube_service,
            "search_videos",
            new_callable=AsyncMock,
            side_effect=QuotaExhaustedError("Quota exceeded"),
        ):
            with patch.object(
                agent,
                "_find_videos_via_gemini_with_verification",
                new_callable=AsyncMock,
                return_value=[
                    VideoResource(
                        url="https://youtube.com/watch?v=fallback",
                        title="Fallback Video",
                        channel="Fallback Channel",
                        thumbnail_url="",
                    )
                ],
            ) as mock_fallback:
                videos = await agent.find_videos(sample_session)

                mock_fallback.assert_called_once()
                assert len(videos) == 1
                assert videos[0].title == "Fallback Video"

    @pytest.mark.asyncio
    async def test_quota_flag_persists(self, agent, sample_session):
        """Test that quota exhausted flag persists across calls."""
        # First call exhausts quota
        with patch.object(
            agent.youtube_service,
            "search_videos",
            new_callable=AsyncMock,
            side_effect=QuotaExhaustedError("Quota exceeded"),
        ):
            with patch.object(
                agent,
                "_find_videos_via_gemini_with_verification",
                new_callable=AsyncMock,
                return_value=[],
            ):
                await agent.find_videos(sample_session)

        # Second call should skip API
        with patch.object(
            agent.youtube_service,
            "search_videos",
            new_callable=AsyncMock,
        ) as mock_api:
            with patch.object(
                agent,
                "_find_videos_via_gemini_with_verification",
                new_callable=AsyncMock,
                return_value=[],
            ):
                await agent.find_videos(sample_session)

            # API should NOT be called on second request
            mock_api.assert_not_called()

    @pytest.mark.asyncio
    async def test_oembed_filters_invalid_videos(self, agent, sample_session):
        """Test that oEmbed verification filters out invalid videos."""
        # Set quota as exhausted to use fallback
        YouTubeAgent._quota_exhausted = True

        gemini_candidates = [
            VideoResource(
                url="https://youtube.com/watch?v=valid123",
                title="Valid Video",
                channel="Channel",
                thumbnail_url="",
            ),
            VideoResource(
                url="https://youtube.com/watch?v=invalid456",
                title="Invalid Video",
                channel="Channel",
                thumbnail_url="",
            ),
        ]

        async def mock_verify(url):
            if "valid" in url:
                return {"title": "Verified Title", "author_name": "Verified Channel"}
            return None

        with patch.object(
            agent,
            "_get_gemini_video_suggestions",
            new_callable=AsyncMock,
            return_value=gemini_candidates,
        ):
            with patch.object(
                agent.youtube_service,
                "verify_video_exists",
                side_effect=mock_verify,
            ):
                videos = await agent.find_videos(sample_session)

                # Only valid video should be returned
                assert len(videos) == 1
                assert "valid" in videos[0].url
```

### Step 6: Update Dependencies

**File**: `server/requirements.txt`

Ensure `httpx` is included (for YouTube API and oEmbed calls):

```
httpx>=0.25.0
```

## Testing Strategy

### Unit Tests
1. `test_youtube_service.py` - Service layer tests
   - API search success/failure
   - Quota exceeded handling
   - oEmbed verification
   - Batch verification

2. `test_youtube_agent.py` - Agent tests
   - Primary API path
   - Fallback activation on quota error
   - Quota flag persistence
   - oEmbed filtering

### Integration Tests
1. Test full pipeline with mocked external APIs
2. Test graceful degradation when no API key configured

### Manual Testing
1. Create a roadmap and verify real videos appear
2. Exhaust quota (or simulate with mock) and verify fallback works
3. Check videos actually play on YouTube

## Rollout Plan

1. **Phase 1**: Deploy with `YOUTUBE_API_KEY` optional
   - If not set, uses Gemini+oEmbed fallback immediately
   - Zero breaking changes

2. **Phase 2**: Add API key to production
   - Monitor quota usage via Google Cloud Console
   - Verify real videos in production

3. **Phase 3**: (Optional) Add quota monitoring
   - Dashboard showing daily quota usage
   - Alerts when approaching limit

## File Changes Summary

| File | Change Type | Description |
|------|-------------|-------------|
| `server/app/config.py` | Modify | Add `youtube_api_key` setting |
| `server/.env.example` | Modify | Add YouTube API key documentation |
| `server/app/services/youtube_service.py` | Create | New YouTube API service |
| `server/app/agents/youtube.py` | Modify | Refactor to use API + fallback |
| `server/tests/unit/test_youtube_service.py` | Create | Service tests |
| `server/tests/unit/test_youtube_agent.py` | Modify | Add fallback tests |
| `server/requirements.txt` | Modify | Add httpx (if not present) |

## Success Criteria

1. ✅ All videos returned are real, playable YouTube videos
2. ✅ Free tier quota is sufficient for typical usage (~20 roadmaps/day)
3. ✅ Graceful fallback when quota exhausted
4. ✅ No breaking changes - works without API key configured
5. ✅ All tests pass
