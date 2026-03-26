"""
ASCII Art MCP Server — Expose image-to-ASCII conversion as MCP tools.
"""

import os
from mcp.server.fastmcp import FastMCP
from ascii_art_mcp.engine import convert, CHAR_SETS, CHARSET_INFO, COLOR_PALETTES

mcp = FastMCP(
    "ascii-art",
    instructions="Convert images to ASCII art with photo and logo modes. Use 'photo' mode for photographs and 'logo' mode for logos/text/graphics.",
)


@mcp.tool()
def convert_image(
    image_path: str,
    mode: str,
    width: int = 80,
    charset: str | None = None,
    color: bool = False,
    color_style: str = "natural",
    invert: bool | None = None,
) -> str:
    """Convert an image to ASCII art.

    Args:
        image_path: Absolute path to an image file (PNG, JPG, BMP, GIF, TIFF, WebP).
        mode: "photo" for photographs/realistic images, "logo" for logos/text/graphics.
              Photo mode: hi-fi processing, fills empty space with ░ for visibility.
              Logo mode: clean spaces, trims whitespace borders, auto-inverts light backgrounds.
        width: Output width in characters. Default 80. Range 20-200.
        charset: Character set to use. Run list_charsets to see options. If omitted, uses mode default.
        color: Enable ANSI 256-color output. Best viewed in terminals that support it.
        color_style: Color palette — "natural", "vivid", "ocean", or "sunset".
        invert: Flip brightness mapping. In logo mode, this auto-detects if not specified.

    Returns:
        ASCII art as text, one line per row.
    """
    image_path = os.path.expanduser(image_path)

    if not os.path.isfile(image_path):
        raise FileNotFoundError(f"Image not found: {image_path}")

    width = max(20, min(200, width))

    if charset is not None and charset not in CHAR_SETS:
        available = ", ".join(CHAR_SETS.keys())
        raise ValueError(f"Unknown charset '{charset}'. Available: {available}")

    if color_style not in COLOR_PALETTES:
        available = ", ".join(COLOR_PALETTES.keys())
        raise ValueError(f"Unknown color_style '{color_style}'. Available: {available}")

    return convert(
        image_path=image_path,
        mode=mode,
        width=width,
        charset=charset,
        color=color,
        color_style=color_style,
        invert=invert,
    )


@mcp.tool()
def list_charsets() -> list[dict]:
    """List available character sets for ASCII art conversion.

    Returns information about each charset including its characters,
    description, and whether it's recommended for photos, logos, or both.
    """
    result = []
    for name, chars in CHAR_SETS.items():
        info = CHARSET_INFO.get(name, {})
        # Show unique chars for display
        unique = "".join(dict.fromkeys(chars))
        result.append({
            "name": name,
            "characters": unique,
            "num_levels": len(set(chars)),
            "description": info.get("description", ""),
            "recommended_for": info.get("recommended_for", "both"),
        })
    return result


def main():
    mcp.run()


if __name__ == "__main__":
    main()
