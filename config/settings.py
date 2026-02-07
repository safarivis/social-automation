"""
Configuration Settings for Multi-Platform Social Automation

Centralizes API keys, paths, and model configuration for all platforms.
"""
import os
from pathlib import Path
from dotenv import load_dotenv

# Load environment variables from ~/Agents/.env
env_path = Path.home() / "Agents" / ".env"
load_dotenv(env_path)

# =============================================================================
# API Keys
# =============================================================================

# xAI / Grok
XAI_API_KEY = os.getenv("XAI_API_KEY")

# TikTok
TIKTOK_CLIENT_KEY = os.getenv("TIKTOK_CLIENT_KEY")
TIKTOK_CLIENT_SECRET = os.getenv("TIKTOK_CLIENT_SECRET")
TIKTOK_ACCESS_TOKEN = os.getenv("TIKTOK_ACCESS_TOKEN")

# Instagram / Facebook
INSTAGRAM_ACCESS_TOKEN = os.getenv("INSTAGRAM_ACCESS_TOKEN")
FACEBOOK_APP_ID = os.getenv("FACEBOOK_APP_ID")
FACEBOOK_APP_SECRET = os.getenv("FACEBOOK_APP_SECRET")

# YouTube / Google
YOUTUBE_API_KEY = os.getenv("YOUTUBE_API_KEY")
GOOGLE_CLIENT_ID = os.getenv("GOOGLE_CLIENT_ID")
GOOGLE_CLIENT_SECRET = os.getenv("GOOGLE_CLIENT_SECRET")

# Twitter / X
TWITTER_API_KEY = os.getenv("TWITTER_API_KEY")
TWITTER_API_SECRET = os.getenv("TWITTER_API_SECRET")
TWITTER_ACCESS_TOKEN = os.getenv("TWITTER_ACCESS_TOKEN")
TWITTER_ACCESS_SECRET = os.getenv("TWITTER_ACCESS_SECRET")
TWITTER_BEARER_TOKEN = os.getenv("TWITTER_BEARER_TOKEN")

# LinkedIn
LINKEDIN_CLIENT_ID = os.getenv("LINKEDIN_CLIENT_ID")
LINKEDIN_CLIENT_SECRET = os.getenv("LINKEDIN_CLIENT_SECRET")
LINKEDIN_ACCESS_TOKEN = os.getenv("LINKEDIN_ACCESS_TOKEN")
LINKEDIN_PERSON_URN = os.getenv("LINKEDIN_PERSON_URN")

# Amazon Affiliate
AMAZON_AFFILIATE_TAG = os.getenv("AMAZON_AFFILIATE_TAG", "yourtag-20")
AMAZON_ACCESS_KEY = os.getenv("AMAZON_ACCESS_KEY")
AMAZON_SECRET_KEY = os.getenv("AMAZON_SECRET_KEY")

# =============================================================================
# Model Configuration
# =============================================================================

GROK_TEXT_MODEL = "grok-4-latest"  # For scripts and analysis
GROK_VIDEO_MODEL = "grok-imagine-video"  # For video generation
GROK_IMAGE_MODEL = "grok-imagine"  # For image generation

# Model selection by task
MODEL_CONFIG = {
    "research": GROK_TEXT_MODEL,      # Product research
    "script": GROK_TEXT_MODEL,        # Script writing
    "analysis": GROK_TEXT_MODEL,      # Content analysis
    "video": GROK_VIDEO_MODEL,        # Video generation
    "image": GROK_IMAGE_MODEL,        # Image generation
}

# =============================================================================
# Project Paths
# =============================================================================

PROJECT_ROOT = Path(__file__).parent.parent
CONFIG_DIR = PROJECT_ROOT / "config"
PROMPTS_DIR = CONFIG_DIR / "prompts"
DATA_DIR = PROJECT_ROOT / "data"
PRODUCTS_DIR = DATA_DIR / "products"
SCRIPTS_DIR = DATA_DIR / "scripts"
VIDEOS_DIR = DATA_DIR / "videos"
CAMPAIGNS_DIR = PROJECT_ROOT / "campaigns"
DB_FILE = DATA_DIR / "social_automation.db"

# Ensure directories exist
for dir_path in [DATA_DIR, PRODUCTS_DIR, SCRIPTS_DIR, VIDEOS_DIR, CAMPAIGNS_DIR]:
    dir_path.mkdir(parents=True, exist_ok=True)

# =============================================================================
# Target Markets
# =============================================================================

TARGET_MARKETS = ["US", "UK", "CA", "AU"]
DEFAULT_MARKET = "US"

# =============================================================================
# Content Categories
# =============================================================================

CONTENT_CATEGORIES = [
    "electronics",
    "beauty",
    "home-garden",
    "kitchen",
    "toys-games",
    "sports-outdoors",
    "fashion",
    "tech-gadgets",
]

# =============================================================================
# Platform-Specific Settings
# =============================================================================

PLATFORM_SETTINGS = {
    "tiktok": {
        "default_duration": 10,
        "max_duration": 60,
        "aspect_ratio": "9:16",
        "resolution": "720p",
        "posts_per_day": 3,
        "optimal_posting_times": ["09:00", "12:00", "19:00"],  # Local time
    },
    "instagram": {
        "default_duration": 15,
        "max_duration": 90,
        "aspect_ratio": "9:16",  # Reels
        "resolution": "1080p",
        "posts_per_day": 2,
        "optimal_posting_times": ["11:00", "13:00", "19:00"],
    },
    "youtube": {
        "default_duration": 15,  # Shorts
        "max_duration": 60,      # Shorts max
        "aspect_ratio": "9:16",  # Shorts
        "resolution": "1080p",
        "posts_per_day": 2,
        "optimal_posting_times": ["14:00", "17:00"],
    },
    "twitter": {
        "default_duration": 30,
        "max_duration": 140,
        "aspect_ratio": "16:9",
        "resolution": "720p",
        "posts_per_day": 5,
        "optimal_posting_times": ["08:00", "12:00", "17:00", "21:00"],
    },
    "linkedin": {
        "default_duration": 30,
        "max_duration": 600,
        "aspect_ratio": "16:9",
        "resolution": "1080p",
        "posts_per_day": 1,
        "optimal_posting_times": ["07:00", "12:00", "17:00"],
    },
}

# =============================================================================
# Scheduling
# =============================================================================

DAILY_RUN_TIME = "08:00"  # Default daily run time
VIDEOS_PER_BATCH = 5

# =============================================================================
# Video Generation Settings
# =============================================================================

VIDEO_SETTINGS = {
    "default_duration": 10,
    "max_duration": 15,  # Grok limit
    "poll_interval": 5,  # seconds between status checks
    "max_wait": 180,     # max seconds to wait for generation
}

# =============================================================================
# Helper Functions
# =============================================================================

def get_platform_setting(platform: str, key: str, default=None):
    """Get a setting for a specific platform"""
    settings = PLATFORM_SETTINGS.get(platform.lower(), {})
    return settings.get(key, default)

def is_platform_configured(platform: str) -> bool:
    """Check if a platform has required API credentials configured"""
    platform = platform.lower()

    if platform == "tiktok":
        return bool(TIKTOK_CLIENT_KEY and TIKTOK_CLIENT_SECRET)
    elif platform == "instagram":
        return bool(INSTAGRAM_ACCESS_TOKEN or (FACEBOOK_APP_ID and FACEBOOK_APP_SECRET))
    elif platform == "youtube":
        return bool(GOOGLE_CLIENT_ID and GOOGLE_CLIENT_SECRET)
    elif platform == "twitter":
        return bool(TWITTER_BEARER_TOKEN or (TWITTER_API_KEY and TWITTER_API_SECRET))
    elif platform == "linkedin":
        return bool(LINKEDIN_CLIENT_ID and LINKEDIN_CLIENT_SECRET)

    return False

def get_configured_platforms() -> list:
    """Get list of platforms that have credentials configured"""
    platforms = ["tiktok", "instagram", "youtube", "twitter", "linkedin"]
    return [p for p in platforms if is_platform_configured(p)]
