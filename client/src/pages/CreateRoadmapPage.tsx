import { useState, useEffect } from 'react';
import { useNavigate, Link } from 'react-router-dom';
import { useRoadmapCreation } from '../hooks/useRoadmapCreation';
import { InterviewQuestions } from '../components/creation/InterviewQuestions';
import { CreationProgressDisplay } from '../components/creation/CreationProgress';
import { ValidationReview } from '../components/creation/ValidationReview';

export function CreateRoadmapPage() {
  const [title, setTitle] = useState('');
  const [rawText, setRawText] = useState('');
  const navigate = useNavigate();
  const { state, start, submitAnswers, submitReview, reset } = useRoadmapCreation();

  // Navigate to roadmap on completion
  useEffect(() => {
    if (state.stage === 'complete' && state.roadmapId) {
      navigate(`/roadmaps/${state.roadmapId}`);
    }
  }, [state.stage, state.roadmapId, navigate]);

  // Clean up on unmount
  useEffect(() => {
    return () => {
      if (state.stage !== 'idle' && state.stage !== 'complete') {
        reset();
      }
    };
  // eslint-disable-next-line react-hooks/exhaustive-deps
  }, []);

  const handleInitialSubmit = (e: React.FormEvent) => {
    e.preventDefault();
    if (!title.trim() || !rawText.trim()) {
      return;
    }
    start(rawText.trim(), title.trim());
  };

  const handleAcceptValidation = () => {
    submitReview(true);
  };

  const handleFixIssues = (issueIds: string[]) => {
    submitReview(false, issueIds);
  };

  // Show interview questions
  if (state.stage === 'interviewing' && state.questions.length > 0) {
    return (
      <div className="max-w-3xl mx-auto py-6">
        <div className="mb-6">
          <button
            onClick={reset}
            className="text-blue-600 hover:text-blue-800 text-sm flex items-center gap-1"
          >
            <svg className="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
              <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M15 19l-7-7 7-7" />
            </svg>
            Start Over
          </button>
        </div>
        <InterviewQuestions
          questions={state.questions}
          onSubmit={submitAnswers}
          isSubmitting={false}
        />
      </div>
    );
  }

  // Show progress during pipeline
  if (['starting', 'architecting', 'researching', 'validating', 'saving'].includes(state.stage)) {
    return (
      <div className="max-w-3xl mx-auto py-6">
        <CreationProgressDisplay progress={state.progress} />
      </div>
    );
  }

  // Show validation review
  if (state.stage === 'user_review' && state.validationResult) {
    return (
      <div className="max-w-3xl mx-auto py-6">
        <ValidationReview
          validationResult={state.validationResult}
          onAccept={handleAcceptValidation}
          onFixIssues={handleFixIssues}
          isSubmitting={false}
        />
      </div>
    );
  }

  // Show error state
  if (state.stage === 'error') {
    return (
      <div className="max-w-3xl mx-auto py-6">
        <div className="bg-red-50 border border-red-200 rounded-lg p-6 text-center">
          <div className="inline-flex items-center justify-center w-12 h-12 bg-red-100 rounded-full mb-4">
            <svg className="w-6 h-6 text-red-600" fill="none" viewBox="0 0 24 24" stroke="currentColor">
              <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M6 18L18 6M6 6l12 12" />
            </svg>
          </div>
          <h3 className="text-lg font-semibold text-red-800 mb-2">Something went wrong</h3>
          <p className="text-red-700 mb-4">{state.error}</p>
          <button
            onClick={reset}
            className="px-4 py-2 bg-red-600 text-white rounded-md hover:bg-red-700"
          >
            Try Again
          </button>
        </div>
      </div>
    );
  }

  // Show initial form (idle state)
  return (
    <div className="max-w-3xl mx-auto">
      <div className="mb-6">
        <Link
          to="/"
          className="text-blue-600 hover:text-blue-800 text-sm flex items-center gap-1"
        >
          <svg className="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
            <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M15 19l-7-7 7-7" />
          </svg>
          Back to Dashboard
        </Link>
      </div>

      <div className="bg-white rounded-lg shadow p-6">
        <h1 className="text-2xl font-bold text-gray-900 mb-2">
          Create New Roadmap
        </h1>
        <p className="text-gray-600 mb-6">
          Our AI will ask you a few questions to personalize your learning path
        </p>

        <form onSubmit={handleInitialSubmit} className="space-y-6">
          <div>
            <label htmlFor="title" className="block text-sm font-medium text-gray-700 mb-1">
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
            <label htmlFor="rawText" className="block text-sm font-medium text-gray-700 mb-1">
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
              We'll analyze your plan and ask clarifying questions to create a personalized roadmap.
            </p>
          </div>

          <div className="flex gap-3">
            <button
              type="submit"
              disabled={state.stage === 'starting' || !title.trim() || !rawText.trim()}
              className="px-4 py-2 bg-blue-600 text-white rounded-md hover:bg-blue-700 focus:outline-none focus:ring-2 focus:ring-offset-2 focus:ring-blue-500 disabled:opacity-50 disabled:cursor-not-allowed"
            >
              {state.stage === 'starting' ? 'Starting...' : 'Continue'}
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
