# Feature: YouTube Agent for Video Recommendations

The following plan should be complete, but it's important that you validate documentation and codebase patterns and task sanity before you start implementing.

Pay special attention to naming of existing utils, types, and models. Import from the right files etc.

## Feature Description

Add a **YouTube Agent** to the multi-agent roadmap creation pipeline that finds relevant educational YouTube video recommendations for each session. The agent uses Gemini with Google Search Grounding to discover real, current YouTube videos that align with session content.

**Key behaviors:**
- Runs **after researchers** to leverage full session content for better search relevance
- Finds **2-3 videos per session** with quality filters (10k+ views, 5-45 min, English, prefer recent)
- **Graceful failure handling**: If the agent fails, roadmap saves successfully and retries in background (up to 3 attempts)
- **Skip silently** if no quality videos found for a session
- Videos display as **thumbnail cards** (image, title, channel, duration) in session view

## User Story

As a self-directed learner,
I want to see curated YouTube video recommendations for each session,
So that I can supplement my learning with visual content from trusted creators.

## Problem Statement

Learners currently receive text-based session content but lack curated video resources. Finding relevant educational videos manually is time-consuming, and generic YouTube searches often return low-quality or tangentially related content.

## Solution Statement

Integrate a new YouTube Agent into the creation pipeline that leverages Gemini's Google Search Grounding to find real, current YouTube videos. The agent runs after researchers complete their work, using session titles and key concepts to craft targeted searches. Videos are stored as structured data on sessions and displayed with thumbnails in the UI.

## Feature Metadata

**Feature Type**: New Capability
**Estimated Complexity**: Medium-High
**Primary Systems Affected**:
- Backend: agents/, models/session.py, routers/roadmaps.py, orchestrator.py
- Frontend: types/, SessionDetailPage.tsx, new VideoCard component

**Dependencies**:
- `google-genai` SDK (already installed) with Google Search Grounding feature
- No new external dependencies required

---

## CONTEXT REFERENCES

### Relevant Codebase Files IMPORTANT: YOU MUST READ THESE FILES BEFORE IMPLEMENTING!

**Agent System:**
- `server/app/agents/base.py` (full file) - Why: BaseAgent class pattern, generate methods, span tracking
- `server/app/agents/researcher.py` (full file) - Why: Model for creating a new agent, ResearchedSession structure
- `server/app/agents/state.py` (lines 88-102) - Why: ResearchedSession model to extend with videos
- `server/app/agents/orchestrator.py` (lines 266-321) - Why: Where to integrate YouTube agent after researchers
- `server/app/agents/prompts.py` - Why: Prompt patterns for agents

**Models:**
- `server/app/models/session.py` (full file) - Why: Session document model to add videos field
- `server/app/models/roadmap.py` - Why: Roadmap model patterns

**API Layer:**
- `server/app/routers/roadmaps.py` (lines 54-68) - Why: SessionResponse schema to update
- `server/app/routers/roadmaps_create.py` - Why: Pipeline flow and SSE events

**Frontend:**
- `client/src/types/index.ts` (lines 16-26) - Why: Session interface to extend
- `client/src/pages/SessionDetailPage.tsx` (lines 110-122) - Why: Where to add video section
- `client/src/components/MarkdownContent.tsx` - Why: Pattern for content components

**Tests:**
- `server/tests/conftest.py` - Why: Test fixtures and patterns
- `server/tests/unit/test_agents.py` - Why: Agent testing patterns with mocks

### New Files to Create

**Backend:**
- `server/app/agents/youtube.py` - YouTube agent implementation
- `server/app/services/video_retry_service.py` - Background retry logic for failed video fetches
- `server/tests/unit/test_youtube_agent.py` - Unit tests for YouTube agent

**Frontend:**
- `client/src/components/VideoCard.tsx` - Video thumbnail card component
- `client/src/components/VideoSection.tsx` - Container for video cards in session view

### Relevant Documentation YOU SHOULD READ THESE BEFORE IMPLEMENTING!

- [Gemini Google Search Grounding](https://ai.google.dev/gemini-api/docs/grounding)
  - Specific section: How to enable grounding with `tools=[types.Tool(google_search=types.GoogleSearch())]`
  - Why: Core API for finding real YouTube videos

- [Google GenAI SDK Reference](https://github.com/google-gemini/generative-ai-python)
  - Specific section: `types.GenerateContentConfig` with tools parameter
  - Why: Exact syntax for grounding configuration

### Patterns to Follow

**Agent Class Pattern** (from `base.py`):
```python
class YouTubeAgent(BaseAgent):
    name = "youtube_agent"
    default_temperature: float = 0.3  # Lower for factual search

    def get_system_prompt(self) -> str:
        return YOUTUBE_AGENT_PROMPT

    async def find_videos(self, session: ResearchedSession) -> list[VideoResource]:
        # Use grounding-enabled generation
        ...
```

**Naming Conventions:**
- Agent classes: `{Name}Agent` (e.g., `YouTubeAgent`)
- Models: PascalCase with descriptive names (e.g., `VideoResource`)
- Functions: snake_case (e.g., `find_videos_for_session`)
- Constants: SCREAMING_SNAKE_CASE (e.g., `YOUTUBE_AGENT_PROMPT`)

**Error Handling:**
```python
try:
    result = await self.find_videos(session)
except Exception as e:
    self.logger.warning("Video search failed", session_id=session.outline_id, error=str(e))
    return []  # Graceful degradation
```

**Logging Pattern:**
```python
self.logger.info(
    "Videos found for session",
    session_id=session.outline_id,
    video_count=len(videos),
)
```

**Pydantic Model Pattern:**
```python
class VideoResource(BaseModel):
    """YouTube video resource for a learning session."""

    url: str = Field(description="Full YouTube video URL")
    title: str = Field(description="Video title")
    channel: str = Field(description="YouTube channel name")
    thumbnail_url: str = Field(description="Video thumbnail URL")
    duration_minutes: int | None = Field(default=None, description="Video duration in minutes")
    description: str | None = Field(default=None, description="Brief video description")
```

---

## IMPLEMENTATION PLAN

### Phase 1: Data Model & Agent Foundation

**Goal:** Define the video data structure and create the base YouTube agent.

**Tasks:**
1. Add `VideoResource` model to state.py
2. Extend `ResearchedSession` with optional videos field
3. Update `Session` document model with videos field
4. Create `YouTubeAgent` class with grounding-enabled generation
5. Add YouTube agent prompt to prompts.py

### Phase 2: Pipeline Integration

**Goal:** Integrate YouTube agent into the orchestrator pipeline.

**Tasks:**
1. Add `_run_youtube_agent` method to orchestrator
2. Call YouTube agent after researchers complete (sequential, not parallel)
3. Add SSE event for YouTube search progress
4. Handle graceful failure - proceed without videos if agent fails

### Phase 3: Background Retry System

**Goal:** Implement retry logic for failed video fetches.

**Tasks:**
1. Create pending video job tracking in session document
2. Create `video_retry_service.py` for background retries
3. Add API endpoint to trigger retry for a session
4. Implement retry limit (max 3 attempts)

### Phase 4: API & Response Updates

**Goal:** Expose video data through existing API endpoints.

**Tasks:**
1. Update `SessionResponse` schema to include videos
2. Update session GET endpoint to return videos
3. Ensure video data serializes correctly

### Phase 5: Frontend Components

**Goal:** Display video cards in session view.

**Tasks:**
1. Add `VideoResource` type to frontend types
2. Create `VideoCard` component with thumbnail
3. Create `VideoSection` container component
4. Integrate into `SessionDetailPage`
5. Style with Tailwind to match existing design

### Phase 6: Testing & Validation

**Goal:** Ensure reliability and correctness.

**Tasks:**
1. Unit tests for YouTubeAgent with mocked responses
2. Unit tests for video retry service
3. Integration tests for session endpoints with videos
4. Manual validation of full flow

---

## STEP-BY-STEP TASKS

IMPORTANT: Execute every task in order, top to bottom. Each task is atomic and independently testable.

---

### Phase 1: Data Model & Agent Foundation

---

### 1. UPDATE `server/app/agents/state.py`

Add VideoResource model and extend ResearchedSession.

- **IMPLEMENT**: Add `VideoResource` Pydantic model after `ResearchedSession` class (around line 102)
- **PATTERN**: Follow `SessionOutlineItem` model structure (lines 68-77)
- **IMPORTS**: No new imports needed (Pydantic already imported)

```python
class VideoResource(BaseModel):
    """YouTube video resource for a learning session."""

    url: str = Field(description="Full YouTube video URL")
    title: str = Field(description="Video title")
    channel: str = Field(description="YouTube channel name")
    thumbnail_url: str = Field(description="Video thumbnail image URL")
    duration_minutes: int | None = Field(default=None, description="Video duration in minutes")
    description: str | None = Field(default=None, description="Brief description of video content")
```

- **IMPLEMENT**: Add `videos` field to `ResearchedSession` class (around line 100)

```python
class ResearchedSession(BaseModel):
    # ... existing fields ...
    exercises: list[str] = Field(default_factory=list)
    videos: list[VideoResource] = Field(default_factory=list)  # ADD THIS
```

- **VALIDATE**: `cd server && ./venv/bin/python -c "from app.agents.state import VideoResource, ResearchedSession; print('OK')"`

---

### 2. UPDATE `server/app/models/session.py`

Add videos field to Session document for persistence.

- **IMPLEMENT**: Import `VideoResource` and add to Session document
- **PATTERN**: Mirror existing field patterns in Session class
- **IMPORTS**: Add import for VideoResource from state module

```python
from app.agents.state import VideoResource  # Add import at top

class Session(Document):
    # ... existing fields ...
    notes: str = ""
    videos: list[VideoResource] = Field(default_factory=list)  # ADD THIS
    created_at: datetime = Field(default_factory=utc_now)
```

- **GOTCHA**: VideoResource is a Pydantic model, not a Beanie Document - it embeds correctly in MongoDB
- **VALIDATE**: `cd server && ./venv/bin/python -c "from app.models.session import Session; print('OK')"`

---

### 3. UPDATE `server/app/agents/prompts.py`

Add YouTube agent system prompt.

- **IMPLEMENT**: Add `YOUTUBE_AGENT_PROMPT` constant at end of file
- **PATTERN**: Follow structure of existing prompts (e.g., RESEARCHER_BASE_PROMPT)

```python
YOUTUBE_AGENT_PROMPT = """You are a YouTube educational content curator specializing in finding high-quality learning videos.

Your task is to find 2-3 relevant YouTube videos for a learning session.

SEARCH CRITERIA:
- Videos should directly relate to the session topic and content
- Prefer educational channels with clear explanations
- Prioritize videos with:
  - 10,000+ views (indicates community validation)
  - 5-45 minutes length (focused learning, not full courses)
  - Content from the last 3 years (prefer recent, but allow timeless content)
  - English language

SEARCH STRATEGY:
1. Use the session title and key concepts to form search queries
2. Include "tutorial", "explained", or "learn" in searches for better results
3. Look for videos from known educational channels when possible

OUTPUT FORMAT:
For each video found, extract:
- Full YouTube URL (must be a real, valid youtube.com URL)
- Exact video title
- Channel name
- Thumbnail URL (youtube thumbnail format)
- Estimated duration in minutes
- Brief 1-sentence description of what the video covers

If you cannot find quality videos matching the criteria, return an empty list.
Do NOT make up or hallucinate video URLs - only return videos you find through search.
"""
```

- **VALIDATE**: `cd server && ./venv/bin/python -c "from app.agents.prompts import YOUTUBE_AGENT_PROMPT; print(len(YOUTUBE_AGENT_PROMPT), 'chars')"`

---

### 4. CREATE `server/app/agents/youtube.py`

Create the YouTube agent with Google Search Grounding.

- **IMPLEMENT**: Create new YouTubeAgent class
- **PATTERN**: Mirror `server/app/agents/researcher.py` structure
- **IMPORTS**: BaseAgent, genai types, VideoResource, prompts

```python
"""YouTube agent for finding educational video recommendations."""

import asyncio
from functools import partial

import structlog
from google import genai
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

        prompt = f"""Find {max_videos} high-quality YouTube tutorial videos for this learning session:

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
            import json
            data = json.loads(cleaned)

            videos = []
            for v in data.get("videos", [])[:max_videos]:
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
```

- **GOTCHA**: Google Search grounding may not be available in all regions or API tiers
- **VALIDATE**: `cd server && ./venv/bin/python -c "from app.agents.youtube import YouTubeAgent; print('OK')"`

---

### Phase 2: Pipeline Integration

---

### 5. UPDATE `server/app/agents/orchestrator.py`

Integrate YouTube agent into the pipeline after researchers.

- **IMPLEMENT**: Add import for YouTubeAgent at top of file
- **IMPLEMENT**: Add `_run_youtube_agent` method after `_run_researchers_parallel` method
- **IMPLEMENT**: Call YouTube agent in `run_pipeline` after researchers complete
- **PATTERN**: Follow `_run_validator` method structure (lines 323-357)

**Add import (around line 14):**
```python
from app.agents.youtube import YouTubeAgent
```

**Add new method after `_run_researchers_parallel` (around line 321):**
```python
async def _run_youtube_agent(
    self,
    researched_sessions: list[ResearchedSession],
) -> list[ResearchedSession]:
    """Run the YouTube agent to find videos for all sessions.

    Videos are added in-place to each ResearchedSession.
    On failure, sessions proceed without videos (graceful degradation).
    """
    youtube_agent = YouTubeAgent(self.client)

    for session in researched_sessions:
        span = youtube_agent.create_span(f"find_videos_{session.order}")

        try:
            videos = await youtube_agent.find_videos(session, max_videos=3)
            session.videos = videos

            youtube_agent.complete_span(
                span,
                status="success" if videos else "no_results",
                output_summary=f"Found {len(videos)} videos",
            )

        except Exception as e:
            youtube_agent.complete_span(span, error=e)
            session.videos = []  # Proceed without videos

        self.trace.spans.append(span)

    await self.trace.save()

    found_count = sum(len(s.videos) for s in researched_sessions)
    self.logger.info(
        "YouTube agent complete",
        total_videos=found_count,
        sessions_with_videos=sum(1 for s in researched_sessions if s.videos),
    )

    return researched_sessions
```

**Update `run_pipeline` method - add after researchers, before validator (around line 158):**

Find this section in `run_pipeline`:
```python
# Run researchers in parallel
yield SSEEvent(...)
researched_sessions = await self._run_researchers_parallel(outline, interview_context)
```

Add after it:
```python
# Run YouTube agent to find videos
yield SSEEvent(
    event="stage_update",
    data={
        "stage": "finding_videos",
        "message": "Finding educational videos...",
    },
)
await self._run_youtube_agent(researched_sessions)
```

- **GOTCHA**: YouTube agent runs sequentially per session (not parallel) to avoid rate limiting
- **VALIDATE**: `cd server && ./venv/bin/python -c "from app.agents.orchestrator import PipelineOrchestrator; print('OK')"`

---

### 6. UPDATE `server/app/agents/orchestrator.py` - `_save_roadmap` method

Ensure videos are saved with sessions.

- **IMPLEMENT**: Update `_save_roadmap` to include videos when creating Session documents
- **PATTERN**: Look at existing session creation (lines 384-391)

**Update the session creation loop (around line 384-391):**
```python
# Create session documents
session_summaries: list[SessionSummary] = []
for rs in researched_sessions:
    session = Session(
        roadmap_id=roadmap.id,
        order=rs.order,
        title=rs.title,
        content=rs.content,
        videos=rs.videos,  # ADD THIS LINE
    )
    await session.insert()
```

- **VALIDATE**: Run unit tests: `cd server && ./venv/bin/pytest tests/unit/test_agents.py -v`

---

### Phase 3: Background Retry System

---

### 7. UPDATE `server/app/models/session.py`

Add field to track pending video retry status.

- **IMPLEMENT**: Add `video_retry_count` and `video_retry_pending` fields

```python
class Session(Document):
    # ... existing fields ...
    videos: list[VideoResource] = Field(default_factory=list)
    video_retry_count: int = Field(default=0)  # ADD THIS
    video_retry_pending: bool = Field(default=False)  # ADD THIS
    created_at: datetime = Field(default_factory=utc_now)
```

- **VALIDATE**: `cd server && ./venv/bin/python -c "from app.models.session import Session; print('OK')"`

---

### 8. CREATE `server/app/services/video_retry_service.py`

Background retry service for failed video fetches.

- **IMPLEMENT**: Create service with retry logic
- **PATTERN**: Follow ai_service.py patterns

```python
"""Background retry service for failed video fetches."""

import structlog
from beanie import PydanticObjectId
from google import genai

from app.agents.state import ResearchedSession, VideoResource
from app.agents.youtube import YouTubeAgent
from app.models.session import Session

logger = structlog.get_logger()

MAX_RETRY_ATTEMPTS = 3


async def retry_videos_for_session(
    session_id: PydanticObjectId,
    client: genai.Client,
) -> list[VideoResource]:
    """Retry finding videos for a session.

    Args:
        session_id: The session to retry videos for
        client: Initialized Gemini client

    Returns:
        List of found videos (may be empty)

    Raises:
        ValueError: If session not found or max retries exceeded
    """
    session = await Session.get(session_id)
    if session is None:
        raise ValueError(f"Session {session_id} not found")

    if session.video_retry_count >= MAX_RETRY_ATTEMPTS:
        logger.warning(
            "Max retry attempts reached",
            session_id=str(session_id),
            attempts=session.video_retry_count,
        )
        session.video_retry_pending = False
        await session.save()
        return []

    # Increment retry count
    session.video_retry_count += 1
    await session.save()

    # Create a ResearchedSession-like object for the agent
    research_session = ResearchedSession(
        outline_id=str(session.id),
        title=session.title,
        session_type="concept",  # Default type for retry
        order=session.order,
        content=session.content,
        key_concepts=[],  # Extract from content if needed
        resources=[],
        exercises=[],
    )

    youtube_agent = YouTubeAgent(client)

    try:
        videos = await youtube_agent.find_videos(research_session, max_videos=3)

        if videos:
            session.videos = videos
            session.video_retry_pending = False
            await session.save()

            logger.info(
                "Retry successful",
                session_id=str(session_id),
                video_count=len(videos),
                attempt=session.video_retry_count,
            )
        else:
            # No videos found, keep pending if retries remain
            session.video_retry_pending = session.video_retry_count < MAX_RETRY_ATTEMPTS
            await session.save()

            logger.info(
                "Retry found no videos",
                session_id=str(session_id),
                attempt=session.video_retry_count,
                will_retry=session.video_retry_pending,
            )

        return videos

    except Exception as e:
        logger.error(
            "Retry failed",
            session_id=str(session_id),
            attempt=session.video_retry_count,
            error=str(e),
        )
        session.video_retry_pending = session.video_retry_count < MAX_RETRY_ATTEMPTS
        await session.save()
        return []


async def mark_session_for_retry(session_id: PydanticObjectId) -> bool:
    """Mark a session for video retry.

    Args:
        session_id: The session to mark

    Returns:
        True if marked, False if already at max retries
    """
    session = await Session.get(session_id)
    if session is None:
        return False

    if session.video_retry_count >= MAX_RETRY_ATTEMPTS:
        return False

    session.video_retry_pending = True
    await session.save()
    return True
```

- **VALIDATE**: `cd server && ./venv/bin/python -c "from app.services.video_retry_service import retry_videos_for_session; print('OK')"`

---

### Phase 4: API & Response Updates

---

### 9. UPDATE `server/app/routers/roadmaps.py`

Add VideoResource to SessionResponse schema.

- **IMPLEMENT**: Import VideoResource and add to SessionResponse
- **IMPLEMENT**: Update get_session endpoint to return videos
- **PATTERN**: Follow existing field patterns in SessionResponse

**Add import (around line 10):**
```python
from app.agents.state import VideoResource
```

**Update SessionResponse class (around line 54):**
```python
class VideoResourceResponse(BaseModel):
    """Schema for video resource in responses."""

    url: str
    title: str
    channel: str
    thumbnail_url: str
    duration_minutes: int | None
    description: str | None


class SessionResponse(BaseModel):
    """Schema for full session response."""

    id: str
    roadmap_id: str
    order: int
    title: str
    content: str
    status: str
    notes: str
    videos: list[VideoResourceResponse] = Field(default_factory=list)  # ADD THIS
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True
```

**Update get_session endpoint (around line 271):**
```python
return SessionResponse(
    id=str(session.id),
    roadmap_id=str(session.roadmap_id),
    order=session.order,
    title=session.title,
    content=session.content,
    status=session.status,
    notes=session.notes,
    videos=[
        VideoResourceResponse(
            url=v.url,
            title=v.title,
            channel=v.channel,
            thumbnail_url=v.thumbnail_url,
            duration_minutes=v.duration_minutes,
            description=v.description,
        )
        for v in session.videos
    ],  # ADD THIS
    created_at=session.created_at,
    updated_at=session.updated_at,
)
```

**Also update the update_session endpoint return (around line 336) with same videos mapping.**

- **VALIDATE**: `cd server && ./venv/bin/pytest tests/integration/test_sessions.py -v`

---

### Phase 5: Frontend Components

---

### 10. UPDATE `client/src/types/index.ts`

Add VideoResource type and extend Session interface.

- **IMPLEMENT**: Add VideoResource interface
- **IMPLEMENT**: Add videos field to Session interface
- **PATTERN**: Follow existing interface patterns

**Add VideoResource interface (after line 31):**
```typescript
export interface VideoResource {
  url: string;
  title: string;
  channel: string;
  thumbnail_url: string;
  duration_minutes: number | null;
  description: string | null;
}
```

**Update Session interface (around line 16):**
```typescript
export interface Session {
  id: string;
  roadmap_id: string;
  order: number;
  title: string;
  content: string;
  status: SessionStatus;
  notes: string;
  videos: VideoResource[];  // ADD THIS
  created_at: string;
  updated_at: string;
}
```

- **VALIDATE**: `cd client && ~/.bun/bin/bun run build` (TypeScript compilation check)

---

### 11. CREATE `client/src/components/VideoCard.tsx`

Create video thumbnail card component.

- **IMPLEMENT**: Create VideoCard with thumbnail, title, channel, duration
- **PATTERN**: Follow component patterns in `client/src/components/`

```typescript
import type { VideoResource } from '../types';

interface VideoCardProps {
  video: VideoResource;
}

export function VideoCard({ video }: VideoCardProps) {
  const formatDuration = (minutes: number | null): string => {
    if (minutes === null) return '';
    if (minutes < 60) return `${minutes} min`;
    const hours = Math.floor(minutes / 60);
    const mins = minutes % 60;
    return mins > 0 ? `${hours}h ${mins}m` : `${hours}h`;
  };

  return (
    <a
      href={video.url}
      target="_blank"
      rel="noopener noreferrer"
      className="block group"
    >
      <div className="bg-white border border-gray-200 rounded-lg overflow-hidden hover:shadow-md transition-shadow">
        {/* Thumbnail */}
        <div className="relative aspect-video bg-gray-100">
          <img
            src={video.thumbnail_url}
            alt={video.title}
            className="w-full h-full object-cover"
            onError={(e) => {
              // Fallback for broken thumbnails
              (e.target as HTMLImageElement).src = 'https://img.youtube.com/vi/default/maxresdefault.jpg';
            }}
          />
          {video.duration_minutes && (
            <span className="absolute bottom-2 right-2 bg-black bg-opacity-80 text-white text-xs px-1.5 py-0.5 rounded">
              {formatDuration(video.duration_minutes)}
            </span>
          )}
          {/* Play overlay on hover */}
          <div className="absolute inset-0 flex items-center justify-center bg-black bg-opacity-0 group-hover:bg-opacity-30 transition-all">
            <svg
              className="w-12 h-12 text-white opacity-0 group-hover:opacity-100 transition-opacity"
              fill="currentColor"
              viewBox="0 0 24 24"
            >
              <path d="M8 5v14l11-7z" />
            </svg>
          </div>
        </div>

        {/* Info */}
        <div className="p-3">
          <h4 className="font-medium text-gray-900 text-sm line-clamp-2 group-hover:text-blue-600">
            {video.title}
          </h4>
          <p className="text-xs text-gray-500 mt-1">{video.channel}</p>
          {video.description && (
            <p className="text-xs text-gray-600 mt-1 line-clamp-2">{video.description}</p>
          )}
        </div>
      </div>
    </a>
  );
}
```

- **VALIDATE**: `cd client && ~/.bun/bin/bun run build`

---

### 12. CREATE `client/src/components/VideoSection.tsx`

Create container component for video cards.

- **IMPLEMENT**: Create VideoSection that displays 2-3 video cards in a grid
- **PATTERN**: Follow section patterns in SessionDetailPage

```typescript
import type { VideoResource } from '../types';
import { VideoCard } from './VideoCard';

interface VideoSectionProps {
  videos: VideoResource[];
}

export function VideoSection({ videos }: VideoSectionProps) {
  if (!videos || videos.length === 0) {
    return null; // Skip silently if no videos
  }

  return (
    <div className="mt-6">
      <h3 className="text-lg font-semibold text-gray-900 mb-4 flex items-center gap-2">
        <svg className="w-5 h-5 text-red-600" fill="currentColor" viewBox="0 0 24 24">
          <path d="M19.615 3.184c-3.604-.246-11.631-.245-15.23 0-3.897.266-4.356 2.62-4.385 8.816.029 6.185.484 8.549 4.385 8.816 3.6.245 11.626.246 15.23 0 3.897-.266 4.356-2.62 4.385-8.816-.029-6.185-.484-8.549-4.385-8.816zm-10.615 12.816v-8l8 3.993-8 4.007z"/>
        </svg>
        Recommended Videos
      </h3>
      <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-3 gap-4">
        {videos.map((video, index) => (
          <VideoCard key={`${video.url}-${index}`} video={video} />
        ))}
      </div>
    </div>
  );
}
```

- **VALIDATE**: `cd client && ~/.bun/bin/bun run build`

---

### 13. UPDATE `client/src/pages/SessionDetailPage.tsx`

Integrate VideoSection into session view.

- **IMPLEMENT**: Import VideoSection and add after MarkdownContent
- **PATTERN**: Follow existing section structure in the page

**Add import (around line 5):**
```typescript
import { VideoSection } from '../components/VideoSection';
```

**Add VideoSection after MarkdownContent section (around line 113):**

Find this section:
```tsx
<div className="p-6 border-b border-gray-200">
  <MarkdownContent content={session.content} />
</div>
```

Add after it:
```tsx
{session.videos && session.videos.length > 0 && (
  <div className="p-6 border-b border-gray-200">
    <VideoSection videos={session.videos} />
  </div>
)}
```

- **VALIDATE**: `cd client && ~/.bun/bin/bun run build`

---

### Phase 6: Testing & Validation

---

### 14. CREATE `server/tests/unit/test_youtube_agent.py`

Unit tests for YouTube agent.

- **IMPLEMENT**: Create test file with mocked responses
- **PATTERN**: Follow patterns in `server/tests/unit/test_agents.py`

```python
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
        mock_response = '''{
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
        }'''

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
        mock_response = '''{
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
        }'''

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
        mock_response = '''```json
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
```'''

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
```

- **VALIDATE**: `cd server && ./venv/bin/pytest tests/unit/test_youtube_agent.py -v`

---

### 15. UPDATE `server/tests/conftest.py`

Update test fixtures to include videos field.

- **IMPLEMENT**: Update `test_roadmap_with_sessions` fixture to include videos
- **PATTERN**: Follow existing fixture patterns

**Update session creation in `test_roadmap_with_sessions` (around line 175):**
```python
for order, (title, content) in enumerate(session_data, start=1):
    session = Session(
        roadmap_id=roadmap.id,
        order=order,
        title=title,
        content=content,
        status="not_started",
        videos=[],  # ADD THIS
    )
    await session.insert()
    sessions.append(session)
```

- **VALIDATE**: `cd server && ./venv/bin/pytest tests/integration/test_sessions.py -v`

---

### 16. RUN FULL VALIDATION

Execute all validation commands to ensure the feature works correctly.

- **VALIDATE**:
  - Backend lint: `cd server && ./venv/bin/ruff check app/`
  - Backend format: `cd server && ./venv/bin/ruff format app/`
  - Backend tests: `cd server && ./venv/bin/pytest -v`
  - Frontend lint: `cd client && ~/.bun/bin/bun run lint`
  - Frontend build: `cd client && ~/.bun/bin/bun run build`

---

## TESTING STRATEGY

### Unit Tests

**YouTubeAgent tests** (`test_youtube_agent.py`):
- `test_find_videos_returns_videos` - Happy path
- `test_find_videos_handles_empty_response` - No results
- `test_find_videos_handles_error_gracefully` - API failure
- `test_find_videos_filters_invalid_urls` - Validation
- `test_find_videos_handles_markdown_wrapped_json` - Response parsing

**VideoRetryService tests** (create `test_video_retry_service.py`):
- `test_retry_increments_count`
- `test_retry_stops_at_max_attempts`
- `test_retry_clears_pending_on_success`

### Integration Tests

**Session endpoint tests** (update `test_sessions.py`):
- `test_get_session_returns_videos` - Videos included in response
- `test_update_session_preserves_videos` - Videos not lost on update

### Edge Cases

- Session with no key concepts (search by title only)
- Very long session content (truncated in prompt)
- All videos fail validation (returns empty list)
- Grounding not available (graceful degradation)
- Malformed JSON response from Gemini
- Network timeout during search

---

## VALIDATION COMMANDS

Execute every command to ensure zero regressions and 100% feature correctness.

### Level 1: Syntax & Style

```bash
# Backend linting
cd server && ./venv/bin/ruff check app/

# Backend formatting
cd server && ./venv/bin/ruff format app/ --check

# Frontend linting
cd client && ~/.bun/bin/bun run lint
```

### Level 2: Unit Tests

```bash
# All backend unit tests
cd server && ./venv/bin/pytest tests/unit/ -v

# Specifically YouTube agent tests
cd server && ./venv/bin/pytest tests/unit/test_youtube_agent.py -v
```

### Level 3: Integration Tests

```bash
# All backend integration tests
cd server && ./venv/bin/pytest tests/integration/ -v

# Session-specific tests
cd server && ./venv/bin/pytest tests/integration/test_sessions.py -v
```

### Level 4: Manual Validation

1. Start backend: `cd server && ./venv/bin/uvicorn app.main:app --reload`
2. Start frontend: `cd client && ~/.bun/bin/bun run dev`
3. Login with Google
4. Create a new roadmap with topic "Learn Python basics"
5. Verify SSE shows "Finding educational videos..." stage
6. Open a session and verify video cards appear
7. Click a video card and verify it opens YouTube in new tab

### Level 5: TypeScript Compilation

```bash
# Full TypeScript build
cd client && ~/.bun/bin/bun run build
```

---

## ACCEPTANCE CRITERIA

- [x] Feature implements all specified functionality
- [ ] YouTube agent finds 2-3 videos per session using Gemini grounding
- [ ] Videos are stored in Session documents with all metadata
- [ ] Session API returns videos in response
- [ ] Frontend displays video thumbnail cards
- [ ] Clicking a card opens YouTube in new tab
- [ ] Sessions without videos show no video section (skip silently)
- [ ] Pipeline continues if YouTube agent fails (graceful degradation)
- [ ] Retry system tracks attempts up to max 3
- [ ] All validation commands pass with zero errors
- [ ] Unit test coverage for YouTube agent
- [ ] Integration tests verify session endpoints with videos
- [ ] Code follows project conventions and patterns
- [ ] No regressions in existing functionality

---

## COMPLETION CHECKLIST

- [ ] All tasks completed in order
- [ ] Each task validation passed immediately
- [ ] All validation commands executed successfully
- [ ] Full test suite passes (unit + integration)
- [ ] No linting or type checking errors
- [ ] Manual testing confirms feature works
- [ ] Acceptance criteria all met
- [ ] Code reviewed for quality and maintainability

---

## NOTES

### Design Decisions

1. **Sequential vs Parallel YouTube searches**: Chose sequential to avoid rate limiting and because video search is not on the critical path.

2. **Grounding vs YouTube API**: Using Gemini grounding avoids additional API credentials and quotas. Trade-off is less structured metadata (duration estimated, not exact).

3. **VideoResource in state.py vs separate file**: Kept in state.py since it's used by the pipeline. Could be moved to models/ if reused elsewhere.

4. **Background retry as service, not Celery**: Simple approach using session fields. Production scale would benefit from proper job queue.

### Trade-offs

- **Thumbnail reliability**: YouTube thumbnails use a standard format but may fail for some videos. Fallback image handles this.
- **Duration accuracy**: Gemini estimates duration from search results, may not be exact. Acceptable for recommendation purposes.
- **No video preview**: Decided against embedded preview to keep sessions fast-loading and focused on learning content.

### Future Enhancements

- Add "Refresh videos" button per session (currently out of scope)
- Support other video platforms (Vimeo, educational sites)
- User preferences for video length, channels to prefer/exclude
- Track which videos users watch for personalization
