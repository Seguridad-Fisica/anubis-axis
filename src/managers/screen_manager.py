"""
Screen Manager module for Anubis Axis project.

This module provides the ScreenManager class that orchestrates the display and navigation
of different screen states in the Anubis Axis measurement and calibration system. It implements
a hierarchical navigation system for managing multiple screen types including basic meters,
advanced multi-wheel meters, and USB measurement interfaces on the Raspberry Pi Pico 2
with GC9A01A LCD display.

The ScreenManager handles screen transitions, brightness control, and provides a unified
interface for navigating between different measurement modes and their respective sub-screens.
It supports touchscreen interaction through the CST816T driver and encoder input for
precise navigation control.

Author: Seguridad Física
File: managers/screen_manager.py
"""

# Basic Meter screen imports
from screens.basic_meter.basic_meter import BasicMeter
from screens.basic_meter.raw_screen import RawScreen as BasicRawScreen
from screens.basic_meter.quarter_screen import QuarterScreen as BasicQuarterScreen
from screens.basic_meter.eighth_screen import EighthScreen as BasicEighthScreen
from screens.basic_meter.tenth_screen import TenthScreen as BasicTenthScreen
from screens.basic_meter.twentieth_screen import TwentiethScreen as BasicTwentiethScreen

# Advanced Three Wheel Meter screen imports
from screens.advanced_three_wheels_meter.advanced_three_wheel_meter import AdvancedThreeWheelMeter
from screens.advanced_three_wheels_meter.raw_screen import RawScreen as ThreeWheelRawScreen
from screens.advanced_three_wheels_meter.quarter_screen import QuarterScreen as ThreeWheelQuarterScreen
from screens.advanced_three_wheels_meter.eighth_screen import EighthScreen as ThreeWheelEighthScreen
from screens.advanced_three_wheels_meter.tenth_screen import TenthScreen as ThreeWheelTenthScreen
from screens.advanced_three_wheels_meter.twentieth_screen import TwentiethScreen as ThreeWheelTwentiethScreen

# Advanced Four Wheel Meter screen imports
from screens.advanced_four_wheels_meter.advanced_four_wheel_meter import AdvancedFourWheelMeter
from screens.advanced_four_wheels_meter.raw_screen import RawScreen as FourWheelRawScreen
from screens.advanced_four_wheels_meter.quarter_screen import QuarterScreen as FourWheelQuarterScreen
from screens.advanced_four_wheels_meter.eighth_screen import EighthScreen as FourWheelEighthScreen
from screens.advanced_four_wheels_meter.tenth_screen import TenthScreen as FourWheelTenthScreen
from screens.advanced_four_wheels_meter.twentieth_screen import TwentiethScreen as FourWheelTwentiethScreen

# USB Meter screen imports
from screens.usb_meter.usb_meter import USBMeter
from screens.usb_meter.usb_screen import USBScreen

from ui.logger import Logger

class ScreenManager:
    """Hierarchical screen navigation and display control interface for the Anubis Axis system.

    This class provides a comprehensive screen management system that handles multiple
    screen types organized in a hierarchical structure. It manages navigation between
    main screens (basic meter, advanced meters, USB meter) and their respective
    sub-screens, while providing brightness control and touch/encoder interaction
    coordination through a mediator pattern.

    The manager implements a state-based navigation system where screens are organized
    into levels (main, submenus) allowing for intuitive navigation patterns. It also
    handles LCD brightness control with predefined levels optimized for the GC9A01A
    display driver on the 1.28-inch 240x240 LCD panel.

    Attributes:
        MAX_BRIGHTNESS (int): Maximum brightness level using 16-bit PWM value (65535)
            for optimal visibility under bright conditions.
        MIN_BRIGHTNESS (int): Minimum brightness level (3000) to prevent screen
            from turning completely off while maintaining visibility.
        BRIGHTNESS_STEP (int): Brightness increment step size calculated to provide
            10 distinct brightness levels between minimum and maximum values.
        lcd: LCD display instance for rendering screen content using GC9A01A driver.
        touch: Touchscreen instance for handling user interactions via CST816T driver.
        encoder: 12-bit absolute encoder instance for navigation and value adjustment.
        configuration: Application configuration instance containing user settings.
        logger (Logger): Logging instance for system event tracking and debugging.
        screen_touch_mediator: Optional mediator for coordinating screen and touch events.
        brightness (int): Current brightness level stored in configuration.
        screen_hierarchy (dict): Hierarchical structure containing all screen instances
            organized by navigation levels and their current indices.
        current_level (str): Currently active navigation level identifier.
        screens (list): Reference to main level screens for backward compatibility.
        current_screen (int): Index of currently active main screen.
    """

    # Maximum brightness level, defined by the 16-bit PWM value
    MAX_BRIGHTNESS = 65535

    # Minimum brightness level to prevent the screen from turning off
    MIN_BRIGHTNESS = 3000

    # Defines 10 brightness levels between the minimum and maximum
    BRIGHTNESS_STEP = (MAX_BRIGHTNESS - MIN_BRIGHTNESS) // 10

    def __init__(self, lcd, touch, encoder, configuration, screen_touch_mediator=None):
        """Initialize the ScreenManager with hardware interfaces and configuration.

        Sets up all screen instances for different meter types, initializes the
        hierarchical navigation structure, and configures brightness settings.
        Creates instances of all available screens including basic meters,
        advanced multi-wheel meters, and USB measurement interfaces.

        Args:
            lcd: LCD display instance (GC9A01A driver) for 240x240 pixel rendering.
            touch: Touchscreen instance (CST816T driver) for user interaction.
            encoder: 12-bit absolute encoder instance for precision navigation input.
            configuration: Configuration instance containing persistent user settings
                including brightness, calibration data, and display preferences.
            screen_touch_mediator (optional): Mediator instance for coordinating
                touch events and screen responses. Defaults to None.

        Examples:
            >>> # Initialize with hardware instances
            >>> screen_manager = ScreenManager(lcd, touch, encoder, config)
            >>> screen_manager.run_current_screen()
        """
        # Store hardware and configuration references for screen instantiation
        self.lcd = lcd
        self.touch = touch
        self.encoder = encoder
        self.configuration = configuration
        self.logger = Logger()
        self.screen_touch_mediator = screen_touch_mediator
        self.brightness = configuration.brightness

        # Initialize Basic Meter screen instances with shared hardware references
        self.basic_meter = BasicMeter(self.lcd, self.touch, self.encoder, self.configuration, self.screen_touch_mediator)
        self.basic_raw_screen = BasicRawScreen(self.lcd, self.touch, self.encoder, self.configuration, self.screen_touch_mediator)
        self.basic_quarter_screen = BasicQuarterScreen(self.lcd, self.touch, self.encoder, self.configuration, self.screen_touch_mediator)
        self.basic_eighth_screen = BasicEighthScreen(self.lcd, self.touch, self.encoder, self.configuration, self.screen_touch_mediator)
        self.basic_tenth_screen = BasicTenthScreen(self.lcd, self.touch, self.encoder, self.configuration, self.screen_touch_mediator)
        self.basic_twentieth_screen = BasicTwentiethScreen(self.lcd, self.touch, self.encoder, self.configuration, self.screen_touch_mediator)

        # Initialize Advanced Three Wheel Meter screen instances for multi-axis measurement
        self.advanced_three_wheel_meter = AdvancedThreeWheelMeter(self.lcd, self.touch, self.encoder, self.configuration, self.screen_touch_mediator)
        self.three_wheel_raw_screen = ThreeWheelRawScreen(self.lcd, self.touch, self.encoder, self.configuration, self.screen_touch_mediator)
        self.three_wheel_quarter_screen = ThreeWheelQuarterScreen(self.lcd, self.touch, self.encoder, self.configuration, self.screen_touch_mediator)
        self.three_wheel_eighth_screen = ThreeWheelEighthScreen(self.lcd, self.touch, self.encoder, self.configuration, self.screen_touch_mediator)
        self.three_wheel_tenth_screen = ThreeWheelTenthScreen(self.lcd, self.touch, self.encoder, self.configuration, self.screen_touch_mediator)
        self.three_wheel_twentieth_screen = ThreeWheelTwentiethScreen(self.lcd, self.touch, self.encoder, self.configuration, self.screen_touch_mediator)

        # Initialize Advanced Four Wheel Meter screen instances for four-axis measurement
        self.advanced_four_wheel_meter = AdvancedFourWheelMeter(self.lcd, self.touch, self.encoder, self.configuration, self.screen_touch_mediator)
        self.four_wheel_raw_screen = FourWheelRawScreen(self.lcd, self.touch, self.encoder, self.configuration, self.screen_touch_mediator)
        self.four_wheel_quarter_screen = FourWheelQuarterScreen(self.lcd, self.touch, self.encoder, self.configuration, self.screen_touch_mediator)
        self.four_wheel_eighth_screen = FourWheelEighthScreen(self.lcd, self.touch, self.encoder, self.configuration, self.screen_touch_mediator)
        self.four_wheel_tenth_screen = FourWheelTenthScreen(self.lcd, self.touch, self.encoder, self.configuration, self.screen_touch_mediator)
        self.four_wheel_twentieth_screen = FourWheelTwentiethScreen(self.lcd, self.touch, self.encoder, self.configuration, self.screen_touch_mediator)

        # Initialize USB Meter screen instances for external measurement interface
        self.usb_meter = USBMeter(self.lcd, self.touch, self.encoder, self.configuration, self.screen_touch_mediator)
        self.usb_screen = USBScreen(self.lcd, self.touch, self.encoder, self.configuration, self.screen_touch_mediator)

        # Define hierarchical screen structure with navigation levels
        self.screen_hierarchy = {
            'main': {
                'screens': [
                    self.basic_meter,
                    self.advanced_three_wheel_meter,
                    self.advanced_four_wheel_meter,
                    self.usb_meter  # Add USB Meter to main screen navigation
                ],
                'current_index': 0
            },
            'basic_meter_submenus': {
                'screens': [
                    self.basic_quarter_screen,
                    self.basic_eighth_screen,
                    self.basic_tenth_screen,
                    self.basic_twentieth_screen,
                    self.basic_raw_screen
                ],
                'current_index': 0
            },
            'advanced_three_wheel_meter_submenus': {
                'screens': [
                    self.three_wheel_quarter_screen,
                    self.three_wheel_eighth_screen,
                    self.three_wheel_tenth_screen,
                    self.three_wheel_twentieth_screen,
                    self.three_wheel_raw_screen
                ],
                'current_index': 0
            },
            'advanced_four_wheel_meter_submenus': {
                'screens': [
                    self.four_wheel_quarter_screen,
                    self.four_wheel_eighth_screen,
                    self.four_wheel_tenth_screen,
                    self.four_wheel_twentieth_screen,
                    self.four_wheel_raw_screen
                ],
                'current_index': 0
            },
            'usb_meter_submenus': {  # New submenu for USB meter functionality
                'screens': [
                    self.usb_screen
                ],
                'current_index': 0
            }
        }

        # Set current navigation level to main menu
        self.current_level = 'main'

        # Maintain backward compatibility with existing code
        self.screens = self.screen_hierarchy['main']['screens']
        self.current_screen = 0

    def next_screen(self):
        """Advance to the next screen within the current navigation level.

        Increments the current screen index and wraps around to the first screen
        when reaching the end of the screen list. Updates compatibility properties
        when navigating at the main level.

        Examples:
            >>> screen_manager.next_screen()  # Move to next screen
        """
        current_level_data = self.screen_hierarchy[self.current_level]
        current_level_data['current_index'] += 1

        # Wrap around to first screen when reaching the end
        if current_level_data['current_index'] >= len(current_level_data['screens']):
            current_level_data['current_index'] = 0

        # Update compatibility properties for main level navigation
        if self.current_level == 'main':
            self.current_screen = current_level_data['current_index']

    def previous_screen(self):
        """Move back to the previous screen within the current navigation level.

        Decrements the current screen index and wraps around to the last screen
        when reaching the beginning of the screen list. Updates compatibility
        properties when navigating at the main level.

        Examples:
            >>> screen_manager.previous_screen()  # Move to previous screen
        """
        current_level_data = self.screen_hierarchy[self.current_level]
        current_level_data['current_index'] -= 1

        # Wrap around to last screen when reaching the beginning
        if current_level_data['current_index'] < 0:
            current_level_data['current_index'] = len(current_level_data['screens']) - 1

        # Update compatibility properties for main level navigation
        if self.current_level == 'main':
            self.current_screen = current_level_data['current_index']

    def enter_submenu(self, submenu_id):
        """Enter a specific submenu navigation level.

        Changes the current navigation level to the specified submenu and resets
        the submenu index to the first screen for consistent navigation behavior.

        Args:
            submenu_id (str): Identifier for the submenu level to enter.
                Valid values include 'basic_meter_submenus', 'advanced_three_wheel_meter_submenus',
                'advanced_four_wheel_meter_submenus', and 'usb_meter_submenus'.

        Returns:
            bool: True if submenu exists and navigation was successful, False otherwise.

        Examples:
            >>> if screen_manager.enter_submenu('basic_meter_submenus'):
            >>>     print("Entered basic meter submenu")
        """
        if submenu_id in self.screen_hierarchy:
            self.current_level = submenu_id
            # Reset submenu index to first screen for consistency
            self.screen_hierarchy[submenu_id]['current_index'] = 0
            return True
        return False

    def run_current_screen(self):
        """Execute and display the currently active screen.

        Renders the screen at the current index within the active navigation level.
        Updates compatibility properties and handles error cases where the screen
        index is out of bounds.

        Examples:
            >>> screen_manager.run_current_screen()  # Display current screen
        """
        current_level_data = self.screen_hierarchy[self.current_level]
        current_index = current_level_data['current_index']

        # Validate screen index and display screen
        if 0 <= current_index < len(current_level_data['screens']):
            # Update compatibility property for main level
            if self.current_level == 'main':
                self.current_screen = current_index

            # Render the selected screen
            current_level_data['screens'][current_index].show()
        else:
            self.logger.console_printing("ERROR", "Index out of range. Check screen configuration.")

    def update_ui(self):
        """Update the user interface elements.

        Currently a placeholder method that can be expanded to handle dynamic UI updates
        such as refresh rates, animation states, or real-time data display updates.

        Examples:
            >>> screen_manager.update_ui()  # Refresh UI components
        """
        self.screens[self.current_screen]

    def increase_brightness(self):
        """Increase the LCD screen brightness level.

        Increments the brightness by the predefined step size and applies hardware
        PWM control to the LCD backlight. Ensures brightness does not exceed the
        maximum safe level for the GC9A01A display driver.

        Examples:
            >>> screen_manager.increase_brightness()  # Make screen brighter
        """
        self.brightness += self.BRIGHTNESS_STEP
        # Clamp brightness to maximum safe level
        if self.brightness > self.MAX_BRIGHTNESS:
            self.brightness = self.MAX_BRIGHTNESS
        self.lcd.set_bl_pwm(self.brightness)

    def decrease_brightness(self):
        """Decrease the LCD screen brightness level.

        Decrements the brightness by the predefined step size and applies hardware
        PWM control to the LCD backlight. Ensures brightness does not fall below
        the minimum visible level to maintain screen readability.

        Examples:
            >>> screen_manager.decrease_brightness()  # Make screen dimmer
        """
        self.brightness -= self.BRIGHTNESS_STEP
        # Clamp brightness to minimum visible level
        if self.brightness < self.MIN_BRIGHTNESS:
            self.brightness = self.MIN_BRIGHTNESS
        self.lcd.set_bl_pwm(self.brightness)
