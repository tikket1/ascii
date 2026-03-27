"""
ASCII Art Engine — Image to ASCII converter with photo and logo modes.

Refactored from tikket_ascii.py with fixes for:
- Configurable space fill (░ vs real spaces)
- Alpha channel awareness
- Whitespace trimming for logos
- Auto-invert for light-background logos
- Bundled processing presets per mode
"""

import numpy as np
from PIL import Image, ImageEnhance, ImageFilter
from typing import Tuple, Optional


CHAR_SETS = {
    "detailed": "@%#*+=-:. ",
    "simple": "█▉▊▋▌▍▎▏ ",
    "classic": "$@B%8&WM#*oahkbdpqwmZO0QLCJUYXzcvunxrjft/\\|()1{}[]?-_+~<>i!lI;:,\"^'. ",
    "blocks": "██▓▒░  ",
    "minimal": "■□ ",
    "hifi": "@@@@@@@@@###########*********+++++++++=========-----:::::.......         ",
    "dense": "██████▓▓▓▓▓▒▒▒▒▒░░░░░      ",
    "ultra": "@@@###***+++===---:::...   ",
}

CHARSET_INFO = {
    "detailed": {"description": "10-level ASCII gradient, good all-rounder", "recommended_for": "both"},
    "simple": {"description": "Unicode block shading, smooth print-like look", "recommended_for": "photo"},
    "classic": {"description": "70-character fine gradient, maximum tonal range", "recommended_for": "photo"},
    "blocks": {"description": "Coarse block shading, good for high-contrast", "recommended_for": "logo"},
    "minimal": {"description": "Binary black/white, crispest edges", "recommended_for": "logo"},
    "hifi": {"description": "Repeated chars for fine gradation", "recommended_for": "photo"},
    "dense": {"description": "Heavy block shading, bold look", "recommended_for": "logo"},
    "ultra": {"description": "Repeated ASCII chars, balanced gradation", "recommended_for": "both"},
}

# Mode presets bundle all the processing settings
MODE_PRESETS = {
    "photo": {
        "charset": "detailed",
        "hifi": True,
        "fill_spaces": True,
        "trim": False,
        "invert": False,
        "alpha_background": (255, 255, 255),  # white
        "contrast": 1.8,
        "brightness": 1.1,
        "gamma": 0.8,
        "shadow_threshold": 0.2,
        "shadow_lift": 0.15,
    },
    "logo": {
        "charset": "detailed",
        "hifi": False,
        "fill_spaces": False,
        "trim": True,
        "invert": None,  # auto-detect
        "alpha_background": (0, 0, 0),  # black
        "contrast": 1.5,
        "brightness": 1.0,
        "gamma": 1.0,
        "shadow_threshold": 0.2,
        "shadow_lift": 0.15,
    },
}


def _get_ansi_color(r: int, g: int, b: int) -> str:
    color_code = 16 + (36 * (r // 51)) + (6 * (g // 51)) + (b // 51)
    return f"\033[38;5;{color_code}m"


ANSI_RESET = "\033[0m"


def _detect_light_background(img: Image.Image, threshold: float = 200.0) -> bool:
    """Sample corner regions to detect if the image has a light background."""
    gray = img.convert("L")
    pixels = np.array(gray, dtype=np.float64)
    h, w = pixels.shape

    sample_size_h = max(1, h // 10)
    sample_size_w = max(1, w // 10)

    corners = [
        pixels[:sample_size_h, :sample_size_w],           # top-left
        pixels[:sample_size_h, -sample_size_w:],           # top-right
        pixels[-sample_size_h:, :sample_size_w],           # bottom-left
        pixels[-sample_size_h:, -sample_size_w:],          # bottom-right
    ]

    corner_mean = np.mean([np.mean(c) for c in corners])
    return corner_mean > threshold


def _trim_whitespace(pixels: np.ndarray, color_pixels: Optional[np.ndarray] = None, threshold: float = 250.0) -> Tuple[np.ndarray, Optional[np.ndarray]]:
    """Remove rows and columns that are entirely near-white or near-black (uniform background)."""
    h, w = pixels.shape

    # Detect whether background is light or dark from corners
    corner_vals = [
        pixels[0, 0], pixels[0, -1], pixels[-1, 0], pixels[-1, -1]
    ]
    bg_bright = np.mean(corner_vals) > 128

    if bg_bright:
        # Trim near-white rows/cols
        row_mask = np.any(pixels < threshold, axis=1)
        col_mask = np.any(pixels < threshold, axis=0)
    else:
        # Trim near-black rows/cols
        dark_threshold = 255 - threshold
        row_mask = np.any(pixels > dark_threshold, axis=1)
        col_mask = np.any(pixels > dark_threshold, axis=0)

    if not np.any(row_mask) or not np.any(col_mask):
        return pixels, color_pixels

    row_start = np.argmax(row_mask)
    row_end = h - np.argmax(row_mask[::-1])
    col_start = np.argmax(col_mask)
    col_end = w - np.argmax(col_mask[::-1])

    # Add small padding (1 row/col) if possible
    row_start = max(0, row_start - 1)
    row_end = min(h, row_end + 1)
    col_start = max(0, col_start - 1)
    col_end = min(w, col_end + 1)

    trimmed = pixels[row_start:row_end, col_start:col_end]
    trimmed_color = None
    if color_pixels is not None:
        trimmed_color = color_pixels[row_start:row_end, col_start:col_end]

    return trimmed, trimmed_color


def _gentle_shadow_lift(pixels: np.ndarray, threshold: float = 0.2, strength: float = 0.15) -> np.ndarray:
    """Lift very dark areas slightly to preserve detail."""
    normalized = pixels / 255.0
    lifted = np.where(
        normalized < threshold,
        normalized + strength * (threshold - normalized) / threshold,
        normalized,
    )
    return np.clip(lifted, 0, 1) * 255.0


def convert(
    image_path: str,
    mode: str = "photo",
    width: int = 80,
    charset: Optional[str] = None,
    color: bool = False,
    invert: Optional[bool] = None,
) -> str:
    """Convert an image to ASCII art.

    Args:
        image_path: Path to the image file.
        mode: "photo" or "logo" — sets processing defaults.
        width: Output width in characters.
        charset: Character set name. If None, uses mode default.
        color: Enable ANSI 256-color output.
        invert: Flip brightness mapping. None = use mode default (auto for logo).

    Returns:
        ASCII art as a newline-separated string.
    """
    if mode not in MODE_PRESETS:
        raise ValueError(f"Unknown mode '{mode}'. Use 'photo' or 'logo'.")

    preset = MODE_PRESETS[mode]
    chars = CHAR_SETS.get(charset or preset["charset"], CHAR_SETS["detailed"])
    fill_spaces = preset["fill_spaces"]
    do_trim = preset["trim"]
    hifi = preset["hifi"]

    # Resolve invert: explicit param > preset > auto-detect
    if invert is not None:
        do_invert = invert
    elif preset["invert"] is not None:
        do_invert = preset["invert"]
    else:
        do_invert = None  # will auto-detect below

    # Load image
    img = Image.open(image_path)

    # Handle alpha channel
    if img.mode == "RGBA":
        bg = Image.new("RGBA", img.size, preset["alpha_background"] + (255,))
        bg.paste(img, mask=img.split()[3])
        img = bg.convert("RGB")
    elif img.mode != "RGB":
        img = img.convert("RGB")

    # Auto-detect invert for logo mode
    if do_invert is None:
        do_invert = _detect_light_background(img)

    # Store color image before grayscale conversion
    color_img = img.copy() if color else None

    # Convert to grayscale
    gray = img.convert("L")

    # Apply processing based on mode
    if hifi:
        gray = gray.filter(ImageFilter.UnsharpMask(radius=1, percent=120, threshold=2))
        gray = Image.eval(gray, lambda x: int(((x / 255.0) ** preset["gamma"]) * 255))
        enhancer = ImageEnhance.Contrast(gray)
        gray = enhancer.enhance(preset["contrast"])
        enhancer = ImageEnhance.Brightness(gray)
        gray = enhancer.enhance(preset["brightness"])
    else:
        enhancer = ImageEnhance.Contrast(gray)
        gray = enhancer.enhance(preset["contrast"])

    # Resize maintaining aspect ratio
    aspect_ratio = gray.height / gray.width
    new_height = max(1, int(width * aspect_ratio * 0.55))
    resample = Image.Resampling.LANCZOS if hifi else Image.Resampling.BILINEAR
    gray = gray.resize((width, new_height), resample)

    if color_img is not None:
        color_img = color_img.resize((width, new_height), resample)

    pixels = np.array(gray, dtype=np.float64)
    color_pixels = np.array(color_img) if color_img is not None else None

    # Trim whitespace borders for logos
    if do_trim:
        pixels, color_pixels = _trim_whitespace(pixels, color_pixels)

    # HiFi shadow processing
    if hifi:
        pixels = _gentle_shadow_lift(pixels, preset["shadow_threshold"], preset["shadow_lift"])

    # Normalize to full range
    px_min, px_max = pixels.min(), pixels.max()
    if px_max > px_min:
        pixels = (pixels - px_min) * 255.0 / (px_max - px_min)
    pixels = np.clip(pixels, 0, 255)

    # Map to character indices
    char_indices = (pixels * (len(chars) - 1) / 255.0).astype(int)
    char_indices = np.clip(char_indices, 0, len(chars) - 1)

    # Build ASCII art
    lines = []
    for row_idx, row in enumerate(char_indices):
        line = ""
        for col_idx, idx in enumerate(row):
            if do_invert:
                ch = chars[len(chars) - 1 - idx]
            else:
                ch = chars[idx]

            # Ensure single character
            if len(ch) > 1:
                ch = ch[0]

            # Space fill
            if ch == " " and fill_spaces:
                ch = "░"

            # Color
            if color and color_pixels is not None:
                r, g, b = color_pixels[row_idx, col_idx]
                line += _get_ansi_color(r, g, b) + ch
            else:
                line += ch

        if color:
            line += ANSI_RESET

        lines.append(line.rstrip())

    return "\n".join(lines)
