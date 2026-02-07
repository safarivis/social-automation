"""
YouTube Platform Adapter

Handles YouTube content via Data API v3.
Supports Shorts and regular videos.
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
    YOUTUBE_API_KEY, GOOGLE_CLIENT_ID, GOOGLE_CLIENT_SECRET,
    get_platform_setting
)


class YouTubeAdapter(PlatformAdapter):
    """YouTube platform adapter for Shorts and regular videos"""

    def __init__(self):
        super().__init__()
        self.api_base = "https://www.googleapis.com/youtube/v3"
        self.upload_base = "https://www.googleapis.com/upload/youtube/v3"
        self._access_token: Optional[str] = None
        self._refresh_token: Optional[str] = None

    @property
    def platform(self) -> Platform:
        return Platform.YOUTUBE

    # =========================================================================
    # Authentication
    # =========================================================================

    def authenticate(self, credentials: Dict[str, str]) -> bool:
        """Authenticate with YouTube"""
        self._access_token = credentials.get("access_token")
        self._refresh_token = credentials.get("refresh_token")
        self._authenticated = bool(self._access_token)
        return self._authenticated

    def get_auth_url(self, redirect_uri: str) -> str:
        """Get Google OAuth URL for YouTube"""
        scopes = (
            "https://www.googleapis.com/auth/youtube.upload "
            "https://www.googleapis.com/auth/youtube"
        )
        return (
            f"https://accounts.google.com/o/oauth2/v2/auth"
            f"?client_id={GOOGLE_CLIENT_ID}"
            f"&redirect_uri={redirect_uri}"
            f"&response_type=code"
            f"&scope={scopes}"
            f"&access_type=offline"
            f"&prompt=consent"
        )

    def exchange_code(self, code: str, redirect_uri: str) -> Dict[str, str]:
        """Exchange code for access token"""
        url = "https://oauth2.googleapis.com/token"
        data = {
            "client_id": GOOGLE_CLIENT_ID,
            "client_secret": GOOGLE_CLIENT_SECRET,
            "code": code,
            "redirect_uri": redirect_uri,
            "grant_type": "authorization_code",
        }

        try:
            response = httpx.post(url, data=data, timeout=30.0)
            response.raise_for_status()
            result = response.json()

            if "access_token" in result:
                self._access_token = result["access_token"]
                self._refresh_token = result.get("refresh_token")
                self._authenticated = True

            return result
        except httpx.HTTPError as e:
            return {"error": str(e)}

    def _refresh_access_token(self) -> bool:
        """Refresh the access token"""
        if not self._refresh_token:
            return False

        url = "https://oauth2.googleapis.com/token"
        data = {
            "client_id": GOOGLE_CLIENT_ID,
            "client_secret": GOOGLE_CLIENT_SECRET,
            "refresh_token": self._refresh_token,
            "grant_type": "refresh_token",
        }

        try:
            response = httpx.post(url, data=data, timeout=30.0)
            result = response.json()
            if "access_token" in result:
                self._access_token = result["access_token"]
                return True
        except httpx.HTTPError:
            pass

        return False

    # =========================================================================
    # Content Generation
    # =========================================================================

    def get_script_instructions(self) -> str:
        """YouTube-specific script writing instructions"""
        return """\
## YouTube Content Guidelines

### YouTube Shorts
- Duration: 15-60 seconds (exactly)
- Aspect ratio: 9:16 vertical
- Use #Shorts in title or description

### YouTube Shorts Hooks
1. **Thumbnail Hook**: First frame must be compelling
2. **Question Start**: "Did you know...?"
3. **Number Hook**: "3 things you're doing wrong"
4. **Shock Value**: Unexpected visual or statement
5. **Result Preview**: Show end result first

### YouTube-Specific Elements
- Title is crucial for search
- Description should include keywords
- Tags still matter for discoverability
- End screen / cards for longer videos
- Chapters for long-form content

### Shorts vs Regular Video
**Shorts:**
- Vertical 9:16
- Under 60 seconds
- Quick entertainment/tips
- Less production required

**Regular Videos:**
- Horizontal 16:9
- Longer, more detailed
- Higher production value
- More ad revenue potential

### Title Guidelines
- Include main keyword
- Add numbers when possible
- Create curiosity gap
- Keep under 60 characters
- Use | for separators

### Description Guidelines
- First 100 chars are preview
- Include links (affiliate)
- Add timestamps for long videos
- Use 3-5 relevant hashtags
- Include call to action

### CTA Patterns
- "Subscribe and hit the bell"
- "Check link in description"
- "Comment your thoughts"
- "Watch next video (end screen)"

### Tags/Keywords
- Use 10-15 relevant tags
- Mix broad and specific
- Include product names
- Add related searches
"""

    def get_supported_content_types(self) -> List[ContentType]:
        return [ContentType.SHORT_VIDEO, ContentType.LONG_VIDEO]

    def get_optimal_settings(self, content_type: ContentType) -> Dict[str, Any]:
        if content_type == ContentType.SHORT_VIDEO:
            return {
                "duration": 15,
                "max_duration": 60,
                "aspect_ratio": AspectRatio.VERTICAL.value,
                "resolution": "1080p",
                "is_short": True,
            }
        else:  # LONG_VIDEO
            return {
                "duration": 600,  # 10 min default
                "max_duration": 3600,  # 1 hour
                "aspect_ratio": AspectRatio.LANDSCAPE.value,
                "resolution": "1080p",
                "is_short": False,
            }

    # =========================================================================
    # Posting
    # =========================================================================

    def upload_media(self, file_path: Path, content_type: ContentType) -> str:
        """Upload video to YouTube"""
        if not self._authenticated:
            return json.dumps({"error": "Not authenticated with YouTube"})

        file_size = file_path.stat().st_size

        # Step 1: Initialize resumable upload
        init_url = f"{self.upload_base}/videos?uploadType=resumable&part=snippet,status"
        headers = {
            "Authorization": f"Bearer {self._access_token}",
            "Content-Type": "application/json",
            "X-Upload-Content-Length": str(file_size),
            "X-Upload-Content-Type": "video/mp4",
        }

        # Placeholder metadata (will be updated on post)
        metadata = {
            "snippet": {
                "title": "Video upload",
                "description": "Uploading...",
                "categoryId": "22",  # People & Blogs
            },
            "status": {
                "privacyStatus": "private",
            }
        }

        try:
            # Initialize upload
            init_response = httpx.post(
                init_url,
                headers=headers,
                json=metadata,
                timeout=30.0
            )
            init_response.raise_for_status()

            upload_url = init_response.headers.get("Location")
            if not upload_url:
                return json.dumps({"error": "No upload URL returned"})

            # Upload the video
            with open(file_path, "rb") as f:
                video_data = f.read()

            upload_response = httpx.put(
                upload_url,
                content=video_data,
                headers={"Content-Type": "video/mp4"},
                timeout=300.0
            )
            upload_response.raise_for_status()

            result = upload_response.json()
            return json.dumps({
                "status": "uploaded",
                "video_id": result.get("id"),
            })

        except httpx.HTTPError as e:
            return json.dumps({"error": str(e)})

    def post_content(self, package: ContentPackage) -> Dict[str, Any]:
        """Post content to YouTube"""
        if not self._authenticated:
            return {"error": "Not authenticated with YouTube"}

        if not package.media_path:
            return {"error": "No media file to upload"}

        is_short = package.content_type == ContentType.SHORT_VIDEO

        # Prepare title and description
        title = package.script.hook[:100]  # Use hook as title
        if is_short:
            title = f"{title} #Shorts"

        description = (
            f"{package.script.full_voiceover}\n\n"
            f"{package.script.cta}\n\n"
            f"Product: {package.product.name}\n"
            f"Link: {package.product.affiliate_link}\n\n"
            f"{' '.join(package.script.hashtags)}"
        )

        # Upload video
        upload_result = json.loads(
            self.upload_media(Path(package.media_path), package.content_type)
        )

        if "error" in upload_result:
            return upload_result

        video_id = upload_result.get("video_id")

        # Update video metadata
        update_url = f"{self.api_base}/videos?part=snippet,status"
        headers = {
            "Authorization": f"Bearer {self._access_token}",
            "Content-Type": "application/json",
        }

        update_data = {
            "id": video_id,
            "snippet": {
                "title": title,
                "description": description,
                "categoryId": "22",
                "tags": package.script.hashtags,
            },
            "status": {
                "privacyStatus": "public",
                "madeForKids": False,
            }
        }

        try:
            response = httpx.put(
                update_url,
                headers=headers,
                json=update_data,
                timeout=30.0
            )

            return {
                "status": "posted",
                "video_id": video_id,
                "url": f"https://youtube.com/watch?v={video_id}",
                "platform": "youtube",
                "is_short": is_short,
            }

        except httpx.HTTPError as e:
            return {"error": str(e), "video_id": video_id}

    def post_draft(self, package: ContentPackage) -> Dict[str, Any]:
        """Post as private/unlisted"""
        # Post with private status
        result = self.post_content(package)
        if "video_id" in result:
            # Update to private
            self._update_privacy(result["video_id"], "private")
        return result

    def _update_privacy(self, video_id: str, privacy: str) -> bool:
        """Update video privacy status"""
        url = f"{self.api_base}/videos?part=status"
        headers = {"Authorization": f"Bearer {self._access_token}"}

        try:
            httpx.put(
                url,
                headers=headers,
                json={"id": video_id, "status": {"privacyStatus": privacy}},
                timeout=30.0
            )
            return True
        except httpx.HTTPError:
            return False

    # =========================================================================
    # Analytics
    # =========================================================================

    def get_post_stats(self, post_id: str) -> Dict[str, Any]:
        """Get video statistics"""
        if not self._authenticated:
            return {"error": "Not authenticated"}

        url = (
            f"{self.api_base}/videos"
            f"?part=statistics,snippet"
            f"&id={post_id}"
            f"&key={YOUTUBE_API_KEY}"
        )

        try:
            response = httpx.get(url, timeout=30.0)
            data = response.json()
            if data.get("items"):
                return data["items"][0]
            return {"error": "Video not found"}
        except httpx.HTTPError as e:
            return {"error": str(e)}


# Create default instance
youtube_adapter = YouTubeAdapter()
