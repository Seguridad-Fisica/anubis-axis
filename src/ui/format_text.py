"""
FormatText module for Anubis Axis project.

This module provides the FormatText class for handling text formatting and positioning
on the 1.28" 240x240 LCD display with GC9A01A driver. It includes optimized text
rendering with position caching for improved performance on the Raspberry Pi Pico 2.
The module supports variable font sizes, centering operations, and memory-efficient
caching for frequent text updates.

Author: Seguridad Física
File: ui/format_text.py
"""

class FormatText:
    """Handles text formatting and positioning on LCD displays for Anubis Axis project.

    This class provides methods to center or position text with variable font sizes
    on the 240x240 circular LCD display. It includes position caching functionality
    to optimize performance during frequent text updates, which is crucial for
    MicroPython applications on Raspberry Pi Pico 2.

    The class handles automatic boundary checking to prevent text overflow and
    provides both immediate and cached rendering methods for different use cases.

    Attributes:
        lcd: LCD display driver instance for text rendering operations.
        width (int): Display width in pixels, typically 240 for the target hardware.
        height (int): Display height in pixels, typically 240 for the target hardware.
        _position_cache (dict): Internal cache for storing calculated text positions
            to avoid recalculation on subsequent renders.
    """

    def __init__(self, lcd, width=240, height=240):
        """Initialize the FormatText with LCD display and dimensions.

        Sets up the text formatter with the LCD driver and display dimensions.
        Initializes the position cache for optimized text rendering performance.

        Args:
            lcd: LCD display driver instance with write_text and write_text_cached methods.
            width (int): Display width in pixels. Defaults to 240 for GC9A01A driver.
            height (int): Display height in pixels. Defaults to 240 for GC9A01A driver.

        Examples:
            >>> lcd_driver = GC9A01A()  # Initialize LCD driver
            >>> format_text = FormatText(lcd_driver)
            >>> format_text = FormatText(lcd_driver, width=320, height=240)  # Custom dimensions
        """
        self.lcd = lcd
        self.width = width
        self.height = height
        # Initialize position cache for performance optimization
        self._position_cache = {}

    def center_or_position_text(self, text, size, color, center_x=False, center_y=False, x=None, y=None):
        """Center or position text on the display with variable font size.

        Calculates text position based on centering flags or provided coordinates
        and renders it immediately. Includes automatic boundary checking to prevent
        text overflow beyond display dimensions.

        Args:
            text (str): The string of characters to display.
            size (int): Font size multiplier, where base character is 8x8 pixels.
            color (int): RGB565 color value for text rendering.
            center_x (bool): If True, centers text horizontally. Defaults to False.
            center_y (bool): If True, centers text vertically. Defaults to False.
            x (int, optional): X-coordinate for text start position when center_x is False.
            y (int, optional): Y-coordinate for text start position when center_y is False.

        Examples:
            >>> # Center text on display
            >>> format_text.center_or_position_text("Hello", 2, 0xFFFF, center_x=True, center_y=True)
            >>> # Position text at specific coordinates
            >>> format_text.center_or_position_text("Status", 1, 0x07E0, x=10, y=220)
        """
        # Handle special "None" text case with error color indication
        if text == "None":
            color = self.lcd.red

        # Calculate text dimensions based on 8x8 pixel base font
        text_width = 8 * size * len(text)
        text_height = 8 * size

        # Calculate horizontal position
        if center_x:
            x = (self.width - text_width) // 2
        elif x is None:
            x = 0  # Default to left edge if no position specified

        # Calculate vertical position
        if center_y:
            y = (self.height - text_height) // 2
        elif y is None:
            y = 0  # Default to top edge if no position specified

        # Apply boundary constraints to prevent text overflow
        x = max(0, min(x, self.width - text_width))
        y = max(0, min(y, self.height - text_height))

        # Render text at calculated position
        self.lcd.write_text(text, x, y, size, color)

    def center_or_position_text_cached(self, text, size, color, center_x=False, center_y=False, x=None, y=None):
        """Center or position text using cached positions for improved performance.

        Similar to center_or_position_text but caches position calculations to avoid
        redundant computation during frequent updates. Ideal for dynamic content
        like sensor readings or status updates that refresh regularly.

        Args:
            text (str): The string of characters to display.
            size (int): Font size multiplier, where base character is 8x8 pixels.
            color (int): RGB565 color value for text rendering.
            center_x (bool): If True, centers text horizontally. Defaults to False.
            center_y (bool): If True, centers text vertically. Defaults to False.
            x (int, optional): X-coordinate for text start position when center_x is False.
            y (int, optional): Y-coordinate for text start position when center_y is False.

        Examples:
            >>> # Cached rendering for frequently updated values
            >>> format_text.center_or_position_text_cached("42.5", 3, 0xFFFF, center_x=True, center_y=True)
            >>> # Cached positioning for status indicators
            >>> format_text.center_or_position_text_cached("READY", 1, 0x07E0, x=10, y=10)
        """
        # Create unique cache key including all positioning parameters
        cache_key = (text, size, center_x, center_y, x, y, self.width, self.height)

        # Use cached position if available to avoid recalculation
        if cache_key in self._position_cache:
            final_x, final_y = self._position_cache[cache_key]
        else:
            # Handle special "None" text case with error color indication
            if text == "None":
                color = self.lcd.red

            # Calculate text dimensions based on 8x8 pixel base font
            text_width = 8 * size * len(text)
            text_height = 8 * size

            # Calculate horizontal position
            if center_x:
                calculated_x = (self.width - text_width) // 2
            elif x is None:
                calculated_x = 0  # Default to left edge
            else:
                calculated_x = x

            # Calculate vertical position
            if center_y:
                calculated_y = (self.height - text_height) // 2
            elif y is None:
                calculated_y = 0  # Default to top edge
            else:
                calculated_y = y

            # Apply boundary constraints to prevent overflow
            final_x = max(0, min(calculated_x, self.width - text_width))
            final_y = max(0, min(calculated_y, self.height - text_height))

            # Cache calculated position for future use
            self._position_cache[cache_key] = (final_x, final_y)

        # Render text using cached rendering method for better performance
        self.lcd.write_text_cached(text, final_x, final_y, size, color)

    def clear_cache(self):
        """Clear the position cache to free memory.

        Removes all cached position calculations and optionally clears LCD text cache.
        Should be called when transitioning between screens or when memory optimization
        is needed. Essential for long-running applications on memory-constrained hardware.

        Examples:
            >>> # Clear cache when changing screens
            >>> format_text.clear_cache()
            >>> # Memory cleanup during screen transitions
            >>> old_screen.format_text.clear_cache()
        """
        self._position_cache = {}
        # Clear LCD driver's text cache if available for complete cleanup
        if hasattr(self.lcd, 'clear_text_cache'):
            self.lcd.clear_text_cache()