"""
Campaign Configuration Loader

Loads and validates campaign configurations from YAML files.
"""
from typing import Dict, Any, List, Optional
from pathlib import Path
import yaml
import sys

sys.path.insert(0, str(Path(__file__).parent.parent))
from core.models import CampaignConfig, Platform, ContentType
from config.settings import CAMPAIGNS_DIR


class CampaignLoader:
    """Loads campaign configurations from YAML files"""

    def __init__(self, campaigns_dir: Optional[Path] = None):
        self.campaigns_dir = campaigns_dir or CAMPAIGNS_DIR
        self.templates_dir = self.campaigns_dir / "templates"
        self._cache: Dict[str, CampaignConfig] = {}

    def list_campaigns(self) -> List[str]:
        """List all available campaign template files"""
        if not self.templates_dir.exists():
            return []

        return [
            f.stem for f in self.templates_dir.glob("*.yaml")
            if not f.name.startswith("_")
        ]

    def load_campaign(self, campaign_id: str) -> CampaignConfig:
        """
        Load a campaign configuration by ID.

        Args:
            campaign_id: Campaign identifier (filename without .yaml)

        Returns:
            CampaignConfig object
        """
        if campaign_id in self._cache:
            return self._cache[campaign_id]

        campaign_path = self.templates_dir / f"{campaign_id}.yaml"
        if not campaign_path.exists():
            raise FileNotFoundError(f"Campaign not found: {campaign_id}")

        with open(campaign_path, 'r') as f:
            data = yaml.safe_load(f)

        config = self._parse_campaign(data, campaign_id)
        self._cache[campaign_id] = config
        return config

    def _parse_campaign(self, data: Dict[str, Any], campaign_id: str) -> CampaignConfig:
        """Parse raw YAML data into CampaignConfig"""
        campaign_data = data.get("campaign", {})
        research_data = data.get("research", {})
        platforms_data = data.get("platforms", {})
        schedule_data = data.get("schedule", {})

        # Parse price range
        price_range = research_data.get("price_range", [15, 75])
        if isinstance(price_range, list) and len(price_range) == 2:
            price_range = tuple(price_range)
        else:
            price_range = (15, 75)

        return CampaignConfig(
            id=campaign_data.get("id", campaign_id),
            name=campaign_data.get("name", campaign_id),
            niche=campaign_data.get("niche", "general"),
            research_template=research_data.get("template", "affiliate"),
            price_range=price_range,
            products_per_run=research_data.get("products_per_run", 5),
            platforms=platforms_data,
            enabled=schedule_data.get("enabled", True),
            schedule=schedule_data.get("cron"),
        )

    def get_enabled_platforms(self, campaign: CampaignConfig) -> List[Platform]:
        """Get list of enabled platforms for a campaign"""
        enabled = []
        for platform_name, settings in campaign.platforms.items():
            if settings.get("enabled", True):
                try:
                    platform = Platform(platform_name.lower())
                    enabled.append(platform)
                except ValueError:
                    pass  # Skip invalid platform names
        return enabled

    def get_platform_settings(
        self,
        campaign: CampaignConfig,
        platform: Platform
    ) -> Dict[str, Any]:
        """Get settings for a specific platform in a campaign"""
        platform_name = platform.value
        return campaign.platforms.get(platform_name, {})

    def validate_campaign(self, campaign: CampaignConfig) -> List[str]:
        """
        Validate a campaign configuration.

        Returns:
            List of validation errors (empty if valid)
        """
        errors = []

        # Check required fields
        if not campaign.id:
            errors.append("Campaign ID is required")

        if not campaign.niche:
            errors.append("Campaign niche is required")

        # Validate platforms
        if not campaign.platforms:
            errors.append("At least one platform must be configured")

        for platform_name, settings in campaign.platforms.items():
            try:
                Platform(platform_name.lower())
            except ValueError:
                errors.append(f"Invalid platform: {platform_name}")

        # Validate price range
        if campaign.price_range[0] >= campaign.price_range[1]:
            errors.append("Price range minimum must be less than maximum")

        return errors


# Global loader instance
campaign_loader = CampaignLoader()


def load_campaign(campaign_id: str) -> CampaignConfig:
    """Convenience function to load a campaign"""
    return campaign_loader.load_campaign(campaign_id)


def list_campaigns() -> List[str]:
    """Convenience function to list campaigns"""
    return campaign_loader.list_campaigns()
