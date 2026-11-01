"""
BaseScreen module for Anubis Axis project.

This module provides the BaseScreen class, which serves as the foundation for all screen
implementations in the Anubis Axis project. It handles common screen functionality including
theme management, UI widget coordination, display operations, and user interaction patterns
for touch-based navigation and exit confirmations.

Author: Seguridad Física
File: screens/base_screen.py
"""
import time
from ui.widgets import WidgetManager
from ui.format_text import FormatText
from ui.color_utils import hex_to_byte_swap_rgb565
from common.constants import GESTURE_RESET, GESTURE_DOUBLE_CLICK, GESTURE_SINGLE_CLICK

class BaseScreen:
    """Base class for all screens in the Anubis Axis project.

    This class provides the foundational structure and common functionality required for all
    screen implementations. It manages theme colors, UI widgets, display operations, and
    standardized user interaction patterns including touch gestures and exit confirmations.

    The class automatically handles theme switching between light and dark modes, manages
    color conversion from hexadecimal to RGB565 format with byte swapping for the display,
    and provides standardized methods for screen clearing and value display.

    Attributes:
        touch: Touchscreen interface instance for handling user input.
        lcd: LCD display instance for rendering content.
        encoder: Encoder interface instance for rotary input handling.
        configuration: Configuration instance containing application settings and theme data.
        screen_touch_mediator: Mediator for coordinating screen and touch interactions.
        format_text (FormatText): Text formatting utility for LCD display operations.
        show_exit (bool): Flag indicating whether exit screen is currently displayed.
        light_theme_colors (dict): RGB565 color values for light theme mode.
        dark_theme_colors (dict): RGB565 color values for dark theme mode.
        theme_colors (dict): Currently active theme color values based on dark_mode setting.
        widget_manager (WidgetManager): Manager for UI widget creation and rendering.
    """

    def __init__(self, lcd, touch, encoder, configuration, screen_touch_mediator):
        """Initialize the BaseScreen instance with hardware interfaces and configuration.

        Sets up the screen with all necessary hardware interfaces, converts theme colors
        from hexadecimal to RGB565 format with byte swapping, and initializes the widget
        manager for UI component handling.

        Args:
            lcd: LCD display driver instance for screen rendering operations.
            touch: Touch interface for capturing user input gestures and coordinates.
            encoder: Rotary encoder interface for handling rotational input.
            configuration: Configuration object containing app settings and color themes.
            screen_touch_mediator: Mediator pattern implementation for screen/touch coordination.
        """
        self.touch = touch
        self.lcd = lcd
        self.encoder = encoder
        self.configuration = configuration
        self.screen_touch_mediator = screen_touch_mediator
        self.format_text = FormatText(lcd)
        self.show_exit = False

        # Convert theme colors from hexadecimal to RGB565 format with byte swapping for display
        self.light_theme_colors = {
            k: hex_to_byte_swap_rgb565(v)
            for k, v in self.configuration.colors.get('light_theme', {}).items()
        }
        self.dark_theme_colors = {
            k: hex_to_byte_swap_rgb565(v)
            for k, v in self.configuration.colors.get('dark_theme', {}).items()
        }

        # Initialize active theme colors dictionary
        self.theme_colors = {}

        # Create widget manager with initial configuration
        self.widget_manager = WidgetManager(
            self.lcd,
            configuration,
            self.theme_colors  # Pass empty color dictionary initially
        )

        # Update theme colors based on current mode
        self.update_theme_colors()

    def update_theme_colors(self):
        """Update active theme colors based on current dark/light mode setting.

        Selects the appropriate color scheme based on the configuration's dark_mode setting,
        updates the internal theme_colors dictionary, and recreates the WidgetManager with
        the new color scheme to ensure all UI components reflect the current theme.
        """
        # Select current theme based on dark mode setting
        current_theme = self.dark_theme_colors if self.configuration.dark_mode else self.light_theme_colors

        # Update active theme colors
        self.theme_colors = current_theme.copy()

        # Recreate WidgetManager with updated colors for consistent theming
        self.widget_manager = WidgetManager(
            self.lcd,
            self.configuration,
            self.theme_colors
        )

    def show(self):
        """Display the screen content.

        This method must be implemented by derived classes to define the specific
        content and layout for each screen type. It serves as the main entry point
        for rendering screen-specific UI elements.

        Raises:
            NotImplementedError: If called directly on BaseScreen without implementation.
        """
        pass

    def display_adjusted_value_on_LCD(self, integer_and_fraction_part):
        """Display numeric value with integer and fractional parts on LCD.

        Parses a space-separated string containing integer and fractional parts of a value
        and displays them with appropriate positioning and sizing on the LCD. If no space
        is found, treats the entire string as a single integer value.

        Args:
            integer_and_fraction_part (str): Value string containing integer and fractional
                parts separated by a space, or a single integer value.

        Examples:
            >>> base_screen.display_adjusted_value_on_LCD("123 45")  # Shows "123" and "45"
            >>> base_screen.display_adjusted_value_on_LCD("789")     # Shows "789" centered
        """
        # Parse value into integer and fractional components if space-separated
        if integer_and_fraction_part and " " in integer_and_fraction_part:
            integer_part, fraction_part = integer_and_fraction_part.split(" ")
            # Display integer part with larger font at top position
            self.format_text.center_or_position_text(integer_part, 5, self.theme_colors['text_title'], center_x=True, center_y=False, y=45)
            # Display fractional part with medium font at center position
            self.format_text.center_or_position_text(fraction_part, 6, self.theme_colors['text_title'], center_x=True, center_y=True)
        else:
            # Display single value with large font at center position
            integer_part = integer_and_fraction_part
            self.format_text.center_or_position_text(integer_part, 7, self.theme_colors['text_title'], center_x=True, center_y=True)

    def clear(self, color=None):
        """Clear the screen with specified color or default background color.

        Fills the entire LCD display with the provided color and updates the display.
        If no color is specified, uses the current theme's background color.

        Args:
            color (int, optional): RGB565 color value for screen fill. Defaults to
                current theme background color if None.

        Examples:
            >>> base_screen.clear()                           # Clear with theme background
            >>> base_screen.clear(0xFFFF)                     # Clear with white
            >>> base_screen.clear(self.theme_colors['primary']) # Clear with theme primary color
        """
        fill_color = color if color is not None else self.theme_colors['background']
        self.lcd.fill(fill_color)
        self.lcd.show()

    def exit_screen(self, show_message=True, cancel_color=None, accept_color=None, exit_message="EXIT"):
        """Display confirmation dialog with cancel and accept buttons at screen bottom.

        Creates a standardized exit confirmation interface with two large circular buttons:
        a cancel button on the left and an accept button on the right. Handles touch input
        to determine user choice and manages resource cleanup and navigation upon confirmation.

        Args:
            show_message (bool): Whether to display exit message above buttons. Defaults to True.
            cancel_color (int, optional): Custom color for cancel button. Defaults to theme shadow_2.
            accept_color (int, optional): Custom color for accept button. Defaults to theme primary.
            exit_message (str): Text message to display above buttons. Defaults to "EXIT".

        Returns:
            bool: True if user confirmed exit (accept button), False if user cancelled.

        Examples:
            >>> should_exit = self.exit_screen()
            >>> if should_exit:
            >>>     return  # Exit current screen
            >>> should_exit = self.exit_screen(exit_message="SAVE CHANGES?")
        """
        # Apply default theme colors if not specified
        cancel_button_color = cancel_color if cancel_color is not None else self.theme_colors['shadow_2']
        accept_button_color = accept_color if accept_color is not None else self.theme_colors['primary']

        # Define button positions for bottom-centered layout
        cancel_x = 75   # Left button center X coordinate
        accept_x = 165  # Right button center X coordinate
        buttons_y = 180  # Y coordinate for both buttons

        # Clear screen and display confirmation message
        self.lcd.fill(self.theme_colors['background'])
        if show_message:
            self.format_text.center_or_position_text(
                exit_message,
                3,
                self.theme_colors['text_title'],
                center_x=True,
                center_y=False,
                y=100
            )

        # Render cancel button (left) with X icon
        cancel_pos = self.widget_manager.draw_circle_button(
            cancel_x,
            buttons_y,
            "cancel_30",      # X/cancel icon
            cancel_button_color,
            self.theme_colors['background'],
            "large",          # 60px diameter
            icon_offset_x=-4
        )

        # Render accept button (right) with checkmark icon
        accept_pos = self.widget_manager.draw_circle_button(
            accept_x,
            buttons_y,
            "check_30",       # Check/confirm icon
            accept_button_color,
            self.theme_colors['background'],
            "large",          # 60px diameter
            icon_offset_x=-6,
            icon_offset_y=-4
        )

        # Handle user input until button selection
        while True:
            self.lcd.show()

            # Process single click gestures for button selection
            if self.touch.Gestures == GESTURE_SINGLE_CLICK:
                # Check if touch is in left half (cancel zone)
                if 0 <= self.touch.X_point <= 120 and 120 <= self.touch.Y_point <= 240:
                    self.show_exit = False
                    print("Cancel selected")
                    self.touch.Gestures = GESTURE_RESET
                    time.sleep_ms(10)
                    return False  # User cancelled

                # Check if touch is in right half (accept zone)
                elif 120 <= self.touch.X_point <= 240 and 120 <= self.touch.Y_point <= 240:
                    self.show_exit = False
                    self.touch.Gestures = GESTURE_RESET
                    print("Accept selected - returning to main menu")

                    # Perform cleanup and navigation
                    self._cleanup_resources()
                    self._navigate_to_main_menu()

                    return True  # User confirmed exit

            time.sleep_ms(10)

    def _cleanup_resources(self):
        """Clean up resources before exiting the screen.

        Handles cleanup of any open resources such as USB connections, file handles,
        or other system resources. Derived classes should override this method to
        add their own specific cleanup logic while calling the parent implementation.

        This method is called automatically by exit_screen() when user confirms exit.
        """
        # Generic cleanup for common resources
        try:
            # Stop USB manager if present
            if hasattr(self, 'usb_manager') and self.usb_manager:
                self.usb_manager.stop()
                print("USB manager stopped")
        except Exception as e:
            print(f"Error during resource cleanup: {e}")

    def _navigate_to_main_menu(self):
        """Navigate back to the main menu screen.

        Handles navigation logic to return to the main menu level using the screen
        touch mediator. Clears the current display and resets the screen manager
        to the main level. Derived classes can override this method to customize
        navigation behavior or redirect to different destinations.
        """
        # Navigate using screen touch mediator if available
        if hasattr(self, 'screen_touch_mediator') and self.screen_touch_mediator:
            if hasattr(self.screen_touch_mediator, 'screen_manager'):
                # Clear display before navigation
                self.lcd.fill(self.theme_colors['background'])
                self.lcd.show()

                # Reset screen manager to main level
                self.screen_touch_mediator.screen_manager.current_level = 'main'
                self.screen_touch_mediator.screen_manager.current_screen = 0  # Reset to first item

                # Update screen hierarchy references
                self.screen_touch_mediator.screen_manager.screen_hierarchy['main']['current_index'] = 0

                print("Navigating to main menu")