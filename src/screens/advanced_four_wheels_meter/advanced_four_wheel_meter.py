"""
BasciMeter module for Anubis Axis project.

Author: Seguridad Física
File: screens/quarter_screen.py

This module provides the QuarterScreen class, which displays numerical values in a 1/4 decimal format on the LCD.
"""

from screens.base_screen import BaseScreen
from common.constants import GESTURE_RESET

class AdvancedFourWheelMeter(BaseScreen):
    """Screen displaying numerical values in 1/4 decimal format.

    Continuously displays the current value in 1/4 format until a gesture is detected.
    """

    def __init__(self, lcd, touch, encoder, configuration, screen_touch_mediator):
        """Initialize the QuarterScreen with necessary components and configurations.

        Sets up format reading for decimal values.

        Args:
            lcd: LCD display instance.
            touch: Touchscreen instance.
            encoder: Encoder instance.
            configuration: Configuration instance.
            screen_touch_mediator: Mediator for screen and touch interactions.

        Examples:
            >>> quarter_screen = QuarterScreen(lcd, touch, encoder, configuration, mediator)
        """
        super().__init__(lcd, touch, encoder, configuration, screen_touch_mediator)

    def show(self):
        """Continuously display the current value in 1/4 format until a gesture is detected.

        Resets touch gestures to default and enters a loop to update the display based on encoder readings.
        Exits the loop if a gesture is detected.

        Examples:
            >>> quarter_screen.show()
        """
        # Resets touch gestures to default
        self.touch.Gestures = GESTURE_RESET

        while True:
            # Update colors using the inherited method from BaseScreen
            self.update_theme_colors()

            # Clear LCD screen by filling it with the background color
            self.lcd.fill(self.theme_colors['background'])

            # Draw dial widget
            self.widget_manager.draw_circle_from_value(
                indicator_radius=3,
                indicator_color=self.theme_colors['shadow'],
                value=3924,
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
                value_offset_y=-60,
                value_color=self.theme_colors['shadow'],
                value_format='SCALE_0_99_QUARTER',
                value_size=3,

                show_fraction_separate=True,
                vertical_fraction=True,
                fraction_offset_y=8,
                fraction_size=4,         # Tamaño personalizado para la fracción
                fraction_color=self.theme_colors['shadow']
            )

            # Draw wheel 1 widget
            self.widget_manager.draw_circle_from_value(
                indicator_radius=3,
                indicator_color=self.theme_colors['shadow'],
                value_color=self.theme_colors['shadow'],
                value=2048,
                center_x=50,
                center_y=120,

                orbit_radius=25,
                orbit_color=self.theme_colors['shadow'],
                show_orbit=True,

                dot_style='double',  # Estilo doble
                dot_rings=3,         # 6 anillos externos
                dot_rings_color=self.theme_colors['background'],  # Color de fondo para los anillos

                label="1",  # Añadir etiqueta
                label_size=1,     # Tamaño del texto
                label_position="up",
                label_color=self.theme_colors['shadow'],  # Color del texto

                show_value=True,
                value_format='decimal',
                value_size=1     # Tamaño más grande
            )

            # Draw wheel 2 widget
            self.widget_manager.draw_circle_from_value(
                indicator_radius=3,
                indicator_color=self.theme_colors['shadow'],
                value_color=self.theme_colors['shadow'],
                value=1024,
                center_x=85,
                center_y=180,

                orbit_radius=25,
                orbit_color=self.theme_colors['shadow'],
                show_orbit=True,

                dot_style='double',  # Estilo doble
                dot_rings=3,         # 6 anillos externos
                dot_rings_color=self.theme_colors['background'],  # Color de fondo para los anillos

                label="2",  # Añadir etiqueta
                label_size=1,     # Tamaño del texto
                label_position="up",
                label_color=self.theme_colors['shadow'],  # Color del texto

                show_value=True,
                value_format='decimal',
                value_size=1     # Tamaño más grande
            )

            # Draw wheel 3 widget
            self.widget_manager.draw_circle_from_value(
                indicator_radius=3,
                indicator_color=self.theme_colors['shadow'],
                value_color=self.theme_colors['shadow'],
                value=2048,
                center_x=155,
                center_y=180,
                orbit_radius=25,
                orbit_color=self.theme_colors['shadow'],
                show_orbit=True,
                dot_style='double',  # Estilo doble
                dot_rings=3,         # 6 anillos externos
                dot_rings_color=self.theme_colors['background'],  # Color de fondo para los anillos
                label="3",  # Añadir etiqueta
                label_size=1,     # Tamaño del texto
                label_position="up",
                label_color=self.theme_colors['shadow'],  # Color del texto

                show_value=True,
                value_format='decimal',
                value_size=1     # Tamaño más grande
            )

            # Draw wheel 4 widget
            self.widget_manager.draw_circle_from_value(
                indicator_radius=3,
                indicator_color=self.theme_colors['shadow'],
                value_color=self.theme_colors['shadow'],
                value=2048,
                center_x=190,
                center_y=120,
                orbit_radius=25,
                orbit_color=self.theme_colors['shadow'],
                show_orbit=True,
                dot_style='double',  # Estilo doble
                dot_rings=3,         # 6 anillos externos
                dot_rings_color=self.theme_colors['background'],  # Color de fondo para los anillos
                label="3",  # Añadir etiqueta
                label_size=1,     # Tamaño del texto
                label_position="up",
                label_color=self.theme_colors['shadow'],  # Color del texto

                show_value=True,
                value_format='decimal',
                value_size=1     # Tamaño más grande
            )

            # Show widgets dot_indicator (screen number indicator)
            self.widget_manager.draw_dot_indicator(
                num_pages=4,        # Número total de páginas
                active_page=2,      # Página actual activa (0-based index)
                dot_size=8,         # Diámetro del punto en píxeles
                arc_radius=105,      # Radio del arco donde se dibujan los puntos
                arc_span=20
            )

            # Show battery monitor on the widget con estilo línea
            self.widget_manager.show_battery_monitor(
                center_x=120,        # Posición X más a la derecha
                center_y=20,         # Posición Y en la parte superior
                size='S',            # Tamaño pequeño para no ocupar mucho espacio
                style='line'         # Nuevo estilo de líneas
            )

            self.format_text.center_or_position_text("ADVANCED", 2, self.theme_colors['primary'], center_x=True, center_y=False, y=90)
            self.format_text.center_or_position_text("METER", 2, self.theme_colors['primary'], center_x=True, center_y=False, y=120)
            self.format_text.center_or_position_text("4 wheels", 2, self.theme_colors['text_body'], center_x=True, center_y=False, y=150)

            # Refresh the current content of the buffer on the LCD screen
            self.lcd.show()

            # Exit loop if a gesture is detected
            if self.screen_touch_mediator.get_gesture():
                break
