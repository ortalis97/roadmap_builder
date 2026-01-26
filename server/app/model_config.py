"""LLM model configuration for all agents and services.

Centralizes model assignments for easy cost control and documentation.
Each agent/service has a specific model config with justification.
"""

from enum import Enum


class GeminiModel(str, Enum):
    """Available Gemini models."""

    FLASH_LITE = "gemini-2.5-flash-lite"  # Fast, cheapest
    FLASH = "gemini-2.5-flash"  # Balanced cost/quality
    FLASH_2_0 = "gemini-2.0-flash"  # Legacy (required for grounding)


class ModelConfig:
    """Model configuration with documentation."""

    def __init__(
        self,
        model: GeminiModel,
        temperature: float,
        max_tokens: int,
        reason: str,
    ):
        self.model = model
        self.temperature = temperature
        self.max_tokens = max_tokens
        self.reason = reason


# Agent/service model assignments with justification
AGENT_MODELS: dict[str, ModelConfig] = {
    # Pipeline agents
    "interviewer": ModelConfig(
        GeminiModel.FLASH_LITE,
        0.7,
        3072,
        "Simple Q&A generation, low complexity",
    ),
    "architect": ModelConfig(
        GeminiModel.FLASH,
        0.7,
        6144,
        "Curriculum design requires logical reasoning",
    ),
    "researcher": ModelConfig(
        GeminiModel.FLASH,
        0.7,
        12288,
        "Educational content quality matters",
    ),
    "validator": ModelConfig(
        GeminiModel.FLASH_LITE,
        0.3,
        3072,
        "Rule-based checking, consistency preferred",
    ),
    # YouTube agent operations
    "youtube_query": ModelConfig(
        GeminiModel.FLASH_LITE,
        0.3,
        1536,
        "Simple query generation",
    ),
    "youtube_rerank": ModelConfig(
        GeminiModel.FLASH_LITE,
        0.3,
        2048,
        "Video selection task",
    ),
    "youtube_grounding": ModelConfig(
        GeminiModel.FLASH_2_0,
        0.3,
        6144,
        "Google Search grounding - keep 2.0 until 2.5 verified",
    ),
    # Chat service
    "chat": ModelConfig(
        GeminiModel.FLASH,
        0.7,
        8192,
        "User-facing chat, quality matters",
    ),
    # Legacy roadmap generation (ai_service.py)
    "roadmap_generation": ModelConfig(
        GeminiModel.FLASH,
        0.7,
        12288,
        "Legacy roadmap generation endpoint",
    ),
}


def get_model_config(agent_name: str) -> ModelConfig:
    """Get model configuration for an agent.

    Args:
        agent_name: Name of the agent or service

    Returns:
        ModelConfig for the agent. Falls back to researcher config if not found.
    """
    return AGENT_MODELS.get(agent_name, AGENT_MODELS["researcher"])
