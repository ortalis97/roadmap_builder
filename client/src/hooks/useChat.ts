import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query';
import { useState, useCallback, useEffect } from 'react';
import {
  fetchChatHistory,
  sendChatMessage,
  clearChatHistory,
} from '../services/api';
import type { ChatMessage, ChatHistory } from '../types';

export function useChatHistory(roadmapId: string, sessionId: string) {
  return useQuery({
    queryKey: ['chat', roadmapId, sessionId],
    queryFn: () => fetchChatHistory(roadmapId, sessionId),
    enabled: !!roadmapId && !!sessionId,
  });
}

export function useChat(roadmapId: string, sessionId: string) {
  const queryClient = useQueryClient();
  const [conversationId, setConversationId] = useState<string | null>(null);

  // Load existing chat history
  const { data: chatHistory, isLoading: isLoadingHistory } = useChatHistory(
    roadmapId,
    sessionId
  );

  // Set conversation ID from loaded history
  useEffect(() => {
    if (chatHistory?.conversation_id && !conversationId) {
      setConversationId(chatHistory.conversation_id);
    }
  }, [chatHistory, conversationId]);

  // Send message mutation
  const sendMessageMutation = useMutation({
    mutationFn: (message: string) =>
      sendChatMessage({
        session_id: sessionId,
        roadmap_id: roadmapId,
        message,
        conversation_id: conversationId ?? undefined,
      }),
    onSuccess: (response) => {
      // Update conversation ID for new conversations
      if (!conversationId) {
        setConversationId(response.conversation_id);
      }

      // Optimistically update the cache with new messages
      queryClient.setQueryData(
        ['chat', roadmapId, sessionId],
        (old: ChatHistory | null | undefined): ChatHistory => {
          const existingMessages = old?.messages || [];
          return {
            conversation_id: response.conversation_id,
            messages: [
              ...existingMessages,
              response.user_message,
              response.assistant_message,
            ],
            created_at: old?.created_at || new Date().toISOString(),
            updated_at: new Date().toISOString(),
          };
        }
      );
    },
  });

  // Clear history mutation
  const clearHistoryMutation = useMutation({
    mutationFn: () => clearChatHistory(roadmapId, sessionId),
    onSuccess: () => {
      setConversationId(null);
      queryClient.setQueryData(['chat', roadmapId, sessionId], null);
    },
  });

  const sendMessage = useCallback(
    (message: string) => {
      if (message.trim()) {
        sendMessageMutation.mutate(message);
      }
    },
    [sendMessageMutation]
  );

  const clearHistory = useCallback(() => {
    clearHistoryMutation.mutate();
  }, [clearHistoryMutation]);

  // Get messages from query cache or return empty array
  const messages: ChatMessage[] = chatHistory?.messages || [];

  return {
    messages,
    conversationId,
    isLoadingHistory,
    isSending: sendMessageMutation.isPending,
    isClearing: clearHistoryMutation.isPending,
    sendMessage,
    clearHistory,
    error: sendMessageMutation.error,
  };
}
