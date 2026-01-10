import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query';
import {
  fetchRoadmaps,
  fetchRoadmap,
  createRoadmap,
  deleteRoadmap,
  createDraft,
} from '../services/api';

export function useRoadmaps() {
  return useQuery({
    queryKey: ['roadmaps'],
    queryFn: fetchRoadmaps,
  });
}

export function useRoadmap(id: string) {
  return useQuery({
    queryKey: ['roadmaps', id],
    queryFn: () => fetchRoadmap(id),
    enabled: !!id,
  });
}

export function useCreateRoadmap() {
  const queryClient = useQueryClient();

  return useMutation({
    mutationFn: async ({
      rawText,
      title,
    }: {
      rawText: string;
      title: string;
    }) => {
      // First create the draft
      const draft = await createDraft(rawText);
      // Then create the roadmap
      return createRoadmap(draft.id, title);
    },
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['roadmaps'] });
    },
  });
}

export function useDeleteRoadmap() {
  const queryClient = useQueryClient();

  return useMutation({
    mutationFn: deleteRoadmap,
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['roadmaps'] });
    },
  });
}
