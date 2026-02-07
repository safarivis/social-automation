"""
Core Pydantic Models for Multi-Platform Social Automation

Shared data models used across all platform adapters.
"""
from enum import Enum
from typing import List, Optional, Dict, Any
from pydantic import BaseModel, Field
from datetime import datetime


class Platform(str, Enum):
    """Supported social media platforms"""
    TIKTOK = "tiktok"
    INSTAGRAM = "instagram"
    YOUTUBE = "youtube"
    TWITTER = "twitter"  # X
    LINKEDIN = "linkedin"


class ContentType(str, Enum):
    """Types of content that can be created"""
    SHORT_VIDEO = "short_video"      # TikTok, Reels, Shorts
    LONG_VIDEO = "long_video"        # YouTube long-form
    IMAGE = "image"                  # Single image
    CAROUSEL = "carousel"            # Multiple images/slides
    TEXT = "text"                    # Text-only post
    DOCUMENT = "document"            # PDF/slides (LinkedIn)


class AspectRatio(str, Enum):
    """Video/image aspect ratios"""
    VERTICAL = "9:16"      # TikTok, Reels, Shorts
    PORTRAIT = "4:5"       # Instagram feed
    SQUARE = "1:1"         # Universal
    LANDSCAPE = "16:9"     # YouTube, LinkedIn
    WIDESCREEN = "21:9"    # Cinematic


class PlatformSpec(BaseModel):
    """Platform-specific content specifications"""
    platform: Platform
    content_types: List[ContentType]
    aspect_ratios: List[AspectRatio]
    min_duration: int = 0           # seconds
    max_duration: int = 60          # seconds
    max_caption_length: int = 2200  # characters
    max_hashtags: int = 30
    requires_business_account: bool = False
    api_name: str = ""


# Platform specifications
PLATFORM_SPECS: Dict[Platform, PlatformSpec] = {
    Platform.TIKTOK: PlatformSpec(
        platform=Platform.TIKTOK,
        content_types=[ContentType.SHORT_VIDEO],
        aspect_ratios=[AspectRatio.VERTICAL],
        min_duration=10,
        max_duration=60,
        max_caption_length=2200,
        max_hashtags=10,
        requires_business_account=False,
        api_name="Content Posting API"
    ),
    Platform.INSTAGRAM: PlatformSpec(
        platform=Platform.INSTAGRAM,
        content_types=[ContentType.SHORT_VIDEO, ContentType.IMAGE, ContentType.CAROUSEL],
        aspect_ratios=[AspectRatio.VERTICAL, AspectRatio.PORTRAIT, AspectRatio.SQUARE],
        min_duration=15,
        max_duration=90,
        max_caption_length=2200,
        max_hashtags=30,
        requires_business_account=True,
        api_name="Graph API"
    ),
    Platform.YOUTUBE: PlatformSpec(
        platform=Platform.YOUTUBE,
        content_types=[ContentType.SHORT_VIDEO, ContentType.LONG_VIDEO],
        aspect_ratios=[AspectRatio.VERTICAL, AspectRatio.LANDSCAPE],
        min_duration=15,
        max_duration=600,  # 10 min for long-form
        max_caption_length=5000,
        max_hashtags=15,
        requires_business_account=False,
        api_name="Data API v3"
    ),
    Platform.TWITTER: PlatformSpec(
        platform=Platform.TWITTER,
        content_types=[ContentType.TEXT, ContentType.IMAGE, ContentType.SHORT_VIDEO],
        aspect_ratios=[AspectRatio.LANDSCAPE, AspectRatio.SQUARE],
        min_duration=1,
        max_duration=140,
        max_caption_length=280,
        max_hashtags=5,
        requires_business_account=False,
        api_name="API v2"
    ),
    Platform.LINKEDIN: PlatformSpec(
        platform=Platform.LINKEDIN,
        content_types=[ContentType.TEXT, ContentType.IMAGE, ContentType.SHORT_VIDEO, ContentType.DOCUMENT],
        aspect_ratios=[AspectRatio.LANDSCAPE, AspectRatio.SQUARE],
        min_duration=3,
        max_duration=600,
        max_caption_length=3000,
        max_hashtags=5,
        requires_business_account=True,
        api_name="Marketing API"
    ),
}


class Product(BaseModel):
    """A product to promote across platforms"""
    asin: str = Field(description="Amazon ASIN or product ID")
    name: str = Field(description="Product name")
    price: float = Field(description="Product price in USD")
    currency: str = Field(default="USD")
    category: str = Field(description="Product category")
    affiliate_link: str = Field(description="Affiliate tracking link")
    image_url: Optional[str] = Field(default=None, description="Product image URL")

    # Analysis fields
    trend_score: int = Field(default=0, ge=0, le=100, description="Trend score 1-100")
    why_trending: str = Field(default="", description="Why this product is trending")
    content_angles: List[str] = Field(default_factory=list, description="Suggested content angles")
    target_platforms: List[Platform] = Field(default_factory=list, description="Best platforms for this product")

    # Metadata
    commission_rate: float = Field(default=0.04, description="Affiliate commission rate")
    discovered_at: datetime = Field(default_factory=datetime.now)


class VisualCue(BaseModel):
    """A visual direction for video editing"""
    timestamp: str = Field(description="Timestamp range, e.g., '0-3s'")
    description: str = Field(description="What to show on screen")
    footage_type: str = Field(description="Type: product_shot, b_roll, text_overlay, transition")


class ContentScript(BaseModel):
    """A script for a single piece of content"""
    product_name: str = Field(description="Product being promoted")
    platform: Platform = Field(description="Target platform")
    content_type: ContentType = Field(description="Type of content")

    # Script structure
    hook: str = Field(description="Opening hook - first 3 seconds")
    hook_variations: List[str] = Field(default_factory=list, description="Alternative hooks to test")
    problem: str = Field(description="Pain point setup")
    solution: str = Field(description="Product reveal and demo")
    cta: str = Field(description="Call to action")

    # Full content
    full_voiceover: str = Field(description="Complete voiceover text")
    duration_estimate: int = Field(description="Estimated duration in seconds")

    # Visual direction
    visuals: List[VisualCue] = Field(default_factory=list)

    # Posting metadata
    caption: str = Field(description="Post caption")
    hashtags: List[str] = Field(default_factory=list)

    # Generation prompt for AI video/image
    media_prompt: str = Field(description="Prompt for AI media generation")


class ContentPackage(BaseModel):
    """A complete content package ready for posting"""
    id: str = Field(description="Unique content ID")
    product: Product
    platform: Platform
    content_type: ContentType

    # Generated content
    script: ContentScript
    media_path: Optional[str] = Field(default=None, description="Local path to generated media")
    media_url: Optional[str] = Field(default=None, description="Remote URL of media")

    # Status
    status: str = Field(default="draft")  # draft, ready, posted, failed
    created_at: datetime = Field(default_factory=datetime.now)
    posted_at: Optional[datetime] = None
    post_id: Optional[str] = None  # Platform's post ID

    # Metadata
    metadata: Dict[str, Any] = Field(default_factory=dict)


class CampaignConfig(BaseModel):
    """Configuration for a content campaign"""
    id: str = Field(description="Campaign identifier")
    name: str = Field(description="Campaign name")
    niche: str = Field(description="Target niche (e.g., tech_gadgets)")

    # Research settings
    research_template: str = Field(default="affiliate", description="Research prompt template")
    price_range: tuple = Field(default=(15, 75), description="Min/max product price")
    products_per_run: int = Field(default=5)

    # Platform settings
    platforms: Dict[str, Dict[str, Any]] = Field(default_factory=dict)

    # Scheduling
    enabled: bool = True
    schedule: Optional[str] = None  # Cron expression


class ResearchConfig(BaseModel):
    """Configuration for product research"""
    template: str = Field(description="Template name (affiliate, trending, etc.)")
    niche: str = Field(description="Target niche")
    market: str = Field(default="US")
    price_min: float = Field(default=10.0)
    price_max: float = Field(default=75.0)
    count: int = Field(default=5)
    categories: List[str] = Field(default_factory=list)
    keywords: List[str] = Field(default_factory=list)
    content_angles: List[str] = Field(default_factory=list)
