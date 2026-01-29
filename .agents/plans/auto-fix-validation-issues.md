# Feature: Auto-Fix Validation Issues with Editor Agent

The following plan should be complete, but it's important that you validate documentation and codebase patterns and task sanity before you start implementing.

Pay special attention to naming of existing utils, types, and models. Import from the right files etc.

## Feature Description

Transform the validation step in the roadmap creation pipeline from a user-facing review stage to an automatic, transparent quality gate. When the validator identifies issues (gaps, overlaps, coherence problems), a new **Editor Agent** performs surgical edits to fix issues — preserving good content and only regenerating what's necessary. The Editor dynamically decides when to call a mini-researcher for missing content (critical gaps only). The user only sees "Validating..." in the progress indicator.

## User Story

As a learner creating a roadmap,
I want the system to automatically fix any quality issues found during validation,
So that I get a high-quality roadmap without having to review technical validation issues myself.

## Problem Statement

Currently, when the validator finds issues:
1. The pipeline stops and emits a `validation_result` SSE event
2. Frontend shows `ValidationReview` component where user must select issues to fix
3. The "Fix Roadmap" button calls `submitReview(false, issueIds)` but this does NOT actually fix anything — `proceed_after_review` just saves the roadmap anyway
4. This creates a confusing UX where users see technical issues they can't meaningfully act on

Additionally, simply re-running the full researcher is a **blunt instrument**:
- Loses good content from the original session
- Expensive (full API call for minor edits)
- Can't do targeted fixes like "remove this duplicate section"

## Solution Statement

1. **Remove user review step** — Validation happens transparently in the background
2. **Editor Agent** — New agent that performs surgical edits:
   - Analyzes each issue and the original content
   - Makes targeted edits (remove overlaps, improve coherence, adjust depth)
   - Dynamically decides if critical missing content needs mini-research
   - Calls researcher only for specific missing sections, not full regeneration
   - Returns full edited content (preserving good parts)
3. **Auto-fix loop** — Up to 2 edit attempts if validation still fails
4. **Always save** — After fix attempts (or if initially valid), proceed to save
5. **Keep videos** — Don't refresh YouTube videos during fix attempts
6. **Comprehensive logging** — Log all validation results and edit events for debugging

## Feature Metadata

**Feature Type**: Bug Fix / Enhancement
**Estimated Complexity**: Medium-High
**Primary Systems Affected**:
- `server/app/agents/editor.py` (NEW FILE - Editor Agent)
- `server/app/agents/orchestrator.py` (main pipeline logic)
- `server/app/agents/prompts.py` (add Editor prompts)
- `server/app/agents/state.py` (add fix attempt tracking)
- `server/app/model_config.py` (add Editor model config)
- `client/src/hooks/useRoadmapCreation.ts` (simplify flow)
- `client/src/pages/CreateRoadmapPage.tsx` (remove ValidationReview rendering)
**Dependencies**: None (all existing libraries)

---

## CONTEXT REFERENCES

### Relevant Codebase Files IMPORTANT: YOU MUST READ THESE FILES BEFORE IMPLEMENTING!

- `server/app/agents/base.py` - Why: Base agent class that Editor will extend
- `server/app/agents/validator.py` (lines 46-134) - Why: Shows `ValidationResult` structure and how issues are created
- `server/app/agents/researcher.py` (lines 52-111) - Why: Pattern for agent that generates content; Editor may call researcher
- `server/app/agents/orchestrator.py` (lines 141-260) - Why: Contains `run_pipeline()` that needs auto-fix loop
- `server/app/agents/orchestrator.py` (lines 305-391) - Why: Contains `_run_researchers_parallel()` pattern for parallel execution
- `server/app/agents/state.py` (lines 93-117) - Why: Shows `ResearchedSession` model that Editor will modify
- `server/app/agents/state.py` (lines 132-150) - Why: Shows `ValidationIssue` model with issue types and affected_session_ids
- `server/app/agents/prompts.py` - Why: All prompts live here; add Editor prompts
- `server/app/model_config.py` - Why: Model assignments; add Editor config
- `client/src/hooks/useRoadmapCreation.ts` (lines 55-116) - Why: SSE event handling to simplify
- `client/src/pages/CreateRoadmapPage.tsx` (lines 87-106) - Why: `user_review` rendering to remove

### New Files to Create

- `server/app/agents/editor.py` — Editor Agent for surgical content fixes

### Files to Modify

1. `server/app/agents/prompts.py` — Add `EDITOR_SYSTEM_PROMPT`
2. `server/app/model_config.py` — Add `"editor"` model config
3. `server/app/agents/state.py` — Add fix attempt tracking fields to `PipelineState`
4. `server/app/agents/orchestrator.py` — Add `_run_editor()` and auto-fix loop
5. `client/src/hooks/useRoadmapCreation.ts` — Remove `user_review` stage handling
6. `client/src/pages/CreateRoadmapPage.tsx` — Remove ValidationReview rendering

### Patterns to Follow

**Base Agent structure (from base.py):**
```python
class BaseAgent:
    name = "base"
    model_config_key = "researcher"  # Override in subclass

    def __init__(self, client: genai.Client):
        self.client = client
        self.logger = structlog.get_logger().bind(agent=self.name)

    def get_system_prompt(self) -> str:
        raise NotImplementedError

    async def generate_structured(self, prompt: str, response_model: type[T]) -> T:
        # ... generates structured output
```

**Researcher pattern for content generation:**
```python
async def research_session(
    self,
    outline_item: SessionOutlineItem,
    interview_context: InterviewContext,
    all_session_outlines: list[SessionOutlineItem],
    language: str = "en",
) -> ResearchedSession:
    prompt = f"""..."""
    response = await self.generate_structured(
        prompt=prompt,
        response_model=ResearchResponse,
    )
    return ResearchedSession(...)
```

**Model config pattern:**
```python
AGENT_MODELS: dict[str, ModelConfig] = {
    "researcher": ModelConfig(
        GeminiModel.FLASH_2_0,
        0.7,
        12288,
        "Educational content generation",
    ),
}
```

---

## IMPLEMENTATION PLAN

### Phase 1: Editor Agent Foundation

Create the Editor Agent with its prompt and model configuration.

**Tasks:**
- Add `EDITOR_SYSTEM_PROMPT` to prompts.py
- Add `"editor"` and `"editor_research"` model configs
- Create `editor.py` with `EditorAgent` class

### Phase 2: Editor Logic Implementation

Implement the core editing logic with dynamic research decision.

**Tasks:**
- Editor analyzes issue type and decides action
- For OVERLAP/COHERENCE/ORDERING/DEPTH: direct editing
- For GAP: assess if missing content is critical
- If critical GAP: call mini-researcher for specific section
- Merge any new research into existing content
- Return full edited session content

### Phase 3: Orchestrator Integration

Wire the Editor into the pipeline's auto-fix loop.

**Tasks:**
- Add fix attempt tracking to `PipelineState`
- Create `_run_editor()` method in orchestrator
- Modify `run_pipeline()` for auto-fix loop
- Remove USER_REVIEW stage emission

### Phase 4: Frontend Simplification

Remove the validation review UI.

**Tasks:**
- Remove `validation_result` SSE handling
- Remove ValidationReview and TitleConfirmation rendering
- Clean up unused types

---

## STEP-BY-STEP TASKS

IMPORTANT: Execute every task in order, top to bottom. Each task is atomic and independently testable.

### Task 1: UPDATE `server/app/agents/prompts.py` - Add Editor prompts

- **IMPLEMENT**: Add `EDITOR_SYSTEM_PROMPT` and `EDITOR_RESEARCH_REQUEST_PROMPT`
- **LOCATION**: After `YOUTUBE_RERANK_PROMPT` (end of file)
- **IMPORTS**: No new imports needed

```python
EDITOR_SYSTEM_PROMPT = """You are an expert learning content editor specializing in \
quality improvements and surgical fixes.

Your role is to edit existing learning session content to fix specific quality issues \
identified by a validator, while preserving all good content.

EDITING PRINCIPLES:
1. **Preserve good content** — Only modify what's necessary to fix the issue
2. **Surgical precision** — Make targeted edits, not wholesale rewrites
3. **Maintain voice** — Keep the original writing style and tone
4. **Improve flow** — Ensure edits integrate smoothly with surrounding content

ISSUE TYPE HANDLING:

**OVERLAP** (content repeated across sessions):
- Remove or condense the duplicate content
- Add a brief reference to the other session if helpful
- Example: "For more details on X, see Session 3"

**GAP** (missing prerequisite content):
- Assess if the gap is critical or minor
- For minor gaps: Add a brief explanation or reference
- For critical gaps: Set needs_research=true with specific research_request

**ORDERING** (sessions in wrong order):
- Add transitional context to bridge knowledge gaps
- Include brief recap of concepts assumed known
- Improve section headings for clarity

**COHERENCE** (content doesn't flow well):
- Improve transitions between sections
- Add connecting sentences
- Restructure paragraphs for better logical flow

**DEPTH** (too shallow or too deep):
- Too shallow: Expand key concepts with more detail
- Too deep: Simplify explanations, remove tangential details
- Ensure depth matches the session's intended level

OUTPUT FORMAT:
Return a JSON object with:
- edited_content: The complete edited session content (full markdown)
- needs_research: Boolean - true only if critical content is missing
- research_request: If needs_research, describe exactly what content to generate

Be conservative with needs_research — only set true for truly critical gaps \
that cannot be addressed with a brief explanation.
"""

EDITOR_RESEARCH_REQUEST_PROMPT = """You are generating a specific section of content \
to fill a gap in an existing learning session.

IMPORTANT: Generate ONLY the requested content section, not a full session.
This content will be merged into an existing session.

Keep the content:
- Focused on the specific request
- Appropriately sized (not too long)
- Written to integrate smoothly with existing content
- At the appropriate depth level for the session

Output JSON:
{
  "section_content": "The markdown content for this section...",
  "suggested_heading": "Optional heading for this section"
}
"""
```

- **VALIDATE**: `cd server && ./venv/bin/python -c "from app.agents.prompts import EDITOR_SYSTEM_PROMPT; print('Editor prompt loaded, length:', len(EDITOR_SYSTEM_PROMPT))"`

### Task 2: UPDATE `server/app/model_config.py` - Add Editor model configs

- **IMPLEMENT**: Add `"editor"` and `"editor_research"` entries to `AGENT_MODELS`
- **LOCATION**: After `"validator"` entry in `AGENT_MODELS` dict (around line 77)

```python
    # Editor agent for surgical content fixes
    "editor": ModelConfig(
        GeminiModel.FLASH,
        0.5,  # Lower temperature for more consistent edits
        12288,
        "Surgical content editing",
    ),
    "editor_research": ModelConfig(
        GeminiModel.FLASH_LITE,
        0.7,
        4096,  # Smaller output for targeted sections
        "Gap-filling research sections",
    ),
```

- **VALIDATE**: `cd server && ./venv/bin/python -c "from app.model_config import get_model_config; e = get_model_config('editor'); print(f'Editor: {e.model.value}, temp={e.temperature}')"`

### Task 3: UPDATE `server/app/agents/state.py` - Add fix tracking and Editor response models

- **IMPLEMENT**: Add `fix_attempt` and `fix_history` fields to `PipelineState`
- **IMPLEMENT**: Add `EditorDecision` model for Editor output
- **LOCATION**: Add EditorDecision after `ValidationResult` (line ~150), add fields to PipelineState after line 200

```python
# Add after ValidationResult class (around line 150):

class EditorDecision(BaseModel):
    """Editor's decision for how to handle an issue."""

    edited_content: str  # Full edited session content
    needs_research: bool = False  # True if critical gap needs research
    research_request: str | None = None  # What to research if needs_research


# Add to PipelineState class (after user_selected_issues field):

    # Fix attempt tracking
    fix_attempt: int = 0  # Current fix attempt (0 = initial, 1 = first fix, 2 = second fix)
    fix_history: list[dict] = Field(default_factory=list)  # Log of fix attempts for debugging
```

- **VALIDATE**: `cd server && ./venv/bin/python -c "from app.agents.state import PipelineState, EditorDecision; p = PipelineState(pipeline_id='t', user_id='t', topic='t'); print(f'fix_attempt={p.fix_attempt}'); e = EditorDecision(edited_content='test'); print(f'needs_research={e.needs_research}')"`

### Task 4: CREATE `server/app/agents/editor.py` - Editor Agent

- **IMPLEMENT**: Create EditorAgent class that performs surgical edits
- **PATTERN**: Follow BaseAgent pattern from base.py and researcher.py
- **IMPORTS**: Import from base, prompts, state, researcher, model_config

```python
"""Editor agent for surgical content fixes."""

from pydantic import BaseModel, Field

from app.agents.base import BaseAgent
from app.agents.prompts import EDITOR_SYSTEM_PROMPT, EDITOR_RESEARCH_REQUEST_PROMPT, get_language_instruction
from app.agents.researcher import get_researcher_for_type, ResearchResponse
from app.agents.state import (
    EditorDecision,
    InterviewContext,
    ResearchedSession,
    SessionOutlineItem,
    ValidationIssue,
)


class EditorResponse(BaseModel):
    """Response schema for editor output."""

    edited_content: str = Field(description="Complete edited session content in markdown")
    needs_research: bool = Field(default=False, description="True if critical gap needs research")
    research_request: str | None = Field(default=None, description="What to research if needs_research")


class ResearchSectionResponse(BaseModel):
    """Response schema for gap-filling research."""

    section_content: str = Field(description="The markdown content for this section")
    suggested_heading: str | None = Field(default=None, description="Optional heading for this section")


class EditorAgent(BaseAgent):
    """Agent that performs surgical edits to fix validation issues."""

    name = "editor"
    model_config_key = "editor"

    def get_system_prompt(self) -> str:
        return EDITOR_SYSTEM_PROMPT

    async def edit_session(
        self,
        session: ResearchedSession,
        issues: list[ValidationIssue],
        outline_item: SessionOutlineItem,
        interview_context: InterviewContext,
        all_session_outlines: list[SessionOutlineItem],
        language: str = "en",
    ) -> ResearchedSession:
        """Edit a session to fix validation issues.

        Args:
            session: The session to edit
            issues: List of validation issues affecting this session
            outline_item: The session's outline for context
            interview_context: Interview context for research if needed
            all_session_outlines: All session outlines for context
            language: Language code for content

        Returns:
            Edited ResearchedSession with fixed content
        """
        # Build issues description
        issues_text = "\n".join([
            f"- **{issue.issue_type.value.upper()}** ({issue.severity}): {issue.description}\n"
            f"  Suggested fix: {issue.suggested_fix}"
            for issue in issues
        ])

        # Build other sessions context for overlap awareness
        other_sessions = [s for s in all_session_outlines if s.order != outline_item.order]
        sessions_context = "\n".join([
            f"- Session {s.order}: {s.title} ({s.session_type.value})"
            for s in other_sessions
        ]) if other_sessions else "This is the only session"

        language_instruction = get_language_instruction(language)

        prompt = f"""{language_instruction}Edit the following learning session content to fix the identified issues.

SESSION INFORMATION:
Title: {session.title}
Type: {session.session_type.value}
Objective: {outline_item.objective}
Order in roadmap: {session.order}

OTHER SESSIONS IN ROADMAP:
{sessions_context}

ISSUES TO FIX:
{issues_text}

CURRENT CONTENT:
{session.content}

---

Analyze each issue and make surgical edits to fix them while preserving good content.
Only set needs_research=true if there's a critical knowledge gap that cannot be
addressed with a brief explanation.

Output JSON:
{{
  "edited_content": "Complete edited markdown content...",
  "needs_research": false,
  "research_request": null
}}"""

        response = await self.generate_structured(
            prompt=prompt,
            response_model=EditorResponse,
        )

        edited_content = response.edited_content

        # If research needed, fetch specific section and merge
        if response.needs_research and response.research_request:
            self.logger.info(
                "Editor requesting research for gap",
                session_order=session.order,
                research_request=response.research_request[:100],
            )

            research_section = await self._fetch_research_section(
                research_request=response.research_request,
                session=session,
                outline_item=outline_item,
                interview_context=interview_context,
                language=language,
            )

            # Merge research section into edited content
            if research_section:
                edited_content = self._merge_research(
                    edited_content,
                    research_section,
                )

        # Return updated session with edited content
        return ResearchedSession(
            outline_id=session.outline_id,
            title=session.title,
            session_type=session.session_type,
            order=session.order,
            content=edited_content,
            key_concepts=session.key_concepts,  # Preserve
            resources=session.resources,  # Preserve
            exercises=session.exercises,  # Preserve
            videos=session.videos,  # Preserve videos
            language=language,
        )

    async def _fetch_research_section(
        self,
        research_request: str,
        session: ResearchedSession,
        outline_item: SessionOutlineItem,
        interview_context: InterviewContext,
        language: str,
    ) -> ResearchSectionResponse | None:
        """Fetch a specific section to fill a content gap.

        Uses a lighter model for targeted research.
        """
        # Use the editor_research model config
        original_config_key = self.model_config_key
        self.model_config_key = "editor_research"

        language_instruction = get_language_instruction(language)

        prompt = f"""{language_instruction}Generate content to fill a gap in a learning session.

SESSION CONTEXT:
Title: {session.title}
Type: {session.session_type.value}
Objective: {outline_item.objective}
Topic: {interview_context.topic}

RESEARCH REQUEST:
{research_request}

Generate a focused section of content that addresses this specific gap.
Keep it concise but complete enough to fill the knowledge gap.

Output JSON:
{{
  "section_content": "Markdown content for this section...",
  "suggested_heading": "Optional heading"
}}"""

        try:
            response = await self.generate_structured(
                prompt=prompt,
                response_model=ResearchSectionResponse,
            )
            return response
        except Exception as e:
            self.logger.warning(
                "Research section fetch failed, proceeding without",
                error=str(e),
            )
            return None
        finally:
            self.model_config_key = original_config_key

    def _merge_research(
        self,
        edited_content: str,
        research_section: ResearchSectionResponse,
    ) -> str:
        """Merge researched section into edited content.

        Simple strategy: append at end with heading.
        Future improvement: use AI to find optimal insertion point.
        """
        heading = research_section.suggested_heading or "Additional Information"
        section = f"\n\n## {heading}\n\n{research_section.section_content}"
        return edited_content + section
```

- **VALIDATE**: `cd server && ./venv/bin/ruff check app/agents/editor.py && ./venv/bin/python -c "from app.agents.editor import EditorAgent; print('EditorAgent imported successfully')"`

### Task 5: UPDATE `server/app/agents/orchestrator.py` - Add Editor import and _run_editor method

- **IMPLEMENT**: Import EditorAgent and add `_run_editor()` method
- **LOCATION**: Add import at top (around line 14), add method after `_run_validator()` (around line 500)
- **IMPORTS**: Add `from app.agents.editor import EditorAgent`

Add to imports:
```python
from app.agents.editor import EditorAgent
```

Add method:
```python
async def _run_editor(
    self,
    validation_result: ValidationResult,
    outline: SessionOutline,
    researched_sessions: list[ResearchedSession],
    interview_context: InterviewContext,
) -> list[ResearchedSession]:
    """Run Editor agent to fix validation issues surgically.

    Args:
        validation_result: The validation result with issues
        outline: Session outline for context
        researched_sessions: Current sessions (some will be edited)
        interview_context: Interview context for research if needed

    Returns:
        Updated list of researched sessions with edited sessions
    """
    self.state.fix_attempt += 1
    self.state.stage = PipelineStage.REVISING

    # Group issues by session
    issues_by_session: dict[str, list[ValidationIssue]] = {}
    for issue in validation_result.issues:
        for session_id in issue.affected_session_ids:
            if session_id not in issues_by_session:
                issues_by_session[session_id] = []
            issues_by_session[session_id].append(issue)

    self.logger.info(
        "Starting edit attempt",
        attempt=self.state.fix_attempt,
        sessions_to_edit=len(issues_by_session),
        total_issues=len(validation_result.issues),
    )

    # Log fix attempt to history
    self.state.fix_history.append({
        "attempt": self.state.fix_attempt,
        "issues_count": len(validation_result.issues),
        "affected_sessions": list(issues_by_session.keys()),
        "issues": [
            {"type": i.issue_type.value, "severity": i.severity, "description": i.description}
            for i in validation_result.issues
        ],
    })

    # Map outline items and sessions by ID for quick lookup
    outline_by_id = {item.id: item for item in outline.sessions}
    sessions_by_id = {s.outline_id: s for s in researched_sessions}

    editor = EditorAgent(self.client)
    spans: list[AgentSpan] = []

    # Edit each affected session
    async def edit_session(session_id: str) -> tuple[str, ResearchedSession, AgentSpan]:
        session = sessions_by_id.get(session_id)
        outline_item = outline_by_id.get(session_id)
        issues = issues_by_session.get(session_id, [])

        if not session or not outline_item:
            self.logger.warning(
                "Session or outline not found for editing",
                session_id=session_id,
            )
            return session_id, session, None

        span = editor.create_span(f"edit_{session.order}")

        semaphore = get_api_semaphore()

        try:
            async with semaphore:
                self.logger.debug(
                    "Editing session",
                    session_order=session.order,
                    session_title=session.title[:50],
                    issues_count=len(issues),
                )

                edited_session = await editor.edit_session(
                    session=session,
                    issues=issues,
                    outline_item=outline_item,
                    interview_context=interview_context,
                    all_session_outlines=outline.sessions,
                    language=self.state.language,
                )

            editor.complete_span(
                span,
                status="success",
                output_summary=f"Edited: {edited_session.title}",
            )
            return session_id, edited_session, span

        except Exception as e:
            editor.complete_span(span, error=e)
            raise

    # Edit all affected sessions in parallel
    tasks = [edit_session(session_id) for session_id in issues_by_session.keys()]
    results = await asyncio.gather(*tasks, return_exceptions=True)

    # Build updated session list
    edited_sessions_map: dict[str, ResearchedSession] = {}

    for result in results:
        if isinstance(result, Exception):
            self.logger.error("Edit failed", error=str(result))
            raise result
        session_id, edited_session, span = result
        if edited_session:
            edited_sessions_map[session_id] = edited_session
        if span:
            spans.append(span)

    # Replace edited sessions in the list
    updated_sessions = []
    for session in researched_sessions:
        if session.outline_id in edited_sessions_map:
            updated_sessions.append(edited_sessions_map[session.outline_id])
        else:
            updated_sessions.append(session)

    # Sort by order
    updated_sessions.sort(key=lambda s: s.order)

    # Add spans to trace
    self.trace.spans.extend(spans)
    await self.trace.save()

    self.logger.info(
        "Edit attempt complete",
        attempt=self.state.fix_attempt,
        sessions_edited=len(edited_sessions_map),
    )

    return updated_sessions
```

- **VALIDATE**: `cd server && ./venv/bin/ruff check app/agents/orchestrator.py && ./venv/bin/python -c "from app.agents.orchestrator import PipelineOrchestrator; print('Import OK')"`

### Task 6: UPDATE `server/app/agents/orchestrator.py` - Modify run_pipeline() for auto-fix loop

- **IMPLEMENT**: Replace the validation/user_review flow with auto-fix loop using Editor
- **LOCATION**: Modify `run_pipeline()` method, replace lines ~206-250 (after YouTube agent, validation section)
- **CHANGES**:
  1. After `_run_validator()`, if not valid, enter edit loop
  2. Loop: edit → re-validate → repeat up to 2 times
  3. After loop (or if initially valid), go directly to save
  4. Remove USER_REVIEW stage emissions

Replace the validation section with:

```python
# Run validator
yield SSEEvent(
    event="stage_update",
    data={"stage": "validating", "message": "Validating roadmap quality..."},
)
validation_result = await self._run_validator(outline, researched_sessions)

# Auto-fix loop: up to 2 attempts if validation fails
max_fix_attempts = 2
while not validation_result.is_valid and self.state.fix_attempt < max_fix_attempts:
    self.logger.info(
        "Validation failed, attempting edit fix",
        attempt=self.state.fix_attempt + 1,
        max_attempts=max_fix_attempts,
        issues=len(validation_result.issues),
        score=validation_result.overall_score,
    )

    yield SSEEvent(
        event="stage_update",
        data={
            "stage": "validating",
            "message": f"Improving content quality (attempt {self.state.fix_attempt + 1}/{max_fix_attempts})...",
        },
    )

    # Run Editor agent to fix issues
    researched_sessions = await self._run_editor(
        validation_result,
        outline,
        researched_sessions,
        interview_context,
    )
    self.state.researched_sessions = researched_sessions

    # Re-validate
    yield SSEEvent(
        event="stage_update",
        data={"stage": "validating", "message": "Re-validating..."},
    )
    validation_result = await self._run_validator(outline, researched_sessions)

# Log final validation state
if validation_result.is_valid:
    self.logger.info(
        "Validation passed",
        attempts=self.state.fix_attempt,
        final_score=validation_result.overall_score,
    )
else:
    self.logger.warning(
        "Validation still has issues after max edit attempts, proceeding anyway",
        attempts=self.state.fix_attempt,
        remaining_issues=len(validation_result.issues),
        final_score=validation_result.overall_score,
    )

# Store final validation result for debugging
self.state.validation_result = validation_result

# Proceed directly to save (no user review)
yield SSEEvent(
    event="stage_update",
    data={"stage": "saving", "message": "Saving your roadmap..."},
)

roadmap = await self._save_roadmap(outline, researched_sessions)

self.state.stage = PipelineStage.COMPLETE
self.trace.final_status = "success"
await self.trace.save()

yield SSEEvent(
    event="complete",
    data={
        "roadmap_id": str(roadmap.id),
        "message": "Roadmap created successfully!",
    },
)
```

- **GOTCHA**: Remove the `return` statement that was after `validation_result` emission
- **GOTCHA**: Make sure `interview_context` is in scope (constructed earlier in method)
- **VALIDATE**: `cd server && ./venv/bin/ruff check app/agents/orchestrator.py && ./venv/bin/ruff format app/agents/orchestrator.py --check`

### Task 7: UPDATE `server/app/agents/orchestrator.py` - Simplify proceed_after_review()

- **IMPLEMENT**: Keep for backwards compatibility, log deprecation warning
- **LOCATION**: Method at lines ~558-640

```python
async def proceed_after_review(
    self,
    accept_as_is: bool = False,
    issues_to_fix: list[str] | None = None,
    confirmed_title: str | None = None,
) -> AsyncGenerator[SSEEvent, None]:
    """Continue pipeline after user review (DEPRECATED).

    Validation/fixing is now automatic. This method just saves the roadmap.
    """
    self.logger.warning(
        "proceed_after_review called - deprecated, validation is now automatic",
        pipeline_id=self.pipeline_id,
    )

    if not self.state or not self.trace:
        raise ValueError("Pipeline not initialized")

    if confirmed_title:
        self.state.confirmed_title = confirmed_title

    try:
        yield SSEEvent(
            event="stage_update",
            data={"stage": "saving", "message": "Saving your roadmap..."},
        )

        roadmap = await self._save_roadmap(
            self.state.session_outline,
            self.state.researched_sessions,
        )

        self.state.stage = PipelineStage.COMPLETE
        self.trace.final_status = "success"
        await self.trace.save()

        yield SSEEvent(
            event="complete",
            data={
                "roadmap_id": str(roadmap.id),
                "message": "Roadmap created successfully!",
            },
        )

    except Exception as e:
        self.state.stage = PipelineStage.ERROR
        self.state.error_message = str(e)
        self.trace.final_status = "error"
        await self.trace.save()

        self.logger.exception("Pipeline failed", error=str(e))
        yield SSEEvent(
            event="error",
            data={"message": str(e)},
        )
```

- **VALIDATE**: `cd server && ./venv/bin/ruff check app/agents/orchestrator.py`

### Task 8: UPDATE `client/src/hooks/useRoadmapCreation.ts` - Remove user_review handling

- **IMPLEMENT**: Remove `validation_result` SSE event handling
- **LOCATION**: Lines 88-95 (validation_result case in handleSSEEvent)
- **CHANGES**: Delete or comment out the `case 'validation_result'` block

```typescript
// DELETE this case from handleSSEEvent:
// case 'validation_result': {
//   const data = event.data as ValidationResult;
//   updateState({
//     stage: 'user_review',
//     progress: { stage: 'user_review', message: 'Review required' },
//     validationResult: data,
//   });
//   break;
// }
```

- **VALIDATE**: `cd client && ~/.bun/bin/bun run lint`

### Task 9: UPDATE `client/src/pages/CreateRoadmapPage.tsx` - Remove ValidationReview

- **IMPLEMENT**: Remove user_review stage rendering and related imports/handlers
- **LOCATION**: Lines 4-7 (imports), lines 46-52 (handlers), lines 87-106 (rendering)
- **CHANGES**:
  1. Remove `ValidationReview` import
  2. Remove `TitleConfirmation` import
  3. Remove `handleAcceptValidation` and `handleFixIssues` handlers
  4. Remove the `if (state.stage === 'user_review' ...)` rendering block

Remove imports:
```typescript
// DELETE:
import { ValidationReview } from '../components/creation/ValidationReview';
import { TitleConfirmation } from '../components/creation/TitleConfirmation';
```

Remove handlers:
```typescript
// DELETE:
const handleAcceptValidation = () => {
  submitReview(true);
};

const handleFixIssues = (issueIds: string[]) => {
  submitReview(false, issueIds);
};
```

Remove rendering block (lines ~87-106):
```typescript
// DELETE this entire block:
// Show validation review with title confirmation
if (state.stage === 'user_review' && state.validationResult) {
  return (
    <div className="max-w-3xl mx-auto py-6 space-y-6">
      {state.suggestedTitle && (
        <TitleConfirmation ... />
      )}
      <ValidationReview ... />
    </div>
  );
}
```

- **VALIDATE**: `cd client && ~/.bun/bin/bun run lint && ~/.bun/bin/bun run build`

### Task 10: Add unit test for Editor agent

- **IMPLEMENT**: Add test for `EditorAgent.edit_session()`
- **LOCATION**: Create `server/tests/unit/test_editor_agent.py`
- **PATTERN**: Follow test patterns in test_agents.py

```python
"""Tests for the Editor agent."""

import pytest
from unittest.mock import AsyncMock, MagicMock, patch

from app.agents.editor import EditorAgent, EditorResponse
from app.agents.state import (
    ResearchedSession,
    SessionOutlineItem,
    SessionType,
    ValidationIssue,
    ValidationIssueType,
    InterviewContext,
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
async def test_editor_preserves_videos(mock_client, sample_session, sample_outline_item, sample_interview_context):
    """Test that Editor preserves videos during editing."""
    # Add videos to session
    sample_session.videos = [{"url": "https://youtube.com/watch?v=123", "title": "Python Tutorial"}]

    editor = EditorAgent(mock_client)

    # Mock generate_structured to return edited content
    editor.generate_structured = AsyncMock(return_value=EditorResponse(
        edited_content="# Edited Introduction\n\nImproved content here.",
        needs_research=False,
        research_request=None,
    ))

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
async def test_editor_triggers_research_for_critical_gap(mock_client, sample_session, sample_outline_item, sample_interview_context):
    """Test that Editor triggers research for critical gaps."""
    editor = EditorAgent(mock_client)

    # First call: Editor decides research is needed
    # Second call: Research section generation
    editor.generate_structured = AsyncMock(side_effect=[
        EditorResponse(
            edited_content="# Content with gap marker\n\n[GAP HERE]",
            needs_research=True,
            research_request="Explain list comprehensions in Python",
        ),
        MagicMock(
            section_content="List comprehensions are a concise way to create lists...",
            suggested_heading="List Comprehensions",
        ),
    ])

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
```

- **VALIDATE**: `cd server && ./venv/bin/pytest tests/unit/test_editor_agent.py -v`

---

## TESTING STRATEGY

### Unit Tests

1. **Test Editor preserves videos** — Videos unchanged after editing
2. **Test Editor triggers research for critical gaps** — needs_research=true triggers mini-research
3. **Test Editor handles multiple issues** — All issues for a session processed
4. **Test research merge** — Researched section properly appended
5. **Test Editor fallback on research failure** — Graceful degradation if research fails

### Integration Tests

1. **Test full pipeline with auto-edit** — Mock Gemini, verify edit loop works
2. **Test pipeline when validation passes first time** — No edit attempts
3. **Test max edit attempts respected** — Stops after 2 attempts, saves anyway

### Edge Cases

- Issue with no affected_session_ids (skip gracefully)
- All sessions affected (edit all)
- Editor throws exception (propagate error)
- Research throws exception (continue without research)

---

## VALIDATION COMMANDS

### Level 1: Syntax & Style

```bash
cd server && ./venv/bin/ruff check app/
cd server && ./venv/bin/ruff format app/ --check
cd client && ~/.bun/bin/bun run lint
```

### Level 2: Unit Tests

```bash
cd server && ./venv/bin/pytest tests/unit/ -v
cd server && ./venv/bin/pytest tests/unit/test_editor_agent.py -v
```

### Level 3: Integration Tests

```bash
cd server && ./venv/bin/pytest tests/integration/ -v
cd server && ./venv/bin/pytest -v
```

### Level 4: Type Checking

```bash
cd client && ~/.bun/bin/bun run build
```

### Level 5: Manual Validation

1. Start backend: `cd server && ./venv/bin/uvicorn app.main:app --reload --port 8000`
2. Start frontend: `cd client && ~/.bun/bin/bun run dev`
3. Create a new roadmap
4. Verify:
   - Progress shows "Validating..." after research
   - If issues found, progress shows "Improving content quality..."
   - No validation review screen appears
   - Roadmap is created
5. Check server logs for:
   - "Starting edit attempt" messages (if issues)
   - "Validation passed" or "Validation still has issues..."
   - Editor research requests (if any gaps)

---

## ACCEPTANCE CRITERIA

- [ ] Editor Agent created with surgical editing capability
- [ ] Editor dynamically decides when to trigger research for gaps
- [ ] Validation runs automatically after research phase
- [ ] Auto-edit loop runs up to 2 times maximum
- [ ] Roadmap saved even if issues remain after max attempts
- [ ] YouTube videos preserved during editing
- [ ] No `user_review` stage shown to users
- [ ] All existing tests pass
- [ ] Frontend builds without errors
- [ ] Backend passes linting

---

## COMPLETION CHECKLIST

- [ ] All tasks completed in order
- [ ] Each task validation passed
- [ ] All validation commands successful
- [ ] Full test suite passes
- [ ] No linting/type errors
- [ ] Manual testing confirms feature works
- [ ] Acceptance criteria met

---

## NOTES

### Design Decisions

1. **Editor vs Re-researcher**: Editor performs surgical edits, preserving good content. Only calls researcher for critical gaps that need new content.

2. **Dynamic research decision**: Editor autonomously decides if a gap is critical enough to warrant research. This balances quality with cost.

3. **Full content output**: Editor returns complete edited content rather than patches. Simpler, more reliable, minimal token cost difference.

4. **Research merge strategy**: Currently appends new sections at end. Future improvement: AI-guided insertion point.

5. **Model selection**: Editor uses FLASH (balanced), research uses FLASH_LITE (fast, cheap).

### Future Improvements

- Smarter research merge with AI-guided insertion points
- Editor could suggest session reordering for ORDERING issues
- Track edit success rate to tune prompts
- User-facing quality badge ("Refined for quality")
