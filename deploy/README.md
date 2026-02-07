# VPS Deployment Guide

## Quick Setup

### 1. Clone to VPS
```bash
ssh user@your-vps
git clone https://github.com/safarivis/social-automation.git
cd social-automation
```

### 2. Create .env file
```bash
nano .env
# Copy your API keys from local ~/Agents/.env
```

### 3. Install & Run
```bash
chmod +x deploy/setup.sh
./deploy/setup.sh
```

### 4. Enable Daily Posts
```bash
# Add to crontab
crontab -e

# Add this line (runs at 9 AM daily):
0 9 * * * cd /path/to/social-automation && .venv/bin/python pipelines/daily_lewkai.py >> data/logs/cron.log 2>&1
```

## Manual Commands

```bash
# Activate environment
source .venv/bin/activate

# Run daily post manually
python pipelines/daily_lewkai.py

# Check logs
tail -f data/logs/lewkai_posts.jsonl
tail -f data/logs/cron.log
```

## Systemd Service (Optional)

For a proper background service, use the provided systemd unit file:

```bash
sudo cp deploy/lewkai-scheduler.service /etc/systemd/system/
sudo systemctl enable lewkai-scheduler
sudo systemctl start lewkai-scheduler
```
