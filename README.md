# Multi-Platform Social Media Automation

Automated content creation and posting across TikTok, Instagram, YouTube, Twitter/X, and LinkedIn.

## Quick Start

```bash
# Install dependencies
pip install -r requirements.txt

# Run interactive mode
python main.py

# Show platform status
python main.py platforms

# List campaigns
python main.py campaigns

# Run a campaign (dry run)
python main.py run tech_daily

# Run a campaign (live)
python main.py run tech_daily --live --post
```

## Project Structure

```
social-automation/
├── core/                    # Shared components
│   ├── models.py           # Pydantic models
│   └── base_agents.py      # Configurable agent base class
├── platforms/              # Platform adapters
│   ├── base.py            # Abstract platform interface
│   ├── tiktok/            # TikTok adapter
│   ├── instagram/         # Instagram (Reels, Images, Carousels)
│   ├── youtube/           # YouTube (Shorts, Long-form)
│   ├── twitter/           # X (Text, Images, Video)
│   └── linkedin/          # LinkedIn (Posts, Video, Documents)
├── campaigns/              # Campaign configurations
│   ├── loader.py          # YAML campaign loader
│   └── templates/         # Campaign definitions
│       ├── tech_daily.yaml
│       ├── beauty_wellness.yaml
│       └── home_kitchen.yaml
├── config/
│   ├── settings.py        # API keys, paths, settings
│   └── prompts/           # Configurable prompts
│       ├── research/      # Product research templates
│       └── content/       # Platform-specific scripts
├── tools/                  # Shared tools
│   ├── amazon_tools.py    # Product research
│   └── video_tools.py     # Grok video generation
├── pipelines/              # Orchestration
│   └── multi_platform.py  # Cross-platform pipeline
├── data/                   # Storage
└── main.py                 # Entry point
```

## Configuration

### API Keys

Add credentials to `~/Agents/.env`:

```env
# xAI / Grok
XAI_API_KEY=your_key

# TikTok
TIKTOK_CLIENT_KEY=your_key
TIKTOK_CLIENT_SECRET=your_secret

# Instagram / Facebook
FACEBOOK_APP_ID=your_id
FACEBOOK_APP_SECRET=your_secret

# YouTube / Google
GOOGLE_CLIENT_ID=your_id
GOOGLE_CLIENT_SECRET=your_secret

# Twitter / X
TWITTER_BEARER_TOKEN=your_token

# LinkedIn
LINKEDIN_CLIENT_ID=your_id
LINKEDIN_CLIENT_SECRET=your_secret

# Amazon Affiliate
AMAZON_AFFILIATE_TAG=yourtag-20
```

### Campaigns

Create YAML campaign files in `campaigns/templates/`:

```yaml
campaign:
  id: my_campaign
  name: "My Campaign"
  niche: tech_gadgets

research:
  template: affiliate
  price_range: [15, 75]
  products_per_run: 5

platforms:
  tiktok:
    enabled: true
    posts_per_day: 3
  instagram:
    enabled: true
    posts_per_day: 2
  youtube:
    enabled: true
    posts_per_day: 2
```

### Prompts

Customize content generation by editing YAML files in `config/prompts/`:
- `research/affiliate.yaml` - Product discovery prompts
- `content/tiktok.yaml` - TikTok script templates
- `content/instagram.yaml` - Instagram content templates
- etc.

## Commands

| Command | Description |
|---------|-------------|
| `python main.py` | Interactive mode |
| `python main.py platforms` | Show platform configuration status |
| `python main.py campaigns` | List available campaigns |
| `python main.py run <campaign>` | Run campaign (dry run) |
| `python main.py run <campaign> --live` | Run with media generation |
| `python main.py run <campaign> --live --post` | Run and post content |
| `python main.py test <platform>` | Test platform adapter |

## Platform Support

| Platform | Content Types | Status |
|----------|--------------|--------|
| TikTok | Short Video | ✓ Ready |
| Instagram | Reels, Images, Carousels | ✓ Ready |
| YouTube | Shorts, Long Video | ✓ Ready |
| Twitter/X | Text, Images, Video | ✓ Ready |
| LinkedIn | Text, Images, Video, PDF | ✓ Ready |

## License

Private - All rights reserved.
