#!/bin/bash

# © 2025 Pallab Basu Roy. All rights reserved.
# This source code is proprietary and confidential.
# Unauthorized copying, modification, or commercial use is strictly prohibited.
# Repository: https://github.com/pallab06/stock-options-intelligence

# Run Polygon.io Listener Service

set -e

echo "Starting Polygon.io SPY Listener..."

# Check if virtual environment exists, create if not
if [ ! -d "venv" ]; then
    echo "Virtual environment not found. Creating..."
    python3 -m venv venv
    source venv/bin/activate
    echo "Installing dependencies..."
    pip install -r requirements.txt
else
    source venv/bin/activate
fi

# Check if .env exists
if [ ! -f ".env" ]; then
    echo "Error: .env file not found. Copy .env.example to .env and add your API keys."
    exit 1
fi

# Create necessary directories
mkdir -p logs state data

# Run the listener
python -m src.data_ingestion.polygon_listener

# Deactivate virtual environment on exit
deactivate
