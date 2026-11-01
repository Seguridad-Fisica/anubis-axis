# screens/set_zero_screen.py

"""
SetZeroScreenThreeWheels module for Anubis Axis project.

Author: Seguridad Física
File: screens/advanced_three_wheels_meter/set_zero_screen_three_wheels.py

This module provides the SetZeroScreenThreeWheels class, which displays the "SET ZERO" instructions
on the LCD screen and handles the user interaction to set the encoder's zero offset for three wheels mode.
"""
import time
from screens.base_screen import BaseScreen
from ui.format_text import FormatText
from common.constants import GESTURE_SINGLE_CLICK, GESTURE_RESET
from ui.logger import Logger

class SetZeroScreenThreeWheels(BaseScreen):
    """Screen for setting the encoder's zero offset in three wheels mode.

    Displays instructions to the user to set the zero offset and waits for a single touch gesture
    to proceed with the zeroing process.
    """

    def __init__(self, lcd, touch, encoder, configuration, screen_touch_mediator):
        """Initialize the SetZeroScreenThreeWheels with necessary components and configurations.

        Args:
            lcd: LCD display instance.
            touch: Touchscreen instance.
            encoder: Encoder instance.
            configuration: Configuration instance.
            screen_touch_mediator: Mediator for screen and touch interactions.
        """
        super().__init__(lcd, touch, encoder, configuration, screen_touch_mediator)
        self.format_text = FormatText(lcd)
        self.logger = Logger()

    def show(self):
        """Display the reset instructions and handle user input to set zero offset."""
        set_zero_text_on_lcd = "Turn 4L or 4R and stop at 0"

        while True:
            # Get raw reading for display and validation
            raw_reading = self.encoder.get_raw_value()

            # Check if reading is valid
            if raw_reading is None:
                initial_reading = "None"
                reading_valid = False
            else:
                initial_reading = str(raw_reading)
                reading_valid = True

            # Update screen display
            self.lcd.fill(self.theme_colors['background'])

            self.format_text.center_or_position_text(
                "Resetting",
                2,
                self.theme_colors['primary'],
                center_x=True,
                center_y=False,
                y=40
            )

            self.format_text.center_or_position_text(
                "the lock",
                2,
                self.theme_colors['primary'],
                center_x=True,
                center_y=False,
                y=60
            )

            self.format_text.center_or_position_text(
                set_zero_text_on_lcd,
                1,
                self.theme_colors['text_title'],
                center_x=True,
                center_y=False,
                y=90
            )

            self.format_text.center_or_position_text(
                initial_reading,
                2,
                self.theme_colors['text_body'],
                center_x=True,
                center_y=False,
                y=110
            )

            # Draw AWL and AWR buttons
            self.widget_manager.draw_rounded_button(
                x=70,
                y=170,
                text="AWL",
                text_size=2,
                button_color=self.theme_colors['primary'],
                text_color=self.theme_colors['on_primary']
            )

            self.widget_manager.draw_rounded_button(
                x=170,
                y=170,
                text="AWR",
                text_size=2,
                button_color=self.theme_colors['primary'],
                text_color=self.theme_colors['on_primary']
            )

            # Display battery monitor widget
            self.widget_manager.show_battery_monitor(
                center_x=120,
                center_y=20,
                size='S',
                style='line'
            )
            self.lcd.show()

            # Process touch input only if reading is valid
            if self.touch.Gestures == GESTURE_SINGLE_CLICK and reading_valid:
                self.logger.console_printing("INFO", f"Touch at: X={self.touch.X_point}, Y={self.touch.Y_point}")

                # AWL button: Left half of bottom area
                if 0 <= self.touch.X_point <= 120 and 120 <= self.touch.Y_point <= 240:
                    self.logger.console_printing("INFO", "AWL button pressed")

                    # Step 1: Configure virtual pins for AWL mode
                    self.encoder.resetting_lock("AWL")

                    # Step 2: Set zero offset with stable raw readings
                    while True:
                        raw_readings = []
                        for _ in range(5):
                            reading = self.encoder.get_raw_value()
                            raw_readings.append(reading)
                            time.sleep_ms(50)

                        # Verify all readings are consistent and valid
                        if all(reading is not None for reading in raw_readings) and all(reading == raw_readings[0] for reading in raw_readings):
                            self.encoder.zero_offset = raw_readings[0]
                            self.logger.console_printing("INFO", f"Encoder offset set to RAW value: {raw_readings[0]}")

                            # Step 3: Reset wheel positions with new zero offset applied
                            self.encoder.reset_lock_values()
                            self.logger.console_printing("INFO", "Wheel positions reset after zero offset")
                            break
                        else:
                            self.logger.console_printing("ERROR", "Readings are not consistent. Trying again...")
                    break

                # AWR button: Right half of bottom area
                elif 120 <= self.touch.X_point <= 240 and 120 <= self.touch.Y_point <= 240:
                    self.logger.console_printing("INFO", "AWR button pressed")

                    # Step 1: Configure virtual pins for AWR mode
                    self.encoder.resetting_lock("AWR")

                    # Step 2: Set zero offset with stable raw readings
                    while True:
                        raw_readings = []
                        for _ in range(5):
                            reading = self.encoder.get_raw_value()
                            raw_readings.append(reading)
                            time.sleep_ms(50)

                        # Verify all readings are consistent and valid
                        if all(reading is not None for reading in raw_readings) and all(reading == raw_readings[0] for reading in raw_readings):
                            self.encoder.zero_offset = raw_readings[0]
                            self.logger.console_printing("INFO", f"Encoder offset set to RAW value: {raw_readings[0]}")

                            # Step 3: Reset wheel positions with new zero offset applied
                            self.encoder.reset_lock_values()
                            self.logger.console_printing("INFO", "Wheel positions reset after zero offset")
                            break
                        else:
                            self.logger.console_printing("ERROR", "Readings are not consistent. Trying again...")
                    break

            #elif self.screen_touch_mediator.get_gesture():
            #    break
            #time.sleep_ms(10)  # Prevent CPU overload