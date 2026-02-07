"""
Twitter/X Platform Adapter

Handles Twitter/X content via the official XDK (X Developer Kit).
Supports text, images, and video posts with OAuth 2.0 PKCE authentication.
Supports multiple accounts with easy switching.
"""
from typing import Dict, Any, List, Optional
from pathlib import Path
import json
import sys

sys.path.insert(0, str(Path(__file__).parent.parent.parent))

from xdk import Client
from xdk.posts import PostsClient
from xdk.media import MediaClient
from xdk.oauth1_auth import OAuth1

from platforms.base import PlatformAdapter
from core.models import Platform, ContentType, ContentPackage, AspectRatio
from config.settings import (
    TWITTER_API_KEY, TWITTER_API_SECRET,
    TWITTER_ACCESS_TOKEN, TWITTER_ACCESS_SECRET,
    TWITTER_BEARER_TOKEN,
    get_platform_setting
)
from config.accounts import account_manager, get_account


class TwitterAdapter(PlatformAdapter):
    """Twitter/X platform adapter using official XDK with multi-account support"""

    def __init__(self, account_id: str = None):
        super().__init__()
        self._client: Optional[Client] = None
        self._posts_client: Optional[PostsClient] = None
        self._media_client: Optional[MediaClient] = None
        self._current_account_id: Optional[str] = None

        # Load account credentials
        self._load_account(account_id)

    def _load_account(self, account_id: str = None):
        """Load credentials for specified account or active account"""
        # Get account from manager
        account = get_account("twitter", account_id)

        if account:
            self._current_account_id = account_id or account_manager.get_active_account_id("twitter")
            self._auth_type = account.get("auth_type", "oauth1")

            if self._auth_type == "oauth2":
                # OAuth 2.0 account (e.g., lewkai)
                self._oauth2_token = account.get("access_token")
                self._oauth2_refresh = account.get("refresh_token")
                self._client_id = account.get("client_id")
                self._client_secret = account.get("client_secret")
                self._bearer_token = None
                self._access_token = None
                self._access_secret = None
            else:
                # OAuth 1.0a account (e.g., personal)
                self._auth_type = "oauth1"
                self._bearer_token = account.get("bearer_token")
                self._access_token = account.get("access_token")
                self._access_secret = account.get("access_secret")
                self._client_id = account.get("api_key")
                self._client_secret = account.get("api_secret")
                self._oauth2_token = None
                self._oauth2_refresh = None
        else:
            # Fallback to direct env vars (OAuth 1.0a)
            self._current_account_id = "personal"
            self._auth_type = "oauth1"
            self._bearer_token = TWITTER_BEARER_TOKEN
            self._access_token = TWITTER_ACCESS_TOKEN
            self._access_secret = TWITTER_ACCESS_SECRET
            self._client_id = TWITTER_API_KEY
            self._client_secret = TWITTER_API_SECRET
            self._oauth2_token = None
            self._oauth2_refresh = None

        # Initialize client with new credentials
        self._initialize_client()

    def switch_account(self, account_id: str) -> bool:
        """Switch to a different Twitter account"""
        accounts = account_manager.list_accounts("twitter")
        if account_id not in accounts:
            return False

        self._load_account(account_id)
        return self._authenticated

    def get_current_account(self) -> str:
        """Get the current account ID"""
        return self._current_account_id or "personal"

    def list_accounts(self) -> List[str]:
        """List available Twitter accounts"""
        return account_manager.list_accounts("twitter")

    def _initialize_client(self):
        """Initialize client with available credentials (OAuth 1.0a or 2.0)"""
        try:
            if self._auth_type == "oauth2" and self._oauth2_token:
                # OAuth 2.0 - use direct API calls instead of XDK
                self._client = None
                self._posts_client = None
                self._media_client = None
                self._authenticated = True
            elif self._client_id and self._client_secret and self._access_token and self._access_secret:
                # OAuth 1.0a - use XDK for posting tweets
                auth = OAuth1(
                    api_key=self._client_id,
                    api_secret=self._client_secret,
                    callback='https://localhost:3000/callback',
                    access_token=self._access_token,
                    access_token_secret=self._access_secret
                )
                self._client = Client(auth=auth)
                self._authenticated = True
                self._posts_client = PostsClient(self._client)
                self._media_client = MediaClient(self._client)
            elif self._bearer_token:
                # App-only auth with bearer token (read-only)
                self._client = Client(bearer_token=self._bearer_token)
                self._authenticated = True
                self._posts_client = PostsClient(self._client)
                self._media_client = MediaClient(self._client)
            else:
                self._authenticated = False

        except Exception as e:
            print(f"Warning: Failed to initialize Twitter client: {e}")
            self._authenticated = False

    @property
    def platform(self) -> Platform:
        return Platform.TWITTER

    # =========================================================================
    # Authentication
    # =========================================================================

    def authenticate(self, credentials: Dict[str, str]) -> bool:
        """Authenticate with Twitter using provided credentials"""
        self._bearer_token = credentials.get("bearer_token")
        self._access_token = credentials.get("access_token")
        self._access_secret = credentials.get("access_secret")
        self._client_id = credentials.get("client_id", self._client_id)
        self._client_secret = credentials.get("client_secret", self._client_secret)

        self._initialize_client()
        return self._authenticated

    def get_auth_url(self, redirect_uri: str) -> str:
        """Get Twitter OAuth 2.0 authorization URL using XDK"""
        if not self._client:
            self._client = Client(
                client_id=self._client_id,
                client_secret=self._client_secret,
                redirect_uri=redirect_uri,
                scope=["tweet.read", "tweet.write", "users.read", "offline.access"],
            )

        try:
            url, state = self._client.get_authorization_url()
            return url
        except Exception as e:
            # Fallback to manual URL construction
            scopes = "tweet.read tweet.write users.read offline.access"
            return (
                f"https://twitter.com/i/oauth2/authorize"
                f"?response_type=code"
                f"&client_id={self._client_id}"
                f"&redirect_uri={redirect_uri}"
                f"&scope={scopes}"
                f"&state=state"
                f"&code_challenge=challenge"
                f"&code_challenge_method=plain"
            )

    def exchange_code(self, code: str, redirect_uri: str) -> Dict[str, str]:
        """Exchange authorization code for access token using XDK"""
        if not self._client:
            self._client = Client(
                client_id=self._client_id,
                client_secret=self._client_secret,
                redirect_uri=redirect_uri,
            )

        try:
            tokens = self._client.exchange_code(authorization_code=code)

            if tokens and "access_token" in tokens:
                self._access_token = tokens["access_token"]
                self._authenticated = True
                self._posts_client = PostsClient(self._client)
                self._media_client = MediaClient(self._client)

            return tokens if tokens else {"error": "No tokens returned"}

        except Exception as e:
            return {"error": str(e)}

    def refresh_access_token(self) -> bool:
        """Refresh the access token using XDK"""
        if not self._client:
            return False

        try:
            if self._client.is_token_expired():
                new_token = self._client.refresh_token()
                if new_token:
                    self._access_token = new_token.get("access_token")
                    return True
            return True  # Token not expired
        except Exception:
            return False

    # =========================================================================
    # Content Generation
    # =========================================================================

    def get_script_instructions(self) -> str:
        """Twitter-specific content instructions"""
        return """\
## Twitter/X Content Guidelines

### Post Types
1. **Text-only**: Quick thoughts, hot takes
2. **Image + Text**: Product shots, infographics
3. **Video + Text**: Short demos, testimonials
4. **Thread**: Multi-tweet storytelling

### Character Limits
- Tweet: 280 characters
- With media: 280 (URL doesn't count if media attached)

### Hook Strategies for Twitter
1. **Hot Take**: Controversial opinion
2. **Thread Starter**: "Thread: 5 things..."
3. **Question**: Engage with a question
4. **Stat/Fact**: Lead with surprising data
5. **Personal Story**: "I just discovered..."

### Twitter-Specific Elements
- Brevity is key
- Reply-worthy content
- Quote-tweet friendly
- Threads for longer content
- Use of relevant #hashtags sparingly

### Hashtag Guidelines
- 1-2 hashtags max
- Trending hashtags if relevant
- Don't overuse (looks spammy)

### Video Specs
- Duration: 0:01 - 2:20 (140 seconds)
- Aspect ratios: 16:9, 1:1
- Max file size: 512MB
- Recommended: 30-60 seconds

### Content Angles That Work
- "Just found this and had to share"
- Product comparison threads
- Quick tip or hack
- Before/after with images
- "Why no one is talking about this"

### CTA Patterns
- "Link in bio" (add to profile)
- "Reply for link"
- "Bookmark this"
- "RT to save"
- Direct link in tweet

### Thread Format
Tweet 1: Hook + promise
Tweets 2-N: Value delivery
Final Tweet: CTA + summary
"""

    def get_supported_content_types(self) -> List[ContentType]:
        return [ContentType.TEXT, ContentType.IMAGE, ContentType.SHORT_VIDEO]

    def get_optimal_settings(self, content_type: ContentType) -> Dict[str, Any]:
        if content_type == ContentType.SHORT_VIDEO:
            return {
                "duration": get_platform_setting("twitter", "default_duration", 30),
                "max_duration": 140,
                "aspect_ratio": AspectRatio.LANDSCAPE.value,
                "resolution": "720p",
            }
        elif content_type == ContentType.IMAGE:
            return {
                "aspect_ratio": AspectRatio.LANDSCAPE.value,
                "max_images": 4,
            }
        else:  # TEXT
            return {
                "max_length": 280,
            }

    # =========================================================================
    # Helper Methods
    # =========================================================================

    def _extract_tweet_id(self, result) -> Optional[str]:
        """Extract tweet ID from XDK CreateResponse"""
        if hasattr(result, 'data'):
            data = result.data
            if isinstance(data, dict):
                return data.get('id')
            elif hasattr(data, 'id'):
                return data.id
        elif isinstance(result, dict):
            return result.get("data", {}).get("id") or result.get("id")
        return None

    # =========================================================================
    # Media Upload
    # =========================================================================

    def upload_media(self, file_path: Path, content_type: ContentType) -> str:
        """Upload media to Twitter using XDK"""
        if not self._authenticated or not self._media_client:
            return json.dumps({"error": "Not authenticated with Twitter"})

        try:
            if content_type == ContentType.SHORT_VIDEO:
                return self._upload_video_xdk(file_path)
            else:
                return self._upload_image_xdk(file_path)
        except Exception as e:
            return json.dumps({"error": str(e)})

    def _upload_image_xdk(self, file_path: Path) -> str:
        """Upload image using XDK MediaClient"""
        try:
            # Use XDK's upload method
            result = self._media_client.upload(
                file_path=str(file_path),
                media_type="image"
            )

            if result and hasattr(result, 'media_id'):
                return json.dumps({
                    "status": "uploaded",
                    "media_id": str(result.media_id),
                })
            elif result and isinstance(result, dict):
                return json.dumps({
                    "status": "uploaded",
                    "media_id": result.get("media_id_string") or result.get("media_id"),
                })
            else:
                return json.dumps({"error": "Upload failed - no media_id returned"})

        except Exception as e:
            return json.dumps({"error": f"Image upload failed: {str(e)}"})

    def _upload_video_xdk(self, file_path: Path) -> str:
        """Upload video using XDK MediaClient chunked upload"""
        try:
            file_size = file_path.stat().st_size

            # Initialize upload
            init_result = self._media_client.initialize_upload(
                total_bytes=file_size,
                media_type="video/mp4",
                media_category="tweet_video"
            )

            media_id = None
            if hasattr(init_result, 'media_id'):
                media_id = init_result.media_id
            elif isinstance(init_result, dict):
                media_id = init_result.get("media_id_string") or init_result.get("media_id")

            if not media_id:
                return json.dumps({"error": "Failed to initialize upload"})

            # Append chunks
            chunk_size = 5 * 1024 * 1024  # 5MB chunks
            with open(file_path, "rb") as f:
                segment_index = 0
                while True:
                    chunk = f.read(chunk_size)
                    if not chunk:
                        break

                    self._media_client.append_upload(
                        media_id=media_id,
                        segment_index=segment_index,
                        media_data=chunk
                    )
                    segment_index += 1

            # Finalize upload
            final_result = self._media_client.finalize_upload(media_id=media_id)

            return json.dumps({
                "status": "uploaded",
                "media_id": str(media_id),
            })

        except Exception as e:
            return json.dumps({"error": f"Video upload failed: {str(e)}"})

    # =========================================================================
    # Posting
    # =========================================================================

    def post_content(self, package: ContentPackage) -> Dict[str, Any]:
        """Post content to Twitter using XDK"""
        if not self._authenticated or not self._posts_client:
            return {"error": "Not authenticated with Twitter"}

        try:
            # Prepare tweet text
            text = package.script.hook[:200]
            hashtags = " ".join(package.script.hashtags[:2])
            tweet_text = f"{text}\n\n{package.product.affiliate_link}\n\n{hashtags}"

            if len(tweet_text) > 280:
                tweet_text = tweet_text[:277] + "..."

            # Upload media if present
            media_ids = None
            if package.media_path:
                upload_result = json.loads(
                    self.upload_media(Path(package.media_path), package.content_type)
                )
                if "media_id" in upload_result:
                    media_ids = [upload_result["media_id"]]
                elif "error" in upload_result:
                    return {"error": f"Media upload failed: {upload_result['error']}"}

            # Create tweet using XDK
            body = {'text': tweet_text}
            if media_ids:
                body['media'] = {'media_ids': media_ids}
            result = self._posts_client.create(body=body)

            # Extract tweet ID from result
            tweet_id = self._extract_tweet_id(result)

            return {
                "status": "posted",
                "tweet_id": tweet_id,
                "platform": "twitter",
                "text": tweet_text[:50] + "..." if len(tweet_text) > 50 else tweet_text,
            }

        except Exception as e:
            return {"error": str(e)}

    def post_thread(self, tweets: List[str]) -> Dict[str, Any]:
        """Post a thread of tweets using XDK"""
        if not self._authenticated or not self._posts_client:
            return {"error": "Not authenticated"}

        tweet_ids = []
        reply_to = None

        try:
            for tweet_text in tweets:
                body = {'text': tweet_text}
                if reply_to:
                    body['reply'] = {'in_reply_to_tweet_id': reply_to}
                result = self._posts_client.create(body=body)

                # Extract tweet ID
                tweet_id = self._extract_tweet_id(result)

                if tweet_id:
                    tweet_ids.append(tweet_id)
                    reply_to = tweet_id

            return {
                "status": "posted",
                "tweet_ids": tweet_ids,
                "thread_length": len(tweet_ids),
                "platform": "twitter",
            }

        except Exception as e:
            return {"error": str(e), "partial_tweets": tweet_ids}

    def post_text_only(self, text: str) -> Dict[str, Any]:
        """Post a simple text tweet"""
        if not self._authenticated:
            return {"error": "Not authenticated"}

        try:
            if len(text) > 280:
                text = text[:277] + "..."

            if self._auth_type == "oauth2":
                # Use direct API call for OAuth 2.0
                return self._post_oauth2(text)
            else:
                # Use XDK for OAuth 1.0a
                if not self._posts_client:
                    return {"error": "Not authenticated"}

                result = self._posts_client.create(body={'text': text})
                tweet_id = self._extract_tweet_id(result)

                return {
                    "status": "posted",
                    "tweet_id": tweet_id,
                    "platform": "twitter",
                    "account": self._current_account_id,
                }

        except Exception as e:
            return {"error": str(e)}

    def _post_oauth2(self, text: str, media_ids: List[str] = None) -> Dict[str, Any]:
        """Post tweet using OAuth 2.0 token (direct API call)"""
        import httpx

        # Try to refresh token if needed
        self._refresh_oauth2_token_if_needed()

        url = 'https://api.twitter.com/2/tweets'
        headers = {
            'Authorization': f'Bearer {self._oauth2_token}',
            'Content-Type': 'application/json'
        }
        data = {'text': text}
        if media_ids:
            data['media'] = {'media_ids': media_ids}

        try:
            response = httpx.post(url, headers=headers, json=data, timeout=30.0)
            result = response.json()

            if response.status_code == 201:
                return {
                    "status": "posted",
                    "tweet_id": result.get("data", {}).get("id"),
                    "platform": "twitter",
                    "account": self._current_account_id,
                }
            elif response.status_code == 401:
                # Token expired, try refresh
                if self._refresh_oauth2_token():
                    return self._post_oauth2(text, media_ids)  # Retry
                return {"error": "Token expired and refresh failed"}
            else:
                return {"error": result.get("detail") or result.get("title") or str(result)}

        except Exception as e:
            return {"error": str(e)}

    def _refresh_oauth2_token_if_needed(self):
        """Refresh OAuth 2.0 token proactively"""
        # Always try to refresh before posting to avoid failures
        if self._oauth2_refresh:
            self._refresh_oauth2_token()

    def _refresh_oauth2_token(self) -> bool:
        """Refresh the OAuth 2.0 access token"""
        import httpx
        import base64
        import os

        if not self._oauth2_refresh:
            return False

        client_id = self._client_id or os.getenv("TWITTER_CLIENT_ID")
        client_secret = self._client_secret or os.getenv("TWITTER_CLIENT_SECRET")

        if not client_id or not client_secret:
            return False

        try:
            credentials = base64.b64encode(f'{client_id}:{client_secret}'.encode()).decode()

            response = httpx.post(
                'https://api.twitter.com/2/oauth2/token',
                headers={
                    'Content-Type': 'application/x-www-form-urlencoded',
                    'Authorization': f'Basic {credentials}'
                },
                data={
                    'grant_type': 'refresh_token',
                    'refresh_token': self._oauth2_refresh,
                },
                timeout=30.0
            )

            if response.status_code == 200:
                result = response.json()
                self._oauth2_token = result.get('access_token')
                self._oauth2_refresh = result.get('refresh_token')

                # Update account manager with new tokens
                from config.accounts import account_manager
                account = account_manager.get_account("twitter", self._current_account_id)
                if account:
                    account['access_token'] = self._oauth2_token
                    account['refresh_token'] = self._oauth2_refresh

                return True
            return False

        except Exception as e:
            print(f"Token refresh failed: {e}")
            return False

    # =========================================================================
    # Analytics
    # =========================================================================

    def get_post_stats(self, post_id: str) -> Dict[str, Any]:
        """Get tweet metrics using XDK"""
        if not self._authenticated or not self._posts_client:
            return {"error": "Not authenticated"}

        try:
            result = self._posts_client.get_by_id(
                tweet_id=post_id,
                tweet_fields=["public_metrics", "created_at"]
            )

            if hasattr(result, 'data'):
                return {
                    "tweet_id": post_id,
                    "metrics": result.data.public_metrics if hasattr(result.data, 'public_metrics') else {},
                    "created_at": result.data.created_at if hasattr(result.data, 'created_at') else None,
                }
            elif isinstance(result, dict):
                return result

            return {"tweet_id": post_id, "data": str(result)}

        except Exception as e:
            return {"error": str(e)}

    def delete_post(self, post_id: str) -> Dict[str, Any]:
        """Delete a tweet using XDK"""
        if not self._authenticated or not self._posts_client:
            return {"error": "Not authenticated"}

        try:
            result = self._posts_client.delete(tweet_id=post_id)
            return {"status": "deleted", "tweet_id": post_id}
        except Exception as e:
            return {"error": str(e)}


# Create default instance
twitter_adapter = TwitterAdapter()
