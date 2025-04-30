#!/bin/bash

# Trading Bot Runner Script
# This script starts the WebSocket-based trading bot with proper environment setup

# Ensure we're in the right directory
cd "$(dirname "$0")"

# Create data directory if it doesn't exist
if [ ! -d "data" ]; then
    echo "Creating data directory..."
    mkdir -p data
    chmod 777 data
fi

# Check if .env file exists, if not copy from example
if [ ! -f ".env" ]; then
    echo "Creating .env file from .env.example..."
    cp .env.example .env
    echo "Please edit .env file with your configuration before running again."
    exit 1
fi

# Set up Python environment
if [ -d "venv" ]; then
    echo "Activating virtual environment..."
    source venv/bin/activate
else
    echo "Creating virtual environment..."
    python -m venv venv
    source venv/bin/activate
    pip install -r requirements.txt
fi

# Set up log directory
if [ ! -d "logs" ]; then
    mkdir -p logs
fi

# Start the bot with logging
echo "Starting trading bot with WebSocket API..."
python trading_bot_ws.py 2>&1 | tee -a logs/trading_bot_$(date +%Y%m%d_%H%M%S).log
