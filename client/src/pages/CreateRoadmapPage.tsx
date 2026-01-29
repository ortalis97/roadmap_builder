import { useState, useEffect } from 'react';
import { useNavigate, Link } from 'react-router-dom';
import { useRoadmapCreation } from '../hooks/useRoadmapCreation';
import { InterviewQuestions } from '../components/creation/InterviewQuestions';
import { CreationProgressDisplay } from '../components/creation/CreationProgress';
import { useIsMobile } from '../hooks/useMediaQuery';

export function CreateRoadmapPage() {
  const [topic, setTopic] = useState('');
  const navigate = useNavigate();
  const isMobile = useIsMobile();
  const { state, start, submitAnswers, reset } = useRoadmapCreation();

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
    if (!topic.trim()) {
      return;
    }
    start(topic.trim());
  };

  // Show interview questions
  if (state.stage === 'interviewing' && state.questions.length > 0) {
    return (
      <div className="max-w-3xl mx-auto py-6">
        <div className="mb-6">
          <button
            onClick={reset}
            className="text-blue-600 hover:text-blue-800 text-sm flex items-center gap-1 py-2 min-h-[44px] md:min-h-0 md:py-0"
          >
            <svg className="w-5 h-5 md:w-4 md:h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
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
  if (['architecting', 'researching', 'finding_videos', 'validating', 'saving'].includes(state.stage)) {
    return (
      <div className="max-w-3xl mx-auto py-6">
        <CreationProgressDisplay progress={state.progress} completedStages={state.completedStages} />
      </div>
    );
  }

  // Show simple loader while fetching interview questions
  if (state.stage === 'starting') {
    return (
      <div className="max-w-3xl mx-auto py-6">
        <div className="bg-white rounded-lg shadow p-8">
          <div className="flex flex-col items-center justify-center py-12">
            <svg className="animate-spin h-10 w-10 text-blue-600 mb-4" viewBox="0 0 24 24">
              <circle className="opacity-25" cx="12" cy="12" r="10" stroke="currentColor" strokeWidth="4" fill="none" />
              <path className="opacity-75" fill="currentColor" d="M4 12a8 8 0 018-8V0C5.373 0 0 5.373 0 12h4zm2 5.291A7.962 7.962 0 014 12H0c0 3.042 1.135 5.824 3 7.938l3-2.647z" />
            </svg>
            <p className="text-lg text-gray-700 font-medium">Preparing your questions...</p>
            <p className="text-sm text-gray-500 mt-2">This will just take a moment</p>
          </div>
        </div>
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
            className="px-4 py-3 md:py-2 min-h-[44px] md:min-h-0 bg-red-600 text-white rounded-md hover:bg-red-700"
          >
            Try Again
          </button>
        </div>
      </div>
    );
  }

  // Show initial form (idle state) - chat-like input
  return (
    <div className="max-w-3xl mx-auto">
      <div className="mb-6">
        <Link
          to="/"
          className="text-blue-600 hover:text-blue-800 text-sm flex items-center gap-1 py-2 min-h-[44px] md:min-h-0 md:py-0"
        >
          <svg className="w-5 h-5 md:w-4 md:h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
            <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M15 19l-7-7 7-7" />
          </svg>
          Back to Dashboard
        </Link>
      </div>

      <div className="bg-white rounded-lg shadow p-8">
        <h1 className="text-2xl font-bold text-gray-900 mb-2 text-center">
          What do you want to learn?
        </h1>
        <p className="text-gray-600 mb-8 text-center">
          Tell us what you want to learn and we'll create a personalized roadmap for you
        </p>

        <form onSubmit={handleInitialSubmit} className="space-y-4">
          {/* Desktop: input with inline button */}
          {!isMobile && (
            <div className="relative">
              <input
                type="text"
                value={topic}
                onChange={(e) => setTopic(e.target.value)}
                placeholder="e.g., Learn Python for data science"
                className="w-full px-4 py-3 pr-12 border border-gray-300 rounded-lg shadow-sm focus:outline-none focus:ring-2 focus:ring-blue-500 focus:border-blue-500 text-lg"
                required
                autoFocus
              />
              <button
                type="submit"
                disabled={!topic.trim()}
                className="absolute right-2 top-1/2 -translate-y-1/2 p-2 bg-blue-600 text-white rounded-md hover:bg-blue-700 focus:outline-none focus:ring-2 focus:ring-offset-2 focus:ring-blue-500 disabled:opacity-50 disabled:cursor-not-allowed"
              >
                <svg className="w-5 h-5" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                  <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M14 5l7 7m0 0l-7 7m7-7H3" />
                </svg>
              </button>
            </div>
          )}

          {/* Mobile: separate input and button */}
          {isMobile && (
            <>
              <input
                type="text"
                value={topic}
                onChange={(e) => setTopic(e.target.value)}
                placeholder="e.g., Learn Python for data science"
                className="w-full px-4 py-3 border border-gray-300 rounded-lg shadow-sm focus:outline-none focus:ring-2 focus:ring-blue-500 focus:border-blue-500 text-lg"
                required
                autoFocus
              />
              <button
                type="submit"
                disabled={!topic.trim()}
                className="w-full flex items-center justify-center gap-2 px-4 py-3 min-h-[44px] bg-blue-600 text-white rounded-lg hover:bg-blue-700 focus:outline-none focus:ring-2 focus:ring-offset-2 focus:ring-blue-500 disabled:opacity-50 disabled:cursor-not-allowed font-medium"
              >
                <span>Create Roadmap</span>
                <svg className="w-5 h-5" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                  <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M14 5l7 7m0 0l-7 7m7-7H3" />
                </svg>
              </button>
            </>
          )}
        </form>

        <div className="mt-8 pt-6 border-t border-gray-200">
          <p className="text-sm text-gray-500 mb-3">Examples:</p>
          <div className="flex flex-wrap gap-2">
            {[
              'Learn Python for data science',
              'Master React and TypeScript',
              'Understand machine learning basics',
              'Build mobile apps with Flutter',
              'ללמוד פייתון למתחילים',
            ].map((example) => (
              <button
                key={example}
                onClick={() => setTopic(example)}
                className="text-sm px-3 py-2 md:py-1.5 min-h-[44px] md:min-h-0 bg-gray-100 text-gray-700 rounded-full hover:bg-gray-200 transition-colors"
              >
                {example}
              </button>
            ))}
          </div>
        </div>
      </div>
    </div>
  );
}
