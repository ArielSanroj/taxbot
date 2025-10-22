#!/bin/bash

# TaxBot Cron Setup Script
# This script sets up automated daily scraping via cron

set -e

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Get script directory
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_DIR="$(dirname "$SCRIPT_DIR")"

echo -e "${BLUE}TaxBot Cron Setup${NC}"
echo "=================="

# Check if running as root
if [[ $EUID -eq 0 ]]; then
   echo -e "${RED}This script should not be run as root${NC}"
   exit 1
fi

# Check if Python is available
if ! command -v python3 &> /dev/null; then
    echo -e "${RED}Python 3 is not installed${NC}"
    exit 1
fi

# Check if virtual environment exists
if [ ! -d "$PROJECT_DIR/venv" ]; then
    echo -e "${YELLOW}Creating virtual environment...${NC}"
    cd "$PROJECT_DIR"
    python3 -m venv venv
    source venv/bin/activate
    pip install -r requirements.txt
else
    echo -e "${GREEN}Virtual environment found${NC}"
fi

# Check if .env file exists
if [ ! -f "$PROJECT_DIR/.env" ]; then
    echo -e "${YELLOW}Creating .env file from template...${NC}"
    cp "$PROJECT_DIR/.env.example" "$PROJECT_DIR/.env"
    echo -e "${YELLOW}Please edit .env file with your configuration${NC}"
fi

# Create cron job
CRON_JOB="0 6 * * * cd $PROJECT_DIR && source venv/bin/activate && python -m taxbot.cli.commands scrape >> logs/cron.log 2>&1"

# Check if cron job already exists
if crontab -l 2>/dev/null | grep -q "taxbot"; then
    echo -e "${YELLOW}Cron job already exists. Updating...${NC}"
    # Remove existing taxbot cron jobs
    crontab -l 2>/dev/null | grep -v "taxbot" | crontab -
fi

# Add new cron job
(crontab -l 2>/dev/null; echo "$CRON_JOB") | crontab -

echo -e "${GREEN}Cron job added successfully${NC}"
echo "Schedule: Daily at 6:00 AM"
echo "Command: $CRON_JOB"

# Create logs directory
mkdir -p "$PROJECT_DIR/logs"

# Test the setup
echo -e "${BLUE}Testing setup...${NC}"
cd "$PROJECT_DIR"
source venv/bin/activate

# Test configuration
echo "Testing configuration..."
python -c "
from taxbot.core.config import get_settings
from taxbot.core.logging import setup_logging
setup_logging()
settings = get_settings()
print(f'Data directory: {settings.data_dir}')
print(f'Ollama model: {settings.ollama_model}')
print(f'Email configured: {bool(settings.email_sender)}')
"

echo -e "${GREEN}Setup completed successfully!${NC}"
echo ""
echo "Next steps:"
echo "1. Edit .env file with your configuration"
echo "2. Test email configuration: python -m taxbot.cli.commands test-email"
echo "3. Test Ollama: python -m taxbot.cli.commands test-ollama"
echo "4. Run manual scraping: python -m taxbot.cli.commands scrape"
echo "5. Check cron logs: tail -f logs/cron.log"
echo ""
echo "To remove the cron job:"
echo "crontab -e"
echo "Then delete the line containing 'taxbot'"
