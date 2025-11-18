#!/bin/bash

# Setup script for Playwright integration in ThetaRay Solution Quality

echo "Setting up Playwright performance testing environment..."

# Create virtual environment if it doesn't exist
if [ ! -d "venv" ]; then
    echo "Creating virtual environment..."
    python3 -m venv venv
fi

# Activate virtual environment
echo "Activating virtual environment..."
source venv/bin/activate

# Install requirements
echo "Installing Python requirements..."
pip install -r requirements.txt

# Install Playwright browsers
echo "Installing Playwright browsers..."
python -m playwright install

# Install system dependencies for Playwright
echo "Installing system dependencies..."
python -m playwright install-deps

# Create reports directory
mkdir -p reports

# Set executable permissions
chmod +x setup.sh

echo "Setup complete!"
echo ""
echo "To run the solution quality system:"
echo "  1. Activate virtual environment: source venv/bin/activate"
echo "  2. Run the main script: python main.py"
echo ""
echo "Available validation modes:"
echo "  - SDLC Validation: Validates code structure, features, DAGs"
echo "  - Performance Testing: Tests UI performance with Playwright"
echo "  - Combined: Runs both SDLC and performance validation"


