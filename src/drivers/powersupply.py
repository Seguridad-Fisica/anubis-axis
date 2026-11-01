"""
PowerSupply driver module for Anubis Axis project.

This module provides the PowerSupply class for monitoring LiPo battery voltage
on the Raspberry Pi Pico 2 through an ADC interface with voltage divider circuit.
It enables battery level monitoring for the Anubis Axis measurement and calibration
system, providing accurate voltage readings for power management and low battery
detection in portable applications.

The driver handles ADC configuration, voltage scaling calculations, and provides
a simple interface for battery monitoring in MicroPython applications.

Author: Seguridad Física
File: drivers/powersupply.py
"""

from machine import Pin, ADC # Import hardware interaction classes from MicroPython

class PowerSupply:
    """Power supply monitoring interface for LiPo battery voltage readings.

    This class manages battery voltage monitoring through an ADC pin connected
    to a voltage divider circuit. It provides accurate voltage measurements
    for LiPo battery monitoring in the Anubis Axis system, enabling power management
    features and low battery warnings.

    The voltage divider circuit reduces the 4.2V maximum LiPo voltage to a safe
    range for the 3.3V ADC input, using a 3:1 voltage division ratio with
    precision resistors for accurate measurements.

    Attributes:
        adc (ADC): 12-bit ADC instance configured for battery voltage reading
            with automatic reference voltage scaling.
    """

    def __init__(self, VBAT_PIN):
        """Initialize the PowerSupply instance with ADC configuration.

        Sets up the ADC pin for battery voltage reading through the voltage
        divider circuit. Configures the ADC for 12-bit resolution to provide
        precise voltage measurements for battery monitoring applications.

        Args:
            VBAT_PIN (int): GPIO pin number connected to the voltage divider output
                (typically pin 29 on Raspberry Pi Pico 2 for VSYS monitoring).

        Examples:
            >>> # Initialize power supply monitoring on pin 29
            >>> power = PowerSupply(VBAT_PIN=29)
            >>> print(f"Battery voltage: {power.read_battery_voltage:.2f}V")
        """
        # Configure ADC pin for battery voltage monitoring
        self.adc = ADC(Pin(VBAT_PIN))

    @property
    def read_battery_voltage(self):
        """Read the current battery voltage through the voltage divider circuit.

        Performs a 12-bit ADC reading and applies the necessary scaling to convert
        the digital value back to the actual battery voltage. The calculation
        accounts for the 3.3V ADC reference voltage and the 3:1 voltage divider
        ratio used to safely measure LiPo voltages up to 4.2V.

        The voltage divider uses precision resistors (typically 100kΩ and 220kΩ)
        to create a 3:1 division ratio, allowing safe measurement of LiPo battery
        voltages while staying within the ADC's 3.3V maximum input range.

        Returns:
            float: Battery voltage in volts (typically 3.0V to 4.2V for LiPo batteries).
                - 4.2V: Fully charged LiPo battery
                - 3.7V: Nominal LiPo battery voltage
                - 3.0V: Low battery warning threshold

        Examples:
            >>> voltage = power.read_battery_voltage
            >>> if voltage < 3.2:
            >>>     print("Low battery warning!")
            >>> elif voltage > 4.0:
            >>>     print("Battery fully charged")
        """
        # Read 16-bit ADC value and convert to 12-bit resolution
        read = self.adc.read_u16() >> 4  # Convert 16-bit to 12-bit ADC reading

        # Calculate actual battery voltage: (ADC_value / max_12bit) * ref_voltage * divider_ratio
        return read / 4095 * 3.3 * 3  # 4095 = max 12-bit value, 3.3V reference, 3:1 voltage divider