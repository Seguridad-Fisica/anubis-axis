"""
ScreenTouchMediator module for Anubis Axis project.

Author: Seguridad Física
File: managers/screen_touch_mediator.py

This module provides the ScreenTouchMediator class, which manages the interaction between screen and touch events.
"""

from managers.screen_manager import ScreenManager
from managers.touch_manager import TouchManager
from screens.basic_meter.set_zero_screen import SetZeroScreen
from screens.advanced_three_wheels_meter.set_zero_screen_three_wheels import SetZeroScreenThreeWheels
from screens.advanced_four_wheels_meter.set_zero_screen_four_wheels import SetZeroScreenFourWheels
from screens.basic_meter.basic_meter import BasicMeter
from screens.advanced_three_wheels_meter.advanced_three_wheel_meter import AdvancedThreeWheelMeter
from screens.advanced_four_wheels_meter.advanced_four_wheel_meter import AdvancedFourWheelMeter
from screens.usb_meter.usb_meter import USBMeter
class ScreenTouchMediator:
    """Mediator for managing screen and touch interactions.

    Facilitates communication between the ScreenManager and TouchManager,
    allowing for coordinated screen navigation and touch gesture handling.

    Attributes:
        configuration: Configuration instance for application settings.
        screen_manager (ScreenManager): Manages different screen states and brightness levels.
        touch_manager (TouchManager): Manages touch gestures and interactions.
        logger (Logger): Logger instance for logging messages.
    """
    def __init__(self, lcd, touch, encoder, configuration):
        """Initialize the ScreenTouchMediator instance.

        Sets up the ScreenManager and TouchManager with the provided components.

        Args:
            lcd: LCD display instance.
            touch: Touchscreen instance.
            encoder: Encoder instance for reading rotary inputs.
            configuration: Configuration instance for application settings.

        Examples:
            >>> mediator = ScreenTouchMediator(lcd, touch, encoder, configuration)
        """
        self.configuration = configuration
        self.screen_manager = ScreenManager(lcd, touch, encoder, configuration, self)
        self.touch_manager = TouchManager(touch, configuration, self)

    def next_screen(self):
        """Delegate the action to move to the next screen to the ScreenManager.

        Advances to the next screen in the sequence.

        Examples:
            >>> mediator.next_screen()
        """
        self.screen_manager.next_screen()

    def previous_screen(self):
        """Delegate the action to move to the previous screen to the ScreenManager.

        Moves back to the previous screen in the sequence.

        Examples:
            >>> mediator.previous_screen()
        """
        self.screen_manager.previous_screen()

    def run_current_screen(self):
        """Execute the current screen's associated method through the ScreenManager.

        Displays the active screen by invoking its show method.

        Examples:
            >>> mediator.run_current_screen()
        """
        self.screen_manager.run_current_screen()

    def get_gesture(self):
        """Retrieve the current gesture from the TouchManager.

        Fetches the latest gesture detected by the touch controller.

        Returns:
            str: The current gesture detected.

        Examples:
            >>> gesture = mediator.get_gesture()
            >>> print(gesture)
        """
        return self.touch_manager.get_gesture()

    def refresh_screen(self):
        """Refresh the user interface by updating the screen through the ScreenManager.

        Redraws the current screen to reflect any changes.

        Examples:
            >>> mediator.refresh_screen()
        """
        self.screen_manager.update_ui()

    def decrease_brightness(self):
        """Decrease the screen brightness through the ScreenManager.

        Lowers the brightness level by a predefined step, ensuring it does not go below the minimum threshold.

        Examples:
            >>> mediator.decrease_brightness()
        """
        self.screen_manager.decrease_brightness()

    def increase_brightness(self):
        """Increase the screen brightness through the ScreenManager.

        Raises the brightness level by a predefined step, ensuring it does not exceed the maximum threshold.

        Examples:
            >>> mediator.increase_brightness()
        """
        self.screen_manager.increase_brightness()

    def enter_submenu(self):
        """Enters submenu based on current main screen, showing the appropriate SetZero screen first for meter screens"""
        if self.screen_manager:
            current_main_screen = self.screen_manager.screen_hierarchy['main']['current_index']

            # Primero mostramos la pantalla SetZero correspondiente (excepto para USB)
            if current_main_screen == 0:  # basic_meter
                set_zero = SetZeroScreen(self.screen_manager.lcd,
                                         self.screen_manager.touch,
                                         self.screen_manager.encoder,
                                         self.screen_manager.configuration,
                                         self)
                set_zero.show()
                # Después de SetZero, entramos al submenú
                self.screen_manager.enter_submenu('basic_meter_submenus')

            elif current_main_screen == 1:  # advanced_three_wheel_meter
                set_zero = SetZeroScreenThreeWheels(self.screen_manager.lcd,
                                                  self.screen_manager.touch,
                                                  self.screen_manager.encoder,
                                                  self.screen_manager.configuration,
                                                  self)
                set_zero.show()
                self.screen_manager.enter_submenu('advanced_three_wheel_meter_submenus')

            elif current_main_screen == 2:  # advanced_four_wheel_meter
                set_zero = SetZeroScreenFourWheels(self.screen_manager.lcd,
                                                 self.screen_manager.touch,
                                                 self.screen_manager.encoder,
                                                 self.screen_manager.configuration,
                                                 self)
                set_zero.show()
                self.screen_manager.enter_submenu('advanced_four_wheel_meter_submenus')

            elif current_main_screen == 3:  # usb_meter
                # Para USB no necesitamos pantalla SetZero, vamos directamente al submenu
                self.screen_manager.enter_submenu('usb_meter_submenus')

    def exit_screen(self):
        """
        Handles exit screen request triggered by a double click gesture.

        Shows a confirmation dialog and redirects to main menu if confirmed.
        If canceled, stays on the current screen.
        """
        # Get the current screen object
        current_level_data = self.screen_manager.screen_hierarchy[self.screen_manager.current_level]
        current_index = current_level_data['current_index']

        if 0 <= current_index < len(current_level_data['screens']):
            current_screen = current_level_data['screens'][current_index]
            if isinstance(current_screen, (BasicMeter, AdvancedThreeWheelMeter, AdvancedFourWheelMeter, USBMeter)):
                return
            # Call the exit_screen method on the current screen
            # The return value indicates if exit was confirmed (True) or canceled (False)
            exit_confirmed = current_screen.exit_screen()

            if exit_confirmed:
                # If exit was confirmed, we're already at main menu (handled by _navigate_to_main_menu)
                # Just run the current screen to refresh the display
                self.run_current_screen()
            else:
                # If exit was canceled, just refresh the current screen
                # This will clear the confirmation dialog
                current_screen.show()