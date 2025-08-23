#!/usr/bin/env python3
"""
ASCII Art Engine - Image to ASCII converter with animation and secret cipher
A fun project combining image processing, ASCII art, and cryptography!
"""

import os
import sys
import time
import argparse
from PIL import Image, ImageEnhance, ImageFilter
import numpy as np
from scipy import ndimage
try:
    from skimage import exposure, filters
    SCIKIT_AVAILABLE = True
except ImportError:
    SCIKIT_AVAILABLE = False
from typing import List, Tuple, Optional
import colorsys


class ASCIIConverter:
    """Converts images to ASCII art with different character sets and styles"""
    
    # Different character sets for various ASCII art styles
    CHAR_SETS = {
        'detailed': '@%#*+=-:. ',
        'simple': '█▉▊▋▌▍▎▏ ',
        'classic': '$@B%8&WM#*oahkbdpqwmZO0QLCJUYXzcvunxrjft/\\|()1{}[]?-_+~<>i!lI;:,\"^`\'. ',
        'blocks': '██▓▒░  ',
        'minimal': '■□ ',
        'hifi': '@@@@@@@@@###########*********+++++++++=========-----:::::.......         ',
        'photorealistic': '█▉▊▋▌▍▎▏▎▍▌▋▊▉█▉▊▋▌▍▎▏ ░░▒▒▓▓██',
        'dense': '██████▓▓▓▓▓▒▒▒▒▒░░░░░      ',
        'ultra': '@@@###***+++===---:::...   '
    }
    
    def __init__(self, char_set: str = 'detailed', width: int = 80):
        self.chars = self.CHAR_SETS.get(char_set, self.CHAR_SETS['detailed'])
        self.width = width
        
    def _enhance_shadows(self, img_array: np.ndarray) -> np.ndarray:
        """Enhance detail in shadow regions while preserving overall contrast"""
        # Shadow lifting: brighten dark areas more than light areas
        shadow_threshold = 0.3  # Areas below 30% brightness are considered shadows
        shadow_lift = 0.2       # How much to lift shadows (0-1) - reduced for subtlety
        
        # Create a mask for shadow areas
        normalized = img_array / 255.0
        shadow_mask = normalized < shadow_threshold
        
        # Apply progressive shadow lifting
        lift_amount = np.where(shadow_mask, 
                              shadow_lift * (shadow_threshold - normalized) / shadow_threshold,
                              0)
        
        # Apply the lifting
        enhanced = normalized + lift_amount
        
        # Ensure we stay in valid range
        enhanced = np.clip(enhanced, 0, 1)
        
        return (enhanced * 255).astype(np.uint8)
    
    def _adaptive_histogram_eq(self, img_array: np.ndarray, clip_limit: float = 0.02) -> np.ndarray:
        """Apply adaptive histogram equalization to enhance local contrast"""
        if SCIKIT_AVAILABLE:
            # Use scikit-image's adaptive histogram equalization with much gentler settings
            normalized = img_array / 255.0
            enhanced = exposure.equalize_adapthist(normalized, clip_limit=clip_limit, kernel_size=None)
            return (enhanced * 255).astype(np.uint8)
        else:
            # Fallback: simple local contrast enhancement
            return self._local_contrast_enhancement(img_array)
    
    def _local_contrast_enhancement(self, img_array: np.ndarray) -> np.ndarray:
        """Fallback local contrast enhancement without scikit-image"""
        # Apply a local standard deviation filter to enhance edges
        local_std = ndimage.generic_filter(img_array.astype(np.float64), np.std, size=5)
        
        # Enhance areas with low local contrast (shadows/flat areas)
        enhancement_factor = 1.0 + (0.3 * (1.0 - local_std / local_std.max()))
        
        enhanced = img_array.astype(np.float64) * enhancement_factor
        return np.clip(enhanced, 0, 255).astype(np.uint8)
    
    def _preserve_detail_in_darks(self, img_array: np.ndarray) -> np.ndarray:
        """Add texture and detail to very dark areas"""
        # Find very dark regions (below 15% brightness)
        very_dark_mask = img_array < 38  # 15% of 255
        
        if not np.any(very_dark_mask):
            return img_array
        
        # Add slight noise/texture to very dark areas to prevent solid blocks
        # This helps preserve facial features in shadows
        texture_strength = 15  # Small amount of texture
        
        enhanced = img_array.copy().astype(np.float64)
        
        # Add structured noise to dark areas
        if np.any(very_dark_mask):
            # Create subtle texture pattern
            h, w = img_array.shape
            texture = np.random.normal(0, texture_strength/3, (h, w))
            
            # Apply gaussian smoothing to make texture more natural
            texture = ndimage.gaussian_filter(texture, sigma=0.8)
            
            # Only apply to very dark areas
            enhanced[very_dark_mask] += texture[very_dark_mask]
        
        return np.clip(enhanced, 0, 255).astype(np.uint8)
    
    def _gentle_shadow_lift(self, img_array: np.ndarray) -> np.ndarray:
        """Very gentle shadow lifting that preserves overall contrast"""
        # Create a gentle curve that lifts shadows just slightly
        # This prevents the "glasses" effect around eyes
        normalized = img_array / 255.0
        
        # Very gentle lift only for very dark areas (below 20%)
        dark_threshold = 0.2
        lift_strength = 0.15  # Very subtle lift
        
        # Apply curve that gently lifts only the darkest areas
        shadow_curve = np.where(normalized < dark_threshold,
                               normalized + lift_strength * (dark_threshold - normalized) / dark_threshold,
                               normalized)
        
        # Ensure we don't exceed valid range
        shadow_curve = np.clip(shadow_curve, 0, 1)
        
        return (shadow_curve * 255).astype(np.float64)
    
    def _get_ansi_color(self, r: int, g: int, b: int, background: bool = False) -> str:
        """Convert RGB to ANSI color code"""
        # Use 256-color mode for better color representation
        color_code = 16 + (36 * (r // 51)) + (6 * (g // 51)) + (b // 51)
        prefix = "48" if background else "38"
        return f"\033[{prefix};5;{color_code}m"
    
    def _reset_color(self) -> str:
        """Reset ANSI color to default"""
        return "\033[0m"
    
    def _color_distance(self, c1: Tuple[int, int, int], c2: Tuple[int, int, int]) -> float:
        """Calculate color distance for palette mapping"""
        return sum((a - b) ** 2 for a, b in zip(c1, c2)) ** 0.5
    
    def _get_color_palette(self, style: str) -> List[Tuple[int, int, int]]:
        """Get color palette for different styles"""
        palettes = {
            'natural': [
                (25, 25, 25),      # Dark/shadows
                (100, 50, 30),     # Brown/earth
                (150, 120, 80),    # Skin/tan
                (200, 180, 150),   # Light skin/highlights
                (50, 100, 150),    # Blue/sky
                (100, 150, 100),   # Green/nature
                (200, 200, 200),   # Light/white
                (255, 220, 180)    # Bright highlights
            ],
            'vivid': [
                (0, 0, 0),         # Black
                (255, 0, 0),       # Red
                (0, 255, 0),       # Green
                (0, 0, 255),       # Blue
                (255, 255, 0),     # Yellow
                (255, 0, 255),     # Magenta
                (0, 255, 255),     # Cyan
                (255, 255, 255)    # White
            ],
            'ocean': [
                (0, 20, 40),       # Deep blue
                (20, 50, 80),      # Dark blue
                (40, 80, 120),     # Medium blue
                (60, 120, 160),    # Light blue
                (100, 150, 180),   # Sky blue
                (150, 200, 220),   # Pale blue
                (200, 230, 250),   # Very light blue
                (255, 255, 255)    # White foam
            ],
            'sunset': [
                (20, 0, 40),       # Dark purple
                (60, 20, 80),      # Purple
                (120, 40, 60),     # Dark red
                (180, 80, 40),     # Red
                (220, 120, 60),    # Orange
                (250, 180, 100),   # Light orange
                (255, 220, 150),   # Yellow
                (255, 255, 200)    # Light yellow
            ]
        }
        return palettes.get(style, palettes['natural'])
        
    def image_to_ascii(self, image_path: str, invert: bool = False, hifi: bool = False, color: bool = False, color_style: str = 'natural') -> List[str]:
        """Convert image to ASCII art with optional high-fidelity processing"""
        try:
            # Open and process image
            img = Image.open(image_path)
            
            # Store original color information if color mode is enabled
            if color:
                color_img = img.convert('RGB')
            
            img = img.convert('L')  # Convert to grayscale for ASCII processing
            
            if hifi:
                # High-fidelity processing
                # 1. Apply slight sharpening to enhance edges
                img = img.filter(ImageFilter.UnsharpMask(radius=1, percent=120, threshold=2))
                
                # 2. Gamma correction to improve midtone detail
                gamma = 0.8
                img = Image.eval(img, lambda x: int(((x / 255.0) ** gamma) * 255))
                
                # 3. Enhanced contrast
                enhancer = ImageEnhance.Contrast(img)
                img = enhancer.enhance(1.8)  # Higher contrast for hifi
                
                # 4. Slight brightness adjustment
                enhancer = ImageEnhance.Brightness(img)
                img = enhancer.enhance(1.1)
            else:
                # Standard processing
                enhancer = ImageEnhance.Contrast(img)
                img = enhancer.enhance(1.5)
            
            # Calculate new height maintaining aspect ratio
            aspect_ratio = img.height / img.width
            new_height = int(self.width * aspect_ratio * 0.55)  # 0.55 to account for character height
            
            # For hifi mode, use higher quality resampling
            resample_method = Image.Resampling.LANCZOS if hifi else Image.Resampling.BILINEAR
            img = img.resize((self.width, new_height), resample_method)
            
            # Resize color image if color mode is enabled
            if color:
                color_img = color_img.resize((self.width, new_height), resample_method)
                color_pixels = np.array(color_img)
            
            # Convert to numpy array for processing
            pixels = np.array(img, dtype=np.float64)
            
            # Advanced histogram processing for better detail
            if hifi:
                # Apply gentler shadow lifting to preserve detail in dark areas
                # This helps with Terry's eye area specifically
                shadow_enhanced = self._gentle_shadow_lift(pixels)
                
                # Standard contrast normalization to use full character range
                pixels_min = shadow_enhanced.min()
                pixels_max = shadow_enhanced.max()
                if pixels_max > pixels_min:
                    pixels = (shadow_enhanced - pixels_min) * 255 / (pixels_max - pixels_min)
                else:
                    pixels = shadow_enhanced
                    
                pixels = np.clip(pixels, 0, 255)
            else:
                # Standard normalization
                pixels_min = pixels.min()
                pixels_max = pixels.max()
                
                if pixels_max > pixels_min:
                    # Stretch to full 0-255 range
                    pixels = (pixels - pixels_min) * 255 / (pixels_max - pixels_min)
            
            # Map to character indices using the full 0-255 range
            char_indices = (pixels * (len(self.chars) - 1) / 255).astype(int)
            
            # Ensure indices are within bounds
            char_indices = np.clip(char_indices, 0, len(self.chars) - 1)
            
            # Generate ASCII art with fixed-width grid
            ascii_lines = []
            
            for row_idx, row in enumerate(char_indices):
                line = ""
                for col_idx, char_idx in enumerate(row):
                    # Get the character
                    if invert:
                        char = self.chars[len(self.chars) - 1 - char_idx]
                    else:
                        char = self.chars[char_idx]
                    
                    # Ensure single character width (some unicode chars can be wide)
                    if len(char) > 1:
                        char = char[0]
                    
                    # For better external app compatibility, use consistent spacing
                    if char == ' ':
                        char = '░'  # Use light shade for empty areas - more visible in Discord
                    
                    # Add color if enabled
                    if color:
                        # Get the actual color from the original image
                        r, g, b = color_pixels[row_idx, col_idx]
                        
                        # Use the actual RGB values directly
                        color_code = self._get_ansi_color(r, g, b)
                        line += color_code + char
                    else:
                        line += char
                
                # Reset color at end of line if using color
                if color:
                    line += self._reset_color()
                
                # Strip trailing whitespace and ensure consistent line endings
                line = line.rstrip()
                ascii_lines.append(line)
                
            return ascii_lines
            
        except Exception as e:
            return [f"Error processing image: {e}"]


class ASCIIAnimator:
    """Creates animated ASCII sequences"""
    
    def __init__(self, converter: ASCIIConverter):
        self.converter = converter
        self.frames = []
        
    def add_frame_from_image(self, image_path: str, invert: bool = False):
        """Add a frame from an image"""
        ascii_art = self.converter.image_to_ascii(image_path, invert)
        self.frames.append(ascii_art)
        
    def add_frame_from_text(self, text_lines: List[str]):
        """Add a frame from text lines"""
        self.frames.append(text_lines)
        
    def create_text_animation(self, text: str, width: int = 80) -> List[List[str]]:
        """Create a simple text scrolling animation"""
        frames = []
        padding = ' ' * width
        full_text = padding + text + padding
        
        for i in range(len(full_text) - width + 1):
            frame = [full_text[i:i + width]]
            frames.append(frame)
            
        return frames
        
    def play_animation(self, fps: float = 10, loops: int = 1):
        """Play the animation in terminal"""
        if not self.frames:
            print("No frames to animate!")
            return
            
        delay = 1.0 / fps
        
        try:
            for loop in range(loops):
                for frame in self.frames:
                    # Clear screen
                    os.system('clear' if os.name == 'posix' else 'cls')
                    
                    # Print frame
                    for line in frame:
                        print(line)
                        
                    time.sleep(delay)
                    
        except KeyboardInterrupt:
            print("\nAnimation stopped!")


class SecretCipher:
    """Hide and reveal secret messages in ASCII art"""
    
    @staticmethod
    def hide_message(ascii_lines: List[str], message: str, key: int = 5) -> List[str]:
        """Hide a message in ASCII art using character substitution"""
        if not message:
            return ascii_lines
            
        # Simple Caesar cipher on the message
        encoded_msg = SecretCipher._caesar_encode(message, key)
        
        # Add a special marker to indicate end of message
        encoded_msg += '\x00'  # Null terminator
        
        # Hide the encoded message by slightly modifying ASCII characters
        hidden_lines = []
        msg_index = 0
        
        for line in ascii_lines:
            new_line = ""
            for char in line:
                if msg_index < len(encoded_msg) and char != ' ':
                    # Encode message character into ASCII char choice
                    hidden_char = SecretCipher._blend_chars(char, encoded_msg[msg_index])
                    new_line += hidden_char
                    msg_index += 1
                else:
                    new_line += char
            hidden_lines.append(new_line)
            
        return hidden_lines
    
    @staticmethod
    def reveal_message(ascii_lines: List[str], key: int = 5) -> str:
        """Extract hidden message from ASCII art"""
        hidden_chars = []
        
        for line in ascii_lines:
            for char in line:
                if char != ' ':
                    # Extract hidden character
                    hidden_char = SecretCipher._extract_char(char)
                    if hidden_char:
                        hidden_chars.append(hidden_char)
                        # Stop at null terminator
                        if hidden_char == '\x00':
                            break
            if hidden_chars and hidden_chars[-1] == '\x00':
                break
                        
        # Remove null terminator and decode the message
        if hidden_chars and hidden_chars[-1] == '\x00':
            hidden_chars = hidden_chars[:-1]
            
        encoded_msg = ''.join(hidden_chars)
        return SecretCipher._caesar_decode(encoded_msg, key)
    
    @staticmethod
    def _caesar_encode(text: str, shift: int) -> str:
        """Simple Caesar cipher encoding"""
        result = ""
        for char in text:
            if char.isalpha():
                ascii_offset = 65 if char.isupper() else 97
                result += chr((ord(char) - ascii_offset + shift) % 26 + ascii_offset)
            else:
                result += char
        return result
    
    @staticmethod
    def _caesar_decode(text: str, shift: int) -> str:
        """Simple Caesar cipher decoding"""
        return SecretCipher._caesar_encode(text, -shift)
    
    @staticmethod
    def _blend_chars(ascii_char: str, message_char: str) -> str:
        """Blend message character into ASCII character using character mapping"""
        # Handle null terminator specially
        if message_char == '\x00':
            char_code = 0
        else:
            # Use character value to determine position (A=1, B=2, ..., Z=26)
            if message_char.isalpha():
                char_code = (ord(message_char.upper()) - ord('A') + 1) % 10
            else:
                char_code = ord(message_char) % 10
        
        # Map to similar-looking characters based on original ASCII char
        char_map = {
            '@': ['@', '&', '%', '#', '*', '+', '=', '-', ':', '.'],
            '%': ['%', '#', '*', '+', '=', '-', ':', '.', ' ', '@'],
            '#': ['#', '*', '+', '=', '-', ':', '.', ' ', '@', '%'],
            '*': ['*', '+', '=', '-', ':', '.', ' ', '@', '%', '#'],
            '+': ['+', '=', '-', ':', '.', ' ', '@', '%', '#', '*'],
            '=': ['=', '-', ':', '.', ' ', '@', '%', '#', '*', '+'],
            '-': ['-', ':', '.', ' ', '@', '%', '#', '*', '+', '='],
            ':': [':', '.', ' ', '@', '%', '#', '*', '+', '=', '-'],
            '.': ['.', ' ', '@', '%', '#', '*', '+', '=', '-', ':'],
            ' ': [' ', '@', '%', '#', '*', '+', '=', '-', ':', '.']
        }
        
        if ascii_char in char_map:
            return char_map[ascii_char][char_code]
        
        return ascii_char
    
    @staticmethod
    def _extract_char(ascii_char: str) -> Optional[str]:
        """Extract hidden character from ASCII character"""
        # Reverse mapping to extract the hidden character
        char_map = {
            '@': ['@', '&', '%', '#', '*', '+', '=', '-', ':', '.'],
            '%': ['%', '#', '*', '+', '=', '-', ':', '.', ' ', '@'],
            '#': ['#', '*', '+', '=', '-', ':', '.', ' ', '@', '%'],
            '*': ['*', '+', '=', '-', ':', '.', ' ', '@', '%', '#'],
            '+': ['+', '=', '-', ':', '.', ' ', '@', '%', '#', '*'],
            '=': ['=', '-', ':', '.', ' ', '@', '%', '#', '*', '+'],
            '-': ['-', ':', '.', ' ', '@', '%', '#', '*', '+', '='],
            ':': [':', '.', ' ', '@', '%', '#', '*', '+', '=', '-'],
            '.': ['.', ' ', '@', '%', '#', '*', '+', '=', '-', ':'],
            ' ': [' ', '@', '%', '#', '*', '+', '=', '-', ':', '.']
        }
        
        # Find which character this could represent
        for original_char, variants in char_map.items():
            if ascii_char in variants:
                position = variants.index(ascii_char)
                # Convert position back to character
                if position == 0:
                    return '\x00'  # Null terminator at position 0
                else:
                    # Map position back to alphabet (1=A, 2=B, etc.)
                    if position <= 26:
                        return chr((position - 1) % 26 + ord('A'))
                    else:
                        return chr(position + ord('A') - 1)  # For positions beyond 26
        
        return None


def main():
    """Main CLI interface"""
    parser = argparse.ArgumentParser(description="ASCII Art Engine with Animation & Cipher")
    parser.add_argument('--image', '-i', help='Input image path')
    parser.add_argument('--width', '-w', type=int, default=80, help='ASCII art width')
    parser.add_argument('--style', '-s', choices=ASCIIConverter.CHAR_SETS.keys(), 
                       default='detailed', help='ASCII character set style')
    parser.add_argument('--invert', action='store_true', help='Invert brightness')
    parser.add_argument('--hifi', action='store_true', help='High-fidelity mode with enhanced processing')
    parser.add_argument('--color', '-c', action='store_true', help='Enable color ASCII art')
    parser.add_argument('--color-style', choices=['natural', 'vivid', 'ocean', 'sunset'], 
                       default='natural', help='Color palette style')
    parser.add_argument('--animate', '-a', action='store_true', help='Create animation')
    parser.add_argument('--hide', help='Hide this message in the ASCII art')
    parser.add_argument('--reveal', action='store_true', help='Reveal hidden message')
    parser.add_argument('--fps', type=float, default=10, help='Animation FPS')
    parser.add_argument('--loops', type=int, default=1, help='Animation loops')
    
    args = parser.parse_args()
    
    # Create converter
    converter = ASCIIConverter(args.style, args.width)
    
    if args.image:
        # Convert image to ASCII
        ascii_art = converter.image_to_ascii(args.image, args.invert, args.hifi, args.color, getattr(args, 'color_style'))
        
        # Hide message if requested
        if args.hide:
            ascii_art = SecretCipher.hide_message(ascii_art, args.hide)
            print("Message hidden in ASCII art!")
            
        # Reveal message if requested
        if args.reveal:
            hidden_msg = SecretCipher.reveal_message(ascii_art)
            if hidden_msg:
                print(f"Hidden message: {hidden_msg}")
            else:
                print("No hidden message found.")
                
        # Display ASCII art
        for line in ascii_art:
            print(line)
            
    elif args.animate:
        # Create a simple text animation demo
        animator = ASCIIAnimator(converter)
        
        # Create scrolling text animation
        demo_text = "ASCII ART ENGINE - Image to ASCII with Animation & Secret Cipher!"
        text_frames = animator.create_text_animation(demo_text, args.width)
        
        for frame in text_frames:
            animator.add_frame_from_text(frame)
            
        print("Starting animation... Press Ctrl+C to stop")
        animator.play_animation(args.fps, args.loops)
        
    else:
        print("Please provide an image (-i) or use --animate for demo animation")
        print("Use --help for more options")


if __name__ == "__main__":
    main()