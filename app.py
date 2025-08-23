#!/usr/bin/env python3
"""
Flask Web GUI for Tikket ASCII Art Generator

████████ ██ ██   ██ ██   ██ ███████ ████████ 
   ██    ██ ██  ██  ██  ██  ██         ██    
   ██    ██ █████   █████   █████      ██    
   ██    ██ ██  ██  ██  ██  ██         ██    
   ██    ██ ██   ██ ██   ██ ███████    ██    

A fun little side project I've been working on for converting images
to ASCII art. Started this because I was bored one weekend and wanted
to mess around with image processing in Python.
"""

import os
import tempfile
import re
import magic
from flask import Flask, render_template, request, jsonify, send_from_directory
from werkzeug.utils import secure_filename
from PIL import Image
from tikket_ascii import ASCIIConverter, SecretCipher

app = Flask(__name__)
app.config['MAX_CONTENT_LENGTH'] = 16 * 1024 * 1024  # 16MB should be plenty for most images
app.config['UPLOAD_FOLDER'] = tempfile.mkdtemp()

# Security headers
@app.after_request
def add_security_headers(response):
    # Content Security Policy - restrict script sources
    response.headers['Content-Security-Policy'] = (
        "default-src 'self'; "
        "script-src 'self' 'unsafe-inline'; "  # Needed for inline scripts
        "style-src 'self' 'unsafe-inline' fonts.googleapis.com; "
        "font-src 'self' fonts.gstatic.com; "
        "img-src 'self' data:; "
        "connect-src 'self'; "
        "frame-ancestors 'none';"
    )
    
    # Additional security headers
    response.headers['X-Frame-Options'] = 'DENY'
    response.headers['X-Content-Type-Options'] = 'nosniff'
    response.headers['X-XSS-Protection'] = '1; mode=block'
    response.headers['Referrer-Policy'] = 'strict-origin-when-cross-origin'
    response.headers['Permissions-Policy'] = 'geolocation=(), microphone=(), camera=()'
    
    return response

# TODO: Maybe add support for more exotic formats later?
ALLOWED_EXTENSIONS = {'png', 'jpg', 'jpeg', 'gif', 'bmp', 'tiff', 'webp'}

def allowed_file(filename):
    """Check if file extension is allowed"""
    return '.' in filename and \
           filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS

def validate_image_file(filepath):
    """Validate uploaded file is actually a legitimate image"""
    try:
        # Check MIME type using python-magic
        mime = magic.from_file(filepath, mime=True)
        if not mime.startswith('image/'):
            return False, f"File is not a valid image (detected: {mime})"
        
        # Try to open with PIL to verify it's a real image
        with Image.open(filepath) as img:
            # Verify image format matches extension
            if img.format.lower() not in ['png', 'jpeg', 'jpg', 'gif', 'bmp', 'tiff', 'webp']:
                return False, f"Unsupported image format: {img.format}"
            
            # Check for reasonable dimensions (prevent memory bombs)
            width, height = img.size
            if width > 10000 or height > 10000:
                return False, f"Image too large: {width}x{height} (max 10000x10000)"
            
            if width * height > 50000000:  # 50MP limit
                return False, "Image has too many pixels (max 50 megapixels)"
            
            # Load a small portion to verify it's not corrupted
            img.load()
            
        return True, "Valid image"
        
    except Exception as e:
        return False, f"Invalid image file: {str(e)}"

def remove_ansi_codes(text):
    """Remove ANSI color codes from text"""
    ansi_escape = re.compile(r'\x1b\[[0-9;]*m')
    return ansi_escape.sub('', text)

def clean_ascii_for_external(ascii_lines):
    """Clean ASCII art for optimal formatting in Discord and other platforms"""
    cleaned_lines = []
    max_width = 0
    
    # First pass: clean lines and find max width
    # This was a pain to figure out - Discord is super picky about formatting
    for line in ascii_lines:
        # Strip out those annoying ANSI color codes
        clean_line = remove_ansi_codes(line)
        # Convert light shade back to spaces for copying (learned this the hard way)
        clean_line = clean_line.replace('░', ' ')
        # Strip trailing spaces but keep the line structure
        clean_line = clean_line.rstrip()
        cleaned_lines.append(clean_line)
        max_width = max(max_width, len(clean_line))
    
    # Second pass: normalize width and remove empty trailing lines
    normalized_lines = []
    for line in cleaned_lines:
        # Pad to consistent width to maintain grid structure
        padded_line = line.ljust(max_width) if line.strip() else ''
        normalized_lines.append(padded_line.rstrip())  # Remove padding spaces at end
    
    # Remove trailing empty lines
    while normalized_lines and not normalized_lines[-1].strip():
        normalized_lines.pop()
    
    return normalized_lines

def format_for_whatsapp(ascii_lines):
    """Format ASCII for WhatsApp - uses monospace formatting"""
    cleaned = clean_ascii_for_external(ascii_lines)
    # WhatsApp uses triple backticks for monospace
    formatted = "```\n" + "\n".join(cleaned) + "\n```"
    return formatted

def format_for_discord(ascii_lines):
    """Format ASCII for Discord - uses code blocks"""
    cleaned = clean_ascii_for_external(ascii_lines)
    # Discord uses triple backticks for code blocks
    formatted = "```\n" + "\n".join(cleaned) + "\n```"
    return formatted

def format_for_print(ascii_lines):
    """Format ASCII for printing - clean and compact"""
    cleaned = clean_ascii_for_external(ascii_lines)
    # Add page header and footer for printing
    formatted = "ASCII Art - Generated by Tikket ASCII\n" + "="*50 + "\n\n"
    formatted += "\n".join(cleaned)
    formatted += "\n\n" + "="*50 + "\nGenerated at: " + str(__import__('datetime').datetime.now().strftime('%Y-%m-%d %H:%M:%S'))
    return formatted

def format_for_email(ascii_lines):
    """Format ASCII for email - with proper spacing"""
    cleaned = clean_ascii_for_external(ascii_lines)
    # Use non-breaking spaces to prevent email clients from collapsing whitespace
    formatted_lines = []
    for line in cleaned:
        # Replace regular spaces with non-breaking spaces
        email_line = line.replace(' ', '\u00A0')
        formatted_lines.append(email_line)
    return "\n".join(formatted_lines)

def convert_ansi_to_html(ascii_lines):
    """Convert ANSI color codes to HTML spans"""
    html_lines = []
    
    # ANSI 256-color palette mapping to hex colors
    ansi_colors = {
        '16': '#000000', '17': '#00005f', '18': '#000087', '19': '#0000af', '20': '#0000d7', '21': '#0000ff',
        '22': '#005f00', '23': '#005f5f', '24': '#005f87', '25': '#005faf', '26': '#005fd7', '27': '#005fff',
        '28': '#008700', '29': '#00875f', '30': '#008787', '31': '#0087af', '32': '#0087d7', '33': '#0087ff',
        '34': '#00af00', '35': '#00af5f', '36': '#00af87', '37': '#00afaf', '38': '#00afd7', '39': '#00afff',
        '40': '#00d700', '41': '#00d75f', '42': '#00d787', '43': '#00d7af', '44': '#00d7d7', '45': '#00d7ff',
        '46': '#00ff00', '47': '#00ff5f', '48': '#00ff87', '49': '#00ffaf', '50': '#00ffd7', '51': '#00ffff',
        '52': '#5f0000', '53': '#5f005f', '54': '#5f0087', '55': '#5f00af', '56': '#5f00d7', '57': '#5f00ff',
        '58': '#5f5f00', '59': '#5f5f5f', '60': '#5f5f87', '61': '#5f5faf', '62': '#5f5fd7', '63': '#5f5fff',
        '64': '#5f8700', '65': '#5f875f', '66': '#5f8787', '67': '#5f87af', '68': '#5f87d7', '69': '#5f87ff',
        '70': '#5faf00', '71': '#5faf5f', '72': '#5faf87', '73': '#5fafaf', '74': '#5fafd7', '75': '#5fafff',
        '76': '#5fd700', '77': '#5fd75f', '78': '#5fd787', '79': '#5fd7af', '80': '#5fd7d7', '81': '#5fd7ff',
        '82': '#5fff00', '83': '#5fff5f', '84': '#5fff87', '85': '#5fffaf', '86': '#5fffd7', '87': '#5fffff',
        '88': '#870000', '89': '#87005f', '90': '#870087', '91': '#8700af', '92': '#8700d7', '93': '#8700ff',
        '94': '#875f00', '95': '#875f5f', '96': '#875f87', '97': '#875faf', '98': '#875fd7', '99': '#875fff',
        '100': '#878700', '101': '#87875f', '102': '#878787', '103': '#8787af', '104': '#8787d7', '105': '#8787ff',
        '106': '#87af00', '107': '#87af5f', '108': '#87af87', '109': '#87afaf', '110': '#87afd7', '111': '#87afff',
        '112': '#87d700', '113': '#87d75f', '114': '#87d787', '115': '#87d7af', '116': '#87d7d7', '117': '#87d7ff',
        '118': '#87ff00', '119': '#87ff5f', '120': '#87ff87', '121': '#87ffaf', '122': '#87ffd7', '123': '#87ffff',
        '124': '#af0000', '125': '#af005f', '126': '#af0087', '127': '#af00af', '128': '#af00d7', '129': '#af00ff',
        '130': '#af5f00', '131': '#af5f5f', '132': '#af5f87', '133': '#af5faf', '134': '#af5fd7', '135': '#af5fff',
        '136': '#af8700', '137': '#af875f', '138': '#af8787', '139': '#af87af', '140': '#af87d7', '141': '#af87ff',
        '142': '#afaf00', '143': '#afaf5f', '144': '#afaf87', '145': '#afafaf', '146': '#afafd7', '147': '#afafff',
        '148': '#afd700', '149': '#afd75f', '150': '#afd787', '151': '#afd7af', '152': '#afd7d7', '153': '#afd7ff',
        '154': '#afff00', '155': '#afff5f', '156': '#afff87', '157': '#afffaf', '158': '#afffd7', '159': '#afffff',
        '160': '#d70000', '161': '#d7005f', '162': '#d70087', '163': '#d700af', '164': '#d700d7', '165': '#d700ff',
        '166': '#d75f00', '167': '#d75f5f', '168': '#d75f87', '169': '#d75faf', '170': '#d75fd7', '171': '#d75fff',
        '172': '#d78700', '173': '#d7875f', '174': '#d78787', '175': '#d787af', '176': '#d787d7', '177': '#d787ff',
        '178': '#d7af00', '179': '#d7af5f', '180': '#d7af87', '181': '#d7afaf', '182': '#d7afd7', '183': '#d7afff',
        '184': '#d7d700', '185': '#d7d75f', '186': '#d7d787', '187': '#d7d7af', '188': '#d7d7d7', '189': '#d7d7ff',
        '190': '#d7ff00', '191': '#d7ff5f', '192': '#d7ff87', '193': '#d7ffaf', '194': '#d7ffd7', '195': '#d7ffff',
        '196': '#ff0000', '197': '#ff005f', '198': '#ff0087', '199': '#ff00af', '200': '#ff00d7', '201': '#ff00ff',
        '202': '#ff5f00', '203': '#ff5f5f', '204': '#ff5f87', '205': '#ff5faf', '206': '#ff5fd7', '207': '#ff5fff',
        '208': '#ff8700', '209': '#ff875f', '210': '#ff8787', '211': '#ff87af', '212': '#ff87d7', '213': '#ff87ff',
        '214': '#ffaf00', '215': '#ffaf5f', '216': '#ffaf87', '217': '#ffafaf', '218': '#ffafd7', '219': '#ffafff',
        '220': '#ffd700', '221': '#ffd75f', '222': '#ffd787', '223': '#ffd7af', '224': '#ffd7d7', '225': '#ffd7ff',
        '226': '#ffff00', '227': '#ffff5f', '228': '#ffff87', '229': '#ffffaf', '230': '#ffffd7', '231': '#ffffff',
    }
    
    for line in ascii_lines:
        # Reset any existing color state
        html_line = ""
        current_color = None
        i = 0
        
        while i < len(line):
            # Look for ANSI escape sequences
            if line[i:i+7] == '\033[38;5;':  # Start of 256-color foreground sequence
                # Find the end of the color code
                color_start = i + 7
                color_end = line.find('m', color_start)
                if color_end != -1:
                    color_code = line[color_start:color_end]
                    
                    # Close previous span if exists
                    if current_color:
                        html_line += '</span>'
                    
                    # Start new colored span
                    hex_color = ansi_colors.get(color_code, '#ffffff')
                    html_line += f'<span style="color: {hex_color};">'
                    current_color = color_code
                    
                    i = color_end + 1  # Skip past the 'm'
                    continue
            elif line[i:i+4] == '\033[0m':  # Reset sequence
                if current_color:
                    html_line += '</span>'
                    current_color = None
                i += 4
                continue
            else:
                html_line += line[i]
                i += 1
        
        # Close any remaining span
        if current_color:
            html_line += '</span>'
        
        html_lines.append(html_line)
    
    return html_lines

@app.route('/')
def index():
    """Main page with upload form"""
    return render_template('index.html')

@app.route('/convert', methods=['POST'])
def convert_image():
    """Handle image upload and conversion"""
    try:
        # Check if file was uploaded
        if 'image' not in request.files:
            return jsonify({'error': 'No image file provided'}), 400
        
        file = request.files['image']
        if file.filename == '':
            return jsonify({'error': 'No file selected'}), 400
        
        if not allowed_file(file.filename):
            return jsonify({'error': 'Invalid file type. Please use PNG, JPG, JPEG, GIF, BMP, TIFF, or WebP'}), 400
        
        # Save uploaded file securely
        filename = secure_filename(file.filename)
        # Generate unique filename to prevent conflicts and path traversal
        import uuid
        safe_filename = f"{uuid.uuid4().hex}_{filename}"
        filepath = os.path.join(app.config['UPLOAD_FOLDER'], safe_filename)
        file.save(filepath)
        
        # Validate the uploaded file is actually an image
        is_valid, validation_msg = validate_image_file(filepath)
        if not is_valid:
            os.remove(filepath)  # Clean up invalid file
            return jsonify({'error': f'Security validation failed: {validation_msg}'}), 400
        
        # Validate and sanitize form parameters
        try:
            width = int(request.form.get('width', 80))
            if not 20 <= width <= 400:
                width = max(20, min(400, width))  # Clamp to valid range
        except (ValueError, TypeError):
            width = 80
            
        style = request.form.get('style', 'detailed')
        # Validate style is in allowed set
        allowed_styles = {'detailed', 'simple', 'classic', 'blocks', 'minimal', 'hifi', 'photorealistic', 'dense', 'ultra'}
        if style not in allowed_styles:
            style = 'detailed'
            
        invert = request.form.get('invert') == 'on'
        hifi = request.form.get('hifi') == 'on'
        color = request.form.get('color') == 'on'
        
        color_style = request.form.get('color_style', 'natural')
        allowed_color_styles = {'natural', 'vivid', 'ocean', 'sunset'}
        if color_style not in allowed_color_styles:
            color_style = 'natural'
            
        # Sanitize hidden message input
        hide_message = request.form.get('hide_message', '').strip()
        if hide_message:
            # Limit message length and remove potentially dangerous characters
            hide_message = hide_message[:200]  # Max 200 chars
            # Only allow alphanumeric, spaces, and basic punctuation
            import string
            allowed_chars = string.ascii_letters + string.digits + ' .,!?-_'
            hide_message = ''.join(c for c in hide_message if c in allowed_chars)
        
        # Convert image to ASCII
        converter = ASCIIConverter(style, width)
        ascii_art = converter.image_to_ascii(filepath, invert, hifi, color, color_style)
        
        # Create plain text version by stripping colors from the SAME ascii_art
        # This ensures identical character mapping between display and copy versions
        plain_text_ascii = clean_ascii_for_external(ascii_art)
        
        # Convert ANSI codes to HTML for web display (after extracting plain text)
        if color:
            ascii_art = convert_ansi_to_html(ascii_art)
        
        # Hide message if provided
        if hide_message:
            ascii_art = SecretCipher.hide_message(ascii_art, hide_message)
            plain_text_ascii = SecretCipher.hide_message(plain_text_ascii, hide_message)
        
        # Clean up uploaded file
        os.remove(filepath)
        
        return jsonify({
            'success': True,
            'ascii_art': ascii_art,
            'plain_text': plain_text_ascii,
            'formatted': {
                'whatsapp': format_for_whatsapp(plain_text_ascii),
                'discord': format_for_discord(plain_text_ascii),
                'print': format_for_print(plain_text_ascii),
                'email': format_for_email(plain_text_ascii)
            },
            'options': {
                'width': width,
                'style': style,
                'invert': invert,
                'hifi': hifi,
                'color': color,
                'color_style': color_style,
                'hide_message': bool(hide_message)
            }
        })
        
    except Exception as e:
        return jsonify({'error': f'Conversion failed: {str(e)}'}), 500

@app.route('/reveal', methods=['POST'])
def reveal_message():
    """Reveal hidden message from ASCII art"""
    try:
        # Validate input
        if not request.json:
            return jsonify({'error': 'Invalid JSON data'}), 400
            
        ascii_lines = request.json.get('ascii_lines', [])
        if not isinstance(ascii_lines, list) or len(ascii_lines) > 1000:
            return jsonify({'error': 'Invalid ASCII data (max 1000 lines)'}), 400
            
        try:
            key = int(request.json.get('key', 5))
            if not 1 <= key <= 25:  # Valid Caesar cipher range
                key = 5
        except (ValueError, TypeError):
            key = 5
        
        if not ascii_lines:
            return jsonify({'error': 'No ASCII art provided'}), 400
        
        # Sanitize ASCII lines (remove any potentially dangerous content)
        sanitized_lines = []
        for line in ascii_lines[:1000]:  # Limit number of lines
            if isinstance(line, str):
                # Keep only printable ASCII characters
                clean_line = ''.join(c for c in line[:500] if ord(c) >= 32 and ord(c) <= 126 or c == '\n')
                sanitized_lines.append(clean_line)
        
        hidden_message = SecretCipher.reveal_message(sanitized_lines, key)
        
        # Sanitize output message
        if hidden_message:
            # Remove any potential XSS characters and limit length
            import html
            clean_message = html.escape(hidden_message[:500])
        else:
            clean_message = 'No hidden message found'
        
        return jsonify({
            'success': True,
            'message': clean_message
        })
        
    except Exception as e:
        # Don't expose internal error details
        return jsonify({'error': 'Message reveal failed'}), 500

@app.route('/styles')
def get_styles():
    """Get available character sets"""
    return jsonify(list(ASCIIConverter.CHAR_SETS.keys()))

if __name__ == '__main__':
    # Get port from environment (for production) or default to 5001 (for local dev)
    port = int(os.environ.get('PORT', 5001))
    host = '0.0.0.0' if 'PORT' in os.environ else '127.0.0.1'
    debug = 'PORT' not in os.environ  # Only debug locally
    
    app.run(debug=debug, host=host, port=port)

# For WSGI servers (production)
application = app