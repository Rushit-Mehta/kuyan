#!/bin/bash

# KUYAN - Setup and Run Script
# This script creates a virtual environment, installs dependencies, and runs the app

set -e  # Exit on error

echo "======================================"
echo "KUYAN - Setup and Run"
echo "======================================"
echo ""

# Check if Python 3 is installed
if ! command -v python3 &> /dev/null; then
    echo "❌ Error: Python 3 is not installed"
    echo "Please install Python 3.11 or higher from https://www.python.org/downloads/"
    exit 1
fi

# Check Python version
PYTHON_VERSION=$(python3 --version | cut -d' ' -f2 | cut -d'.' -f1-2)
REQUIRED_VERSION="3.11"

if [ "$(printf '%s\n' "$REQUIRED_VERSION" "$PYTHON_VERSION" | sort -V | head -n1)" != "$REQUIRED_VERSION" ]; then
    echo "⚠️  Warning: Python $REQUIRED_VERSION or higher is recommended"
    echo "Current version: $PYTHON_VERSION"
    echo ""
fi

# Check if virtual environment exists
if [ -d "venv" ]; then
    echo "✅ Virtual environment already exists"
else
    echo "📦 Creating virtual environment..."
    python3 -m venv venv
    echo "✅ Virtual environment created"
fi

echo ""

# Activate virtual environment
echo "🔧 Activating virtual environment..."
source venv/bin/activate

echo "✅ Virtual environment activated"
echo ""

# Check if dependencies are installed
if [ -f "venv/lib/python*/site-packages/streamlit/__init__.py" ] || [ -f "venv/Lib/site-packages/streamlit/__init__.py" ]; then
    echo "✅ Dependencies already installed"
else
    echo "📥 Installing dependencies..."
    pip install --upgrade pip
    pip install -r requirements.txt
    echo "✅ Dependencies installed"
fi

echo ""
echo "======================================"
echo "🚀 Starting KUYAN..."
echo "======================================"
echo ""
echo "Production Mode: http://localhost:8502"
echo "Sandbox Mode:    http://localhost:8502/?mode=sandbox"
echo ""
echo "Press Ctrl+C to stop the server"
echo ""

# Run Streamlit on port 8502 (for local development)
streamlit run app.py --server.port 8502
