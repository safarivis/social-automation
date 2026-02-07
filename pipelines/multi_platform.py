"""
Multi-Platform Content Pipeline

Orchestrates content creation and posting across multiple platforms.
"""
from typing import List, Dict, Any, Optional
from datetime import datetime
import json
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent))

from agno.agent import Agent
from agno.models.xai import xAI
from agno.db.sqlite import SqliteDb

from core.models import (
    Platform, ContentType, Product, ContentScript, ContentPackage,
    CampaignConfig, ResearchConfig
)
from core.base_agents import prompt_loader, create_agent
from platforms import get_adapter, get_authenticated_adapters
from tools.amazon_tools import AmazonTools
from tools.video_tools import GrokVideoTools
from campaigns.loader import load_campaign, campaign_loader
from config.settings import DB_FILE, GROK_TEXT_MODEL


class MultiPlatformPipeline:
    """
    Orchestrates content generation and posting across multiple platforms.

    Workflow:
    1. Load campaign configuration
    2. Research products using configured template
    3. Generate platform-specific scripts for each product
    4. Create media (videos/images) for each platform
    5. Post to enabled platforms (or save as drafts)
    """

    def __init__(
        self,
        campaign_id: Optional[str] = None,
        dry_run: bool = False,
    ):
        self.campaign_id = campaign_id
        self.campaign: Optional[CampaignConfig] = None
        self.dry_run = dry_run  # If True, don't actually post

        # Database
        self.db = SqliteDb(db_file=str(DB_FILE))

        # Tools
        self.amazon_tools = AmazonTools()
        self.video_tools = GrokVideoTools()

        # Results tracking
        self.products: List[Product] = []
        self.content_packages: Dict[Platform, List[ContentPackage]] = {}
        self.results: Dict[str, Any] = {}

    def load_campaign(self, campaign_id: str) -> CampaignConfig:
        """Load campaign configuration"""
        self.campaign_id = campaign_id
        self.campaign = load_campaign(campaign_id)
        return self.campaign

    def research_products(
        self,
        count: int = 5,
        niche: Optional[str] = None,
    ) -> List[Dict[str, Any]]:
        """
        Research trending products based on campaign or manual settings.

        Returns:
            List of product dictionaries
        """
        if self.campaign:
            niche = niche or self.campaign.niche
            price_range = self.campaign.price_range
        else:
            price_range = (15, 75)
            niche = niche or "tech_gadgets"

        # Get products by niche
        products_json = self.amazon_tools.get_products_by_niche(
            niche=niche,
            limit=count,
        )

        products = json.loads(products_json)

        # Store as Product objects
        self.products = [
            Product(
                asin=p["asin"],
                name=p["name"],
                price=p["price"],
                category=p["category"],
                affiliate_link=self.amazon_tools.generate_affiliate_link(p["url"]),
                image_url=p.get("image_url"),
                trend_score=p.get("trend_score", 0),
                why_trending=p.get("why_trending", ""),
                content_angles=p.get("content_angles", []),
                commission_rate=p.get("commission_rate", 0.04),
            )
            for p in products
        ]

        return products

    def create_product_scout_agent(self) -> Agent:
        """Create the product scout agent"""
        try:
            template = prompt_loader.load_template("research", "affiliate")
            instructions = template.get("base_prompt", "")
        except FileNotFoundError:
            instructions = "Find trending products for affiliate marketing."

        return create_agent(
            name="Product Scout",
            model_id=GROK_TEXT_MODEL,
            db_file=DB_FILE,
            instructions=instructions,
            tools=[self.amazon_tools],
            learning=True,
        )

    def create_script_writer_agent(self, platform: Platform) -> Agent:
        """Create a platform-specific script writer agent"""
        platform_name = platform.value.lower()

        try:
            template = prompt_loader.load_template("content", platform_name)
            instructions = template.get("instructions", "")
        except FileNotFoundError:
            # Fall back to generic instructions
            adapter = get_adapter(platform)
            instructions = adapter.get_script_instructions()

        return create_agent(
            name=f"Script Writer ({platform.value})",
            model_id=GROK_TEXT_MODEL,
            db_file=DB_FILE,
            instructions=instructions,
            learning=True,
        )

    def generate_scripts(
        self,
        product: Product,
        platforms: Optional[List[Platform]] = None,
    ) -> Dict[Platform, ContentScript]:
        """
        Generate scripts for a product across specified platforms.

        Args:
            product: Product to create content for
            platforms: Platforms to target (defaults to campaign platforms)

        Returns:
            Dict mapping platform to generated script
        """
        if platforms is None:
            if self.campaign:
                platforms = campaign_loader.get_enabled_platforms(self.campaign)
            else:
                platforms = list(Platform)

        scripts = {}

        for platform in platforms:
            agent = self.create_script_writer_agent(platform)

            # Build prompt with product context
            content_angle = product.content_angles[0] if product.content_angles else "Product demo"

            prompt = f"""
            Create a {platform.value} script for this product:

            Product: {product.name}
            Price: ${product.price}
            Category: {product.category}
            Why Trending: {product.why_trending}
            Content Angle: {content_angle}

            Generate a complete script package including hook, problem, solution, CTA,
            full voiceover, caption, hashtags, and a prompt for AI video generation.
            """

            try:
                response = agent.run(prompt)

                # Parse response into ContentScript
                # In production, use structured output
                script = ContentScript(
                    product_name=product.name,
                    platform=platform,
                    content_type=ContentType.SHORT_VIDEO,
                    hook=f"This ${product.price} {product.category} changed everything",
                    hook_variations=[],
                    problem=product.why_trending,
                    solution=f"{product.name} solves this perfectly",
                    cta="Link in bio",
                    full_voiceover=response.content[:500] if response.content else "",
                    duration_estimate=15,
                    caption=f"{product.name} - {content_angle}",
                    hashtags=["#ad", f"#{product.category.replace('-', '')}"],
                    media_prompt=f"Product demonstration video for {product.name}, {platform.value} style",
                )

                scripts[platform] = script

            except Exception as e:
                print(f"Error generating script for {platform}: {e}")

        return scripts

    def generate_media(
        self,
        script: ContentScript,
        product: Product,
    ) -> Optional[str]:
        """
        Generate video/image media for a script.

        Returns:
            Path to generated media file, or None if failed
        """
        result_json = self.video_tools.generate_for_platform(
            prompt=script.media_prompt,
            platform=script.platform.value,
            product_name=product.name,
        )

        result = json.loads(result_json)

        if result.get("status") == "completed":
            return result.get("local_path")
        else:
            print(f"Media generation failed: {result.get('message', 'Unknown error')}")
            return None

    def create_content_packages(
        self,
        product: Product,
        scripts: Dict[Platform, ContentScript],
        generate_media: bool = True,
    ) -> Dict[Platform, ContentPackage]:
        """
        Create complete content packages for a product.

        Args:
            product: The product
            scripts: Platform-specific scripts
            generate_media: Whether to generate videos/images

        Returns:
            Dict mapping platform to content package
        """
        packages = {}

        for platform, script in scripts.items():
            # Generate media if requested
            media_path = None
            if generate_media and not self.dry_run:
                media_path = self.generate_media(script, product)

            package = ContentPackage(
                id=f"{product.asin}_{platform.value}_{datetime.now().strftime('%Y%m%d%H%M%S')}",
                product=product,
                platform=platform,
                content_type=script.content_type,
                script=script,
                media_path=media_path,
                status="ready" if media_path else "draft",
            )

            packages[platform] = package

            # Track in instance
            if platform not in self.content_packages:
                self.content_packages[platform] = []
            self.content_packages[platform].append(package)

        return packages

    def post_content(
        self,
        package: ContentPackage,
        draft: bool = False,
    ) -> Dict[str, Any]:
        """
        Post a content package to its platform.

        Args:
            package: Content package to post
            draft: If True, post as draft/private

        Returns:
            Posting result
        """
        if self.dry_run:
            return {
                "status": "dry_run",
                "message": f"Would post to {package.platform.value}",
                "package_id": package.id,
            }

        adapter = get_adapter(package.platform)

        if not adapter.is_authenticated:
            return {
                "status": "error",
                "message": f"Not authenticated with {package.platform.value}",
            }

        # Validate content
        errors = adapter.validate_content(package)
        if errors:
            return {
                "status": "invalid",
                "errors": errors,
            }

        # Post
        if draft:
            result = adapter.post_draft(package)
        else:
            result = adapter.post_content(package)

        # Update package status
        if result.get("status") == "posted":
            package.status = "posted"
            package.posted_at = datetime.now()
            package.post_id = result.get("post_id")

        return result

    def run_campaign(
        self,
        campaign_id: Optional[str] = None,
        products_count: int = 5,
        generate_media: bool = True,
        post: bool = False,
    ) -> Dict[str, Any]:
        """
        Run a complete campaign workflow.

        Args:
            campaign_id: Campaign to run (or use loaded campaign)
            products_count: Number of products to process
            generate_media: Whether to generate videos/images
            post: Whether to actually post (False = draft only)

        Returns:
            Campaign results summary
        """
        start_time = datetime.now()

        # Load campaign if specified
        if campaign_id:
            self.load_campaign(campaign_id)

        print(f"\n{'='*60}")
        print(f"Multi-Platform Content Pipeline")
        print(f"Campaign: {self.campaign.name if self.campaign else 'Manual'}")
        print(f"Time: {start_time.strftime('%Y-%m-%d %H:%M:%S')}")
        print(f"{'='*60}\n")

        # Step 1: Research products
        print("Step 1: Researching products...")
        products = self.research_products(count=products_count)
        print(f"  Found {len(products)} products\n")

        # Get target platforms
        if self.campaign:
            platforms = campaign_loader.get_enabled_platforms(self.campaign)
        else:
            platforms = list(Platform)
        print(f"Target platforms: {[p.value for p in platforms]}\n")

        # Step 2-4: Process each product
        all_packages = []
        for i, product in enumerate(self.products):
            print(f"Processing product {i+1}/{len(self.products)}: {product.name}")

            # Generate scripts
            print("  Generating scripts...")
            scripts = self.generate_scripts(product, platforms)

            # Create content packages
            print("  Creating content packages...")
            packages = self.create_content_packages(
                product, scripts, generate_media=generate_media
            )

            all_packages.extend(packages.values())
            print(f"  Created {len(packages)} packages\n")

        # Step 5: Post content
        if post:
            print("Posting content...")
            for package in all_packages:
                result = self.post_content(package, draft=not post)
                print(f"  {package.platform.value}: {result.get('status')}")

        # Summary
        end_time = datetime.now()
        duration = (end_time - start_time).total_seconds()

        self.results = {
            "campaign_id": self.campaign_id,
            "products_processed": len(self.products),
            "packages_created": len(all_packages),
            "platforms": [p.value for p in platforms],
            "duration_seconds": duration,
            "dry_run": self.dry_run,
            "posted": post,
        }

        print(f"\n{'='*60}")
        print("Pipeline Complete!")
        print(f"Products: {len(self.products)}")
        print(f"Packages: {len(all_packages)}")
        print(f"Duration: {duration:.1f}s")
        print(f"{'='*60}\n")

        return self.results


def run_pipeline(
    campaign_id: str,
    products: int = 5,
    generate_media: bool = True,
    post: bool = False,
    dry_run: bool = True,
) -> Dict[str, Any]:
    """
    Convenience function to run the pipeline.

    Args:
        campaign_id: Campaign configuration to use
        products: Number of products to process
        generate_media: Whether to generate videos
        post: Whether to post (False = drafts only)
        dry_run: If True, simulate without actual API calls

    Returns:
        Pipeline results
    """
    pipeline = MultiPlatformPipeline(dry_run=dry_run)
    return pipeline.run_campaign(
        campaign_id=campaign_id,
        products_count=products,
        generate_media=generate_media,
        post=post,
    )
