# screens/usb_meter/usb_screen.py

"""
USBScreen module for Anubis Axis project.

Author: Seguridad Física
File: screens/usb_meter/usb_screen.py

This module provides the USBScreen class, which displays USB communication status
and enables interaction with the device via USB CDC interface.
"""
import time
from screens.base_screen import BaseScreen
from ui.format_text import FormatText
from common.constants import GESTURE_RESET, GESTURE_DOUBLE_CLICK, GESTURE_SINGLE_CLICK
from ui.logger import Logger
from ui.assets.icons import ICONS

# Import USB CDC data interface from boot.py.
# Use getattr with a default so a missing/failed boot.py CDC init (e.g. an
# incompatible lib/usb/device/*.mpy build) does not crash the whole app at
# import time - only this screen's USB manager degrades gracefully instead.
import usb.device
cdc_data = getattr(usb.device, "cdc_data", None)

from managers.usb_manager import USBManager  # Import USB Manager

class USBScreen(BaseScreen):
    """Screen for USB communication.

    Displays the status of the USB connection and communication data.
    """

    def __init__(self, lcd, touch, encoder, configuration, screen_touch_mediator):
        """Initialize the USBScreen with necessary components and configurations.

        Args:
            lcd: LCD display instance.
            touch: Touchscreen instance.
            encoder: Encoder instance.
            configuration: Configuration instance.
            screen_touch_mediator: Mediator for screen and touch interactions.

        Examples:
            >>> usb_screen = USBScreen(lcd, touch, encoder, configuration, mediator)
        """
        super().__init__(lcd, touch, encoder, configuration, screen_touch_mediator)
        self.format_text = FormatText(lcd)
        self.logger = Logger()

        # Initialize USB Manager with the required dependencies
        self.usb_manager = USBManager(cdc_data, encoder=encoder, lcd=lcd, configuration=configuration)
        self.usb_manager.start()

        print("USBScreen initialized")

    def show(self):
        """Display the USB communication screen and process USB interactions."""
        # Variable para controlar si se debe mostrar la pantalla de salida
        while True:
            self.usb_manager.process()  # Procesa la comunicación USB
            self.lcd.fill(self.theme_colors['background'])
            if self.show_exit == False:
                # Título
                self.format_text.center_or_position_text(
                    "USB Meter",
                    2,
                    self.theme_colors['primary'],
                    center_x=True,
                    center_y=False,
                    y=40
                )
                # Position the 150x150 icon canvas at the center of the display
                img_x = 45  # (240 - 150) / 2
                img_y = 45  # (240 - 150) / 2

                # Lógica para determinar el estado de conexión:
                # 1. Desconectado: CDC no está abierta.
                # 2. Conectado pero sin comunicación: CDC abierta pero DTR inactivo.
                # 3. Conectado con comunicación: CDC abierta y DTR activo.

                if not (self.usb_manager.cdc and self.usb_manager.cdc.is_open()):
                    # Desconectado
                    icon_data = ICONS["usb_off_150px"]
                    icon_color = self.theme_colors['warning']
                else:
                    if self.usb_manager.cdc.dtr:
                        # Conectado con comunicación activa
                        icon_data = ICONS["usb_150px"]
                        icon_color = self.theme_colors['primary']
                    else:
                        # Conectado pero sin comunicación activa
                        icon_data = ICONS["usb_150px"]
                        icon_color = self.theme_colors['shadow_2']


                # Dibujar el ícono correspondiente
                self.lcd.draw_bitmap_data(icon_data, img_x, img_y, icon_color, width=150)
                # Actualizar la pantalla
                self.lcd.show()
                #print(self.touch.Gestures)
                if self.touch.Gestures == GESTURE_DOUBLE_CLICK:
                    self.show_exit = True
                    self.touch.Gestures = GESTURE_RESET

                if self.screen_touch_mediator.get_gesture():
                    break
            else:
                # Llamar a exit_screen y verificar si debemos salir
                should_exit = self.exit_screen(show_message=True)

                # Si el usuario confirmó salir, salimos del bucle while True
                if should_exit:
                    return  # Esto devolverá el control al ScreenManager