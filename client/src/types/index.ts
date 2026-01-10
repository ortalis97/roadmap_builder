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
