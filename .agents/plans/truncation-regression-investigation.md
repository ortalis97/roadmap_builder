# Truncation & Regression Investigation

## Summary

This document analyzes uncommitted changes on the current branch that are suspected of causing:
- Session formatting regression
- Truncated sessions (incomplete content)
- YouTube API quota exhaustion

**Status**: Investigation complete. Changes documented for future reference.

## Current State

### 4 Commits Ahead of origin/main (Already Committed)

| Commit | Description | Impact |
|--------|-------------|--------|
| `418bcc1` | Centralize LLM model config | ✅ Good - base.py uses per-agent models |
| `00fbfd8` | Truncation detection + UNLIMITED_TOKENS switch | ✅ Good - default False |
| `111a4fa` | Docs reorganization | ✅ Docs only |
| `2a5a03c` | Add implementation plans | ✅ Docs only |

### Uncommitted Changes (On Top of Above)

| File | Change Type | Likely Impact |
|------|------------|---------------|
| `base.py` | More truncation logging (mid-sentence, short response) | ✅ Safe - observability |
| `orchestrator.py` | Sequential researcher execution | ⚠️ Experiment - may help or hurt |
| `prompts.py` | Word count + CRITICAL instructions + YouTube prompts | ⚠️ Mixed - YouTube good, rest suspicious |
| `model_config.py` | `UNLIMITED_TOKENS = False → True` | ⚠️ Debug mode - should revert |

### Detailed Analysis

**1. `server/app/agents/base.py` (KEEP)**
- Adds response_len to all log messages
- Logs unexpected finish_reasons (SAFETY, RECITATION, etc.)
- Detects mid-sentence truncation for researcher agents
- Warns on suspiciously short responses (<500 chars)
- **Verdict**: Pure diagnostic code. Does NOT change behavior.

**2. `server/app/agents/orchestrator.py` (QUESTIONABLE)**
- Changed from `asyncio.gather` (parallel) to sequential execution
- Original parallel code passed `[]` (empty list) to ALL tasks - no context sharing
- Sequential now correctly passes previous sessions for context
- Comment: "Parallel execution (13+ concurrent requests) causes incomplete responses"
- **Verdict**: Was an attempt to fix truncation. May be helping or causing slower pipeline.

**3. `server/app/agents/prompts.py` (SPLIT)**

**KEEP - YouTube prompts** (lines 218-280):
```python
YOUTUBE_QUERY_GENERATION_PROMPT = ...
YOUTUBE_RERANK_PROMPT = ...
```
These are needed for the improved YouTube API-based video search.

**REVERT - Researcher prompt additions** (lines 70-76):
```
- Target length: 1,500-2,500 words (enough depth without overwhelming)

CRITICAL: You MUST generate COMPLETE content...
```
- Word count targets may confuse the model
- CRITICAL instructions may conflict with JSON schema
- **Likely causing formatting regression**

**4. `server/app/model_config.py` (REVERT)**
- Changed `UNLIMITED_TOKENS = False` → `True`
- Removes all max_output_tokens limits globally
- Was intended for debugging but left enabled
- **Verdict**: Debug switch should be off for normal operation

## YouTube API Quota Issue (Separate Problem)

The quota issue is from **already committed** code (commit `8ed5dac`), not uncommitted changes.

**Root cause**: Each session triggers many API calls:
- 3-5 search queries per session (Gemini-generated)
- Each query fetches 5 videos → multiple `search` API calls
- Then `videos` API call for metadata on all unique IDs
- All sessions run in parallel → burst of API requests

**Quota math for 10 sessions**:
- 10 sessions × 4 queries avg × 1 search call = 40 search calls
- 10 sessions × ~15 unique videos × 1 details call = ~10 details calls
- **~50+ quota units per roadmap creation**

YouTube API free tier: 10,000 units/day. Search costs 100 units each!
- 40 searches × 100 units = 4,000 units per roadmap
- Only ~2-3 roadmaps before quota exhausted

## Revert Instructions (If Needed)

If you decide to revert the problematic changes, here's what to do:

### Summary of Recommended Actions

| File | Action |
|------|--------|
| `base.py` | **KEEP** - logging improvements (no behavior change) |
| `orchestrator.py` | **REVERT** - return to parallel execution |
| `prompts.py` | **KEEP YouTube prompts**, **REVERT** researcher additions |
| `model_config.py` | **REVERT** - `UNLIMITED_TOKENS = False` |

### Step-by-Step Revert Instructions

#### 1. Revert UNLIMITED_TOKENS to False

File: `server/app/model_config.py` line 12

```python
# Change from:
UNLIMITED_TOKENS = True

# To:
UNLIMITED_TOKENS = False
```

#### 2. Remove researcher prompt additions from prompts.py

File: `server/app/agents/prompts.py`

Delete these lines from RESEARCHER_BASE_PROMPT (around lines 70-76):
```
- Target length: 1,500-2,500 words (enough depth without overwhelming)

CRITICAL: You MUST generate COMPLETE content. Do not stop mid-sentence or mid-section.
- Every section you start must be finished
- Every list must have all its items
- Every sentence must be complete
- End your content with a proper conclusion paragraph
```

**Keep** YOUTUBE_QUERY_GENERATION_PROMPT and YOUTUBE_RERANK_PROMPT at the end of the file.

#### 3. Revert orchestrator.py to parallel execution

File: `server/app/agents/orchestrator.py`

Replace the sequential execution code (around lines 325-340):
```python
# Current (sequential):
for outline_item in outline.sessions:
    result = await research_session(outline_item, researched_sessions)
    if isinstance(result, Exception):
        self.logger.error("Research failed", error=str(result))
        raise result
    session, span = result
    researched_sessions.append(session)
    spans.append(span)
```

With the original parallel execution:
```python
# Original (parallel):
tasks = [research_session(outline_item, []) for outline_item in outline.sessions]
results = await asyncio.gather(*tasks, return_exceptions=True)

for result in results:
    if isinstance(result, Exception):
        self.logger.error("Research failed", error=str(result))
        raise result
    session, span = result
    researched_sessions.append(session)
    spans.append(span)

# Sort by order
researched_sessions.sort(key=lambda s: s.order)
```

#### 4. Keep base.py logging improvements

No action needed - these are pure observability enhancements.

### Post-Revert Testing

After applying reverts:
1. Create a test roadmap
2. Check if sessions are complete and properly formatted
3. If truncation persists, investigate other causes (see learnings doc)

## YouTube API Quota Optimization Options

The YouTube quota issue is NOT from uncommitted changes (it's in commit `8ed5dac`). Options to reduce API usage:

1. **Reduce queries per session**: 2 instead of 3-5
2. **Reduce results per query**: 3 instead of 5
3. **Skip video details API**: Use search snippet data only
4. **Cache by topic**: Same topic = same videos
5. **Lazy loading**: Fetch videos when session is opened, not at creation
6. **Fallback-first**: Use Gemini+oEmbed verification (no quota cost) as primary

## Files Reference

| File | Current State | Recommendation |
|------|---------------|----------------|
| `server/app/agents/base.py` | Enhanced logging | KEEP - pure observability |
| `server/app/agents/orchestrator.py` | Sequential execution | Consider reverting to parallel |
| `server/app/agents/prompts.py` | Word count + CRITICAL + YouTube prompts | Keep YouTube, revert researcher additions |
| `server/app/model_config.py` | `UNLIMITED_TOKENS = True` | Revert to False |

## Verification Checklist

After changes:
1. Create a test roadmap with ~8-10 sessions
2. Verify sessions are complete (not truncated)
3. Verify formatting is correct (proper markdown sections)
4. Check logs for truncation warnings
5. Confirm YouTube videos still work

## Learnings to Document

Create `.claude/reference/truncation-investigation.md` with the following content:

---

# Gemini API Truncation Investigation

## Overview

This document captures learnings from investigating session content truncation issues in the roadmap generation pipeline.

## Problem Statement

Sessions in generated roadmaps were appearing truncated (incomplete content, mid-sentence endings) and with formatting issues.

## What Was Tried

### 1. UNLIMITED_TOKENS Global Switch
- **Change**: Set `UNLIMITED_TOKENS = True` in `model_config.py`
- **Hypothesis**: Token limits were causing premature truncation
- **Result**: Did not fix truncation; may have contributed to formatting issues
- **Learning**: Truncation may not be caused by max_output_tokens limits

### 2. Sequential Researcher Execution
- **Change**: Switched from `asyncio.gather` (parallel) to sequential execution in `orchestrator.py`
- **Hypothesis**: 13+ concurrent Gemini API requests were causing incomplete responses
- **Result**: Inconclusive - truncation still observed
- **Learning**: Keep as an option if parallel proves problematic in the future

### 3. Prompt Engineering - Word Count Targets
- **Change**: Added "Target length: 1,500-2,500 words" to researcher prompts
- **Hypothesis**: Explicit length guidance would produce complete content
- **Result**: **Likely caused formatting regression** - model may prioritize hitting word count over content quality
- **Learning**: Avoid word count targets in prompts; let the model determine appropriate length

### 4. Prompt Engineering - CRITICAL Instructions
- **Change**: Added "CRITICAL: You MUST generate COMPLETE content..." instructions
- **Hypothesis**: Emphatic instructions would prevent truncation
- **Result**: May have conflicted with JSON schema constraints
- **Learning**: CRITICAL/emphatic language in prompts can be counterproductive

## What Actually Worked

- Enhanced logging in `base.py` helps diagnose issues (finish_reason, response_length)
- Centralized model config (`model_config.py`) makes debugging easier

## Recommendations

1. **Avoid prompt hacks** - Don't add word counts or emphatic instructions
2. **Use structured output** - JSON schema constraints are more reliable than prompt instructions
3. **Monitor finish_reason** - MAX_TOKENS indicates actual truncation
4. **Consider sequential execution** - Can be re-enabled if parallel causes issues
5. **Test with realistic roadmaps** - 8-10 sessions to catch truncation issues

## YouTube API Quota Analysis

### Quota Consumption Pattern
- Search API: **100 units per call**
- Videos API (details): 1 unit per video
- Daily free tier: 10,000 units

### Current Implementation (from commit 8ed5dac)
For a 10-session roadmap:
- 10 sessions × 4 queries avg = 40 search calls
- 40 searches × 100 units = **4,000 units per roadmap**
- Only ~2-3 roadmaps per day before quota exhausted

### Optimization Options
1. **Reduce queries per session**: 2 instead of 3-5
2. **Reduce results per query**: 3 instead of 5
3. **Skip video details API**: Use search snippet data only
4. **Cache by topic**: Same topic = same videos
5. **Lazy loading**: Fetch videos when session is opened, not at creation
6. **Fallback-first**: Use Gemini+oEmbed verification (no quota cost) as primary

---
