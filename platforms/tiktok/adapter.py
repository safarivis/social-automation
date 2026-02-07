"""
TikTok Platform Adapter

Handles TikTok-specific content generation and posting via Content Posting API.
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
    TIKTOK_CLIENT_KEY, TIKTOK_CLIENT_SECRET, TIKTOK_ACCESS_TOKEN,
    get_platform_setting
)


class TikTokAdapter(PlatformAdapter):
    """TikTok platform adapter for short-form video content"""

    def __init__(self):
        super().__init__()
        self.api_base = "https://open.tiktokapis.com/v2"
        self.client_key = TIKTOK_CLIENT_KEY
        self.client_secret = TIKTOK_CLIENT_SECRET
        self._access_token = TIKTOK_ACCESS_TOKEN

        if self._access_token:
            self._authenticated = True

    @property
    def platform(self) -> Platform:
        return Platform.TIKTOK

    # =========================================================================
    # Authentication
    # =========================================================================

    def authenticate(self, credentials: Dict[str, str]) -> bool:
        """Authenticate with TikTok API"""
        self._access_token = credentials.get("access_token")
        self.client_key = credentials.get("client_key", self.client_key)
        self.client_secret = credentials.get("client_secret", self.client_secret)
        self._authenticated = bool(self._access_token)
        return self._authenticated

    def get_auth_url(self, redirect_uri: str) -> str:
        """Get TikTok OAuth URL"""
        scopes = "user.info.basic,video.publish,video.upload"
        return (
            f"https://www.tiktok.com/v2/auth/authorize/"
            f"?client_key={self.client_key}"
            f"&scope={scopes}"
            f"&response_type=code"
            f"&redirect_uri={redirect_uri}"
        )

    def exchange_code(self, code: str, redirect_uri: str) -> Dict[str, str]:
        """Exchange authorization code for access token"""
        url = "https://open.tiktokapis.com/v2/oauth/token/"
        data = {
            "client_key": self.client_key,
            "client_secret": self.client_secret,
            "code": code,
            "grant_type": "authorization_code",
            "redirect_uri": redirect_uri,
        }

        try:
            response = httpx.post(url, data=data, timeout=30.0)
            response.raise_for_status()
            result = response.json()

            if "access_token" in result:
                self._access_token = result["access_token"]
                self._authenticated = True

            return result
        except httpx.HTTPError as e:
            return {"error": str(e)}

    # =========================================================================
    # Content Generation
    # =========================================================================

    def get_script_instructions(self) -> str:
        """TikTok-specific script writing instructions"""
        return """\
## TikTok Script Guidelines

### Format
- Duration: 10-60 seconds (sweet spot: 15-30s)
- Aspect ratio: 9:16 vertical
- Front-load the hook in first 3 seconds

### Hook Types That Work on TikTok
1. **Curiosity**: "I didn't believe this would work..."
2. **Controversy**: "Everyone's buying the wrong version"
3. **Bold Claim**: "This $20 thing replaced my $200 one"
4. **Pattern Interrupt**: Start mid-action, unexpected visual
5. **POV**: "POV: You finally found the thing that works"

### TikTok-Specific Elements
- Use trending sounds/music cues in script
- Include text overlay suggestions
- Fast cuts, no dead air
- End with a hook to rewatch or comment

### Caption Guidelines
- Max 2200 characters
- First line is preview (keep punchy)
- 3-5 relevant hashtags (not more)
- Mix broad (#tiktokmademebuyit) and niche tags

### CTA Patterns
- "Link in bio" (for affiliate)
- "Save this for later"
- "Comment LINK"
- "Follow for more"
"""

    def get_supported_content_types(self) -> List[ContentType]:
        return [ContentType.SHORT_VIDEO]

    def get_optimal_settings(self, content_type: ContentType) -> Dict[str, Any]:
        return {
            "duration": get_platform_setting("tiktok", "default_duration", 10),
            "max_duration": get_platform_setting("tiktok", "max_duration", 60),
            "aspect_ratio": AspectRatio.VERTICAL.value,
            "resolution": get_platform_setting("tiktok", "resolution", "720p"),
        }

    # =========================================================================
    # Posting
    # =========================================================================

    def upload_media(self, file_path: Path, content_type: ContentType) -> str:
        """Upload video to TikTok"""
        if not self._authenticated:
            raise RuntimeError("Not authenticated with TikTok")

        # Step 1: Initialize upload
        init_url = f"{self.api_base}/post/publish/video/init/"
        headers = {
            "Authorization": f"Bearer {self._access_token}",
            "Content-Type": "application/json",
        }

        file_size = file_path.stat().st_size
        init_data = {
            "post_info": {
                "title": "Video upload",
                "privacy_level": "SELF_ONLY",  # Draft mode
            },
            "source_info": {
                "source": "FILE_UPLOAD",
                "video_size": file_size,
                "chunk_size": file_size,
                "total_chunk_count": 1,
            }
        }

        try:
            response = httpx.post(
                init_url,
                headers=headers,
                json=init_data,
                timeout=30.0
            )
            response.raise_for_status()
            init_result = response.json()

            upload_url = init_result.get("data", {}).get("upload_url")
            publish_id = init_result.get("data", {}).get("publish_id")

            if not upload_url:
                return json.dumps({"error": "No upload URL returned"})

            # Step 2: Upload video chunk
            with open(file_path, "rb") as f:
                video_data = f.read()

            upload_response = httpx.put(
                upload_url,
                content=video_data,
                headers={
                    "Content-Type": "video/mp4",
                    "Content-Range": f"bytes 0-{file_size - 1}/{file_size}",
                },
                timeout=120.0
            )

            return json.dumps({
                "status": "uploaded",
                "publish_id": publish_id,
            })

        except httpx.HTTPError as e:
            return json.dumps({"error": str(e)})

    def post_content(self, package: ContentPackage) -> Dict[str, Any]:
        """Post content to TikTok"""
        if not self._authenticated:
            return {"error": "Not authenticated with TikTok"}

        if not package.media_path:
            return {"error": "No media file to upload"}

        # Upload the video
        upload_result = json.loads(
            self.upload_media(Path(package.media_path), package.content_type)
        )

        if "error" in upload_result:
            return upload_result

        publish_id = upload_result.get("publish_id")

        # Update post details
        url = f"{self.api_base}/post/publish/status/fetch/"
        headers = {
            "Authorization": f"Bearer {self._access_token}",
            "Content-Type": "application/json",
        }

        try:
            # Poll for publish status
            response = httpx.post(
                url,
                headers=headers,
                json={"publish_id": publish_id},
                timeout=30.0
            )

            result = response.json()
            return {
                "status": "posted",
                "publish_id": publish_id,
                "platform": "tiktok",
                "result": result,
            }

        except httpx.HTTPError as e:
            return {"error": str(e), "publish_id": publish_id}

    def post_draft(self, package: ContentPackage) -> Dict[str, Any]:
        """Post as draft (privacy: SELF_ONLY)"""
        # TikTok draft is handled by setting privacy_level to SELF_ONLY
        return self.post_content(package)

    # =========================================================================
    # Analytics
    # =========================================================================

    def get_post_stats(self, post_id: str) -> Dict[str, Any]:
        """Get video analytics"""
        if not self._authenticated:
            return {"error": "Not authenticated"}

        url = f"{self.api_base}/video/query/"
        headers = {"Authorization": f"Bearer {self._access_token}"}

        try:
            response = httpx.post(
                url,
                headers=headers,
                json={"filters": {"video_ids": [post_id]}},
                timeout=30.0
            )
            return response.json()
        except httpx.HTTPError as e:
            return {"error": str(e)}


# Create default instance
tiktok_adapter = TikTokAdapter()
