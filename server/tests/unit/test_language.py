"""Unit tests for language detection utilities."""

import pytest

from app.utils.language import detect_language, is_hebrew


class TestDetectLanguage:
    """Tests for detect_language function."""

    def test_detect_hebrew_text(self) -> None:
        """Hebrew text should return 'he'."""
        assert detect_language("שלום עולם") == "he"

    def test_detect_english_text(self) -> None:
        """English text should return 'en'."""
        assert detect_language("Learn Python") == "en"

    def test_detect_mixed_hebrew_english(self) -> None:
        """Mixed text with Hebrew should return 'he'."""
        assert detect_language("ללמוד Python") == "he"

    def test_detect_empty_string(self) -> None:
        """Empty string should return 'en' (default)."""
        assert detect_language("") == "en"

    def test_detect_numbers_only(self) -> None:
        """Numbers only should return 'en' (default)."""
        assert detect_language("12345") == "en"

    def test_detect_single_hebrew_char(self) -> None:
        """Single Hebrew character should return 'he'."""
        assert detect_language("Learn א Python") == "he"

    def test_detect_hebrew_with_punctuation(self) -> None:
        """Hebrew with punctuation should return 'he'."""
        assert detect_language("שלום!") == "he"


class TestIsHebrew:
    """Tests for is_hebrew function."""

    def test_is_hebrew_true(self) -> None:
        """Hebrew text should return True."""
        assert is_hebrew("שלום") is True

    def test_is_hebrew_false(self) -> None:
        """English text should return False."""
        assert is_hebrew("hello") is False

    def test_is_hebrew_mixed(self) -> None:
        """Mixed text with Hebrew should return True."""
        assert is_hebrew("hello שלום") is True

    def test_is_hebrew_empty(self) -> None:
        """Empty string should return False."""
        assert is_hebrew("") is False

    def test_is_hebrew_only_spaces(self) -> None:
        """Spaces only should return False."""
        assert is_hebrew("   ") is False
