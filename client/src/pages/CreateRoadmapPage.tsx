import { useState } from 'react';
import { useNavigate, Link } from 'react-router-dom';
import { useCreateRoadmap } from '../hooks/useRoadmaps';

export function CreateRoadmapPage() {
  const [title, setTitle] = useState('');
  const [rawText, setRawText] = useState('');
  const navigate = useNavigate();
  const { mutate: createRoadmap, isPending, error } = useCreateRoadmap();

  const handleSubmit = (e: React.FormEvent) => {
    e.preventDefault();

    if (!title.trim() || !rawText.trim()) {
      return;
    }

    createRoadmap(
      { title: title.trim(), rawText: rawText.trim() },
      {
        onSuccess: (roadmap) => {
          navigate(`/roadmaps/${roadmap.id}`);
        },
      }
    );
  };

  return (
    <div className="max-w-3xl mx-auto">
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

      <div className="bg-white rounded-lg shadow p-6">
        <h1 className="text-2xl font-bold text-gray-900 mb-6">
          Create New Roadmap
        </h1>

        {error && (
          <div className="mb-4 bg-red-50 text-red-700 p-3 rounded-md text-sm">
            {error.message}
          </div>
        )}

        <form onSubmit={handleSubmit} className="space-y-6">
          <div>
            <label
              htmlFor="title"
              className="block text-sm font-medium text-gray-700 mb-1"
            >
              Roadmap Title
            </label>
            <input
              type="text"
              id="title"
              value={title}
              onChange={(e) => setTitle(e.target.value)}
              placeholder="e.g., Learn React Fundamentals"
              className="w-full px-3 py-2 border border-gray-300 rounded-md shadow-sm focus:outline-none focus:ring-2 focus:ring-blue-500 focus:border-blue-500"
              required
            />
          </div>

          <div>
            <label
              htmlFor="rawText"
              className="block text-sm font-medium text-gray-700 mb-1"
            >
              Paste Your Learning Plan
            </label>
            <textarea
              id="rawText"
              value={rawText}
              onChange={(e) => setRawText(e.target.value)}
              placeholder="Paste your learning plan, notes, or outline here..."
              rows={12}
              className="w-full px-3 py-2 border border-gray-300 rounded-md shadow-sm focus:outline-none focus:ring-2 focus:ring-blue-500 focus:border-blue-500 font-mono text-sm"
              required
            />
            <p className="mt-1 text-sm text-gray-500">
              This will be saved as your draft. AI parsing into sessions coming
              soon.
            </p>
          </div>

          <div className="flex gap-3">
            <button
              type="submit"
              disabled={isPending || !title.trim() || !rawText.trim()}
              className="px-4 py-2 bg-blue-600 text-white rounded-md hover:bg-blue-700 focus:outline-none focus:ring-2 focus:ring-offset-2 focus:ring-blue-500 disabled:opacity-50 disabled:cursor-not-allowed"
            >
              {isPending ? 'Creating...' : 'Create Roadmap'}
            </button>
            <Link
              to="/"
              className="px-4 py-2 border border-gray-300 text-gray-700 rounded-md hover:bg-gray-50"
            >
              Cancel
            </Link>
          </div>
        </form>
      </div>
    </div>
  );
}
