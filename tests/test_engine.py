"""Basic tests for the ASCII art engine."""

import os
import tempfile
from PIL import Image
from ascii_art_mcp.engine import convert, CHAR_SETS, CHARSET_INFO, _detect_light_background, _trim_whitespace
import numpy as np


def _make_test_image(color=(128, 128, 128), size=(100, 100), mode="RGB"):
    """Create a simple test image."""
    img = Image.new(mode, size, color)
    fd, path = tempfile.mkstemp(suffix=".png")
    os.close(fd)
    img.save(path)
    return path


def _make_logo_image():
    """Create a dark shape on white background (like a logo)."""
    img = Image.new("RGB", (200, 100), (255, 255, 255))
    # Draw a dark rectangle in the center
    pixels = img.load()
    for x in range(60, 140):
        for y in range(20, 80):
            pixels[x, y] = (0, 0, 0)
    fd, path = tempfile.mkstemp(suffix=".png")
    os.close(fd)
    img.save(path)
    return path


def _make_alpha_image():
    """Create white text on transparent background."""
    img = Image.new("RGBA", (200, 100), (0, 0, 0, 0))
    pixels = img.load()
    for x in range(60, 140):
        for y in range(20, 80):
            pixels[x, y] = (255, 255, 255, 255)
    fd, path = tempfile.mkstemp(suffix=".png")
    os.close(fd)
    img.save(path)
    return path


class TestConvert:
    def test_photo_mode_returns_string(self):
        path = _make_test_image()
        result = convert(path, mode="photo", width=40)
        os.unlink(path)
        assert isinstance(result, str)
        assert len(result.split("\n")) > 0

    def test_logo_mode_returns_string(self):
        path = _make_test_image()
        result = convert(path, mode="logo", width=40)
        os.unlink(path)
        assert isinstance(result, str)

    def test_photo_mode_uses_fill(self):
        path = _make_test_image(color=(255, 255, 255))
        result = convert(path, mode="photo", width=40)
        os.unlink(path)
        assert "░" in result

    def test_logo_mode_no_fill(self):
        path = _make_logo_image()
        result = convert(path, mode="logo", width=40)
        os.unlink(path)
        # Logo mode should have real spaces, not ░ fill
        lines = result.split("\n")
        has_real_space = any(" " in line for line in lines if line.strip())
        assert has_real_space

    def test_logo_mode_auto_inverts_light_bg(self):
        path = _make_logo_image()
        result = convert(path, mode="logo", width=40)
        os.unlink(path)
        # With auto-invert on a white bg image, dark areas should be dense chars
        lines = result.split("\n")
        assert any("@" in line or "#" in line for line in lines)

    def test_alpha_channel_logo(self):
        path = _make_alpha_image()
        result = convert(path, mode="logo", width=40)
        os.unlink(path)
        # Should NOT be all-empty — the alpha fix should make it visible
        non_empty = [l for l in result.split("\n") if l.strip()]
        assert len(non_empty) > 0

    def test_all_charsets_work(self):
        path = _make_test_image()
        for charset_name in CHAR_SETS:
            result = convert(path, mode="photo", width=40, charset=charset_name)
            assert isinstance(result, str)
            assert len(result) > 0
        os.unlink(path)

    def test_color_mode(self):
        path = _make_test_image(color=(255, 0, 0))
        result = convert(path, mode="photo", width=40, color=True)
        os.unlink(path)
        assert "\033[" in result  # ANSI escape codes present

    def test_explicit_invert(self):
        path = _make_test_image()
        normal = convert(path, mode="photo", width=40, invert=False)
        inverted = convert(path, mode="photo", width=40, invert=True)
        os.unlink(path)
        assert normal != inverted

    def test_width_respected(self):
        path = _make_test_image()
        for w in [20, 40, 80, 120]:
            result = convert(path, mode="photo", width=w)
            lines = result.split("\n")
            # Lines should not exceed requested width (ignoring ANSI codes)
            for line in lines:
                assert len(line) <= w + 5  # small tolerance for rounding
        os.unlink(path)

    def test_invalid_mode_raises(self):
        path = _make_test_image()
        try:
            convert(path, mode="invalid")
            assert False, "Should have raised ValueError"
        except ValueError:
            pass
        os.unlink(path)

    def test_invalid_charset_in_server(self):
        from ascii_art_mcp.server import convert_image
        path = _make_test_image()
        try:
            convert_image(path, mode="photo", charset="nonexistent")
            assert False, "Should have raised ValueError"
        except ValueError:
            pass
        os.unlink(path)


class TestDetectLightBackground:
    def test_white_image(self):
        img = Image.new("RGB", (100, 100), (255, 255, 255))
        assert _detect_light_background(img) == True

    def test_black_image(self):
        img = Image.new("RGB", (100, 100), (0, 0, 0))
        assert _detect_light_background(img) == False

    def test_dark_center_light_border(self):
        img = Image.new("RGB", (100, 100), (240, 240, 240))
        pixels = img.load()
        for x in range(30, 70):
            for y in range(30, 70):
                pixels[x, y] = (0, 0, 0)
        assert _detect_light_background(img) == True


class TestCharsetInfo:
    def test_all_charsets_have_info(self):
        for name in CHAR_SETS:
            assert name in CHARSET_INFO, f"Missing info for charset '{name}'"

    def test_info_has_required_fields(self):
        for name, info in CHARSET_INFO.items():
            assert "description" in info
            assert "recommended_for" in info
            assert info["recommended_for"] in ("photo", "logo", "both")
