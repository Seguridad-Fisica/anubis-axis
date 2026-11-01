"""
LCD driver module for Anubis Axis project.

This module provides the GC9A01ALCD class for managing interaction with a 1.28-inch
240x240 circular LCD display using the GC9A01A driver chip. It implements SPI communication,
framebuffer management, text rendering with caching, and image display capabilities for
the Anubis Axis measurement and calibration system on Raspberry Pi Pico 2.

The driver features hardware initialization, backlight PWM control, optimized text rendering,
and supports multiple image formats for comprehensive display functionality.

Author: Seguridad Física, based on the example provided by the manufacturer Waveshare.
File: drivers/lcd.py
"""

from machine import Pin, SPI, PWM   # Import hardware interaction classes from MicroPython
import framebuf # Import frame buffer handling
import time
from ui.logger import Logger # Import Logger for logging messages


class GC9A01ALCD(framebuf.FrameBuffer):
    """LCD controller class for GC9A01A-driven 1.28-inch circular display.

    This class inherits from framebuf.FrameBuffer and manages all aspects of the
    240x240 circular LCD display interaction. It provides SPI communication,
    hardware initialization, text rendering with caching, image display, and
    backlight PWM control optimized for MicroPython on Raspberry Pi Pico 2.

    The driver implements efficient memory management with text pattern caching
    and supports multiple rendering modes for responsive UI applications.

    Attributes:
        width (int): Display width in pixels (240 for GC9A01A).
        height (int): Display height in pixels (240 for GC9A01A).
        buffer (bytearray): Frame buffer memory for display contents (115,200 bytes).
        red (int): Red color constant in byte-swapped RGB565 format (0x00F8).
        green (int): Green color constant in byte-swapped RGB565 format (0xE007).
        blue (int): Blue color constant in byte-swapped RGB565 format (0x1F00).
        white (int): White color constant in byte-swapped RGB565 format (0xFFFF).
        black (int): Black color constant in byte-swapped RGB565 format (0x0000).
        cs (Pin): Chip Select pin object for SPI communication control.
        rst (Pin): Reset pin object for hardware reset operations.
        spi (SPI): SPI interface object configured for high-speed communication.
        dc (Pin): Data/Command pin object for protocol control.
        pwm (PWM): PWM object for backlight brightness control.
        logger (Logger): Logger instance for status and error reporting.
        _text_cache (dict): Internal cache for text rendering patterns.
        spi_baudrate (int): SPI communication speed in Hz (62.5 MHz).
    """
    
    def __init__(self, cs_pin, rst_pin, sck_pin, mosi_pin, dc_pin, bl_pin, width=240, height=240):
        """Initialize the GC9A01ALCD instance with hardware configuration.

        Sets up SPI communication at 62.5MHz, configures GPIO pins, initializes
        the display controller, and establishes PWM backlight control. The
        initialization includes a complete display setup sequence and framebuffer
        allocation for efficient graphics operations.

        Args:
            cs_pin (int): GPIO pin number for SPI Chip Select control.
            rst_pin (int): GPIO pin number for hardware reset control.
            sck_pin (int): GPIO pin number for SPI Serial Clock.
            mosi_pin (int): GPIO pin number for SPI Master Out Slave In data.
            dc_pin (int): GPIO pin number for Data/Command protocol control.
            bl_pin (int): GPIO pin number for PWM backlight control.
            width (int, optional): Display width in pixels. Defaults to 240.
            height (int, optional): Display height in pixels. Defaults to 240.

        Examples:
            >>> # Initialize LCD with standard pinout for Anubis Axis
            >>> lcd = GC9A01ALCD(cs_pin=9, rst_pin=13, sck_pin=10, mosi_pin=11, 
            ...                  dc_pin=8, bl_pin=25)
            >>> lcd.fill(lcd.black)  # Clear screen to black
            >>> lcd.show()  # Update display
        """
        self.logger = Logger()
        self.width = width
        self.height = height

        # Define colors in byte-swapped RGB565 format for GC9A01A compatibility
        self.red   =   0x00f8  # Red with byte swap applied
        self.blue  =   0x1f00  # Blue with byte swap applied
        self.white =   0xffff  # White (same in both endianness)
        self.black =   0x0000  # Black (same in both endianness)
        self.green =   0xe007  # Green with byte swap applied

        # Initialize SPI interface and control pins
        self.cs = Pin(cs_pin, Pin.OUT)
        self.rst = Pin(rst_pin, Pin.OUT)
        
        self.cs(1)  # Deselect device initially
        self.spi_baudrate = 62_500_000  # 62.5 MHz for fast refresh rates
        self.spi = SPI(1, baudrate=self.spi_baudrate, polarity=0, phase=0, bits=8,
                       sck=Pin(sck_pin), mosi=Pin(mosi_pin), miso=None)
        
        # Log SPI initialization for diagnostics
        self.logger.console_printing("INFO", f"SPI initialized. Baudrate: {self.spi_baudrate/1_000_000:.1f} MHz")
        
        self.dc = Pin(dc_pin, Pin.OUT)
        self.dc(1)  # Set to data mode initially
        
        # Allocate framebuffer: 240*240*2 bytes = 115,200 bytes
        self.buffer = bytearray(self.height * self.width * 2)
        
        # Initialize parent FrameBuffer class with RGB565 format
        super().__init__(self.buffer, self.width, self.height, framebuf.RGB565)

        # Initialize display hardware and verify successful setup
        if self.init_display() == True:
            self.logger.console_printing("INFO", "Display initialized correctly.")
        else:
            self.logger.console_printing("ERROR", "Error initializing display.")
                        
        self.fill(self.black)  # Clear screen to black
        self.show()  # Update display with cleared buffer

        # Initialize text rendering cache for performance optimization
        self._text_cache = {}

        # Configure PWM backlight control at 5kHz frequency
        self.pwm = PWM(Pin(bl_pin))
        self.pwm.freq(5000)  # 5kHz PWM frequency to avoid visible flicker

    def write_cmd(self, cmd):
        """Send a command byte to the GC9A01A display controller.

        Sets the DC pin low to indicate command mode, selects the device,
        transmits the command byte via SPI, and deselects the device.

        Args:
            cmd (int): Command byte to send to the display controller (0x00-0xFF).

        Examples:
            >>> lcd.write_cmd(0x29)  # Send display on command
        """
        self.cs(1)
        self.dc(0)  # Set to command mode
        self.cs(0)  # Select device
        self.spi.write(bytearray([cmd]))
        self.cs(1)  # Deselect device

    def write_data(self, buf):
        """Send a data byte to the GC9A01A display controller.

        Sets the DC pin high to indicate data mode, selects the device,
        transmits the data byte via SPI, and deselects the device.

        Args:
            buf (int): Data byte to send to the display controller (0x00-0xFF).

        Examples:
            >>> lcd.write_data(0x05)  # Send RGB565 pixel format data
        """
        self.cs(1)
        self.dc(1)  # Set to data mode
        self.cs(0)  # Select device
        self.spi.write(bytearray([buf]))
        self.cs(1)  # Deselect device
        
    def set_bl_pwm(self, duty):
        """Set the LCD backlight brightness using PWM duty cycle.

        Controls the backlight intensity by adjusting the PWM duty cycle.
        Higher values result in brighter display, lower values dim the display.

        Args:
            duty (int): PWM duty cycle value for brightness control (0-65535).
                - 0: Backlight off (minimum brightness)
                - 32768: 50% brightness (medium)
                - 65535: Maximum brightness (100%)

        Examples:
            >>> lcd.set_bl_pwm(32768)  # Set to 50% brightness
            >>> lcd.set_bl_pwm(0)      # Turn off backlight
            >>> lcd.set_bl_pwm(65535)  # Maximum brightness
        """
        self.pwm.duty_u16(duty)  # Set PWM duty cycle (max 65535)
        
    def init_display(self):
        """Initialize the GC9A01A display controller with configuration sequence.

        Performs a hardware reset and sends the complete initialization sequence
        required by the GC9A01A controller. This includes power settings, gamma
        correction, display mode configuration, and activation commands.

        The initialization sequence is based on the manufacturer's specifications
        and optimizes the display for 240x240 resolution with RGB565 color format.

        Returns:
            bool: True if initialization sequence completed successfully.

        Examples:
            >>> if lcd.init_display():
            >>>     print("Display ready for use")
        """ 
        # Perform hardware reset sequence
        self.rst(1)
        time.sleep(0.01)
        self.rst(0)  # Assert reset for 10ms
        time.sleep(0.01)
        self.rst(1)  # Release reset
        time.sleep(0.05)  # Wait for controller to stabilize
        
        # Send GC9A01A initialization sequence based on datasheet
        self.write_cmd(0xEF)  # Enable test command
        self.write_cmd(0xEB)
        self.write_data(0x14) 
        
        self.write_cmd(0xFE)  # Inter register enable1
        self.write_cmd(0xEF)  # Inter register enable2

        self.write_cmd(0xEB)
        self.write_data(0x14) 

        self.write_cmd(0x84)  # Source setting
        self.write_data(0x40) 

        self.write_cmd(0x85)  # Source setting
        self.write_data(0xFF) 

        self.write_cmd(0x86)  # Source setting
        self.write_data(0xFF) 

        self.write_cmd(0x87)  # Source setting
        self.write_data(0xFF)

        self.write_cmd(0x88)  # Source setting
        self.write_data(0x0A)

        self.write_cmd(0x89)  # Source setting
        self.write_data(0x21) 

        self.write_cmd(0x8A)  # Source setting
        self.write_data(0x00) 

        self.write_cmd(0x8B)  # Source setting
        self.write_data(0x80) 

        self.write_cmd(0x8C)  # Source setting
        self.write_data(0x01) 

        self.write_cmd(0x8D)  # Source setting
        self.write_data(0x01) 

        self.write_cmd(0x8E)  # Source setting
        self.write_data(0xFF) 

        self.write_cmd(0x8F)  # Source setting
        self.write_data(0xFF) 

        self.write_cmd(0xB6)  # Display function control
        self.write_data(0x00)  # Bypass
        self.write_data(0x20)  # Source Output Scan from S1 to S360, Gate Output scan from G1 to G32, scan cycle=2

        self.write_cmd(0x36)  # Memory access control
        self.write_data(0x98)  # MX, MY, RGB mode

        self.write_cmd(0x3A)  # COLMOD: Pixel format set
        self.write_data(0x05)  # 16bit/pixel RGB565

        self.write_cmd(0x90)  # Entry mode set
        self.write_data(0x08)
        self.write_data(0x08)
        self.write_data(0x08)
        self.write_data(0x08) 

        self.write_cmd(0xBD)  # ???
        self.write_data(0x06)
        
        self.write_cmd(0xBC)  # ???
        self.write_data(0x00)

        self.write_cmd(0xFF)  # Set Commands in Manufacturer command set
        self.write_data(0x60)
        self.write_data(0x01)
        self.write_data(0x04)

        self.write_cmd(0xC3)  # Vreg1a voltage Control
        self.write_data(0x13)
        self.write_cmd(0xC4)  # Vreg1b voltage Control
        self.write_data(0x13)

        self.write_cmd(0xC9)  # Vreg2a voltage Control
        self.write_data(0x22)

        self.write_cmd(0xBE)  # VCOM Control 
        self.write_data(0x11) 

        self.write_cmd(0xE1)  # Set Source pre_drive timing
        self.write_data(0x10)
        self.write_data(0x0E)

        self.write_cmd(0xDF)  # Set Gate drive timing
        self.write_data(0x21)
        self.write_data(0x0c)
        self.write_data(0x02)

        # Gamma correction settings for optimal color reproduction
        self.write_cmd(0xF0)   # Set Gamma1
        self.write_data(0x45)
        self.write_data(0x09)
        self.write_data(0x08)
        self.write_data(0x08)
        self.write_data(0x26)
        self.write_data(0x2A)

        self.write_cmd(0xF1)   # Set Gamma2
        self.write_data(0x43)
        self.write_data(0x70)
        self.write_data(0x72)
        self.write_data(0x36)
        self.write_data(0x37)  
        self.write_data(0x6F)

        self.write_cmd(0xF2)   # Set Gamma3
        self.write_data(0x45)
        self.write_data(0x09)
        self.write_data(0x08)
        self.write_data(0x08)
        self.write_data(0x26)
        self.write_data(0x2A)

        self.write_cmd(0xF3)   # Set Gamma4
        self.write_data(0x43)
        self.write_data(0x70)
        self.write_data(0x72)
        self.write_data(0x36)
        self.write_data(0x37) 
        self.write_data(0x6F)

        self.write_cmd(0xED)  # ???
        self.write_data(0x1B) 
        self.write_data(0x0B) 

        self.write_cmd(0xAE)  # ???
        self.write_data(0x77)
        
        self.write_cmd(0xCD)  # ???
        self.write_data(0x63)

        self.write_cmd(0x70)  # ???
        self.write_data(0x07)
        self.write_data(0x07)
        self.write_data(0x04)
        self.write_data(0x0E) 
        self.write_data(0x0F) 
        self.write_data(0x09)
        self.write_data(0x07)
        self.write_data(0x08)
        self.write_data(0x03)

        self.write_cmd(0xE8)  # Frame rate
        self.write_data(0x34)

        # Display timing and synchronization settings
        self.write_cmd(0x62)
        self.write_data(0x18)
        self.write_data(0x0D)
        self.write_data(0x71)
        self.write_data(0xED)
        self.write_data(0x70) 
        self.write_data(0x70)
        self.write_data(0x18)
        self.write_data(0x0F)
        self.write_data(0x71)
        self.write_data(0xEF)
        self.write_data(0x70) 
        self.write_data(0x70)

        self.write_cmd(0x63)
        self.write_data(0x18)
        self.write_data(0x11)
        self.write_data(0x71)
        self.write_data(0xF1)
        self.write_data(0x70) 
        self.write_data(0x70)
        self.write_data(0x18)
        self.write_data(0x13)
        self.write_data(0x71)
        self.write_data(0xF3)
        self.write_data(0x70) 
        self.write_data(0x70)

        self.write_cmd(0x64)
        self.write_data(0x28)
        self.write_data(0x29)
        self.write_data(0xF1)
        self.write_data(0x01)
        self.write_data(0xF1)
        self.write_data(0x00)
        self.write_data(0x07)

        self.write_cmd(0x66)
        self.write_data(0x3C)
        self.write_data(0x00)
        self.write_data(0xCD)
        self.write_data(0x67)
        self.write_data(0x45)
        self.write_data(0x45)
        self.write_data(0x10)
        self.write_data(0x00)
        self.write_data(0x00)
        self.write_data(0x00)

        self.write_cmd(0x67)
        self.write_data(0x00)
        self.write_data(0x3C)
        self.write_data(0x00)
        self.write_data(0x00)
        self.write_data(0x00)
        self.write_data(0x01)
        self.write_data(0x54)
        self.write_data(0x10)
        self.write_data(0x32)
        self.write_data(0x98)

        self.write_cmd(0x74)
        self.write_data(0x10)
        self.write_data(0x85)
        self.write_data(0x80)
        self.write_data(0x00) 
        self.write_data(0x00) 
        self.write_data(0x4E)
        self.write_data(0x00)
        
        self.write_cmd(0x98)
        self.write_data(0x3e)
        self.write_data(0x07)

        self.write_cmd(0x35)  # Tearing effect line on
        self.write_cmd(0x21)  # Display inversion on

        self.write_cmd(0x11)  # Sleep out
        self.write_cmd(0x29)  # Display on
        
        return True
      
    def setWindows(self, Xstart, Ystart, Xend, Yend):
        """Set the active display window for subsequent pixel data writes.

        Configures the column and page address ranges where the next pixel data
        will be written. This is essential for partial screen updates and
        optimized rendering operations.

        Args:
            Xstart (int): Starting X coordinate (0-239).
            Ystart (int): Starting Y coordinate (0-239).
            Xend (int): Ending X coordinate (1-240, exclusive).
            Yend (int): Ending Y coordinate (1-240, exclusive).

        Examples:
            >>> # Set window for full screen update
            >>> lcd.setWindows(0, 0, 240, 240)
            >>> # Set window for partial update (top-left quadrant)
            >>> lcd.setWindows(0, 0, 120, 120)
        """
        # Set column address range
        self.write_cmd(0x2A)  # Column Address Set
        self.write_data(0x00)
        self.write_data(Xstart)
        self.write_data(0x00)
        self.write_data(Xend-1)  # End address is inclusive
        
        # Set page address range
        self.write_cmd(0x2B)  # Page Address Set
        self.write_data(0x00)
        self.write_data(Ystart)
        self.write_data(0x00)
        self.write_data(Yend-1)  # End address is inclusive
        
        self.write_cmd(0x2C)  # Memory Write command
       
    def show(self):
        """Transfer the complete framebuffer contents to the LCD display.

        Updates the entire 240x240 display with the current framebuffer contents.
        This method sets the full display window and transmits all 115,200 bytes
        of pixel data via SPI for complete screen refresh.

        Examples:
            >>> lcd.fill(lcd.blue)  # Fill buffer with blue
            >>> lcd.show()          # Update display to show blue screen
        """
        # Set window to full screen
        self.setWindows(0, 0, self.width, self.height)
        
        # Transfer complete framebuffer via SPI
        self.cs(1)
        self.dc(1)  # Set to data mode
        self.cs(0)  # Select device
        self.spi.write(self.buffer)  # Send all pixel data
        self.cs(1)  # Deselect device
    
    def Windows_show(self, Xstart, Ystart, Xend, Yend):
        """Display a specific rectangular region with boundary adjustments.

        Updates only a portion of the display by extracting the relevant pixels
        from the framebuffer. Applies automatic boundary adjustments with 10-pixel
        margins to ensure proper display window alignment.

        Args:
            Xstart (int): Starting X coordinate for the region.
            Ystart (int): Starting Y coordinate for the region.
            Xend (int): Ending X coordinate for the region.
            Yend (int): Ending Y coordinate for the region.

        Examples:
            >>> # Update only the center region of display
            >>> lcd.Windows_show(60, 60, 180, 180)
        """
        # Ensure proper coordinate ordering
        if Xstart > Xend:
            data = Xstart
            Xstart = Xend
            Xend = data
            
        if (Ystart > Yend):        
            data = Ystart
            Ystart = Yend
            Yend = data
            
        # Apply minimum boundary constraints
        if Xstart <= 10:
            Xstart = 10
        if Ystart <= 10:
            Ystart = 10
            
        # Apply 10-pixel margins for display window alignment
        Xstart -= 10; Xend += 10
        Ystart -= 10; Yend += 10
        
        # Set display window for partial update
        self.setWindows(Xstart, Ystart, Xend, Yend)      
        self.cs(1)
        self.dc(1)  # Set to data mode
        self.cs(0)  # Select device
        
        # Send pixel data row by row for the specified region
        for i in range(Ystart, Yend-1):             
            Addr = (Xstart * 2) + (i * 240 * 2)  # Calculate framebuffer address (2 bytes per pixel)
            self.spi.write(self.buffer[Addr : Addr+((Xend-Xstart)*2)])
        self.cs(1)  # Deselect device
        
    def write_text(self, text, x, y, size, color):
        """Render scaled text on the display using pixel manipulation.

        Draws text at the specified position with variable size scaling by first
        rendering at 1x scale, sampling the pixel pattern, and then redrawing
        at the desired scale factor. This method provides flexible text sizing
        but is computationally intensive for frequent updates.

        Args:
            text (str): The string to display on the screen.
            x (int): X coordinate for the text starting position (0-239).
            y (int): Y coordinate for the text starting position (0-239).
            size (int): Font size multiplier (minimum 1, typical range 1-4).
            color (int): Text color in RGB565 format.

        Examples:
            >>> lcd.write_text("Hello", 10, 10, 2, lcd.white)  # 2x size white text
            >>> lcd.write_text("Status", 0, 220, 1, lcd.green)  # 1x size green text
        """
        background = self.pixel(x, y)  # Sample background color for cleanup
        info = []
        
        # Render reference text at 1x scale to determine pixel pattern
        self.text(text, x, y, color)
        
        # Sample all pixels in the text area (8x8 pixels per character)
        for i in range(x, x+(8*len(text))):
            for j in range(y, y+8):
                px_color = self.pixel(i, j)
                # Store pixel coordinates and color if it matches text color
                info.append((i, j, px_color)) if px_color == color else None
                
        # Clear the reference text by restoring background
        self.text(text, x, y, background)
        
        # Render scaled text using the sampled pixel pattern
        for px_info in info:
            # Calculate scaled position and draw size x size rectangle for each original pixel
            self.fill_rect(size*px_info[0] - (size-1)*x, size*px_info[1] - (size-1)*y, 
                          size, size, px_info[2])

    def write_text_cached(self, text, x, y, size, color):
        """Render scaled text using cached patterns for improved performance.
        
        This method uses a dictionary cache (_text_cache) to store the list of
        relative pixel positions that make up the text in the original 8x8 font.
        If the same text is drawn again with the same parameters, it reuses the
        precalculated pattern instead of iterating over each pixel, significantly
        improving performance for dynamic content updates.
        
        Args:
            text (str): Text string to display.
            x (int): X coordinate where text is positioned.
            y (int): Y coordinate where text is positioned.
            size (int): Scale factor (minimum 1).
            color (int): Text color in RGB565 format.

        Examples:
            >>> # Cached rendering for frequently updated values
            >>> lcd.write_text_cached("42.5°", 100, 100, 3, lcd.white)
        """
        # Define cache key (text, size and color)
        cache_key = (text, size, color)
        if cache_key in self._text_cache:
            glyphs = self._text_cache[cache_key]
        else:
            glyphs = []
            # Get background color to clean reference text
            background = self.pixel(x, y)
            # Draw text with original method to get pattern
            self.text(text, x, y, color)
            # Iterate through text area (standard 8x8 font)
            for i in range(x, x + 8 * len(text)):
                for j in range(y, y + 8):
                    if self.pixel(i, j) == color:
                        # Store relative position relative to (x, y)
                        glyphs.append((i - x, j - y))
            # Clean reference text by restoring background
            self.text(text, x, y, background)
            # Save pattern in cache
            self._text_cache[cache_key] = glyphs

        # Draw scaled text using precalculated pattern
        for rel_x, rel_y in glyphs:
            scaled_x = size * rel_x + x
            scaled_y = size * rel_y + y
            self.fill_rect(scaled_x, scaled_y, size, size, color)

    def clear_text_cache(self):
        """Clear the text rendering cache to free memory.
        
        Call this method when transitioning between screens to avoid 
        keeping unnecessary text pattern data in memory. Essential for
        memory management in long-running applications on Pico 2.
        
        Examples:
            >>> lcd.clear_text_cache()  # Free cached text patterns
        """
        self._text_cache = {}

    def byte_swap_rgb565(self, value):
        """Swap byte order in RGB565 values for GC9A01A compatibility.

        In MicroPython, when using a frame buffer with RGB565 format, data is stored 
        in little-endian order (least significant byte first). However, the GC9A01A
        controller expects data in big-endian format (most significant byte first).
        
        This byte order discrepancy causes colors to display incorrectly (red appears 
        as blue and vice versa). This function reverses the byte order to ensure 
        correct color interpretation by the display controller.

        Args:
            value (int): Original RGB565 value in little-endian format.

        Returns:
            int: RGB565 value with bytes swapped for big-endian format.

        Examples:
            >>> # Convert standard RGB565 colors for display
            >>> red_swapped = lcd.byte_swap_rgb565(0xF800)    # Returns 0x00F8
            >>> green_swapped = lcd.byte_swap_rgb565(0x07E0)  # Returns 0xE007
            >>> blue_swapped = lcd.byte_swap_rgb565(0x001F)   # Returns 0x1F00
        """
        return ((value & 0xFF) << 8) | ((value >> 8) & 0xFF)

    def draw_rgb565_data(self, img_data, x=0, y=0, width=None, height=None):
        """Blit an RGB565 image already encoded in framebuffer-native byte order.

        Copies pixel bytes directly into the framebuffer with a row-level memcpy,
        without any per-pixel color math. img_data must already contain the same
        byte order the framebuffer stores internally (2 bytes per pixel, high byte
        of the byte-swapped RGB565 value first) - i.e. the output produced by
        tools/convert_image_to_rgb565.py. This avoids per-pixel Python loops, which
        are the main bottleneck when rendering full-screen images on MicroPython.

        Args:
            img_data (bytes-like): Image data in framebuffer-native RGB565 byte order.
            x (int, optional): X position where image will be drawn. Defaults to 0.
            y (int, optional): Y position where image will be drawn. Defaults to 0.
            width (int, optional): Image width in pixels. Defaults to display width.
            height (int, optional): Image height in pixels. Defaults to display height.

        Examples:
            >>> # Draw a small icon from a frozen/in-memory buffer
            >>> lcd.draw_rgb565_data(icon_bytes, x=50, y=50, width=32, height=32)
        """
        width = width or self.width
        height = height or self.height
        row_bytes = width * 2
        buf_mv = memoryview(self.buffer)

        # Fast path: image spans the full framebuffer width, so every row is
        # contiguous in the buffer and the whole image is a single memcpy.
        if x == 0 and width == self.width and 0 <= y and y + height <= self.height:
            offset = y * self.width * 2
            buf_mv[offset:offset + row_bytes * height] = img_data[:row_bytes * height]
            return

        # General path: still one memcpy per row instead of one call per pixel.
        for row in range(height):
            dest_y = y + row
            if not (0 <= dest_y < self.height):
                continue
            src_offset = row * row_bytes
            start_col = max(0, -x)
            end_col = min(width, self.width - x)
            if end_col <= start_col:
                continue
            length = (end_col - start_col) * 2
            dest_offset = (dest_y * self.width + x + start_col) * 2
            src_start = src_offset + start_col * 2
            buf_mv[dest_offset:dest_offset + length] = img_data[src_start:src_start + length]

    def draw_bitmap_data(self, bitmap_data, x, y, color=None, width=None):
        """Draw a monochrome bitmap from memory data array.
        
        Renders a monochrome bitmap where each bit represents a pixel state.
        The bitmap_data should be a list of integers where each integer represents
        a row of pixels, with the most significant bit corresponding to the leftmost pixel.
        
        Args:
            bitmap_data (list): List of integers representing bitmap rows.
            x (int): X position where bitmap will be drawn.
            y (int): Y position where bitmap will be drawn.
            color (int, optional): Color for "on" pixels. Defaults to white.
            width (int, optional): Bitmap width in pixels. Inferred when omitted.

        Examples:
            >>> # Draw a simple 8x8 icon
            >>> icon = [0xFF, 0x81, 0x81, 0x81, 0x81, 0x81, 0x81, 0xFF]  # Square outline
            >>> lcd.draw_bitmap_data(icon, 100, 100, lcd.red)
        """
        if color is None:
            color = self.white
            
        # Calculate dimensions from bitmap data
        height = len(bitmap_data)
        
        # Calculate width by finding the number of bits in the largest row
        if width is None:
            width = 0
            for row_data in bitmap_data:
                if row_data > 0:  # Skip rows that are all zeros
                    # Find the position of the most significant set bit
                    bit_length = 0
                    temp = row_data
                    while temp > 0:
                        bit_length += 1
                        temp >>= 1
                    width = max(width, bit_length)
        
        # Draw each pixel of the bitmap
        for row in range(height):
            if row < len(bitmap_data):
                row_data = bitmap_data[row]
                for col in range(width):
                    bit_pos = width - 1 - col  # MSB is leftmost pixel
                    if (row_data >> bit_pos) & 1:  # Check if bit is set
                        self.pixel(x + col, y + row, color)

    def draw_rgb565_file(self, filename, x=0, y=0, width=None, height=None):
        """Load and display an RGB565 binary image file.
        
        Reads a binary file containing raw RGB565 pixel data, in the same
        framebuffer-native byte order the display expects (produced by
        tools/convert_image_to_rgb565.py), and blits it with a row-level memcpy -
        no per-pixel color math or intermediate conversion at runtime.
        
        Args:
            filename (str): Path to the RGB565 binary image file.
            x (int, optional): X position for image placement. Defaults to 0.
            y (int, optional): Y position for image placement. Defaults to 0.
            width (int, optional): Image width. Calculated from file size if None.
            height (int, optional): Image height. Calculated from file size if None.
        
        Returns:
            bool: True if image loaded successfully, False on error.

        Examples:
            >>> # Load a full-screen background image
            >>> success = lcd.draw_rgb565_file("background.rgb565", 0, 0, 240, 240)
            >>> if not success:
            >>>     print("Failed to load background image")
        """
        try:
            with open(filename, 'rb') as f:
                # Calculate dimensions if not provided (needs the file size)
                if width is None or height is None:
                    file_pos = f.tell()
                    f.seek(0, 2)
                    total_pixels = f.tell() // 2  # 2 bytes per pixel
                    f.seek(file_pos)
                    if width is None and height is None:
                        # Default to square aspect ratio
                        width = height = int(total_pixels ** 0.5)
                    elif width is None:
                        width = total_pixels // height
                    elif height is None:
                        height = total_pixels // width

                # Fallbacks so the type is always a concrete int from here on
                if width is None:
                    width = self.width
                if height is None:
                    height = self.height

                row_bytes = width * 2
                buf_mv = memoryview(self.buffer)

                # Fast path: full framebuffer width means the whole image is
                # contiguous in the buffer, so it can be read in a single call.
                if x == 0 and width == self.width and 0 <= y and y + height <= self.height:
                    offset = y * self.width * 2
                    f.readinto(buf_mv[offset:offset + row_bytes * height])
                    return True

                # General path: one read + one memcpy per row instead of one
                # Python call (and byte-order math) per pixel.
                row_buf = bytearray(row_bytes)
                for row in range(height):
                    dest_y = y + row
                    if not (0 <= dest_y < self.height):
                        f.seek(row_bytes, 1)  # Skip this row in the file
                        continue
                    f.readinto(row_buf)
                    start_col = max(0, -x)
                    end_col = min(width, self.width - x)
                    if end_col <= start_col:
                        continue
                    length = (end_col - start_col) * 2
                    dest_offset = (dest_y * self.width + x + start_col) * 2
                    src_start = start_col * 2
                    buf_mv[dest_offset:dest_offset + length] = row_buf[src_start:src_start + length]

            return True
        except Exception as e:
            self.logger.console_printing("ERROR", f"Failed to load image {filename}: {e}")
            return False

    def draw_bmp_file(self, filename, x=0, y=0, color=None):
        """Load and display a monochrome BMP image file.
        
        Reads a 1-bit (monochrome) BMP file and displays it on the screen.
        The BMP file must be in 1-bit per pixel format with standard BMP
        header structure. Black pixels in the BMP are rendered in the specified color.
        
        Args:
            filename (str): Path to the monochrome BMP file.
            x (int, optional): X position for image placement. Defaults to 0.
            y (int, optional): Y position for image placement. Defaults to 0.
            color (int, optional): Color for "black" pixels in BMP. Defaults to white.
        
        Returns:
            bool: True if BMP loaded successfully, False on error.

        Examples:
            >>> # Load a monochrome icon
            >>> success = lcd.draw_bmp_file("icon.bmp", 50, 50, lcd.blue)
            >>> if success:
            >>>     lcd.show()  # Update display
        """
        try:
            if color is None:
                color = self.white
                
            # Read and validate BMP file
            with open(filename, 'rb') as f:
                # Read BMP file header (14 bytes)
                header = f.read(14)
                if header[0:2] != b'BM':
                    self.logger.console_printing("ERROR", "Not a valid BMP file")
                    return False
                    
                # Read DIB header size
                dib_header_size = int.from_bytes(f.read(4), 'little')
                
                # Read image dimensions from DIB header
                width = int.from_bytes(f.read(4), 'little')
                height = int.from_bytes(f.read(4), 'little')
                
                # Check bit depth (must be 1 for monochrome)
                f.seek(14 + 12)
                bit_depth = int.from_bytes(f.read(2), 'little')
                
                if bit_depth != 1:
                    self.logger.console_printing("ERROR", f"Only monochrome BMP supported (got {bit_depth} bpp)")
                    return False
                    
                # Seek to pixel data start
                f.seek(int.from_bytes(header[10:14], 'little'))
                
                # Calculate row size (padded to 4-byte boundary)
                row_size = (width + 31) // 32 * 4
                
                # Process each row (BMP stores rows bottom-to-top)
                for row in range(0, height):
                    # Calculate file position for this row
                    current_pos = int.from_bytes(header[10:14], 'little') + (height - 1 - row) * row_size
                    f.seek(current_pos)
                    
                    row_data = f.read(row_size)
                    
                    # Process each byte (8 pixels per byte)
                    for byte_idx in range(min(row_size, (width + 7) // 8)):
                        byte = row_data[byte_idx]
                        
                        # Process each bit in the byte
                        for bit_idx in range(min(8, width - byte_idx * 8)):
                            # Check if pixel is "black" (0 bit value in BMP)
                            is_set = (byte & (0x80 >> bit_idx)) == 0
                            
                            if is_set:
                                # Calculate pixel position and draw
                                pixel_x = x + byte_idx * 8 + bit_idx
                                pixel_y = y + row
                                
                                if 0 <= pixel_x < self.width and 0 <= pixel_y < self.height:
                                    self.pixel(pixel_x, pixel_y, color)
                
                return True
        except Exception as e:
            self.logger.console_printing("ERROR", f"Failed to load BMP {filename}: {e}")
            return False