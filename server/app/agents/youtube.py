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
            language=getattr(session, "language", "en") or "en",
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
