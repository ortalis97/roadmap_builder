"""Tests for the Editor agent."""

import pytest
from unittest.mock import AsyncMock, MagicMock

from app.agents.editor import EditorAgent, EditorResponse, ResearchSectionResponse
from app.agents.state import (
    InterviewContext,
    ResearchedSession,
    SessionOutlineItem,
    SessionType,
    ValidationIssue,
    ValidationIssueType,
)


@pytest.fixture
def mock_client():
    """Create a mock Gemini client."""
    return MagicMock()


@pytest.fixture
def sample_session():
    """Create a sample session for testing."""
    return ResearchedSession(
        outline_id="session_1",
        title="Introduction to Python",
        session_type=SessionType.CONCEPT,
        order=1,
        content="# Introduction\n\nPython is a programming language.\n\n## Variables\n\nVariables store data.",
        key_concepts=["variables", "data types"],
        resources=[],
        exercises=[],
        videos=[],
    )


@pytest.fixture
def sample_outline_item():
    """Create a sample outline item."""
    return SessionOutlineItem(
        id="session_1",
        title="Introduction to Python",
        objective="Learn Python basics",
        session_type=SessionType.CONCEPT,
        order=1,
    )


@pytest.fixture
def sample_interview_context():
    """Create sample interview context."""
    return InterviewContext(topic="Learn Python programming")


@pytest.mark.asyncio
async def test_editor_preserves_videos(
    mock_client, sample_session, sample_outline_item, sample_interview_context
):
    """Test that Editor preserves videos during editing."""
    from app.agents.state import VideoResource

    # Add videos to session with all required fields
    sample_session.videos = [
        VideoResource(
            url="https://youtube.com/watch?v=123",
            title="Python Tutorial",
            channel="Python Tutorials",
            thumbnail_url="https://i.ytimg.com/vi/123/default.jpg",
            duration_minutes=15,
            description="A great tutorial",
        )
    ]

    editor = EditorAgent(mock_client)

    # Mock generate_structured to return edited content
    editor.generate_structured = AsyncMock(
        return_value=EditorResponse(
            edited_content="# Edited Introduction\n\nImproved content here.",
            needs_research=False,
            research_request=None,
        )
    )

    issue = ValidationIssue(
        id="issue_1",
        issue_type=ValidationIssueType.COHERENCE,
        severity="medium",
        description="Content flow could be improved",
        affected_session_ids=["session_1"],
        suggested_fix="Add better transitions",
    )

    result = await editor.edit_session(
        session=sample_session,
        issues=[issue],
        outline_item=sample_outline_item,
        interview_context=sample_interview_context,
        all_session_outlines=[sample_outline_item],
    )

    # Videos should be preserved
    assert result.videos == sample_session.videos
    assert "Edited Introduction" in result.content


@pytest.mark.asyncio
async def test_editor_triggers_research_for_critical_gap(
    mock_client, sample_session, sample_outline_item, sample_interview_context
):
    """Test that Editor triggers research for critical gaps."""
    editor = EditorAgent(mock_client)

    # First call: Editor decides research is needed
    # Second call: Research section generation
    editor.generate_structured = AsyncMock(
        side_effect=[
            EditorResponse(
                edited_content="# Content with gap marker\n\n[GAP HERE]",
                needs_research=True,
                research_request="Explain list comprehensions in Python",
            ),
            ResearchSectionResponse(
                section_content="List comprehensions are a concise way to create lists...",
                suggested_heading="List Comprehensions",
            ),
        ]
    )

    issue = ValidationIssue(
        id="issue_1",
        issue_type=ValidationIssueType.GAP,
        severity="high",
        description="Missing explanation of list comprehensions",
        affected_session_ids=["session_1"],
        suggested_fix="Add section on list comprehensions",
    )

    result = await editor.edit_session(
        session=sample_session,
        issues=[issue],
        outline_item=sample_outline_item,
        interview_context=sample_interview_context,
        all_session_outlines=[sample_outline_item],
    )

    # Research content should be merged
    assert "List Comprehensions" in result.content
    assert "concise way to create lists" in result.content


@pytest.mark.asyncio
async def test_editor_handles_multiple_issues(
    mock_client, sample_session, sample_outline_item, sample_interview_context
):
    """Test that Editor handles multiple issues for a single session."""
    editor = EditorAgent(mock_client)

    editor.generate_structured = AsyncMock(
        return_value=EditorResponse(
            edited_content="# Fixed content addressing all issues",
            needs_research=False,
            research_request=None,
        )
    )

    issues = [
        ValidationIssue(
            id="issue_1",
            issue_type=ValidationIssueType.COHERENCE,
            severity="medium",
            description="Content flow needs improvement",
            affected_session_ids=["session_1"],
            suggested_fix="Add transitions",
        ),
        ValidationIssue(
            id="issue_2",
            issue_type=ValidationIssueType.DEPTH,
            severity="low",
            description="Too shallow in places",
            affected_session_ids=["session_1"],
            suggested_fix="Add more examples",
        ),
    ]

    result = await editor.edit_session(
        session=sample_session,
        issues=issues,
        outline_item=sample_outline_item,
        interview_context=sample_interview_context,
        all_session_outlines=[sample_outline_item],
    )

    # Should have called generate_structured with both issues in prompt
    call_args = editor.generate_structured.call_args
    prompt = call_args.kwargs.get("prompt", call_args.args[0] if call_args.args else "")
    assert "COHERENCE" in prompt
    assert "DEPTH" in prompt
    assert result.content == "# Fixed content addressing all issues"


@pytest.mark.asyncio
async def test_editor_preserves_key_concepts_and_resources(
    mock_client, sample_session, sample_outline_item, sample_interview_context
):
    """Test that Editor preserves key_concepts, resources, and exercises."""
    # Add metadata to session
    sample_session.key_concepts = ["concept1", "concept2"]
    sample_session.resources = ["https://example.com/resource"]
    sample_session.exercises = ["Exercise 1: Do something"]

    editor = EditorAgent(mock_client)

    editor.generate_structured = AsyncMock(
        return_value=EditorResponse(
            edited_content="# New content",
            needs_research=False,
            research_request=None,
        )
    )

    issue = ValidationIssue(
        id="issue_1",
        issue_type=ValidationIssueType.OVERLAP,
        severity="medium",
        description="Overlap with session 2",
        affected_session_ids=["session_1"],
        suggested_fix="Remove duplicate content",
    )

    result = await editor.edit_session(
        session=sample_session,
        issues=[issue],
        outline_item=sample_outline_item,
        interview_context=sample_interview_context,
        all_session_outlines=[sample_outline_item],
    )

    # All metadata should be preserved
    assert result.key_concepts == sample_session.key_concepts
    assert result.resources == sample_session.resources
    assert result.exercises == sample_session.exercises


@pytest.mark.asyncio
async def test_editor_continues_without_research_on_failure(
    mock_client, sample_session, sample_outline_item, sample_interview_context
):
    """Test that Editor continues gracefully if research section fetch fails."""
    editor = EditorAgent(mock_client)

    # First call succeeds, second call (research) fails
    editor.generate_structured = AsyncMock(
        side_effect=[
            EditorResponse(
                edited_content="# Partial edit\n\nNeeds more content.",
                needs_research=True,
                research_request="Add explanation of decorators",
            ),
            Exception("API error during research"),
        ]
    )

    issue = ValidationIssue(
        id="issue_1",
        issue_type=ValidationIssueType.GAP,
        severity="high",
        description="Missing decorator explanation",
        affected_session_ids=["session_1"],
        suggested_fix="Add decorator section",
    )

    result = await editor.edit_session(
        session=sample_session,
        issues=[issue],
        outline_item=sample_outline_item,
        interview_context=sample_interview_context,
        all_session_outlines=[sample_outline_item],
    )

    # Should have the edited content without the research section
    assert result.content == "# Partial edit\n\nNeeds more content."
    # No exception should be raised


@pytest.mark.asyncio
async def test_editor_respects_language_setting(
    mock_client, sample_session, sample_outline_item, sample_interview_context
):
    """Test that Editor includes language instruction for Hebrew."""
    editor = EditorAgent(mock_client)

    editor.generate_structured = AsyncMock(
        return_value=EditorResponse(
            edited_content="# תוכן ערוך",
            needs_research=False,
            research_request=None,
        )
    )

    issue = ValidationIssue(
        id="issue_1",
        issue_type=ValidationIssueType.COHERENCE,
        severity="medium",
        description="Needs improvement",
        affected_session_ids=["session_1"],
        suggested_fix="Fix flow",
    )

    result = await editor.edit_session(
        session=sample_session,
        issues=[issue],
        outline_item=sample_outline_item,
        interview_context=sample_interview_context,
        all_session_outlines=[sample_outline_item],
        language="he",
    )

    # Should pass Hebrew language
    assert result.language == "he"
    # Check prompt includes Hebrew instruction
    call_args = editor.generate_structured.call_args
    prompt = call_args.kwargs.get("prompt", call_args.args[0] if call_args.args else "")
    assert "Hebrew" in prompt
