import { useState } from 'react';
import { useParams, Link, useNavigate } from 'react-router-dom';
import { useRoadmap, useDeleteRoadmap } from '../hooks/useRoadmaps';

export function RoadmapDetailPage() {
  const { id } = useParams<{ id: string }>();
  const navigate = useNavigate();
  const { data: roadmap, isLoading, error } = useRoadmap(id!);
  const { mutate: deleteRoadmap, isPending: isDeleting } = useDeleteRoadmap();
  const [showDeleteConfirm, setShowDeleteConfirm] = useState(false);

  const handleDelete = () => {
    deleteRoadmap(id!, {
      onSuccess: () => {
        navigate('/');
      },
    });
  };

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
        Failed to load roadmap: {error.message}
      </div>
    );
  }

  if (!roadmap) {
    return (
      <div className="text-center py-12">
        <h2 className="text-xl font-medium text-gray-900">Roadmap not found</h2>
        <Link to="/" className="mt-4 text-blue-600 hover:text-blue-800">
          Back to Dashboard
        </Link>
      </div>
    );
  }

  return (
    <div className="max-w-4xl mx-auto">
      <div className="mb-6">
        <Link
          to="/"
          className="text-blue-600 hover:text-blue-800 text-sm flex items-center gap-1"
        >
          <svg
            className="w-4 h-4"
            fill="none"
            stroke="currentColor"
            viewBox="0 0 24 24"
          >
            <path
              strokeLinecap="round"
              strokeLinejoin="round"
              strokeWidth={2}
              d="M15 19l-7-7 7-7"
            />
          </svg>
          Back to Dashboard
        </Link>
      </div>

      <div className="bg-white rounded-lg shadow">
        <div className="p-6 border-b border-gray-200">
          <div className="flex justify-between items-start">
            <div>
              <h1 className="text-2xl font-bold text-gray-900">
                {roadmap.title}
              </h1>
              <p className="mt-1 text-sm text-gray-500">
                Created {new Date(roadmap.created_at).toLocaleDateString()}
              </p>
            </div>
            <button
              onClick={() => setShowDeleteConfirm(true)}
              className="text-red-600 hover:text-red-800 text-sm"
            >
              Delete
            </button>
          </div>

          {roadmap.summary && (
            <p className="mt-4 text-gray-600">{roadmap.summary}</p>
          )}
        </div>

        <div className="p-6">
          {roadmap.sessions.length > 0 ? (
            <div className="space-y-4">
              <h2 className="text-lg font-medium text-gray-900">Sessions</h2>
              <div className="space-y-2">
                {roadmap.sessions.map((session) => (
                  <div
                    key={session.id}
                    className="p-4 border border-gray-200 rounded-md"
                  >
                    <span className="text-sm text-gray-500 mr-2">
                      #{session.order}
                    </span>
                    <span className="font-medium">{session.title}</span>
                  </div>
                ))}
              </div>
            </div>
          ) : (
            <div className="text-center py-8 text-gray-500">
              <p>No sessions yet.</p>
              <p className="text-sm mt-1">
                AI parsing of your draft into sessions is coming soon.
              </p>
            </div>
          )}
        </div>
      </div>

      {/* Delete Confirmation Modal */}
      {showDeleteConfirm && (
        <div className="fixed inset-0 bg-black bg-opacity-50 flex items-center justify-center z-50">
          <div className="bg-white rounded-lg p-6 max-w-sm w-full mx-4">
            <h3 className="text-lg font-medium text-gray-900">
              Delete Roadmap?
            </h3>
            <p className="mt-2 text-sm text-gray-500">
              Are you sure you want to delete "{roadmap.title}"? This action
              cannot be undone.
            </p>
            <div className="mt-4 flex gap-3 justify-end">
              <button
                onClick={() => setShowDeleteConfirm(false)}
                className="px-4 py-2 text-gray-700 hover:bg-gray-100 rounded-md"
                disabled={isDeleting}
              >
                Cancel
              </button>
              <button
                onClick={handleDelete}
                disabled={isDeleting}
                className="px-4 py-2 bg-red-600 text-white rounded-md hover:bg-red-700 disabled:opacity-50"
              >
                {isDeleting ? 'Deleting...' : 'Delete'}
              </button>
            </div>
          </div>
        </div>
      )}
    </div>
  );
}
