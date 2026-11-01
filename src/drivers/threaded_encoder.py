"""
AS5311 encoder driver with threaded reading for the Anubis Axis project.

This module provides a threaded interface for the AS5311 12-bit absolute magnetic encoder
on Raspberry Pi Pico 2. It implements continuous background reading using the SSI protocol
and provides virtual gear wheel simulation for advanced measurement applications.

The driver features automatic data validation, hysteresis filtering, and comprehensive
error handling optimized for MicroPython on the RP2350 microcontroller.

Author: Seguridad Física
File: drivers/threaded_encoder.py
"""

import _thread
import time
from machine import Pin
from ui.logger import Logger


class ThreadedAS5311Encoder:
    """Interface for the AS5311 magnetic encoder with threaded reading capabilities.

    This class provides a comprehensive interface for the AS5311 12-bit absolute encoder,
    implementing SSI protocol communication with continuous background reading via threading.
    It includes virtual gear wheel simulation, turn counting, and data validation with
    parity checking and status verification.

    The encoder operates in a separate thread to ensure non-blocking operation while
    providing real-time position data, delta calculations, and virtual wheel positions
    for complex measurement applications.

    Attributes:
        logger (Logger): Logger instance for status and error reporting.
        CSn (Pin): Chip Select pin (active low) for SSI communication.
        CLK (Pin): Clock pin for SSI data transmission timing.
        D0 (Pin): Data pin for receiving serial data from encoder.
        resolution (int): Encoder resolution in bits (default 12-bit = 4096 positions).
        max_reading (int): Maximum encoder value (2^resolution - 1).
        clk_delay (int): Clock delay in microseconds for SSI timing.
        hysteresis (int): Noise filtering threshold to avoid minor fluctuations.
        last_reading (int): Last valid encoder reading from SSI protocol.
        zero_offset (int): Zero point offset for measurement applications.
        value_lock (_thread.lock): Thread lock for safe data access.
        delay_s (float): Reading interval in seconds for background thread.
        _values_dict (dict): Dictionary containing all encoder values and metadata.
        _stop (bool): Flag to control background thread execution.
    """

    def __init__(self, CSn_pin, CLK_pin, D0_pin, resolution=12,
                 speed_hz=1800, hysteresis=1, delay_s=0.01):
        """Initialize the threaded AS5311 encoder with SSI communication setup.

        Configures GPIO pins, validates communication parameters, initializes the
        encoder hardware, and starts the background reading thread for continuous
        position monitoring.

        Args:
            CSn_pin (int): GPIO pin number for Chip Select (active low).
            CLK_pin (int): GPIO pin number for Clock signal generation.
            D0_pin (int): GPIO pin number for Data input from encoder.
            resolution (int, optional): Encoder resolution in bits. Defaults to 12.
            speed_hz (int, optional): SSI communication frequency. Defaults to 1800.
            hysteresis (int, optional): Noise filtering threshold. Defaults to 1.
            delay_s (float, optional): Background thread polling interval. Defaults to 0.01.

        Raises:
            Warning: If speed_hz is outside valid range (0-1MHz), uses 1MHz default.
        """
        self.logger = Logger()

        # Validate and configure SSI communication speed
        if speed_hz <= 0 or speed_hz > 1000000:
            self.logger.console_printing(
                "WARNING",
                "speed_hz must be greater than 0 and less or equal to 1,000,000 Hz. Using default value of 1MHz."
            )
            speed_hz = 1000000

        # Configure GPIO pins for SSI protocol
        self.CSn = Pin(CSn_pin, Pin.OUT)  # Chip Select (active low)
        self.CLK = Pin(CLK_pin, Pin.OUT)  # Clock signal
        self.D0 = Pin(D0_pin, Pin.IN)     # Data input

        # Set encoder parameters based on resolution
        self.resolution = resolution
        self.max_reading = (1 << resolution) - 1  # 2^12 - 1 = 4095 for 12-bit
        self.clk_delay = int(1.0 / speed_hz * 1e6)  # Convert Hz to microseconds
        self.hysteresis = hysteresis
        self.last_reading = None  # Last valid sensor reading
        self.zero_offset = 0
        self._first_CCW_turn_counted = False
        
        # Initialize encoder hardware with validation
        self._initialize()

        # Initialize thread synchronization
        self.value_lock = _thread.allocate_lock()
        
        # Initialize encoder values dictionary for comprehensive data tracking
        self._values_dict = {
            "dial": None,     # Current encoder position (0-4095)
            "delta": 0,       # Change since last reading
            "turns_drive": 0, # Complete revolution count
            "wheel_1": 0,     # Virtual gear wheel positions
            "wheel_2": 0,
            "wheel_3": 0,
            "wheel_4": 0,
            "timestamp": time.ticks_ms()  # Timestamp for velocity calculations
        }
        
        # Initialize turn detection variables
        self._previous_value = None
        self._threshold = self.max_reading * 0.75  # 75% threshold for wrap detection
        
        # Initialize virtual gear logic state variables
        self._new_data = 0
        self._old_data = 0
        self._first_read = True
        
        # Virtual wheel position tracking
        self._wheel_4_value = 0
        self._old_wheel_4_value = 0
        self._wheel_3_value = 0
        self._old_wheel_3_value = 0
        self._wheel_2_value = 0
        self._old_wheel_2_value = 0
        self._wheel_1_value = 0
        self._old_wheel_1_value = 0
        
        # Virtual pin states for gear direction logic
        self._right_pin_drive = True
        self._right_pin_w4 = True
        self._right_pin_w3 = True
        self._right_pin_w2 = True
        
        self.delay_s = delay_s  # Background thread reading interval
        self._stop = False

        # Start background reading thread for continuous monitoring
        _thread.start_new_thread(self._reading_loop, ())

    def _initialize(self):
        """Initialize encoder hardware with validation and error handling.

        Attempts to establish communication with the AS5311 encoder by performing
        multiple read attempts. Logs success or failure status for diagnostics.

        Raises:
            Error: Logs error if encoder cannot be initialized after maximum attempts.
        """
        max_attempts = 5
        valid_reading = None

        for attempt in range(1, max_attempts + 1):
            self._clock_high()
            valid_reading = self.read_ssi()
            if valid_reading is not None:
                self.logger.console_printing(
                    "INFO",
                    f"The encoder has been detected and is working properly, current value: {valid_reading}"
                )
                return
            else:
                self.logger.console_printing(
                    "WARNING",
                    f"Error initializing encoder, trying again... Attempt {attempt}/{max_attempts}."
                )
                time.sleep_ms(100)

        self.logger.console_printing(
            "ERROR",
            f"The encoder could not be initialized after: {max_attempts} attempts"
        )

    def _clock_high(self):
        """Set CLK pin high and apply configured timing delay.
        
        Essential for SSI protocol timing compliance with AS5311 specifications.
        """
        self.CLK.value(1)
        time.sleep_us(self.clk_delay)

    def _clock_low(self):
        """Set CLK pin low and apply configured timing delay.
        
        Completes the clock cycle for SSI data transmission.
        """
        self.CLK.value(0)
        time.sleep_us(self.clk_delay)

    def _read_bit(self):
        """Read a single data bit from the AS5311 encoder via SSI protocol.

        Performs a complete clock cycle and samples the data line at the
        appropriate timing for reliable data reception.

        Returns:
            int: The bit value read from D0 pin (0 or 1).
        """
        self._clock_high()
        bit = self.D0.value()
        self._clock_low()
        return bit

    def _check_hysteresis(self, new_reading):
        """Apply hysteresis filtering to reduce noise in encoder readings.

        Compares new reading with previous value to determine if the change
        is significant enough to update the position value.

        Args:
            new_reading (int): New encoder position value to validate.

        Returns:
            bool: True if change exceeds hysteresis threshold, False otherwise.
        """
        if self.last_reading is None:
            return True
        diff = abs(new_reading - self.last_reading)
        return diff > self.hysteresis

    def read_ssi(self):
        """Read encoder position using SSI protocol with comprehensive validation.

        Implements the complete SSI communication sequence including position
        reading, status bit validation, and parity checking as specified in
        the AS5311 datasheet.

        Returns:
            int or None: Valid encoder position (0-4095) or None if validation fails.
            
        Note:
            Returns None for invalid readings due to:
            - Parity check failure
            - OCF (Offset Compensation Finished) = 0
            - COF (CORDIC Overflow) = 1
            - Hysteresis filtering
        """
        # Activate encoder communication (CSn low)
        self.CSn.value(0)
        time.sleep_us(self.clk_delay)
        self.CLK.value(0)

        # Read position bits (MSB first for 12-bit resolution)
        position = 0
        for _ in range(self.resolution):
            position = (position << 1) | self._read_bit()

        # Read status bits: OCF, COF, LIN, MagINC, MagDEC
        status = 0
        for _ in range(5):
            status = (status << 1) | self._read_bit()

        # Read parity bit for error detection
        parity_bit = self._read_bit()

        # Deactivate encoder communication (CSn high)
        self.CSn.value(1)

        # Verify even parity (total ones + parity must be even)
        total_ones = bin(position).count('1') + bin(status).count('1')
        if (total_ones + parity_bit) % 2 != 0:
            return None

        # Extract and validate status flags
        OCF = (status >> 4) & 0x01  # Offset Compensation Finished (must be 1)
        COF = (status >> 3) & 0x01  # CORDIC Overflow (must be 0)
        if OCF == 0 or COF == 1:
            return None

        # Apply hysteresis filtering and update last reading
        if self._check_hysteresis(position):
            self.last_reading = position
            return position
        else:
            return self.last_reading if self.last_reading is not None else None

    def set_zero_offset(self, offset_value=None):
        """Set zero reference point for encoder measurements.
        
        Configures an offset value that will be subtracted from encoder readings
        to establish a custom zero reference point. Only affects the dial value
        returned by get_value() and get_values_dict(), not internal calculations.

        Args:
            offset_value (int, optional): Offset value to apply (0-4095 range).
                If None, offset remains unchanged.
        """
        self.logger.console_printing(
            "INFO",
            f"Zero offset set to: {offset_value}"
        )
        self.zero_offset = offset_value

    def _reading_loop(self):
        """Continuous background reading loop executed in separate thread.

        Performs periodic encoder readings, updates the values dictionary,
        calculates deltas, applies virtual gear logic, and maintains timestamps.
        All operations are protected by thread locks for safe concurrent access.
        """
        while not self._stop:
            new_val = self.read_ssi()
            
            with self.value_lock:
                current_time = time.ticks_ms()
                
                # Calculate delta with wrap-around consideration
                if self._values_dict["dial"] is not None and new_val is not None:
                    raw_delta = new_val - self._values_dict["dial"]
                    # Handle circular encoder wrap-around (0-4095 boundary)
                    if abs(raw_delta) > self.max_reading / 2:
                        if raw_delta > 0:
                            delta = raw_delta - self.max_reading
                        else:
                            delta = raw_delta + self.max_reading
                    else:
                        delta = raw_delta
                    
                    self._values_dict["delta"] = delta
                
                # Update primary encoder value
                self._values_dict["dial"] = new_val
                
                # Apply virtual gear logic for advanced applications
                if new_val is not None:
                    self._apply_gear_logic(new_val)
                
                # Update timestamp for velocity calculations
                self._values_dict["timestamp"] = current_time
            
            time.sleep(self.delay_s)

    def _apply_gear_logic(self, new_val):
        """Apply virtual gear wheel simulation logic to encoder data.
        
        Implements a complex gear train simulation with multiple virtual wheels
        that respond to encoder rotation with different behaviors and timing.
        Used for advanced measurement applications requiring mechanical simulation.
        
        Args:
            new_val (int): Current encoder position value (0-4095).
        """
        # Apply zero offset for gear calculations
        adjusted_val = new_val
        if self.zero_offset and new_val is not None:
            adjusted_val = new_val - self.zero_offset
            if adjusted_val < 0:  # Handle negative wrap-around
                adjusted_val = adjusted_val + self.max_reading + 1
        
        # Initialize gear logic on first reading
        if self._first_read:
            self._old_data = adjusted_val
            self._first_read = False
        
        self._new_data = adjusted_val
        
        # Calculate drive position difference for turn counting
        diff_drive = self._calculate_difference_driveOLD_driveNEW(self._old_data, self._new_data)
        
        # Update revolution counter
        self._values_dict["turns_drive"] = self._set_turns_drive(
            diff_drive, 
            self._values_dict["turns_drive"], 
            self._new_data, 
            self._old_data
        )
        
        # Process virtual wheel 4 (first level gear)
        diff_old_wheel4 = self._calculate_difference_driveOLD_Wheel_position(
            self._old_data, self._wheel_4_value
        )
        diff_new_wheel4 = self._calculate_difference_driveNEW_Wheel_position(
            self._new_data, self._wheel_4_value
        )
        
        # Update direction state for wheel 4
        self._right_pin_drive = self._set_left_or_right(
            diff_old_wheel4, diff_new_wheel4, self._right_pin_drive
        )
        
        # Update wheel 4 position
        self._old_wheel_4_value = self._wheel_4_value
        self._wheel_4_value = self._set_wheel_tree_value(
            diff_new_wheel4, self._right_pin_drive, self._new_data, self._wheel_4_value
        )
        self._values_dict["wheel_4"] = self._wheel_4_value
        
        # Process virtual wheel 3 (driven by wheel 4)
        diff_old_wheel3 = self._calculate_difference_driveOLD_Wheel_position(
            self._old_wheel_4_value, self._wheel_3_value
        )
        diff_new_wheel3 = self._calculate_difference_driveNEW_Wheel_position(
            self._wheel_4_value, self._wheel_3_value
        )
        
        self._right_pin_w4 = self._set_left_or_right(
            diff_old_wheel3, diff_new_wheel3, self._right_pin_w4
        )
        
        self._old_wheel_3_value = self._wheel_3_value
        self._wheel_3_value = self._set_wheel_tree_value(
            diff_new_wheel3, self._right_pin_w4, self._wheel_4_value, self._wheel_3_value
        )
        self._values_dict["wheel_3"] = self._wheel_3_value
        
        # Process virtual wheel 2 (driven by wheel 3)
        diff_old_wheel2 = self._calculate_difference_driveOLD_Wheel_position(
            self._old_wheel_3_value, self._wheel_2_value
        )
        diff_new_wheel2 = self._calculate_difference_driveNEW_Wheel_position(
            self._wheel_3_value, self._wheel_2_value
        )
        
        self._right_pin_w3 = self._set_left_or_right(
            diff_old_wheel2, diff_new_wheel2, self._right_pin_w3
        )
        
        self._old_wheel_2_value = self._wheel_2_value
        self._wheel_2_value = self._set_wheel_tree_value(
            diff_new_wheel2, self._right_pin_w3, self._wheel_3_value, self._wheel_2_value
        )
        self._values_dict["wheel_2"] = self._wheel_2_value
        
        # Process virtual wheel 1 (final gear in chain)
        diff_old_wheel1 = self._calculate_difference_driveOLD_Wheel_position(
            self._old_wheel_2_value, self._wheel_1_value
        )
        diff_new_wheel1 = self._calculate_difference_driveNEW_Wheel_position(
            self._wheel_2_value, self._wheel_1_value
        )
        
        self._right_pin_w2 = self._set_left_or_right(
            diff_old_wheel1, diff_new_wheel1, self._right_pin_w2
        )
        
        self._old_wheel_1_value = self._wheel_1_value
        self._wheel_1_value = self._set_wheel_tree_value(
            diff_new_wheel1, self._right_pin_w2, self._wheel_2_value, self._wheel_1_value
        )
        self._values_dict["wheel_1"] = self._wheel_1_value
        
        # Update state for next iteration
        self._old_data = self._new_data

    def _calculate_difference_driveOLD_driveNEW(self, old_data_drive, new_data_drive):
        """Calculate signed angular difference between old and new drive positions.
        
        Handles circular encoder boundary correctly for accurate delta calculations.
        
        Args:
            old_data_drive (int): Previous drive position.
            new_data_drive (int): Current drive position.
        
        Returns:
            int: Signed difference in range -2048 to +2048.
        """
        resultado = (4096 + new_data_drive - old_data_drive) % 4096
        if resultado > 2048:
            resultado = resultado - 4096
        return resultado

    def _calculate_difference_driveOLD_Wheel_position(self, old_data_drive, wheel_value):
        """Calculate angular difference between old drive position and wheel position.
        
        Args:
            old_data_drive (int): Previous drive position.
            wheel_value (int): Current wheel position.
        
        Returns:
            int: Signed difference in range -2048 to +2048.
        """
        resultado = (4096 + old_data_drive - wheel_value) % 4096
        if resultado > 2048:
            resultado = resultado - 4096
        return resultado

    def _calculate_difference_driveNEW_Wheel_position(self, new_data_drive, wheel_value):
        """Calculate angular difference between new drive position and wheel position.
        
        Args:
            new_data_drive (int): Current drive position.
            wheel_value (int): Current wheel position.
        
        Returns:
            int: Signed difference in range -2048 to +2048.
        """
        resultado = (4096 + new_data_drive - wheel_value) % 4096
        if resultado > 2048:
            resultado = resultado - 4096
        return resultado

    def _set_left_or_right(self, diff_old_wheel, diff_new_wheel, right_pin):
        """Determine drive pin position relative to wheel based on transition analysis.
        
        Analyzes the transition from old to new position to determine if the drive
        pin is positioned to the right or left of the virtual wheel.
        
        Args:
            diff_old_wheel (int): Difference between old drive and wheel position.
            diff_new_wheel (int): Difference between new drive and wheel position.
            right_pin (bool): Previous pin state (True = right, False = left).
        
        Returns:
            bool: New pin state (True if pin is to the right, False if to the left).
        """
        if diff_old_wheel == 0 and diff_new_wheel == 0:
            resultado = right_pin
        elif (right_pin is True and
              0 <= diff_old_wheel <= 1024 and
              -1024 <= diff_new_wheel <= 0):
            resultado = True
        elif diff_old_wheel >= 0 and diff_new_wheel > 0 and right_pin is True:
            resultado = True
        elif right_pin is True and diff_old_wheel >= 1024 and diff_new_wheel <= -1024:
            resultado = False
        elif right_pin is True and diff_new_wheel < 0:
            resultado = True
        elif (right_pin is False and
              diff_old_wheel <= 0 and diff_new_wheel >= 0 and
              -1024 <= diff_new_wheel <= 1024):
            resultado = False
        elif diff_old_wheel <= 0 and diff_new_wheel < 0 and right_pin is False:
            resultado = False
        elif right_pin is False and diff_old_wheel <= -1024 and diff_new_wheel >= 1024:
            resultado = True
        else:
            resultado = right_pin  # Maintain state if no specific condition is met
        return resultado

    def _set_turns_drive(self, difference, turns, new_data, old_data):
        """Update revolution count based on encoder zero-crossing detection.
        
        Detects when the encoder crosses the zero point (wrap-around from 4095 to 0
        or vice versa) to accurately count complete revolutions.
        
        Args:
            difference (int): Angular difference between new and old positions.
            turns (int): Current revolution count.
            new_data (int): New encoder position value.
            old_data (int): Previous encoder position value.
        
        Returns:
            int: Updated revolution count.
                - Incremented for clockwise zero crossing
                - Decremented for counter-clockwise zero crossing
                - Unchanged if no zero crossing detected
        """
        if difference < 0:
            clock_wise = False
        elif difference > 0:
            clock_wise = True
        else:
            clock_wise = None

        # Detect zero crossing using threshold (half of encoder range)
        if difference != 0 and clock_wise is not None and abs(new_data - old_data) > 2048:
            if clock_wise:
                turns += 1
            else:
                # Special handling for first counter-clockwise turn
                if turns == 0 and not self._first_CCW_turn_counted:
                    self._first_CCW_turn_counted = True
                else:
                    turns -= 1
        return turns

    def _set_wheel_tree_value(self, diff_new_wheel, right_of_wheel, data, wheel_value_pos):
        """Update virtual wheel position based on drive pin crossing detection.
        
        Updates wheel position when the drive pin crosses the wheel position,
        simulating mechanical gear engagement.
        
        Args:
            diff_new_wheel (int): Difference between new drive and wheel positions.
            right_of_wheel (bool): Whether pin was to the right of the wheel.
            data (int): Current drive position value.
            wheel_value_pos (int): Current wheel position value.
        
        Returns:
            int: Updated wheel position value.
        """
        if diff_new_wheel < 0 and diff_new_wheel > -1024 and right_of_wheel is True:
            wheel_value_pos = data
        elif diff_new_wheel > 0 and diff_new_wheel < 1024 and right_of_wheel is False:
            wheel_value_pos = data
        return wheel_value_pos

    def get_value(self):
        """Get current encoder reading with zero offset applied.

        Returns the most recent valid encoder position adjusted by the configured
        zero offset for measurement applications.

        Returns:
            int or None: Encoder position with zero offset applied, or None if no valid reading.
        """
        with self.value_lock:
            raw_value = self._values_dict["dial"]
            # Apply zero offset with wrap-around handling
            if raw_value is not None and self.zero_offset:
                adjusted_value = raw_value - self.zero_offset
                if adjusted_value < 0:  # Handle negative wrap-around
                    adjusted_value += self.max_reading + 1
                return adjusted_value
            return raw_value
    
    def get_raw_value(self):
        """Get raw encoder value without zero offset adjustment.
        
        Returns the unmodified encoder position for applications requiring
        absolute position data.
        
        Returns:
            int or None: Raw encoder reading without offset adjustment.
        """
        with self.value_lock:
            return self._values_dict["dial"]
    
    def get_values_dict(self):
        """Get comprehensive dictionary of all encoder values and metadata.

        Returns a complete copy of the internal values dictionary with zero offset
        applied only to the dial value, preserving virtual wheel positions.

        Returns:
            dict: Dictionary containing:
                - dial: Main encoder position (with zero offset)
                - delta: Change since last reading
                - turns_drive: Complete revolution count
                - wheel_1, wheel_2, wheel_3, wheel_4: Virtual gear positions
                - timestamp: Reading timestamp for velocity calculations
        """
        with self.value_lock:
            # Create copy to prevent external modifications
            result = dict(self._values_dict)
            
            # Apply zero offset only to dial value
            if result["dial"] is not None and self.zero_offset:
                adjusted_value = result["dial"] - self.zero_offset
                if adjusted_value < 0:  # Handle negative wrap-around
                    adjusted_value += self.max_reading + 1
                result["dial"] = adjusted_value
            
            return result

    def stop(self):
        """Stop the background reading thread.
        
        Sets the stop flag to terminate the continuous reading loop in the
        background thread.
        """
        self._stop = True

    def reset_lock_values(self):
        """Reset all encoder values and internal state to initial conditions.
        
        Safely resets all tracked values, gear logic variables, and internal
        state using thread synchronization to prevent conflicts.
        
        Returns:
            bool: Always returns True indicating successful reset.
        """
        # Thread-safe reset of all values
        with self.value_lock:
            # Reset primary values dictionary
            self._values_dict["delta"] = 0
            self._values_dict["turns_drive"] = 0
            self._values_dict["wheel_1"] = 0
            self._values_dict["wheel_2"] = 0
            self._values_dict["wheel_3"] = 0
            self._values_dict["wheel_4"] = 0
            self._values_dict["timestamp"] = time.ticks_ms()

            # Reset internal gear logic variables
            self._wheel_1_value = 0
            self._wheel_2_value = 0
            self._wheel_3_value = 0
            self._wheel_4_value = 0
            self._old_wheel_1_value = 0
            self._old_wheel_2_value = 0
            self._old_wheel_3_value = 0
            self._old_wheel_4_value = 0
            
            # Reset reading state
            self._first_read = True
            self._old_data = 0
            self._new_data = 0
            
            # Reset turn counting state
            self._first_CCW_turn_counted = False
            self._previous_value = None

        return True

    def resetting_lock(self, mode):
        """Reset virtual pin states for gear mechanism simulation.
        
        Resets the internal virtual pin states that control the direction logic
        for each wheel in the gear train simulation.
        
        Args:
            mode (str): Reset mode specification:
                - "AWL" (Advanced Wheel Left): Sets all pins to True
                - "AWR" (Advanced Wheel Right): Sets all pins to False
        
        Returns:
            bool: True if reset successful, False if invalid mode specified.
            
        Examples:
            >>> encoder.resetting_lock("AWL")  # Reset all pins to left position
            >>> encoder.resetting_lock("AWR")  # Reset all pins to right position
        """
        # Thread-safe pin state reset
        with self.value_lock:
            if mode == "AWL":
                # Set all virtual pins to True for left configuration
                self._right_pin_drive = False
                self._right_pin_w4 = False
                self._right_pin_w3 = False
                self._right_pin_w2 = False
                self.logger.console_printing("INFO", "Lock reset to AWL mode (all pins = False)")
                return True
            elif mode == "AWR":
                # Set all virtual pins to False for right configuration
                self._right_pin_drive = True
                self._right_pin_w4 = True
                self._right_pin_w3 = True
                self._right_pin_w2 = True
                self.logger.console_printing("INFO", "Lock reset to AWR mode (all pins = True)")
                return True
            else:
                # Invalid mode specified
                self.logger.console_printing("ERROR", f"Invalid mode for lock reset: {mode}")
                return False