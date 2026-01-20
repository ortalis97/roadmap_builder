# Feature: Session Page Markdown Rendering

The following plan should be complete, but it's important that you validate documentation and codebase patterns and task sanity before you start implementing.

Pay special attention to naming of existing utils types and models. Import from the right files etc.

## Feature Description

Add proper markdown rendering to the session detail page so that AI-generated session content (which includes markdown formatting like headers, lists, bold text, code blocks) is displayed correctly. Additionally, remove the hardcoded "Content" heading that appears above the session content, as the content itself already includes its own title as a markdown header.

## User Story

As a learner viewing a session
I want to see the session content with proper markdown formatting
So that headers, lists, code blocks, and other formatting are readable and visually clear

## Problem Statement

Currently, the session page displays markdown content as plain text with `whitespace-pre-wrap`, which shows raw markdown syntax (e.g., `# Header`, `**bold**`, `* list items`) instead of rendered HTML. Additionally, there's a redundant "Content" heading above the session content that adds no value since the content already has its own title.

## Solution Statement

1. Install `react-markdown` library for rendering markdown content
2. Install `@tailwindcss/typography` plugin to properly style the rendered markdown
3. Create a reusable `MarkdownContent` component for rendering markdown
4. Update `SessionDetailPage` to use the new component and remove the "Content" heading

## Feature Metadata

**Feature Type**: Enhancement
**Estimated Complexity**: Low
**Primary Systems Affected**: Frontend (client)
**Dependencies**:
- `react-markdown` - Markdown to React component rendering
- `@tailwindcss/typography` - Tailwind prose styles for markdown content

---

## CONTEXT REFERENCES

### Relevant Codebase Files - IMPORTANT: YOU MUST READ THESE FILES BEFORE IMPLEMENTING!

- `client/src/pages/SessionDetailPage.tsx` (lines 110-115) - Why: This is where the content is displayed and the "Content" heading exists; this file needs to be updated
- `client/tailwind.config.js` - Why: Needs to add the typography plugin
- `client/package.json` - Why: Verify dependencies and add new ones
- `client/src/components/ChatMessage.tsx` - Why: Shows pattern for displaying content; may also benefit from markdown rendering in future

### New Files to Create

- `client/src/components/MarkdownContent.tsx` - Reusable markdown rendering component

### Relevant Documentation

- react-markdown: https://github.com/remarkjs/react-markdown
  - Usage: Renders markdown as React components
  - Why: Standard library for React markdown rendering
- @tailwindcss/typography: https://tailwindcss.com/docs/typography-plugin
  - Usage: Provides `prose` classes for beautiful typography
  - Why: Styles the rendered markdown elements automatically

### Patterns to Follow

**Component Pattern (from existing components):**
```tsx
// Simple functional component with props interface
interface MarkdownContentProps {
  content: string;
  className?: string;
}

export function MarkdownContent({ content, className }: MarkdownContentProps) {
  // Component implementation
}
```

**Tailwind Styling Pattern:**
- Use Tailwind classes for styling
- Use `prose` classes from typography plugin for markdown content
- The file already uses `prose prose-sm max-w-none` classes (line 112 of SessionDetailPage.tsx)

---

## IMPLEMENTATION PLAN

### Phase 1: Install Dependencies

Install the required npm packages using bun (not npm - company restriction noted in CLAUDE.md).

**Tasks:**
- Add `react-markdown` as a dependency
- Add `@tailwindcss/typography` as a dev dependency
- Configure the typography plugin in tailwind.config.js

### Phase 2: Create MarkdownContent Component

Create a reusable component that wraps react-markdown with proper styling.

**Tasks:**
- Create the component file
- Configure proper prose classes for consistent styling
- Export the component

### Phase 3: Update SessionDetailPage

Replace plain text content display with markdown rendering and remove redundant heading.

**Tasks:**
- Import the new MarkdownContent component
- Remove the "Content" heading
- Replace the content div with MarkdownContent component

### Phase 4: Testing & Validation

Verify the changes work correctly.

**Tasks:**
- Run the frontend linter
- Verify the build completes
- Manual testing of markdown rendering

---

## STEP-BY-STEP TASKS

IMPORTANT: Execute every task in order, top to bottom. Each task is atomic and independently testable.

### Task 1: ADD react-markdown dependency

- **IMPLEMENT**: Install react-markdown package using bun
- **COMMAND**: `cd client && ~/.bun/bin/bun add react-markdown`
- **VALIDATE**: `cd client && cat package.json | grep react-markdown`

### Task 2: ADD @tailwindcss/typography dependency

- **IMPLEMENT**: Install the typography plugin as dev dependency
- **COMMAND**: `cd client && ~/.bun/bin/bun add -D @tailwindcss/typography`
- **VALIDATE**: `cd client && cat package.json | grep typography`

### Task 3: UPDATE client/tailwind.config.js

- **IMPLEMENT**: Add the typography plugin to the plugins array
- **PATTERN**: Reference existing empty plugins array at line 10
- **OLD CODE**:
```js
plugins: [],
```
- **NEW CODE**:
```js
plugins: [
  require('@tailwindcss/typography'),
],
```
- **VALIDATE**: `cd client && cat tailwind.config.js | grep typography`

### Task 4: CREATE client/src/components/MarkdownContent.tsx

- **IMPLEMENT**: Create a reusable markdown rendering component
- **IMPORTS**: `import ReactMarkdown from 'react-markdown';`
- **PATTERN**: Follow existing component patterns from ChatMessage.tsx
- **CONTENT**:
```tsx
import ReactMarkdown from 'react-markdown';

interface MarkdownContentProps {
  content: string;
  className?: string;
}

export function MarkdownContent({ content, className = '' }: MarkdownContentProps) {
  return (
    <div className={`prose prose-sm max-w-none prose-headings:text-gray-900 prose-p:text-gray-700 prose-strong:text-gray-900 prose-ul:text-gray-700 prose-ol:text-gray-700 prose-code:text-gray-800 prose-code:bg-gray-100 prose-code:px-1 prose-code:py-0.5 prose-code:rounded prose-pre:bg-gray-900 prose-pre:text-gray-100 ${className}`}>
      <ReactMarkdown>{content}</ReactMarkdown>
    </div>
  );
}
```
- **VALIDATE**: `cd client && ls -la src/components/MarkdownContent.tsx`

### Task 5: UPDATE client/src/pages/SessionDetailPage.tsx - Add Import

- **IMPLEMENT**: Add import for MarkdownContent component at the top of the file
- **PATTERN**: Follow existing import patterns (lines 1-6)
- **ADD AFTER LINE 5** (after NotesEditor import):
```tsx
import { MarkdownContent } from '../components/MarkdownContent';
```
- **VALIDATE**: `cd client && grep "MarkdownContent" src/pages/SessionDetailPage.tsx`

### Task 6: UPDATE client/src/pages/SessionDetailPage.tsx - Replace Content Section

- **IMPLEMENT**: Remove "Content" heading and replace plain text with MarkdownContent
- **PATTERN**: Lines 110-115 of SessionDetailPage.tsx
- **OLD CODE** (lines 110-115):
```tsx
        <div className="p-6 border-b border-gray-200">
          <h2 className="text-lg font-medium text-gray-900 mb-4">Content</h2>
          <div className="prose prose-sm max-w-none text-gray-700 whitespace-pre-wrap">
            {session.content}
          </div>
        </div>
```
- **NEW CODE**:
```tsx
        <div className="p-6 border-b border-gray-200">
          <MarkdownContent content={session.content} />
        </div>
```
- **VALIDATE**: `cd client && grep -A 3 "p-6 border-b border-gray-200" src/pages/SessionDetailPage.tsx | grep -v "Content"`

---

## TESTING STRATEGY

### Manual Testing

1. Start the frontend dev server: `cd client && ~/.bun/bin/bun run dev`
2. Navigate to a session page with markdown content
3. Verify that:
   - Headers are rendered as proper HTML headings (h1, h2, etc.)
   - Lists are rendered as bullet/numbered lists
   - Bold text (`**text**`) is rendered as bold
   - Code blocks are styled with background color
   - The "Content" heading no longer appears
   - The session title is displayed properly from the markdown content itself

### Edge Cases

- Empty content should not cause errors
- Very long content should render without performance issues
- Code blocks with different languages should render properly
- Nested lists should render correctly

---

## VALIDATION COMMANDS

Execute every command to ensure zero regressions and 100% feature correctness.

### Level 1: Syntax & Style

```bash
cd /Users/talis1/Documents/personal_projects/roadmap_builder/client && ~/.bun/bin/bun run lint
```

### Level 2: Build Verification

```bash
cd /Users/talis1/Documents/personal_projects/roadmap_builder/client && ~/.bun/bin/bun run build
```

### Level 3: TypeScript Check

```bash
cd /Users/talis1/Documents/personal_projects/roadmap_builder/client && ~/.bun/bin/bunx tsc --noEmit
```

### Level 4: Manual Validation

1. Start dev server: `cd client && ~/.bun/bin/bun run dev`
2. Log in and navigate to an existing roadmap
3. Click on a session to open the session detail page
4. Verify markdown is rendered properly:
   - Headers appear as larger text
   - Lists have bullets/numbers
   - Bold text is bold
   - Code has background styling
5. Verify the "Content" heading is removed

---

## ACCEPTANCE CRITERIA

- [x] `react-markdown` package is installed
- [x] `@tailwindcss/typography` plugin is installed and configured
- [x] `MarkdownContent` component is created and exports properly
- [x] Session page renders markdown content as formatted HTML
- [x] "Content" heading is removed from session page
- [x] Linting passes with no errors
- [x] Build completes successfully
- [x] TypeScript has no type errors

---

## COMPLETION CHECKLIST

- [ ] All tasks completed in order
- [ ] Each task validation passed immediately
- [ ] All validation commands executed successfully
- [ ] Lint check passes
- [ ] Build completes without errors
- [ ] Manual testing confirms markdown renders correctly
- [ ] Manual testing confirms "Content" heading is removed
- [ ] Code follows project conventions

---

## NOTES

### Design Decisions

1. **react-markdown over other libraries**: react-markdown is the most popular and well-maintained React markdown library. It's lightweight and integrates well with React.

2. **@tailwindcss/typography plugin**: This provides the `prose` classes that automatically style all HTML elements generated by markdown rendering. This is the standard Tailwind approach and keeps styling consistent.

3. **Reusable MarkdownContent component**: While we only need it in one place now, creating a reusable component allows for future use in:
   - Chat messages (AI responses often contain markdown)
   - Roadmap summaries
   - Any other place markdown might be displayed

4. **Prose customizations**: The component includes customized prose classes to:
   - Match the existing gray color scheme
   - Style inline code with background color
   - Style code blocks with dark background

### Future Considerations

- The `ChatMessage` component could also use MarkdownContent for rendering AI responses, but that's outside the scope of this task
- If syntax highlighting for code blocks is needed, `react-syntax-highlighter` can be integrated with react-markdown
- The NotesEditor could potentially support markdown preview, but that would be a separate feature
