"""YouTube agent for finding educational video recommendations."""

import asyncio
import json
from functools import partial

from google.genai import types
from pydantic import BaseModel, Field

from app.agents.base import BaseAgent
from app.agents.prompts import YOUTUBE_AGENT_PROMPT
from app.agents.state import ResearchedSession, VideoResource


class YouTubeSearchResponse(BaseModel):
    """Response schema for YouTube video search."""

    videos: list[VideoResource] = Field(default_factory=list)


class YouTubeAgent(BaseAgent):
    """Agent for finding YouTube video recommendations using Google Search Grounding."""

    name = "youtube_agent"
    default_temperature: float = 0.3  # Lower for factual search results
    default_max_tokens: int = 4096

    def get_system_prompt(self) -> str:
        return YOUTUBE_AGENT_PROMPT

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

    async def find_videos(
        self,
        session: ResearchedSession,
        max_videos: int = 3,
    ) -> list[VideoResource]:
        """Find YouTube videos for a session using Google Search grounding.

        Args:
            session: The researched session to find videos for
            max_videos: Maximum number of videos to return (default 3)

        Returns:
            List of VideoResource objects, empty if none found or on error
        """
        # Build search context from session
        key_concepts_str = ", ".join(session.key_concepts[:5]) if session.key_concepts else ""

        prompt = f"""Find {max_videos} high-quality YouTube tutorial videos \
for this learning session:

SESSION TITLE: {session.title}

KEY CONCEPTS TO COVER: {key_concepts_str}

SESSION CONTENT SUMMARY (first 500 chars):
{session.content[:500]}...

Search YouTube for educational videos that would help someone learn these concepts.
Return the videos as a JSON object with a "videos" array containing objects with these fields:
- url: Full YouTube URL
- title: Video title
- channel: Channel name
- thumbnail_url: YouTube thumbnail URL (format: https://img.youtube.com/vi/VIDEO_ID/maxresdefault.jpg)
- duration_minutes: Estimated duration in minutes (integer)
- description: Brief 1-sentence description

If you cannot find {max_videos} quality videos, return fewer or an empty array.
Only include real videos you find through search - do not make up URLs.

Respond with only the JSON object, no other text."""

        try:
            response_text = await self.generate_with_grounding(prompt)

            # Parse the response - it may have markdown code blocks
            cleaned = response_text.strip()
            if cleaned.startswith("```json"):
                cleaned = cleaned[7:]
            if cleaned.startswith("```"):
                cleaned = cleaned[3:]
            if cleaned.endswith("```"):
                cleaned = cleaned[:-3]
            cleaned = cleaned.strip()

            # Parse and validate
            data = json.loads(cleaned)

            # Handle both formats: {"videos": [...]} or [...]
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
                    # Basic validation - must have URL and title
                    if video.url and video.title and "youtube.com" in video.url:
                        videos.append(video)
                except Exception as e:
                    self.logger.warning("Failed to parse video", error=str(e))
                    continue

            self.logger.info(
                "Videos found for session",
                session_title=session.title,
                video_count=len(videos),
            )
            return videos

        except Exception as e:
            self.logger.warning(
                "YouTube search failed",
                session_title=session.title,
                error=str(e),
            )
            return []  # Graceful degradation
