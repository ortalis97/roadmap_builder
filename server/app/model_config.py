"""LLM model configuration for all agents and services.

Centralizes model assignments for easy cost control and documentation.
Each agent/service has a specific model config with justification.
"""

from enum import Enum

# Global switch to disable all token limits for debugging truncation issues.
# When True, all agents pass max_output_tokens=None to the Gemini API.
# Usage: Temporarily set to True when investigating truncated content.
UNLIMITED_TOKENS = False

# Concurrency and retry configuration for Gemini API calls.
# Prevents connection drops from too many parallel requests.
MAX_CONCURRENT_API_CALLS = 5  # Max parallel Gemini API requests

# Network error retry settings with exponential backoff.
NETWORK_RETRY_ATTEMPTS = 3  # Number of retry attempts for network errors
NETWORK_RETRY_BASE_DELAY = 1.0  # Initial delay in seconds (doubles each retry)
NETWORK_RETRY_MAX_DELAY = 30.0  # Maximum delay between retries


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
# NOTE: Currently all using FLASH_2_0 to match original behavior.
# Other models (FLASH_LITE, FLASH) kept in enum for future experimentation.
AGENT_MODELS: dict[str, ModelConfig] = {
    # Pipeline agents - all use original base.py defaults (0.7 temp, 8192 tokens)
    "interviewer": ModelConfig(
        GeminiModel.FLASH,
        0.7,
        8192,
        "Simple Q&A generation",
    ),
    "architect": ModelConfig(
        GeminiModel.FLASH,
        0.7,
        8192,
        "Curriculum design",
    ),
    "researcher": ModelConfig(
        GeminiModel.FLASH_2_0,
        0.7,
        12288,
        "Educational content generation",
    ),
    "validator": ModelConfig(
        GeminiModel.FLASH_2_0,
        0.7,
        12288,
        "Quality validation",
    ),
    # Editor agent for surgical content fixes
    "editor": ModelConfig(
        GeminiModel.FLASH,
        0.5,  # Lower temperature for more consistent edits
        12288,
        "Surgical content editing",
    ),
    "editor_research": ModelConfig(
        GeminiModel.FLASH_LITE,
        0.7,
        4096,  # Smaller output for targeted sections
        "Gap-filling research sections",
    ),
    # YouTube agent operations - use original youtube.py defaults (0.3 temp, 4096 tokens)
    "youtube_query": ModelConfig(
        GeminiModel.FLASH_LITE,
        0.3,
        4096,
        "YouTube search query generation",
    ),
    "youtube_rerank": ModelConfig(
        GeminiModel.FLASH_LITE,
        0.3,
        4096,
        "Video re-ranking selection",
    ),
    "youtube_grounding": ModelConfig(
        GeminiModel.FLASH_LITE,
        0.3,
        4096,
        "Google Search grounding for video discovery",
    ),
    # Chat service
    "chat": ModelConfig(
        GeminiModel.FLASH_LITE,
        0.7,
        8192,
        "User-facing chat",
    ),
    # Legacy roadmap generation (ai_service.py)
    "roadmap_generation": ModelConfig(
        GeminiModel.FLASH_2_0,
        0.7,
        8192,
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
