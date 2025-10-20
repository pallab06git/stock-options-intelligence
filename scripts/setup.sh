#!/bin/bash

# © 2025 Pallab Basu Roy. All rights reserved.
# This source code is proprietary and confidential.
# Unauthorized copying, modification, or commercial use is strictly prohibited.
# Repository: https://github.com/pallab06/stock-options-intelligence

# Setup script for Stock Options Intelligence

set -e

echo "Setting up Stock Options Intelligence..."

# Check Python version
python_version=$(python3 --version | cut -d' ' -f2 | cut -d'.' -f1,2)
required_version="3.11"

if [ "$(printf '%s\n' "$required_version" "$python_version" | sort -V | head -n1)" != "$required_version" ]; then
    echo "Error: Python $required_version or higher is required. Found: $python_version"
    exit 1
fi

# Create virtual environment
if [ ! -d "venv" ]; then
    echo "Creating virtual environment..."
    python3 -m venv venv
fi

# Activate virtual environment
echo "Activating virtual environment..."
source venv/bin/activate

# Upgrade pip
echo "Upgrading pip..."
pip install --upgrade pip

# Install dependencies
echo "Installing dependencies..."
pip install -r requirements.txt

# Create .env file if it doesn't exist
if [ ! -f ".env" ]; then
    echo "Creating .env file from template..."
    cp .env.example .env
    echo "Please edit .env file with your API keys"
fi

# Create necessary directories
echo "Creating directories..."
mkdir -p logs models data/raw data/processed data/historical

# Install pre-commit hooks
echo "Installing pre-commit hooks..."
pre-commit install

# Create placeholder files
touch models/.gitkeep
touch data/raw/.gitkeep
touch data/processed/.gitkeep
touch data/historical/.gitkeep

echo ""
echo "Setup complete! 🎉"
echo ""
echo "Next steps:"
echo "1. Edit .env file with your API keys"
echo "2. Start services: docker-compose up -d postgres redis"
echo "3. Run the application: python -m src.api.main"
echo ""
