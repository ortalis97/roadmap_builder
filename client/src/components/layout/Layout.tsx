import { useState } from 'react';
import { Outlet, Link, useParams } from 'react-router-dom';
import { useAuth } from '../../context/AuthContext';
import { ChatSidebar } from '../ChatSidebar';
import { MobileNav, HamburgerButton } from './MobileNav';
import { useIsMobile } from '../../hooks/useMediaQuery';

const MIN_WIDTH = 280;

export function Layout() {
  const { user, signOut } = useAuth();
  const params = useParams<{ id?: string; roadmapId?: string; sessionId?: string }>();
  const [sidebarOpen, setSidebarOpen] = useState(true);
  const [sidebarWidth, setSidebarWidth] = useState(384);
  const [mobileNavOpen, setMobileNavOpen] = useState(false);
  const [mobileChatOpen, setMobileChatOpen] = useState(false);
  const isMobile = useIsMobile();

  // Handle both route patterns: /roadmaps/:id and /roadmaps/:roadmapId/sessions/:sessionId
  const roadmapId = params.roadmapId || params.id;
  const sessionId = params.sessionId;

  // Handle drag-to-expand from collapsed rail (desktop only)
  const handleCollapsedRailMouseDown = (e: React.MouseEvent) => {
    if (isMobile) return;
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
            <div className="flex items-center gap-2">
              {/* Hamburger menu on mobile */}
              <HamburgerButton onClick={() => setMobileNavOpen(true)} />

              <Link to="/" className="text-xl font-semibold text-gray-900">
                Learning Roadmap
              </Link>
            </div>

            {/* Desktop user info and sign out */}
            <div className="hidden md:flex items-center gap-4">
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

            {/* Mobile profile picture only */}
            <div className="flex md:hidden items-center">
              {user?.photoURL && (
                <img
                  src={user.photoURL}
                  alt="Profile"
                  className="w-8 h-8 rounded-full"
                />
              )}
            </div>
          </div>
        </div>
      </header>

      {/* Mobile Navigation Drawer */}
      <MobileNav isOpen={mobileNavOpen} onClose={() => setMobileNavOpen(false)} />

      <div className="flex flex-1 overflow-hidden">
        <main className="flex-1 overflow-auto px-4 sm:px-6 lg:px-8 py-8">
          <div className="max-w-7xl mx-auto">
            <Outlet />
          </div>
        </main>

        {/* Desktop Chat Sidebar - only show on roadmap/session pages */}
        {!isMobile && roadmapId && sidebarOpen && (
          <ChatSidebar
            onToggle={() => setSidebarOpen(false)}
            roadmapId={roadmapId}
            sessionId={sessionId}
            width={sidebarWidth}
            onWidthChange={setSidebarWidth}
          />
        )}

        {/* Collapsed rail when sidebar is closed (desktop only) */}
        {!isMobile && roadmapId && !sidebarOpen && (
          <div
            className="w-2 bg-gray-200 hover:bg-blue-400 cursor-ew-resize transition-colors flex-shrink-0"
            onClick={() => setSidebarOpen(true)}
            onMouseDown={handleCollapsedRailMouseDown}
            title="Click or drag to open AI Assistant"
          />
        )}
      </div>

      {/* Mobile Chat FAB - only show on roadmap/session pages */}
      {isMobile && roadmapId && !mobileChatOpen && (
        <button
          onClick={() => setMobileChatOpen(true)}
          className="fixed bottom-6 right-6 w-14 h-14 bg-blue-600 text-white rounded-full shadow-lg flex items-center justify-center hover:bg-blue-700 active:bg-blue-800 z-30"
          aria-label="Open AI Assistant"
        >
          <svg className="w-6 h-6" fill="none" stroke="currentColor" viewBox="0 0 24 24">
            <path
              strokeLinecap="round"
              strokeLinejoin="round"
              strokeWidth={2}
              d="M8 12h.01M12 12h.01M16 12h.01M21 12c0 4.418-4.03 8-9 8a9.863 9.863 0 01-4.255-.949L3 20l1.395-3.72C3.512 15.042 3 13.574 3 12c0-4.418 4.03-8 9-8s9 3.582 9 8z"
            />
          </svg>
        </button>
      )}

      {/* Mobile Chat Drawer */}
      {isMobile && roadmapId && mobileChatOpen && (
        <div className="fixed inset-0 z-50 flex flex-col bg-white">
          {/* Mobile chat header */}
          <div className="flex items-center justify-between p-4 border-b bg-white">
            <h2 className="text-lg font-semibold text-gray-900">AI Assistant</h2>
            <button
              onClick={() => setMobileChatOpen(false)}
              className="p-2 min-h-[44px] min-w-[44px] flex items-center justify-center rounded-md hover:bg-gray-100"
              aria-label="Close chat"
            >
              <svg className="w-6 h-6 text-gray-600" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M6 18L18 6M6 6l12 12" />
              </svg>
            </button>
          </div>

          {/* Chat content */}
          <div className="flex-1 overflow-hidden">
            <ChatSidebar
              onToggle={() => setMobileChatOpen(false)}
              roadmapId={roadmapId}
              sessionId={sessionId}
              width={undefined}
              onWidthChange={() => {}}
              isMobileFullscreen
            />
          </div>
        </div>
      )}
    </div>
  );
}
