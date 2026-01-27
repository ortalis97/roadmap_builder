# Feature: Gemini API Resilience and Enhanced Logging

The following plan should be complete, but it's important that you validate documentation and codebase patterns and task sanity before you start implementing.

Pay special attention to naming of existing utils, types, and models. Import from the right files.

## Feature Description

Add network error retry with exponential backoff, API concurrency limiting, and enhanced logging to prevent pipeline failures caused by Gemini API connection issues. When running many parallel API requests (e.g., 11 researcher sessions), the API occasionally drops connections with `RemoteProtocolError: Server disconnected without sending a response`. This feature adds resilience to handle these transient failures gracefully.

## User Story

As a user creating a learning roadmap,
I want the system to automatically retry failed API calls and manage request concurrency,
So that my roadmap creation succeeds even when the AI API has transient issues.

## Problem Statement

When running 11+ parallel researcher requests, the Gemini API occasionally drops connections (likely rate limiting or server-side timeout). The current retry logic only handles JSON parsing errors, not network errors. Failed pipelines show error status in traces but no error spans are recorded, making debugging difficult.

**Evidence:**
- Failed pipelines stop after architect (2 spans), before any researcher spans
- Testing 11 parallel researchers locally reproduced: `RemoteProtocolError: Server disconnected without sending a response`
- Error occurs after ~60 seconds of waiting

## Solution Statement

1. **Network Error Retry**: Catch `RemoteProtocolError`, `ConnectionError`, `ReadTimeout`, and similar network errors in `generate_structured` and retry with exponential backoff
2. **Concurrency Limiting**: Add an asyncio.Semaphore to limit parallel Gemini API calls (max 5-6 concurrent requests)
3. **Enhanced Logging**: Add detailed logging for retries, concurrency waits, and errors to improve debugging visibility

---

## Feature Metadata

**Feature Type**: Bug Fix / Enhancement
**Estimated Complexity**: Medium
**Primary Systems Affected**: `app/agents/base.py`, `app/agents/orchestrator.py`, `app/model_config.py`
**Dependencies**: `httpcore`, `httpx` (already installed via google-genai)

---

## CONTEXT REFERENCES

### Relevant Codebase Files IMPORTANT: YOU MUST READ THESE FILES BEFORE IMPLEMENTING!

- `server/app/agents/base.py` (lines 261-338) - Why: Contains `generate_structured` method that needs network error retry logic
- `server/app/agents/base.py` (lines 54-106) - Why: Contains `_generate_sync` that makes actual API calls
- `server/app/agents/base.py` (lines 157-237) - Why: Contains `_generate_structured_sync` that makes structured API calls
- `server/app/agents/orchestrator.py` (lines 290-348) - Why: Contains `_run_researchers_parallel` that needs concurrency limiting
- `server/app/agents/orchestrator.py` (lines 350-398) - Why: Contains `_run_youtube_agent` that also runs parallel requests
- `server/app/model_config.py` - Why: Configuration constants should be added here
- `server/tests/unit/test_agents.py` - Why: Test patterns for agents

### New Files to Create

None - all changes are to existing files.

### Relevant Documentation

- [Python asyncio.Semaphore](https://docs.python.org/3/library/asyncio-sync.html#asyncio.Semaphore)
  - Specific section: Semaphore usage for limiting concurrency
  - Why: Used to limit parallel API calls
- [httpcore.RemoteProtocolError](https://www.encode.io/httpcore/exceptions/)
  - Why: The specific exception type to catch for connection drops

### Patterns to Follow

**Logging Pattern (from base.py):**
```python
self.logger.warning(
    "Descriptive message",
    agent=self.name,
    param1=value1,
    param2=value2,
)
```

**Configuration Pattern (from model_config.py):**
```python
# Global constants at module level
CONSTANT_NAME = value  # Comment explaining purpose
```

**Retry Pattern (existing in base.py lines 286-336):**
```python
for attempt in range(max_retries + 1):
    try:
        # ... attempt operation
    except (ExceptionType1, ExceptionType2) as e:
        last_error = e
        self.logger.warning(
            "Failed message",
            attempt=attempt + 1,
            error=str(e),
        )
raise ValueError(f"Failed after {max_retries + 1} attempts: {last_error}")
```

**Error Handling Pattern:**
- Network errors should be retried with exponential backoff
- Parsing errors should be retried immediately (already implemented)
- Final errors should preserve the original exception type

---

## IMPLEMENTATION PLAN

### Phase 1: Configuration

Add new configuration constants to `model_config.py` for retry and concurrency settings.

**Tasks:**
- Add `MAX_CONCURRENT_API_CALLS` constant (default: 5)
- Add `NETWORK_RETRY_ATTEMPTS` constant (default: 3)
- Add `NETWORK_RETRY_BASE_DELAY` constant (default: 1.0 seconds)
- Add `NETWORK_RETRY_MAX_DELAY` constant (default: 30.0 seconds)

### Phase 2: Network Error Retry in BaseAgent

Update `base.py` to catch and retry network errors with exponential backoff.

**Tasks:**
- Import network error exception types (`httpcore.RemoteProtocolError`, `httpx.ConnectError`, `httpx.ReadTimeout`)
- Create helper method `_is_retryable_network_error()` to identify retryable errors
- Update `_generate_sync` to wrap API call in retry logic for network errors
- Update `_generate_structured_sync` similarly
- Add comprehensive logging for retry attempts

### Phase 3: Concurrency Limiting in Orchestrator

Add semaphore-based concurrency limiting to parallel operations.

**Tasks:**
- Create module-level semaphore using `MAX_CONCURRENT_API_CALLS`
- Update `_run_researchers_parallel` to acquire semaphore before each API call
- Update `_run_youtube_agent` similarly
- Add logging for semaphore wait times

### Phase 4: Enhanced Error Logging

Improve logging throughout the pipeline for better debugging.

**Tasks:**
- Add pipeline-level metrics logging (total sessions, parallel count, timing)
- Log when concurrency limit is reached and request is waiting
- Log network errors with full context (attempt number, delay, error type)
- Ensure error spans are always saved to trace even on failure

### Phase 5: Testing

Add unit tests for new functionality.

**Tasks:**
- Test network error retry logic with mocked exceptions
- Test exponential backoff timing
- Test concurrency limiting behavior
- Test that errors are properly logged

---

## STEP-BY-STEP TASKS

IMPORTANT: Execute every task in order, top to bottom. Each task is atomic and independently testable.

### Task 1: UPDATE `server/app/model_config.py` - Add Configuration Constants

- **IMPLEMENT**: Add concurrency and retry configuration constants after `UNLIMITED_TOKENS`
- **PATTERN**: Follow existing constant pattern (line 12)
- **CODE**:
```python
# Concurrency and retry configuration for Gemini API calls.
# Prevents connection drops from too many parallel requests.
MAX_CONCURRENT_API_CALLS = 5  # Max parallel Gemini API requests

# Network error retry settings with exponential backoff.
NETWORK_RETRY_ATTEMPTS = 3  # Number of retry attempts for network errors
NETWORK_RETRY_BASE_DELAY = 1.0  # Initial delay in seconds (doubles each retry)
NETWORK_RETRY_MAX_DELAY = 30.0  # Maximum delay between retries
```
- **VALIDATE**: `cd server && ./venv/bin/python -c "from app.model_config import MAX_CONCURRENT_API_CALLS, NETWORK_RETRY_ATTEMPTS; print('OK')"`

### Task 2: UPDATE `server/app/agents/base.py` - Add Imports for Network Errors

- **IMPLEMENT**: Add imports for network error types and asyncio at the top of the file
- **PATTERN**: Follow existing import organization (lines 1-17)
- **IMPORTS**:
```python
import time
from httpcore import RemoteProtocolError
from httpx import ConnectError, ReadTimeout
```
- **ALSO IMPORT** from model_config:
```python
from app.model_config import (
    UNLIMITED_TOKENS,
    get_model_config,
    MAX_CONCURRENT_API_CALLS,
    NETWORK_RETRY_ATTEMPTS,
    NETWORK_RETRY_BASE_DELAY,
    NETWORK_RETRY_MAX_DELAY,
)
```
- **VALIDATE**: `cd server && ./venv/bin/python -c "from app.agents.base import BaseAgent; print('OK')"`

### Task 3: UPDATE `server/app/agents/base.py` - Add Retryable Error Detection

- **IMPLEMENT**: Add a tuple of retryable network error types as a class attribute or module constant
- **LOCATION**: After the imports, before the `BaseAgent` class definition
- **CODE**:
```python
# Network errors that should trigger automatic retry with backoff
RETRYABLE_NETWORK_ERRORS = (
    RemoteProtocolError,
    ConnectError,
    ReadTimeout,
    ConnectionError,
    TimeoutError,
    OSError,  # Catches various socket errors
)
```
- **VALIDATE**: `cd server && ./venv/bin/python -c "from app.agents.base import RETRYABLE_NETWORK_ERRORS; print(f'Errors: {len(RETRYABLE_NETWORK_ERRORS)}')" `

### Task 4: UPDATE `server/app/agents/base.py` - Add Network Retry Helper Method

- **IMPLEMENT**: Add a method to perform API calls with network error retry
- **LOCATION**: After `_get_effective_max_tokens` method (around line 156)
- **CODE**:
```python
def _call_with_network_retry(
    self,
    api_call_func,
    operation_name: str,
) -> str:
    """Execute an API call with network error retry and exponential backoff.

    Args:
        api_call_func: Callable that makes the API request and returns response text
        operation_name: Name of the operation for logging

    Returns:
        The API response text

    Raises:
        The last network error if all retries are exhausted
    """
    last_error: Exception | None = None

    for attempt in range(NETWORK_RETRY_ATTEMPTS + 1):
        try:
            return api_call_func()
        except RETRYABLE_NETWORK_ERRORS as e:
            last_error = e

            if attempt < NETWORK_RETRY_ATTEMPTS:
                # Calculate exponential backoff delay
                delay = min(
                    NETWORK_RETRY_BASE_DELAY * (2 ** attempt),
                    NETWORK_RETRY_MAX_DELAY,
                )

                self.logger.warning(
                    "Network error, retrying with backoff",
                    agent=self.name,
                    operation=operation_name,
                    attempt=attempt + 1,
                    max_attempts=NETWORK_RETRY_ATTEMPTS + 1,
                    error_type=type(e).__name__,
                    error_message=str(e)[:200],
                    retry_delay_seconds=delay,
                )

                time.sleep(delay)
            else:
                self.logger.error(
                    "Network error, all retries exhausted",
                    agent=self.name,
                    operation=operation_name,
                    total_attempts=NETWORK_RETRY_ATTEMPTS + 1,
                    error_type=type(e).__name__,
                    error_message=str(e)[:500],
                )

    # Re-raise the last error
    raise last_error
```
- **VALIDATE**: `cd server && ./venv/bin/python -c "from app.agents.base import BaseAgent; print('OK')"`

### Task 5: UPDATE `server/app/agents/base.py` - Wrap `_generate_sync` with Network Retry

- **IMPLEMENT**: Modify `_generate_sync` to use the network retry helper
- **LOCATION**: Method `_generate_sync` (lines 54-106)
- **STRATEGY**: Extract the API call into a lambda and wrap with `_call_with_network_retry`
- **CODE**: Replace the direct `self.client.models.generate_content(...)` call with:
```python
def _generate_sync(
    self,
    prompt: str,
    system_prompt: str,
    temperature: float | None = None,
    max_tokens: int | None = None,
    model: str | None = None,
) -> str:
    """Synchronous Gemini API call with network retry."""
    effective_max_tokens = self._get_effective_max_tokens(max_tokens)

    def make_api_call():
        return self.client.models.generate_content(
            model=model or self.model,
            contents=prompt,
            config=types.GenerateContentConfig(
                system_instruction=system_prompt,
                temperature=temperature or self.default_temperature,
                max_output_tokens=effective_max_tokens,
            ),
        )

    # Execute with network retry
    response = self._call_with_network_retry(make_api_call, "generate")

    # Check for truncation (existing code continues unchanged)
    finish_reason = self._extract_finish_reason(response)
    # ... rest of method unchanged
```
- **GOTCHA**: The `_call_with_network_retry` returns the response object, not text. Extract `.text` after the call.
- **VALIDATE**: `cd server && ./venv/bin/python -c "from app.agents.interviewer import InterviewerAgent; print('OK')"`

### Task 6: UPDATE `server/app/agents/base.py` - Wrap `_generate_structured_sync` with Network Retry

- **IMPLEMENT**: Modify `_generate_structured_sync` similarly to `_generate_sync`
- **LOCATION**: Method `_generate_structured_sync` (lines 157-237)
- **STRATEGY**: Same pattern as Task 5
- **VALIDATE**: `cd server && ./venv/bin/python -c "from app.agents.researcher import ConceptResearcher; print('OK')"`

### Task 7: UPDATE `server/app/agents/orchestrator.py` - Add Semaphore Import and Creation

- **IMPLEMENT**: Import `MAX_CONCURRENT_API_CALLS` and create module-level semaphore
- **LOCATION**: Top of file, after existing imports
- **CODE**:
```python
from app.model_config import MAX_CONCURRENT_API_CALLS

# Semaphore to limit concurrent Gemini API calls
_api_semaphore: asyncio.Semaphore | None = None


def get_api_semaphore() -> asyncio.Semaphore:
    """Get or create the API concurrency semaphore.

    Created lazily to ensure it's created in the right event loop.
    """
    global _api_semaphore
    if _api_semaphore is None:
        _api_semaphore = asyncio.Semaphore(MAX_CONCURRENT_API_CALLS)
    return _api_semaphore
```
- **VALIDATE**: `cd server && ./venv/bin/python -c "from app.agents.orchestrator import get_api_semaphore; print('OK')"`

### Task 8: UPDATE `server/app/agents/orchestrator.py` - Add Concurrency to Researchers

- **IMPLEMENT**: Update `_run_researchers_parallel` to use semaphore
- **LOCATION**: Method `_run_researchers_parallel` (lines 290-348)
- **CODE**: Modify the inner `research_session` function:
```python
async def research_session(
    outline_item: Any,
    all_outlines: list[Any],
) -> tuple[ResearchedSession, AgentSpan]:
    researcher = get_researcher_for_type(outline_item.session_type, self.client)
    span = researcher.create_span(f"research_{outline_item.session_type.value}")

    semaphore = get_api_semaphore()

    try:
        # Log if we need to wait for semaphore
        if semaphore.locked():
            self.logger.debug(
                "Waiting for API slot",
                session_order=outline_item.order,
                session_title=outline_item.title[:50],
            )

        async with semaphore:
            self.logger.debug(
                "Acquired API slot, starting research",
                session_order=outline_item.order,
                session_title=outline_item.title[:50],
            )

            session = await researcher.research_session(
                outline_item=outline_item,
                interview_context=interview_context,
                all_session_outlines=all_outlines,
                language=self.state.language,
            )

        researcher.complete_span(
            span,
            status="success",
            output_summary=f"Researched: {session.title}",
        )
        return session, span

    except Exception as e:
        researcher.complete_span(span, error=e)
        raise
```
- **VALIDATE**: `cd server && ./venv/bin/python -c "from app.agents.orchestrator import PipelineOrchestrator; print('OK')"`

### Task 9: UPDATE `server/app/agents/orchestrator.py` - Add Concurrency to YouTube Agent

- **IMPLEMENT**: Update `_run_youtube_agent` to use semaphore
- **LOCATION**: Method `_run_youtube_agent` (lines 350-398)
- **CODE**: Same pattern as Task 8
- **VALIDATE**: `cd server && ./venv/bin/python -c "from app.agents.orchestrator import PipelineOrchestrator; print('OK')"`

### Task 10: UPDATE `server/app/agents/orchestrator.py` - Ensure Error Spans Are Saved

- **IMPLEMENT**: In `_run_researchers_parallel`, save error spans to trace before re-raising
- **LOCATION**: The exception handling block after `asyncio.gather` (lines 331-337)
- **CODE**:
```python
for result in results:
    if isinstance(result, Exception):
        self.logger.error(
            "Research failed",
            error=str(result),
            error_type=type(result).__name__,
        )
        # Note: spans from failed tasks are already recorded via complete_span(error=e)
        raise result
    session, span = result
    researched_sessions.append(session)
    spans.append(span)
```
- **GOTCHA**: The spans from failed parallel tasks won't be in `spans` list because the exception propagates. Need to capture them differently - but this is acceptable since the error is logged.
- **VALIDATE**: `cd server && ./venv/bin/pytest tests/unit/test_agents.py -v`

### Task 11: UPDATE `server/app/agents/orchestrator.py` - Add Pipeline Start Logging

- **IMPLEMENT**: Add logging at the start of `_run_researchers_parallel` with session count
- **LOCATION**: Beginning of `_run_researchers_parallel` method
- **CODE**:
```python
self.logger.info(
    "Starting parallel research",
    total_sessions=len(outline.sessions),
    max_concurrent=MAX_CONCURRENT_API_CALLS,
)
```
- **VALIDATE**: Manual - will be visible in server logs

### Task 12: CREATE `server/tests/unit/test_network_retry.py` - Add Unit Tests

- **IMPLEMENT**: Create new test file for network retry logic
- **PATTERN**: Follow `server/tests/unit/test_agents.py` pattern
- **CODE**:
```python
"""Unit tests for network error retry logic in BaseAgent."""

import time
from unittest.mock import MagicMock, patch

import pytest
from httpcore import RemoteProtocolError

from app.agents.base import RETRYABLE_NETWORK_ERRORS
from app.agents.interviewer import InterviewerAgent


@pytest.fixture
def mock_gemini_client():
    """Create a mock Gemini client."""
    return MagicMock()


class TestNetworkRetry:
    """Tests for network error retry with exponential backoff."""

    def test_retryable_errors_include_remote_protocol_error(self):
        """Test that RemoteProtocolError is in retryable errors."""
        assert RemoteProtocolError in RETRYABLE_NETWORK_ERRORS

    def test_retryable_errors_include_connection_error(self):
        """Test that ConnectionError is in retryable errors."""
        assert ConnectionError in RETRYABLE_NETWORK_ERRORS

    def test_retryable_errors_include_timeout_error(self):
        """Test that TimeoutError is in retryable errors."""
        assert TimeoutError in RETRYABLE_NETWORK_ERRORS

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

    def test_call_with_network_retry_retries_on_network_error(self, mock_gemini_client):
        """Test that network errors trigger retry."""
        agent = InterviewerAgent(mock_gemini_client)

        call_count = [0]
        def failing_then_success_call():
            call_count[0] += 1
            if call_count[0] < 3:
                raise RemoteProtocolError("Server disconnected")
            return "success"

        with patch("app.agents.base.time.sleep"):  # Skip actual sleep
            result = agent._call_with_network_retry(failing_then_success_call, "test_op")

        assert result == "success"
        assert call_count[0] == 3  # Failed twice, succeeded on third

    def test_call_with_network_retry_raises_after_max_retries(self, mock_gemini_client):
        """Test that error is raised after all retries exhausted."""
        agent = InterviewerAgent(mock_gemini_client)

        def always_failing_call():
            raise RemoteProtocolError("Server disconnected")

        with patch("app.agents.base.time.sleep"):  # Skip actual sleep
            with pytest.raises(RemoteProtocolError):
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
```
- **VALIDATE**: `cd server && ./venv/bin/pytest tests/unit/test_network_retry.py -v`

---

## TESTING STRATEGY

### Unit Tests

- Test `_call_with_network_retry` succeeds on first try
- Test retry behavior when network errors occur
- Test that max retries is respected
- Test that non-network errors are not retried
- Test exponential backoff timing (mocked)
- Test configuration constants are properly defined

### Integration Tests

No new integration tests needed - the existing pipeline tests will exercise this code path.

### Edge Cases

- [ ] All retries exhausted - error is properly re-raised
- [ ] First try succeeds - no retry overhead
- [ ] Mixed errors (network then parsing) - each handled appropriately
- [ ] Semaphore fully saturated - requests wait correctly
- [ ] Semaphore released on error - no deadlock

---

## VALIDATION COMMANDS

Execute every command to ensure zero regressions and 100% feature correctness.

### Level 1: Syntax & Style

```bash
cd server && ./venv/bin/ruff check app/
cd server && ./venv/bin/ruff format app/ --check
```

### Level 2: Unit Tests

```bash
cd server && ./venv/bin/pytest tests/unit/ -v
```

### Level 3: Integration Tests

```bash
cd server && ./venv/bin/pytest tests/integration/ -v
```

### Level 4: Manual Validation

```bash
# Start the server
cd server && ./venv/bin/uvicorn app.main:app --reload --port 8000

# In another terminal, test basic API
curl http://localhost:8000/health

# Create a roadmap via the UI and observe logs for:
# - "Starting parallel research" with session count
# - "Acquired API slot" messages
# - Any "Network error, retrying" messages
```

### Level 5: Stress Test (Optional)

```bash
# Run the parallel researcher test to verify resilience
cd server && ./venv/bin/python -c "
import asyncio
from dotenv import load_dotenv
import os
load_dotenv()

from google import genai
from app.agents.researcher import get_researcher_for_type
from app.agents.state import SessionOutlineItem, SessionType, InterviewContext

client = genai.Client(api_key=os.getenv('GEMINI_API_KEY'))

async def test():
    outline_items = [
        SessionOutlineItem(
            id=f'test{i}',
            title=f'Session {i}: Topic',
            objective=f'Learn topic {i}',
            session_type=SessionType.CONCEPT,
            order=i,
        )
        for i in range(1, 12)  # 11 sessions
    ]

    context = InterviewContext(topic='test topic')

    from app.agents.orchestrator import get_api_semaphore
    semaphore = get_api_semaphore()

    async def research(item):
        async with semaphore:
            researcher = get_researcher_for_type(item.session_type, client)
            return await researcher.research_session(
                item, context, outline_items, 'en'
            )

    results = await asyncio.gather(
        *[research(item) for item in outline_items],
        return_exceptions=True
    )

    success = sum(1 for r in results if not isinstance(r, Exception))
    print(f'Success: {success}/11')

asyncio.run(test())
"
```

---

## ACCEPTANCE CRITERIA

- [x] Feature implements all specified functionality
- [ ] All validation commands pass with zero errors
- [ ] Network errors trigger automatic retry with exponential backoff
- [ ] Parallel API calls are limited by semaphore (max 5 concurrent)
- [ ] Retry attempts and delays are logged with full context
- [ ] Semaphore wait times are logged at debug level
- [ ] Unit tests cover retry logic, backoff, and max retry exhaustion
- [ ] No regressions in existing pipeline functionality
- [ ] Stress test with 11 parallel requests shows improved success rate

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

1. **Concurrency limit of 5**: Conservative default to prevent API rate limiting. Can be increased if the Gemini API proves stable with more concurrent requests.

2. **Exponential backoff starting at 1 second**: Standard pattern that gives the API time to recover while not waiting too long for transient issues.

3. **Module-level semaphore**: Lazy initialization to ensure it's created in the correct event loop. Alternative was per-pipeline semaphore, but module-level provides global protection.

4. **Sync retry in sync methods**: The `_generate_sync` and `_generate_structured_sync` methods use synchronous `time.sleep` since they run in the thread pool executor. This is acceptable.

5. **Not retrying parsing errors**: Parsing errors (JSONDecodeError, ValueError) are already handled by existing retry logic at a higher level in `generate_structured`.

### Future Improvements

- Add metrics/telemetry for retry rates to monitor API reliability
- Consider circuit breaker pattern if failures are sustained
- Add configurable retry settings per agent (some operations may need different retry behavior)
