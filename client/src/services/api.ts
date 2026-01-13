import { auth } from './firebase';
import type {
  Draft,
  Roadmap,
  RoadmapListItem,
  Session,
  SessionSummaryWithStatus,
  SessionUpdate,
  RoadmapProgress,
  ChatHistory,
  ChatRequest,
  ChatResponse,
} from '../types';

const API_BASE_URL = import.meta.env.VITE_API_BASE_URL || 'http://localhost:8000';

async function request<T>(
  endpoint: string,
  options: RequestInit = {}
): Promise<T> {
  const token = await auth.currentUser?.getIdToken();

  const response = await fetch(`${API_BASE_URL}${endpoint}`, {
    ...options,
    headers: {
      'Content-Type': 'application/json',
      ...(token && { Authorization: `Bearer ${token}` }),
      ...options.headers,
    },
  });

  if (!response.ok) {
    const error = await response.json().catch(() => ({}));
    throw new Error(error.detail || `Request failed: ${response.status}`);
  }

  if (response.status === 204) {
    return null as T;
  }

  return response.json();
}

// Draft API
export async function createDraft(rawText: string): Promise<Draft> {
  return request<Draft>('/api/v1/drafts/', {
    method: 'POST',
    body: JSON.stringify({ raw_text: rawText }),
  });
}

export async function fetchDraft(draftId: string): Promise<Draft> {
  return request<Draft>(`/api/v1/drafts/${draftId}`);
}

// Roadmap API
export async function fetchRoadmaps(): Promise<RoadmapListItem[]> {
  return request<RoadmapListItem[]>('/api/v1/roadmaps/');
}

export async function fetchRoadmap(roadmapId: string): Promise<Roadmap> {
  return request<Roadmap>(`/api/v1/roadmaps/${roadmapId}`);
}

export async function createRoadmap(
  draftId: string,
  title: string
): Promise<Roadmap> {
  return request<Roadmap>('/api/v1/roadmaps/', {
    method: 'POST',
    body: JSON.stringify({ draft_id: draftId, title }),
  });
}

export async function deleteRoadmap(roadmapId: string): Promise<void> {
  return request<void>(`/api/v1/roadmaps/${roadmapId}`, {
    method: 'DELETE',
  });
}

// Session API
export async function fetchSessions(roadmapId: string): Promise<SessionSummaryWithStatus[]> {
  return request<SessionSummaryWithStatus[]>(`/api/v1/roadmaps/${roadmapId}/sessions`);
}

export async function fetchSession(roadmapId: string, sessionId: string): Promise<Session> {
  return request<Session>(`/api/v1/roadmaps/${roadmapId}/sessions/${sessionId}`);
}

export async function updateSession(
  roadmapId: string,
  sessionId: string,
  data: SessionUpdate
): Promise<Session> {
  return request<Session>(`/api/v1/roadmaps/${roadmapId}/sessions/${sessionId}`, {
    method: 'PATCH',
    body: JSON.stringify(data),
  });
}

export async function fetchRoadmapProgress(roadmapId: string): Promise<RoadmapProgress> {
  return request<RoadmapProgress>(`/api/v1/roadmaps/${roadmapId}/progress`);
}

// Chat API
export async function sendChatMessage(data: ChatRequest): Promise<ChatResponse> {
  return request<ChatResponse>('/api/v1/chat/', {
    method: 'POST',
    body: JSON.stringify(data),
  });
}

export async function fetchChatHistory(
  roadmapId: string,
  sessionId: string
): Promise<ChatHistory | null> {
  return request<ChatHistory | null>(
    `/api/v1/chat/roadmaps/${roadmapId}/sessions/${sessionId}`
  );
}

export async function clearChatHistory(
  roadmapId: string,
  sessionId: string
): Promise<void> {
  return request<void>(
    `/api/v1/chat/roadmaps/${roadmapId}/sessions/${sessionId}`,
    { method: 'DELETE' }
  );
}
