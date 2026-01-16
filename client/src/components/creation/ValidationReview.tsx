/**
 * Validation review component for roadmap quality issues.
 */

import { useState } from 'react';
import type { ValidationResult } from '../../types';

interface ValidationReviewProps {
  validationResult: ValidationResult;
  onAccept: () => void;
  onFixIssues: (issueIds: string[]) => void;
  isSubmitting?: boolean;
}

const severityColors = {
  low: { bg: 'bg-yellow-50', border: 'border-yellow-200', text: 'text-yellow-800', badge: 'bg-yellow-100' },
  medium: { bg: 'bg-orange-50', border: 'border-orange-200', text: 'text-orange-800', badge: 'bg-orange-100' },
  high: { bg: 'bg-red-50', border: 'border-red-200', text: 'text-red-800', badge: 'bg-red-100' },
};

const issueTypeLabels: Record<string, string> = {
  overlap: 'Content Overlap',
  gap: 'Knowledge Gap',
  ordering: 'Ordering Issue',
  coherence: 'Coherence Issue',
  depth: 'Depth Issue',
};

export function ValidationReview({
  validationResult,
  onAccept,
  onFixIssues,
  isSubmitting = false,
}: ValidationReviewProps) {
  const [selectedIssues, setSelectedIssues] = useState<Set<string>>(new Set());

  const toggleIssue = (issueId: string) => {
    setSelectedIssues(prev => {
      const next = new Set(prev);
      if (next.has(issueId)) {
        next.delete(issueId);
      } else {
        next.add(issueId);
      }
      return next;
    });
  };

  const handleFixSelected = () => {
    onFixIssues(Array.from(selectedIssues));
  };

  const scoreColor =
    validationResult.score >= 80
      ? 'text-green-600'
      : validationResult.score >= 60
        ? 'text-yellow-600'
        : 'text-red-600';

  return (
    <div className="max-w-3xl mx-auto py-8">
      {/* Header with score */}
      <div className="text-center mb-8">
        <h2 className="text-2xl font-bold text-gray-900 mb-4">
          Quality Review
        </h2>
        <div className="inline-flex items-center gap-4 bg-white rounded-lg px-8 py-4 shadow-md">
          <div className="text-center">
            <div className={`text-4xl font-bold ${scoreColor}`}>
              {Math.round(validationResult.score)}
            </div>
            <div className="text-sm text-gray-500">Quality Score</div>
          </div>
          <div className="w-px h-12 bg-gray-200" />
          <div className="text-left">
            <div className="text-lg font-medium text-gray-800">
              {validationResult.issues.length} issue{validationResult.issues.length !== 1 ? 's' : ''} found
            </div>
            <div className="text-sm text-gray-500">{validationResult.summary}</div>
          </div>
        </div>
      </div>

      {/* Issues list */}
      {validationResult.issues.length > 0 && (
        <div className="space-y-4 mb-8">
          <h3 className="text-lg font-semibold text-gray-800">Issues Found</h3>
          {validationResult.issues.map(issue => {
            const colors = severityColors[issue.severity];
            const isSelected = selectedIssues.has(issue.id);

            return (
              <div
                key={issue.id}
                className={`rounded-lg border ${colors.border} ${colors.bg} p-4 transition-shadow ${
                  isSelected ? 'ring-2 ring-blue-500' : ''
                }`}
              >
                <div className="flex items-start gap-4">
                  <input
                    type="checkbox"
                    checked={isSelected}
                    onChange={() => toggleIssue(issue.id)}
                    className="mt-1 h-4 w-4 rounded border-gray-300 text-blue-600 focus:ring-blue-500"
                  />
                  <div className="flex-1">
                    <div className="flex items-center gap-2 mb-2">
                      <span
                        className={`inline-flex px-2 py-1 rounded text-xs font-medium ${colors.badge} ${colors.text}`}
                      >
                        {issue.severity.toUpperCase()}
                      </span>
                      <span className="text-sm font-medium text-gray-600">
                        {issueTypeLabels[issue.issue_type] || issue.issue_type}
                      </span>
                    </div>
                    <p className={`${colors.text} mb-2`}>{issue.description}</p>
                    <p className="text-sm text-gray-600">
                      <span className="font-medium">Suggested fix:</span> {issue.suggested_fix}
                    </p>
                  </div>
                </div>
              </div>
            );
          })}
        </div>
      )}

      {/* Action buttons */}
      <div className="flex justify-center gap-4">
        <button
          onClick={onAccept}
          disabled={isSubmitting}
          className={`px-6 py-3 rounded-lg font-medium transition-colors ${
            isSubmitting
              ? 'bg-gray-300 text-gray-500 cursor-not-allowed'
              : 'bg-green-600 text-white hover:bg-green-700'
          }`}
        >
          {isSubmitting ? 'Saving...' : 'Accept & Save'}
        </button>
        {selectedIssues.size > 0 && (
          <button
            onClick={handleFixSelected}
            disabled={isSubmitting}
            className={`px-6 py-3 rounded-lg font-medium transition-colors ${
              isSubmitting
                ? 'bg-gray-300 text-gray-500 cursor-not-allowed'
                : 'bg-blue-600 text-white hover:bg-blue-700'
            }`}
          >
            Fix Selected ({selectedIssues.size})
          </button>
        )}
      </div>

      <p className="text-center text-sm text-gray-500 mt-4">
        You can accept the roadmap as-is or select issues to fix before saving.
      </p>
    </div>
  );
}
