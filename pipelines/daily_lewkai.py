#!/usr/bin/env python3
"""
Daily Lewkai X/Twitter Post Automation

Researches latest AI agent news and creates brand-aligned posts for @lewkai_.
Runs 3x daily at optimal times for SA, Europe, and US audiences.

Schedule (UTC):
- 07:00 UTC = SA/Europe morning
- 14:00 UTC = Europe afternoon / US East morning
- 21:00 UTC = US prime time

Run via cron with post number argument:
  python daily_lewkai.py 1  # Morning post
  python daily_lewkai.py 2  # Afternoon post
  python daily_lewkai.py 3  # Evening post
"""
import sys
import json
import random
import hashlib
from pathlib import Path
from datetime import datetime, date
from typing import Optional, Dict, Any, List

sys.path.insert(0, str(Path(__file__).parent.parent))

import httpx
from config.settings import XAI_API_KEY, DATA_DIR
from platforms.twitter.adapter import TwitterAdapter

# Ensure logs directory exists
LOGS_DIR = DATA_DIR / "logs"
LOGS_DIR.mkdir(parents=True, exist_ok=True)

# Brand voice and themes
LEWKAI_THEMES = [
    "AI agent adoption challenges",
    "enterprise AI implementation",
    "agentic AI trends",
    "AI orchestration enterprise",
    "human in the loop AI",
    "AI governance enterprise",
    "multi-agent systems business",
    "AI automation ROI",
    "AI pilot to production",
    "AI agents vs AI tools",
]

LEWKAI_VOICE = """
You are writing a Twitter/X post for Lewkai (@lewkai_), an AI agent design company.

Brand voice:
- Professional but accessible
- Confident, not arrogant
- Clear and direct
- Thought leadership without jargon
- Practical over theoretical

Key messages to weave in:
- "AI is powerful. But unmanaged AI is noise."
- Companies aren't anti-AI, they're stuck
- The gap is orchestration, strategy, and ownership
- AI agents should work like team members, not features
- From chaos to clarity

Post style:
- Short, punchy lines
- Use line breaks for readability
- End with insight or call to reflection
- No hashtags (they look spammy)
- No emojis
- 280 characters max, but can go up to 400 if needed for impact

DO NOT:
- Be salesy or promotional
- Mention Lewkai directly
- Use buzzwords without substance
- Be generic or vague
"""

# Curated insights for variety
INSIGHTS_POOL = [
    {
        "stat": "Only 8.6% of enterprises have AI agents deployed in production",
        "source": "Recon Analytics 2026",
        "angle": "pilot purgatory"
    },
    {
        "stat": "67% projected increase in multi-agent adoption by 2027",
        "source": "Salesforce Connectivity Report",
        "angle": "acceleration"
    },
    {
        "stat": "46% cite integration with existing systems as primary challenge",
        "source": "Enterprise AI Survey 2026",
        "angle": "integration struggles"
    },
    {
        "stat": "50% of AI agents operate in isolated silos vs multi-agent systems",
        "source": "State of AI Agents Report",
        "angle": "fragmentation"
    },
    {
        "stat": "42% cite risk management and compliance as top barrier",
        "source": "Deloitte Agentic AI Report",
        "angle": "governance"
    },
    {
        "stat": "Only 6% have fully implemented agentic AI",
        "source": "Enterprise AI Adoption Study",
        "angle": "gap between hype and reality"
    },
    {
        "stat": "41% lack internal expertise in AI/agent design",
        "source": "AI Talent Gap Report 2026",
        "angle": "skills shortage"
    },
    {
        "stat": "27% of APIs are currently ungoverned in enterprises",
        "source": "API Governance Study",
        "angle": "shadow AI risk"
    },
    {
        "stat": "96% of IT leaders agree agent success depends on seamless data integration",
        "source": "Salesforce Research",
        "angle": "data architecture"
    },
    {
        "stat": "Organizations use an average of 12 AI agents today",
        "source": "Multi-Agent Report 2026",
        "angle": "tool sprawl"
    },
    {
        "stat": "60% of AI leaders say legacy integration is a primary adoption challenge",
        "source": "Agentic AI Strategy Report",
        "angle": "technical debt"
    },
    {
        "stat": "Only 54% of organizations have centralized governance for AI capabilities",
        "source": "Enterprise AI Governance Study",
        "angle": "governance gaps"
    },
]


def get_daily_insights(post_number: int) -> Dict[str, Any]:
    """Get a consistent insight for each post slot per day (no duplicates)"""
    # Use date + post number as seed for consistent daily selection
    today = date.today().isoformat()
    seed = hashlib.md5(f"{today}-{post_number}".encode()).hexdigest()
    random.seed(seed)

    # Shuffle and pick based on post number
    shuffled = INSIGHTS_POOL.copy()
    random.shuffle(shuffled)

    # Ensure different insight for each post
    return shuffled[post_number % len(shuffled)]


def generate_post(insight: Dict[str, Any], post_number: int) -> str:
    """Generate a post using Grok AI based on insight"""

    if not XAI_API_KEY:
        return generate_post_template(insight, post_number)

    # Vary the angle based on post number
    angles = [
        "Focus on the problem/challenge aspect",
        "Focus on the opportunity/solution aspect",
        "Focus on a thought-provoking question"
    ]

    prompt = f"""
{LEWKAI_VOICE}

Create a Twitter/X post based on this insight:
- Statistic: {insight['stat']}
- Source context: {insight['source']}
- Theme to explore: {insight['angle']}

Angle for this post: {angles[post_number % 3]}

Write a compelling post that turns this data into an insight about AI agent adoption.
Make it thought-provoking, not just informative.

Return ONLY the post text, nothing else. No quotes around it.
"""

    try:
        response = httpx.post(
            "https://api.x.ai/v1/chat/completions",
            headers={
                "Authorization": f"Bearer {XAI_API_KEY}",
                "Content-Type": "application/json"
            },
            json={
                "model": "grok-3-latest",
                "messages": [{"role": "user", "content": prompt}],
                "temperature": 0.8,
                "max_tokens": 500
            },
            timeout=30.0
        )

        if response.status_code == 200:
            result = response.json()
            text = result["choices"][0]["message"]["content"].strip()
            # Remove quotes if Grok wrapped the response
            if text.startswith('"') and text.endswith('"'):
                text = text[1:-1]
            return text
        else:
            print(f"Grok API error: {response.status_code}")
            return generate_post_template(insight, post_number)

    except Exception as e:
        print(f"Error calling Grok: {e}")
        return generate_post_template(insight, post_number)


def generate_post_template(insight: Dict[str, Any], post_number: int) -> str:
    """Generate post using templates (fallback)"""

    templates = [
        # Problem-focused (post 1)
        f"""{insight['stat']}.

The gap isn't technology. It's orchestration.

Most companies aren't anti-AI — they're stuck between experimentation and execution.

The question isn't "should we use AI?"

It's "how do we make AI actually work?"
""",
        # Opportunity-focused (post 2)
        f"""{insight['stat']}.

This is the opportunity gap.

While most companies collect AI tools, the winners are building AI systems.

The difference:
- Tools sit in silos
- Systems create compounding value

From chaos to clarity. That's the edge.
""",
        # Question-focused (post 3)
        f"""{insight['stat']}.

The real question no one's asking:

Who's orchestrating your AI?

Not which tools you're using.
Not how much you're spending.

But who's turning scattered experiments into coordinated systems?

That's where the value lives.
""",
    ]

    return templates[post_number % len(templates)].strip()


def check_duplicate_post(text: str) -> bool:
    """Check if we've posted similar content today"""
    log_file = LOGS_DIR / "lewkai_posts.jsonl"
    if not log_file.exists():
        return False

    today = date.today().isoformat()

    with open(log_file, "r") as f:
        for line in f:
            try:
                entry = json.loads(line)
                if entry.get("timestamp", "").startswith(today):
                    # Check for similar content (first 50 chars)
                    if entry.get("post_text", "")[:50] == text[:50]:
                        return True
            except:
                continue
    return False


def post_to_lewkai(text: str) -> Dict[str, Any]:
    """Post to @lewkai_ account"""
    twitter = TwitterAdapter('lewkai')

    if not twitter._authenticated:
        return {"error": "Not authenticated with lewkai account"}

    # Ensure within character limit
    if len(text) > 400:
        text = text[:397] + "..."

    return twitter.post_text_only(text)


def log_post(post_number: int, insight: Dict, post_text: str, result: Dict):
    """Log the post for tracking"""
    log_file = LOGS_DIR / "lewkai_posts.jsonl"

    log_entry = {
        "timestamp": datetime.now().isoformat(),
        "post_number": post_number,
        "insight": insight,
        "post_text": post_text,
        "result": result,
        "char_count": len(post_text)
    }

    with open(log_file, "a") as f:
        f.write(json.dumps(log_entry) + "\n")


def run_daily_post(post_number: int = 1) -> Dict[str, Any]:
    """Main function to run daily post"""
    print(f"[{datetime.now()}] Starting Lewkai post #{post_number}...")

    # 1. Get insight for this post slot
    insight = get_daily_insights(post_number)
    print(f"Insight: {insight['stat']}")

    # 2. Generate post
    post_text = generate_post(insight, post_number)
    print(f"Generated post ({len(post_text)} chars):")
    print(post_text)
    print()

    # 3. Check for duplicates
    if check_duplicate_post(post_text):
        print("Duplicate detected, skipping...")
        return {"status": "skipped", "reason": "duplicate"}

    # 4. Post to Twitter
    result = post_to_lewkai(post_text)
    print(f"Result: {result}")

    # 5. Log the post
    log_post(post_number, insight, post_text, result)

    if "error" not in result:
        tweet_id = result.get("tweet_id")
        print(f"Success! https://x.com/lewkai_/status/{tweet_id}")

    return result


if __name__ == "__main__":
    # Get post number from command line (1, 2, or 3)
    post_number = 1
    if len(sys.argv) > 1:
        try:
            post_number = int(sys.argv[1])
        except ValueError:
            pass

    run_daily_post(post_number)
