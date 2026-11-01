"""
LogoScreen module for Anubis Axis project.

Author: Seguridad Física
File: screens/logo_screen.py

This module provides the LogoScreen class, which displays the initial logo and version information on the LCD screen.
"""
import gc
import time
from common.constants import __version__
from .base_screen import BaseScreen
from ui.format_text import FormatText

# Full-width raster logo, pre-encoded in framebuffer-native RGB565 byte order
# (see tools/convert_image_to_rgb565.py). When the application is frozen into
# the firmware (.uf2), ui/assets/logo_240.py is compiled to bytecode by mpy-cross
# on the host PC and embedded in Flash ROM. Falls back to the .rgb565 file on the
# filesystem, and finally to the text wordmark if neither is present.
try:
    from ui.assets.logo_240 import LOGO_240_RGB565, LOGO_240_WIDTH, LOGO_240_HEIGHT
except (ImportError, MemoryError):
    LOGO_240_RGB565 = None
    LOGO_240_WIDTH = LOGO_240_HEIGHT = None

LOGO_IMAGE_PATH = "/ui/assets/logo_240.rgb565"
LOGO_IMAGE_HEIGHT = 240

class LogoScreen(BaseScreen):
    """Screen displaying the initial logo and version information.

    Shows the logo, designer name, and version on the LCD screen for 2 seconds.
    """

    def __init__(self, lcd, touch, encoder, configuration, screen_touch_mediator):
        """Initialize the LogoScreen with necessary components and configurations.

        Sets up text formatting for LCD display.

        Args:
            lcd: LCD display instance.
            touch: Touchscreen instance.
            encoder: Encoder instance.
            configuration: Configuration instance.
            screen_touch_mediator: Mediator for screen and touch interactions.

        Examples:
            >>> logo_screen = LogoScreen(lcd, touch, encoder, config, mediator)
        """
        super().__init__(lcd, touch, encoder, configuration, screen_touch_mediator)
        # Initialize text formatting for LCD display
        self.format_text = FormatText(lcd)

    def show(self):
        """Display the logo and version information on the LCD screen for 2 seconds.

        Accesses specific translations for the LCD display and shows the logo,
        designer name, and version. Clears the screen after displaying for 2 seconds.

        Examples:
            >>> logo_screen.show()
        """
        # Accessing specific translations for the LCD screen
        logo_text_on_lcd = self.configuration.translations['logo_screen'].get('logo', '??')
        #designer_text_on_lcd = self.configuration.translations['logo_screen'].get('designer', 'SEGURIDAD FISICA')
        version_text_on_lcd = f"v{__version__}"

        # Display the logo on the screen
        self.lcd.fill(self.theme_colors['background'])

        # Prefer the frozen in-memory asset (no filesystem access, works even
        # without deploying the .rgb565 file); fall back to the filesystem
        # copy, and finally to the text wordmark if neither is available.
        if LOGO_240_RGB565 is not None:
            self.lcd.draw_rgb565_data(LOGO_240_RGB565, 0, 0, LOGO_240_WIDTH, LOGO_240_HEIGHT)
            logo_loaded = True
        else:
            logo_loaded = self.lcd.draw_rgb565_file(LOGO_IMAGE_PATH, 0, 0, self.lcd.width, LOGO_IMAGE_HEIGHT)
        if not logo_loaded:
            self.format_text.center_or_position_text(logo_text_on_lcd, 3, self.theme_colors['primary'], center_x=True, center_y=False, y=80)

        #self.format_text.center_or_position_text(designer_text_on_lcd, 1, self.theme_colors['text_title'], center_x=True, center_y=False, y=220)
        self.format_text.center_or_position_text(version_text_on_lcd, 1, self.theme_colors['text_body'], center_x=True, center_y=False, y=230)
        self.lcd.show()
        time.sleep(3)  # Wait for 3 seconds