#!/usr/bin/env python3
"""Debug the fixed ASCII converter"""

from PIL import Image, ImageEnhance
import numpy as np

def debug_fixed_conversion(image_path):
    print(f"Debugging fixed conversion for: {image_path}")
    
    # Open and process image
    img = Image.open(image_path)
    img = img.convert('L')  # Convert to grayscale
    
    print(f"Original image range: {np.array(img).min()} to {np.array(img).max()}")
    
    # Enhance contrast
    enhancer = ImageEnhance.Contrast(img)
    img = enhancer.enhance(1.5)
    
    print(f"After contrast enhancement: {np.array(img).min()} to {np.array(img).max()}")
    
    # Resize to small size for debugging
    img = img.resize((20, 15))
    
    # Convert to numpy array
    pixels = np.array(img, dtype=np.float64)
    
    print(f"Resized image range: {pixels.min()} to {pixels.max()}")
    
    # Apply the normalization
    pixels_min = pixels.min()
    pixels_max = pixels.max()
    if pixels_max > pixels_min:
        pixels_normalized = (pixels - pixels_min) * 255 / (pixels_max - pixels_min)
        print(f"After normalization: {pixels_normalized.min()} to {pixels_normalized.max()}")
    else:
        pixels_normalized = pixels
        print("No normalization applied (min == max)")
    
    # Test character mapping
    chars = '@%#*+=-:. '
    char_indices = (pixels_normalized * (len(chars) - 1) / 255).astype(int)
    char_indices = np.clip(char_indices, 0, len(chars) - 1)
    
    print(f"Character indices range: {char_indices.min()} to {char_indices.max()}")
    print(f"Unique character indices: {np.unique(char_indices)}")
    
    print("\nFirst few rows of character indices:")
    print(char_indices[:3])
    
    print("\nActual ASCII output (first 3 lines):")
    for i in range(3):
        line = ''.join(chars[j] for j in char_indices[i])
        print(repr(line))

if __name__ == "__main__":
    debug_fixed_conversion("Terry_A._Davis_in_front_of_Richland_WA_library_(cropped).jpg")