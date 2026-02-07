#!/usr/bin/env python3
"""
Comprehensive test suite for social-automation

Run with:
    cd ~/Agents/garyV/social-automation
    source .venv/bin/activate
    python tests/test_all.py
"""
import sys
from pathlib import Path

# Add project to path
sys.path.insert(0, str(Path(__file__).parent.parent))


def test_imports():
    """Phase 2: Test all modules can be imported"""
    print("Testing imports...")

    import core.models
    import core.base_agents
    import config.settings
    import platforms
    import campaigns.loader
    import tools.amazon_tools
    import tools.video_tools
    import pipelines.multi_platform
    import main

    print("  All imports successful")


def test_models():
    """Phase 2: Test Pydantic models and enums"""
    print("Testing models...")

    from core.models import Platform, ContentType, AspectRatio, Product

    # Test enum values
    assert Platform.TIKTOK.value == "tiktok", "Platform.TIKTOK should be 'tiktok'"
    assert ContentType.SHORT_VIDEO.value == "short_video", "ContentType.SHORT_VIDEO should be 'short_video'"
    assert AspectRatio.VERTICAL.value == "9:16", "AspectRatio.VERTICAL should be '9:16'"

    # Test model instantiation
    p = Product(
        asin="B123",
        name="Test Product",
        price=29.99,
        category="electronics",
        affiliate_link="https://amazon.com/dp/B123"
    )
    assert p.trend_score == 0, "Default trend_score should be 0"
    assert p.name == "Test Product"
    assert p.price == 29.99

    print("  Models work correctly")


def test_config_and_settings():
    """Phase 3: Test settings load and paths are created"""
    print("Testing configuration...")

    from config.settings import (
        PROJECT_ROOT, DATA_DIR, get_platform_setting, is_platform_configured
    )

    # Check paths exist
    assert PROJECT_ROOT.exists(), "PROJECT_ROOT should exist"
    assert DATA_DIR.exists(), "DATA_DIR should exist"

    # Check settings functions
    duration = get_platform_setting("tiktok", "default_duration", 10)
    assert duration == 10, "TikTok default_duration should be 10"

    max_duration = get_platform_setting("instagram", "max_duration", 90)
    assert max_duration == 90, "Instagram max_duration should be 90"

    # is_platform_configured returns False if no env vars set (expected)
    # Just verify the function runs without error
    is_platform_configured("tiktok")
    is_platform_configured("instagram")

    print("  Configuration works correctly")


def test_yaml_template_loading():
    """Phase 4: Test prompt and campaign templates load correctly"""
    print("Testing YAML template loading...")

    from core.base_agents import prompt_loader
    from campaigns.loader import list_campaigns, load_campaign

    # Test prompt loading
    template = prompt_loader.load_template("research", "affiliate")
    assert "base_prompt" in template, "affiliate template should have 'base_prompt'"
    assert "niches" in template, "affiliate template should have 'niches'"

    # Test content templates
    tiktok_template = prompt_loader.load_template("content", "tiktok")
    assert "instructions" in tiktok_template or "hook_types" in tiktok_template

    # Test campaign loading
    campaigns = list_campaigns()
    assert len(campaigns) >= 1, "Should have at least 1 campaign"
    assert "tech_daily" in campaigns, "'tech_daily' campaign should exist"

    config = load_campaign("tech_daily")
    assert config.niche == "tech_gadgets", "tech_daily niche should be 'tech_gadgets'"

    print("  YAML templates load correctly")


def test_platform_adapters():
    """Phase 5: Test all 5 platform adapters instantiate and implement interface"""
    print("Testing platform adapters...")

    from platforms import get_adapter, get_all_adapters, ADAPTERS
    from core.models import Platform, ContentType

    # Test all adapters load
    adapters = get_all_adapters()
    assert len(adapters) == 5, f"Should have 5 adapters, got {len(adapters)}"

    # Test each adapter
    for platform, adapter in adapters.items():
        # Check required attributes
        assert hasattr(adapter, 'platform'), f"{platform.value} should have 'platform' attribute"
        assert hasattr(adapter, 'get_script_instructions'), f"{platform.value} should have 'get_script_instructions'"
        assert hasattr(adapter, 'get_supported_content_types'), f"{platform.value} should have 'get_supported_content_types'"

        # Check content types
        types = adapter.get_supported_content_types()
        assert len(types) > 0, f"{platform.value} should support at least one content type"

        # Check settings
        settings = adapter.get_optimal_settings(types[0])
        has_required = "aspect_ratio" in settings or "max_length" in settings or "duration" in settings
        assert has_required, f"{platform.value} optimal_settings should have aspect_ratio, max_length, or duration"

        # Check script instructions
        instructions = adapter.get_script_instructions()
        assert len(instructions) > 100, f"{platform.value} should have detailed script instructions"

    print(f"  All 5 platform adapters work correctly")


def test_tools():
    """Phase 6: Test Amazon and Video tools work"""
    print("Testing tools...")

    import json
    from tools.amazon_tools import AmazonTools
    from tools.video_tools import GrokVideoTools

    # Test Amazon tools (mock data)
    amazon = AmazonTools()

    # Test get_trending_products
    products_json = amazon.get_trending_products(category="electronics", limit=3)
    products = json.loads(products_json)
    assert len(products) <= 3, "Should return at most 3 products"
    assert all("asin" in p for p in products), "All products should have 'asin'"
    assert all("name" in p for p in products), "All products should have 'name'"

    # Test niche products
    niche_json = amazon.get_products_by_niche("tech_gadgets", limit=5)
    niche_products = json.loads(niche_json)
    assert len(niche_products) <= 5, "Should return at most 5 products"

    # Test affiliate link generation
    link = amazon.generate_affiliate_link("https://amazon.com/dp/B123")
    assert "tag=" in link, "Affiliate link should have tag parameter"

    # Test video tools instantiation (no API call)
    video_tools = GrokVideoTools()
    assert video_tools.videos_dir.exists(), "Videos directory should exist"

    print("  Tools work correctly")


def test_campaigns_loader():
    """Additional: Test campaign loader functionality"""
    print("Testing campaign loader...")

    from campaigns.loader import campaign_loader, list_campaigns, load_campaign
    from core.models import Platform

    # List campaigns
    campaigns = list_campaigns()
    assert isinstance(campaigns, list), "list_campaigns should return a list"

    # Load each available campaign
    for campaign_id in campaigns:
        config = load_campaign(campaign_id)

        # Basic validation
        assert config.id, f"{campaign_id} should have an id"
        assert config.niche, f"{campaign_id} should have a niche"

        # Check enabled platforms
        platforms = campaign_loader.get_enabled_platforms(config)
        assert len(platforms) >= 1, f"{campaign_id} should have at least 1 enabled platform"

        # Validate campaign
        errors = campaign_loader.validate_campaign(config)
        assert len(errors) == 0, f"{campaign_id} validation errors: {errors}"

    print(f"  All {len(campaigns)} campaigns load and validate correctly")


def test_pipeline_init():
    """Phase 8: Test pipeline initialization"""
    print("Testing pipeline initialization...")

    from pipelines.multi_platform import MultiPlatformPipeline

    # Create pipeline in dry run mode
    pipeline = MultiPlatformPipeline(dry_run=True)
    assert pipeline.dry_run == True, "Pipeline should be in dry run mode"

    # Load campaign
    pipeline.load_campaign("tech_daily")
    assert pipeline.campaign is not None, "Campaign should be loaded"
    assert pipeline.campaign.niche == "tech_gadgets"

    # Research products
    products = pipeline.research_products(count=2)
    assert len(products) == 2, "Should return 2 products"
    assert len(pipeline.products) == 2, "Pipeline should store 2 products"

    print("  Pipeline initialization works correctly")


def test_all():
    """Run all tests"""
    print("\n" + "="*60)
    print("Social Automation - Test Suite")
    print("="*60 + "\n")

    tests = [
        ("Imports", test_imports),
        ("Models", test_models),
        ("Configuration", test_config_and_settings),
        ("YAML Templates", test_yaml_template_loading),
        ("Platform Adapters", test_platform_adapters),
        ("Tools", test_tools),
        ("Campaigns Loader", test_campaigns_loader),
        ("Pipeline", test_pipeline_init),
    ]

    passed = 0
    failed = 0
    errors = []

    for name, test_func in tests:
        try:
            test_func()
            passed += 1
            print(f"  PASS: {name}\n")
        except AssertionError as e:
            failed += 1
            errors.append((name, str(e)))
            print(f"  FAIL: {name} - {e}\n")
        except Exception as e:
            failed += 1
            errors.append((name, f"Error: {e}"))
            print(f"  ERROR: {name} - {e}\n")

    print("="*60)
    print(f"Results: {passed} passed, {failed} failed")
    print("="*60)

    if errors:
        print("\nFailures:")
        for name, error in errors:
            print(f"  - {name}: {error}")
        print()
        return False
    else:
        print("\nALL TESTS PASSED\n")
        return True


if __name__ == "__main__":
    success = test_all()
    sys.exit(0 if success else 1)
