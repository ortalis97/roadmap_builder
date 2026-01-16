import { useState, useEffect } from 'react';

interface TitleConfirmationProps {
  suggestedTitle: string;
  onConfirm: (title: string) => void;
  isSubmitting?: boolean;
}

export function TitleConfirmation({
  suggestedTitle,
  onConfirm,
  isSubmitting = false,
}: TitleConfirmationProps) {
  const [editedTitle, setEditedTitle] = useState(suggestedTitle);

  useEffect(() => {
    setEditedTitle(suggestedTitle);
  }, [suggestedTitle]);

  const handleSubmit = (e: React.FormEvent) => {
    e.preventDefault();
    if (editedTitle.trim()) {
      onConfirm(editedTitle.trim());
    }
  };

  return (
    <div className="bg-white rounded-lg shadow p-6">
      <div className="flex items-center justify-center mb-6">
        <div className="w-12 h-12 bg-green-100 rounded-full flex items-center justify-center">
          <svg
            className="w-6 h-6 text-green-600"
            fill="none"
            viewBox="0 0 24 24"
            stroke="currentColor"
          >
            <path
              strokeLinecap="round"
              strokeLinejoin="round"
              strokeWidth={2}
              d="M5 13l4 4L19 7"
            />
          </svg>
        </div>
      </div>

      <h2 className="text-xl font-semibold text-gray-900 text-center mb-2">
        We've created a roadmap for you!
      </h2>
      <p className="text-gray-600 text-center mb-6">
        Confirm the title or edit it to your preference
      </p>

      <form onSubmit={handleSubmit} className="space-y-4">
        <div>
          <label htmlFor="title" className="block text-sm font-medium text-gray-700 mb-1">
            Roadmap Title
          </label>
          <input
            type="text"
            id="title"
            value={editedTitle}
            onChange={(e) => setEditedTitle(e.target.value)}
            className="w-full px-3 py-2 border border-gray-300 rounded-md shadow-sm focus:outline-none focus:ring-2 focus:ring-blue-500 focus:border-blue-500"
            required
            autoFocus
          />
        </div>

        <button
          type="submit"
          disabled={isSubmitting || !editedTitle.trim()}
          className="w-full px-4 py-2 bg-blue-600 text-white rounded-md hover:bg-blue-700 focus:outline-none focus:ring-2 focus:ring-offset-2 focus:ring-blue-500 disabled:opacity-50 disabled:cursor-not-allowed"
        >
          {isSubmitting ? 'Saving...' : 'Confirm & Save'}
        </button>
      </form>
    </div>
  );
}
