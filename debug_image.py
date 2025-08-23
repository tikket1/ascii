#!/usr/bin/env python3
"""Debug script to check image processing"""

from PIL import Image
import numpy as np

def debug_image(image_path):
    print(f"Debugging image: {image_path}")
    
    # Load and convert image
    img = Image.open(image_path)
    print(f"Original size: {img.size}")
    print(f"Original mode: {img.mode}")
    
    # Convert to grayscale
    img_gray = img.convert('L')
    
    # Resize to small size for debugging
    img_small = img_gray.resize((20, 15))
    
    # Convert to numpy array
    pixels = np.array(img_small)
    
    print(f"Pixel value range: {pixels.min()} to {pixels.max()}")
    print(f"Average pixel value: {pixels.mean():.2f}")
    print(f"Standard deviation: {pixels.std():.2f}")
    
    print("\nSample pixel values (first 5x5):")
    print(pixels[:5, :5])
    
    # Show histogram of values
    unique, counts = np.unique(pixels, return_counts=True)
    print(f"\nPixel value distribution (first 10):")
    for val, count in zip(unique[:10], counts[:10]):
        print(f"  {val}: {count} pixels")

if __name__ == "__main__":
    debug_image("Terry_A._Davis_in_front_of_Richland_WA_library_(cropped).jpg")
    print("\n" + "="*50 + "\n")
    debug_image("smiley.png")