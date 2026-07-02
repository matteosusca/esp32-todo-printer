"""ESC/POS commands and formatting utilities for thermal printers.

This module provides standard byte sequences and formatting functions for
controlling ESC/POS thermal printers (like the QR203 58mm printer).
"""

# ==============================================================================
# ESC/POS Constants
# ==============================================================================

# Initialization (ESC @ + ESC t 0 + ESC ! 0 + ESC 7 n1 n2 n3)
# Set CP437 code page, reset modes, and set heating parameters (max 64 dots, 800us heat time, 400us heat interval)
# The heating interval (40 * 10us = 400us) prevents thermal accumulation on long text jobs.
INIT = b'\x1b\x40\x1b\x74\x00\x1b\x21\x00\x1b\x37\x07\x50\x28'

# Code Page Selection Commands (ESC t n)
CODEPAGE_CP437 = b'\x1b\x74\x00'    # ESC t 0 - Code Page 437 (USA/Standard Europe)
CODEPAGE_CP850 = b'\x1b\x74\x02'    # ESC t 2 - Code Page 850 (Multilingual)
CODEPAGE_WPC1252 = b'\x1b\x74\x10'  # ESC t 16 - WPC1252 (Western Europe)

# Basic Feed Control
LF = b'\x0a'                 # LF - Print and line feed
CR = b'\x0d'                 # CR - Carriage return
FF = b'\x0c'                 # FF - Print and return to standard mode (page feed)

# Alignment (ESC a n)
ALIGN_LEFT = b'\x1b\x61\x00'    # Left justification
ALIGN_CENTER = b'\x1b\x61\x01'  # Centered
ALIGN_RIGHT = b'\x1b\x61\x02'   # Right justification

# Bold Font (ESC E n)
BOLD_ON = b'\x1b\x45\x01'       # Turn on bold
BOLD_OFF = b'\x1b\x45\x00'      # Turn off bold

# Double Strike (ESC G n)
DOUBLE_STRIKE_ON = b'\x1b\x47\x01'   # Turn on double-strike
DOUBLE_STRIKE_OFF = b'\x1b\x47\x00'  # Turn off double-strike

# Master Mode Reset (ESC ! n)
RESET_MODE = b'\x1b\x21\x00'          # Reset all print modes (normal font, no bold/size/underline)

# Underline (ESC - n)
UNDERLINE_OFF = b'\x1b\x2d\x00'     # Underline off
UNDERLINE_ON_1DOT = b'\x1b\x2d\x01' # Underline on (1-dot thickness)
UNDERLINE_ON_2DOT = b'\x1b\x2d\x02' # Underline on (2-dot thickness)

# Font Selection (ESC M n)
FONT_A = b'\x1b\x4d\x00'        # Font A (typically 12x24)
FONT_B = b'\x1b\x4d\x01'        # Font B (typically 9x17)

# Color Inversion / White-on-Black (GS B n)
REVERSE_ON = b'\x1d\x42\x01'    # Reverse video print mode on
REVERSE_OFF = b'\x1d\x42\x00'   # Reverse video print mode off

# Line Spacing
LINE_SPACING_DEFAULT = b'\x1b\x32'  # ESC 2 - Default line spacing (1/6 inch)

# Code Page 437 / 850 Character Mapping Table for Western European Accented Characters
CP437_MAP = {
    'ç': 0x87, 'ü': 0x81, 'é': 0x82, 'â': 0x83, 'ä': 0x84, 'à': 0x85, 'å': 0x86,
    'ê': 0x88, 'ë': 0x89, 'è': 0x8a, 'ï': 0x8b, 'î': 0x8c, 'ì': 0x8d, 'Ä': 0x8e,
    'Å': 0x8f, 'É': 0x90, 'æ': 0x91, 'Æ': 0x92, 'ô': 0x93, 'ö': 0x94, 'ò': 0x95,
    'û': 0x96, 'ù': 0x97, 'ÿ': 0x98, 'Ö': 0x99, 'Ü': 0x9a, '°': 0xf8, '€': 0xd5,
    'À': 0x85, 'È': 0x8a, 'Ì': 0x8d, 'Ò': 0x95, 'Ù': 0x97
}

# ==============================================================================
# Helper Functions
# ==============================================================================

def text(string, encoding="cp437"):
    """Convert a text string to printable ESC/POS bytes.

    Translates extended UTF-8 characters (like è, é, à, ò, ù) to the printer's
    Code Page 437 byte values for accurate physical printing.

    Args:
        string (str): The text content to encode.
        encoding (str): Encoding to use ('cp437', 'cp850', or 'utf-8').

    Returns:
        bytes: Raw byte string representation.
    """
    if encoding.lower() in ("cp437", "cp850", "auto"):
        res = bytearray()
        for char in string:
            if char in CP437_MAP:
                res.append(CP437_MAP[char])
            else:
                try:
                    res.extend(char.encode("ascii"))
                except UnicodeError:
                    res.extend(char.encode("utf-8"))
        return bytes(res)
    else:
        try:
            return string.encode(encoding)
        except (LookupError, UnicodeError):
            return string.encode("utf-8")


def feed(lines=1):
    """Generate command bytes to feed paper by a given number of lines.

    Args:
        lines (int): Number of lines to feed.

    Returns:
        bytes: ESC/POS feed bytes.
    """
    if lines <= 0:
        return b''
    
    result = bytearray()
    while lines > 0:
        chunk = min(lines, 255)
        # ESC d n: Print and feed n lines
        result.extend(b'\x1b\x64' + bytes([chunk]))
        lines -= chunk
    return bytes(result)


def align(alignment="left"):
    """Generate alignment command bytes.

    Args:
        alignment (str): 'left', 'center', or 'right'.

    Returns:
        bytes: ESC/POS justification command.

    Raises:
        ValueError: If alignment parameter is invalid.
    """
    alignment = alignment.lower()
    if alignment == "left":
        return ALIGN_LEFT
    elif alignment == "center":
        return ALIGN_CENTER
    elif alignment == "right":
        return ALIGN_RIGHT
    else:
        raise ValueError("Alignment must be 'left', 'center', or 'right'")


def bold(enable=True):
    """Generate command bytes to enable or disable bold text.

    Args:
        enable (bool): True to enable bold, False to disable.

    Returns:
        bytes: ESC/POS bold command.
    """
    return BOLD_ON if enable else BOLD_OFF


def underline(enable=True, thickness=1):
    """Generate command bytes to enable or disable underline.

    Args:
        enable (bool): True to enable underline, False to disable.
        thickness (int): Underline thickness: 1 (single-dot) or 2 (double-dot).

    Returns:
        bytes: ESC/POS underline command.

    Raises:
        ValueError: If thickness is not 1 or 2.
    """
    if not enable:
        return UNDERLINE_OFF
    
    if thickness == 1:
        return UNDERLINE_ON_1DOT
    elif thickness == 2:
        return UNDERLINE_ON_2DOT
    else:
        raise ValueError("Underline thickness must be 1 or 2")


def font(font_type="A"):
    """Generate command bytes to select font A or font B.

    Args:
        font_type (str): 'A' or 'B'.

    Returns:
        bytes: ESC/POS font selection command.

    Raises:
        ValueError: If font_type is not 'A' or 'B'.
    """
    font_type = font_type.upper()
    if font_type == "A":
        return FONT_A
    elif font_type == "B":
        return FONT_B
    else:
        raise ValueError("Font type must be 'A' or 'B'")


def font_size(width=1, height=1):
    """Generate command bytes to set character width and height magnification.

    Args:
        width (int): Width magnification factor (1 to 8).
        height (int): Height magnification factor (1 to 8).

    Returns:
        bytes: ESC/POS GS ! command.

    Raises:
        ValueError: If magnification factors are outside the 1 to 8 range.
    """
    if not (1 <= width <= 8) or not (1 <= height <= 8):
        raise ValueError("Font size magnification must be between 1 and 8")
    
    # GS ! n (Select character size)
    # Bits 0-3 select height magnification, bits 4-7 select width magnification
    n = ((width - 1) & 0x07) << 4 | ((height - 1) & 0x07)
    return b'\x1d\x21' + bytes([n])


def reverse_colors(enable=True):
    """Generate command bytes to enable or disable reverse color printing.

    Args:
        enable (bool): True for white-on-black printing, False for normal.

    Returns:
        bytes: ESC/POS reverse printing command.
    """
    return REVERSE_ON if enable else REVERSE_OFF


def line_spacing(dots=None):
    """Generate command bytes to set line spacing in dots (0 to 255).

    Args:
        dots (int, optional): Number of dots for spacing. If None, resets to default.

    Returns:
        bytes: ESC/POS line spacing command.

    Raises:
        ValueError: If dots is outside the 0 to 255 range.
    """
    if dots is None:
        return LINE_SPACING_DEFAULT
    
    if not (0 <= dots <= 255):
        raise ValueError("Line spacing dots must be between 0 and 255")
    
    # ESC 3 n - Set line spacing to n dots
    return b'\x1b\x33' + bytes([dots])


def cut(feed_lines=3):
    """Generate command bytes to perform paper cutting (if supported).

    Args:
        feed_lines (int): Number of lines to feed before cutting.

    Returns:
        bytes: ESC/POS partial cut command.
    """
    # GS V m n
    # m = 66 (Feed paper to cutting position and partial cut)
    # n = feed_lines
    return b'\x1d\x56\x42' + bytes([feed_lines])


def set_heat_params(max_dots=7, heating_time=80, heating_interval=40):
    """Generate command bytes to configure thermal printhead heating parameters (ESC 7).

    Adjusting these parameters prevents thermal saturation (where continuous lines
    become progressively darker/bolder/blacker due to heat accumulation in the printhead).

    Args:
        max_dots (int): Max heating dots (0-255, 7 = 64 dots).
        heating_time (int): Heating time per dot in 10us units (3-255, e.g., 80 = 800us).
        heating_interval (int): Cooling interval between dots in 10us units (0-255, e.g., 40 = 400us).

    Returns:
        bytes: ESC 7 command bytes.
    """
    return b'\x1b\x37' + bytes([max_dots & 0xFF, heating_time & 0xFF, heating_interval & 0xFF])


def set_density(density=15, break_time=4):
    """Generate command bytes to set print density and heating break time (DC2 # n).

    Args:
        density (int): Print density level 0 to 31 (default 15).
        break_time (int): Heating break time level 0 to 7 (default 4).

    Returns:
        bytes: DC2 # command bytes.
    """
    n = (break_time & 0x07) << 5 | (density & 0x1F)
    return b'\x12\x23' + bytes([n])


def double_strike(enable=True):
    """Generate command bytes to enable or disable double-strike mode.

    Args:
        enable (bool): True to enable double-strike, False to disable.

    Returns:
        bytes: ESC G command bytes.
    """
    return DOUBLE_STRIKE_ON if enable else DOUBLE_STRIKE_OFF


def reset_mode():
    """Generate command bytes to reset all character print modes to defaults (ESC ! 0).

    Returns:
        bytes: ESC ! 0 command bytes.
    """
    return RESET_MODE



# ==============================================================================
# Raster Image/Graphics Utilities (Streaming Friendly)
# ==============================================================================

def pack_pixel_row(pixels):
    """Pack an iterable of pixel values into bytes for standard thermal printing.

    Each pixel should be truthy (1/True = black/burn) or falsy (0/False = white/blank).
    Bits are packed MSB-first (most significant bit is leftmost pixel).

    Args:
        pixels (iterable): A sequence of boolean or 0/1 pixel values.

    Returns:
        bytes: The packed byte sequence.
    """
    row_bytes = bytearray()
    current_byte = 0
    for i, pixel in enumerate(pixels):
        if pixel:
            current_byte |= (1 << (7 - (i % 8)))
        if (i + 1) % 8 == 0:
            row_bytes.append(current_byte)
            current_byte = 0
            
    # Append the last partial byte if the total number of pixels was not a multiple of 8
    if len(pixels) % 8 != 0:
        row_bytes.append(current_byte)
        
    return bytes(row_bytes)


def raster_image_row(row_bytes, width_bytes=48):
    """Wrap raw packed pixel bytes in an ESC/POS GS v 0 command for a single row.

    This enables streaming images line-by-line using a generator (RNF4 constraint),
    minimizing RAM overhead.

    Args:
        row_bytes (bytes): Pre-packed bytes of the image row.
        width_bytes (int): Standard target width of the printer in bytes.
                           For 58mm printer (384 dots width), this is 48 bytes.

    Returns:
        bytes: The raw GS v 0 printer command package for this row.
    """
    # Align row_bytes length to width_bytes
    if len(row_bytes) < width_bytes:
        row_bytes = row_bytes + b'\x00' * (width_bytes - len(row_bytes))
    elif len(row_bytes) > width_bytes:
        row_bytes = row_bytes[:width_bytes]
        
    xL = width_bytes & 0xFF
    xH = (width_bytes >> 8) & 0xFF
    
    # GS v 0 m xL xH yL yH d1...dk
    # m = 0 (Normal mode), yL = 1, yH = 0 (Height is exactly 1 dot row)
    return b'\x1d\x76\x30\x00' + bytes([xL, xH, 1, 0]) + row_bytes
