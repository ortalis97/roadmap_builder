import { useState } from 'react';
import { Outlet, Link, useParams } from 'react-router-dom';
import { useAuth } from '../../context/AuthContext';
import { ChatSidebar } from '../ChatSidebar';

const MIN_WIDTH = 280;

export function Layout() {
  const { user, signOut } = useAuth();
  const params = useParams<{ id?: string; roadmapId?: string; sessionId?: string }>();
  const [sidebarOpen, setSidebarOpen] = useState(true);
  const [sidebarWidth, setSidebarWidth] = useState(384);

  // Handle both route patterns: /roadmaps/:id and /roadmaps/:roadmapId/sessions/:sessionId
  const roadmapId = params.roadmapId || params.id;
  const sessionId = params.sessionId;

  // Handle drag-to-expand from collapsed rail
  const handleCollapsedRailMouseDown = (e: React.MouseEvent) => {
    e.preventDefault();
    const startX = e.clientX;

    const handleMouseMove = (moveEvent: MouseEvent) => {
      const delta = startX - moveEvent.clientX;
      if (delta > 20) {
        // Start expanding when dragged enough
        setSidebarOpen(true);
        setSidebarWidth(Math.max(MIN_WIDTH, delta));
      }
    };

    const handleMouseUp = () => {
      document.removeEventListener('mousemove', handleMouseMove);
      document.removeEventListener('mouseup', handleMouseUp);
    };

    document.addEventListener('mousemove', handleMouseMove);
    document.addEventListener('mouseup', handleMouseUp);
  };

  return (
    <div className="h-screen bg-gray-50 flex flex-col">
      <header className="bg-white shadow-sm flex-shrink-0">
        <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
          <div className="flex justify-between items-center h-16">
            <Link to="/" className="text-xl font-semibold text-gray-900">
              Learning Roadmap
            </Link>

            <div className="flex items-center gap-4">
              {user && (
                <>
                  <span className="text-sm text-gray-600">{user.email}</span>
                  {user.photoURL && (
                    <img
                      src={user.photoURL}
                      alt="Profile"
                      className="w-8 h-8 rounded-full"
                    />
                  )}
                  <button
                    onClick={() => signOut()}
                    className="text-sm text-gray-600 hover:text-gray-900"
                  >
                    Sign out
                  </button>
                </>
              )}
            </div>
          </div>
        </div>
      </header>

      <div className="flex flex-1 overflow-hidden">
        <main className="flex-1 overflow-auto px-4 sm:px-6 lg:px-8 py-8">
          <div className="max-w-7xl mx-auto">
            <Outlet />
          </div>
        </main>

        {/* Chat Sidebar - only show on roadmap/session pages */}
        {roadmapId && sidebarOpen && (
          <ChatSidebar
            onToggle={() => setSidebarOpen(false)}
            roadmapId={roadmapId}
            sessionId={sessionId}
            width={sidebarWidth}
            onWidthChange={setSidebarWidth}
          />
        )}

        {/* Collapsed rail when sidebar is closed */}
        {roadmapId && !sidebarOpen && (
          <div
            className="w-2 bg-gray-200 hover:bg-blue-400 cursor-ew-resize transition-colors flex-shrink-0"
            onClick={() => setSidebarOpen(true)}
            onMouseDown={handleCollapsedRailMouseDown}
            title="Click or drag to open AI Assistant"
          />
        )}
      </div>
    </div>
  );
}
