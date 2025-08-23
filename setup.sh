#!/bin/bash

echo "Setting up ASCII Art Engine..."

# Create virtual environment
python3 -m venv venv

# Activate virtual environment
source venv/bin/activate

# Install dependencies
pip install -r requirements.txt

echo "Setup complete! To use:"
echo "1. source venv/bin/activate"
echo "2. python tikket_ascii.py [image_path] [options]"
echo ""
echo "Example: python tikket_ascii.py my_image.jpg --color --width 120"