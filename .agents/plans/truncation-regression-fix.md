# Feature: Truncation Regression Fix

The following plan should be complete, but validate documentation and codebase patterns before implementing.

Pay special attention to naming of existing utils, types, and models. Import from the right files.

## Feature Description

Selectively keep, modify, or revert changes made since origin/main to fix truncation and formatting regressions while preserving valuable improvements. Key changes include reverting to parallel researcher execution with session context, removing problematic prompt additions, and optimizing YouTube API quota usage.

## User Story

As a learner using the roadmap builder
I want roadmaps with complete, well-formatted sessions that don't overlap
So that I can follow a coherent learning path without missing or duplicated content

## Problem Statement

Recent uncommitted changes introduced:
1. Sequential researcher execution (slower, was attempt to fix truncation)
2. Word count targets and "CRITICAL" instructions in prompts (causing formatting regression)
3. UNLIMITED_TOKENS=True debug flag left enabled
4. YouTube API consuming excessive quota (~4000 units/roadmap)

## Solution Statement

1. Revert to parallel researcher execution but pass full session context
2. Remove problematic prompt additions, add overlap avoidance instruction
3. Reset UNLIMITED_TOKENS=False (already done)
4. Optimize YouTube: 2 queries instead of 3-5, skip video details API call

## Feature Metadata

**Feature Type**: Bug Fix / Refactor
**Estimated Complexity**: Medium
**Primary Systems Affected**: Orchestrator, Researcher, YouTube Agent, Prompts
**Dependencies**: None (internal refactoring)

---

## CONTEXT REFERENCES

### Relevant Codebase Files - READ BEFORE IMPLEMENTING

- `server/app/agents/orchestrator.py` (lines 300-340) - Research phase with sequential loop to revert
- `server/app/agents/researcher.py` (lines 43-81) - research_session method and context building
- `server/app/agents/prompts.py` (lines 67-76) - Researcher prompt additions to remove
- `server/app/agents/prompts.py` (lines 220-280) - YouTube prompts (query count to reduce)
- `server/app/agents/youtube.py` (lines 160-275) - Query generation and video fetching to optimize
- `server/app/agents/state.py` (lines 70-88) - SessionOutlineItem structure for context
- `server/app/model_config.py` - Already updated, verify UNLIMITED_TOKENS=False

### Files to Modify

| File | Action |
|------|--------|
| `server/app/model_config.py` | **DONE** - already edited |
| `server/app/agents/orchestrator.py` | Revert to parallel + pass outline context |
| `server/app/agents/researcher.py` | Accept outline context, update prompt building |
| `server/app/agents/prompts.py` | Remove word count/CRITICAL, reduce YouTube queries |
| `server/app/agents/youtube.py` | Reduce query limit, skip video details call |

### Patterns to Follow

**Error Handling (orchestrator.py:325-334):**
```python
for result in results:
    if isinstance(result, Exception):
        self.logger.error("Research failed", error=str(result))
        raise result
```

**Context Building (researcher.py:51-58):**
```python
prev_context = (
    "\n".join([f"- {s.title}: {', '.join(s.key_concepts[:3])}" for s in previous_sessions[-3:]])
    if previous_sessions
    else "None yet"
)
```

**VideoResource Construction (youtube.py:301-309):**
```python
VideoResource(
    url=c["url"],
    title=c["title"],
    channel=c["channel"],
    thumbnail_url=c["thumbnail_url"],
    duration_minutes=c["duration_minutes"],  # Can be None
    description=c["description"],
)
```

---

## IMPLEMENTATION PLAN

### Phase 1: Prompts Cleanup

Remove problematic researcher prompt additions and reduce YouTube query count.

### Phase 2: Researcher Context Enhancement

Update researcher to accept and use full session outline for overlap avoidance.

### Phase 3: Orchestrator Parallel Restoration

Revert to parallel execution while passing session context.

### Phase 4: YouTube Optimization

Reduce queries and skip expensive video details API call.

---

## STEP-BY-STEP TASKS

### Task 1: UPDATE `server/app/agents/prompts.py` - Remove Researcher Additions

**IMPLEMENT**: Remove lines 70-76 from RESEARCHER_BASE_PROMPT

**CURRENT CODE (lines 67-76):**
```python
- Be appropriate for self-directed learning
- Target length: 1,500-2,500 words (enough depth without overwhelming)

CRITICAL: You MUST generate COMPLETE content. Do not stop mid-sentence or mid-section.
- Every section you start must be finished
- Every list must have all its items
- Every sentence must be complete
- End your content with a proper conclusion paragraph

Output valid JSON matching the schema provided. No markdown code blocks."""
```

**NEW CODE:**
```python
- Be appropriate for self-directed learning

Output valid JSON matching the schema provided. No markdown code blocks."""
```

**VALIDATE**: `cd server && ./venv/bin/ruff check app/agents/prompts.py`

---

### Task 2: UPDATE `server/app/agents/prompts.py` - Reduce YouTube Query Count

**IMPLEMENT**: Change "3-5" to "2" in YOUTUBE_QUERY_GENERATION_PROMPT (line 223)

**CURRENT CODE (line 223):**
```python
Given a learning session's context, generate 3-5 diverse search queries that will \
```

**NEW CODE:**
```python
Given a learning session's context, generate 2 diverse search queries that will \
```

**VALIDATE**: `cd server && ./venv/bin/ruff check app/agents/prompts.py`

---

### Task 3: UPDATE `server/app/agents/researcher.py` - Change Parameter Type

**IMPLEMENT**: Change `previous_sessions` parameter to accept outline items instead

**CURRENT SIGNATURE (lines 43-49):**
```python
async def research_session(
    self,
    outline_item: SessionOutlineItem,
    interview_context: InterviewContext,
    previous_sessions: list[ResearchedSession],
    language: str = "en",
) -> ResearchedSession:
```

**NEW SIGNATURE:**
```python
async def research_session(
    self,
    outline_item: SessionOutlineItem,
    interview_context: InterviewContext,
    all_session_outlines: list[SessionOutlineItem],
    language: str = "en",
) -> ResearchedSession:
```

**IMPORTS**: Add `SessionOutlineItem` to imports if not already there (check line ~10)

**VALIDATE**: `cd server && ./venv/bin/ruff check app/agents/researcher.py`

---

### Task 4: UPDATE `server/app/agents/researcher.py` - Update Context Building

**IMPLEMENT**: Replace previous session context with full roadmap context (lines 51-58)

**CURRENT CODE (lines 51-58):**
```python
# Build context from previous sessions
prev_context = (
    "\n".join(
        [f"- {s.title}: {', '.join(s.key_concepts[:3])}" for s in previous_sessions[-3:]]
    )
    if previous_sessions
    else "None yet"
)
```

**NEW CODE:**
```python
# Build context showing all sessions in roadmap for overlap avoidance
other_sessions = [s for s in all_session_outlines if s.order != outline_item.order]
session_context = (
    "\n".join(
        [f"- Session {s.order}: {s.title} ({s.session_type.value})" for s in other_sessions]
    )
    if other_sessions
    else "This is the only session"
)
```

**VALIDATE**: `cd server && ./venv/bin/ruff check app/agents/researcher.py`

---

### Task 5: UPDATE `server/app/agents/researcher.py` - Update Prompt Template

**IMPLEMENT**: Update the prompt template to use new context and add overlap instruction (lines 61-81)

**FIND** the section with `Previous sessions covered:` (around line 70)

**REPLACE WITH:**
```python
Other sessions in this roadmap:
{session_context}

IMPORTANT: Focus on YOUR session's specific content. Avoid duplicating material
that belongs in other sessions - reference them instead if needed.
```

**VALIDATE**: `cd server && ./venv/bin/ruff check app/agents/researcher.py`

---

### Task 6: UPDATE `server/app/agents/orchestrator.py` - Update Inner Function Signature

**IMPLEMENT**: Change the research_session inner function signature (lines 300-303)

**CURRENT CODE:**
```python
async def research_session(
    outline_item: Any,
    previous: list[ResearchedSession],
) -> tuple[ResearchedSession, AgentSpan]:
```

**NEW CODE:**
```python
async def research_session(
    outline_item: Any,
    all_outlines: list[Any],
) -> tuple[ResearchedSession, AgentSpan]:
```

**VALIDATE**: `cd server && ./venv/bin/ruff check app/agents/orchestrator.py`

---

### Task 7: UPDATE `server/app/agents/orchestrator.py` - Update Researcher Call

**IMPLEMENT**: Update the call to researcher.research_session (around line 310)

**FIND** the line calling `researcher.research_session` with `previous_sessions=previous`

**REPLACE** `previous_sessions=previous` with `all_session_outlines=all_outlines`

**VALIDATE**: `cd server && ./venv/bin/ruff check app/agents/orchestrator.py`

---

### Task 8: UPDATE `server/app/agents/orchestrator.py` - Revert to Parallel Execution

**IMPLEMENT**: Replace sequential loop with parallel asyncio.gather (lines 325-334)

**CURRENT CODE (sequential):**
```python
# Run researchers SEQUENTIALLY to avoid Gemini API truncation issues
# Parallel execution (13+ concurrent requests) causes incomplete responses
for outline_item in outline.sessions:
    result = await research_session(outline_item, researched_sessions)
    if isinstance(result, Exception):
        self.logger.error("Research failed", error=str(result))
        raise result
    session, span = result
    researched_sessions.append(session)
    spans.append(span)
```

**NEW CODE (parallel with context):**
```python
# Run all researchers in parallel with full outline context
tasks = [research_session(outline_item, outline.sessions) for outline_item in outline.sessions]
results = await asyncio.gather(*tasks, return_exceptions=True)

for result in results:
    if isinstance(result, Exception):
        self.logger.error("Research failed", error=str(result))
        raise result
    session, span = result
    researched_sessions.append(session)
    spans.append(span)

# Sort by order (parallel doesn't guarantee order)
researched_sessions.sort(key=lambda s: s.order)
```

**VALIDATE**: `cd server && ./venv/bin/ruff check app/agents/orchestrator.py`

---

### Task 9: UPDATE `server/app/agents/youtube.py` - Reduce Query Limit

**IMPLEMENT**: Change query limit from 5 to 2 (around line 188)

**CURRENT CODE (line 188):**
```python
return response.queries[:5]
```

**NEW CODE:**
```python
return response.queries[:2]
```

**ALSO UPDATE** the prompt text in `_generate_search_queries` (around line 176):

**CURRENT:**
```python
Generate 3-5 diverse search queries to find the best tutorial videos."""
```

**NEW:**
```python
Generate 2 diverse search queries to find the best tutorial videos."""
```

**VALIDATE**: `cd server && ./venv/bin/ruff check app/agents/youtube.py`

---

### Task 10: UPDATE `server/app/agents/youtube.py` - Skip Video Details API

**IMPLEMENT**: Remove get_video_details call and use search snippet data directly (lines 242-274)

**FIND** the section in `_fetch_candidate_videos` that calls `get_video_details` (around line 245)

**REPLACE** the entire details fetching and combining section with:

```python
# Build candidates directly from search results (skip video details API to save quota)
candidates = []
for raw in raw_candidates:
    video_id = raw["video_id"]
    snippet = raw["snippet"]

    candidates.append({
        "video_id": video_id,
        "url": f"https://www.youtube.com/watch?v={video_id}",
        "title": snippet.get("title", ""),
        "channel": snippet.get("channelTitle", ""),
        "description": snippet.get("description", "")[:300],
        "thumbnail_url": snippet.get("thumbnails", {}).get("high", {}).get("url", ""),
        "view_count": 0,  # Not available from search, skip details API
        "published_at": snippet.get("publishedAt", ""),
        "duration_minutes": None,  # Not available from search, skip details API
    })

return candidates
```

**REMOVE**: The entire `get_video_details` call section and the details dict merging

**VALIDATE**: `cd server && ./venv/bin/ruff check app/agents/youtube.py`

---

### Task 11: UPDATE `server/app/agents/youtube.py` - Update Rerank Prompt

**IMPLEMENT**: Update the rerank candidates_text formatting since view_count is now 0

**FIND** the candidates_text formatting in `_rerank_videos` (around line 320)

**CURRENT:**
```python
candidates_text = "\n".join([
    f"[{i}] \"{c['title']}\" by {c['channel']} "
    f"({c['view_count']:,} views, {c['duration_minutes'] or '?'} min)\n"
    f"    Description: {c['description'][:150]}..."
    for i, c in enumerate(candidates)
])
```

**NEW:**
```python
candidates_text = "\n".join([
    f"[{i}] \"{c['title']}\" by {c['channel']}\n"
    f"    Description: {c['description'][:150]}..."
    for i, c in enumerate(candidates)
])
```

**VALIDATE**: `cd server && ./venv/bin/ruff check app/agents/youtube.py`

---

## TESTING STRATEGY

### Unit Tests

Existing tests in `server/tests/unit/` should still pass. Key tests:
- `test_agents.py` - Agent behavior tests
- `test_model_config.py` - Model configuration tests

### Integration Tests

Create a test roadmap to verify:
1. Parallel execution works without truncation
2. Sessions don't overlap in content
3. YouTube videos are found with reduced queries

### Edge Cases

- Roadmap with 1 session (no other sessions for context)
- Roadmap with 10+ sessions (parallel stress test)
- Session with no YouTube results (fallback handling)

---

## VALIDATION COMMANDS

### Level 1: Syntax & Style

```bash
cd server && ./venv/bin/ruff check app/
cd server && ./venv/bin/ruff format app/ --check
```

### Level 2: Unit Tests

```bash
cd server && ./venv/bin/pytest tests/unit/ -v
```

### Level 3: Type Checking (if available)

```bash
cd server && ./venv/bin/python -m py_compile app/agents/orchestrator.py app/agents/researcher.py app/agents/youtube.py app/agents/prompts.py
```

### Level 4: Manual Validation

1. Start the server: `cd server && ./venv/bin/uvicorn app.main:app --reload --port 8000`
2. Create a test roadmap with 8-10 sessions
3. Verify:
   - All sessions complete (not truncated)
   - Proper markdown formatting
   - No overlapping content between sessions
   - YouTube videos found for each session
   - Check server logs for truncation warnings

---

## ACCEPTANCE CRITERIA

- [ ] Parallel researcher execution restored with asyncio.gather
- [ ] Session context passed to each researcher (full outline)
- [ ] Overlap avoidance instruction added to researcher prompt
- [ ] Word count and CRITICAL instructions removed from prompts
- [ ] YouTube queries reduced from 3-5 to 2 per session
- [ ] Video details API call removed (using search snippets only)
- [ ] All linting passes with zero errors
- [ ] All unit tests pass
- [ ] Manual test shows complete, well-formatted sessions
- [ ] No truncation warnings in logs during roadmap creation

---

## COMPLETION CHECKLIST

- [ ] All 11 tasks completed in order
- [ ] Each task validation passed
- [ ] `ruff check` passes on all modified files
- [ ] `pytest` passes all tests
- [ ] Manual roadmap creation test successful
- [ ] Sessions are complete and properly formatted
- [ ] No content overlap between sessions

---

## NOTES

**Quota Impact:**
- Before: ~4,000 units/roadmap (~2-3 roadmaps/day)
- After: ~2,000 units/roadmap (~5 roadmaps/day)
- Savings: 2 queries instead of 4 avg (50%), skip video details API

**Risk Considerations:**
- Parallel execution with 10+ concurrent Gemini requests - monitor for rate limiting
- Removing view_count from reranking - quality may be slightly affected but saves quota
- Session context changes - test thoroughly for prompt compatibility

**Already Completed:**
- `model_config.py` updated: UNLIMITED_TOKENS=False, all agents use gemini-2.0-flash
