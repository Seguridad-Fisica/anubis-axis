"""
Constants module for Anubis Axis project.

This module defines all hardware pin assignments and configuration constants
for the Anubis Axis measurement and calibration system running on Raspberry Pi Pico 2.
It centralizes GPIO pin mappings for the 1.28" LCD display, capacitive touchscreen,
12-bit absolute encoder, and battery monitoring subsystems.

The module provides essential configuration for SPI, I2C, SSI interfaces and
touch gesture recognition constants used throughout the application.

Author: Seguridad Física
File: common/constants.py

Attributes:
    SSI_CSN_PIN (int): Chip Select pin for 12-bit absolute encoder SSI interface.
    SSI_CLK_PIN (int): Clock pin for encoder SSI communication.
    SSI_D0_PIN (int): Data 0 pin for encoder SSI serial data transmission.
    
    SPI_DC_PIN (int): Data/Command control pin for GC9A01A LCD SPI interface.
    SPI_CS_PIN (int): Chip Select pin for LCD SPI communication.
    SPI_SCK_PIN (int): Serial Clock pin for LCD SPI interface.
    SPI_MOSI_PIN (int): Master Out Slave In data pin for LCD SPI.
    SPI_MISO_PIN (int): Master In Slave Out data pin for LCD SPI.
    SPI_RST_PIN (int): Hardware reset pin for LCD initialization.
    
    PWM_BACKLIGHT_PIN (int): PWM control pin for LCD backlight brightness.
    
    I2C_SDA_PIN (int): Serial Data pin for CST816T touchscreen I2C interface.
    I2C_SDL_PIN (int): Serial Clock pin for touchscreen I2C communication.
    I2C_INT_PIN (int): Interrupt pin for touchscreen gesture detection.
    I2C_RST_PIN (int): Hardware reset pin for touchscreen initialization.
    
    GESTURE_SLIDE_DOWN (int): Touch gesture constant for downward slide.
    GESTURE_SLIDE_UP (int): Touch gesture constant for upward slide.
    GESTURE_SLIDE_LEFT (int): Touch gesture constant for leftward slide.
    GESTURE_SLIDE_RIGHT (int): Touch gesture constant for rightward slide.
    GESTURE_SINGLE_CLICK (int): Touch gesture constant for single tap.
    GESTURE_DOUBLE_CLICK (int): Touch gesture constant for double tap.
    GESTURE_LONG_PRESS (int): Touch gesture constant for press and hold.
    GESTURE_RESET (int): Touch gesture reset/idle state constant.
    
    VBAT_PIN (int): ADC pin for LiPo battery voltage monitoring through voltage divider.
"""

# Firmware semantic version (Single Source of Truth)
__version__ = "1.0.0"

# 12-bit absolute encoder SSI interface configuration (current wiring)
SSI_D0_PIN = 18   # Data 0 serial output from encoder
SSI_CSN_PIN = 26  # Chip Select (active low) for encoder communication
SSI_CLK_PIN = 27  # Clock signal for SSI data transmission

# Alternative encoder SPI configuration
#SSI_D0_PIN = 16   # Data 0 | GPIO brown wire connects to encoder white wire
#SSI_CSN_PIN = 17  # Chip Select | GPIO orange wire connects to encoder yellow wire
#SSI_CLK_PIN = 18  # Clock | GPIO green wire connects to encoder green wire

# GC9A01A LCD display SPI interface configuration
SPI_DC_PIN = 8    # Data/Command selection pin (0=command, 1=data)
SPI_CS_PIN = 9    # Chip Select pin for LCD SPI communication
SPI_SCK_PIN = 10  # Serial Clock pin for SPI data transfer
SPI_MOSI_PIN = 11 # Master Out Slave In - data transmission to LCD
SPI_MISO_PIN = 12 # Master In Slave Out - data reception from LCD (unused)
SPI_RST_PIN = 13  # Hardware reset pin for LCD initialization sequence

# LCD backlight PWM control configuration
PWM_BACKLIGHT_PIN = 25  # PWM output for brightness control (0-100% duty cycle)

# CST816T capacitive touchscreen I2C interface configuration
I2C_SDA_PIN = 6  # Serial Data line for I2C communication
I2C_SDL_PIN = 7  # Serial Clock line for I2C timing
I2C_INT_PIN = 21 # Interrupt pin for touch event notification
I2C_RST_PIN = 22 # Hardware reset pin for touchscreen initialization

# Touch gesture recognition constants from CST816T driver
GESTURE_SLIDE_DOWN = 0x01    # Downward finger slide gesture
GESTURE_SLIDE_UP = 0x02      # Upward finger slide gesture
GESTURE_SLIDE_LEFT = 0x03    # Leftward finger slide gesture
GESTURE_SLIDE_RIGHT = 0x04   # Rightward finger slide gesture
GESTURE_SINGLE_CLICK = 0x05  # Single finger tap gesture
GESTURE_DOUBLE_CLICK = 0x0b  # Double finger tap gesture
GESTURE_LONG_PRESS = 0x0c    # Press and hold gesture
GESTURE_RESET = 0x00         # No gesture detected or reset state

# Battery monitoring configuration for LiPo power management
VBAT_PIN = 29  # ADC input pin connected to voltage divider (R1=100kΩ, R2=220kΩ) for 4.2V max LiPo measurement