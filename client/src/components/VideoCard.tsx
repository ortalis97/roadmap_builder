import type { VideoResource } from '../types';

interface VideoCardProps {
  video: VideoResource;
}

export function VideoCard({ video }: VideoCardProps) {
  const formatDuration = (minutes: number | null): string => {
    if (minutes === null) return '';
    if (minutes < 60) return `${minutes} min`;
    const hours = Math.floor(minutes / 60);
    const mins = minutes % 60;
    return mins > 0 ? `${hours}h ${mins}m` : `${hours}h`;
  };

  return (
    <a
      href={video.url}
      target="_blank"
      rel="noopener noreferrer"
      className="block group"
    >
      <div className="bg-white border border-gray-200 rounded-lg overflow-hidden hover:shadow-md transition-shadow">
        {/* Thumbnail */}
        <div className="relative aspect-video bg-gray-100">
          <img
            src={video.thumbnail_url}
            alt={video.title}
            className="w-full h-full object-cover"
            onError={(e) => {
              // Fallback for broken thumbnails
              (e.target as HTMLImageElement).src = 'https://img.youtube.com/vi/default/maxresdefault.jpg';
            }}
          />
          {video.duration_minutes && (
            <span className="absolute bottom-2 right-2 bg-black bg-opacity-80 text-white text-xs px-1.5 py-0.5 rounded">
              {formatDuration(video.duration_minutes)}
            </span>
          )}
          {/* Play overlay on hover */}
          <div className="absolute inset-0 flex items-center justify-center bg-black bg-opacity-0 group-hover:bg-opacity-30 transition-all">
            <svg
              className="w-12 h-12 text-white opacity-0 group-hover:opacity-100 transition-opacity"
              fill="currentColor"
              viewBox="0 0 24 24"
            >
              <path d="M8 5v14l11-7z" />
            </svg>
          </div>
        </div>

        {/* Info */}
        <div className="p-3">
          <h4 className="font-medium text-gray-900 text-sm line-clamp-2 group-hover:text-blue-600">
            {video.title}
          </h4>
          <p className="text-xs text-gray-500 mt-1">{video.channel}</p>
          {video.description && (
            <p className="text-xs text-gray-600 mt-1 line-clamp-2">{video.description}</p>
          )}
        </div>
      </div>
    </a>
  );
}
