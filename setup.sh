#!/bin/bash

# Setup script for Binance WebSocket Trading Bot
# This script initializes the environment and installs all dependencies

set -e  # Exit on error

echo "Setting up Binance WebSocket Trading Bot environment..."

# Create virtual environment
if [ ! -d "venv" ]; then
    echo "Creating Python virtual environment..."
    python3 -m venv venv
fi

# Activate virtual environment
source venv/bin/activate

# Install dependencies
echo "Installing dependencies..."
pip install --upgrade pip
pip install -r requirements.txt

# Create data directory
if [ ! -d "data" ]; then
    echo "Creating data directory..."
    mkdir -p data
    chmod 777 data
fi

# Create logs directory
if [ ! -d "logs" ]; then
    echo "Creating logs directory..."
    mkdir -p logs
fi

# Create .env file if not exists
if [ ! -f ".env" ]; then
    echo "Creating .env file from template..."
    cp .env.example .env
    echo "Please edit .env file with your configuration before running the bot."
fi

# Make scripts executable
chmod +x run.sh
chmod +x deploy_to_ec2.sh

echo "Setup complete! Follow these steps to proceed:"
echo "1. Edit the .env file with your Binance API credentials and configuration"
echo "2. Run the bot using ./run.sh"
echo "3. To deploy to EC2, use ./deploy_to_ec2.sh user@your-ec2-instance"
echo ""
echo "For more details, please refer to the README.md file." 