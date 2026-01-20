# Feature: Hebrew Language and RTL Support

The following plan should be complete, but it's important that you validate documentation and codebase patterns and task sanity before you start implementing.

Pay special attention to naming of existing utils, types, and models. Import from the right files etc.

## Feature Description

Enable users to create roadmaps in Hebrew by automatically detecting Hebrew input and generating all content (interview questions, roadmap, sessions, chat) in Hebrew. The UI dynamically switches to RTL (right-to-left) layout for content areas when viewing Hebrew roadmaps, while keeping the app shell (navigation, layout) in LTR for consistency.

This is **language-aware content generation**, not UI translation. The AI agents detect the input language and respond accordingly.

## User Story

As a Hebrew-speaking learner,
I want to write my learning topic in Hebrew and have the entire roadmap generated in Hebrew,
So that I can learn in my native language with proper RTL text display.

## Problem Statement

Currently, the app only generates content in English regardless of input language. Hebrew-speaking users cannot create roadmaps in their native language, and there's no RTL support for displaying Hebrew text properly.

## Solution Statement

1. **Language Detection**: Detect Hebrew characters in the topic input using Unicode range detection
2. **Language Storage**: Store detected language per-roadmap in the database
3. **AI Language Adaptation**: Modify agent prompts to generate content in the detected language (with technical terms in English)
4. **RTL Content Display**: Apply RTL direction to content areas (not layout) for Hebrew roadmaps
5. **Auto-detect Text Inputs**: Notes editor and chat input auto-detect direction based on content

## Feature Metadata

**Feature Type**: New Capability
**Estimated Complexity**: Medium
**Primary Systems Affected**: Backend (agents, models), Frontend (pages, components)
**Dependencies**: None (uses existing Tailwind CSS capabilities)

---

## CONTEXT REFERENCES

### Relevant Codebase Files — READ THESE BEFORE IMPLEMENTING!

**Backend - Models:**
- `server/app/models/roadmap.py` (lines 26-46) — Roadmap model, add `language` field here
- `server/app/models/session.py` (lines 18-41) — Session model for reference

**Backend - Agents (modify prompts for language awareness):**
- `server/app/agents/prompts.py` (lines 1-157) — All agent prompts, need language instructions
- `server/app/agents/interviewer.py` (lines 26-83) — Interview question generation, add language param
- `server/app/agents/architect.py` — Architect agent, add language param
- `server/app/agents/researcher.py` — Researcher agents, add language param
- `server/app/agents/orchestrator.py` (lines 45-65, 227-258) — Pipeline initialization and architect call
- `server/app/agents/state.py` — Pipeline state, may need language field

**Backend - Routes:**
- `server/app/routers/roadmaps_create.py` (lines 55-59, 91-146) — StartCreationRequest and start endpoint
- `server/app/routers/chat.py` — Chat endpoint for language-aware responses

**Frontend - Types:**
- `client/src/types/index.ts` (lines 42-56, 49) — Roadmap type, add `language` field

**Frontend - Pages (add RTL support):**
- `client/src/pages/RoadmapDetailPage.tsx` (lines 53-189) — Roadmap view, wrap content in RTL
- `client/src/pages/SessionDetailPage.tsx` (lines 70-155) — Session view, wrap content in RTL
- `client/src/pages/CreateRoadmapPage.tsx` (lines 130-204) — Creation page, example buttons

**Frontend - Components:**
- `client/src/components/MarkdownContent.tsx` (lines 11-67) — Markdown rendering, add RTL prop
- `client/src/components/NotesEditor.tsx` (lines 46-68) — Notes textarea, add auto-detect direction
- `client/src/components/ChatMessage.tsx` (lines 19-41) — Chat bubbles, add auto-detect direction
- `client/src/components/creation/InterviewQuestions.tsx` — Interview UI, RTL for Hebrew questions

**Frontend - Hooks:**
- `client/src/hooks/useRoadmaps.ts` — Roadmap queries, language field flows through
- `client/src/hooks/useRoadmapCreation.ts` (lines 118-141) — Creation hook, language detection

### New Files to Create

- `client/src/utils/language.ts` — Language detection utilities (isHebrew, getTextDirection)
- `server/app/utils/language.py` — Backend language detection utility

### Patterns to Follow

**Backend Naming Conventions:**
- Snake_case for Python variables and functions
- Type hints on all function signatures
- Pydantic models for data validation

**Backend Field Pattern (from roadmap.py):**
```python
language: str = "en"  # "en" or "he"
```

**Frontend Type Pattern (from types/index.ts):**
```typescript
export interface Roadmap {
  // ... existing fields
  language: 'en' | 'he';
}
```

**Tailwind RTL Pattern:**
```tsx
<div dir={language === 'he' ? 'rtl' : 'ltr'}>
  {/* Content here */}
</div>
```

**Auto-detect Direction Pattern:**
```tsx
// For text inputs, use CSS `dir="auto"` for automatic detection
<textarea dir="auto" />
```

---

## IMPLEMENTATION PLAN

### Phase 1: Backend Language Detection & Storage

Add language detection utility and store language per-roadmap.

**Tasks:**
- Create language detection utility
- Add language field to Roadmap model
- Detect language in creation pipeline
- Pass language through pipeline state

### Phase 2: AI Agent Language Adaptation

Modify agent prompts to generate content in the detected language.

**Tasks:**
- Add language-aware prompt instructions
- Update interviewer agent for Hebrew questions
- Update architect agent for Hebrew titles/outlines
- Update researcher agents for Hebrew content
- Update chat endpoint for message-language matching

### Phase 3: Frontend RTL Display

Add RTL support for Hebrew roadmap content.

**Tasks:**
- Create frontend language utilities
- Update TypeScript types
- Add RTL wrapper to content areas
- Update MarkdownContent for RTL
- Add auto-direction to text inputs

### Phase 4: Testing & Validation

Ensure all components work correctly with Hebrew.

**Tasks:**
- Test language detection edge cases
- Verify RTL display in all views
- Test mixed Hebrew/English content
- Verify code blocks stay LTR

---

## STEP-BY-STEP TASKS

### Task 1: CREATE `server/app/utils/language.py`

- **IMPLEMENT**: Language detection utility using Hebrew Unicode range
- **PATTERN**: Simple utility module like other utils
- **IMPORTS**: `import re`
- **CODE**:
```python
"""Language detection utilities."""

import re

# Hebrew Unicode range: \u0590-\u05FF (Hebrew letters and marks)
HEBREW_PATTERN = re.compile(r'[\u0590-\u05FF]')


def detect_language(text: str) -> str:
    """Detect language from text content.

    Returns 'he' if Hebrew characters are found, otherwise 'en'.
    """
    if HEBREW_PATTERN.search(text):
        return "he"
    return "en"


def is_hebrew(text: str) -> bool:
    """Check if text contains Hebrew characters."""
    return bool(HEBREW_PATTERN.search(text))
```
- **VALIDATE**: `cd server && ./venv/bin/python -c "from app.utils.language import detect_language; print(detect_language('שלום')); print(detect_language('hello'))"`

### Task 2: CREATE `server/app/utils/__init__.py`

- **IMPLEMENT**: Export language utilities
- **CODE**:
```python
"""Utility modules."""

from app.utils.language import detect_language, is_hebrew

__all__ = ["detect_language", "is_hebrew"]
```
- **VALIDATE**: `cd server && ./venv/bin/python -c "from app.utils import detect_language; print(detect_language('test'))"`

### Task 3: UPDATE `server/app/models/roadmap.py`

- **IMPLEMENT**: Add `language` field to Roadmap model
- **PATTERN**: Follow existing field patterns (line 33-37)
- **CHANGE**: Add after `summary` field:
```python
language: str = "en"  # "en" for English, "he" for Hebrew
```
- **VALIDATE**: `cd server && ./venv/bin/python -c "from app.models.roadmap import Roadmap; print(Roadmap.model_fields.keys())"`

### Task 4: UPDATE `server/app/agents/state.py`

- **IMPLEMENT**: Add language to PipelineState
- **PATTERN**: Follow existing field patterns in PipelineState
- **CHANGE**: Add `language: str = "en"` field to PipelineState class
- **VALIDATE**: `cd server && ./venv/bin/python -c "from app.agents.state import PipelineState; print('language' in PipelineState.model_fields)"`

### Task 5: UPDATE `server/app/agents/prompts.py`

- **IMPLEMENT**: Add language instruction helper and update prompts
- **CHANGE**: Add at the top of file:
```python
def get_language_instruction(language: str) -> str:
    """Get language instruction for prompts."""
    if language == "he":
        return """
IMPORTANT: Generate all content in Hebrew.
- Write explanations, questions, and content in Hebrew
- Keep technical terms in English (e.g., React, useState, API, Python)
- Use Hebrew punctuation and right-to-left text flow
"""
    return ""
```
- **VALIDATE**: `cd server && ./venv/bin/python -c "from app.agents.prompts import get_language_instruction; print(get_language_instruction('he'))"`

### Task 6: UPDATE `server/app/agents/interviewer.py`

- **IMPLEMENT**: Accept language parameter and include in prompt
- **PATTERN**: Modify `generate_questions` method
- **CHANGE**:
  1. Add `language: str = "en"` parameter to `generate_questions`
  2. Import `get_language_instruction` from prompts
  3. Prepend language instruction to prompt
- **CODE SNIPPET**:
```python
from app.agents.prompts import INTERVIEWER_SYSTEM_PROMPT, get_language_instruction

async def generate_questions(
    self,
    topic: str,
    raw_input: str,
    title: str,
    max_questions: int = 5,
    language: str = "en",
) -> list[InterviewQuestion]:
    language_instruction = get_language_instruction(language)
    prompt = f"""{language_instruction}Generate {max_questions} clarifying questions...
```
- **VALIDATE**: `cd server && ./venv/bin/ruff check app/agents/interviewer.py`

### Task 7: UPDATE `server/app/agents/architect.py`

- **IMPLEMENT**: Accept language parameter and include in prompt
- **PATTERN**: Similar to interviewer changes
- **CHANGE**: Add `language: str = "en"` to `create_outline` method and prepend language instruction
- **VALIDATE**: `cd server && ./venv/bin/ruff check app/agents/architect.py`

### Task 8: UPDATE `server/app/agents/researcher.py`

- **IMPLEMENT**: Accept language parameter and include in prompt
- **PATTERN**: Similar to interviewer changes
- **CHANGE**: Add `language: str = "en"` to `research_session` method and prepend language instruction
- **VALIDATE**: `cd server && ./venv/bin/ruff check app/agents/researcher.py`

### Task 9: UPDATE `server/app/agents/orchestrator.py`

- **IMPLEMENT**: Detect language from topic and pass through pipeline
- **IMPORTS**: Add `from app.utils.language import detect_language`
- **CHANGES**:
  1. In `initialize()`: Detect and store language in state
  2. Pass language to `generate_interview_questions()`
  3. Pass language to `_run_architect()`
  4. Pass language to `_run_researchers_parallel()`
  5. Set language on roadmap in `_save_roadmap()`
- **CODE SNIPPET for initialize()**:
```python
async def initialize(self, topic: str) -> None:
    # Detect language from topic
    detected_language = detect_language(topic)

    self.state = PipelineState(
        pipeline_id=self.pipeline_id,
        user_id=str(self.user_id),
        topic=topic,
        language=detected_language,  # Add this
        stage=PipelineStage.INITIALIZED,
    )
```
- **VALIDATE**: `cd server && ./venv/bin/ruff check app/agents/orchestrator.py`

### Task 10: UPDATE `server/app/routers/chat.py`

- **IMPLEMENT**: Chat should match message language, not roadmap language
- **PATTERN**: Read existing chat endpoint structure
- **CHANGE**: No change needed — the AI naturally responds in the language of the question. The system prompt just needs to not force English.
- **VALIDATE**: `cd server && ./venv/bin/ruff check app/routers/chat.py`

### Task 11: CREATE `client/src/utils/language.ts`

- **IMPLEMENT**: Frontend language detection utilities
- **CODE**:
```typescript
/**
 * Language detection utilities.
 */

// Hebrew Unicode range: \u0590-\u05FF
const HEBREW_REGEX = /[\u0590-\u05FF]/;

/**
 * Check if text contains Hebrew characters.
 */
export function isHebrew(text: string): boolean {
  return HEBREW_REGEX.test(text);
}

/**
 * Get text direction based on content.
 */
export function getTextDirection(text: string): 'rtl' | 'ltr' {
  return isHebrew(text) ? 'rtl' : 'ltr';
}

/**
 * Get direction for a language code.
 */
export function getLanguageDirection(language: string): 'rtl' | 'ltr' {
  return language === 'he' ? 'rtl' : 'ltr';
}

export type Language = 'en' | 'he';
```
- **VALIDATE**: `cd client && ~/.bun/bin/bun run lint`

### Task 12: UPDATE `client/src/types/index.ts`

- **IMPLEMENT**: Add language field to Roadmap types
- **PATTERN**: Follow existing type patterns
- **CHANGES**:
  1. Add `Language` type
  2. Add `language` to `Roadmap` interface
  3. Add `language` to `RoadmapListItem` interface
- **CODE SNIPPET**:
```typescript
export type Language = 'en' | 'he';

export interface RoadmapListItem {
  id: string;
  title: string;
  session_count: number;
  language: Language;  // Add this
  created_at: string;
}

export interface Roadmap {
  id: string;
  title: string;
  summary: string | null;
  sessions: SessionSummary[];
  language: Language;  // Add this
  created_at: string;
  updated_at: string;
}
```
- **VALIDATE**: `cd client && ~/.bun/bin/bun run lint`

### Task 13: UPDATE `client/src/components/MarkdownContent.tsx`

- **IMPLEMENT**: Add RTL support prop
- **PATTERN**: Existing component prop patterns
- **CHANGES**:
  1. Add `direction?: 'ltr' | 'rtl'` prop
  2. Apply `dir` attribute to container
  3. Keep code blocks LTR
- **CODE SNIPPET**:
```typescript
interface MarkdownContentProps {
  content: string;
  className?: string;
  direction?: 'ltr' | 'rtl';
}

export function MarkdownContent({ content, className = '', direction = 'ltr' }: MarkdownContentProps) {
  return (
    <div
      dir={direction}
      className={`prose prose-sm max-w-none ... ${className}`}
    >
      <ReactMarkdown
        // ... existing config
        components={{
          code({ className, children, ...props }) {
            // ... existing code block handling
            // Fenced code block - force LTR
            if (match || codeString.includes('\n')) {
              return (
                <div dir="ltr">
                  <CodeBlock language={match?.[1]}>
                    {codeString}
                  </CodeBlock>
                </div>
              );
            }
            // ... rest
          },
          // ... other components
        }}
      >
        {content}
      </ReactMarkdown>
    </div>
  );
}
```
- **VALIDATE**: `cd client && ~/.bun/bin/bun run lint`

### Task 14: UPDATE `client/src/components/NotesEditor.tsx`

- **IMPLEMENT**: Add `dir="auto"` for auto-detection
- **PATTERN**: HTML5 dir attribute
- **CHANGE**: Add `dir="auto"` to textarea element
- **CODE SNIPPET**:
```typescript
<textarea
  dir="auto"
  value={notes}
  onChange={handleChange}
  // ... rest
/>
```
- **VALIDATE**: `cd client && ~/.bun/bin/bun run lint`

### Task 15: UPDATE `client/src/components/ChatMessage.tsx`

- **IMPLEMENT**: Add `dir="auto"` for auto-detection on message content
- **CHANGE**: Add `dir="auto"` to the content div
- **CODE SNIPPET**:
```typescript
<div className="text-sm whitespace-pre-wrap break-words" dir="auto">
  {message.content}
</div>
```
- **VALIDATE**: `cd client && ~/.bun/bin/bun run lint`

### Task 16: UPDATE `client/src/pages/RoadmapDetailPage.tsx`

- **IMPLEMENT**: Apply RTL to content areas for Hebrew roadmaps
- **IMPORTS**: Add `import { getLanguageDirection } from '../utils/language';`
- **CHANGES**:
  1. Get direction from roadmap.language
  2. Apply `dir` to title and summary
  3. Apply `dir` to session titles in list
- **CODE SNIPPET**:
```typescript
const direction = roadmap ? getLanguageDirection(roadmap.language) : 'ltr';

// In JSX, wrap title:
<h1 className="text-2xl font-bold text-gray-900" dir={direction}>
  {roadmap.title}
</h1>

// Summary:
{roadmap.summary && (
  <p className="mt-4 text-gray-600" dir={direction}>{roadmap.summary}</p>
)}

// Session title in list:
<span className="font-medium hover:text-blue-600" dir={direction}>
  {session.title}
</span>
```
- **VALIDATE**: `cd client && ~/.bun/bin/bun run lint`

### Task 17: UPDATE `client/src/pages/SessionDetailPage.tsx`

- **IMPLEMENT**: Apply RTL to session content for Hebrew roadmaps
- **IMPORTS**: Add `import { getLanguageDirection } from '../utils/language';`
- **CHANGES**:
  1. Fetch roadmap to get language (or pass via context/state)
  2. Apply direction to title and MarkdownContent
- **NOTE**: Need to get roadmap language — either fetch roadmap or add language to session API response
- **APPROACH**: Add useRoadmap hook to get language
- **CODE SNIPPET**:
```typescript
import { useRoadmap } from '../hooks/useRoadmaps';

// In component:
const { data: roadmap } = useRoadmap(roadmapId!);
const direction = roadmap ? getLanguageDirection(roadmap.language) : 'ltr';

// Apply to title:
<h1 className="text-2xl font-bold text-gray-900" dir={direction}>{session.title}</h1>

// Apply to MarkdownContent:
<MarkdownContent content={session.content} direction={direction} />
```
- **VALIDATE**: `cd client && ~/.bun/bin/bun run lint`

### Task 18: UPDATE `client/src/pages/CreateRoadmapPage.tsx`

- **IMPLEMENT**: Add Hebrew example to examples list
- **CHANGE**: Add a Hebrew example to the examples array
- **CODE SNIPPET**:
```typescript
{[
  'Learn Python for data science',
  'Master React and TypeScript',
  'Understand machine learning basics',
  'Build mobile apps with Flutter',
  'ללמוד פייתון למתחילים',  // Hebrew example
].map((example) => (
```
- **VALIDATE**: `cd client && ~/.bun/bin/bun run lint`

### Task 19: UPDATE `client/src/components/creation/InterviewQuestions.tsx`

- **IMPLEMENT**: Apply RTL to questions if they contain Hebrew
- **IMPORTS**: Add `import { getTextDirection } from '../../utils/language';`
- **CHANGE**: Apply direction to question text based on content
- **CODE SNIPPET**:
```typescript
<p className="text-lg font-medium text-gray-900" dir={getTextDirection(question.question)}>
  {question.question}
</p>
```
- **VALIDATE**: `cd client && ~/.bun/bin/bun run lint`

### Task 20: RUN full validation suite

- **VALIDATE Backend**: `cd server && ./venv/bin/ruff check app/ && ./venv/bin/ruff format app/`
- **VALIDATE Frontend**: `cd client && ~/.bun/bin/bun run lint`
- **VALIDATE Tests**: `cd server && ./venv/bin/pytest`
- **VALIDATE Build**: `cd client && ~/.bun/bin/bun run build`

---

## TESTING STRATEGY

### Unit Tests

**Backend - Language Detection:**
```python
# server/tests/unit/test_language.py
from app.utils.language import detect_language, is_hebrew

def test_detect_hebrew():
    assert detect_language("שלום עולם") == "he"
    assert detect_language("Learn Python") == "en"
    assert detect_language("ללמוד Python") == "he"  # Mixed

def test_is_hebrew():
    assert is_hebrew("שלום") is True
    assert is_hebrew("hello") is False
    assert is_hebrew("hello שלום") is True
```

### Integration Tests

**Backend - Roadmap Creation with Hebrew:**
- Create roadmap with Hebrew topic
- Verify language field is "he"
- Verify interview questions are in Hebrew

### Manual Testing

1. Create roadmap with Hebrew topic: "ללמוד פייתון למתחילים"
2. Verify interview questions appear in Hebrew with RTL
3. Complete creation flow
4. Verify roadmap title and summary are Hebrew
5. Verify session content is Hebrew
6. Verify code blocks stay LTR
7. Test notes editor with Hebrew input
8. Test chat with Hebrew and English messages

---

## VALIDATION COMMANDS

### Level 1: Syntax & Style

```bash
# Backend
cd server && ./venv/bin/ruff check app/ && ./venv/bin/ruff format app/

# Frontend
cd client && ~/.bun/bin/bun run lint
```

### Level 2: Unit Tests

```bash
cd server && ./venv/bin/pytest tests/unit/ -v
```

### Level 3: Integration Tests

```bash
cd server && ./venv/bin/pytest tests/integration/ -v
```

### Level 4: Build Validation

```bash
cd client && ~/.bun/bin/bun run build
```

### Level 5: Manual Validation

1. Start backend: `cd server && ./venv/bin/uvicorn app.main:app --reload`
2. Start frontend: `cd client && ~/.bun/bin/bun run dev`
3. Create roadmap with Hebrew topic
4. Verify RTL display throughout flow

---

## ACCEPTANCE CRITERIA

- [ ] Hebrew topic input triggers Hebrew content generation
- [ ] Language field stored on roadmap document
- [ ] Interview questions generated in Hebrew for Hebrew topics
- [ ] Roadmap title and summary in Hebrew
- [ ] Session content in Hebrew with technical terms in English
- [ ] RTL direction applied to Hebrew roadmap content areas
- [ ] Code blocks remain LTR within RTL content
- [ ] Notes editor auto-detects input direction
- [ ] Chat messages auto-detect direction per message
- [ ] Dashboard stays LTR (only Hebrew titles render RTL inline)
- [ ] All validation commands pass
- [ ] No regressions in English roadmap functionality

---

## COMPLETION CHECKLIST

- [ ] All tasks completed in order
- [ ] Each task validation passed
- [ ] Ruff linting passes (backend)
- [ ] ESLint passes (frontend)
- [ ] Build succeeds
- [ ] Unit tests pass
- [ ] Integration tests pass
- [ ] Manual Hebrew test successful
- [ ] README.md updated with Hebrew support in "Current Status"

---

## NOTES

### Design Decisions

1. **Auto-detect vs explicit toggle**: Chose auto-detect for simplicity. Hebrew characters trigger Hebrew mode automatically.

2. **Language stored per-roadmap, not per-session**: All sessions in a roadmap share the same language. Simpler and matches user intent.

3. **RTL on content only, not layout**: Keeps navigation familiar. Users don't need to relearn the app just because content is Hebrew.

4. **Technical terms stay English**: Standard practice in Israeli tech education. Terms like "React", "API", "useState" remain in English.

5. **Chat matches message language**: More natural UX — user can ask in English on a Hebrew roadmap and get English response.

### Edge Cases

- **Mixed input**: If topic has both Hebrew and English, Hebrew wins (detected via any Hebrew character)
- **Empty roadmap language**: Default to "en" if somehow missing
- **Code in Hebrew content**: All code blocks force LTR via wrapper div

### Future Enhancements

- Language toggle in UI to override auto-detection
- User preference for default language
- Additional RTL languages (Arabic)
