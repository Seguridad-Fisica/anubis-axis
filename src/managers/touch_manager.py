"""
TouchManager module for Anubis Axis project.

Author: Seguridad Física
File: managers/touch_manager.py

This module provides the TouchManager class, which processes touch gestures and delegates actions
to the ScreenTouchMediator.
"""

from common.constants import GESTURE_SLIDE_LEFT, GESTURE_SLIDE_RIGHT, GESTURE_LONG_PRESS, GESTURE_SLIDE_UP, GESTURE_SLIDE_DOWN, GESTURE_DOUBLE_CLICK, GESTURE_SINGLE_CLICK

class TouchManager:
    """Handles touch gesture processing and delegates actions accordingly.

    Processes user input gestures and performs corresponding actions such as toggling dark mode,
    navigating between screens, and adjusting screen brightness.

    Attributes:
        touch: Instance of the touch interface.
        configuration: Configuration instance for application settings.
        screen_touch_mediator: Mediator for screen and touch interactions.
    """
    def __init__(self, touch, configuration, screen_touch_mediator=None):
        """Initialize the TouchManager instance.

        Sets up the touch interface, configuration settings, and the screen touch mediator.

        Args:
            touch: Touch interface instance.
            configuration: Configuration instance for application settings.
            screen_touch_mediator (ScreenTouchMediator, optional): Mediator for screen and touch interactions.
                Defaults to None.

        Examples:
            >>> touch_manager = TouchManager(touch, configuration, mediator)
        """
        self.touch = touch
        self.configuration = configuration
        self.screen_touch_mediator = screen_touch_mediator

    def get_gesture(self):
        """Process the current touch gesture and perform the corresponding action.

        Processes user input gestures and performs corresponding actions:
            - Toggle dark mode on long press gesture.
            - Navigate to the next or previous screen with slide gestures.
            - Adjust screen brightness with up and down slide gestures.

        Returns:
            bool: True if an actionable gesture is detected and processed, False otherwise.

        Examples:
            >>> gesture_detected = touch_manager.get_gesture()
            >>> if gesture_detected:
            ...     print("Gesture processed.")
        """
        gesture = self.touch.get_gesture_state()
        # Toggle dark mode on long press gesture.
        if gesture == GESTURE_LONG_PRESS:
            if self.screen_touch_mediator is not None:      # Check if a screen touch mediator is available.
                self.configuration.dark_mode = not self.configuration.dark_mode
                self.configuration.save_configuration()
                self.screen_touch_mediator.refresh_screen()
            return True

        # Navigate to the next or previous screen with slide gestures.
        elif gesture == GESTURE_SLIDE_LEFT:
            if self.screen_touch_mediator is not None:      # Check if a screen touch mediator is available.
                self.screen_touch_mediator.next_screen()
            return True
        elif gesture == GESTURE_SLIDE_RIGHT:
            if self.screen_touch_mediator is not None:      # Check if a screen touch mediator is available.
                self.screen_touch_mediator.previous_screen()
            return True

        # Adjust screen brightness with up and down slide gestures.
        elif gesture == GESTURE_SLIDE_UP:
            if self.screen_touch_mediator is not None:      # Check if a screen touch mediator is available.
                self.screen_touch_mediator.decrease_brightness()
            return True
        elif gesture == GESTURE_SLIDE_DOWN:
            if self.screen_touch_mediator is not None:      # Check if a screen touch mediator is available.
                self.screen_touch_mediator.increase_brightness()
            return True

        # Enter submenu on single click gesture, but only if we're in main menu
        elif gesture == GESTURE_SINGLE_CLICK:
            if self.screen_touch_mediator is not None:
                # Check if we're in the main level before entering submenu
                if hasattr(self.screen_touch_mediator, 'screen_manager') and self.screen_touch_mediator.screen_manager.current_level == 'main':
                    self.screen_touch_mediator.enter_submenu()
            return True

        # Exit screen on double click gesture.
        elif gesture == GESTURE_DOUBLE_CLICK:
            if self.screen_touch_mediator is not None:
                self.screen_touch_mediator.exit_screen()
            return True
        # Return False if no actionable gesture is detected.
        return False