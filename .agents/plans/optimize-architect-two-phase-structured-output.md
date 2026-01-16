# Feature: Optimize Architect Agent with Two-Phase Approach and Structured Output

The following plan should be complete, but it's important that you validate documentation and codebase patterns and task sanity before you start implementing.

Pay special attention to naming of existing utils, types, and models. Import from the right files etc.

## Feature Description

Optimize the architect agent's roadmap creation process by:
1. **Two-phase approach**: Split the architect into a fast Phase 1 (title + session outline) and parallel Phase 2 (detailed session info)
2. **Gemini structured output**: Use the `response_schema` parameter to guarantee valid JSON output instead of manual parsing
3. **Progressive UI updates**: Stream title immediately after Phase 1 completes

This significantly reduces perceived latency and eliminates JSON parsing failures.

## User Story

As a learner creating a roadmap
I want the "designing" phase to complete faster
So that I don't have to wait as long before seeing my roadmap structure

## Problem Statement

The current architect agent is slow (~5-10 seconds) because:
1. It generates all session details (title, objective, type, duration, prerequisites) in a single large API call
2. The response is manually parsed with retry logic, adding latency on failures
3. Users see no feedback until the entire architect phase completes

## Solution Statement

1. **Phase 1 (fast)**: Single API call to get roadmap title + minimal session list (title, type, order only)
2. **Phase 2 (parallel)**: Multiple parallel API calls to get details for each session (objective, duration, prerequisites)
3. **Structured output**: Use Gemini's `response_schema` to guarantee JSON structure, eliminating parse failures
4. **Progressive SSE**: Emit title immediately after Phase 1, show "designing session 1/N" during Phase 2

## Feature Metadata

**Feature Type**: Enhancement
**Estimated Complexity**: Medium-High
**Primary Systems Affected**: `server/app/agents/` (base, architect, orchestrator)
**Dependencies**: google-genai SDK (already installed, version ≥1.0.0)

---

## CONTEXT REFERENCES

### Relevant Codebase Files IMPORTANT: YOU MUST READ THESE FILES BEFORE IMPLEMENTING!

- `server/app/agents/base.py` (lines 38-115) - Why: Contains `generate_structured()` method that needs updating for schema output
- `server/app/agents/architect.py` (full file) - Why: Main file to refactor with two-phase approach
- `server/app/agents/state.py` (lines 68-86) - Why: `SessionOutlineItem` and `SessionOutline` models to understand/modify
- `server/app/agents/orchestrator.py` (lines 227-264) - Why: `_run_architect()` method that calls architect agent
- `server/app/agents/prompts.py` (lines 18-42) - Why: `ARCHITECT_SYSTEM_PROMPT` needs updating
- `server/app/services/ai_service.py` (lines 116-131) - Why: Pattern for Gemini API calls with `types.GenerateContentConfig`
- `server/tests/unit/test_agents.py` (lines 79-125) - Why: Test pattern for architect agent

### New Files to Create

None - all changes are modifications to existing files

### Relevant Documentation

**Gemini Structured Output** (from official docs: https://ai.google.dev/gemini-api/docs/structured-output):

```python
from google import genai
from pydantic import BaseModel, Field
from typing import List

class Ingredient(BaseModel):
    name: str = Field(description="Name of the ingredient.")
    quantity: str = Field(description="Quantity of the ingredient.")

class Recipe(BaseModel):
    recipe_name: str = Field(description="The name of the recipe.")
    ingredients: List[Ingredient]
    instructions: List[str]

client = genai.Client()

response = client.models.generate_content(
    model="gemini-2.0-flash",
    contents=prompt,
    config={
        "response_mime_type": "application/json",
        "response_json_schema": Recipe.model_json_schema(),  # NOT response_schema!
    },
)

# Parse directly with Pydantic
recipe = Recipe.model_validate_json(response.text)
```

**CRITICAL for Gemini 2.0**: The docs note that "Gemini 2.0 requires an explicit `propertyOrdering` list within the JSON input to define the preferred structure." We must add this to schemas.

**Key API details**:
- Config param is `response_json_schema` (NOT `response_schema`)
- Use `model_validate_json(response.text)` for parsing (simpler than json.loads + validate)
- Supported types: string, number, integer, boolean, object, array, null
- Use `Field(description="...")` in Pydantic models for better results

### Patterns to Follow

**Naming Conventions:**
- Agent classes: `{Name}Agent` (e.g., `ArchitectAgent`)
- Response models: `{Name}Response` (e.g., `ArchitectResponse`)
- Methods: `snake_case` async methods (e.g., `create_outline`, `generate_structured`)

**Pydantic → JSON Schema Pattern:**
```python
from pydantic import BaseModel

class MyResponse(BaseModel):
    field: str

# Convert Pydantic to JSON schema for Gemini
schema = MyResponse.model_json_schema()
```

**Async Gemini Call Pattern (from base.py):**
```python
async def generate(self, prompt: str, ...) -> str:
    loop = asyncio.get_event_loop()
    return await loop.run_in_executor(
        None,
        partial(self._generate_sync, prompt, ...),
    )
```

**Error Handling Pattern:**
- Log warnings on recoverable errors
- Raise `ValueError` with context on failures
- Use structlog for all logging

---

## IMPLEMENTATION PLAN

### Phase 1: Add Structured Output Support to BaseAgent

Update `BaseAgent` to support Gemini's schema-constrained output via `response_schema` parameter.

**Tasks:**
- Add new `_generate_structured_sync()` method that uses `response_mime_type` and `response_schema`
- Update `generate_structured()` to use the new method
- Keep fallback to manual parsing for backward compatibility

### Phase 2: Create Two-Phase Architect Models

Define new Pydantic models for the two-phase output:
- Phase 1: Minimal outline (title + session titles/types)
- Phase 2: Session details (objective, duration, prerequisites)

**Tasks:**
- Add `ArchitectPhase1Response` model
- Add `SessionDetailResponse` model for Phase 2
- Keep existing `ArchitectResponse` for backward compatibility during transition

### Phase 3: Implement Two-Phase Architect Logic

Split `create_outline()` into two phases with parallel execution in Phase 2.

**Tasks:**
- Implement `create_outline_phase1()` for fast title + structure
- Implement `get_session_details()` for individual session details
- Update `create_outline()` to orchestrate both phases

### Phase 4: Update Orchestrator for Progressive Updates

Modify orchestrator to emit SSE events during architect phase.

**Tasks:**
- Emit title immediately after Phase 1
- Emit progress during Phase 2 session details
- Update SSE event types if needed

### Phase 5: Update Tests

Update unit tests to cover new functionality.

**Tasks:**
- Add tests for structured output generation
- Add tests for two-phase architect flow
- Update existing tests for new behavior

---

## STEP-BY-STEP TASKS

IMPORTANT: Execute every task in order, top to bottom. Each task is atomic and independently testable.

### Task 1: UPDATE `server/app/agents/base.py` - Add structured output method

- **IMPLEMENT**: Add `_generate_structured_sync()` method that uses Gemini's `response_json_schema`
- **PATTERN**: Follow existing `_generate_sync()` pattern at lines 38-55
- **IMPORTS**: No new imports needed (use dict config, not types.GenerateContentConfig)
- **GOTCHA**: Gemini 2.0 requires `propertyOrdering` in schema - add helper to inject this

```python
def _add_property_ordering(self, schema: dict) -> dict:
    """Add propertyOrdering to schema for Gemini 2.0 compatibility.

    Gemini 2.0 requires explicit propertyOrdering to ensure consistent output order.
    """
    schema = schema.copy()
    if "properties" in schema:
        schema["propertyOrdering"] = list(schema["properties"].keys())
        # Recursively add to nested objects
        for prop_schema in schema["properties"].values():
            if isinstance(prop_schema, dict):
                if prop_schema.get("type") == "object":
                    self._add_property_ordering(prop_schema)
                elif prop_schema.get("type") == "array" and "items" in prop_schema:
                    if prop_schema["items"].get("type") == "object":
                        self._add_property_ordering(prop_schema["items"])
    return schema

def _generate_structured_sync(
    self,
    prompt: str,
    system_prompt: str,
    response_schema: dict,
    temperature: float | None = None,
    max_tokens: int | None = None,
) -> str:
    """Synchronous Gemini API call with schema-constrained output."""
    # Add propertyOrdering for Gemini 2.0 compatibility
    schema_with_ordering = self._add_property_ordering(response_schema)

    response = self.client.models.generate_content(
        model="gemini-2.0-flash",
        contents=prompt,
        config={
            "system_instruction": system_prompt,
            "temperature": temperature or self.default_temperature,
            "max_output_tokens": max_tokens or self.default_max_tokens,
            "response_mime_type": "application/json",
            "response_json_schema": schema_with_ordering,
        },
    )
    return response.text
```

- **VALIDATE**: `cd server && ./venv/bin/python -c "from app.agents.base import BaseAgent; print('Import OK')"`

### Task 2: UPDATE `server/app/agents/base.py` - Update generate_structured()

- **IMPLEMENT**: Modify `generate_structured()` to use schema-constrained output
- **PATTERN**: Use `response_model.model_json_schema()` to get JSON schema from Pydantic
- **PATTERN**: Use `response_model.model_validate_json()` for simpler parsing (no json.loads needed)
- **GOTCHA**: Keep fallback path for backward compatibility

```python
async def generate_structured(
    self,
    prompt: str,
    response_model: type[T],
    system_prompt: str | None = None,
    max_retries: int = 2,
    use_schema_output: bool = True,  # New parameter
) -> T:
    """Generate and parse structured output into a Pydantic model.

    Args:
        prompt: The user prompt
        response_model: Pydantic model class to validate against
        system_prompt: Optional system prompt override
        max_retries: Number of retry attempts
        use_schema_output: If True, use Gemini's response_json_schema for guaranteed JSON
    """
    last_error: Exception | None = None

    for attempt in range(max_retries + 1):
        try:
            if use_schema_output:
                # Get JSON schema from Pydantic model
                json_schema = response_model.model_json_schema()

                # Use schema-constrained output
                loop = asyncio.get_event_loop()
                response_text = await loop.run_in_executor(
                    None,
                    partial(
                        self._generate_structured_sync,
                        prompt,
                        system_prompt or self.get_system_prompt(),
                        json_schema,
                    ),
                )

                # Parse directly with Pydantic (simpler than json.loads + validate)
                return response_model.model_validate_json(response_text)
            else:
                # Fallback to manual parsing (legacy path)
                response_text = await self.generate(
                    prompt=prompt,
                    system_prompt=system_prompt,
                )

                # Clean markdown code blocks if present
                cleaned = response_text.strip()
                if cleaned.startswith("```json"):
                    cleaned = cleaned[7:]
                if cleaned.startswith("```"):
                    cleaned = cleaned[3:]
                if cleaned.endswith("```"):
                    cleaned = cleaned[:-3]
                cleaned = cleaned.strip()

                data = json.loads(cleaned)
                return response_model.model_validate(data)

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

- **VALIDATE**: `cd server && ./venv/bin/pytest tests/unit/test_agents.py -v -k "test_" --tb=short`

### Task 3: UPDATE `server/app/agents/architect.py` - Add Phase 1 response model

- **IMPLEMENT**: Add `ArchitectPhase1Response` model for fast initial outline
- **PATTERN**: Follow existing `ArchitectResponse` pattern at lines 27-33
- **IMPORTS**: None new needed

```python
class SessionOutlineMinimal(BaseModel):
    """Minimal session info for Phase 1 (fast)."""
    title: str
    session_type: str  # concept|tutorial|practice|project|review


class ArchitectPhase1Response(BaseModel):
    """Phase 1 response: title and minimal session list."""
    title: str
    sessions: list[SessionOutlineMinimal]
    learning_path_summary: str
```

- **VALIDATE**: `cd server && ./venv/bin/python -c "from app.agents.architect import ArchitectPhase1Response; print('Import OK')"`

### Task 4: UPDATE `server/app/agents/architect.py` - Add Phase 2 response model

- **IMPLEMENT**: Add `SessionDetailResponse` model for per-session details
- **PATTERN**: Follow existing Pydantic patterns

```python
class SessionDetailResponse(BaseModel):
    """Phase 2 response: detailed info for a single session."""
    objective: str
    estimated_duration_minutes: int = 60
    prerequisites: list[int] = Field(default_factory=list)  # 0-based indices
```

- **VALIDATE**: `cd server && ./venv/bin/python -c "from app.agents.architect import SessionDetailResponse; print('Import OK')"`

### Task 5: UPDATE `server/app/agents/architect.py` - Add create_outline_phase1()

- **IMPLEMENT**: New method for Phase 1 that returns title + minimal session list
- **PATTERN**: Follow existing `create_outline()` pattern but with smaller output
- **GOTCHA**: Use a simpler prompt focused only on structure

```python
async def create_outline_phase1(
    self,
    interview_context: InterviewContext,
) -> ArchitectPhase1Response:
    """Phase 1: Get roadmap title and session structure (fast).

    Returns minimal session info for quick response.
    """
    qa_context = "\n".join([f"Q: {q}\nA: {a}" for q, a in interview_context.qa_pairs])

    prompt = f"""Create a learning roadmap structure for:

Topic: {interview_context.topic}

Learner Context:
{qa_context if qa_context else "No additional context provided"}

Create 5-15 sessions. For each session, specify only:
- title: Clear session title
- session_type: One of concept, tutorial, practice, project, review

Also provide:
- title: Descriptive roadmap title (3-8 words)
- learning_path_summary: 2-3 sentence overview"""

    return await self.generate_structured(
        prompt=prompt,
        response_model=ArchitectPhase1Response,
    )
```

- **VALIDATE**: `cd server && ./venv/bin/python -c "from app.agents.architect import ArchitectAgent; print('Method OK')"`

### Task 6: UPDATE `server/app/agents/architect.py` - Add get_session_details()

- **IMPLEMENT**: New method to get details for a single session
- **PATTERN**: Similar to researcher pattern but lighter weight

```python
async def get_session_details(
    self,
    session_title: str,
    session_type: str,
    session_index: int,
    all_session_titles: list[str],
    topic: str,
) -> SessionDetailResponse:
    """Phase 2: Get detailed info for a single session.

    Args:
        session_title: Title of this session
        session_type: Type of session (concept, tutorial, etc.)
        session_index: 0-based index of this session
        all_session_titles: List of all session titles for context
        topic: Main learning topic
    """
    sessions_context = "\n".join(
        f"{i}. {title}" for i, title in enumerate(all_session_titles)
    )

    prompt = f"""For this learning session, provide:

Session: {session_title}
Type: {session_type}
Position: Session {session_index + 1} of {len(all_session_titles)}

Topic: {topic}

All sessions in order:
{sessions_context}

Provide:
- objective: What the learner will achieve (1-2 sentences)
- estimated_duration_minutes: Realistic time to complete (30-180)
- prerequisites: List of session indices (0-based) that must come before this one"""

    return await self.generate_structured(
        prompt=prompt,
        response_model=SessionDetailResponse,
    )
```

- **VALIDATE**: `cd server && ./venv/bin/python -c "from app.agents.architect import ArchitectAgent; print('Method OK')"`

### Task 7: UPDATE `server/app/agents/architect.py` - Update create_outline() for two-phase

- **IMPLEMENT**: Refactor `create_outline()` to use two-phase approach with parallel Phase 2
- **PATTERN**: Follow `asyncio.gather()` pattern from orchestrator.py lines 300-302
- **IMPORTS**: Add `import asyncio` if not present

```python
async def create_outline(
    self,
    interview_context: InterviewContext,
) -> tuple[str, SessionOutline]:
    """Create a session outline based on interview context.

    Uses two-phase approach:
    1. Fast call to get title + session structure
    2. Parallel calls to get details for each session

    Returns:
        A tuple of (suggested_title, session_outline)
    """
    # Phase 1: Get structure quickly
    phase1 = await self.create_outline_phase1(interview_context)

    # Phase 2: Get details for each session in parallel
    all_titles = [s.title for s in phase1.sessions]

    async def get_details(idx: int, session: SessionOutlineMinimal) -> SessionDetailResponse:
        return await self.get_session_details(
            session_title=session.title,
            session_type=session.session_type,
            session_index=idx,
            all_session_titles=all_titles,
            topic=interview_context.topic,
        )

    tasks = [get_details(i, s) for i, s in enumerate(phase1.sessions)]
    details_list = await asyncio.gather(*tasks)

    # Combine into SessionOutline
    sessions = []
    for i, (minimal, details) in enumerate(zip(phase1.sessions, details_list)):
        session_id = f"session_{uuid.uuid4().hex[:8]}"

        try:
            session_type = SessionType(minimal.session_type.lower())
        except ValueError:
            session_type = SessionType.CONCEPT

        sessions.append(
            SessionOutlineItem(
                id=session_id,
                title=minimal.title,
                objective=details.objective,
                session_type=session_type,
                estimated_duration_minutes=details.estimated_duration_minutes,
                prerequisites=[
                    sessions[idx].id for idx in details.prerequisites if idx < len(sessions)
                ],
                order=i + 1,
            )
        )

    # Calculate total hours
    total_minutes = sum(s.estimated_duration_minutes for s in sessions)
    total_hours = round(total_minutes / 60, 1)

    outline = SessionOutline(
        sessions=sessions,
        learning_path_summary=phase1.learning_path_summary,
        total_estimated_hours=total_hours,
    )

    return phase1.title, outline
```

- **VALIDATE**: `cd server && ./venv/bin/pytest tests/unit/test_agents.py::TestArchitectAgent -v --tb=short`

### Task 8: UPDATE `server/app/agents/prompts.py` - Simplify architect prompt

- **IMPLEMENT**: Update `ARCHITECT_SYSTEM_PROMPT` to focus on structure, not JSON details
- **PATTERN**: Keep the session type explanations
- **GOTCHA**: Remove JSON format instructions since structured output handles this

```python
ARCHITECT_SYSTEM_PROMPT = """You are a learning architect who designs structured learning paths.
Given interview context and a learning topic, create a session outline.

Generate a descriptive, engaging title for the roadmap (3-8 words) that captures
the learning journey.

Each session must have a type:
- concept: Theory, definitions, mental models (for understanding)
- tutorial: Step-by-step guided learning (for skill building)
- practice: Exercises, challenges, drills (for reinforcement)
- project: Hands-on building projects (for application)
- review: Recap, assessment, reflection (for consolidation)

Guidelines:
- Create 5-15 sessions depending on scope
- Progress from fundamentals to advanced
- Mix session types for engagement (don't cluster all concepts first)
- First session should be accessible to beginners in that topic
- Generate a clear, descriptive title that captures the learning goal"""
```

- **VALIDATE**: `cd server && ./venv/bin/python -c "from app.agents.prompts import ARCHITECT_SYSTEM_PROMPT; print('OK')"`

### Task 9: UPDATE `server/tests/unit/test_agents.py` - Add Phase 1 test

- **IMPLEMENT**: Add test for `create_outline_phase1()` method
- **PATTERN**: Follow existing `TestArchitectAgent` pattern at lines 79-125

```python
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
```

- **VALIDATE**: `cd server && ./venv/bin/pytest tests/unit/test_agents.py::TestArchitectAgent::test_create_outline_phase1_returns_minimal_outline -v`

### Task 10: UPDATE `server/tests/unit/test_agents.py` - Add two-phase integration test

- **IMPLEMENT**: Add test for full two-phase `create_outline()` flow
- **PATTERN**: Follow existing test patterns

```python
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

    call_count = 0

    async def mock_generate_structured(prompt, response_model, **kwargs):
        nonlocal call_count
        if response_model.__name__ == "ArchitectPhase1Response":
            return phase1_response
        else:
            result = detail_responses[call_count]
            call_count += 1
            return result

    with patch.object(agent, "generate_structured", side_effect=mock_generate_structured):
        context = InterviewContext(topic="Python")
        title, outline = await agent.create_outline(context)

        assert title == "Python Mastery"
        assert len(outline.sessions) == 2
        assert outline.sessions[0].objective == "Learn basics"
        assert outline.sessions[1].objective == "Practice skills"
        # Check prerequisites were resolved
        assert outline.sessions[1].prerequisites == [outline.sessions[0].id]
```

- **VALIDATE**: `cd server && ./venv/bin/pytest tests/unit/test_agents.py::TestArchitectAgent -v --tb=short`

### Task 11: RUN full test suite

- **IMPLEMENT**: Run all tests to ensure no regressions
- **VALIDATE**: `cd server && ./venv/bin/pytest -v --tb=short`

### Task 12: RUN linting

- **IMPLEMENT**: Ensure code passes linting
- **VALIDATE**: `cd server && ./venv/bin/ruff check app/ --fix && ./venv/bin/ruff format app/`

---

## TESTING STRATEGY

### Unit Tests

- Test `generate_structured()` with schema output enabled
- Test `create_outline_phase1()` returns minimal structure
- Test `get_session_details()` returns session details
- Test `create_outline()` two-phase flow with mocked responses
- Test backward compatibility with existing agents

### Integration Tests

- Test full pipeline with mocked Gemini client
- Verify SSE events are emitted correctly
- Test error handling when Phase 2 calls fail

### Edge Cases

- Empty interview context (no Q&A pairs)
- Invalid session types from Gemini (should fallback to CONCEPT)
- Prerequisites referencing future sessions (should be filtered)
- Very large session counts (15+ sessions)

---

## VALIDATION COMMANDS

Execute every command to ensure zero regressions and 100% feature correctness.

### Level 1: Syntax & Style

```bash
cd server && ./venv/bin/ruff check app/ && ./venv/bin/ruff format app/ --check
```

### Level 2: Unit Tests

```bash
cd server && ./venv/bin/pytest tests/unit/ -v --tb=short
```

### Level 3: Integration Tests

```bash
cd server && ./venv/bin/pytest tests/integration/ -v --tb=short
```

### Level 4: Manual Validation

1. Start the backend: `cd server && ./venv/bin/uvicorn app.main:app --reload --port 8000`
2. Start the frontend: `cd client && ~/.bun/bin/bun run dev`
3. Create a new roadmap and observe:
   - Title appears faster than before (within ~2-3 seconds)
   - "Designing" phase shows progress
   - No JSON parsing errors in logs
4. Check server logs for timing information

### Level 5: Performance Comparison

Before implementing, note the current architect duration in logs. After implementing, compare:
- Phase 1 should complete in ~2-3 seconds
- Phase 2 should complete in ~3-5 seconds (parallel)
- Total should be similar or slightly faster, but UX is much better

---

## ACCEPTANCE CRITERIA

- [ ] `generate_structured()` uses Gemini's `response_schema` for guaranteed JSON
- [ ] Architect Phase 1 returns title + minimal session list in ~2-3 seconds
- [ ] Architect Phase 2 fetches session details in parallel
- [ ] Title is available to UI after Phase 1 (before session details)
- [ ] All existing tests pass without modification (backward compatible)
- [ ] New unit tests cover two-phase flow
- [ ] No JSON parsing errors in logs during roadmap creation
- [ ] Linting passes with zero errors
- [ ] Integration tests pass

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

1. **Schema output vs manual parsing**: Using Gemini's `response_schema` eliminates entire categories of bugs (malformed JSON, markdown code blocks, etc.) and makes the code simpler.

2. **Two-phase vs single call**: The two-phase approach trades slightly more total API calls for:
   - Faster perceived response (title shows in ~2s vs ~8s)
   - Better parallelization (5+ concurrent calls vs 1 sequential)
   - Smaller, more focused prompts (better quality)

3. **Backward compatibility**: The `use_schema_output` parameter allows gradual rollout and fallback if issues arise.

### Potential Risks

1. **Gemini rate limits**: More API calls could hit rate limits faster. Monitor during testing.
2. **Schema compatibility**: The `response_schema` format may have quirks with complex nested types. Test thoroughly.
3. **Phase 2 failures**: If one session detail call fails, the whole pipeline fails. Consider adding retry logic per-session.

### Future Improvements

1. **Streaming Phase 2**: Emit SSE events as each session detail completes (not just at end)
2. **Caching**: Cache common session structures for similar topics
3. **Adaptive parallelism**: Limit concurrent calls based on session count to avoid rate limits
