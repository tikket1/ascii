# Tikket ASCII Art Generator

A professional web-based ASCII art generator with advanced image processing capabilities.

## Features

- **High-fidelity ASCII conversion** with realistic color mapping
- **Multiple character sets** (detailed, simple, classic, blocks, minimal, hifi, photorealistic)
- **Variable resolution** (20-400+ character widths) 
- **Real-time preview** with live setting adjustments
- **Color support** with multiple palette options
- **Export options** for different platforms (WhatsApp, Discord, Email)
- **Background modes** (black, white, transparent)
- **Hidden message encryption** using steganographic techniques
- **Responsive web interface** with modern, clean design

## Quick Start

### Command Line Interface

```bash
# Install dependencies
pip install -r requirements.txt

# Basic usage
python tikket_ascii.py image.jpg

# With color and custom width
python tikket_ascii.py image.jpg --color --width 160

# Different character set
python tikket_ascii.py image.jpg --style detailed --color
```

### Web Interface

```bash
# Start the web server
python app.py

# Open browser to http://localhost:5001
```

## Installation

```bash
git clone https://github.com/yourusername/tikket-ascii
cd tikket-ascii
pip install -r requirements.txt
```

## Requirements

- Python 3.7+
- PIL/Pillow
- NumPy
- SciPy
- scikit-image
- Flask (for web interface)

## Usage Examples

### Command Line

```bash
# Basic ASCII (no color)
python tikket_ascii.py image.jpg

# High-resolution colored output
python tikket_ascii.py image.jpg --color --width 200 --hifi

# Custom character set with invert
python tikket_ascii.py image.jpg --style blocks --invert

# Hide secret message
python tikket_ascii.py image.jpg --hide-message "secret text"
```

### Web Interface

1. Upload an image using the file selector
2. Adjust width, style, and color options
3. See real-time preview as you change settings
4. Copy output in different formats for various platforms
5. Switch background modes for optimal viewing

## Character Sets

- **detailed**: `@%#*+=-:. ` (high detail)
- **simple**: `█▉▊▋▌▍▎▏ ` (block characters)
- **classic**: Full ASCII character range
- **blocks**: `██▓▒░  ` (solid blocks)
- **minimal**: `■□ ` (simple shapes)

## Architecture

- **Backend**: Flask web server with image processing pipeline
- **Frontend**: Modern vanilla JavaScript with responsive CSS
- **Image Processing**: PIL/Pillow with NumPy optimizations
- **Real-time Updates**: Debounced AJAX requests for smooth UX
- **Export System**: Multi-format output for platform compatibility

## Contributing

1. Fork the repository
2. Create a feature branch
3. Make your changes
4. Add tests if applicable
5. Submit a pull request

## License

MIT License - see LICENSE file for details

## Performance

- Handles images up to 16MB
- Real-time processing for most common image sizes
- Optimized algorithms for fast conversion
- Memory-efficient temporary file handling

## Browser Support

- Chrome 80+
- Firefox 75+
- Safari 13+
- Edge 80+

## Security

- File type validation
- Size limits enforced
- Secure filename handling
- Temporary file cleanup
- Input sanitization