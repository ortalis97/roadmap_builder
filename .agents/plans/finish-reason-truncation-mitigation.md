# Plan: Finish Reason Truncation Mitigation

## Objective
Detect and handle content truncation caused by token limits in Gemini API responses by:
1. Checking `finish_reason` from Gemini responses
2. Retrying with higher limits when `MAX_TOKENS` is detected
3. Adding an `unlimited_tokens` switch to ModelConfig

---

## Background

### Problem
Session content is sometimes truncated mid-sentence (e.g., "like saying" with no continuation). This happens when Gemini hits the `max_output_tokens` limit before completing the content.

### Solution Approach
The Gemini API returns a `finish_reason` field in the response:
- `STOP` - Normal completion
- `MAX_TOKENS` - Hit the token limit (content truncated)
- `SAFETY` - Blocked by safety filters
- `RECITATION` - Blocked for potential verbatim recitation

We can detect `MAX_TOKENS` and retry with higher/no limits.

---

## Part A: Add `unlimited_tokens` Flag to ModelConfig

### Changes to `server/app/model_config.py`

1. Add `unlimited_tokens` parameter to `ModelConfig`:
```python
class ModelConfig:
    def __init__(
        self,
        model: GeminiModel,
        temperature: float,
        max_tokens: int,
        reason: str,
        unlimited_tokens: bool = False,  # NEW
    ):
        self.model = model
        self.temperature = temperature
        self.max_tokens = max_tokens
        self.reason = reason
        self.unlimited_tokens = unlimited_tokens  # NEW
```

2. Update `researcher` config to use unlimited_tokens:
```python
"researcher": ModelConfig(
    GeminiModel.FLASH,
    0.7,
    12288,
    "Educational content quality matters",
    unlimited_tokens=True,  # Allow retry without limits on truncation
),
```

---

## Part B: Check `finish_reason` in BaseAgent

### Changes to `server/app/agents/base.py`

1. Create a custom exception for truncation:
```python
class ContentTruncatedError(Exception):
    """Raised when Gemini response was truncated due to max_tokens."""
    pass
```

2. Modify `_generate_structured_sync` to return full response (not just text):
```python
def _generate_structured_sync(
    self,
    prompt: str,
    system_prompt: str,
    response_schema: dict,
    temperature: float | None = None,
    max_tokens: int | None = None,
    model: str | None = None,
) -> tuple[str, str]:  # Returns (text, finish_reason)
    """Synchronous Gemini API call with schema-constrained output."""
    schema_with_ordering = self._add_property_ordering(response_schema)

    response = self.client.models.generate_content(
        model=model or self.model,
        contents=prompt,
        config={
            "system_instruction": system_prompt,
            "temperature": temperature or self.default_temperature,
            "max_output_tokens": max_tokens or self.default_max_tokens,
            "response_mime_type": "application/json",
            "response_json_schema": schema_with_ordering,
        },
    )

    # Extract finish_reason from response
    finish_reason = "STOP"  # Default
    if response.candidates and len(response.candidates) > 0:
        candidate = response.candidates[0]
        if hasattr(candidate, 'finish_reason') and candidate.finish_reason:
            finish_reason = str(candidate.finish_reason.name)

    return response.text, finish_reason
```

3. Modify `generate_structured` to handle truncation with retry:
```python
async def generate_structured(
    self,
    prompt: str,
    response_model: type[T],
    system_prompt: str | None = None,
    max_retries: int = 2,
    use_schema_output: bool = True,
    temperature: float | None = None,
    max_tokens: int | None = None,
    model: str | None = None,
) -> T:
    """Generate and parse structured output into a Pydantic model."""
    last_error: Exception | None = None
    current_max_tokens = max_tokens

    for attempt in range(max_retries + 1):
        try:
            if use_schema_output:
                json_schema = response_model.model_json_schema()

                loop = asyncio.get_event_loop()
                response_text, finish_reason = await loop.run_in_executor(
                    None,
                    partial(
                        self._generate_structured_sync,
                        prompt,
                        system_prompt or self.get_system_prompt(),
                        json_schema,
                        temperature,
                        current_max_tokens,
                        model,
                    ),
                )

                # Check for truncation
                if finish_reason == "MAX_TOKENS":
                    self.logger.warning(
                        "Response truncated due to max_tokens",
                        attempt=attempt + 1,
                        max_tokens=current_max_tokens,
                        unlimited_allowed=self._model_config.unlimited_tokens,
                    )

                    # If unlimited_tokens is enabled, retry without limit
                    if self._model_config.unlimited_tokens and current_max_tokens is not None:
                        current_max_tokens = None  # Remove limit for retry
                        raise ContentTruncatedError("Retrying without token limit")
                    else:
                        self.logger.error(
                            "Content truncated but unlimited_tokens not enabled",
                            agent=self.name,
                        )
                        # Continue with truncated content (best effort)

                return response_model.model_validate_json(response_text)
            else:
                # Legacy path (unchanged)
                ...

        except ContentTruncatedError:
            last_error = e
            continue  # Retry with no limit

        except (json.JSONDecodeError, ValueError) as e:
            last_error = e
            self.logger.warning(
                "Failed to parse response",
                attempt=attempt + 1,
                error=str(e),
                use_schema_output=use_schema_output,
            )

    raise ValueError(f"Failed after {max_retries + 1} attempts: {last_error}")
```

4. Similarly update `_generate_sync` and `generate` methods for non-structured calls.

---

## Part C: Logging Improvements

Add structured logging for truncation events to help debugging:

```python
self.logger.warning(
    "content_truncation_detected",
    agent=self.name,
    operation="generate_structured",
    finish_reason=finish_reason,
    max_tokens_configured=self.default_max_tokens,
    max_tokens_used=current_max_tokens,
    will_retry=self._model_config.unlimited_tokens,
)
```

---

## Implementation Order

1. **model_config.py**: Add `unlimited_tokens` flag to ModelConfig class
2. **model_config.py**: Update researcher config to set `unlimited_tokens=True`
3. **base.py**: Add `ContentTruncatedError` exception class
4. **base.py**: Modify `_generate_structured_sync` to return finish_reason
5. **base.py**: Modify `generate_structured` to check finish_reason and retry
6. **base.py**: Update `_generate_sync` and `generate` similarly
7. **Test**: Create a roadmap and verify no truncation in researcher output

---

## Files Summary

| File | Action |
|------|--------|
| `server/app/model_config.py` | Edit - add unlimited_tokens parameter |
| `server/app/agents/base.py` | Edit - check finish_reason, retry on truncation |

---

## Testing

1. **Manual test**: Create a roadmap with a complex topic that produces long content
2. **Log verification**: Check logs for any `content_truncation_detected` warnings
3. **Retry verification**: Confirm retries happen when truncation detected (with logging)

---

## Future Considerations

- Could add finish_reason to AgentSpan for tracing
- Could add metrics/alerts for truncation frequency
- Could make retry behavior configurable per-agent
