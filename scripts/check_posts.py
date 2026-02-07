#!/usr/bin/env python3
"""
Quick daily post status checker for Lewkai automation.

Usage:
  python scripts/check_posts.py         # Today's posts
  python scripts/check_posts.py --week  # Last 7 days
"""
import sys
import json
from pathlib import Path
from datetime import datetime, date, timedelta
from collections import defaultdict

# Find project root
SCRIPT_DIR = Path(__file__).parent
PROJECT_ROOT = SCRIPT_DIR.parent
LOGS_DIR = PROJECT_ROOT / "data" / "logs"
LOG_FILE = LOGS_DIR / "lewkai_posts.jsonl"


def load_posts(days: int = 1) -> list:
    """Load posts from the last N days"""
    if not LOG_FILE.exists():
        return []

    cutoff = datetime.now() - timedelta(days=days)
    posts = []

    with open(LOG_FILE, "r") as f:
        for line in f:
            try:
                entry = json.loads(line)
                timestamp = datetime.fromisoformat(entry["timestamp"])
                if timestamp >= cutoff:
                    posts.append(entry)
            except:
                continue

    return posts


def format_post(post: dict) -> str:
    """Format a single post for display"""
    ts = datetime.fromisoformat(post["timestamp"])
    result = post.get("result", {})

    status = "✓" if result.get("status") == "posted" else "✗"
    tweet_id = result.get("tweet_id", "N/A")
    chars = post.get("char_count", 0)
    post_num = post.get("post_number", "?")

    # Truncate post text
    text = post.get("post_text", "")[:60].replace("\n", " ")
    if len(post.get("post_text", "")) > 60:
        text += "..."

    return f"{status} Post #{post_num} | {ts.strftime('%H:%M')} | {chars} chars | {text}"


def print_daily_report(posts: list, day: date):
    """Print report for a single day"""
    day_posts = [p for p in posts if datetime.fromisoformat(p["timestamp"]).date() == day]

    print(f"\n{'='*60}")
    print(f"  {day.strftime('%A, %B %d, %Y')}")
    print(f"{'='*60}")

    if not day_posts:
        print("  No posts recorded")
        return

    success = sum(1 for p in day_posts if p.get("result", {}).get("status") == "posted")
    print(f"  Posts: {success}/{len(day_posts)} successful\n")

    for post in sorted(day_posts, key=lambda x: x["timestamp"]):
        print(f"  {format_post(post)}")

        # Show tweet link if successful
        tweet_id = post.get("result", {}).get("tweet_id")
        if tweet_id:
            print(f"    → https://x.com/lewkai_/status/{tweet_id}")


def print_summary(posts: list, days: int):
    """Print summary statistics"""
    total = len(posts)
    success = sum(1 for p in posts if p.get("result", {}).get("status") == "posted")

    print(f"\n{'='*60}")
    print(f"  SUMMARY ({days} day{'s' if days > 1 else ''})")
    print(f"{'='*60}")
    print(f"  Total posts attempted: {total}")
    print(f"  Successful: {success}")
    print(f"  Failed: {total - success}")
    if total > 0:
        print(f"  Success rate: {success/total*100:.0f}%")


def main():
    # Parse args
    days = 1
    if "--week" in sys.argv:
        days = 7
    elif len(sys.argv) > 1:
        try:
            days = int(sys.argv[1])
        except:
            pass

    print(f"\n🐦 LEWKAI DAILY POST REPORT")

    posts = load_posts(days)

    if not posts:
        print(f"\nNo posts found in the last {days} day(s)")
        print(f"Log file: {LOG_FILE}")
        return

    # Group by day
    if days == 1:
        print_daily_report(posts, date.today())
    else:
        for i in range(days):
            day = date.today() - timedelta(days=i)
            print_daily_report(posts, day)

    print_summary(posts, days)
    print()


if __name__ == "__main__":
    main()
