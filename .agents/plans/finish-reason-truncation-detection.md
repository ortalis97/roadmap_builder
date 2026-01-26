# Feature: Finish Reason Truncation Detection

The following plan should be complete, but it's important that you validate documentation and codebase patterns and task sanity before you start implementing.

Pay special attention to naming of existing utils, types, and models. Import from the right files etc.

## Feature Description

Detect when Gemini API responses are truncated due to hitting `max_output_tokens` limits by checking the `finish_reason` field. Add a global `UNLIMITED_TOKENS` switch that bypasses token limits for debugging truncation issues.

## User Story

As a developer debugging content truncation issues,
I want to know when Gemini responses hit token limits,
So that I can identify and fix truncation problems quickly.

## Problem Statement

Session content is sometimes truncated mid-sentence (e.g., "like saying" with no continuation). The Gemini API provides a `finish_reason` field that indicates `MAX_TOKENS` when this happens, but our code ignores it. Without visibility into truncation, debugging these issues is difficult.

## Solution Statement

1. Add a global `UNLIMITED_TOKENS = False` constant in `model_config.py`
2. When `UNLIMITED_TOKENS` is `True`, all agents pass `None` for `max_output_tokens` (no limit)
3. Modify `_generate_structured_sync` to extract `finish_reason` from the response
4. When `finish_reason` is `MAX_TOKENS`, log a warning with agent name and configured limit

## Feature Metadata

**Feature Type**: Enhancement (Observability)
**Estimated Complexity**: Low
**Primary Systems Affected**: `server/app/agents/base.py`, `server/app/model_config.py`
**Dependencies**: None (uses existing google-genai SDK)

---

## CONTEXT REFERENCES

### Relevant Codebase Files - IMPORTANT: READ THESE BEFORE IMPLEMENTING!

- `server/app/model_config.py` (lines 1-107) - Where `UNLIMITED_TOKENS` constant will be added and `ModelConfig` class is defined
- `server/app/agents/base.py` (lines 54-72) - `_generate_sync` method showing current API call pattern
- `server/app/agents/base.py` (lines 95-119) - `_generate_structured_sync` method that needs to check finish_reason
- `server/app/agents/base.py` (lines 143-220) - `generate_structured` method that calls `_generate_structured_sync`
- `server/tests/unit/test_model_config.py` - Test patterns for model_config module
- `server/tests/unit/test_agents.py` - Test patterns for agent classes with mocking

### New Files to Create

None - this is an enhancement to existing files only.

### Relevant Documentation

- Gemini API finish_reason values:
  - `STOP` - Normal completion
  - `MAX_TOKENS` - Truncated due to token limit
  - `SAFETY` - Blocked by safety filters
  - `RECITATION` - Blocked for verbatim recitation

- Access pattern: `response.candidates[0].finish_reason.name`

### Patterns to Follow

**Logging Pattern** (from base.py lines 213-218):
```python
self.logger.warning(
    "Failed to parse response",
    attempt=attempt + 1,
    error=str(e),
    use_schema_output=use_schema_output,
)
```

**Model Config Usage** (from base.py lines 30-33):
```python
def __init__(self, client: genai.Client):
    self.client = client
    self._model_config = get_model_config(self.model_config_key)
    self.logger = structlog.get_logger().bind(agent=self.name)
```

**Import Pattern** (from base.py line 16):
```python
from app.model_config import get_model_config
```

---

## IMPLEMENTATION PLAN

### Phase 1: Add Global UNLIMITED_TOKENS Constant

Add a module-level constant in `model_config.py` that allows temporarily bypassing all token limits for debugging.

**Tasks:**
- Add `UNLIMITED_TOKENS = False` constant at module level
- Document its purpose with a comment

### Phase 2: Modify BaseAgent to Check finish_reason

Update the generation methods to extract and check the `finish_reason` field from Gemini responses.

**Tasks:**
- Import `UNLIMITED_TOKENS` in base.py
- Modify `_generate_structured_sync` to return both text and finish_reason
- Update `generate_structured` to handle the tuple return and log warnings
- Similarly update `_generate_sync` and `generate` for non-structured calls
- Apply UNLIMITED_TOKENS logic to bypass max_tokens when enabled

### Phase 3: Testing

Add unit tests to verify the new functionality.

**Tasks:**
- Add test for UNLIMITED_TOKENS constant
- Add test for finish_reason extraction
- Add test for warning log when MAX_TOKENS detected

---

## STEP-BY-STEP TASKS

### Task 1: ADD UNLIMITED_TOKENS constant to model_config.py

- **IMPLEMENT**: Add `UNLIMITED_TOKENS = False` constant at the top of the file, after the imports and before the `GeminiModel` class
- **PATTERN**: Follow existing module-level constant style (none currently, so use standard Python docstring style)
- **IMPORTS**: None needed
- **GOTCHA**: Place it BEFORE the class definitions but AFTER any imports
- **VALIDATE**: `cd server && ./venv/bin/python -c "from app.model_config import UNLIMITED_TOKENS; print(f'UNLIMITED_TOKENS={UNLIMITED_TOKENS}')"`

**Code to add after line 7 (after imports, before GeminiModel class):**
```python
# Global switch to disable all token limits for debugging truncation issues.
# When True, all agents pass max_output_tokens=None to the Gemini API.
# Usage: Temporarily set to True when investigating truncated content.
UNLIMITED_TOKENS = False
```

### Task 2: UPDATE test_model_config.py to test UNLIMITED_TOKENS

- **IMPLEMENT**: Add a test class for the new constant
- **PATTERN**: Follow existing test class structure in test_model_config.py (lines 13-24)
- **IMPORTS**: Add `UNLIMITED_TOKENS` to the import from app.model_config
- **GOTCHA**: Test should verify default is False
- **VALIDATE**: `cd server && ./venv/bin/pytest tests/unit/test_model_config.py -v`

**Code to add:**
```python
# Add to imports at top (line 5-9):
from app.model_config import (
    AGENT_MODELS,
    GeminiModel,
    ModelConfig,
    UNLIMITED_TOKENS,  # ADD THIS
    get_model_config,
)

# Add new test class after TestGeminiModel:
class TestUnlimitedTokens:
    """Tests for UNLIMITED_TOKENS global switch."""

    def test_default_is_false(self):
        """UNLIMITED_TOKENS should be False by default."""
        assert UNLIMITED_TOKENS is False
```

### Task 3: UPDATE base.py imports to include UNLIMITED_TOKENS

- **IMPLEMENT**: Update the import statement to include UNLIMITED_TOKENS
- **PATTERN**: Existing import at line 16: `from app.model_config import get_model_config`
- **IMPORTS**: Add UNLIMITED_TOKENS to the import
- **GOTCHA**: Use multi-line import style if needed
- **VALIDATE**: `cd server && ./venv/bin/python -c "from app.agents.base import BaseAgent; print('Import OK')"`

**Change line 16 from:**
```python
from app.model_config import get_model_config
```

**To:**
```python
from app.model_config import UNLIMITED_TOKENS, get_model_config
```

### Task 4: ADD helper method to extract finish_reason in base.py

- **IMPLEMENT**: Add a static method `_extract_finish_reason` to BaseAgent class that safely extracts finish_reason from a response
- **PATTERN**: Place after `_add_property_ordering` method (around line 93)
- **IMPORTS**: None additional needed
- **GOTCHA**: The response.candidates may be None or empty; handle gracefully
- **VALIDATE**: `cd server && ./venv/bin/ruff check app/agents/base.py`

**Code to add after `_add_property_ordering` method:**
```python
def _extract_finish_reason(self, response) -> str:
    """Extract finish_reason from Gemini response.

    Returns:
        The finish_reason name as string, or "UNKNOWN" if not available.
    """
    try:
        if response.candidates and len(response.candidates) > 0:
            candidate = response.candidates[0]
            if hasattr(candidate, "finish_reason") and candidate.finish_reason:
                return str(candidate.finish_reason.name)
    except Exception:
        pass
    return "UNKNOWN"
```

### Task 5: ADD helper method to get effective max_tokens in base.py

- **IMPLEMENT**: Add a method `_get_effective_max_tokens` that returns None when UNLIMITED_TOKENS is True, otherwise returns the specified or default max_tokens
- **PATTERN**: Place after `_extract_finish_reason` method
- **IMPORTS**: None additional needed
- **GOTCHA**: When UNLIMITED_TOKENS is True, return None regardless of input
- **VALIDATE**: `cd server && ./venv/bin/ruff check app/agents/base.py`

**Code to add after `_extract_finish_reason` method:**
```python
def _get_effective_max_tokens(self, max_tokens: int | None) -> int | None:
    """Get effective max_tokens respecting UNLIMITED_TOKENS global switch.

    Args:
        max_tokens: Explicitly specified max_tokens, or None to use default

    Returns:
        None if UNLIMITED_TOKENS is True, otherwise the specified or default value.
    """
    if UNLIMITED_TOKENS:
        return None
    return max_tokens if max_tokens is not None else self.default_max_tokens
```

### Task 6: UPDATE _generate_sync to check finish_reason

- **IMPLEMENT**: Modify `_generate_sync` to:
  1. Use `_get_effective_max_tokens` for the max_tokens value
  2. Extract finish_reason after the API call
  3. Log a warning if finish_reason is MAX_TOKENS
- **PATTERN**: Follow existing logging pattern (lines 213-218)
- **IMPORTS**: None additional
- **GOTCHA**: Must still return only the text (don't change return type to avoid breaking callers)
- **VALIDATE**: `cd server && ./venv/bin/ruff check app/agents/base.py`

**Modify `_generate_sync` method (lines 54-72) to:**
```python
def _generate_sync(
    self,
    prompt: str,
    system_prompt: str,
    temperature: float | None = None,
    max_tokens: int | None = None,
    model: str | None = None,
) -> str:
    """Synchronous Gemini API call."""
    effective_max_tokens = self._get_effective_max_tokens(max_tokens)

    response = self.client.models.generate_content(
        model=model or self.model,
        contents=prompt,
        config=types.GenerateContentConfig(
            system_instruction=system_prompt,
            temperature=temperature or self.default_temperature,
            max_output_tokens=effective_max_tokens,
        ),
    )

    # Check for truncation
    finish_reason = self._extract_finish_reason(response)
    if finish_reason == "MAX_TOKENS":
        self.logger.warning(
            "Response truncated due to max_tokens limit",
            agent=self.name,
            configured_max_tokens=self.default_max_tokens,
            effective_max_tokens=effective_max_tokens,
            finish_reason=finish_reason,
        )

    return response.text
```

### Task 7: UPDATE _generate_structured_sync to check finish_reason

- **IMPLEMENT**: Apply the same changes as Task 6 to `_generate_structured_sync`
- **PATTERN**: Same as Task 6
- **IMPORTS**: None additional
- **GOTCHA**: This method uses dict config instead of GenerateContentConfig - still works the same
- **VALIDATE**: `cd server && ./venv/bin/ruff check app/agents/base.py`

**Modify `_generate_structured_sync` method (lines 95-119) to:**
```python
def _generate_structured_sync(
    self,
    prompt: str,
    system_prompt: str,
    response_schema: dict,
    temperature: float | None = None,
    max_tokens: int | None = None,
    model: str | None = None,
) -> str:
    """Synchronous Gemini API call with schema-constrained output."""
    # Add propertyOrdering for Gemini compatibility
    schema_with_ordering = self._add_property_ordering(response_schema)
    effective_max_tokens = self._get_effective_max_tokens(max_tokens)

    response = self.client.models.generate_content(
        model=model or self.model,
        contents=prompt,
        config={
            "system_instruction": system_prompt,
            "temperature": temperature or self.default_temperature,
            "max_output_tokens": effective_max_tokens,
            "response_mime_type": "application/json",
            "response_json_schema": schema_with_ordering,
        },
    )

    # Check for truncation
    finish_reason = self._extract_finish_reason(response)
    if finish_reason == "MAX_TOKENS":
        self.logger.warning(
            "Structured response truncated due to max_tokens limit",
            agent=self.name,
            configured_max_tokens=self.default_max_tokens,
            effective_max_tokens=effective_max_tokens,
            finish_reason=finish_reason,
        )

    return response.text
```

### Task 8: ADD unit tests for finish_reason detection in test_agents.py

- **IMPLEMENT**: Add tests that verify:
  1. `_extract_finish_reason` returns correct value from mock response
  2. `_get_effective_max_tokens` respects UNLIMITED_TOKENS
  3. Warning is logged when MAX_TOKENS detected
- **PATTERN**: Follow existing test patterns in test_agents.py (MagicMock for responses)
- **IMPORTS**: Add `patch` if not already imported
- **GOTCHA**: Need to mock UNLIMITED_TOKENS for testing since it's a module constant
- **VALIDATE**: `cd server && ./venv/bin/pytest tests/unit/test_agents.py -v`

**Code to add at end of test_agents.py:**
```python
class TestBaseAgentFinishReason:
    """Tests for finish_reason detection in BaseAgent."""

    def test_extract_finish_reason_returns_stop(self, mock_gemini_client):
        """Test extracting STOP finish_reason."""
        from app.agents.interviewer import InterviewerAgent

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
        from app.agents.interviewer import InterviewerAgent

        agent = InterviewerAgent(mock_gemini_client)

        mock_response = MagicMock()
        mock_candidate = MagicMock()
        mock_candidate.finish_reason.name = "MAX_TOKENS"
        mock_response.candidates = [mock_candidate]

        result = agent._extract_finish_reason(mock_response)
        assert result == "MAX_TOKENS"

    def test_extract_finish_reason_handles_empty_candidates(self, mock_gemini_client):
        """Test extracting finish_reason when candidates is empty."""
        from app.agents.interviewer import InterviewerAgent

        agent = InterviewerAgent(mock_gemini_client)

        mock_response = MagicMock()
        mock_response.candidates = []

        result = agent._extract_finish_reason(mock_response)
        assert result == "UNKNOWN"

    def test_extract_finish_reason_handles_none_candidates(self, mock_gemini_client):
        """Test extracting finish_reason when candidates is None."""
        from app.agents.interviewer import InterviewerAgent

        agent = InterviewerAgent(mock_gemini_client)

        mock_response = MagicMock()
        mock_response.candidates = None

        result = agent._extract_finish_reason(mock_response)
        assert result == "UNKNOWN"

    def test_get_effective_max_tokens_default(self, mock_gemini_client):
        """Test _get_effective_max_tokens returns default when not unlimited."""
        from app.agents.interviewer import InterviewerAgent

        agent = InterviewerAgent(mock_gemini_client)

        # When UNLIMITED_TOKENS is False (default), should return default
        with patch("app.agents.base.UNLIMITED_TOKENS", False):
            result = agent._get_effective_max_tokens(None)
            assert result == agent.default_max_tokens

    def test_get_effective_max_tokens_explicit(self, mock_gemini_client):
        """Test _get_effective_max_tokens respects explicit value."""
        from app.agents.interviewer import InterviewerAgent

        agent = InterviewerAgent(mock_gemini_client)

        with patch("app.agents.base.UNLIMITED_TOKENS", False):
            result = agent._get_effective_max_tokens(5000)
            assert result == 5000

    def test_get_effective_max_tokens_unlimited(self, mock_gemini_client):
        """Test _get_effective_max_tokens returns None when unlimited."""
        from app.agents.interviewer import InterviewerAgent

        agent = InterviewerAgent(mock_gemini_client)

        with patch("app.agents.base.UNLIMITED_TOKENS", True):
            result = agent._get_effective_max_tokens(5000)
            assert result is None

            result = agent._get_effective_max_tokens(None)
            assert result is None
```

### Task 9: RUN all validation commands

- **IMPLEMENT**: Run linting, type checking, and all tests
- **VALIDATE**: See Validation Commands section below

---

## TESTING STRATEGY

### Unit Tests

Following existing patterns in `tests/unit/test_agents.py`:

1. **test_extract_finish_reason_returns_stop** - Verify extraction of STOP
2. **test_extract_finish_reason_returns_max_tokens** - Verify extraction of MAX_TOKENS
3. **test_extract_finish_reason_handles_empty_candidates** - Edge case: empty list
4. **test_extract_finish_reason_handles_none_candidates** - Edge case: None
5. **test_get_effective_max_tokens_default** - Default behavior
6. **test_get_effective_max_tokens_explicit** - Explicit value respected
7. **test_get_effective_max_tokens_unlimited** - UNLIMITED_TOKENS=True returns None

### Integration Tests

Not needed - this is internal behavior that doesn't change API contracts.

### Edge Cases

- Empty candidates list
- None candidates
- Missing finish_reason attribute on candidate
- Exception during extraction (should return "UNKNOWN")

---

## VALIDATION COMMANDS

Execute every command to ensure zero regressions and 100% feature correctness.

### Level 1: Syntax & Style

```bash
cd server && ./venv/bin/ruff check app/model_config.py app/agents/base.py
cd server && ./venv/bin/ruff format --check app/model_config.py app/agents/base.py
```

### Level 2: Import Verification

```bash
cd server && ./venv/bin/python -c "from app.model_config import UNLIMITED_TOKENS; print(f'UNLIMITED_TOKENS={UNLIMITED_TOKENS}')"
cd server && ./venv/bin/python -c "from app.agents.base import BaseAgent; print('BaseAgent imports OK')"
```

### Level 3: Unit Tests

```bash
cd server && ./venv/bin/pytest tests/unit/test_model_config.py -v
cd server && ./venv/bin/pytest tests/unit/test_agents.py -v -k "TestBaseAgentFinishReason"
cd server && ./venv/bin/pytest tests/unit/ -v
```

### Level 4: Full Test Suite

```bash
cd server && ./venv/bin/pytest -v
```

### Level 5: Manual Validation

1. Set `UNLIMITED_TOKENS = True` temporarily in `model_config.py`
2. Run the dev server: `cd server && ./venv/bin/uvicorn app.main:app --reload`
3. Create a roadmap with a complex topic
4. Check logs for any "max_tokens limit" warnings
5. Reset `UNLIMITED_TOKENS = False`

---

## ACCEPTANCE CRITERIA

- [x] `UNLIMITED_TOKENS = False` constant exists in `model_config.py`
- [ ] Setting `UNLIMITED_TOKENS = True` causes all agents to pass `max_output_tokens=None`
- [ ] When `finish_reason` is `MAX_TOKENS`, a warning is logged with:
  - Agent name
  - Configured max_tokens
  - Effective max_tokens used
  - finish_reason value
- [ ] All existing unit tests pass
- [ ] All existing integration tests pass
- [ ] New unit tests pass for:
  - `_extract_finish_reason` method
  - `_get_effective_max_tokens` method
  - `UNLIMITED_TOKENS` constant default value
- [ ] Linting passes with no errors
- [ ] No breaking changes to existing agent behavior

---

## COMPLETION CHECKLIST

- [ ] All tasks completed in order
- [ ] Each task validation passed immediately
- [ ] All validation commands executed successfully
- [ ] Full test suite passes (unit + integration)
- [ ] No linting or type checking errors
- [ ] Manual testing confirms warning appears for truncation
- [ ] Acceptance criteria all met
- [ ] Code reviewed for quality and maintainability

---

## NOTES

### Design Decisions

1. **Global switch vs per-agent config**: The user requested a simple global switch for debugging, not a per-agent setting. This keeps the implementation simple and matches the debugging use case.

2. **Warning only, no retry**: The user explicitly requested logging a warning rather than implementing automatic retry logic. This keeps the change minimal and non-breaking.

3. **Return type unchanged**: The `_generate_sync` and `_generate_structured_sync` methods still return `str` only, avoiding breaking changes to all callers.

4. **Helper methods**: Added `_extract_finish_reason` and `_get_effective_max_tokens` as instance methods for clean separation and testability.

### Related Files

An existing draft plan exists at `.agents/plans/finish-reason-truncation-mitigation.md` with a more complex retry-based approach. This plan implements the simpler version requested by the user.

### Future Enhancements

- Could add finish_reason to AgentSpan for tracing visibility
- Could implement retry logic with increasing token limits
- Could add per-agent unlimited_tokens config if needed
