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
