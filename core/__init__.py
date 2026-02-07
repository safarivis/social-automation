"""
Core Components for Multi-Platform Social Automation
"""
from core.models import (
    Platform,
    ContentType,
    AspectRatio,
    PlatformSpec,
    PLATFORM_SPECS,
    Product,
    VisualCue,
    ContentScript,
    ContentPackage,
    CampaignConfig,
    ResearchConfig,
)
from core.base_agents import (
    PromptLoader,
    prompt_loader,
    create_agent,
    ConfigurableAgent,
)

__all__ = [
    # Models
    "Platform",
    "ContentType",
    "AspectRatio",
    "PlatformSpec",
    "PLATFORM_SPECS",
    "Product",
    "VisualCue",
    "ContentScript",
    "ContentPackage",
    "CampaignConfig",
    "ResearchConfig",
    # Agent utilities
    "PromptLoader",
    "prompt_loader",
    "create_agent",
    "ConfigurableAgent",
]
