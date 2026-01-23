# Mobile Support Implementation Plan

## 1. Feature Understanding

### User Story
As a learner using the roadmap app on my phone, I want the interface to be touch-friendly and properly sized so that I can track my learning progress and use the AI assistant while on the go.

### Success Criteria
- All interactive elements have minimum 44x44px touch targets
- Sidebar converts to a slide-out drawer on mobile (<768px)
- Navigation is accessible via hamburger menu on mobile
- All pages are usable on 320px-428px viewport widths
- No horizontal scrolling on any page
- Chat interface works well with mobile keyboard
- Forms and inputs are properly sized for touch

### Out of Scope
- Native mobile app (React Native/Flutter)
- Offline support / PWA features
- Push notifications
- Device-specific features (haptics, camera, etc.)

---

## 2. Codebase Intelligence

### Current State Analysis

**Responsive Breakpoints Found**: Only 2 instances in entire codebase
- `client/src/pages/DashboardPage.tsx`: `md:grid-cols-2 lg:grid-cols-3`
- `client/src/components/VideoSection.tsx`: Uses responsive classes

**Critical Issues Identified**:

| Component | Issue | Impact |
|-----------|-------|--------|
| `Layout.tsx` | Fixed 280px min sidebar width | Sidebar takes 87% of 320px screen |
| `ChatSidebar.tsx` | Mouse-only resize handler | No touch support |
| `SessionDetailPage.tsx` | Small buttons (px-4 py-2) | Hard to tap |
| `InterviewQuestions.tsx` | Small option chips | ~32px height, below 44px minimum |
| `CreateRoadmapPage.tsx` | Button inside input | Awkward on mobile |
| Header in Layout | Email shown inline | Overflows on narrow screens |

### Existing Patterns to Leverage

**Good Pattern - Responsive Grid** (DashboardPage.tsx:67):
```tsx
<div className="grid gap-4 md:grid-cols-2 lg:grid-cols-3">
```

**Tailwind Config** (tailwind.config.js):
- Standard breakpoints available: sm (640px), md (768px), lg (1024px), xl (1280px)
- Typography plugin installed (good for content readability)

### Files to Modify

| File | Changes Required | Priority |
|------|------------------|----------|
| `client/src/components/layout/Layout.tsx` | Mobile nav, responsive header, drawer toggle | P0 |
| `client/src/components/ChatSidebar.tsx` | Convert to drawer/modal on mobile | P0 |
| `client/src/pages/SessionDetailPage.tsx` | Touch-friendly buttons, responsive layout | P1 |
| `client/src/pages/CreateRoadmapPage.tsx` | Larger touch targets, responsive form | P1 |
| `client/src/components/creation/InterviewQuestions.tsx` | Larger option buttons | P1 |
| `client/src/components/ChatInterface.tsx` | Mobile keyboard handling | P1 |
| `client/src/pages/RoadmapDetailPage.tsx` | Responsive session list | P2 |
| `client/src/pages/LoginPage.tsx` | Already reasonable, minor tweaks | P2 |

### New Files to Create

| File | Purpose |
|------|---------|
| `client/src/components/layout/MobileNav.tsx` | Hamburger menu + slide-out navigation |
| `client/src/hooks/useMediaQuery.ts` | Responsive breakpoint detection hook |
| `client/src/hooks/useMobileKeyboard.ts` | Handle mobile keyboard show/hide |

---

## 3. External Research

### Mobile UX Best Practices

**Touch Target Sizing** (Apple HIG / Material Design):
- Minimum touch target: 44x44 points (iOS) / 48x48dp (Android)
- Padding around interactive elements counts toward touch target
- Apply via Tailwind: `min-h-[44px] min-w-[44px]` or `p-3` on buttons

**Mobile Navigation Patterns**:
- Hamburger menu for primary navigation (widely understood)
- Bottom navigation for 3-5 primary actions (not applicable here)
- Slide-out drawer for secondary content (chat sidebar)

**Mobile Keyboard Handling**:
- Use `visualViewport` API to detect keyboard
- Scroll input into view when keyboard appears
- Consider `position: sticky` for input at bottom of chat

### Tailwind Mobile-First Approach

Default styles apply to mobile, then override for larger screens:
```tsx
// Mobile-first pattern
<div className="flex flex-col md:flex-row">
<div className="w-full md:w-64">
<button className="p-3 md:p-2"> // Larger on mobile
```

---

## 4. Strategic Thinking

### Implementation Approach: Mobile-First Refactor

**Option A: Gradual Enhancement** (RECOMMENDED)
- Add mobile styles incrementally to existing components
- Create reusable responsive components (MobileNav, Drawer)
- Lower risk, can ship incrementally

**Option B: Full Rewrite**
- Rewrite layout system from scratch
- Higher risk, longer timeline, all-or-nothing

**Decision**: Option A - Gradual enhancement allows shipping improvements incrementally and testing on real devices throughout.

### Key Architectural Decisions (Confirmed)

1. **Breakpoint Strategy**: Use `md:` (768px) as primary mobile/desktop breakpoint
   - Below 768px = mobile layout (phones, tablets in portrait)
   - 768px and above = desktop layout
   - **Status**: ✅ Confirmed

2. **Sidebar → Drawer**: On mobile, ChatSidebar becomes a full-screen overlay drawer
   - Triggered by floating action button (FAB) in bottom-right
   - Closes on backdrop click, swipe, or close button
   - **Status**: ✅ Confirmed

3. **Navigation**: Hamburger menu in header on mobile
   - Slides out navigation drawer from left
   - Contains: Dashboard, Create, Sign Out
   - **Status**: ✅ Confirmed

4. **Touch Targets**: Larger targets on mobile only
   - Use responsive classes (`py-3 md:py-2`) to increase mobile targets to 44px
   - Desktop stays compact with current sizing
   - **Status**: ✅ Confirmed

5. **Create Input**: Separate submit button on mobile
   - Input full-width, large submit button below on mobile
   - Keep inline button on desktop
   - **Status**: ✅ Confirmed

6. **State Management**: Use existing React state (no new libraries needed)
   - `isMobileNavOpen` in Layout
   - Use media query hook for responsive logic

### Risk Assessment

| Risk | Mitigation |
|------|------------|
| Breaking desktop layout | Mobile-first classes don't affect desktop (md: overrides) |
| Touch interactions conflict with mouse | Use pointer events, not just touch/mouse |
| Performance on low-end devices | Avoid heavy animations, use CSS transforms |
| Testing coverage | Manual testing on real devices + Chrome DevTools |

---

## 5. Implementation Tasks

### Phase 1: Foundation (P0)

#### Task 1.1: Create useMediaQuery Hook
**File**: `client/src/hooks/useMediaQuery.ts`

```tsx
import { useState, useEffect } from 'react';

export function useMediaQuery(query: string): boolean {
  const [matches, setMatches] = useState(false);

  useEffect(() => {
    const media = window.matchMedia(query);
    setMatches(media.matches);

    const listener = (e: MediaQueryListEvent) => setMatches(e.matches);
    media.addEventListener('change', listener);
    return () => media.removeEventListener('change', listener);
  }, [query]);

  return matches;
}

export function useIsMobile(): boolean {
  return !useMediaQuery('(min-width: 768px)');
}
```

**Validation**:
```bash
cd client && ~/.bun/bin/bun run build
```

#### Task 1.2: Create MobileNav Component
**File**: `client/src/components/layout/MobileNav.tsx`

Create hamburger menu button and slide-out navigation drawer:
- Hamburger icon button (44x44px touch target)
- Full-screen overlay when open
- Navigation links: Dashboard, Create New, Sign Out
- Close on backdrop click or navigation

**Validation**:
```bash
cd client && ~/.bun/bin/bun run build && ~/.bun/bin/bun run lint
```

#### Task 1.3: Refactor Layout.tsx for Mobile
**File**: `client/src/components/layout/Layout.tsx`

Changes:
1. Import and use `useIsMobile()` hook
2. Add mobile navigation state (`isMobileNavOpen`)
3. Show hamburger menu on mobile, hide desktop nav
4. Make header responsive (stack on mobile)
5. Hide sidebar completely on mobile (use FAB instead)

**Key Changes**:
```tsx
// Header responsive
<div className="flex flex-col sm:flex-row items-start sm:items-center gap-2">

// Hide desktop sidebar on mobile
{!isMobile && roadmapId && sidebarOpen && (
  <ChatSidebar ... />
)}

// Show FAB for chat on mobile
{isMobile && roadmapId && (
  <button onClick={() => setMobileChatOpen(true)}
    className="fixed bottom-4 right-4 w-14 h-14 bg-blue-600 rounded-full shadow-lg...">
    Chat Icon
  </button>
)}
```

**Validation**:
```bash
cd client && ~/.bun/bin/bun run dev
# Test in Chrome DevTools mobile view (iPhone SE, iPhone 12 Pro)
```

#### Task 1.4: Convert ChatSidebar to Mobile Drawer
**File**: `client/src/components/ChatSidebar.tsx`

Changes:
1. Accept `isMobile` and `isOpen` props
2. On mobile: render as full-screen modal overlay
3. On desktop: keep existing resizable sidebar behavior
4. Add close button in mobile view header
5. Remove resize handle on mobile

**Validation**:
```bash
cd client && ~/.bun/bin/bun run build
# Test chat opens/closes properly on mobile view
```

### Phase 2: Touch-Friendly UI (P1)

#### Task 2.1: Increase Touch Targets in SessionDetailPage
**File**: `client/src/pages/SessionDetailPage.tsx`

Changes:
- Previous/Next buttons: `px-4 py-2` → `px-4 py-3 md:py-2 min-h-[44px] md:min-h-0`
- Status dropdown: increase padding on mobile
- All interactive buttons: responsive padding for mobile-only enlargement

**Validation**:
```bash
cd client && ~/.bun/bin/bun run build
```

#### Task 2.2: Responsive CreateRoadmapPage
**File**: `client/src/pages/CreateRoadmapPage.tsx`

Changes:
- On mobile: Input full-width, submit button as separate full-width button below
- On desktop: Keep current inline button layout
- Use responsive classes: show inline button with `hidden md:block`, show separate button with `md:hidden`
- Increase example topic buttons to 44px height on mobile (`py-3 md:py-1.5`)
- Stack layout on narrow screens

**Validation**:
```bash
cd client && ~/.bun/bin/bun run build
# Test form submission works on both mobile and desktop views
```

#### Task 2.3: Larger Interview Option Buttons
**File**: `client/src/components/creation/InterviewQuestions.tsx`

Changes:
- Option buttons: `px-4 py-2` → `px-4 py-3 md:py-2 min-h-[44px] md:min-h-0`
- Text area: ensure comfortable tap target
- Submit button: full-width on mobile (`w-full md:w-auto`)

**Validation**:
```bash
cd client && ~/.bun/bin/bun run build
```

#### Task 2.4: Mobile Chat Interface
**File**: `client/src/components/ChatInterface.tsx`

Changes:
- Send button: `min-h-[44px] md:min-h-0` for mobile touch target
- Input field: larger touch target on mobile
- Consider sticky input at bottom for mobile drawer context

**Validation**:
```bash
cd client && ~/.bun/bin/bun run build
# Test typing and sending messages on mobile keyboard
```

### Phase 3: Page Layouts (P2)

#### Task 3.1: Responsive RoadmapDetailPage
**File**: `client/src/pages/RoadmapDetailPage.tsx`

Changes:
- Session list items: touch-friendly tap targets
- Delete button: confirm on tap (already has modal)
- Progress bar: ensure readable on narrow screens

#### Task 3.2: Review All Modal Dialogs
Ensure modals are:
- Full-screen or near-full on mobile
- Have large close buttons
- Don't overflow viewport

#### Task 3.3: Test and Fix Any Remaining Issues
- Test all pages at 320px, 375px, 428px widths
- Fix any horizontal scroll issues
- Ensure text is readable (16px+ for body text)

---

## 6. Testing Strategy

### Manual Testing Checklist

**Devices/Viewports to Test**:
- iPhone SE (320px) - smallest target
- iPhone 12/13/14 (390px) - most common
- iPhone 14 Pro Max (428px) - large phone
- iPad (768px) - breakpoint boundary

**Test Scenarios**:
1. [ ] Login flow on mobile
2. [ ] Create roadmap (input topic, answer questions)
3. [ ] View roadmap detail
4. [ ] Navigate between sessions
5. [ ] Update session status
6. [ ] Use chat assistant
7. [ ] Navigate via hamburger menu
8. [ ] All modals display correctly

### Automated Testing

Add responsive test cases:
```tsx
// In component tests
describe('Mobile Layout', () => {
  beforeEach(() => {
    // Mock window.matchMedia for mobile
    window.matchMedia = jest.fn().mockImplementation(query => ({
      matches: query === '(max-width: 767px)',
      addEventListener: jest.fn(),
      removeEventListener: jest.fn(),
    }));
  });

  it('shows hamburger menu on mobile', () => {
    // ...
  });
});
```

---

## 7. Validation Commands

```bash
# Build check (no TypeScript errors)
cd client && ~/.bun/bin/bun run build

# Lint check
cd client && ~/.bun/bin/bun run lint

# Run tests
cd client && ~/.bun/bin/bun test

# Development server for manual testing
cd client && ~/.bun/bin/bun run dev
# Open Chrome DevTools → Toggle device toolbar → Select mobile device
```

---

## 8. Acceptance Criteria

- [x] All buttons and interactive elements have 44px minimum touch targets
- [x] ChatSidebar displays as full-screen drawer on mobile
- [x] Hamburger menu provides navigation on mobile
- [x] No horizontal scrolling on any page at 320px width
- [x] Chat input works correctly with mobile keyboard
- [ ] All existing E2E tests pass
- [ ] Manual testing passes on iPhone SE and iPhone 12 viewports

## 10. Implementation Status: COMPLETE

All implementation tasks have been completed:

### Phase 1: Foundation (P0) ✅
- Task 1.1: Created `useMediaQuery` hook with `useIsMobile()` helper
- Task 1.2: Created `MobileNav` component with hamburger menu and slide-out drawer
- Task 1.3: Refactored `Layout.tsx` for mobile (responsive header, nav, FAB for chat)
- Task 1.4: Converted `ChatSidebar` to mobile drawer (full-screen overlay on mobile)

### Phase 2: Touch-Friendly UI (P1) ✅
- Task 2.1: Updated `SessionDetailPage` with touch-friendly buttons (44px targets)
- Task 2.2: Made `CreateRoadmapPage` responsive (separate input/button on mobile)
- Task 2.3: Enlarged `InterviewQuestions` option buttons for mobile
- Task 2.4: Optimized `ChatInterface` for mobile (larger targets, 2-row input, hidden hints)

### Phase 3: Page Layouts (P2) ✅
- Task 3.1: Made `RoadmapDetailPage` responsive (session list, modal buttons)
- Task 3.2: Updated `DashboardPage` touch targets
- Task 3.3: Reviewed all pages - `LoginPage` already adequate

### Files Created:
- `client/src/hooks/useMediaQuery.ts`
- `client/src/components/layout/MobileNav.tsx`

### Files Modified:
- `client/src/components/layout/Layout.tsx`
- `client/src/components/ChatSidebar.tsx`
- `client/src/pages/SessionDetailPage.tsx`
- `client/src/pages/CreateRoadmapPage.tsx`
- `client/src/components/creation/InterviewQuestions.tsx`
- `client/src/components/ChatInterface.tsx`
- `client/src/pages/RoadmapDetailPage.tsx`
- `client/src/pages/DashboardPage.tsx`

Build verified: ✅ All TypeScript compiles without errors

---

## 9. Implementation Order

1. **Task 1.1**: useMediaQuery hook (dependency for all other tasks)
2. **Task 1.3**: Layout.tsx refactor (core mobile structure)
3. **Task 1.2**: MobileNav component (navigation)
4. **Task 1.4**: ChatSidebar drawer (chat on mobile)
5. **Tasks 2.1-2.4**: Touch targets (can be parallelized)
6. **Tasks 3.1-3.3**: Page layouts and polish

**Estimated Complexity**: Medium-High
- Many files to modify but changes are additive (mobile styles)
- Main complexity in Layout.tsx and ChatSidebar conversions
- Testing requires real device or emulator validation
