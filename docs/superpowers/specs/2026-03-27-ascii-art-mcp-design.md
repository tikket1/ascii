# ASCII Art MCP Server — Design Spec

## Overview

An open-source MCP server that converts images to ASCII art. Two explicit modes — `photo` and `logo` — bundle the right processing defaults for each use case. Dead simple to install, capable underneath.

## MCP Tools

### `convert`

The main tool. Converts an image file to ASCII art.

**Parameters:**

| Param | Type | Required | Default | Description |
|-------|------|----------|---------|-------------|
| `image_path` | string | yes | — | Absolute path to image file |
| `mode` | string | yes | — | `"photo"` or `"logo"` |
| `width` | int | no | 80 | Output width in characters |
| `charset` | string | no | mode default | Character set override |
| `color` | bool | no | false | Enable ANSI 256-color output |
| `color_style` | string | no | "natural" | Color palette: natural, vivid, ocean, sunset |
| `invert` | bool | no | mode default | Flip brightness mapping |

**Returns:** The ASCII art as a string (newline-separated lines).

**Mode defaults:**

| Setting | Photo | Logo |
|---------|-------|------|
| charset | `detailed` | `detailed` |
| hifi processing | yes | no |
| fill spaces with ░ | yes | no (real spaces) |
| trim whitespace borders | no | yes |
| alpha compositing | white background | black background |
| auto-invert | no | yes (if light bg detected) |

### `list_charsets`

Returns available character sets with example characters and recommended use case (photo vs logo vs both).

**Parameters:** None.

**Returns:** JSON list of charset objects: `{ name, chars, recommended_for }`.

## Engine Fixes (from current tikket_ascii.py)

1. **Configurable space fill**: The `░` replacement (line 293-294) becomes a parameter `fill_spaces: bool`. Photo mode enables it, logo mode disables it.

2. **Alpha channel awareness**: Detect RGBA images. In logo mode, composite against black (so white-on-transparent logos become visible). In photo mode, composite against white (standard behavior).

3. **Whitespace trimming**: In logo mode, detect and remove rows/columns that are entirely background (uniform brightness at image edges). Trim before conversion so the ASCII output is tight around the subject.

4. **Auto-invert for logos**: Sample corner pixels of the image. If the background is light (mean brightness > 200), auto-invert the output so the logo renders as dense characters on empty space. User can override with explicit `invert` param.

5. **Clean up hardcoded settings**: Bundle shadow_threshold, gamma, contrast, clip_limit into the mode presets rather than scattered magic numbers.

## What's Cut (v1)

- Animation system (terminal-only, doesn't map to MCP)
- Secret cipher (steganography is stubbed/non-functional)
- Platform formatters (Discord, WhatsApp, etc. — consumer decides formatting)
- Flask web GUI (separate concern)
- Color palettes beyond the existing 4

## Project Structure

```
ascii/
├── pyproject.toml          # Package config, entry point for MCP
├── README.md               # Install + usage docs
├── src/
│   └── ascii_art_mcp/
│       ├── __init__.py
│       ├── server.py       # MCP server (FastMCP)
│       └── engine.py       # Refactored ASCIIConverter
└── tests/
    └── test_engine.py      # Basic conversion tests
```

## Install & Usage

```bash
# Install
pip install ascii-art-mcp
# or
uvx ascii-art-mcp

# Claude Code config
# settings.json -> mcpServers:
{
  "ascii-art": {
    "command": "uvx",
    "args": ["ascii-art-mcp"]
  }
}
```

## Dependencies

- `mcp[cli]` — MCP Python SDK
- `Pillow` — image loading/processing
- `numpy` — pixel math
- `scipy` — gaussian filters, ndimage
- `scikit-image` — adaptive histogram equalization (optional, graceful fallback)
