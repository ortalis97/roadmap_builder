"""Language detection utilities."""

import re

# Hebrew Unicode range: \u0590-\u05FF (Hebrew letters and marks)
HEBREW_PATTERN = re.compile(r"[\u0590-\u05FF]")


def detect_language(text: str) -> str:
    """Detect language from text content.

    Returns 'he' if Hebrew characters are found, otherwise 'en'.
    """
    if HEBREW_PATTERN.search(text):
        return "he"
    return "en"


def is_hebrew(text: str) -> bool:
    """Check if text contains Hebrew characters."""
    return bool(HEBREW_PATTERN.search(text))
