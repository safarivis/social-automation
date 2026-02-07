#!/usr/bin/env python3
"""
Multi-Platform Social Media Automation

Main entry point for the social automation system.
Supports TikTok, Instagram, YouTube, Twitter/X, and LinkedIn.

Usage:
    python main.py                         # Interactive mode
    python main.py run <campaign>          # Run a campaign
    python main.py platforms               # Show platform status
    python main.py campaigns               # List available campaigns
    python main.py test <platform>         # Test a platform adapter
"""
import argparse
import sys
from pathlib import Path
from datetime import datetime

# Add project to path
sys.path.insert(0, str(Path(__file__).parent))

from config.settings import get_configured_platforms
from campaigns.loader import list_campaigns, load_campaign, campaign_loader
from platforms import get_adapter, get_all_adapters, get_authenticated_adapters
from core.models import Platform
from pipelines.multi_platform import MultiPlatformPipeline, run_pipeline


def show_banner():
    """Display the application banner"""
    print("""
╔══════════════════════════════════════════════════════════╗
║     Multi-Platform Social Media Automation               ║
║     ─────────────────────────────────────────────────    ║
║     TikTok • Instagram • YouTube • Twitter • LinkedIn    ║
╚══════════════════════════════════════════════════════════╝
    """)


def cmd_platforms():
    """Show platform configuration status"""
    print("\nPlatform Status:")
    print("-" * 50)

    adapters = get_all_adapters()

    for platform, adapter in adapters.items():
        status = "✓ Configured" if adapter.is_authenticated else "✗ Not configured"
        print(f"  {platform.value.ljust(12)} {status}")

    # Show which have credentials
    configured = get_configured_platforms()
    print(f"\nConfigured platforms: {len(configured)}/5")

    if not configured:
        print("\nTo configure platforms, add API credentials to ~/Agents/.env")
        print("See config/settings.py for required environment variables.")


def cmd_campaigns():
    """List available campaign configurations"""
    campaigns = list_campaigns()

    if not campaigns:
        print("\nNo campaigns found.")
        print("Create campaign templates in campaigns/templates/")
        return

    print("\nAvailable Campaigns:")
    print("-" * 50)

    for campaign_id in campaigns:
        try:
            config = load_campaign(campaign_id)
            platforms = campaign_loader.get_enabled_platforms(config)
            platform_str = ", ".join(p.value for p in platforms)
            print(f"  {campaign_id.ljust(20)} {config.niche.ljust(15)} [{platform_str}]")
        except Exception as e:
            print(f"  {campaign_id.ljust(20)} (error: {e})")


def cmd_run(campaign_id: str, products: int = 5, dry_run: bool = True, post: bool = False):
    """Run a campaign"""
    print(f"\nRunning campaign: {campaign_id}")
    print(f"Products: {products}")
    print(f"Mode: {'Dry run' if dry_run else 'Live'}")
    print(f"Post: {'Yes' if post else 'No (drafts only)'}")
    print("-" * 50)

    try:
        results = run_pipeline(
            campaign_id=campaign_id,
            products=products,
            generate_media=not dry_run,
            post=post,
            dry_run=dry_run,
        )

        print("\nResults:")
        for key, value in results.items():
            print(f"  {key}: {value}")

    except FileNotFoundError:
        print(f"\nError: Campaign '{campaign_id}' not found.")
        print("Use 'python main.py campaigns' to see available campaigns.")
    except Exception as e:
        print(f"\nError running campaign: {e}")


def cmd_test(platform_name: str):
    """Test a platform adapter"""
    try:
        platform = Platform(platform_name.lower())
    except ValueError:
        print(f"\nError: Unknown platform '{platform_name}'")
        print(f"Valid platforms: {[p.value for p in Platform]}")
        return

    adapter = get_adapter(platform)

    print(f"\nTesting {platform.value} adapter:")
    print("-" * 50)
    print(f"  Platform: {adapter.name}")
    print(f"  Authenticated: {adapter.is_authenticated}")
    print(f"  Content Types: {[ct.value for ct in adapter.get_supported_content_types()]}")
    print(f"  Best Posting Times: {adapter.get_best_posting_times()}")

    # Show optimal settings
    for content_type in adapter.get_supported_content_types():
        settings = adapter.get_optimal_settings(content_type)
        print(f"\n  Settings for {content_type.value}:")
        for key, value in settings.items():
            print(f"    {key}: {value}")


def cmd_interactive():
    """Interactive mode"""
    show_banner()

    print("Commands:")
    print("  'platforms' - Show platform status")
    print("  'campaigns' - List available campaigns")
    print("  'run <campaign> [count]' - Run a campaign")
    print("  'test <platform>' - Test a platform adapter")
    print("  'quit' - Exit")
    print()

    while True:
        try:
            user_input = input("\n> ").strip()

            if not user_input:
                continue

            parts = user_input.split()
            command = parts[0].lower()

            if command in ["quit", "exit", "q"]:
                print("Goodbye!")
                break

            elif command == "platforms":
                cmd_platforms()

            elif command == "campaigns":
                cmd_campaigns()

            elif command == "run":
                if len(parts) < 2:
                    print("Usage: run <campaign_id> [product_count]")
                    continue
                campaign_id = parts[1]
                products = int(parts[2]) if len(parts) > 2 else 5
                cmd_run(campaign_id, products, dry_run=True)

            elif command == "test":
                if len(parts) < 2:
                    print("Usage: test <platform>")
                    continue
                cmd_test(parts[1])

            elif command == "help":
                print("Commands: platforms, campaigns, run <campaign>, test <platform>, quit")

            else:
                print(f"Unknown command: {command}")
                print("Type 'help' for available commands.")

        except KeyboardInterrupt:
            print("\n\nInterrupted. Goodbye!")
            break
        except EOFError:
            print("\nGoodbye!")
            break
        except Exception as e:
            print(f"\nError: {e}")


def main():
    parser = argparse.ArgumentParser(
        description="Multi-Platform Social Media Automation",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  python main.py                     Interactive mode
  python main.py platforms           Show platform status
  python main.py campaigns           List campaigns
  python main.py run tech_daily      Run tech_daily campaign
  python main.py test tiktok         Test TikTok adapter
        """
    )

    subparsers = parser.add_subparsers(dest="command", help="Available commands")

    # platforms command
    subparsers.add_parser("platforms", help="Show platform configuration status")

    # campaigns command
    subparsers.add_parser("campaigns", help="List available campaigns")

    # run command
    run_parser = subparsers.add_parser("run", help="Run a campaign")
    run_parser.add_argument("campaign", help="Campaign ID to run")
    run_parser.add_argument(
        "-n", "--products",
        type=int,
        default=5,
        help="Number of products to process (default: 5)"
    )
    run_parser.add_argument(
        "--live",
        action="store_true",
        help="Run in live mode (generate media, actually post)"
    )
    run_parser.add_argument(
        "--post",
        action="store_true",
        help="Actually post content (default: drafts only)"
    )

    # test command
    test_parser = subparsers.add_parser("test", help="Test a platform adapter")
    test_parser.add_argument("platform", help="Platform to test")

    args = parser.parse_args()

    if args.command == "platforms":
        cmd_platforms()
    elif args.command == "campaigns":
        cmd_campaigns()
    elif args.command == "run":
        cmd_run(
            args.campaign,
            args.products,
            dry_run=not args.live,
            post=args.post
        )
    elif args.command == "test":
        cmd_test(args.platform)
    else:
        cmd_interactive()


if __name__ == "__main__":
    main()
