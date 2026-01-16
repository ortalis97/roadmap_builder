/**
 * Progress indicator for roadmap creation pipeline.
 */

import type { CreationProgress, CreationStage } from '../../types';

interface CreationProgressProps {
  progress: CreationProgress;
}

const stageOrder: CreationStage[] = [
  'starting',
  'interviewing',
  'architecting',
  'researching',
  'validating',
  'saving',
  'complete',
];

const stageLabels: Record<CreationStage, string> = {
  idle: 'Ready',
  starting: 'Starting',
  interviewing: 'Interview',
  architecting: 'Designing',
  researching: 'Researching',
  validating: 'Validating',
  user_review: 'Review',
  saving: 'Saving',
  complete: 'Complete',
  error: 'Error',
};

function getStageIndex(stage: CreationStage): number {
  const idx = stageOrder.indexOf(stage);
  return idx >= 0 ? idx : 0;
}

export function CreationProgressDisplay({ progress }: CreationProgressProps) {
  const currentIndex = getStageIndex(progress.stage);

  return (
    <div className="w-full max-w-2xl mx-auto py-8">
      {/* Stage indicators */}
      <div className="flex justify-between mb-8">
        {stageOrder.slice(2, -1).map((stage, index) => {
          const actualIndex = index + 2;
          const isComplete = currentIndex > actualIndex;
          const isCurrent = currentIndex === actualIndex;

          return (
            <div key={stage} className="flex flex-col items-center">
              <div
                className={`w-10 h-10 rounded-full flex items-center justify-center mb-2 transition-colors ${
                  isComplete
                    ? 'bg-green-500 text-white'
                    : isCurrent
                      ? 'bg-blue-600 text-white'
                      : 'bg-gray-200 text-gray-500'
                }`}
              >
                {isComplete ? (
                  <svg className="w-6 h-6" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                    <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M5 13l4 4L19 7" />
                  </svg>
                ) : (
                  <span className="text-sm font-medium">{index + 1}</span>
                )}
              </div>
              <span
                className={`text-xs font-medium ${
                  isCurrent ? 'text-blue-600' : isComplete ? 'text-green-600' : 'text-gray-500'
                }`}
              >
                {stageLabels[stage]}
              </span>
            </div>
          );
        })}
      </div>

      {/* Current stage message */}
      <div className="text-center mb-6">
        <div className="inline-flex items-center gap-3 bg-white rounded-lg px-6 py-4 shadow-md">
          {progress.stage !== 'complete' && progress.stage !== 'error' && (
            <svg className="animate-spin h-6 w-6 text-blue-600" viewBox="0 0 24 24">
              <circle
                className="opacity-25"
                cx="12"
                cy="12"
                r="10"
                stroke="currentColor"
                strokeWidth="4"
                fill="none"
              />
              <path
                className="opacity-75"
                fill="currentColor"
                d="M4 12a8 8 0 018-8V0C5.373 0 0 5.373 0 12h4zm2 5.291A7.962 7.962 0 014 12H0c0 3.042 1.135 5.824 3 7.938l3-2.647z"
              />
            </svg>
          )}
          <span className="text-lg font-medium text-gray-800">{progress.message}</span>
        </div>
      </div>

      {/* Research progress bar */}
      {progress.stage === 'researching' && progress.total_sessions && (
        <div className="bg-white rounded-lg p-6 shadow-md">
          <div className="flex justify-between text-sm text-gray-600 mb-2">
            <span>Session {progress.current_session} of {progress.total_sessions}</span>
            <span>{Math.round(((progress.current_session || 0) / progress.total_sessions) * 100)}%</span>
          </div>
          <div className="w-full bg-gray-200 rounded-full h-3">
            <div
              className="bg-blue-600 h-3 rounded-full transition-all duration-300"
              style={{ width: `${((progress.current_session || 0) / progress.total_sessions) * 100}%` }}
            />
          </div>
          {progress.session_title && (
            <p className="mt-3 text-sm text-gray-500 text-center">
              {progress.session_title}
            </p>
          )}
        </div>
      )}

      {/* Complete state */}
      {progress.stage === 'complete' && (
        <div className="text-center">
          <div className="inline-flex items-center justify-center w-16 h-16 bg-green-100 rounded-full mb-4">
            <svg className="w-8 h-8 text-green-600" fill="none" viewBox="0 0 24 24" stroke="currentColor">
              <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M5 13l4 4L19 7" />
            </svg>
          </div>
          <h3 className="text-xl font-semibold text-gray-900">Roadmap Created!</h3>
        </div>
      )}
    </div>
  );
}
