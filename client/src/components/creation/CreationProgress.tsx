/**
 * Progress indicator for roadmap creation pipeline.
 * Shows a single progress bar with activity log of completed/current/pending stages.
 */

import type { CreationProgress, CreationStage, CompletedStage } from '../../types';

interface CreationProgressProps {
  progress: CreationProgress;
  completedStages?: CompletedStage[];
}

// Pipeline stages in order (excluding interviewing which happens before this screen)
const PIPELINE_STAGES: { stage: CreationStage; label: string; pendingLabel: string }[] = [
  { stage: 'architecting', label: 'Designing', pendingLabel: 'Design learning path' },
  { stage: 'researching', label: 'Researching', pendingLabel: 'Research content' },
  { stage: 'finding_videos', label: 'Videos', pendingLabel: 'Find videos' },
  { stage: 'validating', label: 'Validating', pendingLabel: 'Quality check' },
  { stage: 'saving', label: 'Saving', pendingLabel: 'Save roadmap' },
];

// Stage weights based on actual time spent (total = 100%)
const STAGE_WEIGHTS: Record<string, { start: number; weight: number }> = {
  architecting:   { start: 0,   weight: 10 },  // 0-10%
  researching:    { start: 10,  weight: 50 },  // 10-60%
  finding_videos: { start: 60,  weight: 20 },  // 60-80%
  validating:     { start: 80,  weight: 15 },  // 80-95%
  saving:         { start: 95,  weight: 5 },   // 95-100%
};

function getStageIndex(stage: CreationStage): number {
  return PIPELINE_STAGES.findIndex(s => s.stage === stage);
}

function calculateProgress(
  currentStage: CreationStage,
  completedSessions?: number,
  totalSessions?: number
): number {
  if (currentStage === 'complete') return 100;

  const stageConfig = STAGE_WEIGHTS[currentStage];
  if (!stageConfig) return 0;

  const { start, weight } = stageConfig;

  // For researching, interpolate based on completed sessions
  if (currentStage === 'researching' && completedSessions !== undefined && totalSessions && totalSessions > 0) {
    const sessionProgress = (completedSessions / totalSessions) * weight;
    return Math.round(start + sessionProgress);
  }

  // For other in-progress stages, show start of that stage
  return start;
}

export function CreationProgressDisplay({ progress, completedStages = [] }: CreationProgressProps) {
  const currentStageIndex = getStageIndex(progress.stage);
  const progressPercent = calculateProgress(
    progress.stage,
    progress.completed_sessions,
    progress.total_sessions
  );

  // Build summary map from completed stages
  const summaryMap = new Map<CreationStage, string>();
  for (const cs of completedStages) {
    summaryMap.set(cs.stage, cs.summary);
  }

  return (
    <div className="w-full max-w-2xl mx-auto">
      {/* Header */}
      <div className="text-center mb-8">
        <h2 className="text-2xl font-bold text-gray-900 mb-2">Creating your roadmap...</h2>
        <p className="text-gray-600">This usually takes about 30 seconds</p>
      </div>

      {/* Main progress card */}
      <div className="bg-white rounded-lg border border-gray-200 shadow-sm p-6">
        {/* Progress bar */}
        <div className="mb-6">
          <div className="flex justify-between text-sm text-gray-600 mb-2">
            <span>Progress</span>
            <span>{progressPercent}%</span>
          </div>
          <div className="w-full bg-gray-200 rounded-full h-3 overflow-hidden">
            <div
              className="bg-blue-600 h-3 rounded-full transition-all duration-500 ease-out"
              style={{ width: `${progressPercent}%` }}
            />
          </div>
        </div>

        {/* Activity log */}
        <div className="space-y-3">
          {PIPELINE_STAGES.map((stageInfo, index) => {
            const isComplete = currentStageIndex > index;
            const isCurrent = currentStageIndex === index;
            const isPending = currentStageIndex < index;
            const summary = summaryMap.get(stageInfo.stage);

            return (
              <div key={stageInfo.stage} className="flex items-start gap-3">
                {/* Status icon */}
                <div className="flex-shrink-0 w-6 h-6 flex items-center justify-center">
                  {isComplete && (
                    <svg className="w-5 h-5 text-green-500" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                      <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M5 13l4 4L19 7" />
                    </svg>
                  )}
                  {isCurrent && (
                    <div className="w-5 h-5 rounded-full border-2 border-blue-600 border-t-transparent animate-spin" />
                  )}
                  {isPending && (
                    <div className="w-3 h-3 rounded-full bg-gray-300" />
                  )}
                </div>

                {/* Stage text */}
                <div className="flex-1 min-w-0">
                  {isComplete && (
                    <p className="text-gray-700">
                      <span className="text-green-600 font-medium">✓</span>{' '}
                      {summary || `${stageInfo.label} complete`}
                    </p>
                  )}
                  {isCurrent && (
                    <p className="text-blue-700 font-medium">
                      {progress.stage === 'researching' && progress.completed_sessions !== undefined && progress.total_sessions
                        ? `Researching sessions... (${progress.completed_sessions} of ${progress.total_sessions} complete)`
                        : progress.message}
                    </p>
                  )}
                  {isPending && (
                    <p className="text-gray-400">{stageInfo.pendingLabel}</p>
                  )}
                </div>
              </div>
            );
          })}
        </div>
      </div>

      {/* Tip or encouragement */}
      <p className="text-center text-sm text-gray-500 mt-6">
        We're creating personalized content just for you
      </p>
    </div>
  );
}
