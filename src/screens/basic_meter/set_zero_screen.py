# screens/set_zero_screen.py

"""
SetZeroScreen module for Anubis Axis project.

Author: Seguridad Física
File: screens/set_zero_screen.py

This module provides the SetZeroScreen class, which displays the "SET ZERO" instructions on the LCD screen
and handles the user interaction to set the encoder's zero offset.
"""
import time
from screens.base_screen import BaseScreen
from ui.format_text import FormatText
from common.constants import GESTURE_SINGLE_CLICK
from ui.logger import Logger

class SetZeroScreen(BaseScreen):
    """Screen for setting the encoder's zero offset.

    Displays instructions to the user to set the zero offset and waits for a single touch gesture
    to proceed with the zeroing process.
    """

    def __init__(self, lcd, touch, encoder, configuration, screen_touch_mediator):
        """Initialize the SetZeroScreen with necessary components and configurations.

        Args:
            lcd: LCD display instance.
            touch: Touchscreen instance.
            encoder: Encoder instance.
            configuration: Configuration instance.
            screen_touch_mediator: Mediator for screen and touch interactions.

        Examples:
            >>> set_zero_screen = SetZeroScreen(lcd, touch, encoder, configuration, mediator)
        """
        super().__init__(lcd, touch, encoder, configuration, screen_touch_mediator)
        self.format_text = FormatText(lcd)
        self.logger = Logger()

    def show(self):
        """Display the "SET ZERO" instructions and handle user input to set zero offset."""
        title_screen = self.configuration.translations['set_zero_screen'].get('title')
        set_zero_text_on_lcd = self.configuration.translations['set_zero_screen'].get('set_zero')
        press_text_on_lcd = self.configuration.translations['set_zero_screen'].get('press')

        while True:
            # Obtener la lectura del encoder - CAMBIO: usar get_value() para mostrar pero get_raw_value() para establecer
            reading = self.encoder.get_value()  # Para mostrar usamos el valor ajustado
            raw_reading = self.encoder.get_raw_value()  # Para establecer zero usamos el valor raw

            # Verificar si la lectura es None
            if reading is None or raw_reading is None:
                initial_reading = "None"
                reading_valid = False
            else:
                initial_reading = str(raw_reading)
                reading_valid = True

            # Actualizar siempre la pantalla
            self.lcd.fill(self.theme_colors['background'])

            self.format_text.center_or_position_text(
                title_screen,
                2,
                self.theme_colors['primary'],  # Usar color de título
                center_x=True,
                center_y=False,
                y=40
            )

            self.format_text.center_or_position_text(
                set_zero_text_on_lcd,
                1,
                self.theme_colors['text_title'],  # Usar color de título
                center_x=True,
                center_y=False,
                y=70
            )

            self.format_text.center_or_position_text(
                initial_reading,
                3,
                self.theme_colors['text_body'],   # Usar color de texto normal
                center_x=True,
                center_y=False,
                y=110
            )

            self.widget_manager.draw_rounded_button(
                x=120,
                y=180,
                text=press_text_on_lcd,
                text_size=2,
                button_color=self.theme_colors['primary'],
                text_color=self.theme_colors['on_primary']
            )

            # Show battery monitor on the widget con estilo línea
            self.widget_manager.show_battery_monitor(
                center_x=120,        # Posición X más a la derecha
                center_y=20,         # Posición Y en la parte superior
                size='S',            # Tamaño pequeño para no ocupar mucho espacio
                style='line'         # Nuevo estilo de líneas
            )
            self.lcd.show()

            # Solo proceder si la lectura es válida
            if self.touch.Gestures == GESTURE_SINGLE_CLICK and reading_valid:
                self.logger.console_printing("INFO", f"Touch at: X={self.touch.X_point}, Y={self.touch.Y_point}")
                while True:
                    raw_readings = []  # Inicializar lista de lecturas RAW (sin offset)
                    for _ in range(5):  # Tomar 5 lecturas
                        # CAMBIO: Usamos get_raw_value() en lugar de get_value()
                        reading = self.encoder.get_raw_value()
                        raw_readings.append(reading)
                        time.sleep_ms(50)

                    # Verificar que todas las lecturas no sean None y sean iguales
                    if all(reading is not None for reading in raw_readings) and all(reading == raw_readings[0] for reading in raw_readings):
                        # CAMBIO: Guardamos el valor raw como offset
                        self.encoder.zero_offset = raw_readings[0]
                        self.logger.console_printing("INFO", f"Encoder offset set to RAW value: {raw_readings[0]}")
                        break
                    else:
                        self.logger.console_printing("ERROR", "Readings are not consistent. Trying again...")
                break
            #elif self.screen_touch_mediator.get_gesture():
            #    break

            time.sleep_ms(10)  # Añadir un pequeño retraso para evitar sobrecargar la CPU