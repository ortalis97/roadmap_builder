"""Unit tests for network error retry logic in BaseAgent."""

from unittest.mock import MagicMock, patch

import pytest
from httpcore import RemoteProtocolError as HttpcoreRemoteProtocolError
from httpx import RemoteProtocolError as HttpxRemoteProtocolError

from app.agents.base import RETRYABLE_NETWORK_ERRORS
from app.agents.interviewer import InterviewerAgent


@pytest.fixture
def mock_gemini_client():
    """Create a mock Gemini client."""
    return MagicMock()


class TestNetworkRetry:
    """Tests for network error retry with exponential backoff."""

    def test_retryable_errors_include_httpcore_remote_protocol_error(self):
        """Test that httpcore.RemoteProtocolError is in retryable errors."""
        assert HttpcoreRemoteProtocolError in RETRYABLE_NETWORK_ERRORS

    def test_retryable_errors_include_httpx_remote_protocol_error(self):
        """Test that httpx.RemoteProtocolError is in retryable errors."""
        assert HttpxRemoteProtocolError in RETRYABLE_NETWORK_ERRORS

    def test_retryable_errors_include_connection_error(self):
        """Test that ConnectionError is in retryable errors."""
        assert ConnectionError in RETRYABLE_NETWORK_ERRORS

    def test_retryable_errors_include_timeout_error(self):
        """Test that TimeoutError is in retryable errors."""
        assert TimeoutError in RETRYABLE_NETWORK_ERRORS

    def test_retryable_errors_include_os_error(self):
        """Test that OSError is in retryable errors."""
        assert OSError in RETRYABLE_NETWORK_ERRORS

    def test_call_with_network_retry_succeeds_first_try(self, mock_gemini_client):
        """Test that successful call returns immediately."""
        agent = InterviewerAgent(mock_gemini_client)

        call_count = [0]

        def successful_call():
            call_count[0] += 1
            return "success"

        result = agent._call_with_network_retry(successful_call, "test_op")

        assert result == "success"
        assert call_count[0] == 1

    def test_call_with_network_retry_retries_on_httpcore_error(self, mock_gemini_client):
        """Test that httpcore network errors trigger retry."""
        agent = InterviewerAgent(mock_gemini_client)

        call_count = [0]

        def failing_then_success_call():
            call_count[0] += 1
            if call_count[0] < 3:
                raise HttpcoreRemoteProtocolError("Server disconnected")
            return "success"

        with patch("app.agents.base.time.sleep"):  # Skip actual sleep
            result = agent._call_with_network_retry(failing_then_success_call, "test_op")

        assert result == "success"
        assert call_count[0] == 3  # Failed twice, succeeded on third

    def test_call_with_network_retry_retries_on_httpx_error(self, mock_gemini_client):
        """Test that httpx network errors trigger retry."""
        agent = InterviewerAgent(mock_gemini_client)

        call_count = [0]

        def failing_then_success_call():
            call_count[0] += 1
            if call_count[0] < 2:
                raise HttpxRemoteProtocolError("Server disconnected")
            return "success"

        with patch("app.agents.base.time.sleep"):  # Skip actual sleep
            result = agent._call_with_network_retry(failing_then_success_call, "test_op")

        assert result == "success"
        assert call_count[0] == 2

    def test_call_with_network_retry_raises_after_max_retries(self, mock_gemini_client):
        """Test that error is raised after all retries exhausted."""
        agent = InterviewerAgent(mock_gemini_client)

        def always_failing_call():
            raise HttpxRemoteProtocolError("Server disconnected")

        with patch("app.agents.base.time.sleep"):  # Skip actual sleep
            with pytest.raises(HttpxRemoteProtocolError):
                agent._call_with_network_retry(always_failing_call, "test_op")

    def test_call_with_network_retry_does_not_retry_value_error(self, mock_gemini_client):
        """Test that non-network errors are not retried."""
        agent = InterviewerAgent(mock_gemini_client)

        call_count = [0]

        def value_error_call():
            call_count[0] += 1
            raise ValueError("Not a network error")

        with pytest.raises(ValueError):
            agent._call_with_network_retry(value_error_call, "test_op")

        assert call_count[0] == 1  # No retry for ValueError

    def test_call_with_network_retry_logs_retry_attempts(self, mock_gemini_client):
        """Test that retry attempts are logged."""
        agent = InterviewerAgent(mock_gemini_client)

        call_count = [0]

        def failing_then_success_call():
            call_count[0] += 1
            if call_count[0] < 2:
                raise ConnectionError("Connection refused")
            return "success"

        with patch("app.agents.base.time.sleep"):
            with patch.object(agent.logger, "warning") as mock_warning:
                result = agent._call_with_network_retry(failing_then_success_call, "test_op")

                assert result == "success"
                # Should have logged the retry
                mock_warning.assert_called_once()
                call_args = mock_warning.call_args
                assert "Network error, retrying" in call_args[0][0]

    def test_call_with_network_retry_logs_exhausted_retries(self, mock_gemini_client):
        """Test that exhausted retries are logged as error."""
        agent = InterviewerAgent(mock_gemini_client)

        def always_failing_call():
            raise TimeoutError("Connection timed out")

        with patch("app.agents.base.time.sleep"):
            with patch.object(agent.logger, "error") as mock_error:
                with pytest.raises(TimeoutError):
                    agent._call_with_network_retry(always_failing_call, "test_op")

                # Should have logged the final error
                mock_error.assert_called_once()
                call_args = mock_error.call_args
                assert "all retries exhausted" in call_args[0][0]


class TestConcurrencyConfig:
    """Tests for concurrency configuration."""

    def test_max_concurrent_api_calls_is_configured(self):
        """Test that MAX_CONCURRENT_API_CALLS is defined."""
        from app.model_config import MAX_CONCURRENT_API_CALLS

        assert isinstance(MAX_CONCURRENT_API_CALLS, int)
        assert MAX_CONCURRENT_API_CALLS > 0

    def test_network_retry_attempts_is_configured(self):
        """Test that NETWORK_RETRY_ATTEMPTS is defined."""
        from app.model_config import NETWORK_RETRY_ATTEMPTS

        assert isinstance(NETWORK_RETRY_ATTEMPTS, int)
        assert NETWORK_RETRY_ATTEMPTS > 0

    def test_network_retry_base_delay_is_configured(self):
        """Test that NETWORK_RETRY_BASE_DELAY is defined."""
        from app.model_config import NETWORK_RETRY_BASE_DELAY

        assert isinstance(NETWORK_RETRY_BASE_DELAY, float)
        assert NETWORK_RETRY_BASE_DELAY > 0

    def test_network_retry_max_delay_is_configured(self):
        """Test that NETWORK_RETRY_MAX_DELAY is defined."""
        from app.model_config import NETWORK_RETRY_MAX_DELAY

        assert isinstance(NETWORK_RETRY_MAX_DELAY, float)
        assert NETWORK_RETRY_MAX_DELAY > 0


class TestSemaphore:
    """Tests for API concurrency semaphore."""

    def test_get_api_semaphore_returns_semaphore(self):
        """Test that get_api_semaphore returns a semaphore."""
        import asyncio

        from app.agents.orchestrator import get_api_semaphore

        semaphore = get_api_semaphore()
        assert isinstance(semaphore, asyncio.Semaphore)

    def test_get_api_semaphore_returns_same_instance(self):
        """Test that get_api_semaphore returns the same semaphore on multiple calls."""
        from app.agents.orchestrator import get_api_semaphore

        semaphore1 = get_api_semaphore()
        semaphore2 = get_api_semaphore()
        assert semaphore1 is semaphore2
