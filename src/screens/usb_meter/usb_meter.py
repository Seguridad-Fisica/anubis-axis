"""
BasciMeter module for Anubis Axis project.

Author: Seguridad Física
File: screens/quarter_screen.py

This module provides the QuarterScreen class, which displays numerical values in a 1/4 decimal format on the LCD.
"""

from screens.base_screen import BaseScreen
from common.constants import GESTURE_RESET
from ui.assets.icons import ICONS
class USBMeter(BaseScreen):
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
        """Muestra la pantalla del medidor USB hasta que se detecta un gesto.

        Restablece los gestos táctiles por defecto y entra en un bucle para actualizar la pantalla.
        Sale del bucle si se detecta un gesto.

        Examples:
            >>> quarter_screen.show()
        """
        # Restablece los gestos táctiles por defecto
        self.touch.Gestures = GESTURE_RESET

        while True:
            # Actualiza los colores usando el método heredado de BaseScreen
            self.update_theme_colors()

            # Limpia la pantalla LCD rellenándola con el color de fondo
            self.lcd.fill(self.theme_colors['background'])

            # Muestra el indicador de puntos (indicador de número de pantalla)
            self.widget_manager.draw_dot_indicator(
                num_pages=4,        # Número total de páginas
                active_page=3,      # Página activa actual (índice basado en 0)
                dot_size=8,         # Diámetro del punto en píxeles
                arc_radius=105,     # Radio del arco donde se dibujan los puntos
                arc_span=20
            )

            # Muestra el monitor de batería en el widget con estilo de línea
            self.widget_manager.show_battery_monitor(
                center_x=120,       # Posición X en el extremo derecho
                center_y=20,        # Posición Y en la parte superior
                size='S',           # Tamaño pequeño para no ocupar demasiado espacio
                style='line'        # Nuevo estilo de línea
            )

            # Calculate center position for the 150x150 icon canvas
            img_x = 45
            img_y = 45

            # Draw the USB icon from frozen/in-memory bitmap data
            self.lcd.draw_bitmap_data(
                ICONS["usb_150px"],
                img_x,
                img_y,
                self.theme_colors['shadow'],
                width=150
            )

            # Añade el título y el texto de instrucciones
            self.format_text.center_or_position_text(
                "USB Meter",
                2,
                self.theme_colors['primary'],
                center_x=True,
                center_y=False,
                y=100
            )

            self.format_text.center_or_position_text(
                "Connect to Anubis Axis",
                1,
                self.theme_colors['text_body'],
                center_x=True,
                center_y=False,
                y=205
            )

            # Actualiza el contenido actual del buffer en la pantalla LCD
            self.lcd.show()

            # Sale del bucle si se detecta un gesto
            if self.screen_touch_mediator.get_gesture():
                break