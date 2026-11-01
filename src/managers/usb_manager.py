"""
USB Communication Manager for Anubis Axis project.

This module provides a manager for handling USB CDC communications
with a host device via the secondary CDC interface configured in boot.py.
It implements a simple text-based command protocol for monitoring and controlling
the device.

Author: Seguridad Física
File: managers/usb_manager.py
"""
import time
import json
from common.constants import __version__
from ui.logger import Logger

class USBManager:
    """
    Manages communication with the host via secondary USB CDC interface.

    Listens for commands, processes them, and sends responses.
    """
    def __init__(self, cdc_interface, encoder=None, lcd=None, configuration=None):
        self.cdc = cdc_interface
        self.encoder = encoder
        self.lcd = lcd
        self.configuration = configuration
        self.logger = Logger()
        self.buffer = b""
        self.command_handlers = {
            "ping": self._handle_ping,
            "status": self._handle_status,
            "get_encoder": self._handle_get_encoder,
            "set_zero": self._handle_set_zero,
            "reset_lock": self._handle_reset_lock,
        }
        self._running = False

    def start(self):
        """Start the USB communication manager."""
        self._running = True
        self.logger.info("USB Manager started")
        if self.cdc:
            self.cdc.write(b"USB Manager ready\r\n> ")

    def stop(self):
        """Stop the USB communication manager."""
        self._running = False

    def process(self):
        """
        Poll the CDC interface for incoming data.

        This method should be called regularly from the main loop.
        """
        if not self._running or not self.cdc or not self.cdc.is_open():
            return

        try:
            # Drain every byte already buffered in this call instead of one per
            # call, since the caller's loop period is gated by the LCD redraw.
            while True:
                char = self.cdc.read(1)
                if not char:
                    break
                # Backspace / Delete
                if char in (b'\x08', b'\x7f'):
                    if self.buffer:
                        self.buffer = self.buffer[:-1]
                        self.cdc.write(b"\b \b")
                # Enter/Return: finish command
                elif char in (b'\r', b'\n'):
                    # Don't echo the new line, we'll handle it in the response
                    if self.buffer:
                        command_str = self.buffer.decode('utf-8', 'replace').strip()
                        self.buffer = b""
                        # Print a newline before processing the command
                        self.cdc.write(b"\r\n")
                        self.logger.info(f"USB command received: {command_str}")
                        self._process_command(command_str)
                        # Add a prompt for next command
                        self.cdc.write(b"\r\n> ")
                    else:
                        # Just an empty line, provide a prompt
                        self.cdc.write(b"\r\n> ")
                # Normal character: accumulate and echo
                else:
                    self.buffer += char
                    self.cdc.write(char)  # Echo the character back
        except Exception as e:
            self.logger.error(f"USB Manager error: {e}")

    def send_message(self, message):
        """
        Send a message to the host.

        Args:
            message: The message to send (string or bytes)
        """
        if not self.cdc or not self.cdc.is_open():
            return False
        try:
            if isinstance(message, str):
                message = message.encode('utf-8')
            if not message.endswith(b'\r\n'):
                message += b'\r\n'

            # Ensure we don't break the terminal formatting
            self.cdc.write(message)
            return True
        except Exception as e:
            self.logger.error(f"Failed to send message: {e}")
            return False

    def _process_command(self, command_str):
        """
        Process a received command string.

        Args:
            command_str: The command string to process
        """
        parts = command_str.split(" ", 1)
        command = parts[0].lower()
        args = parts[1] if len(parts) > 1 else ""
        self.logger.info(f"Processing command: {command} {args}")
        if command in self.command_handlers:
            try:
                self.command_handlers[command](args)
            except Exception as e:
                self.send_message(f"ERROR: Command execution failed: {e}")
        else:
            self.send_message(f"ERROR: Unknown command: {command}")
            self.send_message("Type 'help' for available commands")

    # Command handlers
    def _handle_ping(self, args):
        """Handle the ping command."""
        self.logger.info("Handling ping command")
        self.send_message("pong")

    def _handle_status(self, args):
        """Handle the status command."""
        import machine
        status = {
            "system": "online",
            "firmware": __version__,
            "cpu_freq_mhz": int(machine.freq() / 1000000),
        }
        if self.encoder:
            status["encoder"] = {
                "connected": True,
                "value": self.encoder.get_value()
            }
        else:
            status["encoder"] = {"connected": False}
        self.send_message(json.dumps(status))

    def _handle_get_encoder(self, args):
        """Handle the get_encoder command."""
        if not self.encoder:
            self.send_message("ERROR: Encoder not available")
            return
        try:
            values = self.encoder.get_values_dict()
            self.send_message(json.dumps(values))
        except Exception as e:
            self.send_message(f"ERROR: Failed to read encoder: {e}")

    def _handle_set_zero(self, args):
        """
        Handle the set_zero command.

        Usage: set_zero [value]
        """
        if not self.encoder:
            self.send_message("ERROR: Encoder not available")
            return
        try:
            if args:
                try:
                    offset = int(args)
                    self.encoder.zero_offset = offset
                    self.send_message(f"Zero offset set to: {offset}")
                except ValueError:
                    self.send_message(f"ERROR: Invalid value: {args}")
            else:
                reading = self.encoder.get_value()
                if reading is None:
                    self.send_message("ERROR: No valid encoder reading")
                    return
                self.encoder.zero_offset = reading
                self.send_message(f"Zero offset set to current reading: {reading}")
        except Exception as e:
            self.send_message(f"ERROR: Failed to set zero offset: {e}")

    def _handle_reset_lock(self, args):
        """
        Handle the reset_lock command.

        Usage: reset_lock [mode]  where mode is either 'AWL' or 'AWR'
        """
        if not self.encoder:
            self.send_message("ERROR: Encoder not available")
            return
        try:
            if args.upper() in ["AWL", "AWR"]:
                self.encoder.resetting_lock(args.upper())
                self.send_message(f"Lock reset to {args.upper()} mode")
            else:
                self.send_message("ERROR: Mode must be 'AWL' or 'AWR'")
        except Exception as e:
            self.send_message(f"ERROR: Failed to reset lock: {e}")