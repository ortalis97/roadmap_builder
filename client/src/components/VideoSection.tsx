import type { VideoResource } from '../types';
import { VideoCard } from './VideoCard';

interface VideoSectionProps {
  videos: VideoResource[];
}

export function VideoSection({ videos }: VideoSectionProps) {
  if (!videos || videos.length === 0) {
    return null; // Skip silently if no videos
  }

  return (
    <div className="mt-6">
      <h3 className="text-lg font-semibold text-gray-900 mb-4 flex items-center gap-2">
        <svg className="w-5 h-5 text-red-600" fill="currentColor" viewBox="0 0 24 24">
          <path d="M19.615 3.184c-3.604-.246-11.631-.245-15.23 0-3.897.266-4.356 2.62-4.385 8.816.029 6.185.484 8.549 4.385 8.816 3.6.245 11.626.246 15.23 0 3.897-.266 4.356-2.62 4.385-8.816-.029-6.185-.484-8.549-4.385-8.816zm-10.615 12.816v-8l8 3.993-8 4.007z"/>
        </svg>
        Recommended Videos
      </h3>
      <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-3 gap-4">
        {videos.map((video, index) => (
          <VideoCard key={`${video.url}-${index}`} video={video} />
        ))}
      </div>
    </div>
  );
}
