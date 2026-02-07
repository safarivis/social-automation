"""
LinkedIn Platform Adapter

Handles LinkedIn content via Marketing API.
Supports text posts, images, video, and documents.
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
    LINKEDIN_CLIENT_ID, LINKEDIN_CLIENT_SECRET, LINKEDIN_ACCESS_TOKEN,
    LINKEDIN_PERSON_URN, get_platform_setting
)


class LinkedInAdapter(PlatformAdapter):
    """LinkedIn platform adapter for professional content"""

    def __init__(self):
        super().__init__()
        self.api_base = "https://api.linkedin.com/v2"
        self._access_token = LINKEDIN_ACCESS_TOKEN
        self._person_urn: Optional[str] = LINKEDIN_PERSON_URN

        if self._access_token:
            self._authenticated = True
            # Fetch person URN if not configured
            if not self._person_urn:
                self._fetch_person_urn()

    @property
    def platform(self) -> Platform:
        return Platform.LINKEDIN

    # =========================================================================
    # Authentication
    # =========================================================================

    def authenticate(self, credentials: Dict[str, str]) -> bool:
        """Authenticate with LinkedIn"""
        self._access_token = credentials.get("access_token")
        self._person_urn = credentials.get("person_urn")
        self._authenticated = bool(self._access_token)

        if self._authenticated and not self._person_urn:
            self._fetch_person_urn()

        return self._authenticated

    def get_auth_url(self, redirect_uri: str) -> str:
        """Get LinkedIn OAuth URL"""
        # Use OpenID Connect scopes for profile + posting permission
        scopes = "openid+profile+w_member_social"
        return (
            f"https://www.linkedin.com/oauth/v2/authorization"
            f"?response_type=code"
            f"&client_id={LINKEDIN_CLIENT_ID}"
            f"&redirect_uri={redirect_uri}"
            f"&scope={scopes}"
        )

    def exchange_code(self, code: str, redirect_uri: str) -> Dict[str, str]:
        """Exchange code for access token"""
        url = "https://www.linkedin.com/oauth/v2/accessToken"
        data = {
            "grant_type": "authorization_code",
            "code": code,
            "redirect_uri": redirect_uri,
            "client_id": LINKEDIN_CLIENT_ID,
            "client_secret": LINKEDIN_CLIENT_SECRET,
        }

        try:
            response = httpx.post(url, data=data, timeout=30.0)
            response.raise_for_status()
            result = response.json()

            if "access_token" in result:
                self._access_token = result["access_token"]
                self._authenticated = True
                self._fetch_person_urn()

            return result
        except httpx.HTTPError as e:
            return {"error": str(e)}

    def _fetch_person_urn(self):
        """Fetch the authenticated user's person URN using OpenID Connect"""
        if not self._access_token:
            return

        # Use OpenID Connect userinfo endpoint
        url = "https://api.linkedin.com/v2/userinfo"
        headers = {"Authorization": f"Bearer {self._access_token}"}

        try:
            response = httpx.get(url, headers=headers, timeout=30.0)
            data = response.json()
            # OpenID returns 'sub' as the person ID
            person_id = data.get("sub")
            if person_id:
                self._person_urn = f"urn:li:person:{person_id}"
        except httpx.HTTPError:
            pass

    # =========================================================================
    # Content Generation
    # =========================================================================

    def get_script_instructions(self) -> str:
        """LinkedIn-specific content instructions"""
        return """\
## LinkedIn Content Guidelines

### Content Style
- Professional but personable
- Value-driven, educational
- Story-based engagement
- Industry insights and expertise

### Post Types
1. **Text Post**: Thought leadership, stories
2. **Image + Text**: Infographics, product shots
3. **Video**: Professional tutorials, testimonials
4. **Document/Carousel**: Slide decks, guides
5. **Article**: Long-form content

### Hook Strategies for LinkedIn
1. **Personal Story**: "Last week, I discovered..."
2. **Contrarian View**: "Unpopular opinion:"
3. **Data Lead**: "87% of professionals..."
4. **Question**: "What's stopping you from..."
5. **Achievement**: "Just hit a milestone..."

### LinkedIn-Specific Elements
- First 3 lines visible in feed (crucial!)
- Use line breaks for readability
- Emojis sparingly (professional)
- Tag relevant people/companies
- Engagement in first hour matters

### Caption Guidelines
- Max 3000 characters
- First 3 lines = hook (before "see more")
- Short paragraphs
- 3-5 hashtags at end
- End with question or CTA

### Video Specs
- Duration: 3 seconds - 10 minutes
- Aspect ratio: 16:9 or 1:1
- Square performs well
- Add captions (80% watch muted)

### Content Angles for Products
- "Tool I can't live without"
- "How I solved [problem]"
- Productivity/efficiency focus
- Business use case stories
- ROI and results focus

### CTA Patterns
- "Link in first comment"
- "DM me for link"
- "Comment 'interested'"
- "Save this for later"
- "Share if you agree"

### Best Practices
- Post consistently (1-2x daily max)
- Engage in comments (first 2 hours)
- Cross-promote from other platforms
- Use LinkedIn native video
- Avoid external links in post (put in comments)
"""

    def get_supported_content_types(self) -> List[ContentType]:
        return [
            ContentType.TEXT,
            ContentType.IMAGE,
            ContentType.SHORT_VIDEO,
            ContentType.DOCUMENT
        ]

    def get_optimal_settings(self, content_type: ContentType) -> Dict[str, Any]:
        if content_type == ContentType.SHORT_VIDEO:
            return {
                "duration": get_platform_setting("linkedin", "default_duration", 30),
                "max_duration": 600,
                "aspect_ratio": AspectRatio.LANDSCAPE.value,
                "resolution": "1080p",
            }
        elif content_type == ContentType.IMAGE:
            return {
                "aspect_ratio": AspectRatio.LANDSCAPE.value,
                "resolution": "1200x627",
            }
        elif content_type == ContentType.DOCUMENT:
            return {
                "format": "pdf",
                "max_pages": 300,
                "max_size_mb": 100,
            }
        else:  # TEXT
            return {
                "max_length": 3000,
            }

    # =========================================================================
    # Posting
    # =========================================================================

    def upload_media(self, file_path: Path, content_type: ContentType) -> str:
        """Upload media to LinkedIn"""
        if not self._authenticated or not self._person_urn:
            return json.dumps({"error": "Not authenticated with LinkedIn"})

        if content_type == ContentType.SHORT_VIDEO:
            return self._upload_video(file_path)
        elif content_type == ContentType.DOCUMENT:
            return self._upload_document(file_path)
        else:
            return self._upload_image(file_path)

    def _upload_image(self, file_path: Path) -> str:
        """Upload image to LinkedIn"""
        # Step 1: Register upload
        register_url = f"{self.api_base}/assets?action=registerUpload"
        headers = {
            "Authorization": f"Bearer {self._access_token}",
            "Content-Type": "application/json",
        }

        register_data = {
            "registerUploadRequest": {
                "recipes": ["urn:li:digitalmediaRecipe:feedshare-image"],
                "owner": self._person_urn,
                "serviceRelationships": [{
                    "relationshipType": "OWNER",
                    "identifier": "urn:li:userGeneratedContent"
                }]
            }
        }

        try:
            response = httpx.post(
                register_url, headers=headers, json=register_data, timeout=30.0
            )
            result = response.json()

            upload_url = result["value"]["uploadMechanism"][
                "com.linkedin.digitalmedia.uploading.MediaUploadHttpRequest"
            ]["uploadUrl"]
            asset = result["value"]["asset"]

            # Step 2: Upload image
            with open(file_path, "rb") as f:
                image_data = f.read()

            httpx.put(
                upload_url,
                content=image_data,
                headers={"Authorization": f"Bearer {self._access_token}"},
                timeout=60.0
            )

            return json.dumps({"status": "uploaded", "asset": asset})

        except (httpx.HTTPError, KeyError) as e:
            return json.dumps({"error": str(e)})

    def _upload_video(self, file_path: Path) -> str:
        """Upload video to LinkedIn"""
        # Similar to image but with video recipe
        register_url = f"{self.api_base}/assets?action=registerUpload"
        headers = {
            "Authorization": f"Bearer {self._access_token}",
            "Content-Type": "application/json",
        }

        register_data = {
            "registerUploadRequest": {
                "recipes": ["urn:li:digitalmediaRecipe:feedshare-video"],
                "owner": self._person_urn,
                "serviceRelationships": [{
                    "relationshipType": "OWNER",
                    "identifier": "urn:li:userGeneratedContent"
                }]
            }
        }

        try:
            response = httpx.post(
                register_url, headers=headers, json=register_data, timeout=30.0
            )
            result = response.json()

            upload_url = result["value"]["uploadMechanism"][
                "com.linkedin.digitalmedia.uploading.MediaUploadHttpRequest"
            ]["uploadUrl"]
            asset = result["value"]["asset"]

            with open(file_path, "rb") as f:
                video_data = f.read()

            httpx.put(
                upload_url,
                content=video_data,
                headers={
                    "Authorization": f"Bearer {self._access_token}",
                    "Content-Type": "video/mp4",
                },
                timeout=300.0
            )

            return json.dumps({"status": "uploaded", "asset": asset})

        except (httpx.HTTPError, KeyError) as e:
            return json.dumps({"error": str(e)})

    def _upload_document(self, file_path: Path) -> str:
        """Upload document (PDF) to LinkedIn"""
        register_url = f"{self.api_base}/assets?action=registerUpload"
        headers = {
            "Authorization": f"Bearer {self._access_token}",
            "Content-Type": "application/json",
        }

        register_data = {
            "registerUploadRequest": {
                "recipes": ["urn:li:digitalmediaRecipe:feedshare-document"],
                "owner": self._person_urn,
                "serviceRelationships": [{
                    "relationshipType": "OWNER",
                    "identifier": "urn:li:userGeneratedContent"
                }]
            }
        }

        try:
            response = httpx.post(
                register_url, headers=headers, json=register_data, timeout=30.0
            )
            result = response.json()

            upload_url = result["value"]["uploadMechanism"][
                "com.linkedin.digitalmedia.uploading.MediaUploadHttpRequest"
            ]["uploadUrl"]
            asset = result["value"]["asset"]

            with open(file_path, "rb") as f:
                doc_data = f.read()

            httpx.put(
                upload_url,
                content=doc_data,
                headers={
                    "Authorization": f"Bearer {self._access_token}",
                    "Content-Type": "application/pdf",
                },
                timeout=120.0
            )

            return json.dumps({"status": "uploaded", "asset": asset})

        except (httpx.HTTPError, KeyError) as e:
            return json.dumps({"error": str(e)})

    def post_content(self, package: ContentPackage) -> Dict[str, Any]:
        """Post content to LinkedIn"""
        if not self._authenticated or not self._person_urn:
            return {"error": "Not authenticated with LinkedIn"}

        url = f"{self.api_base}/ugcPosts"
        headers = {
            "Authorization": f"Bearer {self._access_token}",
            "Content-Type": "application/json",
            "X-Restli-Protocol-Version": "2.0.0",
        }

        # Prepare post text
        text = (
            f"{package.script.hook}\n\n"
            f"{package.script.problem}\n\n"
            f"{package.script.solution}\n\n"
            f"{package.script.cta}\n\n"
            f"{' '.join(package.script.hashtags)}"
        )

        # Build share content
        share_content = {
            "shareCommentary": {"text": text},
            "shareMediaCategory": "NONE",
        }

        # Add media if present
        if package.media_path:
            upload_result = json.loads(
                self.upload_media(Path(package.media_path), package.content_type)
            )

            if "asset" in upload_result:
                if package.content_type == ContentType.SHORT_VIDEO:
                    share_content["shareMediaCategory"] = "VIDEO"
                elif package.content_type == ContentType.DOCUMENT:
                    share_content["shareMediaCategory"] = "DOCUMENT"
                else:
                    share_content["shareMediaCategory"] = "IMAGE"

                share_content["media"] = [{
                    "status": "READY",
                    "media": upload_result["asset"],
                    "title": {"text": package.product.name},
                }]

        post_data = {
            "author": self._person_urn,
            "lifecycleState": "PUBLISHED",
            "specificContent": {
                "com.linkedin.ugc.ShareContent": share_content
            },
            "visibility": {
                "com.linkedin.ugc.MemberNetworkVisibility": "PUBLIC"
            }
        }

        try:
            response = httpx.post(url, headers=headers, json=post_data, timeout=30.0)
            result = response.json()

            return {
                "status": "posted",
                "post_id": result.get("id"),
                "platform": "linkedin",
            }

        except httpx.HTTPError as e:
            return {"error": str(e)}

    def post_with_link_in_comment(self, package: ContentPackage) -> Dict[str, Any]:
        """Post content then add affiliate link as first comment"""
        # First, post the content
        post_result = self.post_content(package)

        if "error" in post_result or "post_id" not in post_result:
            return post_result

        post_id = post_result["post_id"]

        # Then add comment with link
        comment_url = f"{self.api_base}/socialActions/{post_id}/comments"
        headers = {
            "Authorization": f"Bearer {self._access_token}",
            "Content-Type": "application/json",
        }

        comment_data = {
            "actor": self._person_urn,
            "message": {
                "text": f"Link: {package.product.affiliate_link}"
            }
        }

        try:
            httpx.post(comment_url, headers=headers, json=comment_data, timeout=30.0)
            post_result["comment_added"] = True
        except httpx.HTTPError:
            post_result["comment_added"] = False

        return post_result

    # =========================================================================
    # Analytics
    # =========================================================================

    def get_post_stats(self, post_id: str) -> Dict[str, Any]:
        """Get post statistics"""
        if not self._authenticated:
            return {"error": "Not authenticated"}

        url = f"{self.api_base}/socialActions/{post_id}"
        headers = {"Authorization": f"Bearer {self._access_token}"}

        try:
            response = httpx.get(url, headers=headers, timeout=30.0)
            return response.json()
        except httpx.HTTPError as e:
            return {"error": str(e)}


# Create default instance
linkedin_adapter = LinkedInAdapter()
