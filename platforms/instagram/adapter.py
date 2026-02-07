"""
Instagram Platform Adapter

Handles Instagram content via Facebook Graph API.
Supports Reels, Images, and Carousels.
"""
from typing import Dict, Any, List, Optional
from pathlib import Path
import json
import httpx
import sys

sys.path.insert(0, str(Path(__file__).parent.parent.parent))
from platforms.base import PlatformAdapter
from core.models import Platform, ContentType, ContentPackage, AspectRatio
from config.settings import (
    INSTAGRAM_ACCESS_TOKEN, FACEBOOK_APP_ID, FACEBOOK_APP_SECRET,
    get_platform_setting
)


class InstagramAdapter(PlatformAdapter):
    """Instagram platform adapter for Reels, Images, and Carousels"""

    def __init__(self):
        super().__init__()
        self.api_base = "https://graph.facebook.com/v18.0"
        self._access_token = INSTAGRAM_ACCESS_TOKEN
        self._ig_user_id: Optional[str] = None

        if self._access_token:
            self._authenticated = True

    @property
    def platform(self) -> Platform:
        return Platform.INSTAGRAM

    # =========================================================================
    # Authentication
    # =========================================================================

    def authenticate(self, credentials: Dict[str, str]) -> bool:
        """Authenticate with Instagram via Facebook"""
        self._access_token = credentials.get("access_token")
        self._ig_user_id = credentials.get("instagram_user_id")
        self._authenticated = bool(self._access_token and self._ig_user_id)
        return self._authenticated

    def get_auth_url(self, redirect_uri: str) -> str:
        """Get Facebook OAuth URL for Instagram"""
        scopes = (
            "instagram_basic,instagram_content_publish,"
            "pages_show_list,pages_read_engagement"
        )
        return (
            f"https://www.facebook.com/v18.0/dialog/oauth"
            f"?client_id={FACEBOOK_APP_ID}"
            f"&redirect_uri={redirect_uri}"
            f"&scope={scopes}"
            f"&response_type=code"
        )

    def exchange_code(self, code: str, redirect_uri: str) -> Dict[str, str]:
        """Exchange code for access token"""
        url = f"{self.api_base}/oauth/access_token"
        params = {
            "client_id": FACEBOOK_APP_ID,
            "client_secret": FACEBOOK_APP_SECRET,
            "redirect_uri": redirect_uri,
            "code": code,
        }

        try:
            response = httpx.get(url, params=params, timeout=30.0)
            response.raise_for_status()
            result = response.json()

            if "access_token" in result:
                self._access_token = result["access_token"]
                # Need to get Instagram user ID
                self._fetch_instagram_user_id()

            return result
        except httpx.HTTPError as e:
            return {"error": str(e)}

    def _fetch_instagram_user_id(self):
        """Fetch Instagram Business Account ID linked to Facebook Page"""
        if not self._access_token:
            return

        # Get pages
        pages_url = f"{self.api_base}/me/accounts?access_token={self._access_token}"
        try:
            response = httpx.get(pages_url, timeout=30.0)
            pages = response.json().get("data", [])

            if pages:
                page_id = pages[0]["id"]
                page_token = pages[0]["access_token"]

                # Get Instagram account linked to page
                ig_url = (
                    f"{self.api_base}/{page_id}"
                    f"?fields=instagram_business_account"
                    f"&access_token={page_token}"
                )
                ig_response = httpx.get(ig_url, timeout=30.0)
                ig_data = ig_response.json()

                if "instagram_business_account" in ig_data:
                    self._ig_user_id = ig_data["instagram_business_account"]["id"]
                    self._authenticated = True

        except httpx.HTTPError:
            pass

    # =========================================================================
    # Content Generation
    # =========================================================================

    def get_script_instructions(self) -> str:
        """Instagram-specific script writing instructions"""
        return """\
## Instagram Content Guidelines

### Reels (Primary Format)
- Duration: 15-90 seconds (sweet spot: 30-60s)
- Aspect ratio: 9:16 vertical
- Cover image matters for discovery

### Hook Strategies for Instagram
1. **Visual Hook**: Start with the most striking visual
2. **Text Overlay**: Bold statement in first frame
3. **Transformation**: Before/after reveal
4. **Tutorial Start**: "Here's how to..."
5. **Trend Participation**: Use trending audio/format

### Instagram-Specific Elements
- Trending audio is HUGE for reach
- Text overlays essential (many watch muted)
- Clean, aesthetic visuals preferred
- Smooth transitions > jump cuts
- Save-worthy content ranks higher

### Caption Guidelines
- Max 2200 characters (first 125 visible)
- Line breaks for readability
- Up to 30 hashtags (use 10-15 strategically)
- Mix hashtag sizes (big + niche)
- End with question for engagement

### Content Types
1. **Reels**: Short video, best for reach
2. **Carousel**: Multi-image, great for tutorials
3. **Single Image**: Product shots, quotes

### CTA Patterns
- "Save this for later" (boosts algorithm)
- "Share to your story"
- "Link in bio"
- "Double tap if you agree"
- "Comment your favorite"

### Aesthetic Notes
- Consistent color grading
- Clean backgrounds
- Good lighting is essential
- Professional but not overproduced
"""

    def get_supported_content_types(self) -> List[ContentType]:
        return [ContentType.SHORT_VIDEO, ContentType.IMAGE, ContentType.CAROUSEL]

    def get_optimal_settings(self, content_type: ContentType) -> Dict[str, Any]:
        if content_type == ContentType.SHORT_VIDEO:
            return {
                "duration": get_platform_setting("instagram", "default_duration", 15),
                "max_duration": 90,
                "aspect_ratio": AspectRatio.VERTICAL.value,
                "resolution": "1080p",
            }
        elif content_type == ContentType.IMAGE:
            return {
                "aspect_ratio": AspectRatio.PORTRAIT.value,  # 4:5
                "resolution": "1080x1350",
            }
        elif content_type == ContentType.CAROUSEL:
            return {
                "aspect_ratio": AspectRatio.PORTRAIT.value,
                "max_slides": 10,
                "resolution": "1080x1350",
            }
        return {}

    # =========================================================================
    # Posting
    # =========================================================================

    def upload_media(self, file_path: Path, content_type: ContentType) -> str:
        """Upload media to Instagram"""
        if not self._authenticated or not self._ig_user_id:
            return json.dumps({"error": "Not authenticated with Instagram"})

        # For videos, need to use video container endpoint
        if content_type == ContentType.SHORT_VIDEO:
            return self._upload_reel(file_path)
        else:
            return self._upload_image(file_path)

    def _upload_reel(self, file_path: Path) -> str:
        """Upload a Reel video"""
        # Step 1: Create media container
        url = f"{self.api_base}/{self._ig_user_id}/media"

        # Video must be hosted externally for Graph API
        # In production, upload to cloud storage first
        video_url = str(file_path)  # Would be cloud URL in production

        try:
            response = httpx.post(
                url,
                data={
                    "media_type": "REELS",
                    "video_url": video_url,
                    "access_token": self._access_token,
                },
                timeout=60.0
            )
            result = response.json()
            return json.dumps({
                "status": "created",
                "container_id": result.get("id"),
            })
        except httpx.HTTPError as e:
            return json.dumps({"error": str(e)})

    def _upload_image(self, file_path: Path) -> str:
        """Upload a single image"""
        url = f"{self.api_base}/{self._ig_user_id}/media"

        try:
            response = httpx.post(
                url,
                data={
                    "image_url": str(file_path),  # Would be cloud URL
                    "access_token": self._access_token,
                },
                timeout=60.0
            )
            result = response.json()
            return json.dumps({
                "status": "created",
                "container_id": result.get("id"),
            })
        except httpx.HTTPError as e:
            return json.dumps({"error": str(e)})

    def post_content(self, package: ContentPackage) -> Dict[str, Any]:
        """Post content to Instagram"""
        if not self._authenticated or not self._ig_user_id:
            return {"error": "Not authenticated with Instagram"}

        if not package.media_path:
            return {"error": "No media file to upload"}

        # Upload media first
        upload_result = json.loads(
            self.upload_media(Path(package.media_path), package.content_type)
        )

        if "error" in upload_result:
            return upload_result

        container_id = upload_result.get("container_id")

        # Publish the container
        publish_url = f"{self.api_base}/{self._ig_user_id}/media_publish"

        try:
            response = httpx.post(
                publish_url,
                data={
                    "creation_id": container_id,
                    "caption": f"{package.script.caption}\n\n{' '.join(package.script.hashtags)}",
                    "access_token": self._access_token,
                },
                timeout=60.0
            )

            result = response.json()
            return {
                "status": "posted",
                "post_id": result.get("id"),
                "platform": "instagram",
            }

        except httpx.HTTPError as e:
            return {"error": str(e), "container_id": container_id}

    # =========================================================================
    # Analytics
    # =========================================================================

    def get_post_stats(self, post_id: str) -> Dict[str, Any]:
        """Get post insights"""
        if not self._authenticated:
            return {"error": "Not authenticated"}

        url = (
            f"{self.api_base}/{post_id}/insights"
            f"?metric=impressions,reach,engagement"
            f"&access_token={self._access_token}"
        )

        try:
            response = httpx.get(url, timeout=30.0)
            return response.json()
        except httpx.HTTPError as e:
            return {"error": str(e)}


# Create default instance
instagram_adapter = InstagramAdapter()
