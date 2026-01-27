"""Unit tests for multi-agent pipeline agents."""

from unittest.mock import AsyncMock, MagicMock, patch

import pytest

from app.agents.architect import ArchitectAgent
from app.agents.interviewer import InterviewerAgent
from app.agents.researcher import ConceptResearcher, get_researcher_for_type
from app.agents.state import (
    InterviewContext,
    SessionOutlineItem,
    SessionType,
)
from app.agents.validator import ValidatorAgent


@pytest.fixture
def mock_gemini_client():
    """Create a mock Gemini client."""
    client = MagicMock()
    return client


class TestInterviewerAgent:
    """Tests for the InterviewerAgent."""

    @pytest.mark.asyncio
    async def test_generate_questions_returns_questions(self, mock_gemini_client):
        """Test that generate_questions returns interview questions."""
        # Mock the response
        mock_response = {
            "questions": [
                {
                    "question": "What is your current experience level?",
                    "purpose": "To calibrate the starting point",
                    "example_options": [
                        {"label": "A", "text": "Beginner"},
                        {"label": "B", "text": "Intermediate"},
                        {"label": "C", "text": "Advanced"},
                    ],
                    "allows_freeform": True,
                },
                {
                    "question": "How many hours per week can you dedicate?",
                    "purpose": "To set realistic goals",
                    "example_options": [
                        {"label": "A", "text": "1-5 hours"},
                        {"label": "B", "text": "5-10 hours"},
                    ],
                    "allows_freeform": True,
                },
            ]
        }

        agent = InterviewerAgent(mock_gemini_client)

        with patch.object(
            agent, "generate_structured", new_callable=AsyncMock
        ) as mock_generate:
            # Mock the response model
            mock_result = MagicMock()
            mock_result.questions = mock_response["questions"]
            mock_generate.return_value = mock_result

            questions = await agent.generate_questions(
                topic="Python programming",
                raw_input="I want to learn Python from scratch",
                title="Learn Python",
                max_questions=5,
            )

            assert len(questions) == 2
            assert questions[0].question == "What is your current experience level?"
            assert len(questions[0].example_options) == 3
            assert questions[0].allows_freeform is True


class TestArchitectAgent:
    """Tests for the ArchitectAgent."""

    @pytest.mark.asyncio
    async def test_create_outline_phase1_returns_minimal_outline(self, mock_gemini_client):
        """Test that create_outline_phase1 returns title and minimal session list."""
        from app.agents.architect import ArchitectPhase1Response, SessionOutlineMinimal

        mock_response = ArchitectPhase1Response(
            title="Python Programming Fundamentals",
            sessions=[
                SessionOutlineMinimal(title="Introduction to Python", session_type="concept"),
                SessionOutlineMinimal(title="Variables and Data Types", session_type="tutorial"),
            ],
            learning_path_summary="A beginner Python course"
        )

        agent = ArchitectAgent(mock_gemini_client)

        with patch.object(
            agent, "generate_structured", new_callable=AsyncMock
        ) as mock_generate:
            mock_generate.return_value = mock_response

            context = InterviewContext(topic="Python programming")
            result = await agent.create_outline_phase1(context)

            assert result.title == "Python Programming Fundamentals"
            assert len(result.sessions) == 2
            assert result.sessions[0].title == "Introduction to Python"
            assert result.sessions[0].session_type == "concept"

    @pytest.mark.asyncio
    async def test_create_outline_two_phase_parallel(self, mock_gemini_client):
        """Test that create_outline uses two-phase approach with parallel calls."""
        from app.agents.architect import (
            ArchitectPhase1Response,
            SessionDetailResponse,
            SessionOutlineMinimal,
        )

        phase1_response = ArchitectPhase1Response(
            title="Python Mastery",
            sessions=[
                SessionOutlineMinimal(title="Intro", session_type="concept"),
                SessionOutlineMinimal(title="Practice", session_type="practice"),
            ],
            learning_path_summary="Learn Python"
        )

        detail_responses = [
            SessionDetailResponse(objective="Learn basics", estimated_duration_minutes=60, prerequisites=[]),
            SessionDetailResponse(objective="Practice skills", estimated_duration_minutes=90, prerequisites=[0]),
        ]

        agent = ArchitectAgent(mock_gemini_client)

        call_count = [0]  # Use list to allow mutation in closure

        async def mock_generate_structured(prompt, response_model, **kwargs):
            if response_model.__name__ == "ArchitectPhase1Response":
                return phase1_response
            else:
                idx = call_count[0]
                call_count[0] += 1
                return detail_responses[idx % len(detail_responses)]

        with patch.object(agent, "generate_structured", side_effect=mock_generate_structured):
            context = InterviewContext(topic="Python")
            title, outline = await agent.create_outline(context)

            assert title == "Python Mastery"
            assert len(outline.sessions) == 2
            assert outline.sessions[0].objective == "Learn basics"
            assert outline.sessions[1].objective == "Practice skills"
            assert outline.sessions[0].session_type == SessionType.CONCEPT
            assert outline.sessions[1].session_type == SessionType.PRACTICE
            # Total hours calculated from session durations
            assert outline.total_estimated_hours == 2.5  # (60 + 90) / 60

    @pytest.mark.asyncio
    async def test_create_outline_returns_session_outline(self, mock_gemini_client):
        """Test that create_outline returns a title and structured session outline."""
        from app.agents.architect import (
            ArchitectPhase1Response,
            SessionDetailResponse,
            SessionOutlineMinimal,
        )

        # Phase 1 response
        phase1_response = ArchitectPhase1Response(
            title="Python Programming Fundamentals",
            sessions=[
                SessionOutlineMinimal(title="Introduction to Python", session_type="concept"),
                SessionOutlineMinimal(title="Variables and Data Types", session_type="tutorial"),
            ],
            learning_path_summary="A beginner Python course"
        )

        # Phase 2 responses
        detail_responses = [
            SessionDetailResponse(objective="Learn basic syntax", estimated_duration_minutes=60, prerequisites=[]),
            SessionDetailResponse(objective="Understand data types", estimated_duration_minutes=90, prerequisites=[0]),
        ]

        agent = ArchitectAgent(mock_gemini_client)

        call_count = [0]

        async def mock_generate_structured(prompt, response_model, **kwargs):
            if response_model.__name__ == "ArchitectPhase1Response":
                return phase1_response
            else:
                idx = call_count[0]
                call_count[0] += 1
                return detail_responses[idx % len(detail_responses)]

        with patch.object(agent, "generate_structured", side_effect=mock_generate_structured):
            context = InterviewContext(
                topic="Python programming",
            )

            title, outline = await agent.create_outline(context)

            assert title == "Python Programming Fundamentals"
            assert len(outline.sessions) == 2
            assert outline.sessions[0].title == "Introduction to Python"
            assert outline.sessions[0].session_type == SessionType.CONCEPT
            assert outline.sessions[1].session_type == SessionType.TUTORIAL
            assert outline.learning_path_summary == "A beginner Python course"


class TestResearcherAgent:
    """Tests for the ResearcherAgent classes."""

    def test_get_researcher_for_type_returns_correct_class(self, mock_gemini_client):
        """Test that the factory function returns the correct researcher type."""
        concept = get_researcher_for_type(SessionType.CONCEPT, mock_gemini_client)
        assert isinstance(concept, ConceptResearcher)
        assert concept.session_type == SessionType.CONCEPT

        tutorial = get_researcher_for_type(SessionType.TUTORIAL, mock_gemini_client)
        assert tutorial.session_type == SessionType.TUTORIAL

        practice = get_researcher_for_type(SessionType.PRACTICE, mock_gemini_client)
        assert practice.session_type == SessionType.PRACTICE

    @pytest.mark.asyncio
    async def test_research_session_returns_content(self, mock_gemini_client):
        """Test that research_session returns researched session content."""
        mock_response = MagicMock()
        mock_response.content = "# Introduction to Python\n\nPython is..."
        mock_response.key_concepts = ["variables", "data types", "syntax"]
        mock_response.resources = ["https://python.org/docs"]
        mock_response.exercises = ["Create a simple variable"]

        researcher = ConceptResearcher(mock_gemini_client)

        with patch.object(
            researcher, "generate_structured", new_callable=AsyncMock
        ) as mock_generate:
            mock_generate.return_value = mock_response

            outline_item = SessionOutlineItem(
                id="session_001",
                title="Introduction to Python",
                objective="Learn Python basics",
                session_type=SessionType.CONCEPT,
                estimated_duration_minutes=60,
                prerequisites=[],
                order=1,
            )

            context = InterviewContext(
                topic="Python programming",
            )

            session = await researcher.research_session(
                outline_item=outline_item,
                interview_context=context,
                all_session_outlines=[outline_item],
            )

            assert session.title == "Introduction to Python"
            assert session.content == "# Introduction to Python\n\nPython is..."
            assert len(session.key_concepts) == 3
            assert "variables" in session.key_concepts


class TestValidatorAgent:
    """Tests for the ValidatorAgent."""

    @pytest.mark.asyncio
    async def test_validate_returns_validation_result(self, mock_gemini_client):
        """Test that validate returns a structured validation result."""
        mock_response = MagicMock()
        mock_response.is_valid = True
        mock_response.issues = []
        mock_response.overall_score = 92.5
        mock_response.summary = "Well-structured roadmap with good progression"

        agent = ValidatorAgent(mock_gemini_client)

        with patch.object(
            agent, "generate_structured", new_callable=AsyncMock
        ) as mock_generate:
            mock_generate.return_value = mock_response

            from app.agents.state import ResearchedSession, SessionOutline

            outline = SessionOutline(
                sessions=[],
                learning_path_summary="Test summary",
                total_estimated_hours=10.0,
            )

            researched = [
                ResearchedSession(
                    outline_id="s1",
                    title="Intro",
                    session_type=SessionType.CONCEPT,
                    order=1,
                    content="Content here",
                    key_concepts=["test"],
                    resources=[],
                    exercises=[],
                ),
            ]

            result = await agent.validate(outline, researched)

            assert result.is_valid is True
            assert result.overall_score == 92.5
            assert len(result.issues) == 0
            assert result.summary == "Well-structured roadmap with good progression"

    @pytest.mark.asyncio
    async def test_validate_detects_issues(self, mock_gemini_client):
        """Test that validate correctly reports issues."""
        mock_response = MagicMock()
        mock_response.is_valid = False
        mock_response.issues = [
            MagicMock(
                issue_type="gap",
                severity="high",
                description="Missing prerequisite knowledge",
                affected_session_indices=[1],
                suggested_fix="Add an intro session",
            ),
        ]
        mock_response.overall_score = 65.0
        mock_response.summary = "Issues found that need attention"

        agent = ValidatorAgent(mock_gemini_client)

        with patch.object(
            agent, "generate_structured", new_callable=AsyncMock
        ) as mock_generate:
            mock_generate.return_value = mock_response

            from app.agents.state import ResearchedSession, SessionOutline

            outline = SessionOutline(
                sessions=[],
                learning_path_summary="Test summary",
                total_estimated_hours=10.0,
            )

            researched = [
                ResearchedSession(
                    outline_id="s1",
                    title="Session 1",
                    session_type=SessionType.CONCEPT,
                    order=1,
                    content="Content",
                    key_concepts=[],
                    resources=[],
                    exercises=[],
                ),
                ResearchedSession(
                    outline_id="s2",
                    title="Session 2",
                    session_type=SessionType.TUTORIAL,
                    order=2,
                    content="Content",
                    key_concepts=[],
                    resources=[],
                    exercises=[],
                ),
            ]

            result = await agent.validate(outline, researched)

            # High severity issues make it invalid
            assert result.is_valid is False
            assert len(result.issues) == 1
            assert result.issues[0].severity == "high"
            assert result.overall_score == 65.0


class TestBaseAgentFinishReason:
    """Tests for finish_reason detection in BaseAgent."""

    def test_extract_finish_reason_returns_stop(self, mock_gemini_client):
        """Test extracting STOP finish_reason."""
        agent = InterviewerAgent(mock_gemini_client)

        # Mock response with STOP finish_reason
        mock_response = MagicMock()
        mock_candidate = MagicMock()
        mock_candidate.finish_reason.name = "STOP"
        mock_response.candidates = [mock_candidate]

        result = agent._extract_finish_reason(mock_response)
        assert result == "STOP"

    def test_extract_finish_reason_returns_max_tokens(self, mock_gemini_client):
        """Test extracting MAX_TOKENS finish_reason."""
        agent = InterviewerAgent(mock_gemini_client)

        mock_response = MagicMock()
        mock_candidate = MagicMock()
        mock_candidate.finish_reason.name = "MAX_TOKENS"
        mock_response.candidates = [mock_candidate]

        result = agent._extract_finish_reason(mock_response)
        assert result == "MAX_TOKENS"

    def test_extract_finish_reason_handles_empty_candidates(self, mock_gemini_client):
        """Test extracting finish_reason when candidates is empty."""
        agent = InterviewerAgent(mock_gemini_client)

        mock_response = MagicMock()
        mock_response.candidates = []

        result = agent._extract_finish_reason(mock_response)
        assert result == "UNKNOWN"

    def test_extract_finish_reason_handles_none_candidates(self, mock_gemini_client):
        """Test extracting finish_reason when candidates is None."""
        agent = InterviewerAgent(mock_gemini_client)

        mock_response = MagicMock()
        mock_response.candidates = None

        result = agent._extract_finish_reason(mock_response)
        assert result == "UNKNOWN"

    def test_get_effective_max_tokens_default(self, mock_gemini_client):
        """Test _get_effective_max_tokens returns default when not unlimited."""
        agent = InterviewerAgent(mock_gemini_client)

        # When UNLIMITED_TOKENS is False (default), should return default
        with patch("app.agents.base.UNLIMITED_TOKENS", False):
            result = agent._get_effective_max_tokens(None)
            assert result == agent.default_max_tokens

    def test_get_effective_max_tokens_explicit(self, mock_gemini_client):
        """Test _get_effective_max_tokens respects explicit value."""
        agent = InterviewerAgent(mock_gemini_client)

        with patch("app.agents.base.UNLIMITED_TOKENS", False):
            result = agent._get_effective_max_tokens(5000)
            assert result == 5000

    def test_get_effective_max_tokens_unlimited(self, mock_gemini_client):
        """Test _get_effective_max_tokens returns None when unlimited."""
        agent = InterviewerAgent(mock_gemini_client)

        with patch("app.agents.base.UNLIMITED_TOKENS", True):
            result = agent._get_effective_max_tokens(5000)
            assert result is None

            result = agent._get_effective_max_tokens(None)
            assert result is None


class TestContentSanitization:
    """Tests for content sanitization in researcher output."""

    @pytest.mark.asyncio
    async def test_sanitize_content_replaces_br_tags(self, mock_gemini_client):
        """Test that {br} tags are replaced with newlines."""
        from app.agents.researcher import _sanitize_content

        # Test basic replacement
        content = "Line 1{br}Line 2{br}Line 3"
        result = _sanitize_content(content)
        assert result == "Line 1\nLine 2\nLine 3"

    @pytest.mark.asyncio
    async def test_sanitize_content_preserves_normal_content(self, mock_gemini_client):
        """Test that normal content without {br} is unchanged."""
        from app.agents.researcher import _sanitize_content

        content = "# Heading\n\nNormal paragraph with no special tags."
        result = _sanitize_content(content)
        assert result == content

    @pytest.mark.asyncio
    async def test_research_session_sanitizes_content(self, mock_gemini_client):
        """Test that research_session applies content sanitization."""
        mock_response = MagicMock()
        mock_response.content = "# Introduction{br}{br}Paragraph with{br}line breaks"
        mock_response.key_concepts = ["test"]
        mock_response.resources = []
        mock_response.exercises = []

        researcher = ConceptResearcher(mock_gemini_client)

        with patch.object(
            researcher, "generate_structured", new_callable=AsyncMock
        ) as mock_generate:
            mock_generate.return_value = mock_response

            outline_item = SessionOutlineItem(
                id="session_001",
                title="Test Session",
                objective="Test objective",
                session_type=SessionType.CONCEPT,
                estimated_duration_minutes=60,
                prerequisites=[],
                order=1,
            )

            context = InterviewContext(topic="Test topic")

            session = await researcher.research_session(
                outline_item=outline_item,
                interview_context=context,
                all_session_outlines=[outline_item],
            )

            # Verify {br} tags are replaced with newlines
            assert "{br}" not in session.content
            assert "# Introduction\n\nParagraph with\nline breaks" == session.content


class TestContentTruncatedError:
    """Tests for ContentTruncatedError behavior."""

    def test_content_truncated_error_exists(self):
        """Test that ContentTruncatedError is importable."""
        from app.agents.base import ContentTruncatedError

        error = ContentTruncatedError("Test message")
        assert str(error) == "Test message"

    def test_content_truncated_error_is_exception(self):
        """Test that ContentTruncatedError is a proper exception."""
        from app.agents.base import ContentTruncatedError

        with pytest.raises(ContentTruncatedError):
            raise ContentTruncatedError("Content was truncated")

    def test_generate_structured_catches_truncation_error(self, mock_gemini_client):
        """Test that generate_structured catches ContentTruncatedError in retry loop."""
        from app.agents.base import ContentTruncatedError

        # The error should be caught and retried like other parse errors
        researcher = ConceptResearcher(mock_gemini_client)

        # Verify the error is in the exception tuple
        # This is a structural test - the actual retry behavior is tested via integration
        import inspect
        source = inspect.getsource(researcher.generate_structured)
        assert "ContentTruncatedError" in source
