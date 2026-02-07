"""
Amazon Product Research Tools

Tools for finding trending products on Amazon for affiliate content.
Supports multi-platform content strategies.
"""
from typing import List, Dict, Any, Optional
from agno.tools import Toolkit
import json
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent))
from config.settings import AMAZON_AFFILIATE_TAG
from core.models import Platform


class AmazonTools(Toolkit):
    """Tools for Amazon product research"""

    def __init__(self, affiliate_tag: Optional[str] = None):
        super().__init__(name="amazon_tools")
        self.affiliate_tag = affiliate_tag or AMAZON_AFFILIATE_TAG

        # Register tools
        self.register(self.get_trending_products)
        self.register(self.get_product_details)
        self.register(self.generate_affiliate_link)
        self.register(self.get_products_by_niche)

    def get_trending_products(
        self,
        category: str = "all",
        market: str = "US",
        limit: int = 10,
        min_price: float = 10.0,
        max_price: float = 75.0,
    ) -> str:
        """
        Get trending products from Amazon bestseller lists.

        Args:
            category: Product category (electronics, beauty, home-garden, kitchen, etc.)
            market: Target market (US or UK)
            limit: Number of products to return
            min_price: Minimum price filter
            max_price: Maximum price filter

        Returns:
            JSON string with list of trending products
        """
        # Mock data for MVP - replace with real API/scraping later
        mock_products = [
            {
                "asin": "B09V3KXJPB",
                "name": "LED Strip Lights 50ft",
                "price": 24.99,
                "currency": "USD",
                "rating": 4.5,
                "reviews": 45000,
                "category": "electronics",
                "commission_rate": 0.04,
                "trend_score": 92,
                "url": "https://amazon.com/dp/B09V3KXJPB",
                "image_url": "https://m.media-amazon.com/images/I/71example.jpg",
                "why_trending": "Room decor trend on TikTok, RGB gaming setups popular",
                "content_angles": ["Show bedroom transformation", "Before/after", "Gaming setup upgrade"],
                "best_platforms": ["tiktok", "instagram", "youtube"],
            },
            {
                "asin": "B08N5WRWNW",
                "name": "Portable Blender USB Rechargeable",
                "price": 29.99,
                "currency": "USD",
                "rating": 4.4,
                "reviews": 78000,
                "category": "kitchen",
                "commission_rate": 0.06,
                "trend_score": 88,
                "url": "https://amazon.com/dp/B08N5WRWNW",
                "image_url": "https://m.media-amazon.com/images/I/71example2.jpg",
                "why_trending": "Fitness and health trend, on-the-go lifestyle",
                "content_angles": ["Morning routine", "Gym prep", "Protein shake demo"],
                "best_platforms": ["tiktok", "instagram", "youtube"],
            },
            {
                "asin": "B07PXGQC1Q",
                "name": "Sunset Lamp Projector",
                "price": 19.99,
                "currency": "USD",
                "rating": 4.3,
                "reviews": 32000,
                "category": "home-garden",
                "commission_rate": 0.05,
                "trend_score": 95,
                "url": "https://amazon.com/dp/B07PXGQC1Q",
                "image_url": "https://m.media-amazon.com/images/I/71example3.jpg",
                "why_trending": "Aesthetic room vibes, Instagram/TikTok photo lighting",
                "content_angles": ["Room transformation", "Golden hour any time", "Photo lighting hack"],
                "best_platforms": ["tiktok", "instagram"],
            },
            {
                "asin": "B08XVYZ123",
                "name": "Ice Roller for Face",
                "price": 9.99,
                "currency": "USD",
                "rating": 4.6,
                "reviews": 55000,
                "category": "beauty",
                "commission_rate": 0.07,
                "trend_score": 85,
                "url": "https://amazon.com/dp/B08XVYZ123",
                "image_url": "https://m.media-amazon.com/images/I/71example4.jpg",
                "why_trending": "Skincare routine, de-puffing, morning routine",
                "content_angles": ["Morning skincare routine", "Before/after puffiness", "Self-care Sunday"],
                "best_platforms": ["tiktok", "instagram", "youtube"],
            },
            {
                "asin": "B09ABC1234",
                "name": "Mini Waffle Maker",
                "price": 15.99,
                "currency": "USD",
                "rating": 4.7,
                "reviews": 92000,
                "category": "kitchen",
                "commission_rate": 0.06,
                "trend_score": 90,
                "url": "https://amazon.com/dp/B09ABC1234",
                "image_url": "https://m.media-amazon.com/images/I/71example5.jpg",
                "why_trending": "Quick breakfast, dorm room essential, cute food content",
                "content_angles": ["3 waffle recipes in 60 seconds", "Breakfast hack", "Dorm room cooking"],
                "best_platforms": ["tiktok", "instagram", "youtube"],
            },
            {
                "asin": "B0ADEF5678",
                "name": "Wireless Earbuds Pro",
                "price": 39.99,
                "currency": "USD",
                "rating": 4.4,
                "reviews": 28000,
                "category": "electronics",
                "commission_rate": 0.04,
                "trend_score": 82,
                "url": "https://amazon.com/dp/B0ADEF5678",
                "image_url": "https://m.media-amazon.com/images/I/71example6.jpg",
                "why_trending": "AirPods alternative, budget tech, work from home",
                "content_angles": ["AirPods dupe test", "Budget tech review", "WFH essentials"],
                "best_platforms": ["youtube", "twitter", "linkedin"],
            },
            {
                "asin": "B0BXYZ9876",
                "name": "Desk Organizer Set",
                "price": 32.99,
                "currency": "USD",
                "rating": 4.5,
                "reviews": 18000,
                "category": "home-garden",
                "commission_rate": 0.05,
                "trend_score": 78,
                "url": "https://amazon.com/dp/B0BXYZ9876",
                "image_url": "https://m.media-amazon.com/images/I/71example7.jpg",
                "why_trending": "Work from home, productivity, desk setup",
                "content_angles": ["Desk transformation", "Productivity setup", "Work from home upgrade"],
                "best_platforms": ["instagram", "youtube", "linkedin"],
            },
            {
                "asin": "B0CDEF1122",
                "name": "Posture Corrector",
                "price": 22.99,
                "currency": "USD",
                "rating": 4.2,
                "reviews": 42000,
                "category": "sports-outdoors",
                "commission_rate": 0.05,
                "trend_score": 80,
                "url": "https://amazon.com/dp/B0CDEF1122",
                "image_url": "https://m.media-amazon.com/images/I/71example8.jpg",
                "why_trending": "WFH posture issues, health awareness, before/after results",
                "content_angles": ["30 day posture challenge", "WFH back pain solution", "Before/after"],
                "best_platforms": ["tiktok", "youtube", "linkedin"],
            },
        ]

        # Filter by category
        if category != "all":
            mock_products = [p for p in mock_products if p["category"] == category]

        # Filter by price
        mock_products = [
            p for p in mock_products
            if min_price <= p["price"] <= max_price
        ]

        # Sort by trend score
        mock_products.sort(key=lambda x: x["trend_score"], reverse=True)

        return json.dumps(mock_products[:limit], indent=2)

    def get_products_by_niche(
        self,
        niche: str,
        market: str = "US",
        limit: int = 5,
    ) -> str:
        """
        Get products optimized for a specific content niche.

        Args:
            niche: Content niche (tech_gadgets, beauty_skincare, home_organization, kitchen_gadgets, fitness_wellness)
            market: Target market
            limit: Number of products

        Returns:
            JSON with niche-optimized products
        """
        niche_categories = {
            "tech_gadgets": ["electronics"],
            "beauty_skincare": ["beauty"],
            "home_organization": ["home-garden"],
            "kitchen_gadgets": ["kitchen"],
            "fitness_wellness": ["sports-outdoors"],
        }

        categories = niche_categories.get(niche, ["all"])

        products = []
        for cat in categories:
            result = json.loads(self.get_trending_products(category=cat, market=market, limit=limit))
            products.extend(result)

        # Sort by trend score and return top N
        products.sort(key=lambda x: x["trend_score"], reverse=True)

        return json.dumps(products[:limit], indent=2)

    def get_product_details(self, asin: str) -> str:
        """
        Get detailed information about a specific Amazon product.

        Args:
            asin: Amazon Standard Identification Number

        Returns:
            JSON string with product details
        """
        # Mock implementation - replace with real API later
        return json.dumps({
            "asin": asin,
            "name": "Product Name",
            "price": 29.99,
            "description": "Product description here",
            "features": ["Feature 1", "Feature 2", "Feature 3"],
            "commission_rate": 0.05,
            "rating": 4.5,
            "reviews": 10000,
        })

    def generate_affiliate_link(self, url: str, tag: Optional[str] = None) -> str:
        """
        Convert an Amazon URL to an affiliate link.

        Args:
            url: Amazon product URL
            tag: Optional custom affiliate tag

        Returns:
            Affiliate link with tracking tag
        """
        affiliate_tag = tag or self.affiliate_tag

        if "amazon.com" in url or "amazon.co.uk" in url:
            separator = "&" if "?" in url else "?"
            return f"{url}{separator}tag={affiliate_tag}"
        return url
