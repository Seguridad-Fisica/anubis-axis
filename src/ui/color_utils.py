"""
Color utilities module for Anubis Axis project.

This module provides utility functions for color conversion and manipulation
in different formats used by the 1.28" 240x240 GC9A01A LCD display on
Raspberry Pi Pico 2. It handles RGB888 to RGB565 conversion and byte swapping
operations required for proper color rendering on the target hardware.

Author: Seguridad Física
File: ui/color_utils.py
"""

def rgb888_to_rgb565(r: int, g: int, b: int) -> int:
    """Convert 8-bit RGB values to RGB565 format.

    Converts standard 24-bit RGB color values to the 16-bit RGB565 format
    used by the GC9A01A LCD driver. This compression reduces memory usage
    while maintaining acceptable color accuracy for the display.

    The conversion uses proportional scaling:
    - Red: 8-bit (0-255) to 5-bit (0-31)
    - Green: 8-bit (0-255) to 6-bit (0-63)
    - Blue: 8-bit (0-255) to 5-bit (0-31)

    Args:
        r (int): Red component value (0-255).
        g (int): Green component value (0-255).
        b (int): Blue component value (0-255).

    Returns:
        int: Color value in RGB565 format (16-bit integer).

    Examples:
        >>> rgb888_to_rgb565(255, 0, 0)    # Pure red
        63488
        >>> rgb888_to_rgb565(0, 255, 0)    # Pure green
        2016
        >>> rgb888_to_rgb565(255, 255, 255) # White
        65535
    """
    # Scale 8-bit values to their respective bit depths
    r5 = (r * 31) // 255  # Red: 5 bits (0-31)
    g6 = (g * 63) // 255  # Green: 6 bits (0-63)
    b5 = (b * 31) // 255  # Blue: 5 bits (0-31)

    # Pack components into 16-bit RGB565 format: RRRRRGGGGGGBBBBB
    return (r5 << 11) | (g6 << 5) | b5

def byte_swap(value: int) -> int:
    """Perform byte swapping for a 16-bit value.

    Swaps the high and low bytes of a 16-bit integer to match the
    endianness requirements of the GC9A01A LCD driver. This is necessary
    because the display expects data in big-endian format while the
    Raspberry Pi Pico 2 operates in little-endian format.

    Args:
        value (int): 16-bit value to byte swap.

    Returns:
        int: Value with high and low bytes swapped.

    Examples:
        >>> byte_swap(0x1234)  # Returns 0x3412
        13330
        >>> byte_swap(0xFF00)  # Returns 0x00FF
        255
    """
    # Extract low byte and shift to high position, extract high byte and shift to low
    return ((value & 0xFF) << 8) | ((value >> 8) & 0xFF)

def hex_to_byte_swap_rgb565(hex_color: str) -> int:
    """Convert hexadecimal color string to byte-swapped RGB565 format.

    Converts a standard web-format hexadecimal color string (#RRGGBB) to
    the RGB565 format with byte swapping applied for direct use with the
    GC9A01A LCD driver. This is the primary color conversion function used
    throughout the Anubis Axis project for theme color processing.

    Args:
        hex_color (str): Hexadecimal color string in format "#RRGGBB" or "RRGGBB".

    Returns:
        int: RGB565 color value with bytes swapped for LCD compatibility.

    Examples:
        >>> hex_to_byte_swap_rgb565("#FF0000")  # Red
        248
        >>> hex_to_byte_swap_rgb565("#00FF00")  # Green
        57568
        >>> hex_to_byte_swap_rgb565("#FFFFFF")  # White
        65535

    Raises:
        ValueError: If hex_color is not a valid 6-character hexadecimal string.
    """
    # Remove leading '#' if present for consistent processing
    hex_color = hex_color.lstrip('#')

    # Extract RGB components from hex string
    r = int(hex_color[0:2], 16)  # Red component
    g = int(hex_color[2:4], 16)  # Green component
    b = int(hex_color[4:6], 16)  # Blue component

    # Convert to RGB565 and apply byte swapping for LCD compatibility
    rgb565 = rgb888_to_rgb565(r, g, b)
    return byte_swap(rgb565)