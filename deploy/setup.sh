#!/bin/bash
# VPS Setup Script for Social Automation

set -e

echo "=== Social Automation VPS Setup ==="

# Check Python
if ! command -v python3 &> /dev/null; then
    echo "Installing Python..."
    sudo apt update && sudo apt install -y python3 python3-pip python3-venv
fi

# Create virtual environment
echo "Creating virtual environment..."
python3 -m venv .venv
source .venv/bin/activate

# Install dependencies
echo "Installing dependencies..."
pip install --upgrade pip
pip install -r requirements.txt

# Create directories
echo "Creating directories..."
mkdir -p data/logs
mkdir -p data/products
mkdir -p data/scripts
mkdir -p data/videos

# Check .env
if [ ! -f .env ]; then
    echo ""
    echo "WARNING: No .env file found!"
    echo "Copy your API keys to .env before running."
    echo ""
fi

# Test imports
echo "Testing imports..."
python -c "import main; print('Imports OK')"

echo ""
echo "=== Setup Complete ==="
echo ""
echo "Next steps:"
echo "1. Create .env with your API keys"
echo "2. Test: python pipelines/daily_lewkai.py"
echo "3. Add cron job for daily posts"
