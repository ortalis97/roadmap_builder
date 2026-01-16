export interface Draft {
  id: string;
  user_id: string;
  raw_text: string;
  created_at: string;
}

export interface SessionSummary {
  id: string;
  title: string;
  order: number;
}

export type SessionStatus = 'not_started' | 'in_progress' | 'done' | 'skipped';

export interface SessionSummaryWithStatus {
  id: string;
  title: string;
  order: number;
  status: SessionStatus;
}

export interface Session {
  id: string;
  roadmap_id: string;
  order: number;
  title: string;
  content: string;
  status: SessionStatus;
  notes: string;
  created_at: string;
  updated_at: string;
}

export interface SessionUpdate {
  status?: SessionStatus;
  notes?: string;
}

export interface RoadmapProgress {
  total: number;
  done: number;
  in_progress: number;
  skipped: number;
  not_started: number;
  percentage: number;
}

export interface RoadmapListItem {
  id: string;
  title: string;
  session_count: number;
  created_at: string;
}

export interface Roadmap {
  id: string;
  draft_id: string;
  title: string;
  summary: string | null;
  sessions: SessionSummary[];
  created_at: string;
  updated_at: string;
}

export interface User {
  id: string;
  firebase_uid: string;
  email: string;
  name: string;
  picture: string | null;
}

// Chat types
export interface ChatMessage {
  role: 'user' | 'assistant';
  content: string;
  timestamp: string;
}

export interface ChatHistory {
  conversation_id: string;
  messages: ChatMessage[];
  created_at: string;
  updated_at: string;
}

export interface ChatRequest {
  session_id: string;
  roadmap_id: string;
  message: string;
  conversation_id?: string;
}

export interface ChatResponse {
  conversation_id: string;
  user_message: ChatMessage;
  assistant_message: ChatMessage;
}

// Roadmap creation types
export interface ExampleOption {
  label: string;
  text: string;
}

export interface InterviewQuestion {
  id: string;
  question: string;
  purpose: string;
  example_options: ExampleOption[];
  allows_freeform: boolean;
}

export interface InterviewAnswer {
  question_id: string;
  answer: string;
}

export interface StartCreationResponse {
  pipeline_id: string;
  questions: InterviewQuestion[];
}

export interface ValidationIssue {
  id: string;
  issue_type: 'overlap' | 'gap' | 'ordering' | 'coherence' | 'depth';
  severity: 'low' | 'medium' | 'high';
  description: string;
  suggested_fix: string;
}

export interface ValidationResult {
  is_valid: boolean;
  issues: ValidationIssue[];
  score: number;
  summary: string;
}

export type CreationStage =
  | 'idle'
  | 'starting'
  | 'interviewing'
  | 'architecting'
  | 'researching'
  | 'validating'
  | 'user_review'
  | 'saving'
  | 'complete'
  | 'error';

export interface CreationProgress {
  stage: CreationStage;
  message: string;
  current_session?: number;
  total_sessions?: number;
  session_title?: string;
}

export interface SSEStageUpdateData {
  stage: string;
  message: string;
}

export interface SSESessionProgressData {
  current: number;
  total: number;
  session_title: string;
}

export interface SSECompleteData {
  roadmap_id: string;
  message: string;
}

export interface SSEErrorData {
  message: string;
}
