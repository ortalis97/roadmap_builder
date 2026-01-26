"""YouTube agent for finding educational video recommendations."""

import asyncio
import json
import re
from functools import partial

from google.genai import types
from pydantic import BaseModel, Field

from app.agents.base import BaseAgent
from app.agents.prompts import (
    YOUTUBE_AGENT_PROMPT,
    YOUTUBE_QUERY_GENERATION_PROMPT,
    YOUTUBE_RERANK_PROMPT,
)
from app.agents.state import ResearchedSession, VideoResource
from app.model_config import get_model_config
from app.services.youtube_service import (
    QuotaExhaustedError,
    YouTubeService,
)


class YouTubeSearchResponse(BaseModel):
    """Response schema for YouTube video search."""

    videos: list[VideoResource] = Field(default_factory=list)


class QueryGenerationResponse(BaseModel):
    """Response schema for query generation."""

    queries: list[str] = Field(
        description="List of 3-5 diverse YouTube search queries"
    )


class SelectedVideo(BaseModel):
    """A single selected video with reason."""

    index: int = Field(description="0-based index of the selected video")
    reason: str = Field(description="Brief reason why this video was selected")


class RerankResponse(BaseModel):
    """Response schema for video re-ranking."""

    selected_videos: list[SelectedVideo] = Field(
        description="Top 3 selected videos ordered by relevance"
    )


class YouTubeAgent(BaseAgent):
    """Agent for finding YouTube video recommendations.

    Uses YouTube Data API v3 as primary source. Falls back to
    Gemini + oEmbed verification when API quota is exhausted.
    """

    name = "youtube_agent"
    model_config_key = "youtube_query"  # Default for query generation

    # Class-level flag for quota state (shared across instances in same process)
    _quota_exhausted: bool = False

    def __init__(self, client):
        super().__init__(client)
        self.youtube_service = YouTubeService()
        # Load configs for different operations
        self._query_config = get_model_config("youtube_query")
        self._rerank_config = get_model_config("youtube_rerank")
        self._grounding_config = get_model_config("youtube_grounding")

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
        """Find videos using YouTube Data API v3 with candidate & re-rank pattern.

        1. Generate multiple search queries using Gemini
        2. Fetch candidate videos from all queries
        3. Enrich with metadata (view count, duration)
        4. Re-rank using Gemini to select the best matches
        """
        # Step 1: Generate diverse search queries
        queries = await self._generate_search_queries(session)
        if not queries:
            # Fallback to simple query if generation fails
            key_concepts = ", ".join(session.key_concepts[:3]) if session.key_concepts else ""
            queries = [f"{session.title} tutorial {key_concepts}"]

        self.logger.info(
            "Generated search queries",
            session_title=session.title,
            queries=queries,
        )

        # Step 2: Fetch candidate videos from all queries
        candidates = await self._fetch_candidate_videos(
            queries=queries,
            language=getattr(session, "language", "en") or "en",
        )

        if not candidates:
            self.logger.warning(
                "No candidate videos found",
                session_title=session.title,
            )
            return []

        self.logger.info(
            "Candidate videos fetched",
            session_title=session.title,
            candidate_count=len(candidates),
        )

        # Step 3: Re-rank and select top videos
        selected_videos = await self._rerank_videos(
            session=session,
            candidates=candidates,
            max_videos=max_videos,
        )

        self.logger.info(
            "Videos selected via re-ranking",
            session_title=session.title,
            video_count=len(selected_videos),
        )
        return selected_videos

    async def _generate_search_queries(
        self,
        session: ResearchedSession,
    ) -> list[str]:
        """Use Gemini to generate diverse search queries for the session."""
        key_concepts_str = ", ".join(session.key_concepts[:5]) if session.key_concepts else ""

        prompt = f"""Generate YouTube search queries for this learning session:

SESSION TITLE: {session.title}

KEY CONCEPTS: {key_concepts_str}

SESSION CONTENT (first 300 chars):
{session.content[:300]}...

Generate 3-5 diverse search queries to find the best tutorial videos."""

        try:
            response = await self.generate_structured(
                prompt=prompt,
                response_model=QueryGenerationResponse,
                system_prompt=YOUTUBE_QUERY_GENERATION_PROMPT,
            )
            return response.queries[:5]

        except Exception as e:
            self.logger.warning(
                "Failed to generate search queries",
                error=str(e),
            )
            return []

    async def _fetch_candidate_videos(
        self,
        queries: list[str],
        language: str,
        max_per_query: int = 5,
    ) -> list[dict]:
        """Fetch candidate videos from multiple queries and enrich with metadata.

        Returns a list of dicts with video info including view counts.
        """
        # Run all searches in parallel
        search_tasks = [
            self.youtube_service.search_videos(
                query=query,
                max_results=max_per_query,
                language=language,
            )
            for query in queries
        ]
        search_results = await asyncio.gather(*search_tasks, return_exceptions=True)

        # Collect unique video IDs
        seen_ids = set()
        raw_candidates = []

        for result in search_results:
            if isinstance(result, Exception):
                if isinstance(result, QuotaExhaustedError) or "quota" in str(result).lower():
                    raise QuotaExhaustedError("YouTube API quota exhausted")
                if isinstance(result, ValueError):
                     raise result
                self.logger.warning("Search query failed", error=str(result))
                continue
            for item in result:
                video_id = item.get("id", {}).get("videoId")
                if video_id and video_id not in seen_ids:
                    seen_ids.add(video_id)
                    raw_candidates.append({
                        "video_id": video_id,
                        "snippet": item.get("snippet", {}),
                    })

        if not raw_candidates:
            return []

        # Fetch detailed metadata for all candidates
        video_ids = [c["video_id"] for c in raw_candidates]
        try:
            details = await self.youtube_service.get_video_details(video_ids)
        except QuotaExhaustedError:
            raise
        except Exception as e:
            self.logger.warning("Failed to fetch video details", error=str(e))
            details = {}

        # Combine search results with details
        candidates = []
        for raw in raw_candidates:
            video_id = raw["video_id"]
            snippet = raw["snippet"]
            detail = details.get(video_id, {})

            # Parse ISO 8601 duration to minutes
            duration_iso = detail.get("duration_iso", "")
            duration_minutes = self._parse_iso_duration(duration_iso)

            candidates.append({
                "video_id": video_id,
                "url": f"https://www.youtube.com/watch?v={video_id}",
                "title": detail.get("title") or snippet.get("title", ""),
                "channel": detail.get("channel") or snippet.get("channelTitle", ""),
                "description": (detail.get("description") or snippet.get("description", ""))[:300],
                "thumbnail_url": detail.get("thumbnail_url") or snippet.get("thumbnails", {}).get("high", {}).get("url", ""),
                "view_count": detail.get("view_count", 0),
                "published_at": detail.get("published_at", ""),
                "duration_minutes": duration_minutes,
            })

        return candidates

    def _parse_iso_duration(self, duration_iso: str) -> int | None:
        """Parse ISO 8601 duration (PT1H2M3S) to minutes."""
        if not duration_iso:
            return None
        try:
            match = re.match(r"PT(?:(\d+)H)?(?:(\d+)M)?(?:(\d+)S)?", duration_iso)
            if match:
                hours = int(match.group(1) or 0)
                minutes = int(match.group(2) or 0)
                seconds = int(match.group(3) or 0)
                return hours * 60 + minutes + (1 if seconds >= 30 else 0)
        except Exception:
            pass
        return None

    async def _rerank_videos(
        self,
        session: ResearchedSession,
        candidates: list[dict],
        max_videos: int,
    ) -> list[VideoResource]:
        """Use Gemini to re-rank candidates and select the best matches."""
        if len(candidates) <= max_videos:
            # No need to re-rank if we have fewer candidates than requested
            return [
                VideoResource(
                    url=c["url"],
                    title=c["title"],
                    channel=c["channel"],
                    thumbnail_url=c["thumbnail_url"],
                    duration_minutes=c["duration_minutes"],
                    description=c["description"],
                )
                for c in candidates
            ]

        # Format candidates for the prompt
        key_concepts_str = ", ".join(session.key_concepts[:5]) if session.key_concepts else ""
        candidates_text = "\n".join([
            f"[{i}] \"{c['title']}\" by {c['channel']} "
            f"({c['view_count']:,} views, {c['duration_minutes'] or '?'} min)\n"
            f"    Description: {c['description'][:150]}..."
            for i, c in enumerate(candidates)
        ])

        prompt = f"""Select the {max_videos} best videos for this learning session:

SESSION TITLE: {session.title}

KEY CONCEPTS TO LEARN: {key_concepts_str}

CANDIDATE VIDEOS:
{candidates_text}

Select the videos that will best help a learner understand the key concepts."""

        try:
            response = await self.generate_structured(
                prompt=prompt,
                response_model=RerankResponse,
                system_prompt=YOUTUBE_RERANK_PROMPT,
            )

            # Extract selected videos by index
            result = []
            for item in response.selected_videos[:max_videos]:
                idx = item.index
                if 0 <= idx < len(candidates):
                    c = candidates[idx]
                    result.append(VideoResource(
                        url=c["url"],
                        title=c["title"],
                        channel=c["channel"],
                        thumbnail_url=c["thumbnail_url"],
                        duration_minutes=c["duration_minutes"],
                        description=c["description"],
                    ))

            if result:
                return result

        except Exception as e:
            self.logger.warning(
                "Re-ranking failed, using top candidates by view count",
                error=str(e),
            )

        # Fallback: return top candidates by view count
        sorted_candidates = sorted(
            candidates,
            key=lambda c: c.get("view_count", 0),
            reverse=True,
        )
        return [
            VideoResource(
                url=c["url"],
                title=c["title"],
                channel=c["channel"],
                thumbnail_url=c["thumbnail_url"],
                duration_minutes=c["duration_minutes"],
                description=c["description"],
            )
            for c in sorted_candidates[:max_videos]
        ]

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
        config = self._grounding_config
        response = self.client.models.generate_content(
            model=config.model.value,
            contents=prompt,
            config=types.GenerateContentConfig(
                system_instruction=system_prompt,
                temperature=config.temperature,
                max_output_tokens=config.max_tokens,
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
