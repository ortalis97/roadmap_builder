/**
 * SSE Client for streaming roadmap creation progress.
 */

import { auth } from './firebase';

export interface SSEEvent {
  event: string;
  data: unknown;
}

export interface SSEConnection {
  close: () => void;
}

/**
 * Create an SSE connection for a POST request with JSON body.
 * This is needed because the browser's EventSource API only supports GET.
 */
export async function createSSEConnection(
  url: string,
  body: Record<string, unknown>,
  onEvent: (event: SSEEvent) => void,
  onError: (error: Error) => void,
  onComplete?: () => void
): Promise<SSEConnection> {
  // Get Firebase token
  const user = auth.currentUser;
  if (!user) {
    throw new Error('Not authenticated');
  }
  const token = await user.getIdToken();

  // Create fetch request with SSE handling
  const controller = new AbortController();

  const processStream = async () => {
    try {
      const response = await fetch(url, {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
          Authorization: `Bearer ${token}`,
          Accept: 'text/event-stream',
        },
        body: JSON.stringify(body),
        signal: controller.signal,
      });

      if (!response.ok) {
        const errorText = await response.text();
        throw new Error(errorText || `HTTP ${response.status}`);
      }

      if (!response.body) {
        throw new Error('No response body');
      }

      const reader = response.body.getReader();
      const decoder = new TextDecoder();
      let buffer = '';

      while (true) {
        const { done, value } = await reader.read();

        if (done) {
          onComplete?.();
          break;
        }

        buffer += decoder.decode(value, { stream: true });

        // Parse SSE events from buffer
        const lines = buffer.split('\n');
        buffer = lines.pop() || ''; // Keep incomplete line in buffer

        let currentEvent = '';
        let currentData = '';

        for (const line of lines) {
          if (line.startsWith('event:')) {
            currentEvent = line.slice(6).trim();
          } else if (line.startsWith('data:')) {
            currentData = line.slice(5).trim();
          } else if (line === '' && currentEvent && currentData) {
            // Empty line signals end of event
            try {
              const data = JSON.parse(currentData);
              onEvent({ event: currentEvent, data });
            } catch {
              // If not JSON, pass raw string
              onEvent({ event: currentEvent, data: currentData });
            }
            currentEvent = '';
            currentData = '';
          }
        }
      }
    } catch (error) {
      if (error instanceof Error && error.name === 'AbortError') {
        // Connection was closed intentionally
        return;
      }
      onError(error instanceof Error ? error : new Error(String(error)));
    }
  };

  // Start processing in background
  processStream();

  return {
    close: () => {
      controller.abort();
    },
  };
}
