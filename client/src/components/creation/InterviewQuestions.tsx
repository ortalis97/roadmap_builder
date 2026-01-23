/**
 * Interview questions component for roadmap creation.
 */

import { useState } from 'react';
import type { InterviewQuestion, InterviewAnswer } from '../../types';
import { getTextDirection } from '../../utils/language';

interface InterviewQuestionsProps {
  questions: InterviewQuestion[];
  onSubmit: (answers: InterviewAnswer[]) => void;
  isSubmitting?: boolean;
}

export function InterviewQuestions({
  questions,
  onSubmit,
  isSubmitting = false,
}: InterviewQuestionsProps) {
  const [answers, setAnswers] = useState<Record<string, string>>({});

  const handleOptionClick = (questionId: string, optionText: string) => {
    setAnswers(prev => ({ ...prev, [questionId]: optionText }));
  };

  const handleTextChange = (questionId: string, value: string) => {
    setAnswers(prev => ({ ...prev, [questionId]: value }));
  };

  const handleSubmit = (e: React.FormEvent) => {
    e.preventDefault();
    const formattedAnswers: InterviewAnswer[] = questions.map(q => ({
      question_id: q.id,
      answer: answers[q.id] || '',
    }));
    onSubmit(formattedAnswers);
  };

  const allAnswered = questions.every(q => answers[q.id]?.trim());

  return (
    <form onSubmit={handleSubmit} className="space-y-8">
      <div className="text-center mb-8">
        <h2 className="text-2xl font-bold text-gray-900 mb-2">
          Help us personalize your roadmap
        </h2>
        <p className="text-gray-600">
          Answer a few questions so we can tailor your learning path
        </p>
      </div>

      {questions.map((question, index) => (
        <div
          key={question.id}
          className="bg-white rounded-lg border border-gray-200 p-6 shadow-sm"
        >
          <div className="flex items-start gap-4 mb-4">
            <span className="flex-shrink-0 w-8 h-8 bg-blue-100 text-blue-700 rounded-full flex items-center justify-center font-semibold text-sm">
              {index + 1}
            </span>
            <div className="flex-1">
              <h3
                className="text-lg font-medium text-gray-900 mb-1"
                dir={getTextDirection(question.question)}
              >
                {question.question}
              </h3>
              <p
                className="text-sm text-gray-500"
                dir={getTextDirection(question.purpose)}
              >
                {question.purpose}
              </p>
            </div>
          </div>

          {/* Example options as clickable chips */}
          <div className="flex flex-wrap gap-3 md:gap-2 mb-4">
            {question.example_options.map(option => (
              <button
                key={option.label}
                type="button"
                onClick={() => handleOptionClick(question.id, option.text)}
                className={`px-4 py-3 md:py-2 min-h-[44px] md:min-h-0 rounded-full text-sm font-medium transition-colors ${
                  answers[question.id] === option.text
                    ? 'bg-blue-600 text-white'
                    : 'bg-gray-100 text-gray-700 hover:bg-gray-200'
                }`}
              >
                <span className="font-bold mr-1">{option.label}.</span>
                {option.text}
              </button>
            ))}
          </div>

          {/* Freeform text input */}
          {question.allows_freeform && (
            <div className="mt-4">
              <label className="block text-sm text-gray-600 mb-2">
                Or write your own answer:
              </label>
              <textarea
                dir="auto"
                value={answers[question.id] || ''}
                onChange={e => handleTextChange(question.id, e.target.value)}
                placeholder="Type your answer..."
                rows={2}
                className="w-full px-4 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-blue-500 resize-none"
              />
            </div>
          )}
        </div>
      ))}

      <div className="flex justify-end">
        <button
          type="submit"
          disabled={!allAnswered || isSubmitting}
          className={`w-full md:w-auto px-6 py-3 min-h-[44px] md:min-h-0 rounded-lg font-medium transition-colors ${
            allAnswered && !isSubmitting
              ? 'bg-blue-600 text-white hover:bg-blue-700'
              : 'bg-gray-300 text-gray-500 cursor-not-allowed'
          }`}
        >
          {isSubmitting ? (
            <span className="flex items-center gap-2">
              <svg className="animate-spin h-5 w-5" viewBox="0 0 24 24">
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
              Processing...
            </span>
          ) : (
            'Create My Roadmap'
          )}
        </button>
      </div>
    </form>
  );
}
