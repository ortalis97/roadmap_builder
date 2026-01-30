# Feature: UX Dashboard & Session Flow Improvements

The following plan should be complete, but it's important that you validate documentation and codebase patterns and task sanity before you start implementing.

Pay special attention to naming of existing utils, types, and models. Import from the right files etc.

## Feature Description

A collection of UX improvements to enhance the learning flow experience:

1. **Sort roadmaps by last visit time** - Most recently accessed roadmaps appear first
2. **Search/filter bar on dashboard** - Client-side filtering of roadmaps by title
3. **Auto-status progression** - Sessions automatically transition to "in_progress" when opened, and to "done" when user clicks "Next Session"
4. **"Continue Learning" button** - One-click access to the last in-progress session from the dashboard

## User Story

As a self-directed learner,
I want my most recent roadmaps at the top, easy filtering, and frictionless session progression,
So that I can quickly resume learning without manual status management.

## Problem Statement

Currently:
- Roadmaps are displayed in database insertion order, not by relevance
- Users with many roadmaps have no way to filter/search
- Users must manually update session status (friction in learning flow)
- Resuming learning requires multiple clicks to find where you left off

## Solution Statement

1. Add `last_visited_at` field to Roadmap model, update on roadmap/session access, sort by it
2. Add client-side search bar that filters roadmaps by title (appears after 3+ roadmaps)
3. Auto-set session to "in_progress" on entry (if "not_started"), auto-set to "done" on explicit "Next Session" click
4. Add "Continue Learning" button that navigates directly to the first "in_progress" session

## Feature Metadata

**Feature Type**: Enhancement
**Estimated Complexity**: Medium
**Primary Systems Affected**: Dashboard, Session navigation, Roadmap model, Session API
**Dependencies**: None (uses existing stack)

---

## CONTEXT REFERENCES

### Relevant Codebase Files - YOU MUST READ THESE BEFORE IMPLEMENTING!

**Backend - Models:**
- `server/app/models/roadmap.py` (lines 1-47) - Roadmap model, needs `last_visited_at` field
- `server/app/models/session.py` - Session model reference

**Backend - Routes:**
- `server/app/routers/roadmaps.py` (lines 28-38) - RoadmapListItem schema, needs `last_visited_at`
- `server/app/routers/roadmaps.py` (lines 115-134) - list_roadmaps endpoint, needs sorting
- `server/app/routers/roadmaps.py` (lines 137-184) - get_roadmap endpoint, update `last_visited_at`
- `server/app/routers/roadmaps.py` (lines 257-308) - get_session endpoint, update parent roadmap's `last_visited_at`
- `server/app/routers/roadmaps.py` (lines 311-384) - update_session endpoint, pattern for session updates

**Frontend - Pages:**
- `client/src/pages/DashboardPage.tsx` (all) - Add search bar, sort logic, "Continue Learning" button
- `client/src/pages/SessionDetailPage.tsx` (lines 35-47) - Status handlers, needs auto-status on entry
- `client/src/pages/SessionDetailPage.tsx` (lines 138-166) - Navigation buttons, needs auto-done on "Next"
- `client/src/pages/RoadmapDetailPage.tsx` (all) - Reference for navigation patterns

**Frontend - Hooks:**
- `client/src/hooks/useRoadmaps.ts` (all) - Roadmap fetching hooks
- `client/src/hooks/useSessions.ts` (all) - Session hooks, needs modification for auto-status

**Frontend - Types:**
- `client/src/types/index.ts` (lines 54-60) - RoadmapListItem type, needs `last_visited_at`
- `client/src/types/index.ts` (lines 43-50) - RoadmapProgress type, for "Continue Learning"

**Frontend - Services:**
- `client/src/services/api.ts` (lines 44-57) - API functions for roadmaps

**Frontend - Components:**
- `client/src/components/SessionStatusIcon.tsx` (all) - getNextStatus function reference

### New Files to Create

None - all changes are modifications to existing files.

### Patterns to Follow

**Backend Model Pattern (from roadmap.py):**
```python
class Roadmap(Document):
    last_visited_at: datetime = Field(default_factory=utc_now)  # Add this field

    async def update_last_visited(self) -> None:
        """Update the last_visited_at timestamp."""
        self.last_visited_at = utc_now()
        await self.save()
```

**Backend Response Schema Pattern (from roadmaps.py):**
```python
class RoadmapListItem(BaseModel):
    last_visited_at: datetime  # Add to schema
```

**Frontend Sorting Pattern (client-side):**
```typescript
// Sort by last_visited_at descending (most recent first)
const sortedRoadmaps = [...roadmaps].sort(
  (a, b) => new Date(b.last_visited_at).getTime() - new Date(a.last_visited_at).getTime()
);
```

**Frontend Filter Pattern:**
```typescript
const filteredRoadmaps = roadmaps.filter(r =>
  r.title.toLowerCase().includes(searchQuery.toLowerCase())
);
```

**Frontend useEffect for Auto-Status Pattern:**
```typescript
useEffect(() => {
  if (session && session.status === 'not_started') {
    updateSession({ status: 'in_progress' });
  }
}, [session?.id]); // Only run when session changes, not on every status update
```

---

## IMPLEMENTATION PLAN

### Phase 1: Backend - Add last_visited_at Field

Add `last_visited_at` field to Roadmap model and update it when roadmap or its sessions are accessed.

**Tasks:**
- Add `last_visited_at` field with default value to Roadmap model
- Add `update_last_visited()` method to Roadmap model
- Update RoadmapListItem schema to include `last_visited_at`
- Update list_roadmaps endpoint to sort by `last_visited_at` descending
- Update get_roadmap endpoint to call `update_last_visited()`
- Update get_session endpoint to update parent roadmap's `last_visited_at`

### Phase 2: Frontend - Update Types and API

Update frontend types to match new backend response.

**Tasks:**
- Add `last_visited_at` to RoadmapListItem type
- Ensure API responses are properly typed

### Phase 3: Frontend - Dashboard Improvements

Add search bar and "Continue Learning" button to dashboard.

**Tasks:**
- Add search state and filter logic
- Add search input UI (conditionally shown when 3+ roadmaps)
- Add "Continue Learning" button that finds first in_progress session
- Apply client-side sorting by last_visited_at as fallback

### Phase 4: Frontend - Auto-Status Progression

Implement automatic status updates on session navigation.

**Tasks:**
- Auto-set to "in_progress" when entering a "not_started" session
- Mark current session as "done" when clicking "Next Session" button
- Add toast notification for status changes with context

---

## STEP-BY-STEP TASKS

### Task 1: UPDATE `server/app/models/roadmap.py`

- **IMPLEMENT**: Add `last_visited_at` field (optional for migration) and update method
- **PATTERN**: Mirror existing `update_timestamp()` method pattern
- **IMPORTS**: Already has `datetime`, `utc_now`, `Field`
- **GOTCHA**: Make field optional (`None` default) so existing docs without it load correctly
- **VALIDATE**: `cd server && ./venv/bin/ruff check app/models/roadmap.py`

```python
# Add field after updated_at (optional for existing docs):
last_visited_at: datetime | None = None

# Add method after update_timestamp():
async def update_last_visited(self) -> None:
    """Update the last_visited_at timestamp."""
    self.last_visited_at = utc_now()
    await self.save()
```

### Task 2: UPDATE `server/app/routers/roadmaps.py` - Schema

- **IMPLEMENT**: Add `last_visited_at` to `RoadmapListItem` schema
- **PATTERN**: Follow existing datetime field pattern in schema
- **IMPORTS**: `datetime` already imported
- **GOTCHA**: Ensure `from_attributes = True` config is present
- **VALIDATE**: `cd server && ./venv/bin/ruff check app/routers/roadmaps.py`

```python
class RoadmapListItem(BaseModel):
    """Schema for roadmap in list view."""
    id: str
    title: str
    session_count: int
    language: str = "en"
    created_at: datetime
    last_visited_at: datetime  # ADD THIS
```

### Task 3: UPDATE `server/app/routers/roadmaps.py` - list_roadmaps endpoint

- **IMPLEMENT**: Sort roadmaps by `last_visited_at` descending, with fallback to `updated_at` for existing docs
- **PATTERN**: Fetch all, then sort in Python to handle None values gracefully
- **IMPORTS**: None needed
- **GOTCHA**: Existing roadmaps may have `last_visited_at=None`, use `updated_at` as fallback
- **VALIDATE**: `cd server && ./venv/bin/ruff check app/routers/roadmaps.py`

```python
@router.get("/", response_model=list[RoadmapListItem])
async def list_roadmaps(
    current_user: User = Depends(get_current_user),
) -> list[RoadmapListItem]:
    """List all roadmaps for the current user, sorted by last visited."""
    roadmaps = await Roadmap.find(
        Roadmap.user_id == current_user.id
    ).to_list()

    # Sort by last_visited_at descending, fallback to updated_at for existing docs
    roadmaps.sort(
        key=lambda r: r.last_visited_at or r.updated_at,
        reverse=True,
    )

    return [
        RoadmapListItem(
            id=str(roadmap.id),
            title=roadmap.title,
            session_count=len(roadmap.sessions),
            language=roadmap.language,
            created_at=roadmap.created_at,
            last_visited_at=roadmap.last_visited_at or roadmap.updated_at,  # Fallback for response
        )
        for roadmap in roadmaps
    ]
```

### Task 4: UPDATE `server/app/routers/roadmaps.py` - get_roadmap endpoint

- **IMPLEMENT**: Call `update_last_visited()` when roadmap is fetched
- **PATTERN**: Similar to existing `update_timestamp()` pattern
- **IMPORTS**: None needed
- **GOTCHA**: Call update AFTER ownership verification, BEFORE returning response
- **VALIDATE**: `cd server && ./venv/bin/ruff check app/routers/roadmaps.py`

```python
# After ownership verification (line ~167), before building response:
await roadmap.update_last_visited()
```

### Task 5: UPDATE `server/app/routers/roadmaps.py` - get_session endpoint

- **IMPLEMENT**: Update parent roadmap's `last_visited_at` when session is fetched
- **PATTERN**: Roadmap is already fetched for ownership check, reuse it
- **IMPORTS**: None needed
- **GOTCHA**: Call update on the roadmap object that's already loaded
- **VALIDATE**: `cd server && ./venv/bin/ruff check app/routers/roadmaps.py`

```python
# After session validation (line ~285), before building response:
await roadmap.update_last_visited()
```

### Task 6: UPDATE `client/src/types/index.ts` - RoadmapListItem type

- **IMPLEMENT**: Add `last_visited_at` field to RoadmapListItem interface
- **PATTERN**: Match existing `created_at` field type (string for ISO date)
- **IMPORTS**: None needed
- **GOTCHA**: Use `string` type for dates (JSON serialization)
- **VALIDATE**: `cd client && ~/.bun/bin/bun run lint`

```typescript
export interface RoadmapListItem {
  id: string;
  title: string;
  session_count: number;
  language: Language;
  created_at: string;
  last_visited_at: string;  // ADD THIS
}
```

### Task 7: UPDATE `client/src/pages/DashboardPage.tsx` - Add search state and filtering

- **IMPLEMENT**: Add search state, filter logic, and search input UI
- **PATTERN**: Standard React controlled input pattern
- **IMPORTS**: Add `useState` to React import
- **GOTCHA**: Only show search bar when 3+ roadmaps exist, case-insensitive search
- **VALIDATE**: `cd client && ~/.bun/bin/bun run lint`

Add to DashboardPage component:
```typescript
const [searchQuery, setSearchQuery] = useState('');

// Filter roadmaps by search query
const filteredRoadmaps = roadmaps?.filter(r =>
  r.title.toLowerCase().includes(searchQuery.toLowerCase())
) ?? [];
```

Add search input in JSX (between header and roadmap list, conditionally):
```tsx
{roadmaps && roadmaps.length >= 3 && (
  <div className="relative">
    <input
      type="text"
      placeholder="Search roadmaps..."
      value={searchQuery}
      onChange={(e) => setSearchQuery(e.target.value)}
      className="w-full px-4 py-2 border border-gray-300 rounded-md focus:ring-2 focus:ring-blue-500 focus:border-blue-500"
    />
    {searchQuery && (
      <button
        onClick={() => setSearchQuery('')}
        className="absolute right-3 top-1/2 -translate-y-1/2 text-gray-400 hover:text-gray-600"
      >
        ✕
      </button>
    )}
  </div>
)}
```

Update grid to use `filteredRoadmaps`:
```tsx
{filteredRoadmaps.map((roadmap) => (
  <RoadmapCard key={roadmap.id} roadmap={roadmap} />
))}
```

### Task 8: UPDATE `client/src/pages/DashboardPage.tsx` - Add "Continue Learning" button

- **IMPLEMENT**: Find first in_progress session across all roadmaps, add button to navigate to it
- **PATTERN**: Use existing progress hook to find roadmaps with in_progress sessions
- **IMPORTS**: Add `useNavigate` from react-router-dom (already imported via Link)
- **GOTCHA**: Need to find which roadmap has in_progress session and which session
- **VALIDATE**: `cd client && ~/.bun/bin/bun run lint`

This requires knowing which sessions are in_progress. We have two options:
1. Fetch all sessions for all roadmaps (expensive)
2. Extend RoadmapListItem to include `current_session_id` (backend change)

For simplicity, we'll:
- Add a new hook that fetches sessions for roadmaps with in_progress status
- Or simpler: add `current_session` to progress endpoint response

**Simpler approach**: Add to RoadmapProgress response the first in_progress session ID, then use that in dashboard.

Actually, let's go simpler: Add a "first_in_progress_session" field to the RoadmapProgress endpoint that returns the first in_progress session's ID. Then in the dashboard, we can iterate through roadmap progress to find one with in_progress.

**Even simpler approach for MVP**: Skip "Continue Learning" for now since it requires fetching progress for all roadmaps. Instead, focus on sorting by last_visited_at which naturally puts the active roadmap at top.

**Decision**: Defer "Continue Learning" button to a follow-up task. The sorting by last_visited_at already addresses the core need of finding recent work.

### Task 9: UPDATE `client/src/pages/SessionDetailPage.tsx` - Auto-set to in_progress

- **IMPLEMENT**: Auto-update status to "in_progress" when entering a "not_started" session
- **PATTERN**: Use useEffect with session.id dependency
- **IMPORTS**: Add `useEffect` to React import (may already be there via useMemo)
- **GOTCHA**: Only trigger when session ID changes AND status is "not_started", prevent infinite loops
- **VALIDATE**: `cd client && ~/.bun/bin/bun run lint`

```typescript
// Add after hooks section, before the navigation useMemo:
useEffect(() => {
  if (session && session.status === 'not_started' && !isPending) {
    updateSession({ status: 'in_progress' });
  }
  // eslint-disable-next-line react-hooks/exhaustive-deps
}, [session?.id]); // Only run when session ID changes, not on every render
```

### Task 10: UPDATE `client/src/pages/SessionDetailPage.tsx` - Auto-done on Next Session

- **IMPLEMENT**: Mark current session as "done" when clicking "Next Session" button
- **PATTERN**: Combine status update with navigation
- **IMPORTS**: None needed
- **GOTCHA**: Only mark done if current status is "in_progress" (not already done/skipped)
- **VALIDATE**: `cd client && ~/.bun/bin/bun run lint`

Replace the simple navigate onClick with a handler:
```typescript
const handleNextSession = () => {
  if (nextSession) {
    // Mark current session as done if it's in_progress
    if (session && session.status === 'in_progress') {
      updateSession({ status: 'done' });
    }
    navigate(`/roadmaps/${roadmapId}/sessions/${nextSession.id}`);
  }
};
```

Update the Next button:
```tsx
<button
  onClick={handleNextSession}  // Changed from inline navigate
  className="flex items-center gap-2 px-4 py-3 md:py-2 min-h-[44px] md:min-h-0 text-gray-700 hover:bg-gray-100 rounded-md"
>
```

### Task 11: Run Backend Tests

- **IMPLEMENT**: Ensure all existing tests pass
- **VALIDATE**: `cd server && ./venv/bin/pytest`

### Task 12: Run Frontend Lint

- **IMPLEMENT**: Ensure all lint rules pass
- **VALIDATE**: `cd client && ~/.bun/bin/bun run lint`

---

## TESTING STRATEGY

### Unit Tests

**Backend**: The existing test suite should cover the roadmap endpoints. The new `last_visited_at` field is a simple addition that follows existing patterns.

No new unit tests required - existing integration tests will validate the changes.

### Integration Tests

**Backend** (`server/tests/integration/test_roadmaps.py`):
- Verify `last_visited_at` is returned in list response
- Verify roadmaps are sorted by `last_visited_at` descending
- Verify `last_visited_at` updates when accessing roadmap
- Verify `last_visited_at` updates when accessing session

### Edge Cases

- New roadmaps should have `last_visited_at` set to creation time
- Existing roadmaps in DB (if any) will have `last_visited_at` as None initially - ensure graceful handling
  - **Solution**: Set default in model, MongoDB will use it for new docs
  - For existing docs, they'll get updated on first access
- Empty search results should show "No roadmaps match your search" message
- Auto-status should not trigger for already "done" or "skipped" sessions

---

## VALIDATION COMMANDS

### Level 1: Syntax & Style

```bash
cd server && ./venv/bin/ruff check app/ && ./venv/bin/ruff format app/
cd client && ~/.bun/bin/bun run lint
```

### Level 2: Unit Tests

```bash
cd server && ./venv/bin/pytest tests/unit/
```

### Level 3: Integration Tests

```bash
cd server && ./venv/bin/pytest tests/integration/
```

### Level 4: Manual Validation

1. **Last Visited Sorting**:
   - Create or access multiple roadmaps
   - Verify most recently accessed appears first on dashboard
   - Access an old roadmap, verify it moves to top

2. **Search/Filter**:
   - Navigate to dashboard with 3+ roadmaps
   - Verify search bar appears
   - Type partial title, verify filtering works
   - Clear search, verify all roadmaps show

3. **Auto In-Progress**:
   - Click on a session with "not_started" status
   - Verify status automatically changes to "in_progress"
   - Verify status icon updates

4. **Auto Done on Next**:
   - Navigate to a session that's "in_progress"
   - Click "Next Session" button
   - Verify previous session is now "done"
   - Verify you're on the next session (which becomes "in_progress")

---

## ACCEPTANCE CRITERIA

- [ ] Roadmaps are sorted by last_visited_at descending on dashboard
- [ ] `last_visited_at` updates when accessing roadmap detail page
- [ ] `last_visited_at` updates when accessing session detail page
- [ ] Search bar appears when user has 3+ roadmaps
- [ ] Search filters roadmaps by title (case-insensitive)
- [ ] Clear button removes search query
- [ ] Entering a "not_started" session auto-sets it to "in_progress"
- [ ] Clicking "Next Session" marks current session as "done" (if in_progress)
- [ ] All existing tests pass
- [ ] No lint errors in frontend or backend

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

1. **Backend sorting vs frontend sorting**: Using backend sorting (`-last_visited_at` in Beanie query) for efficiency and consistency. Frontend receives already-sorted data.

2. **Search threshold (3+ roadmaps)**: Showing search bar only when useful. Single/two roadmaps don't benefit from search.

3. **Auto-status on enter vs explicit action**: Chose auto-status because it reduces friction. Users entering a session clearly intend to work on it.

4. **Auto-done trigger**: Only on "Next Session" click, not on "Previous" or "Back to Roadmap". This respects intentional forward progression.

5. **Deferred "Continue Learning"**: This feature requires additional API work to efficiently find in_progress sessions. The `last_visited_at` sorting already provides most of the value by putting active roadmaps first.

### Migration Consideration

Existing roadmaps in the database won't have `last_visited_at` field. The migration is handled gracefully:
- Model field is optional (`datetime | None = None`)
- Sorting uses `last_visited_at or updated_at` as fallback
- API response uses same fallback logic
- On first access, `update_last_visited()` populates the field

No database migration script needed - the field will be populated naturally as users access their roadmaps.

### Potential Follow-ups

1. "Continue Learning" button - requires extending progress API
2. Toast notifications for auto-status changes
3. Keyboard shortcuts for session navigation
4. "Last visited X days ago" label on roadmap cards
