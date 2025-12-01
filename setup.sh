#!/bin/bash
# setup.sh - Quick setup script for SecurePath Backend

set -e  # Exit on error

echo "🚀 SecurePath Backend Setup"
echo "=========================="
echo ""

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

# Check Python version
if ! command -v python3 &> /dev/null; then
    echo -e "${RED}Error: Python 3 is not installed${NC}"
    exit 1
fi

PYTHON_VERSION=$(python3 --version | cut -d' ' -f2 | cut -d'.' -f1,2)
echo -e "${GREEN}✓${NC} Python $PYTHON_VERSION found"

# Create virtual environment
if [ ! -d "venv" ]; then
    echo "Creating virtual environment..."
    python3 -m venv venv
    echo -e "${GREEN}✓${NC} Virtual environment created"
else
    echo -e "${YELLOW}!${NC} Virtual environment already exists"
fi

# Activate virtual environment
source venv/bin/activate

# Install dependencies
echo "Installing Python dependencies..."
pip install --upgrade pip
pip install -r requirements.txt
echo -e "${GREEN}✓${NC} Python dependencies installed"

# Setup environment file
if [ ! -f ".env" ]; then
    echo "Creating .env file..."
    cp .env.example .env
    echo -e "${YELLOW}!${NC} Please edit .env with your configuration"
else
    echo -e "${YELLOW}!${NC} .env file already exists"
fi

# Create logs directory
mkdir -p logs
echo -e "${GREEN}✓${NC} Logs directory created"

# Run migrations
echo "Running database migrations..."
python manage.py makemigrations
python manage.py migrate
echo -e "${GREEN}✓${NC} Database migrations completed"

echo ""
echo "=========================="
echo -e "${GREEN}✅ Backend Setup Complete!${NC}"
echo "=========================="
echo ""
echo "Next steps:"
echo "1. Edit .env with your configuration"
echo "2. Start the server: python manage.py runserver"
echo "3. (Optional) Start Celery: celery -A backend worker -l info"
echo ""
