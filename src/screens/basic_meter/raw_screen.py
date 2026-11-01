# screens/raw_screen.py

"""
RawScreen module for Anubis Axis project.

Author: Seguridad Física
File: screens/basic_meter/raw_screen.py

This module provides the RawScreen class, which displays the raw numerical value
directly converted from the 12-bit encoder data (0 to 4095) on the LCD screen.
"""

from screens.base_screen import BaseScreen
from common.constants import GESTURE_RESET

class RawScreen(BaseScreen):
    """Screen displaying the raw numerical value from the encoder.

    Continuously displays the raw value directly converted from the 12-bit encoder data
    (ranging from 0 to 4095) until a gesture is detected.
    """

    def __init__(self, lcd, touch, encoder, configuration, screen_touch_mediator):
        """Initialize the RawScreen with necessary components and configurations.

        Sets up format reading for raw value display and initializes text formatting.

        Args:
            lcd: LCD display instance.
            touch: Touchscreen instance.
            encoder: Encoder instance.
            configuration: Configuration instance.
            screen_touch_mediator: Mediator for screen and touch interactions.

        Examples:
            >>> raw_screen = RawScreen(lcd, touch, encoder, configuration, mediator)
        """
        super().__init__(lcd, touch, encoder, configuration, screen_touch_mediator)

    def show(self):
        """Continuously display the raw value until a gesture is detected.

        Resets touch gestures to default and enters a loop to update the display based
        on encoder readings. Exits the loop if a gesture is detected.

        Examples:
            >>> raw_screen.show()
        """
        # Resets touch gestures to default
        self.touch.Gestures = GESTURE_RESET

        while True:
            # Obtener la lectura cruda del encoder
            raw_data = self.encoder.get_value()

            # Update colors using the inherited method from BaseScreen
            self.update_theme_colors()
            # Clear LCD screen by filling it with the background color
            self.lcd.fill(self.theme_colors['background'])

            # Verificar si la lectura es None
            if raw_data is None:
                raw_value_for_circle = 0  # Usar 0 para evitar errores en draw_circle_from_value

                # Draw dial widget
                self.widget_manager.draw_circle_from_value(
                    indicator_radius=3,
                    indicator_color=self.theme_colors['shadow'],
                    value=raw_value_for_circle,
                    value_color=self.theme_colors['shadow'],
                    center_x=120,
                    center_y=120,

                    orbit_radius=113,
                    orbit_color=self.theme_colors['shadow'],
                    show_orbit=True,

                    dot_style='double',
                    dot_rings=3,
                    dot_rings_color=self.theme_colors['background'],

                    label="Dial",
                    label_size=1,
                    label_color=self.theme_colors['shadow'],

                    show_value=True,
                    value_format='raw',
                    value_size=4
                )

                self.format_text.center_or_position_text("ERROR", 3, self.theme_colors['warning'], center_x=True, center_y=False, y=75)
                self.format_text.center_or_position_text("ENCODER", 2, self.theme_colors['text_body'], center_x=True, center_y=False, y=140)

            else:
                raw_value_for_circle = raw_data

                # Draw dial widget
                self.widget_manager.draw_circle_from_value(
                    indicator_radius=3,
                    indicator_color=self.theme_colors['primary'],
                    value=raw_value_for_circle,
                    center_x=120,
                    center_y=120,

                    orbit_radius=113,
                    orbit_color=self.theme_colors['primary_shadow'],
                    show_orbit=True,

                    dot_style='double',
                    dot_rings=3,
                    dot_rings_color=self.theme_colors['background'],

                    label="Dial",
                    label_size=1,
                    label_color=self.theme_colors['primary'],

                    show_value=True,
                    value_format='raw',
                    value_size=4
                )

            # Show widgets dot_indicator (screen number indicator)
            self.widget_manager.draw_dot_indicator(
                num_pages=5,        # Número total de páginas
                active_page=4,      # Página actual activa (0-based index)
                dot_size=8,         # Diámetro del punto en píxeles
                arc_radius=100      # Radio del arco donde se dibujan los puntos
            )

            # Show battery monitor on the widget con estilo línea
            self.widget_manager.show_battery_monitor(
                center_x=120,        # Posición X más a la derecha
                center_y=20,         # Posición Y en la parte superior
                size='S',            # Tamaño pequeño para no ocupar mucho espacio
                style='line'         # Nuevo estilo de líneas
            )

            # Refresh the current content of the buffer on the LCD screen
            self.lcd.show()

            # Exit loop if a gesture is detected
            if self.screen_touch_mediator.get_gesture():
                break