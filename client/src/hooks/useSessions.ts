import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query';
import {
  fetchSessions,
  fetchSession,
  updateSession,
  fetchRoadmapProgress,
} from '../services/api';
import type { SessionUpdate, SessionStatus, Session, SessionSummaryWithStatus } from '../types';

export function useSessions(roadmapId: string) {
  return useQuery({
    queryKey: ['roadmaps', roadmapId, 'sessions'],
    queryFn: () => fetchSessions(roadmapId),
    enabled: !!roadmapId,
  });
}

export function useSession(roadmapId: string, sessionId: string) {
  return useQuery({
    queryKey: ['sessions', roadmapId, sessionId],
    queryFn: () => fetchSession(roadmapId, sessionId),
    enabled: !!roadmapId && !!sessionId,
  });
}

export function useRoadmapProgress(roadmapId: string) {
  return useQuery({
    queryKey: ['roadmaps', roadmapId, 'progress'],
    queryFn: () => fetchRoadmapProgress(roadmapId),
    enabled: !!roadmapId,
  });
}

export function useUpdateSession(roadmapId: string, sessionId: string) {
  const queryClient = useQueryClient();

  return useMutation({
    mutationFn: (data: SessionUpdate) => updateSession(roadmapId, sessionId, data),
    onMutate: async (newData) => {
      await queryClient.cancelQueries({ queryKey: ['sessions', roadmapId, sessionId] });
      const previousSession = queryClient.getQueryData(['sessions', roadmapId, sessionId]);

      queryClient.setQueryData(['sessions', roadmapId, sessionId], (old: Session | undefined) => {
        if (!old) return old;
        return { ...old, ...newData };
      });

      return { previousSession };
    },
    onError: (_err, _newData, context) => {
      if (context?.previousSession) {
        queryClient.setQueryData(
          ['sessions', roadmapId, sessionId],
          context.previousSession
        );
      }
    },
    onSettled: () => {
      queryClient.invalidateQueries({ queryKey: ['sessions', roadmapId, sessionId] });
      queryClient.invalidateQueries({ queryKey: ['roadmaps', roadmapId, 'sessions'] });
      queryClient.invalidateQueries({ queryKey: ['roadmaps', roadmapId, 'progress'] });
    },
  });
}

export function useUpdateSessionStatus(roadmapId: string) {
  const queryClient = useQueryClient();

  return useMutation({
    mutationFn: ({ sessionId, status }: { sessionId: string; status: SessionStatus }) =>
      updateSession(roadmapId, sessionId, { status }),
    onMutate: async ({ sessionId, status }) => {
      await queryClient.cancelQueries({ queryKey: ['roadmaps', roadmapId, 'sessions'] });
      const previousSessions = queryClient.getQueryData(['roadmaps', roadmapId, 'sessions']);

      queryClient.setQueryData(['roadmaps', roadmapId, 'sessions'], (old: SessionSummaryWithStatus[] | undefined) => {
        if (!old) return old;
        return old.map((s: SessionSummaryWithStatus) =>
          s.id === sessionId ? { ...s, status } : s
        );
      });

      return { previousSessions };
    },
    onError: (_err, _variables, context) => {
      if (context?.previousSessions) {
        queryClient.setQueryData(
          ['roadmaps', roadmapId, 'sessions'],
          context.previousSessions
        );
      }
    },
    onSettled: () => {
      queryClient.invalidateQueries({ queryKey: ['roadmaps', roadmapId, 'sessions'] });
      queryClient.invalidateQueries({ queryKey: ['roadmaps', roadmapId, 'progress'] });
    },
  });
}
