#!/usr/bin/env python3
"""
Daily Lewkai X/Twitter Post Automation

Researches latest AI agent news and creates brand-aligned posts for @lewkai_.
Run daily via cron or scheduler.
"""
import sys
import json
import random
from pathlib import Path
from datetime import datetime
from typing import Optional, Dict, Any

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


def search_news(query: str) -> str:
    """Search for latest news using web search (simplified)"""
    # For now, return curated recent stats and trends
    # In production, integrate with news API or web search

    recent_insights = [
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
    ]

    return json.dumps(random.choice(recent_insights))


def generate_post(insight: Dict[str, Any]) -> str:
    """Generate a post using Grok AI based on insight"""

    if not XAI_API_KEY:
        # Fallback to template-based generation
        return generate_post_template(insight)

    prompt = f"""
{LEWKAI_VOICE}

Create a Twitter/X post based on this insight:
- Statistic: {insight['stat']}
- Source context: {insight['source']}
- Angle to explore: {insight['angle']}

Write a compelling post that turns this data into an insight about AI agent adoption.
Make it thought-provoking, not just informative.

Return ONLY the post text, nothing else.
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
                "temperature": 0.7,
                "max_tokens": 500
            },
            timeout=30.0
        )

        if response.status_code == 200:
            result = response.json()
            return result["choices"][0]["message"]["content"].strip()
        else:
            print(f"Grok API error: {response.status_code}")
            return generate_post_template(insight)

    except Exception as e:
        print(f"Error calling Grok: {e}")
        return generate_post_template(insight)


def generate_post_template(insight: Dict[str, Any]) -> str:
    """Generate post using templates (fallback)"""

    templates = [
        # Data-led insight
        f"""{insight['stat']}.

The gap isn't technology.

It's orchestration.

Most companies aren't anti-AI — they're stuck between experimentation and execution.

The question isn't "should we use AI?"

It's "how do we make AI actually work?"
""",
        # Contrarian take
        f"""{insight['stat']}.

Everyone's talking about AI adoption.

Few are talking about AI orchestration.

The difference?

Adoption is adding tools.
Orchestration is building systems.

One creates noise.
The other creates value.
""",
        # Problem-solution frame
        f"""{insight['stat']}.

This isn't a technology problem.

It's an architecture problem.

AI agents without clear roles, boundaries, and coordination just create expensive chaos.

The future isn't more AI.

It's better orchestrated AI.
""",
        # Question-led
        f"""{insight['stat']}.

Why?

Not because companies don't want AI.

Because they don't know how to operationalize it.

The winners won't be early adopters.

They'll be the ones who figure out how to make AI agents work like team members.
""",
        # Future-focused
        f"""{insight['stat']}.

The next competitive divide won't be who uses AI.

It'll be who operates AI responsibly and at scale.

Companies that fail to build coordinated agent systems will move slower and take on more risk.

Those that succeed will compound advantage.
""",
    ]

    return random.choice(templates).strip()


def post_to_lewkai(text: str) -> Dict[str, Any]:
    """Post to @lewkai_ account"""
    twitter = TwitterAdapter('lewkai')

    if not twitter._authenticated:
        return {"error": "Not authenticated with lewkai account"}

    # Ensure within character limit
    if len(text) > 400:
        text = text[:397] + "..."

    return twitter.post_text_only(text)


def log_post(insight: Dict, post_text: str, result: Dict):
    """Log the post for tracking"""
    log_file = LOGS_DIR / "lewkai_posts.jsonl"

    log_entry = {
        "timestamp": datetime.now().isoformat(),
        "insight": insight,
        "post_text": post_text,
        "result": result,
        "char_count": len(post_text)
    }

    with open(log_file, "a") as f:
        f.write(json.dumps(log_entry) + "\n")


def run_daily_post() -> Dict[str, Any]:
    """Main function to run daily post"""
    print(f"[{datetime.now()}] Starting daily Lewkai post...")

    # 1. Get random theme and search for insights
    theme = random.choice(LEWKAI_THEMES)
    print(f"Theme: {theme}")

    # 2. Get insight data
    insight_json = search_news(theme)
    insight = json.loads(insight_json)
    print(f"Insight: {insight['stat']}")

    # 3. Generate post
    post_text = generate_post(insight)
    print(f"Generated post ({len(post_text)} chars):")
    print(post_text)
    print()

    # 4. Post to Twitter
    result = post_to_lewkai(post_text)
    print(f"Result: {result}")

    # 5. Log the post
    log_post(insight, post_text, result)

    if "error" not in result:
        tweet_id = result.get("tweet_id")
        print(f"Success! https://x.com/lewkai_/status/{tweet_id}")

    return result


if __name__ == "__main__":
    run_daily_post()
