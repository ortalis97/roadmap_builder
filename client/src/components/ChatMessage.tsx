import { useMemo } from 'react';
import type { ChatMessage as ChatMessageType } from '../types';

interface ChatMessageProps {
  message: ChatMessageType;
}

export function ChatMessage({ message }: ChatMessageProps) {
  const isUser = message.role === 'user';

  const formattedTime = useMemo(() => {
    const date = new Date(message.timestamp);
    return date.toLocaleTimeString(undefined, {
      hour: '2-digit',
      minute: '2-digit',
    });
  }, [message.timestamp]);

  return (
    <div className={`flex ${isUser ? 'justify-end' : 'justify-start'} mb-4`}>
      <div
        className={`max-w-[80%] px-4 py-3 rounded-lg ${
          isUser
            ? 'bg-blue-600 text-white rounded-br-sm'
            : 'bg-gray-100 text-gray-900 rounded-bl-sm'
        }`}
      >
        <div className="text-sm whitespace-pre-wrap break-words" dir="auto">
          {message.content}
        </div>
        <div
          className={`text-xs mt-1 ${
            isUser ? 'text-blue-200' : 'text-gray-500'
          }`}
        >
          {formattedTime}
        </div>
      </div>
    </div>
  );
}
