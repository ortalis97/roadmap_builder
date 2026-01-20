# Product Requirements Document: Learning Roadmap App

## 1. Executive Summary

The Learning Roadmap App is a focused tool for self-directed learners to transform messy learning plans into clear, trackable roadmaps with an AI assistant embedded directly into the learning flow. Unlike generic note-taking apps or task managers, this is a roadmap-first learning workspace where structure, progress, and understanding live together.

The core value proposition is simple: paste a messy learning plan, get a structured roadmap, track your progress, and get contextual AI help—all in one place. The AI assistant knows your entire learning context, making it meaningfully helpful rather than generic.

**MVP Goal:** Deliver a functional web application where users can create AI-generated learning roadmaps from freeform text, track progress through sessions, and interact with a context-aware AI assistant.

---

## 2. Mission

**Mission Statement:** Empower self-directed learners to turn chaotic learning intentions into structured, trackable journeys with intelligent assistance.

**Core Principles:**
1. **Roadmap-first** — The roadmap is the primary object, not notes or tasks
2. **Context is king** — AI assistance is valuable because it understands your learning structure
3. **Clarity over gamification** — Show progress without pressure or manipulation
4. **Calm and minimal** — Serious tool for serious learners, no distractions
5. **Living documents** — Roadmaps evolve with your learning, not static plans

---

## 3. Target Users

### Primary Personas

**Self-Directed Learner**
- Already learns independently using articles, videos, courses, and AI
- Creates learning plans in ChatGPT, Notion, or Google Docs
- Frustrated that plans become static and disconnected from actual learning
- Technical comfort: Comfortable with web apps, uses AI tools regularly

**Tech Professional Upskilling**
- Needs to learn new technologies or domains for work
- Values structured approaches but lacks time to maintain them
- Wants to see progress and know what's next
- Technical comfort: High

**Student (Self-Study)**
- Supplements formal education with self-directed learning
- Needs organization for personal learning projects
- Wants AI help to understand concepts
- Technical comfort: Medium to high

### Non-Goals (v1)
- ❌ Teams or collaborative learning
- ❌ Teachers managing students
- ❌ Corporate learning programs
- ❌ Non-technical users uncomfortable with AI

---

## 4. MVP Scope

### In Scope ✅

**Core Functionality**
- ✅ User authentication (Google OAuth)
- ✅ Create roadmap from freeform text via AI
- ✅ View roadmap with all sessions
- ✅ Open and view individual sessions
- ✅ Mark session status (Not started, In progress, Done, Skipped)
- ✅ View progress (completion percentage, session statuses)
- ✅ Write notes within sessions
- ✅ AI chat assistant (context-aware of roadmap and current session)

**Technical**
- ✅ React + Vite frontend
- ✅ MongoDB Atlas database
- ✅ Gemini API integration for AI features
- ✅ Responsive web design (mobile-friendly)
- ✅ User data isolation (users only see their own roadmaps)

**Deployment**
- ✅ Web application deployment
- ✅ Basic error handling and loading states

### Out of Scope ❌

**Features Deferred**
- ❌ Roadmap sharing/templates
- ❌ Live Google Docs syncing
- ❌ Notifications or reminders
- ❌ Gamification or streaks
- ❌ Team learning features
- ❌ Public profiles
- ❌ AI auto-editing the roadmap
- ❌ Monetization
- ❌ Weekly review/reflection features
- ❌ Roadmap editing with AI suggestions
- ❌ Collections/public library

**Technical Deferred**
- ❌ Native mobile apps
- ❌ Offline support
- ❌ Real-time collaboration
- ❌ Export/import formats

---

## 5. User Stories

### Primary User Stories

**US1: Create Roadmap from Text**
> As a learner, I want to paste my messy learning plan and get a structured roadmap, so that I don't have to manually organize my learning goals.

*Example: User pastes "I want to learn React - components, hooks, state management, routing, maybe some testing. Probably 2-3 months of learning." → App generates a roadmap with 8-10 sessions covering these topics.*

**US2: View Learning Progress**
> As a learner, I want to see my overall progress and what's next, so that I stay motivated and know where I am in my journey.

*Example: Dashboard shows "React Fundamentals: 4/10 sessions complete (40%)" with clear visual of completed vs remaining sessions.*

**US3: Track Session Completion**
> As a learner, I want to mark sessions as complete or skipped, so that my progress accurately reflects my learning.

*Example: After finishing a session on React Hooks, user clicks "Mark as Done" and sees progress update immediately.*

**US4: Take Session Notes**
> As a learner, I want to write notes within a session, so that I capture my understanding and questions in context.

*Example: While learning about useEffect, user writes notes about cleanup functions directly in that session.*

**US5: Get Contextual AI Help**
> As a learner, I want to ask the AI assistant questions while learning, so that I get help that understands what I'm studying.

*Example: While in "React State Management" session, user asks "What's the difference between useState and useReducer?" and AI responds with context-aware explanation referencing the roadmap structure.*

**US6: Review Session Content**
> As a learner, I want to see the content and resources for each session, so that I know what to study.

*Example: Opening "React Components" session shows learning objectives, key concepts, and suggested resources.*

**US7: Authenticate Securely**
> As a user, I want to log in with my Google account, so that I can access my roadmaps securely without creating another password.

*Example: User clicks "Sign in with Google", authenticates, and sees their dashboard with existing roadmaps.*

**US8: Manage Multiple Roadmaps**
> As a learner, I want to have multiple roadmaps for different topics, so that I can track parallel learning journeys.

*Example: User has separate roadmaps for "React", "System Design", and "TypeScript", each with independent progress.*

---

## 6. Core Architecture & Patterns

### High-Level Architecture

```
┌─────────────────────────────────────────────────────────┐
│                    Frontend (React + Vite)               │
│  ┌──────────┐  ┌──────────┐  ┌──────────┐  ┌─────────┐ │
│  │  Auth    │  │ Roadmap  │  │ Session  │  │   AI    │ │
│  │  Views   │  │  Views   │  │  Views   │  │  Chat   │ │
│  └──────────┘  └──────────┘  └──────────┘  └─────────┘ │
└─────────────────────────────────────────────────────────┘
                            │
                            ▼
┌─────────────────────────────────────────────────────────┐
│                   API Layer (REST)                       │
│  ┌──────────┐  ┌──────────┐  ┌──────────┐  ┌─────────┐ │
│  │  Auth    │  │ Roadmap  │  │ Session  │  │   AI    │ │
│  │   API    │  │   API    │  │   API    │  │   API   │ │
│  └──────────┘  └──────────┘  └──────────┘  └─────────┘ │
└─────────────────────────────────────────────────────────┘
                            │
              ┌─────────────┼─────────────┐
              ▼             ▼             ▼
        ┌──────────┐  ┌──────────┐  ┌──────────┐
        │ MongoDB  │  │  Auth    │  │  Gemini  │
        │  Atlas   │  │ Provider │  │   API    │
        └──────────┘  └──────────┘  └──────────┘
```

### Directory Structure

```
roadmap_builder/
├── client/                 # React frontend
│   ├── src/
│   │   ├── components/     # Reusable UI components
│   │   ├── pages/          # Route-level components
│   │   ├── hooks/          # Custom React hooks
│   │   ├── services/       # API client functions
│   │   ├── context/        # React context providers
│   │   ├── types/          # TypeScript types
│   │   └── utils/          # Helper functions
│   ├── public/
│   └── index.html
├── server/                 # Python FastAPI backend
│   ├── app/
│   │   ├── __init__.py
│   │   ├── main.py         # FastAPI app entry point
│   │   ├── config.py       # Settings and configuration
│   │   ├── routers/        # API route handlers
│   │   │   ├── auth.py
│   │   │   ├── roadmaps.py
│   │   │   └── ai.py
│   │   ├── models/         # Pydantic + Beanie models
│   │   │   ├── user.py
│   │   │   ├── roadmap.py
│   │   │   └── chat.py
│   │   ├── services/       # Business logic
│   │   │   ├── ai_service.py
│   │   │   └── roadmap_service.py
│   │   ├── middleware/     # Auth, CORS, etc.
│   │   └── utils/          # Helper functions
│   ├── tests/
│   ├── requirements.txt
│   └── pyproject.toml
└── docs/                   # Documentation
```

### Key Design Patterns

1. **Document-Oriented Data Model** — Leverage MongoDB's document structure for roadmaps and sessions
2. **Context-Aware AI** — Pass roadmap + session context with every AI request
3. **Optimistic Updates** — Update UI immediately, sync with server in background
4. **Component Composition** — Small, focused React components composed together
5. **Service Layer Separation** — API calls abstracted into service modules

---

## 7. Core Features

### Feature 1: Roadmap Creation

**Purpose:** Transform unstructured learning intentions into structured roadmaps

**Operations:**
- Accept freeform text input describing learning goals
- Optional hints: duration, depth, specific goals
- Send to Gemini API for parsing and structuring
- Generate roadmap title, summary, and session list
- Allow user to review and confirm before saving

**Key Behaviors:**
- AI interprets intent, not just keywords
- Reasonable defaults for session count (5-15 sessions)
- Each session gets: title, content, learning objectives
- User can regenerate if unsatisfied

### Feature 2: Roadmap Dashboard

**Purpose:** Provide overview of all learning journeys

**Operations:**
- List all user's roadmaps with progress indicators
- Show completion percentage per roadmap
- Quick access to continue learning (last active session)
- Create new roadmap action

**Key Behaviors:**
- Maximum 10 roadmaps per user (v1 limit)
- Sort by last accessed or creation date
- Visual progress bars

### Feature 3: Session View

**Purpose:** Focus on a single learning unit

**Operations:**
- Display session title, content, and resources
- Show current status with ability to change
- Notes editor for personal annotations
- Navigation to previous/next sessions
- Access to AI chat

**Key Behaviors:**
- Auto-save notes
- Status changes update roadmap progress
- Session content is read-only (intentional separation from editing)

### Feature 4: AI Chat Assistant

**Purpose:** Provide contextual help during learning

**Operations:**
- Chat interface available while viewing roadmap/session
- Explain concepts mentioned in current session
- Answer questions about the topic
- Suggest additional resources
- Clarify confusion

**Constraints (AI Cannot):**
- ❌ Modify roadmap structure
- ❌ Change session content
- ❌ Update progress/status
- ❌ Access other users' data

**Context Provided to AI:**
- Full roadmap structure and summary
- Current session content
- User's progress state
- Current conversation history

### Feature 5: Progress Tracking

**Purpose:** Visualize learning journey completion

**Operations:**
- Calculate completion percentage
- Track session statuses
- Show visual progress indicators
- Identify current/next session

**Session Statuses:**
- Not started (default)
- In progress
- Done
- Skipped

---

## 8. Technology Stack

### Frontend
| Technology | Version | Purpose |
|------------|---------|---------|
| React | 18.x | UI framework |
| Vite | 5.x | Build tool and dev server |
| TypeScript | 5.x | Type safety |
| React Router | 6.x | Client-side routing |
| TanStack Query | 5.x | Server state management |
| Tailwind CSS | 3.x | Styling |

### Backend
| Technology | Version | Purpose |
|------------|---------|---------|
| Python | 3.11+ | Runtime |
| FastAPI | 0.109+ | Web framework |
| Pydantic | 2.x | Data validation and settings |
| Uvicorn | 0.27+ | ASGI server |

### Database
| Technology | Purpose |
|------------|---------|
| MongoDB Atlas | Primary database (document storage) |
| Motor | Async MongoDB driver for Python |
| Beanie | Async ODM for MongoDB (Pydantic-based) |

### AI Integration
| Technology | Purpose |
|------------|---------|
| Gemini API | Roadmap generation, chat assistant |
| google-generativeai | Official Gemini Python SDK |

### Authentication
| Technology | Purpose |
|------------|---------|
| Firebase Auth | Google OAuth provider (client-side) |
| firebase-admin | Server-side token verification |

### Development
| Tool | Purpose |
|------|---------|
| ESLint + Prettier | Frontend linting/formatting |
| Ruff | Python linting and formatting |
| pytest | Python testing |
| Vitest | Frontend testing |

---

## 9. Security & Configuration

### Authentication
- Firebase Auth handles Google OAuth 2.0 on the client
- Client sends Firebase ID token with each API request
- Backend verifies token using firebase-admin SDK
- User ID extracted from verified token for data filtering

### Authorization
- Users can only access their own roadmaps
- All API endpoints require valid Firebase ID token
- User ID from token used for all database queries

### Configuration (Environment Variables)

**Backend (.env)**
```
# Database
MONGODB_URI=mongodb+srv://...

# Firebase (download from Firebase Console)
GOOGLE_APPLICATION_CREDENTIALS=./firebase-service-account.json

# AI
GEMINI_API_KEY=...

# Server
PORT=8000
ENVIRONMENT=development|production
CORS_ORIGINS=http://localhost:5173
```

**Frontend (.env)**
```
VITE_API_URL=http://localhost:8000/api/v1
VITE_FIREBASE_API_KEY=...
VITE_FIREBASE_AUTH_DOMAIN=...
VITE_FIREBASE_PROJECT_ID=...
```

### Security Scope

**In Scope (v1):**
- ✅ Secure authentication via OAuth
- ✅ Data isolation between users
- ✅ HTTPS in production
- ✅ Environment variable secrets
- ✅ Input validation

**Out of Scope (v1):**
- ❌ Rate limiting (add if needed)
- ❌ Audit logging
- ❌ Two-factor authentication
- ❌ Data encryption at rest

---

## 10. API Specification

### Base URL
```
/api/v1
```

### Authentication
All endpoints except `/auth/*` require Bearer token in Authorization header.

### Endpoints

#### Auth
```
POST   /auth/google          # Initiate Google OAuth
GET    /auth/google/callback # OAuth callback
POST   /auth/logout          # Logout
GET    /auth/me              # Get current user
```

#### Roadmaps
```
GET    /roadmaps             # List user's roadmaps
POST   /roadmaps             # Create roadmap (from AI)
GET    /roadmaps/:id         # Get roadmap with sessions
DELETE /roadmaps/:id         # Delete roadmap
```

#### Sessions
```
GET    /roadmaps/:id/sessions/:sessionId    # Get session details
PATCH  /roadmaps/:id/sessions/:sessionId    # Update status/notes
```

#### AI
```
POST   /ai/generate-roadmap  # Generate roadmap from text
POST   /ai/chat              # Chat with AI assistant
```

### Example Payloads

**Create Roadmap Request:**
```json
{
  "input": "I want to learn React - components, hooks, state management...",
  "hints": {
    "duration": "2-3 months",
    "depth": "intermediate"
  }
}
```

**Create Roadmap Response:**
```json
{
  "id": "roadmap_123",
  "title": "React Fundamentals to Intermediate",
  "summary": "A structured journey through React...",
  "sessions": [
    {
      "id": "session_1",
      "title": "Introduction to React",
      "content": "...",
      "status": "not_started",
      "order": 1
    }
  ],
  "progress": 0,
  "createdAt": "2024-01-15T..."
}
```

**AI Chat Request:**
```json
{
  "roadmapId": "roadmap_123",
  "sessionId": "session_5",
  "message": "Can you explain useEffect cleanup functions?"
}
```

---

## 11. Success Criteria

### MVP Success Definition
The MVP is successful when a user can complete the full journey: paste a learning plan → get a structured roadmap → track progress through sessions → get meaningful AI help along the way.

### Functional Requirements
- ✅ User can authenticate with Google
- ✅ User can paste text and receive AI-generated roadmap
- ✅ User can view roadmap with all sessions
- ✅ User can open individual sessions
- ✅ User can mark sessions as done/skipped/in-progress
- ✅ User can write and save notes per session
- ✅ User can chat with AI that knows the roadmap context
- ✅ User can see progress percentage
- ✅ User can create up to 10 roadmaps
- ✅ User can delete roadmaps

### Quality Indicators
- Page load under 2 seconds
- AI responses under 5 seconds
- No data loss on session updates
- Mobile-responsive layout
- Clear error messages

### User Experience Goals
- "I can turn my messy plan into a real roadmap in under 2 minutes"
- "I can see exactly where I am in my learning"
- "The AI actually understands what I'm learning"
- "The app feels calm and focused, not overwhelming"

---

## 12. Implementation Phases

### Phase 1: Foundation
**Goal:** Set up project structure, database, and authentication

**Deliverables:**
- ✅ React + Vite project setup with TypeScript
- ✅ FastAPI backend with Python project structure
- ✅ MongoDB Atlas connection with Beanie ODM
- ✅ Firebase Auth integration (client + server verification)
- ✅ Basic user model and API
- ✅ Protected routes setup (frontend + backend)

**Validation:** User can sign in with Google and see empty dashboard

---

### Phase 2: Core Roadmap Features
**Goal:** Implement roadmap creation and viewing

**Deliverables:**
- ✅ Roadmap creation UI (text input + hints)
- ✅ Gemini integration for roadmap generation
- ✅ Roadmap and Session MongoDB models
- ✅ Roadmap list view (dashboard)
- ✅ Roadmap detail view with sessions
- ✅ Session detail view
- ✅ Basic styling with Tailwind

**Validation:** User can create a roadmap from text and view it

---

### Phase 3: Progress & Notes
**Goal:** Enable progress tracking and note-taking

**Deliverables:**
- ✅ Session status updates (UI + API)
- ✅ Progress calculation and display
- ✅ Notes editor in session view
- ✅ Auto-save for notes
- ✅ Visual progress indicators on dashboard

**Validation:** User can track progress and take notes

---

### Phase 4: AI Assistant & Polish
**Goal:** Add AI chat and polish the experience

**Deliverables:**
- ✅ AI chat component
- ✅ Chat API with context injection
- ✅ Chat history per session
- ✅ Error handling and loading states
- ✅ Mobile responsiveness
- ✅ Delete roadmap functionality
- ✅ Empty states and onboarding hints

**Validation:** Full user journey works smoothly

---

## 13. Future Considerations

### Post-MVP Enhancements
- Roadmap sharing as templates
- Clone shared roadmaps
- Guided roadmap creation (AI interview)
- Roadmap editing with AI suggestions
- Weekly review/reflection features
- **YouTube Agent** — AI agent that finds relevant video recommendations for each session
  - Runs after Researcher agent to ensure videos align with generated content
  - Searches YouTube for educational content matching session topics
  - Provides curated video links with descriptions, duration, and channel info
  - Filters for quality (views, ratings, channel reputation)
  - **Data model**: Add `resources: list[VideoResource]` field to Session model
    - Structured storage enables refresh, filtering, and analytics
    - UI renders as markdown in a "Recommended Videos" section
  - **Pipeline integration**:
    ```
    Researcher → YouTube Agent → Validator → Save
        ↓              ↓
    content      video links → merge into ResearchedSession
    ```

### Integration Opportunities
- Export to Notion/Google Docs
- Import from existing plans
- Calendar integration for scheduling
- Browser extension for resource saving

### Advanced Features
- Collections/public library of roadmaps
- Light collaboration features
- Mobile native apps (React Native)
- Offline support with sync

### Internationalization (i18n)
- **Hebrew support (RTL)** — Full right-to-left layout support for Hebrew speakers
  - RTL text direction for UI components
  - Hebrew UI translations
  - RTL-aware markdown rendering
  - Bidirectional text handling for mixed Hebrew/English content
- Additional language support as needed

---

## 14. Risks & Mitigations

### Risk 1: AI Output Quality
**Risk:** Gemini may generate poorly structured, inconsistent, or unhelpful roadmaps
**Impact:** High — core value proposition depends on good AI output

**Mitigation Strategy:**

1. **Structured Prompting with Examples**
   - Use few-shot prompting: provide 2-3 example inputs → outputs in the prompt
   - Define explicit JSON schema for expected output format
   - Include constraints: min/max sessions, required fields, content guidelines

2. **Output Validation Layer**
   - Validate AI response against Pydantic schema before saving
   - Check for required fields: title, summary, sessions array
   - Verify session count is reasonable (3-20 sessions)
   - Reject malformed responses and retry with adjusted prompt

3. **Retry with Fallback**
   - On validation failure, retry up to 2 times with refined prompt
   - Add explicit instructions addressing the failure reason
   - If all retries fail, show user-friendly error with option to try again

4. **User Control**
   - "Regenerate" button to request a new version
   - Preview before saving — user confirms or regenerates
   - Future: allow manual editing of generated structure

5. **Prompt Iteration Infrastructure**
   - Store prompts in separate files for easy iteration
   - Log AI inputs/outputs for debugging and improvement
   - Track regeneration rate as a quality metric

**Example Prompt Structure:**
```python
SYSTEM_PROMPT = """
You are a learning roadmap architect. Given a learning goal, create a structured roadmap.

Output JSON matching this schema:
{
  "title": "Clear, descriptive title",
  "summary": "2-3 sentence overview of the learning journey",
  "sessions": [
    {
      "title": "Session title",
      "content": "Detailed learning content with objectives and key concepts",
      "resources": ["Optional suggested resources"]
    }
  ]
}

Rules:
- Create 5-15 sessions depending on scope
- Each session should be completable in 1-3 hours
- Progress from fundamentals to advanced
- Include practical application where relevant
"""
```

### Risk 2: Scope Creep
**Risk:** Temptation to add features during MVP development
**Impact:** Medium — delays launch
**Mitigation:**
- Strict adherence to Out of Scope list
- Document ideas for future phases instead of implementing
- Regular check-ins against MVP definition

### Risk 3: AI API Costs
**Risk:** Gemini API costs may be higher than expected with usage
**Impact:** Low for MVP — manageable at small scale
**Mitigation:**
- Monitor usage closely
- Implement basic caching for repeated queries
- Consider usage limits per user if needed

### Risk 4: MongoDB Document Size
**Risk:** Roadmaps with extensive chat history could grow large
**Impact:** Low — unlikely in MVP timeframe
**Mitigation:**
- Store chat history in separate collection
- Implement pagination for chat history

---

## 15. Deployment Strategy

### Overview

The application is deployed using a low-cost, easy-to-manage stack:

| Component | Service | Cost |
|-----------|---------|------|
| **Frontend** | Vercel | Free |
| **Backend** | Railway | Free ($5 credit/month) |
| **Database** | MongoDB Atlas | Free (M0 tier) |
| **Auth** | Firebase | Free |
| **AI** | Gemini API | Free tier |

### Architecture

```
┌─────────────────┐     ┌─────────────────┐     ┌─────────────────┐
│     Vercel      │────▶│     Railway     │────▶│  MongoDB Atlas  │
│  (React SPA)    │     │   (FastAPI)     │     │   (Database)    │
└─────────────────┘     └─────────────────┘     └─────────────────┘
        │                       │
        │                       ▼
        │               ┌─────────────────┐
        └──────────────▶│  Firebase Auth  │
                        └─────────────────┘
```

### Key Considerations

- **SSE Streaming**: Railway supports long-lived connections required for real-time roadmap creation progress
- **Cold Starts**: Railway free tier runs continuously (no cold starts) until $5 credit exhausted
- **Fallback**: Can migrate backend to Render if Railway credits become insufficient

### Detailed Plan

See [`.agents/plans/deployment-railway-vercel.md`](.agents/plans/deployment-railway-vercel.md) for step-by-step implementation instructions.

---

## 16. Appendix

### Data Models (Pydantic/Beanie)

**User**
```python
class User(Document):
    firebase_uid: str
    email: str
    name: str
    picture: Optional[str] = None
    created_at: datetime = Field(default_factory=datetime.utcnow)
    updated_at: datetime = Field(default_factory=datetime.utcnow)

    class Settings:
        name = "users"
```

**Draft** (stores original pasted text, used once for parsing)
```python
class Draft(Document):
    user_id: PydanticObjectId
    raw_text: str                    # Original pasted content
    created_at: datetime = Field(default_factory=datetime.utcnow)

    class Settings:
        name = "drafts"
```

**Roadmap** (production document, references Draft)
```python
class SessionSummary(BaseModel):
    """Embedded in Roadmap for quick session listing."""
    id: PydanticObjectId
    title: str
    order: int

class Roadmap(Document):
    user_id: PydanticObjectId
    draft_id: PydanticObjectId       # Reference to original Draft
    title: str
    summary: Optional[str] = None    # AI-generated later
    sessions: List[SessionSummary] = []  # Lightweight refs (id, title, order)
    created_at: datetime = Field(default_factory=datetime.utcnow)
    updated_at: datetime = Field(default_factory=datetime.utcnow)

    class Settings:
        name = "roadmaps"
```

**Session** (separate collection, full content)
```python
class Session(Document):
    roadmap_id: PydanticObjectId     # Reference to parent Roadmap
    order: int                        # Session number (1, 2, 3...)
    title: str
    content: str                      # Full session content (markdown)
    status: Literal["not_started", "in_progress", "done", "skipped"] = "not_started"
    notes: str = ""                   # User's notes
    created_at: datetime = Field(default_factory=datetime.utcnow)
    updated_at: datetime = Field(default_factory=datetime.utcnow)

    class Settings:
        name = "sessions"
```

**ChatHistory**
```python
class ChatMessage(BaseModel):
    role: Literal["user", "assistant"]
    content: str
    timestamp: datetime = Field(default_factory=datetime.utcnow)

class ChatHistory(Document):
    roadmap_id: PydanticObjectId
    session_id: PydanticObjectId     # Reference to Session document
    messages: List[ChatMessage] = []

    class Settings:
        name = "chat_histories"
```

**Data Model Relationships**
```
Draft (raw_text)
  ↑
  │ draft_id
  │
Roadmap (title, summary, sessions[])
  ↑
  │ roadmap_id
  │
Session (content, notes, status)
  ↑
  │ session_id
  │
ChatHistory (messages[])
```

### Related Documents
- Initial thoughts: `initial_thoughts.txt`
- Tech decisions documented in this conversation

### Key Dependencies

**Frontend:**
- [React](https://react.dev/)
- [Vite](https://vitejs.dev/)
- [Tailwind CSS](https://tailwindcss.com/)
- [TanStack Query](https://tanstack.com/query)
- [Firebase JS SDK](https://firebase.google.com/docs/web/setup)

**Backend:**
- [FastAPI](https://fastapi.tiangolo.com/)
- [Beanie ODM](https://beanie-odm.dev/)
- [Motor](https://motor.readthedocs.io/)
- [firebase-admin](https://firebase.google.com/docs/admin/setup)
- [google-generativeai](https://ai.google.dev/tutorials/python_quickstart)

**Services:**
- [MongoDB Atlas](https://www.mongodb.com/atlas)
- [Firebase Auth](https://firebase.google.com/docs/auth)
- [Gemini API](https://ai.google.dev/)
