import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query';
import {
  fetchRoadmaps,
  fetchRoadmap,
  deleteRoadmap,
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

export function useDeleteRoadmap() {
  const queryClient = useQueryClient();

  return useMutation({
    mutationFn: deleteRoadmap,
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['roadmaps'] });
    },
  });
}
