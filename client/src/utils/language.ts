/**
 * Language detection utilities.
 */

// Hebrew Unicode range: \u0590-\u05FF
const HEBREW_REGEX = /[\u0590-\u05FF]/;

/**
 * Check if text contains Hebrew characters.
 */
export function isHebrew(text: string): boolean {
  return HEBREW_REGEX.test(text);
}

/**
 * Get text direction based on content.
 */
export function getTextDirection(text: string): 'rtl' | 'ltr' {
  return isHebrew(text) ? 'rtl' : 'ltr';
}

/**
 * Get direction for a language code.
 */
export function getLanguageDirection(language: string): 'rtl' | 'ltr' {
  return language === 'he' ? 'rtl' : 'ltr';
}

export type Language = 'en' | 'he';
