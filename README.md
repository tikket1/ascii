# ascii-art-mcp

MCP server for converting images to ASCII art.

![Photo mode — NASA astronaut rendered as hi-fi colored ASCII art](ascii_preview.png)

> 200 chars wide, `classic` charset (70 tonal levels), hi-fi color — every character is a pixel.

Two modes — **photo** and **logo** — with smart defaults for each.

| | Photo | Logo |
|---|---|---|
| **Processing** | Hi-fi: sharpening, gamma, shadow lifting | Standard contrast |
| **Background** | `░` fill for visibility | Clean spaces |
| **Trimming** | None | Auto-trims whitespace borders |
| **Invert** | Off | Auto-detects light backgrounds |
| **Alpha** | Composites on white | Composites on black |

![Logo mode — horse silhouette as ASCII art](ascii_logo_preview.png)

## Quick Start

Works out of the box as an MCP server — install it, add it to your config, done.

```bash
pip install ascii-art-mcp
```

Add to your Claude Code settings (`~/.claude/settings.json`):

```json
{
  "mcpServers": {
    "ascii-art": {
      "command": "uvx",
      "args": ["ascii-art-mcp"]
    }
  }
}
```

That's it. The server starts automatically when Claude Code launches, advertises its tools (`convert_image`, `list_charsets`), and handles requests over stdio. No API keys, no configuration, no hosting.

Then just ask:

> "Convert this screenshot to ASCII art in logo mode"
> "Turn my profile photo into colored ASCII art"

Works with any MCP-compatible client (Claude Code, Cursor, etc.).

## Tools

### `convert_image`

Convert an image to ASCII art.

| Parameter | Type | Required | Default | Description |
|-----------|------|----------|---------|-------------|
| `image_path` | string | yes | — | Path to image file |
| `mode` | string | yes | — | `"photo"` or `"logo"` |
| `width` | int | no | 80 | Output width (20-200 chars) |
| `charset` | string | no | auto | Character set (run `list_charsets`) |
| `color` | bool | no | false | ANSI 256-color output |
| `invert` | bool | no | auto | Flip brightness mapping |

**Photo mode** — optimized for photographs: hi-fi processing with shadow lifting, sharpening, gamma correction. Fills empty space with `░` for visibility in terminals/chat.

**Logo mode** — optimized for logos, icons, and text: clean spaces (no `░` fill), auto-trims whitespace borders, auto-inverts light backgrounds, alpha-aware compositing against black.

### `list_charsets`

Returns available character sets with descriptions and recommendations.

## Character Sets

| Name | Levels | Best for | Description |
|------|--------|----------|-------------|
| `detailed` | 10 | both | ASCII gradient, good all-rounder |
| `classic` | 70 | photo | Maximum tonal range |
| `simple` | 9 | photo | Unicode block shading |
| `hifi` | ~9 | photo | Repeated chars for fine gradation |
| `minimal` | 3 | logo | Binary black/white, crispest edges |
| `blocks` | ~4 | logo | Coarse block shading |
| `dense` | ~4 | logo | Heavy block shading |
| `ultra` | ~9 | both | Balanced ASCII gradation |

## License

MIT
