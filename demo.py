#!/usr/bin/env python3
"""
Demo script for ASCII Art Engine
Creates test images and shows all features
"""

import numpy as np
from PIL import Image, ImageDraw, ImageFont
import os

def create_test_image():
    """Create a simple test image with geometric shapes"""
    width, height = 400, 300
    img = Image.new('RGB', (width, height), 'white')
    draw = ImageDraw.Draw(img)
    
    # Draw some shapes
    draw.ellipse([50, 50, 150, 150], fill='black')
    draw.rectangle([200, 50, 350, 150], fill='gray')
    draw.polygon([(100, 200), (200, 180), (250, 250), (50, 250)], fill='black')
    
    # Try to add text
    try:
        font = ImageFont.load_default()
        draw.text((10, 10), "ASCII", fill='black', font=font)
    except:
        # Fallback if font loading fails
        draw.text((10, 10), "ASCII", fill='black')
    
    img.save('test_image.png')
    print("Created test_image.png")

def create_smiley():
    """Create a simple smiley face image"""
    size = 200
    img = Image.new('RGB', (size, size), 'white')
    draw = ImageDraw.Draw(img)
    
    # Face outline
    draw.ellipse([20, 20, size-20, size-20], outline='black', width=5)
    
    # Eyes
    draw.ellipse([60, 70, 80, 90], fill='black')
    draw.ellipse([120, 70, 140, 90], fill='black')
    
    # Smile
    draw.arc([60, 100, 140, 140], 0, 180, fill='black', width=5)
    
    img.save('smiley.png')
    print("Created smiley.png")

if __name__ == "__main__":
    print("Creating test images...")
    create_test_image()
    create_smiley()
    print("\nNow try these commands:")
    print("source ascii_env/bin/activate")
    print("python3 ascii_art_engine.py -i test_image.png")
    print("python3 ascii_art_engine.py -i smiley.png --style blocks")
    print("python3 ascii_art_engine.py -i smiley.png --hide 'Secret Message!' --style detailed")
    print("python3 ascii_art_engine.py --animate --fps 15")