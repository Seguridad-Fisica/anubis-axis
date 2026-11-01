"""
Touchscreen driver module for Anubis Axis project.

This module provides the CST816TTouchScreen class for managing interaction with the CST816T
capacitive touch controller chip used in the 1.28" LCD display module. It implements I2C
communication protocol, gesture recognition, and touch coordinate detection for the
Anubis Axis measurement and calibration system on Raspberry Pi Pico 2.

The driver supports multiple operation modes and provides interrupt-driven touch detection
for responsive user interface interactions.

Author: Seguridad Física based on the example provided by the manufacturer Waveshare.
File: drivers/touchscreen.py
"""

from machine import Pin, I2C, Timer # Import hardware interaction classes from MicroPython
from ui.logger import Logger # Import Logger for logging messages
import time # Import time functions

class CST816TTouchScreen:
    """Touchscreen controller driver for the CST816T capacitive touch chip.

    This class implements a comprehensive driver for the CST816T touch control chip,
    providing I2C communication, gesture recognition, touch point detection, and
    interrupt handling. It supports three operation modes for different UI interaction
    patterns in the Anubis Axis system.

    The driver handles hardware initialization, chip identification, and provides
    both polling and interrupt-driven touch detection methods optimized for
    MicroPython on Raspberry Pi Pico 2.

    Attributes:
        _bus (I2C): I2C bus instance for communication with the touch controller.
        _address (int): I2C address of the touch control chip (default 0x15).
        int (Pin): Interrupt pin object for touch event notifications.
        tim (Timer): Timer instance for managing touch event timing.
        rst (Pin): Reset pin object for hardware reset operations.
        Mode (int): Current operation mode (0=Gesture, 1=Point, 2=Mixed).
        Gestures (str or int): Last detected gesture code or "None".
        Flag (int): Touch event flag for polling mode operation.
        Flgh (int): Additional touch event flag for internal state tracking.
        l (int): Counter for timer callback operations.
        X_point (int): X-coordinate of the current touch point (0-240 pixels).
        Y_point (int): Y-coordinate of the current touch point (0-240 pixels).
        last_gesture (int): Previous gesture code for duplicate detection.
        gesture_active (bool): Flag indicating if a gesture is currently active.
        logger (Logger): Logger instance for status and error reporting.
    """
    
    def __init__(self, i2c_sda, i2c_scl, int_pin, rst_pin, address=0x15, mode=0, i2c_num=1):
        """Initialize the CST816TTouchScreen instance with hardware configuration.

        Sets up I2C communication, configures GPIO pins, performs hardware reset,
        verifies chip presence, and initializes the touch controller for operation.
        The initialization process includes chip identification and wake-up sequence.

        Args:
            i2c_sda (int): SDA pin number for I2C bus communication.
            i2c_scl (int): SCL pin number for I2C bus communication.
            int_pin (int): Interrupt pin number for touch event notifications.
            rst_pin (int): Reset pin number for hardware reset control.
            address (int, optional): I2C slave address of the touch chip. Defaults to 0x15.
            mode (int, optional): Initial operation mode. Defaults to 0.
                0: Gesture mode - Only detects swipe and tap gestures
                1: Point mode - Only detects touch coordinates
                2: Mixed mode - Detects both gestures and coordinates
            i2c_num (int, optional): I2C bus number to use. Defaults to 1.

        Raises:
            Returns None if touch controller is not detected during initialization.

        Examples:
            >>> # Initialize touchscreen for Anubis Axis interface
            >>> touch = CST816TTouchScreen(i2c_sda=6, i2c_scl=7, int_pin=21, rst_pin=22, mode=2)
        """
        self.logger = Logger()
        
        # Initialize I2C bus with 400kHz frequency for reliable communication
        self._bus = I2C(id=i2c_num, scl=Pin(i2c_scl), sda=Pin(i2c_sda), freq=400_000)
        self._address = address  # Set CST816T I2C slave address
        
        # Configure interrupt pin with pull-up for touch event detection
        self.int = Pin(int_pin, Pin.IN, Pin.PULL_UP)
        self.tim = Timer()  # Timer for touch event management
        self.rst = Pin(rst_pin, Pin.OUT)  # Reset pin for hardware control
        
        # Perform hardware reset sequence
        self.Reset()
        
        # Verify chip presence and get revision information
        bRet = self.WhoAmI()
        if bRet:
            Rev = self.Read_Revision()
            self.logger.console_printing("INFO", f"Detected CST816T. CST816T Revision = {Rev}")
            self.Stop_Sleep()  # Wake up chip from sleep mode
        else:
            self.logger.console_printing("ERROR", "Touch screen not detected.")
            return None
        
        # Initialize operation parameters and state variables
        self.Mode = mode
        self.Gestures = "None"
        self.Flag = self.Flgh = self.l = 0
        self.X_point = self.Y_point = 0
        self.last_gesture = None
        self.gesture_active = False
        
        # Configure interrupt handler for falling edge detection
        self.int.irq(handler=self.Int_Callback, trigger=Pin.IRQ_FALLING)

    def _read_byte(self, cmd):
        """Read a single byte from a specific register of the touch controller.

        Performs I2C read operation to retrieve data from the specified register
        address of the CST816T chip.

        Args:
            cmd (int): Register address to read from (0x00-0xFF range).

        Returns:
            int: Value of the byte read from the specified register.

        Examples:
            >>> # Read chip ID register
            >>> chip_id = touch._read_byte(0xA7)
            >>> print(f"Chip ID: 0x{chip_id:02X}")
        """
        rec = self._bus.readfrom_mem(int(self._address), int(cmd), 1)
        return rec[0]
    
    def _read_block(self, reg, length=1):
        """Read a block of consecutive bytes from the touch controller.

        Performs bulk I2C read operation to retrieve multiple bytes starting
        from the specified register address. Efficient for reading coordinate
        data and multi-byte values.

        Args:
            reg (int): Starting register address to read from.
            length (int, optional): Number of consecutive bytes to read. Defaults to 1.

        Returns:
            bytearray: Array of bytes read from consecutive registers.

        Examples:
            >>> # Read touch coordinates (4 bytes starting from 0x03)
            >>> coord_data = touch._read_block(0x03, 4)
            >>> print([f"0x{b:02X}" for b in coord_data])
        """
        rec = self._bus.readfrom_mem(int(self._address), int(reg), length)
        return rec
    
    def _write_byte(self, cmd, val):
        """Write a single byte to a specific register of the touch controller.

        Performs I2C write operation to set configuration or control values
        in the specified register of the CST816T chip.

        Args:
            cmd (int): Register address to write to (0x00-0xFF range).
            val (int): Value to write to the register (0x00-0xFF range).

        Examples:
            >>> # Set touch controller to sleep mode
            >>> touch._write_byte(0xFE, 0x03)
        """
        self._bus.writeto_mem(int(self._address), int(cmd), bytes([int(val)]))

    def WhoAmI(self):
        """Verify the presence and identity of the CST816T touch controller.

        Reads the chip identification register and compares it with the expected
        value to confirm proper I2C communication and chip presence.

        Returns:
            bool: True if the chip responds with correct ID (0xB5), False otherwise.

        Examples:
            >>> if touch.WhoAmI():
            >>>     print("CST816T detected successfully")
            >>> else:
            >>>     print("Touch controller not found")
        """
        if (0xB5) != self._read_byte(0xA7):  # Check chip ID register
            return False
        return True
    
    def Read_Revision(self):
        """Read the hardware revision number of the touch controller.

        Retrieves the chip revision information which can be useful for
        compatibility checking and debugging purposes.

        Returns:
            int: Hardware revision number of the CST816T chip.

        Examples:
            >>> revision = touch.Read_Revision()
            >>> print(f"Touch controller revision: {revision}")
        """
        return self._read_byte(0xA9)  # Read revision register
      
    def Stop_Sleep(self):
        """Wake up the touch controller from sleep mode for active operation.
        
        Sends the wake-up command to ensure the touchscreen is ready to detect
        inputs for the Anubis Axis interface. Essential during initialization and
        after any power-saving operations.

        Examples:
            >>> touch.Stop_Sleep()  # Ensure touchscreen is active
        """
        self._write_byte(0xFE, 0x01)  # Write wake-up command
    
    def Reset(self):
        """Perform hardware reset of the touch controller.

        Toggles the reset pin to perform a complete hardware reset of the
        CST816T chip. Essential for proper initialization and can be used
        to recover from error states or communication failures.

        Examples:
            >>> touch.Reset()  # Reset touch controller to initial state
        """
        self.rst(0)  # Assert reset (active low)
        time.sleep_ms(1)  # Hold reset for minimum required time
        self.rst(1)  # Release reset
        time.sleep_ms(50)  # Wait for chip to complete reset sequence
    
    def Set_Mode(self, mode, callback_time=10, rest_time=5): 
        """Configure the operation mode of the touch controller.

        Sets the touch controller to operate in different modes depending on
        the requirements of the current Anubis Axis interface context. Each mode
        optimizes the controller for specific types of user interactions.

        Args:
            mode (int): Operation mode to configure:
                0: Gesture mode - Only detects gestures (swipes, taps), no coordinates
                1: Point mode - Only detects touch coordinates, no gestures  
                2: Mixed mode - Detects both gestures and coordinates (recommended)
            callback_time (int, optional): Callback timing parameter. Defaults to 10.
            rest_time (int, optional): Rest timing parameter. Defaults to 5.

        Examples:
            >>> touch.Set_Mode(2)  # Set to Mixed mode for full UI interaction
            >>> touch.Set_Mode(0)  # Set to Gesture mode for simple navigation
        """
        if (mode == 1):      
            # Point mode - coordinates only
            self._write_byte(0xFA, 0X41)
            
        elif (mode == 2):
            # Mixed mode - both gestures and coordinates
            self._write_byte(0xFA, 0X71)
            self._write_byte(0xEC, 0x01)  # Enable gesture detection
        else:
            # Gesture mode - gestures only (default for mode 0)
            self._write_byte(0xFA, 0X11)
            self._write_byte(0xEC, 0X01)  # Enable gesture detection

    def get_point(self):
        """Read and update the current touch point coordinates.

        Reads the 4-byte coordinate data from the touch controller and extracts
        the X and Y position values. Updates the internal X_point and Y_point
        attributes with the current touch position.

        The coordinate system ranges from 0-240 for both X and Y axes,
        matching the 240x240 pixel LCD display dimensions.

        Examples:
            >>> touch.get_point()
            >>> print(f"Touch at: ({touch.X_point}, {touch.Y_point})")
        """
        # Read 4 bytes of coordinate data starting from register 0x03
        xy_point = self._read_block(0x03, 4)
        
        # Extract X coordinate from bytes 0 and 1 (12-bit value)
        x_point = ((xy_point[0] & 0x0f) << 8) + xy_point[1]
        # Extract Y coordinate from bytes 2 and 3 (12-bit value)
        y_point = ((xy_point[2] & 0x0f) << 8) + xy_point[3]
        
        # Update internal coordinate storage
        self.X_point = x_point
        self.Y_point = y_point
        
    def Int_Callback(self, pin):
        """Interrupt callback handler for touch events.

        Processes touch events based on the current operation mode when the
        interrupt pin is triggered. Handles gesture detection, coordinate
        reading, and state management for different interaction types.

        Args:
            pin (Pin): The interrupt pin object that triggered the callback.

        Note:
            This method is called automatically by the MicroPython interrupt
            system and should not be called directly by user code.
        """
        if self.Mode == 0:
            # Gesture mode - detect and process gestures only
            current_gesture = self._read_byte(0x01)  # Read gesture register
            touch_status = self._read_byte(0x02)     # Read touch status
            
            if current_gesture != 0:
                # Valid gesture detected
                if not self.gesture_active or current_gesture != self.last_gesture:
                    # New gesture or first detection
                    self.Gestures = current_gesture
                    self.last_gesture = current_gesture
                    self.gesture_active = True
            else:
                # No gesture detected, reset state
                self.gesture_active = False
                self.last_gesture = None
                self.Gestures = "None"

        elif self.Mode == 1:  
            # Point mode - detect coordinates only         
            self.Flag = 1  # Set touch event flag
            self.get_point()  # Read current touch coordinates
            
        elif self.Mode == 2:
            # Mixed mode - handle both gestures and coordinates
            current_gesture = self._read_byte(0x01)  # Read gesture register
            touch_status = self._read_byte(0x02)     # Read touch status
            
            # Process gesture detection similar to Mode 0
            if current_gesture != 0:
                if not self.gesture_active or current_gesture != self.last_gesture:
                    self.Gestures = current_gesture
                    self.last_gesture = current_gesture
                    self.gesture_active = True
            else:
                self.gesture_active = False
                self.last_gesture = None
                self.Gestures = "None"
                
            # Also read coordinates similar to Mode 1
            self.Flag = 1  # Set touch event flag
            self.get_point()  # Read current touch coordinates
    
    def get_gesture_state(self):
        """Get the current gesture state and reset it to prevent continuous triggering.
        
        Returns the current detected gesture and resets the internal gesture state
        to prevent the same gesture from being reported multiple times. This method
        should be called from the main application loop to poll for gestures.

        Returns:
            int or str: Current detected gesture code (0x01-0x0C) or "None" if no gesture.
                Common gesture codes:
                - 0x01: Swipe down
                - 0x02: Swipe up  
                - 0x03: Swipe left
                - 0x04: Swipe right
                - 0x05: Single click
                - 0x0B: Double click
                - 0x0C: Long press
        
        Examples:
            >>> gesture = touch.get_gesture_state()
            >>> if gesture == 0x01:
            >>>     print("Down swipe detected")
            >>> elif gesture == 0x05:
            >>>     print("Single tap detected")
        """
        gesture = self.Gestures
        # Reset the gesture state after reading to prevent continuous triggering
        if self.gesture_active:
            # Keep the gesture active but don't report it again
            self.Gestures = "None"
        return gesture

    def Timer_callback(self, t):
        """Timer callback for managing touch event timing and state cleanup.

        Increments an internal counter and resets it based on predefined thresholds
        to manage touch event timing. Can be used for implementing touch hold
        detection and gesture timeout functionality.

        Args:
            t (Timer): Timer instance that triggered the callback.

        Note:
            This method is called automatically by the Timer system and manages
            internal timing state for touch event processing.

        Examples:
            >>> # This method is called automatically by the timer
            >>> # No direct user interaction required
        """
        self.l += 1  # Increment timing counter
        if self.l > 100:
            self.l = 50  # Reset counter to prevent overflow