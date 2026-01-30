import { useParams, Link, useNavigate } from 'react-router-dom';
import { useSession, useUpdateSession, useSessions } from '../hooks/useSessions';
import { useRoadmap } from '../hooks/useRoadmaps';
import { SessionStatusIcon, getNextStatus } from '../components/SessionStatusIcon';
import { NotesEditor } from '../components/NotesEditor';
import { MarkdownContent } from '../components/MarkdownContent';
import { VideoSection } from '../components/VideoSection';
import type { SessionStatus } from '../types';
import { useCallback, useEffect, useMemo } from 'react';
import { getLanguageDirection } from '../utils/language';

export function SessionDetailPage() {
  const { roadmapId, sessionId } = useParams<{ roadmapId: string; sessionId: string }>();
  const navigate = useNavigate();

  const { data: session, isLoading, error } = useSession(roadmapId!, sessionId!);
  const { data: roadmap } = useRoadmap(roadmapId!);
  const { data: allSessions } = useSessions(roadmapId!);
  const { mutate: updateSession, isPending } = useUpdateSession(roadmapId!, sessionId!);

  const direction = roadmap ? getLanguageDirection(roadmap.language) : 'ltr';

  const { prevSession, nextSession } = useMemo(() => {
    if (!allSessions || !session) return { prevSession: null, nextSession: null };

    const sorted = [...allSessions].sort((a, b) => a.order - b.order);
    const currentIndex = sorted.findIndex((s) => s.id === sessionId);

    return {
      prevSession: currentIndex > 0 ? sorted[currentIndex - 1] : null,
      nextSession: currentIndex < sorted.length - 1 ? sorted[currentIndex + 1] : null,
    };
  }, [allSessions, session, sessionId]);

  const handleStatusToggle = () => {
    if (session) {
      updateSession({ status: getNextStatus(session.status) });
    }
  };

  const handleStatusChange = (status: SessionStatus) => {
    updateSession({ status });
  };

  const handleNotesSave = useCallback((notes: string) => {
    updateSession({ notes });
  }, [updateSession]);

  // Auto-set to "in_progress" when entering a "not_started" session
  useEffect(() => {
    if (session && session.status === 'not_started' && !isPending) {
      updateSession({ status: 'in_progress' });
    }
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [session?.id]); // Only run when session ID changes

  // Mark current session as done and navigate to next session
  const handleNextSession = () => {
    if (nextSession) {
      // Mark current session as done if it's in_progress
      if (session && session.status === 'in_progress') {
        updateSession({ status: 'done' });
      }
      navigate(`/roadmaps/${roadmapId}/sessions/${nextSession.id}`);
    }
  };

  if (isLoading) {
    return (
      <div className="flex items-center justify-center py-12">
        <div className="animate-spin rounded-full h-8 w-8 border-b-2 border-blue-600"></div>
      </div>
    );
  }

  if (error) {
    return (
      <div className="bg-red-50 text-red-700 p-4 rounded-md">
        Failed to load session: {error.message}
      </div>
    );
  }

  if (!session) {
    return (
      <div className="text-center py-12">
        <h2 className="text-xl font-medium text-gray-900">Session not found</h2>
        <Link to={`/roadmaps/${roadmapId}`} className="mt-4 text-blue-600 hover:text-blue-800">
          Back to Roadmap
        </Link>
      </div>
    );
  }

  return (
    <div className="max-w-4xl mx-auto">
      <div className="mb-6">
        <Link
          to={`/roadmaps/${roadmapId}`}
          className="text-blue-600 hover:text-blue-800 text-sm flex items-center gap-1 py-2 min-h-[44px] md:min-h-0 md:py-0"
        >
          <svg className="w-5 h-5 md:w-4 md:h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
            <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M15 19l-7-7 7-7" />
          </svg>
          Back to Roadmap
        </Link>
      </div>

      <div className="bg-white rounded-lg shadow">
        <div className="p-6 border-b border-gray-200">
          <div className="flex items-start gap-4">
            <SessionStatusIcon status={session.status} onClick={handleStatusToggle} />
            <div className="flex-1">
              <h1 className="text-2xl font-bold text-gray-900" dir={direction}>
                {session.title}
              </h1>
              <p className="mt-1 text-sm text-gray-500">
                Session {session.order} of {allSessions?.length || '?'}
              </p>
            </div>
          </div>

          <div className="mt-4 flex items-center gap-2">
            <span className="text-sm text-gray-500">Status:</span>
            <select
              value={session.status}
              onChange={(e) => handleStatusChange(e.target.value as SessionStatus)}
              className="text-sm border-gray-300 rounded-md focus:ring-blue-500 focus:border-blue-500 py-2 min-h-[44px] md:min-h-0 md:py-1"
            >
              <option value="not_started">Not Started</option>
              <option value="in_progress">In Progress</option>
              <option value="done">Done</option>
              <option value="skipped">Skipped</option>
            </select>
          </div>
        </div>

        <div className="p-6 border-b border-gray-200">
          <MarkdownContent content={session.content} direction={direction} />
        </div>

        {session.videos && session.videos.length > 0 && (
          <div className="p-6 border-b border-gray-200">
            <VideoSection videos={session.videos} />
          </div>
        )}

        <div className="p-6">
          <NotesEditor
            initialNotes={session.notes}
            onSave={handleNotesSave}
            isSaving={isPending}
          />
        </div>
      </div>

      <div className="mt-6 flex justify-between">
        {prevSession ? (
          <button
            onClick={() => navigate(`/roadmaps/${roadmapId}/sessions/${prevSession.id}`)}
            className="flex items-center gap-2 px-4 py-3 md:py-2 min-h-[44px] md:min-h-0 text-gray-700 hover:bg-gray-100 rounded-md"
          >
            <svg className="w-5 h-5 md:w-4 md:h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
              <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M15 19l-7-7 7-7" />
            </svg>
            <span className="text-sm md:text-sm">{prevSession.title}</span>
          </button>
        ) : (
          <div />
        )}

        {nextSession ? (
          <button
            onClick={handleNextSession}
            className="flex items-center gap-2 px-4 py-3 md:py-2 min-h-[44px] md:min-h-0 text-gray-700 hover:bg-gray-100 rounded-md"
          >
            <span className="text-sm md:text-sm">{nextSession.title}</span>
            <svg className="w-5 h-5 md:w-4 md:h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
              <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M9 5l7 7-7 7" />
            </svg>
          </button>
        ) : (
          <div />
        )}
      </div>
    </div>
  );
}
