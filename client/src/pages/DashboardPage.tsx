import { useState } from 'react';
import { Link } from 'react-router-dom';
import { useRoadmaps } from '../hooks/useRoadmaps';
import { useRoadmapProgress } from '../hooks/useSessions';
import { ProgressBar } from '../components/ProgressBar';
import type { RoadmapListItem } from '../types';

function RoadmapCard({ roadmap }: { roadmap: RoadmapListItem }) {
  const { data: progress } = useRoadmapProgress(roadmap.id);

  return (
    <Link
      to={`/roadmaps/${roadmap.id}`}
      className="block p-6 bg-white rounded-lg shadow hover:shadow-md transition-shadow"
    >
      <h3 className="text-lg font-medium text-gray-900">
        {roadmap.title}
      </h3>
      <div className="mt-2 flex items-center gap-4 text-sm text-gray-500">
        <span>{roadmap.session_count} sessions</span>
        <span>
          {new Date(roadmap.created_at).toLocaleDateString()}
        </span>
      </div>
      {progress && progress.total > 0 && (
        <div className="mt-3">
          <ProgressBar percentage={progress.percentage} size="sm" />
        </div>
      )}
    </Link>
  );
}

export function DashboardPage() {
  const { data: roadmaps, isLoading, error } = useRoadmaps();
  const [searchQuery, setSearchQuery] = useState('');

  // Filter roadmaps by search query
  const filteredRoadmaps = roadmaps?.filter(r =>
    r.title.toLowerCase().includes(searchQuery.toLowerCase())
  ) ?? [];

  if (isLoading) {
    return (
      <div className="flex items-center justify-center py-12">
        <div className="animate-spin rounded-full h-8 w-8 border-b-2 border-blue-600"></div>
      </div>
    );
  }

  if (error) {
    return (
      <div className="bg-red-50 text-red-700 p-4 rounded-md">
        Failed to load roadmaps: {error.message}
      </div>
    );
  }

  return (
    <div className="space-y-6">
      <div className="flex justify-between items-center">
        <h1 className="text-2xl font-bold text-gray-900">My Roadmaps</h1>
        <Link
          to="/create"
          className="px-4 py-3 md:py-2 min-h-[44px] md:min-h-0 bg-blue-600 text-white rounded-md hover:bg-blue-700 focus:outline-none focus:ring-2 focus:ring-offset-2 focus:ring-blue-500"
        >
          Create New Roadmap
        </Link>
      </div>

      {roadmaps && roadmaps.length === 0 ? (
        <div className="text-center py-12 bg-white rounded-lg shadow">
          <h3 className="text-lg font-medium text-gray-900">No roadmaps yet</h3>
          <p className="mt-2 text-gray-500">
            Create your first learning roadmap to get started.
          </p>
          <Link
            to="/create"
            className="mt-4 inline-block px-4 py-3 md:py-2 min-h-[44px] md:min-h-0 bg-blue-600 text-white rounded-md hover:bg-blue-700"
          >
            Create Roadmap
          </Link>
        </div>
      ) : (
        <>
          {roadmaps && roadmaps.length >= 3 && (
            <div className="relative">
              <input
                type="text"
                placeholder="Search roadmaps..."
                value={searchQuery}
                onChange={(e) => setSearchQuery(e.target.value)}
                className="w-full px-4 py-2 border border-gray-300 rounded-md focus:ring-2 focus:ring-blue-500 focus:border-blue-500"
              />
              {searchQuery && (
                <button
                  onClick={() => setSearchQuery('')}
                  className="absolute right-3 top-1/2 -translate-y-1/2 text-gray-400 hover:text-gray-600"
                  aria-label="Clear search"
                >
                  ✕
                </button>
              )}
            </div>
          )}

          {filteredRoadmaps.length === 0 && searchQuery ? (
            <div className="text-center py-12 bg-white rounded-lg shadow">
              <h3 className="text-lg font-medium text-gray-900">No roadmaps match your search</h3>
              <p className="mt-2 text-gray-500">
                Try a different search term.
              </p>
            </div>
          ) : (
            <div className="grid gap-4 md:grid-cols-2 lg:grid-cols-3">
              {filteredRoadmaps.map((roadmap) => (
                <RoadmapCard key={roadmap.id} roadmap={roadmap} />
              ))}
            </div>
          )}
        </>
      )}
    </div>
  );
}
