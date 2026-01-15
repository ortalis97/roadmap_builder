import { ChatInterface } from './ChatInterface';

interface ChatSidebarProps {
  onToggle: () => void;
  roadmapId: string;
  sessionId?: string;
  width: number;
  onWidthChange: (width: number) => void;
}

const MIN_WIDTH = 280;
const MAX_WIDTH = 600;

export function ChatSidebar({
  onToggle,
  roadmapId,
  sessionId,
  width,
  onWidthChange,
}: ChatSidebarProps) {
  const handleMouseDown = (e: React.MouseEvent) => {
    e.preventDefault();
    const startX = e.clientX;
    const startWidth = width;

    const handleMouseMove = (moveEvent: MouseEvent) => {
      const delta = startX - moveEvent.clientX;
      const newWidth = Math.min(MAX_WIDTH, Math.max(MIN_WIDTH, startWidth + delta));
      onWidthChange(newWidth);
    };

    const handleMouseUp = () => {
      document.removeEventListener('mousemove', handleMouseMove);
      document.removeEventListener('mouseup', handleMouseUp);
    };

    document.addEventListener('mousemove', handleMouseMove);
    document.addEventListener('mouseup', handleMouseUp);
  };

  return (
    <div
      style={{ width: `${width}px` }}
      className="h-full bg-white border-l border-gray-200 flex flex-col flex-shrink-0"
    >
      {/* Resize handle */}
      <div
        className="absolute left-0 top-0 h-full w-1 cursor-ew-resize hover:bg-blue-400 active:bg-blue-500 transition-colors"
        onMouseDown={handleMouseDown}
      />

      {/* Sidebar header */}
      <div className="flex items-center justify-between px-4 py-3 border-b border-gray-200 bg-gray-50 flex-shrink-0">
        <div className="flex items-center gap-2">
          <svg
            className="w-5 h-5 text-blue-600"
            fill="none"
            stroke="currentColor"
            viewBox="0 0 24 24"
          >
            <path
              strokeLinecap="round"
              strokeLinejoin="round"
              strokeWidth={2}
              d="M8 12h.01M12 12h.01M16 12h.01M21 12c0 4.418-4.03 8-9 8a9.863 9.863 0 01-4.255-.949L3 20l1.395-3.72C3.512 15.042 3 13.574 3 12c0-4.418 4.03-8 9-8s9 3.582 9 8z"
            />
          </svg>
          <span className="font-medium text-gray-900">AI Learning Assistant</span>
        </div>
        <button
          onClick={onToggle}
          className="p-1 text-gray-500 hover:text-gray-700 rounded"
          aria-label="Close chat"
        >
          <svg
            className="w-5 h-5"
            fill="none"
            stroke="currentColor"
            viewBox="0 0 24 24"
          >
            <path
              strokeLinecap="round"
              strokeLinejoin="round"
              strokeWidth={2}
              d="M6 18L18 6M6 6l12 12"
            />
          </svg>
        </button>
      </div>

      {/* Sidebar content */}
      <div className="flex-1 overflow-hidden">
        {sessionId ? (
          <ChatInterface roadmapId={roadmapId} sessionId={sessionId} />
        ) : (
          <div className="flex flex-col items-center justify-center h-full text-gray-500 p-6 text-center">
            <svg
              className="w-16 h-16 mb-4 text-gray-300"
              fill="none"
              stroke="currentColor"
              viewBox="0 0 24 24"
            >
              <path
                strokeLinecap="round"
                strokeLinejoin="round"
                strokeWidth={1.5}
                d="M8 10h.01M12 10h.01M16 10h.01M9 16H5a2 2 0 01-2-2V6a2 2 0 012-2h14a2 2 0 012 2v8a2 2 0 01-2 2h-5l-5 5v-5z"
              />
            </svg>
            <h3 className="text-lg font-medium text-gray-900 mb-2">
              Select a Session
            </h3>
            <p className="text-sm">
              Click on a session from the roadmap to start chatting with the
              AI assistant about that topic.
            </p>
          </div>
        )}
      </div>
    </div>
  );
}
