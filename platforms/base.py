"""
Abstract Platform Adapter Base Class

Defines the interface that all platform adapters must implement.
"""
from abc import ABC, abstractmethod
from typing import Optional, Dict, Any, List
from pathlib import Path
import sys

sys.path.insert(0, str(Path(__file__).parent.parent))
from core.models import (
    Platform, ContentType, AspectRatio, PlatformSpec,
    ContentPackage, ContentScript, Product, PLATFORM_SPECS
)


class PlatformAdapter(ABC):
    """
    Abstract base class for platform-specific adapters.

    Each platform (TikTok, Instagram, YouTube, Twitter, LinkedIn)
    implements this interface to handle platform-specific content
    generation and posting.
    """

    def __init__(self):
        self._authenticated = False
        self._access_token: Optional[str] = None

    @property
    @abstractmethod
    def platform(self) -> Platform:
        """Return the platform this adapter handles"""
        pass

    @property
    def spec(self) -> PlatformSpec:
        """Get the platform specification"""
        return PLATFORM_SPECS[self.platform]

    @property
    def name(self) -> str:
        """Human-readable platform name"""
        return self.platform.value.title()

    @property
    def is_authenticated(self) -> bool:
        """Check if adapter has valid authentication"""
        return self._authenticated

    # =========================================================================
    # Authentication
    # =========================================================================

    @abstractmethod
    def authenticate(self, credentials: Dict[str, str]) -> bool:
        """
        Authenticate with the platform API.

        Args:
            credentials: Platform-specific credentials dict

        Returns:
            True if authentication successful
        """
        pass

    @abstractmethod
    def get_auth_url(self, redirect_uri: str) -> str:
        """
        Get OAuth authorization URL for user authentication.

        Args:
            redirect_uri: Callback URL after authorization

        Returns:
            URL to redirect user for OAuth
        """
        pass

    @abstractmethod
    def exchange_code(self, code: str, redirect_uri: str) -> Dict[str, str]:
        """
        Exchange authorization code for access token.

        Args:
            code: Authorization code from OAuth callback
            redirect_uri: Same redirect URI used in auth URL

        Returns:
            Dict with access_token and other credentials
        """
        pass

    # =========================================================================
    # Content Generation
    # =========================================================================

    @abstractmethod
    def get_script_instructions(self) -> str:
        """
        Get platform-specific script writing instructions.

        Returns:
            Instruction string for the script writer agent
        """
        pass

    @abstractmethod
    def get_supported_content_types(self) -> List[ContentType]:
        """
        Get content types this platform supports.

        Returns:
            List of supported ContentType enums
        """
        pass

    @abstractmethod
    def get_optimal_settings(self, content_type: ContentType) -> Dict[str, Any]:
        """
        Get optimal content settings for a content type.

        Args:
            content_type: Type of content to create

        Returns:
            Dict with duration, aspect_ratio, resolution, etc.
        """
        pass

    def validate_content(self, package: ContentPackage) -> List[str]:
        """
        Validate a content package against platform requirements.

        Args:
            package: Content package to validate

        Returns:
            List of validation errors (empty if valid)
        """
        errors = []
        spec = self.spec

        # Check content type
        if package.content_type not in spec.content_types:
            errors.append(
                f"Content type {package.content_type} not supported on {self.name}"
            )

        # Check caption length
        if len(package.script.caption) > spec.max_caption_length:
            errors.append(
                f"Caption too long: {len(package.script.caption)} > {spec.max_caption_length}"
            )

        # Check hashtags
        if len(package.script.hashtags) > spec.max_hashtags:
            errors.append(
                f"Too many hashtags: {len(package.script.hashtags)} > {spec.max_hashtags}"
            )

        # Check duration
        if package.script.duration_estimate < spec.min_duration:
            errors.append(
                f"Duration too short: {package.script.duration_estimate}s < {spec.min_duration}s"
            )
        if package.script.duration_estimate > spec.max_duration:
            errors.append(
                f"Duration too long: {package.script.duration_estimate}s > {spec.max_duration}s"
            )

        return errors

    # =========================================================================
    # Posting
    # =========================================================================

    @abstractmethod
    def post_content(self, package: ContentPackage) -> Dict[str, Any]:
        """
        Post content to the platform.

        Args:
            package: Complete content package with media

        Returns:
            Dict with post_id, status, url, etc.
        """
        pass

    @abstractmethod
    def upload_media(self, file_path: Path, content_type: ContentType) -> str:
        """
        Upload media file to platform.

        Args:
            file_path: Path to media file
            content_type: Type of content

        Returns:
            Media ID or URL from platform
        """
        pass

    def post_draft(self, package: ContentPackage) -> Dict[str, Any]:
        """
        Post content as draft (if platform supports it).

        Args:
            package: Content package

        Returns:
            Dict with draft_id, status, etc.
        """
        # Default: just mark as draft in response
        return {
            "status": "draft",
            "message": f"{self.name} draft mode not implemented"
        }

    # =========================================================================
    # Analytics (Optional)
    # =========================================================================

    def get_post_stats(self, post_id: str) -> Dict[str, Any]:
        """
        Get analytics for a posted content.

        Args:
            post_id: Platform-specific post ID

        Returns:
            Dict with views, likes, shares, etc.
        """
        return {"status": "not_implemented"}

    def get_account_stats(self) -> Dict[str, Any]:
        """
        Get account-level analytics.

        Returns:
            Dict with followers, engagement rate, etc.
        """
        return {"status": "not_implemented"}

    # =========================================================================
    # Utility Methods
    # =========================================================================

    def adapt_content_for_platform(
        self,
        script: ContentScript,
        source_platform: Platform
    ) -> ContentScript:
        """
        Adapt content from another platform for this platform.

        Args:
            script: Original script from source platform
            source_platform: Where the script was created for

        Returns:
            Adapted script for this platform
        """
        # Default: just update platform and basic fields
        adapted = script.model_copy()
        adapted.platform = self.platform

        # Truncate caption if needed
        max_len = self.spec.max_caption_length
        if len(adapted.caption) > max_len:
            adapted.caption = adapted.caption[:max_len - 3] + "..."

        # Limit hashtags
        max_tags = self.spec.max_hashtags
        if len(adapted.hashtags) > max_tags:
            adapted.hashtags = adapted.hashtags[:max_tags]

        return adapted

    def get_best_posting_times(self) -> List[str]:
        """
        Get optimal posting times for this platform.

        Returns:
            List of time strings in HH:MM format
        """
        from config.settings import get_platform_setting
        return get_platform_setting(
            self.platform.value,
            "optimal_posting_times",
            ["12:00"]
        )

    def __repr__(self) -> str:
        auth_status = "authenticated" if self.is_authenticated else "not authenticated"
        return f"<{self.__class__.__name__} ({self.name}, {auth_status})>"
