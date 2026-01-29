# Feature: Redesign Creation Progress Stepper

The following plan should be complete, but it's important that you validate documentation and codebase patterns and task sanity before you start implementing.

Pay special attention to naming of existing utils, types, and models. Import from the right files etc.

## Feature Description

Redesign the roadmap creation progress screen to provide a cleaner, more informative UX. The current 5-circle stepper design will be replaced with a single progress bar + activity log design that shows real-time status updates for each stage. Additionally, fix a bug where the progress screen incorrectly appears during the `starting` stage (when fetching interview questions).

**New Design:**
```
┌─────────────────────────────────────────────────────────┐
│  Creating your roadmap...                               │
│                                                         │
│  [████████████░░░░░░░░░░░░░░░░░░] 45%                  │
│                                                         │
│  ✓ Designed 8 sessions                                  │
│  ● Researching session 4 of 8: "React Hooks"           │
│  ○ Finding videos                                       │
│  ○ Quality check                                        │
└─────────────────────────────────────────────────────────┘
```

## User Story

As a user creating a learning roadmap
I want to see clear, granular progress updates during roadmap generation
So that I understand what's happening and feel confident the system is working

## Problem Statement

1. **Bug**: The progress stepper appears during `starting` stage (while fetching interview questions), making it look like the pipeline is already running
2. **UX Issue**: The current 5-circle stepper provides minimal feedback - stages complete quickly but the UI feels static with just a spinner and generic message

## Solution Statement

1. Replace the circle stepper with a unified progress bar + activity log design
2. Show a simple loading state during `starting` stage instead of the full stepper
3. Emit richer SSE events from the backend to provide session count after architecting
4. Update frontend types and state management to track completed stage summaries

## Feature Metadata

**Feature Type**: Enhancement
**Estimated Complexity**: Medium
**Primary Systems Affected**:
- `client/src/components/creation/CreationProgress.tsx`
- `client/src/pages/CreateRoadmapPage.tsx`
- `client/src/hooks/useRoadmapCreation.ts`
- `client/src/types/index.ts`
- `server/app/agents/orchestrator.py`

**Dependencies**: None (uses existing Tailwind CSS)

---

## CONTEXT REFERENCES

### Relevant Codebase Files - IMPORTANT: YOU MUST READ THESE FILES BEFORE IMPLEMENTING!

- `client/src/components/creation/CreationProgress.tsx` - Current stepper implementation to be replaced
- `client/src/pages/CreateRoadmapPage.tsx` (lines 79-85) - Condition that shows progress screen during `starting`
- `client/src/hooks/useRoadmapCreation.ts` (lines 55-116) - SSE event handling, state structure
- `client/src/types/index.ts` (lines 146-189) - CreationStage, CreationProgress, SSE types
- `client/src/components/ProgressBar.tsx` - Existing progress bar component (can reuse or mirror)
- `server/app/agents/orchestrator.py` (lines 160-210) - SSE events emitted during pipeline

### New Files to Create

None - all changes are modifications to existing files

### Files to Modify

1. `client/src/types/index.ts` - Add new types for stage completion data
2. `client/src/hooks/useRoadmapCreation.ts` - Track completed stages with summaries
3. `client/src/components/creation/CreationProgress.tsx` - Complete rewrite with new design
4. `client/src/pages/CreateRoadmapPage.tsx` - Remove `starting` from progress display condition, add simple loader
5. `server/app/agents/orchestrator.py` - Emit session count in architecting_complete event

### Relevant Documentation

- [Tailwind CSS Transitions](https://tailwindcss.com/docs/transition-property) - For smooth animations
- [React State Updates](https://react.dev/learn/updating-objects-in-state) - For immutable state updates

### Patterns to Follow

**Spinner Pattern** (from InterviewQuestions.tsx lines 127-141):
```tsx
<svg className="animate-spin h-5 w-5" viewBox="0 0 24 24">
  <circle className="opacity-25" cx="12" cy="12" r="10" stroke="currentColor" strokeWidth="4" fill="none" />
  <path className="opacity-75" fill="currentColor" d="M4 12a8 8 0 018-8V0C5.373 0 0 5.373 0 12h4zm2 5.291A7.962 7.962 0 014 12H0c0 3.042 1.135 5.824 3 7.938l3-2.647z" />
</svg>
```

**Progress Bar Pattern** (from ProgressBar.tsx):
```tsx
<div className="flex-1 bg-gray-200 rounded-full h-3 overflow-hidden">
  <div
    className="bg-blue-600 h-3 rounded-full transition-all duration-300"
    style={{ width: `${percentage}%` }}
  />
</div>
```

**Card Container Pattern** (from InterviewQuestions.tsx):
```tsx
<div className="bg-white rounded-lg border border-gray-200 p-6 shadow-sm">
```

**SSE Event Handling Pattern** (from useRoadmapCreation.ts):
```tsx
case 'stage_update': {
  const data = event.data as SSEStageUpdateData;
  updateState({
    stage: data.stage as CreationStage,
    progress: { stage: data.stage as CreationStage, message: data.message },
  });
  break;
}
```

---

## IMPLEMENTATION PLAN

### Phase 1: Backend - Emit Richer SSE Events

Add a new `stage_complete` event after architecting finishes to include session count.

### Phase 2: Frontend Types & State

Extend types to track completed stage summaries and update hook to accumulate them.

### Phase 3: UI Component Rewrite

Replace the circle stepper with the new progress bar + activity log design.

### Phase 4: Fix Starting Stage Bug

Update CreateRoadmapPage to show a simple loader during `starting` instead of the progress screen.

### Phase 5: Testing & Validation

Verify all stages display correctly and test mobile responsiveness.

---

## STEP-BY-STEP TASKS

### Task 1: UPDATE `server/app/agents/orchestrator.py` - Add stage_complete event

- **IMPLEMENT**: After `_run_architect` completes, emit a `stage_complete` event with session count
- **PATTERN**: Follow existing SSEEvent pattern at line 165
- **LOCATION**: After line 176 (after title_suggestion event)

Add this event emission:
```python
# Emit architect completion with session count
yield SSEEvent(
    event="stage_complete",
    data={
        "stage": "architecting",
        "summary": f"Designed {len(outline.sessions)} sessions",
        "session_count": len(outline.sessions),
    },
)
```

- **VALIDATE**: `cd server && ./venv/bin/ruff check app/agents/orchestrator.py`

### Task 2: UPDATE `client/src/types/index.ts` - Add new types

- **IMPLEMENT**: Add types for stage completion tracking
- **LOCATION**: After line 189 (after SSETitleSuggestionData)

Add these types:
```typescript
export interface SSEStageCompleteData {
  stage: string;
  summary: string;
  session_count?: number;
}

export interface CompletedStage {
  stage: CreationStage;
  summary: string;
}
```

Also update `CreationProgress` interface (around line 159) to include:
```typescript
export interface CreationProgress {
  stage: CreationStage;
  message: string;
  current_session?: number;
  total_sessions?: number;
  session_title?: string;
  completed_stages?: CompletedStage[];  // NEW
}
```

- **VALIDATE**: `cd client && ~/.bun/bin/bun run lint`

### Task 3: UPDATE `client/src/hooks/useRoadmapCreation.ts` - Track completed stages

- **IMPLEMENT**: Handle new `stage_complete` event, accumulate completed stages in state
- **PATTERN**: Follow existing event handling pattern at lines 55-116

Add to `CreationState` interface (around line 21):
```typescript
completedStages: CompletedStage[];
```

Add to `initialState` (around line 34):
```typescript
completedStages: [],
```

Add new case in `handleSSEEvent` switch (after line 79):
```typescript
case 'stage_complete': {
  const data = event.data as SSEStageCompleteData;
  setState(prev => ({
    ...prev,
    completedStages: [
      ...prev.completedStages,
      { stage: data.stage as CreationStage, summary: data.summary }
    ],
    progress: {
      ...prev.progress,
      total_sessions: data.session_count ?? prev.progress.total_sessions,
    },
  }));
  break;
}
```

Update imports to include new types:
```typescript
import type {
  // ... existing imports
  SSEStageCompleteData,
  CompletedStage,
} from '../types';
```

- **VALIDATE**: `cd client && ~/.bun/bin/bun run lint`

### Task 4: UPDATE `client/src/pages/CreateRoadmapPage.tsx` - Fix starting stage bug

- **IMPLEMENT**: Remove `'starting'` from progress display condition, add inline simple loader
- **LOCATION**: Lines 79-85 and around line 131

**Step 4a**: Change line 79 from:
```tsx
if (['starting', 'architecting', 'researching', 'finding_videos', 'validating', 'saving'].includes(state.stage)) {
```
To:
```tsx
if (['architecting', 'researching', 'finding_videos', 'validating', 'saving'].includes(state.stage)) {
```

**Step 4b**: Add a new condition for `starting` stage before the idle form (before line 132). Insert:
```tsx
// Show simple loader while fetching interview questions
if (state.stage === 'starting') {
  return (
    <div className="max-w-3xl mx-auto py-6">
      <div className="bg-white rounded-lg shadow p-8">
        <div className="flex flex-col items-center justify-center py-12">
          <svg className="animate-spin h-10 w-10 text-blue-600 mb-4" viewBox="0 0 24 24">
            <circle className="opacity-25" cx="12" cy="12" r="10" stroke="currentColor" strokeWidth="4" fill="none" />
            <path className="opacity-75" fill="currentColor" d="M4 12a8 8 0 018-8V0C5.373 0 0 5.373 0 12h4zm2 5.291A7.962 7.962 0 014 12H0c0 3.042 1.135 5.824 3 7.938l3-2.647z" />
          </svg>
          <p className="text-lg text-gray-700 font-medium">Preparing your questions...</p>
          <p className="text-sm text-gray-500 mt-2">This will just take a moment</p>
        </div>
      </div>
    </div>
  );
}
```

- **VALIDATE**: `cd client && ~/.bun/bin/bun run lint`

### Task 5: REWRITE `client/src/components/creation/CreationProgress.tsx` - New design

- **IMPLEMENT**: Complete rewrite with progress bar + activity log design
- **PATTERN**: Use ProgressBar.tsx pattern for the bar, card pattern from InterviewQuestions.tsx

Replace entire file content with:

```tsx
/**
 * Progress indicator for roadmap creation pipeline.
 * Shows a single progress bar with activity log of completed/current/pending stages.
 */

import type { CreationProgress, CreationStage, CompletedStage } from '../../types';

interface CreationProgressProps {
  progress: CreationProgress;
  completedStages?: CompletedStage[];
}

// Pipeline stages in order (excluding interviewing which happens before this screen)
const PIPELINE_STAGES: { stage: CreationStage; label: string; pendingLabel: string }[] = [
  { stage: 'architecting', label: 'Designing', pendingLabel: 'Design learning path' },
  { stage: 'researching', label: 'Researching', pendingLabel: 'Research content' },
  { stage: 'finding_videos', label: 'Videos', pendingLabel: 'Find videos' },
  { stage: 'validating', label: 'Validating', pendingLabel: 'Quality check' },
  { stage: 'saving', label: 'Saving', pendingLabel: 'Save roadmap' },
];

function getStageIndex(stage: CreationStage): number {
  return PIPELINE_STAGES.findIndex(s => s.stage === stage);
}

function calculateProgress(currentStage: CreationStage, currentSession?: number, totalSessions?: number): number {
  const stageIndex = getStageIndex(currentStage);
  if (stageIndex === -1) return 0;

  // Each stage is worth 20% (5 stages total)
  const baseProgress = stageIndex * 20;

  // For researching stage, add granular progress based on session
  if (currentStage === 'researching' && currentSession && totalSessions) {
    const sessionProgress = (currentSession / totalSessions) * 20;
    return Math.round(baseProgress + sessionProgress);
  }

  // For completed stages, add the full 20%
  if (currentStage === 'complete') return 100;

  // For in-progress stages, show partial progress (10% into the stage)
  return Math.round(baseProgress + 10);
}

export function CreationProgressDisplay({ progress, completedStages = [] }: CreationProgressProps) {
  const currentStageIndex = getStageIndex(progress.stage);
  const progressPercent = calculateProgress(
    progress.stage,
    progress.current_session,
    progress.total_sessions
  );

  // Build summary map from completed stages
  const summaryMap = new Map<CreationStage, string>();
  for (const cs of completedStages) {
    summaryMap.set(cs.stage, cs.summary);
  }

  return (
    <div className="w-full max-w-2xl mx-auto">
      {/* Header */}
      <div className="text-center mb-8">
        <h2 className="text-2xl font-bold text-gray-900 mb-2">Creating your roadmap...</h2>
        <p className="text-gray-600">This usually takes about 30 seconds</p>
      </div>

      {/* Main progress card */}
      <div className="bg-white rounded-lg border border-gray-200 shadow-sm p-6">
        {/* Progress bar */}
        <div className="mb-6">
          <div className="flex justify-between text-sm text-gray-600 mb-2">
            <span>Progress</span>
            <span>{progressPercent}%</span>
          </div>
          <div className="w-full bg-gray-200 rounded-full h-3 overflow-hidden">
            <div
              className="bg-blue-600 h-3 rounded-full transition-all duration-500 ease-out"
              style={{ width: `${progressPercent}%` }}
            />
          </div>
        </div>

        {/* Activity log */}
        <div className="space-y-3">
          {PIPELINE_STAGES.map((stageInfo, index) => {
            const isComplete = currentStageIndex > index;
            const isCurrent = currentStageIndex === index;
            const isPending = currentStageIndex < index;
            const summary = summaryMap.get(stageInfo.stage);

            return (
              <div key={stageInfo.stage} className="flex items-start gap-3">
                {/* Status icon */}
                <div className="flex-shrink-0 w-6 h-6 flex items-center justify-center">
                  {isComplete && (
                    <svg className="w-5 h-5 text-green-500" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                      <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M5 13l4 4L19 7" />
                    </svg>
                  )}
                  {isCurrent && (
                    <div className="w-5 h-5 rounded-full border-2 border-blue-600 border-t-transparent animate-spin" />
                  )}
                  {isPending && (
                    <div className="w-3 h-3 rounded-full bg-gray-300" />
                  )}
                </div>

                {/* Stage text */}
                <div className="flex-1 min-w-0">
                  {isComplete && (
                    <p className="text-gray-700">
                      <span className="text-green-600 font-medium">✓</span>{' '}
                      {summary || `${stageInfo.label} complete`}
                    </p>
                  )}
                  {isCurrent && (
                    <p className="text-blue-700 font-medium">
                      {progress.stage === 'researching' && progress.current_session && progress.total_sessions
                        ? `Researching session ${progress.current_session} of ${progress.total_sessions}${progress.session_title ? `: "${progress.session_title}"` : ''}`
                        : progress.message}
                    </p>
                  )}
                  {isPending && (
                    <p className="text-gray-400">{stageInfo.pendingLabel}</p>
                  )}
                </div>
              </div>
            );
          })}
        </div>
      </div>

      {/* Tip or encouragement */}
      <p className="text-center text-sm text-gray-500 mt-6">
        We're creating personalized content just for you
      </p>
    </div>
  );
}
```

- **VALIDATE**: `cd client && ~/.bun/bin/bun run lint`

### Task 6: UPDATE `client/src/pages/CreateRoadmapPage.tsx` - Pass completedStages to CreationProgress

- **IMPLEMENT**: Pass the new `completedStages` from state to the component
- **LOCATION**: Around line 82

Change:
```tsx
<CreationProgressDisplay progress={state.progress} />
```
To:
```tsx
<CreationProgressDisplay progress={state.progress} completedStages={state.completedStages} />
```

- **VALIDATE**: `cd client && ~/.bun/bin/bun run lint`

### Task 7: UPDATE orchestrator.py - Add stage_complete events for all stages

- **IMPLEMENT**: Emit stage_complete after each major stage completes
- **LOCATION**: After each stage in run_pipeline method

**After researching completes** (after line 197 loop):
```python
# Emit research completion
yield SSEEvent(
    event="stage_complete",
    data={
        "stage": "researching",
        "summary": f"Researched {len(researched_sessions)} sessions",
    },
)
```

**After finding_videos completes** (after line 207 `_run_youtube_agent`):
```python
# Emit video search completion
videos_found = sum(len(s.videos) for s in researched_sessions)
yield SSEEvent(
    event="stage_complete",
    data={
        "stage": "finding_videos",
        "summary": f"Found {videos_found} videos",
    },
)
```

**After validation completes** (after line 270, before saving stage_update):
```python
# Emit validation completion
yield SSEEvent(
    event="stage_complete",
    data={
        "stage": "validating",
        "summary": f"Quality score: {validation_result.overall_score:.0f}/100",
    },
)
```

- **VALIDATE**: `cd server && ./venv/bin/ruff check app/agents/orchestrator.py`

---

## TESTING STRATEGY

### Manual Testing

1. **Start roadmap creation**
   - Enter a topic and submit
   - Verify simple "Preparing questions..." loader appears (not the stepper)

2. **Submit interview answers**
   - Answer questions and submit
   - Verify new progress bar design appears
   - Verify stages show as completed with summaries
   - Verify current stage shows spinner and detail
   - Verify pending stages show as grayed out

3. **Watch full pipeline**
   - Let pipeline complete
   - Verify progress bar fills smoothly
   - Verify session-by-session progress during researching
   - Verify completion redirects to roadmap

4. **Mobile testing**
   - Test on 375px width viewport
   - Verify text doesn't overflow
   - Verify touch targets are adequate

### Edge Cases

- Very long session titles (should truncate or wrap)
- Fast stage completion (should still animate smoothly)
- Error during pipeline (should show error state correctly)

---

## VALIDATION COMMANDS

### Level 1: Syntax & Style

```bash
# Backend linting
cd server && ./venv/bin/ruff check app/agents/orchestrator.py

# Frontend linting
cd client && ~/.bun/bin/bun run lint
```

### Level 2: Type Checking

```bash
# Frontend type check
cd client && ~/.bun/bin/bun run build
```

### Level 3: Backend Tests

```bash
cd server && ./venv/bin/pytest tests/ -v
```

### Level 4: Manual Validation

1. Start both servers:
   ```bash
   # Terminal 1
   cd server && ./venv/bin/uvicorn app.main:app --reload --port 8000

   # Terminal 2
   cd client && ~/.bun/bin/bun run dev
   ```

2. Open http://localhost:5173

3. Log in and create a new roadmap

4. Verify:
   - [ ] "Preparing questions..." loader appears during starting stage
   - [ ] Progress bar + activity log appears after submitting answers
   - [ ] Completed stages show green checkmark with summary
   - [ ] Current stage shows spinner with detail
   - [ ] Pending stages are grayed out
   - [ ] Progress bar fills smoothly as stages complete
   - [ ] Researching shows "session X of Y" progress
   - [ ] Pipeline completes and redirects to roadmap

---

## ACCEPTANCE CRITERIA

- [ ] `starting` stage shows simple "Preparing questions..." loader, not the stepper
- [ ] Progress screen shows single progress bar (not 5 circles)
- [ ] Completed stages display with green checkmark and summary text
- [ ] Current stage displays with spinner and detailed message
- [ ] Pending stages display as grayed out with simple labels
- [ ] Progress bar percentage updates as stages complete
- [ ] Researching stage shows granular "session X of Y" progress
- [ ] All linting and type checks pass
- [ ] Backend tests pass
- [ ] Mobile responsive (works on 375px width)
- [ ] Smooth animations and transitions

---

## COMPLETION CHECKLIST

- [ ] All tasks completed in order
- [ ] Backend emits new `stage_complete` SSE events
- [ ] Frontend types extended with new interfaces
- [ ] Hook tracks completed stages
- [ ] CreationProgress component fully rewritten
- [ ] CreateRoadmapPage shows simple loader for starting stage
- [ ] All validation commands executed successfully
- [ ] Manual testing confirms feature works
- [ ] No regressions in existing functionality

---

## NOTES

### Design Decisions

1. **Single progress bar vs. stepped circles**: The new design provides continuous visual feedback rather than discrete steps. This feels more dynamic when stages complete quickly.

2. **Activity log style**: Using a vertical list with status icons (checkmark, spinner, dot) is more scannable than horizontal circles and allows for longer status messages.

3. **Percentage calculation**: Each of 5 stages is worth 20%. Research stage interpolates based on session progress for granular updates.

4. **Summary text**: Stage completion summaries (e.g., "Designed 8 sessions") give users concrete feedback about what happened.

### Potential Future Enhancements

- Add estimated time remaining based on historical data
- Add subtle animation when a stage completes (brief highlight)
- Add ability to expand completed stages to see more detail
