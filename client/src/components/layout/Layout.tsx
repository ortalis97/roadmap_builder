import { useState } from 'react';
import { Outlet, Link, useParams } from 'react-router-dom';
import { useAuth } from '../../context/AuthContext';
import { ChatSidebar } from '../ChatSidebar';

export function Layout() {
  const { user, signOut } = useAuth();
  const params = useParams<{ id?: string; roadmapId?: string; sessionId?: string }>();
  const [sidebarOpen, setSidebarOpen] = useState(false);

  // Handle both route patterns: /roadmaps/:id and /roadmaps/:roadmapId/sessions/:sessionId
  const roadmapId = params.roadmapId || params.id;
  const sessionId = params.sessionId;

  return (
    <div className="min-h-screen bg-gray-50">
      <header className="bg-white shadow-sm">
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

      <main className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-8">
        <Outlet />
      </main>

      {/* Chat Sidebar - only show on roadmap/session pages */}
      {roadmapId && (
        <ChatSidebar
          isOpen={sidebarOpen}
          onToggle={() => setSidebarOpen(!sidebarOpen)}
          roadmapId={roadmapId}
          sessionId={sessionId}
        />
      )}
    </div>
  );
}
