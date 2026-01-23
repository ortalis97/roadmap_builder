import { useState, useEffect } from 'react';

/**
 * Hook to detect if a media query matches.
 * @param query - CSS media query string (e.g., '(min-width: 768px)')
 * @returns boolean indicating if the query matches
 */
export function useMediaQuery(query: string): boolean {
  const [matches, setMatches] = useState(() => {
    // Check on initial render (SSR-safe with fallback)
    if (typeof window !== 'undefined') {
      return window.matchMedia(query).matches;
    }
    return false;
  });

  useEffect(() => {
    const media = window.matchMedia(query);
    setMatches(media.matches);

    const listener = (e: MediaQueryListEvent) => setMatches(e.matches);
    media.addEventListener('change', listener);
    return () => media.removeEventListener('change', listener);
  }, [query]);

  return matches;
}

/**
 * Hook to detect if the viewport is mobile-sized (below 768px).
 * @returns true if viewport width is less than 768px
 */
export function useIsMobile(): boolean {
  return !useMediaQuery('(min-width: 768px)');
}
