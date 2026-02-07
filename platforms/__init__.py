"""
Platform Adapters for Multi-Platform Social Automation

Provides a unified interface for posting content to various social media platforms.
"""
from platforms.base import PlatformAdapter
from platforms.tiktok.adapter import tiktok_adapter, TikTokAdapter
from platforms.instagram.adapter import instagram_adapter, InstagramAdapter
from platforms.youtube.adapter import youtube_adapter, YouTubeAdapter
from platforms.twitter.adapter import twitter_adapter, TwitterAdapter
from platforms.linkedin.adapter import linkedin_adapter, LinkedInAdapter
from core.models import Platform

# Registry of all available adapters
ADAPTERS = {
    Platform.TIKTOK: tiktok_adapter,
    Platform.INSTAGRAM: instagram_adapter,
    Platform.YOUTUBE: youtube_adapter,
    Platform.TWITTER: twitter_adapter,
    Platform.LINKEDIN: linkedin_adapter,
}


def get_adapter(platform: Platform) -> PlatformAdapter:
    """Get the adapter for a specific platform"""
    if platform not in ADAPTERS:
        raise ValueError(f"No adapter available for platform: {platform}")
    return ADAPTERS[platform]


def get_all_adapters() -> dict:
    """Get all available adapters"""
    return ADAPTERS.copy()


def get_authenticated_adapters() -> dict:
    """Get only adapters that are authenticated"""
    return {p: a for p, a in ADAPTERS.items() if a.is_authenticated}


__all__ = [
    "PlatformAdapter",
    "TikTokAdapter",
    "InstagramAdapter",
    "YouTubeAdapter",
    "TwitterAdapter",
    "LinkedInAdapter",
    "tiktok_adapter",
    "instagram_adapter",
    "youtube_adapter",
    "twitter_adapter",
    "linkedin_adapter",
    "get_adapter",
    "get_all_adapters",
    "get_authenticated_adapters",
    "ADAPTERS",
]
