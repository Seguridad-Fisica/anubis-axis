"""
USB Configuration Module for Raspberry Pi Pico 2 (RP2350).

This module initializes an additional CDC (Communications Device Class) interface
at boot time, providing a second USB serial port alongside the built-in one.
This configuration enables dual-channel USB communication for the Anubis Axis project,
separating application data streams from REPL debugging interfaces.

The module is executed automatically during MicroPython boot sequence before main.py,
ensuring USB interfaces are properly configured for the measurement and calibration
system hardware components.

Hardware:
- Raspberry Pi Pico 2 with RP2350
- 520KB SRAM, 4MB Flash Memory
- 1.28" LCD Screen (240x240) with GC9A01A driver
- CST816T Touch Screen
- 12-bit absolute encoder

Benefits of dual CDC interfaces:
1. Separate data communication from REPL control
2. Dedicated channel for application logs/data
3. Maintain access to MicroPython REPL for debugging
4. Improved debugging capabilities during development

Author: Seguridad Física
File: boot.py
"""
import usb.device

# Default to None so downstream modules can detect an unavailable CDC channel
# instead of crashing at import time (e.g. lib/usb/device/*.mpy version mismatch
# against the running firmware).
usb.device.cdc_data = None

try:
    from usb.device.cdc import CDCInterface

    # Create and initialize the additional CDC interface for data communication
    cdc_data = CDCInterface()
    cdc_data.init(timeout=0)  # Non-blocking read operations to prevent blocking main thread

    # Register in the manual singleton pattern for global access from other modules
    usb.device.cdc_data = cdc_data

    # Initialize USB device while preserving the original CDC interface for REPL
    usb.device.get().init(cdc_data, builtin_driver=True)
    print("boot.py: Additional CDC initialized")
except Exception as e:
    # Keep booting with REPL-only USB so the rest of the app remains usable
    # even if the secondary CDC (lib/usb/device) fails to load.
    print("boot.py: Additional CDC unavailable:", e)