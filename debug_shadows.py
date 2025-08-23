#!/usr/bin/env python3
"""Debug shadow enhancement functions"""

from PIL import Image, ImageEnhance, ImageFilter
import numpy as np
from ascii_art_engine import ASCIIConverter

def debug_shadow_processing(image_path):
    print(f"Debugging shadow processing for: {image_path}")
    
    # Open and process image like the main function
    img = Image.open(image_path)
    img = img.convert('L')
    
    # Apply HiFi preprocessing  
    img = img.filter(ImageFilter.UnsharpMask(radius=1, percent=120, threshold=2))
    gamma = 0.8
    img = Image.eval(img, lambda x: int(((x / 255.0) ** gamma) * 255))
    enhancer = ImageEnhance.Contrast(img)
    img = enhancer.enhance(1.8)
    enhancer = ImageEnhance.Brightness(img)
    img = enhancer.enhance(1.1)
    
    # Resize
    img = img.resize((50, 30), Image.Resampling.LANCZOS)
    
    # Convert to numpy
    pixels = np.array(img, dtype=np.float64)
    print(f"Initial pixel range: {pixels.min()} to {pixels.max()}")
    
    # Create converter to test methods
    converter = ASCIIConverter()
    
    # Test shadow enhancement
    try:
        enhanced = converter._enhance_shadows(pixels)
        print(f"After shadow enhancement: {enhanced.min()} to {enhanced.max()}")
        
        # Test adaptive histogram
        adaptive = converter._adaptive_histogram_eq(enhanced)
        print(f"After adaptive histogram: {adaptive.min()} to {adaptive.max()}")
        
        # Test dark detail preservation
        detailed = converter._preserve_detail_in_darks(adaptive)
        print(f"After detail preservation: {detailed.min()} to {detailed.max()}")
        
        # Ensure in range (like the fixed version)
        final = np.clip(detailed, 0, 255)
        print(f"After clipping to 0-255: {final.min()} to {final.max()}")
        
        # Test character mapping
        chars = '@%#*+=-:. '
        char_indices = (final * (len(chars) - 1) / 255).astype(int)
        char_indices = np.clip(char_indices, 0, len(chars) - 1)
        
        print(f"Character indices range: {char_indices.min()} to {char_indices.max()}")
        print(f"Unique character indices: {sorted(np.unique(char_indices))}")
        
        # Show a sample
        print("\nFirst 3 lines:")
        for i in range(3):
            line = ''.join(chars[j] for j in char_indices[i])
            print(repr(line))
                
    except Exception as e:
        print(f"Error during processing: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    debug_shadow_processing("Terry_A._Davis_in_front_of_Richland_WA_library_(cropped).jpg")