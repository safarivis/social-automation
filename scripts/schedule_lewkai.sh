#!/bin/bash
# Daily Lewkai Post Scheduler
#
# Add to crontab with: crontab -e
# Then add: 0 9 * * * /home/louisdup/Agents/garyV/social-automation/scripts/schedule_lewkai.sh
#
# This runs daily at 9 AM

cd /home/louisdup/Agents/garyV/social-automation
source .venv/bin/activate
python pipelines/daily_lewkai.py >> data/logs/cron.log 2>&1
