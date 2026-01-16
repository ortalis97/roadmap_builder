/**
 * Hook for managing roadmap creation with multi-agent pipeline.
 */

import { useState, useCallback, useRef } from 'react';
import { startCreation, getInterviewSubmitUrl, getReviewSubmitUrl, cancelCreation } from '../services/api';
import { createSSEConnection, type SSEConnection } from '../services/sseClient';
import type {
  CreationStage,
  CreationProgress,
  InterviewQuestion,
  InterviewAnswer,
  ValidationResult,
  SSEStageUpdateData,
  SSESessionProgressData,
  SSECompleteData,
  SSEErrorData,
  SSETitleSuggestionData,
} from '../types';

export interface CreationState {
  stage: CreationStage;
  progress: CreationProgress;
  pipelineId: string | null;
  questions: InterviewQuestion[];
  answers: InterviewAnswer[];
  suggestedTitle: string | null;
  confirmedTitle: string | null;
  validationResult: ValidationResult | null;
  roadmapId: string | null;
  error: string | null;
}

const initialState: CreationState = {
  stage: 'idle',
  progress: { stage: 'idle', message: '' },
  pipelineId: null,
  questions: [],
  answers: [],
  suggestedTitle: null,
  confirmedTitle: null,
  validationResult: null,
  roadmapId: null,
  error: null,
};

export function useRoadmapCreation() {
  const [state, setState] = useState<CreationState>(initialState);
  const connectionRef = useRef<SSEConnection | null>(null);

  const updateState = useCallback((updates: Partial<CreationState>) => {
    setState(prev => ({ ...prev, ...updates }));
  }, []);

  const handleSSEEvent = useCallback((event: { event: string; data: unknown }) => {
    switch (event.event) {
      case 'stage_update': {
        const data = event.data as SSEStageUpdateData;
        updateState({
          stage: data.stage as CreationStage,
          progress: {
            stage: data.stage as CreationStage,
            message: data.message,
          },
        });
        break;
      }
      case 'session_progress': {
        const data = event.data as SSESessionProgressData;
        updateState({
          progress: {
            stage: 'researching',
            message: `Researching: ${data.session_title}`,
            current_session: data.current,
            total_sessions: data.total,
            session_title: data.session_title,
          },
        });
        break;
      }
      case 'title_suggestion': {
        const data = event.data as SSETitleSuggestionData;
        updateState({
          suggestedTitle: data.suggested_title,
        });
        break;
      }
      case 'validation_result': {
        const data = event.data as ValidationResult;
        updateState({
          stage: 'user_review',
          progress: { stage: 'user_review', message: 'Review required' },
          validationResult: data,
        });
        break;
      }
      case 'complete': {
        const data = event.data as SSECompleteData;
        updateState({
          stage: 'complete',
          progress: { stage: 'complete', message: data.message },
          roadmapId: data.roadmap_id,
        });
        break;
      }
      case 'error': {
        const data = event.data as SSEErrorData;
        updateState({
          stage: 'error',
          progress: { stage: 'error', message: data.message },
          error: data.message,
        });
        break;
      }
    }
  }, [updateState]);

  const start = useCallback(async (topic: string) => {
    try {
      updateState({ stage: 'starting', error: null });

      // Start creation pipeline with topic
      const response = await startCreation(topic);

      updateState({
        stage: 'interviewing',
        pipelineId: response.pipeline_id,
        questions: response.questions,
        progress: {
          stage: 'interviewing',
          message: 'Please answer a few questions to personalize your roadmap',
        },
      });
    } catch (error) {
      updateState({
        stage: 'error',
        error: error instanceof Error ? error.message : 'Failed to start creation',
        progress: { stage: 'error', message: 'Failed to start creation' },
      });
    }
  }, [updateState]);

  const submitAnswers = useCallback(async (answers: InterviewAnswer[]) => {
    if (!state.pipelineId) {
      updateState({ error: 'No active pipeline' });
      return;
    }

    updateState({
      stage: 'architecting',
      answers,
      progress: { stage: 'architecting', message: 'Creating your learning path...' },
    });

    try {
      connectionRef.current = await createSSEConnection(
        getInterviewSubmitUrl(),
        { pipeline_id: state.pipelineId, answers },
        handleSSEEvent,
        (error) => {
          updateState({
            stage: 'error',
            error: error.message,
            progress: { stage: 'error', message: error.message },
          });
        },
        () => {
          connectionRef.current = null;
        }
      );
    } catch (error) {
      updateState({
        stage: 'error',
        error: error instanceof Error ? error.message : 'Failed to connect',
        progress: { stage: 'error', message: 'Failed to connect' },
      });
    }
  }, [state.pipelineId, handleSSEEvent, updateState]);

  const submitReview = useCallback(async (acceptAsIs: boolean, issuesToFix: string[] = []) => {
    if (!state.pipelineId) {
      updateState({ error: 'No active pipeline' });
      return;
    }

    updateState({
      stage: 'saving',
      progress: { stage: 'saving', message: 'Saving your roadmap...' },
    });

    try {
      connectionRef.current = await createSSEConnection(
        getReviewSubmitUrl(),
        {
          pipeline_id: state.pipelineId,
          accept_as_is: acceptAsIs,
          issues_to_fix: issuesToFix,
          confirmed_title: state.confirmedTitle || state.suggestedTitle,
        },
        handleSSEEvent,
        (error) => {
          updateState({
            stage: 'error',
            error: error.message,
            progress: { stage: 'error', message: error.message },
          });
        },
        () => {
          connectionRef.current = null;
        }
      );
    } catch (error) {
      updateState({
        stage: 'error',
        error: error instanceof Error ? error.message : 'Failed to connect',
        progress: { stage: 'error', message: 'Failed to connect' },
      });
    }
  }, [state.pipelineId, state.confirmedTitle, state.suggestedTitle, handleSSEEvent, updateState]);

  const setConfirmedTitle = useCallback((title: string) => {
    updateState({ confirmedTitle: title });
  }, [updateState]);

  const reset = useCallback(async () => {
    // Close any active connection
    if (connectionRef.current) {
      connectionRef.current.close();
      connectionRef.current = null;
    }

    // Cancel pipeline on server if active
    if (state.pipelineId && state.stage !== 'complete' && state.stage !== 'error') {
      try {
        await cancelCreation(state.pipelineId);
      } catch {
        // Ignore cancellation errors
      }
    }

    setState(initialState);
  }, [state.pipelineId, state.stage]);

  return {
    state,
    start,
    submitAnswers,
    submitReview,
    setConfirmedTitle,
    reset,
  };
}
