"""
EighthScreen module for Anubis Axis project.

Author: Seguridad Física
File: screens/eighth_screen.py

This module provides the EighthScreen class, which displays numerical values in a 1/8 format on the LCD.
"""

from screens.base_screen import BaseScreen
from common.constants import GESTURE_RESET

class EighthScreen(BaseScreen):
    """Screen displaying numerical values in 1/8 decimal format.

    Continuously displays the current value in 1/8 format until a gesture is detected.
    """

    def __init__(self, lcd, touch, encoder, configuration, screen_touch_mediator):
        """Initialize the EighthScreen with necessary components and configurations.

        Sets up format reading for decimal values.

        Args:
            lcd: LCD display instance.
            touch: Touchscreen instance.
            encoder: Encoder instance.
            configuration: Configuration instance.
            screen_touch_mediator: Mediator for screen and touch interactions.

        Examples:
            >>> screen = EighthScreen(lcd, touch, encoder, config, mediator)
        """
        super().__init__(lcd, touch, encoder, configuration, screen_touch_mediator)

    def show(self):
        """Continuously display the current value in 1/8 format until a gesture is detected.

        Resets touch gestures to default and enters a loop to update the display based on encoder readings.
        Exits the loop if a gesture is detected.

        Examples:
            >>> screen.show()
        """
        # Resets touch gestures to default
        self.touch.Gestures = GESTURE_RESET

        while True:
            # Get raw reading value
            raw_data = self.encoder.get_value()

            # Update colors using the inherited method from BaseScreen
            self.update_theme_colors()
            # Clear LCD screen by filling it with the background color
            self.lcd.fill(self.theme_colors['background'])

            # Verificar si la lectura es None
            if raw_data is None:
                raw_value_for_circle = 0  # Establecer raw a cero para evitar errores en draw_circle_from_value
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
                raw_value_for_circle = raw_data  # Establecer raw a cero para evitar errores en draw_circle_from_value
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
                    value_format='SCALE_0_99_EIGHTH',
                    value_size=3,
                    value_offset_y=-50,
                    show_fraction_separate=True,
                    vertical_fraction=True,  # Habilitamos el formato vertical
                    fraction_offset_y=10,    # Añadimos offset vertical
                    fraction_size=5,         # Tamaño personalizado para la fracción
                    fraction_color=self.theme_colors['text_title'],  # Color de la fracción
                    show_empty_fraction=True
                )

            self.widget_manager.draw_dot_indicator(
                num_pages=5,        # Número total de páginas
                active_page=1,      # Página actual activa (0-based index)
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
