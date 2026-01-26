"""Tests for LLM model configuration."""

import pytest

from app.model_config import (
    AGENT_MODELS,
    GeminiModel,
    ModelConfig,
    get_model_config,
)


class TestGeminiModel:
    """Tests for GeminiModel enum."""

    def test_flash_lite_value(self):
        assert GeminiModel.FLASH_LITE.value == "gemini-2.5-flash-lite"

    def test_flash_value(self):
        assert GeminiModel.FLASH.value == "gemini-2.5-flash"

    def test_flash_2_0_value(self):
        assert GeminiModel.FLASH_2_0.value == "gemini-2.0-flash"


class TestModelConfig:
    """Tests for ModelConfig class."""

    def test_config_has_all_fields(self):
        config = ModelConfig(
            model=GeminiModel.FLASH,
            temperature=0.7,
            max_tokens=4096,
            reason="Test reason",
        )
        assert config.model == GeminiModel.FLASH
        assert config.temperature == 0.7
        assert config.max_tokens == 4096
        assert config.reason == "Test reason"


class TestAgentModels:
    """Tests for AGENT_MODELS configuration."""

    def test_interviewer_uses_flash_lite(self):
        config = AGENT_MODELS["interviewer"]
        assert config.model == GeminiModel.FLASH_LITE

    def test_architect_uses_flash(self):
        config = AGENT_MODELS["architect"]
        assert config.model == GeminiModel.FLASH

    def test_researcher_uses_flash(self):
        config = AGENT_MODELS["researcher"]
        assert config.model == GeminiModel.FLASH

    def test_validator_uses_flash_lite(self):
        config = AGENT_MODELS["validator"]
        assert config.model == GeminiModel.FLASH_LITE

    def test_youtube_query_uses_flash_lite(self):
        config = AGENT_MODELS["youtube_query"]
        assert config.model == GeminiModel.FLASH_LITE

    def test_youtube_grounding_uses_flash_2_0(self):
        """Grounding requires 2.0 until 2.5 is verified."""
        config = AGENT_MODELS["youtube_grounding"]
        assert config.model == GeminiModel.FLASH_2_0

    def test_chat_uses_flash(self):
        config = AGENT_MODELS["chat"]
        assert config.model == GeminiModel.FLASH

    def test_all_configs_have_reasons(self):
        """Every config should document why that model was chosen."""
        for name, config in AGENT_MODELS.items():
            assert config.reason, f"Config '{name}' missing reason"
            assert len(config.reason) > 10, f"Config '{name}' has too short reason"


class TestGetModelConfig:
    """Tests for get_model_config function."""

    def test_returns_correct_config(self):
        config = get_model_config("interviewer")
        assert config.model == GeminiModel.FLASH_LITE

    def test_unknown_agent_falls_back_to_researcher(self):
        config = get_model_config("unknown_agent")
        assert config == AGENT_MODELS["researcher"]

    def test_returns_model_config_instance(self):
        config = get_model_config("chat")
        assert isinstance(config, ModelConfig)
