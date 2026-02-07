"""
Grok Imagine Video/Image Generation Tools

Tools for generating videos and images using xAI's Grok Imagine API.
Supports multi-platform content with different aspect ratios.
"""
from typing import Optional, Dict, Any
from agno.tools import Toolkit
from openai import OpenAI
import httpx
import time
import json
import os
from pathlib import Path
from datetime import datetime
import re
import sys

sys.path.insert(0, str(Path(__file__).parent.parent))
from config.settings import XAI_API_KEY, VIDEOS_DIR, VIDEO_SETTINGS
from core.models import Platform, AspectRatio


class GrokVideoTools(Toolkit):
    """Tools for video generation using Grok Imagine"""

    def __init__(
        self,
        api_key: Optional[str] = None,
        videos_dir: Optional[Path] = None
    ):
        super().__init__(name="grok_video_tools")
        self.api_key = api_key or XAI_API_KEY
        self.base_url = "https://api.x.ai/v1"

        # Initialize OpenAI client for xAI API
        self.client = OpenAI(
            api_key=self.api_key,
            base_url=self.base_url
        )

        # Set up videos directory
        self.videos_dir = videos_dir or VIDEOS_DIR
        self.videos_dir.mkdir(parents=True, exist_ok=True)

        # Register tools
        self.register(self.generate_video)
        self.register(self.check_video_status)
        self.register(self.generate_video_from_image)
        self.register(self.download_video)
        self.register(self.generate_and_download)
        self.register(self.generate_for_platform)

    def generate_video(
        self,
        prompt: str,
        duration: int = 10,
        aspect_ratio: str = "9:16",
        resolution: str = "720p"
    ) -> str:
        """
        Generate a video from a text prompt using Grok Imagine.

        Args:
            prompt: Description of the video to generate
            duration: Video length in seconds (1-15)
            aspect_ratio: Video aspect ratio (9:16 for TikTok vertical)
            resolution: Video resolution (720p or 480p)

        Returns:
            JSON with request_id for polling, or video_url if complete
        """
        headers = {
            "Authorization": f"Bearer {self.api_key}",
            "Content-Type": "application/json"
        }

        payload = {
            "prompt": prompt,
            "model": "grok-imagine-video",
            "duration": min(max(duration, 1), 15),
            "aspect_ratio": aspect_ratio,
            "resolution": resolution
        }

        try:
            response = httpx.post(
                f"{self.base_url}/videos/generations",
                headers=headers,
                json=payload,
                timeout=30.0
            )
            response.raise_for_status()
            result = response.json()

            request_id = result.get("request_id")
            if not request_id:
                return json.dumps({
                    "status": "error",
                    "message": "No request_id in response",
                    "raw_response": result
                })

            return json.dumps({
                "status": "submitted",
                "request_id": request_id,
                "message": "Video generation started. Use check_video_status to poll for completion."
            })

        except httpx.HTTPStatusError as e:
            return json.dumps({
                "status": "error",
                "message": str(e),
                "status_code": e.response.status_code,
                "detail": e.response.text[:500] if e.response.text else None
            })
        except httpx.HTTPError as e:
            return json.dumps({
                "status": "error",
                "message": str(e)
            })

    def generate_for_platform(
        self,
        prompt: str,
        platform: str,
        product_name: Optional[str] = None,
    ) -> str:
        """
        Generate a video optimized for a specific platform.

        Args:
            prompt: Description of the video to generate
            platform: Target platform (tiktok, instagram, youtube, twitter, linkedin)
            product_name: Product name for filename

        Returns:
            JSON with generation result
        """
        # Platform-specific settings
        platform_settings = {
            "tiktok": {"aspect_ratio": "9:16", "duration": 10, "resolution": "720p"},
            "instagram": {"aspect_ratio": "9:16", "duration": 15, "resolution": "1080p"},
            "youtube": {"aspect_ratio": "9:16", "duration": 15, "resolution": "1080p"},
            "twitter": {"aspect_ratio": "16:9", "duration": 30, "resolution": "720p"},
            "linkedin": {"aspect_ratio": "16:9", "duration": 30, "resolution": "1080p"},
        }

        settings = platform_settings.get(platform.lower(), platform_settings["tiktok"])

        return self.generate_and_download(
            prompt=prompt,
            product_name=product_name,
            duration=settings["duration"],
            aspect_ratio=settings["aspect_ratio"],
        )

    def check_video_status(self, request_id: str) -> str:
        """
        Check the status of a video generation request.

        Args:
            request_id: The request ID from generate_video

        Returns:
            JSON with status and video_url when complete
        """
        try:
            result = self.client.videos.retrieve(request_id)

            # Extract video URL from response
            video_data = result.video if hasattr(result, 'video') else None
            video_url = None
            duration = None

            if video_data:
                if isinstance(video_data, dict):
                    video_url = video_data.get('url')
                    duration = video_data.get('duration')
                elif hasattr(video_data, 'url'):
                    video_url = video_data.url
                    duration = getattr(video_data, 'duration', None)

            # Determine status
            if video_url:
                status = "completed"
            elif result.status:
                status = result.status
            elif result.error:
                status = "failed"
            else:
                status = "pending"

            return json.dumps({
                "status": status,
                "video_url": video_url,
                "duration": duration,
                "request_id": request_id,
                "error": str(result.error) if result.error else None
            })

        except Exception as e:
            return json.dumps({
                "status": "error",
                "message": str(e),
                "request_id": request_id
            })

    def generate_video_from_image(
        self,
        image_url: str,
        prompt: str,
        duration: int = 10,
        aspect_ratio: str = "9:16"
    ) -> str:
        """
        Generate a video from an image using Grok Imagine (image-to-video).

        Args:
            image_url: URL of the source image
            prompt: Description of the motion/animation to add
            duration: Video length in seconds (1-15)
            aspect_ratio: Video aspect ratio

        Returns:
            JSON with request_id for polling
        """
        headers = {
            "Authorization": f"Bearer {self.api_key}",
            "Content-Type": "application/json"
        }

        payload = {
            "prompt": prompt,
            "model": "grok-imagine-video",
            "image_url": image_url,
            "duration": min(max(duration, 1), 15),
            "aspect_ratio": aspect_ratio
        }

        try:
            response = httpx.post(
                f"{self.base_url}/videos/generations",
                headers=headers,
                json=payload,
                timeout=30.0
            )
            response.raise_for_status()
            result = response.json()

            return json.dumps({
                "status": "submitted",
                "request_id": result.get("request_id"),
                "message": "Image-to-video generation started."
            })

        except httpx.HTTPError as e:
            return json.dumps({
                "status": "error",
                "message": str(e)
            })

    def download_video(
        self,
        video_url: str,
        filename: Optional[str] = None,
        product_name: Optional[str] = None,
        platform: Optional[str] = None,
    ) -> str:
        """
        Download a video from URL and save to data/videos folder.

        Args:
            video_url: URL of the video to download
            filename: Optional custom filename (without extension)
            product_name: Optional product name for auto-naming
            platform: Optional platform for folder organization

        Returns:
            JSON with local file path or error
        """
        try:
            # Generate filename if not provided
            if not filename:
                timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
                if product_name:
                    # Sanitize product name for filename
                    safe_name = re.sub(r'[^\w\s-]', '', product_name).strip()
                    safe_name = re.sub(r'[-\s]+', '_', safe_name).lower()
                    filename = f"{safe_name}_{timestamp}"
                else:
                    filename = f"video_{timestamp}"

            # Add platform prefix if specified
            if platform:
                filename = f"{platform}_{filename}"

            # Determine extension from URL or default to mp4
            url_path = video_url.split('?')[0]
            if url_path.endswith('.mp4'):
                ext = '.mp4'
            elif url_path.endswith('.webm'):
                ext = '.webm'
            else:
                ext = '.mp4'

            filepath = self.videos_dir / f"{filename}{ext}"

            # Download the video
            with httpx.stream("GET", video_url, timeout=120.0, follow_redirects=True) as response:
                response.raise_for_status()

                with open(filepath, 'wb') as f:
                    for chunk in response.iter_bytes(chunk_size=8192):
                        f.write(chunk)

            # Get file size
            file_size = filepath.stat().st_size
            file_size_mb = round(file_size / (1024 * 1024), 2)

            return json.dumps({
                "status": "downloaded",
                "local_path": str(filepath),
                "filename": filepath.name,
                "size_mb": file_size_mb,
                "product_name": product_name,
                "platform": platform,
            })

        except httpx.HTTPError as e:
            return json.dumps({
                "status": "error",
                "message": f"Download failed: {str(e)}"
            })
        except Exception as e:
            return json.dumps({
                "status": "error",
                "message": f"Error saving video: {str(e)}"
            })

    def generate_and_download(
        self,
        prompt: str,
        product_name: Optional[str] = None,
        duration: int = 10,
        aspect_ratio: str = "9:16",
        max_wait: int = 180,
        poll_interval: int = 5,
        platform: Optional[str] = None,
    ) -> str:
        """
        Generate a video, wait for completion, and download to local folder.

        Args:
            prompt: Video description
            product_name: Product name for filename
            duration: Video length (1-15 seconds)
            aspect_ratio: Video aspect ratio
            max_wait: Maximum seconds to wait for generation
            poll_interval: Seconds between status checks
            platform: Target platform for folder organization

        Returns:
            JSON with local file path, video_url, and metadata
        """
        # Start generation
        gen_result = json.loads(self.generate_video(prompt, duration, aspect_ratio))

        if gen_result.get("status") == "error":
            return json.dumps(gen_result)

        request_id = gen_result.get("request_id")

        # Poll for completion
        elapsed = 0
        video_url = None
        while elapsed < max_wait:
            time.sleep(poll_interval)
            elapsed += poll_interval

            status_result = json.loads(self.check_video_status(request_id))

            if status_result.get("status") == "completed":
                video_url = status_result.get("video_url")
                break
            elif status_result.get("status") == "failed":
                return json.dumps({
                    "status": "failed",
                    "message": "Video generation failed",
                    "request_id": request_id
                })

        if not video_url:
            return json.dumps({
                "status": "timeout",
                "message": f"Video not ready after {max_wait} seconds",
                "request_id": request_id
            })

        # Download the video
        download_result = json.loads(self.download_video(
            video_url=video_url,
            product_name=product_name,
            platform=platform,
        ))

        if download_result.get("status") == "error":
            return json.dumps({
                "status": "partial",
                "message": "Video generated but download failed",
                "video_url": video_url,
                "request_id": request_id,
                "download_error": download_result.get("message")
            })

        return json.dumps({
            "status": "completed",
            "local_path": download_result.get("local_path"),
            "filename": download_result.get("filename"),
            "size_mb": download_result.get("size_mb"),
            "video_url": video_url,
            "request_id": request_id,
            "product_name": product_name,
            "platform": platform,
            "prompt": prompt,
        })


class GrokImageTools(Toolkit):
    """Tools for image generation using Grok Imagine"""

    def __init__(self, api_key: Optional[str] = None):
        super().__init__(name="grok_image_tools")
        self.api_key = api_key or XAI_API_KEY
        self.base_url = "https://api.x.ai/v1"

        self.client = OpenAI(
            api_key=self.api_key,
            base_url=self.base_url
        )

        self.register(self.generate_image)

    def generate_image(
        self,
        prompt: str,
        aspect_ratio: str = "1:1",
        style: str = "natural",
    ) -> str:
        """
        Generate an image using Grok Imagine.

        Args:
            prompt: Description of the image to generate
            aspect_ratio: Image aspect ratio (1:1, 16:9, 9:16, 4:5)
            style: Image style (natural, vivid, etc.)

        Returns:
            JSON with image URL
        """
        try:
            response = self.client.images.generate(
                model="grok-imagine",
                prompt=prompt,
                n=1,
            )

            image_url = response.data[0].url if response.data else None

            return json.dumps({
                "status": "completed",
                "image_url": image_url,
                "prompt": prompt,
            })

        except Exception as e:
            return json.dumps({
                "status": "error",
                "message": str(e)
            })
