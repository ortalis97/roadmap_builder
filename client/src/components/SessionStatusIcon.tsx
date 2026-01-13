import type { SessionStatus } from '../types';

interface SessionStatusIconProps {
  status: SessionStatus;
  onClick?: () => void;
  size?: 'sm' | 'md';
}

const statusConfig = {
  not_started: {
    icon: '○',
    color: 'text-gray-400',
    bg: 'bg-gray-100 hover:bg-gray-200',
    label: 'Not started',
  },
  in_progress: {
    icon: '◐',
    color: 'text-blue-500',
    bg: 'bg-blue-100 hover:bg-blue-200',
    label: 'In progress',
  },
  done: {
    icon: '✓',
    color: 'text-green-600',
    bg: 'bg-green-100 hover:bg-green-200',
    label: 'Done',
  },
  skipped: {
    icon: '–',
    color: 'text-gray-500',
    bg: 'bg-gray-100 hover:bg-gray-200',
    label: 'Skipped',
  },
};

export function SessionStatusIcon({ status, onClick, size = 'md' }: SessionStatusIconProps) {
  const config = statusConfig[status];
  const sizeClasses = size === 'sm' ? 'w-6 h-6 text-sm' : 'w-8 h-8 text-base';

  return (
    <button
      type="button"
      onClick={onClick}
      className={`${sizeClasses} ${config.bg} ${config.color} rounded-full flex items-center justify-center transition-colors focus:outline-none focus:ring-2 focus:ring-offset-2 focus:ring-blue-500`}
      title={config.label}
    >
      {config.icon}
    </button>
  );
}

export function getNextStatus(current: SessionStatus): SessionStatus {
  const cycle: SessionStatus[] = ['not_started', 'in_progress', 'done'];
  const index = cycle.indexOf(current);
  if (index === -1) return 'not_started';
  return cycle[(index + 1) % cycle.length];
}
