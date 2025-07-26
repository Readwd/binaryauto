#!/bin/bash

# QXBroker Auto Trading Bot Startup Script

echo "🤖 QXBroker Auto Trading Bot"
echo "============================="

# Check if .env file exists
if [ ! -f ".env" ]; then
    echo "❌ .env file not found!"
    echo "📋 Please copy .env.example to .env and configure your settings"
    echo "   cp .env.example .env"
    exit 1
fi

# Check if virtual environment exists
if [ ! -d "venv" ]; then
    echo "📦 Creating virtual environment..."
    python3 -m venv venv
fi

# Activate virtual environment
echo "🔄 Activating virtual environment..."
source venv/bin/activate

# Install/upgrade dependencies
echo "📦 Installing dependencies..."
pip install --upgrade pip
pip install -r requirements.txt

# Test installation
echo "🧪 Testing installation..."
python test_installation.py

if [ $? -eq 0 ]; then
    echo ""
    echo "🚀 Starting QXBroker Auto Trading Bot..."
    echo "   Press Ctrl+C to stop the bot"
    echo ""
    python main.py
else
    echo "❌ Installation test failed. Please fix the issues and try again."
    exit 1
fi