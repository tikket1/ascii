# Tikket ASCII

Convert images to high-fidelity colored ASCII art with animation and cipher features.

## Quick Start

```bash
./setup.sh
source venv/bin/activate
python tikket_ascii.py your_image.jpg --color --width 120
```

## Features

- **High-fidelity ASCII conversion** with realistic color mapping
- **Multiple character sets** (standard, detailed, blocks, shading)
- **Variable resolution** (40-200+ character widths)
- **Animation support** for moving ASCII art
- **Secret cipher** for text encryption
- **Advanced image processing** with shadow enhancement

## Usage Examples

```bash
# Basic ASCII (no color)
python tikket_ascii.py image.jpg

# Colored high-resolution
python tikket_ascii.py image.jpg --color --width 160

# Different character set
python tikket_ascii.py image.jpg --color --charset detailed

# Encrypt text
python tikket_ascii.py --cipher "secret message" --shift 5
```

## Requirements

- Python 3.7+
- PIL/Pillow, NumPy, SciPy, scikit-image (auto-installed by setup.sh)