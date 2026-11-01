"""
Logger module for Anubis Axis project.

This module provides a singleton Logger class for the Raspberry Pi Pico 2,
implementing centralized logging functionality for handling debug, info, warning,
error and critical messages. The logger supports ANSI color coding for better
console readability and can be configured to enable/disable debug mode and colors.

Author: Seguridad Física
File: ui/logger.py
"""

import time

class Logger:
    """Singleton Logger class for handling debug and error messages.

    Implements a singleton pattern to ensure only one instance of the logger exists
    throughout the application lifecycle. Provides structured logging with different
    severity levels and optional ANSI color coding for enhanced console output.

    The logger is designed specifically for MicroPython on Raspberry Pi Pico 2,
    with memory-efficient operations and direct English messaging without
    translation overhead.

    Attributes:
        _instance: Class-level singleton instance reference.
        _initialized (bool): Flag to prevent multiple initialization.
        COLORS (dict): ANSI color codes mapping for different log levels.
        default_language (str): Default language code for legacy compatibility.
        debug_mode (bool): Flag to control debug message output.
        use_colors (bool): Flag to enable/disable ANSI color codes in output.
    """
    _instance = None

    def __new__(cls):
        """Create or return the singleton instance of Logger.

        Ensures only one Logger instance exists using the singleton pattern.
        Creates a new instance on first call, returns existing instance on
        subsequent calls.

        Returns:
            Logger: The singleton instance of the Logger class.
        """
        if cls._instance is None:
            cls._instance = super(Logger, cls).__new__(cls)
            cls._instance._initialized = False
        return cls._instance

    def __init__(self):
        """Initialize the Logger with default settings.

        Sets up default configuration values including ANSI color codes,
        debug mode, and color usage flags. Prevents re-initialization
        of the singleton instance.

        Note:
            Configuration should be updated later using update_config() method
            to apply specific project settings.
        """
        if self._initialized:
            return
        self._initialized = True

        # Define ANSI color codes for console output formatting
        self.COLORS = {
            "RESET": "\033[0m",
            "RED": "\033[31m",
            "GREEN": "\033[32m",
            "YELLOW": "\033[33m",
            "WHITE": "\033[37m",
        }
        self.default_language = "en"  # Legacy compatibility
        self.debug_mode = True        # Enable debug output by default
        self.use_colors = True        # Enable ANSI colors by default

    def update_config(self, default_language=None, debug_mode=None, use_colors=None):
        """Update logger configuration with values provided by Configuration class.

        Allows dynamic reconfiguration of logger settings without requiring
        reinitialization. Accepts optional parameters to update specific
        configuration aspects while preserving existing settings.

        Args:
            default_language (str, optional): Language code for legacy compatibility.
            debug_mode (bool, optional): Enable/disable debug message output.
            use_colors (bool, optional): Enable/disable ANSI color codes in console.

        Examples:
            >>> logger = Logger()
            >>> logger.update_config(debug_mode=False, use_colors=True)
            >>> logger.update_config(default_language="es")
        """
        if default_language is not None:
            self.default_language = default_language
        if debug_mode is not None:
            self.debug_mode = debug_mode
        if use_colors is not None:
            self.use_colors = use_colors

    def _get_color(self, level):
        """Get the ANSI color code for a given log level.

        Maps log levels to their corresponding ANSI color codes for enhanced
        console readability. Returns empty string if colors are disabled.

        Args:
            level (str): The log level identifier (INFO, DEBUG, WARNING, ERROR, CRITICAL).

        Returns:
            str: ANSI color code for the specified level, or empty string if colors disabled.

        Examples:
            >>> logger._get_color('ERROR')    # Returns '\033[31m' (red)
            >>> logger._get_color('INFO')     # Returns '\033[32m' (green)
        """
        if not self.use_colors:
            return ''

        # Map log levels to specific colors for visual distinction
        level_colors = {
            "INFO": self.COLORS["GREEN"],      # Success/normal operations
            "DEBUG": self.COLORS["WHITE"],     # Development information
            "WARNING": self.COLORS["YELLOW"],  # Caution/potential issues
            "ERROR": self.COLORS["RED"],       # Error conditions
            "CRITICAL": self.COLORS["RED"]     # Critical system failures
        }
        return level_colors.get(level.upper(), self.COLORS["WHITE"])

    def console_printing(self, level, message):
        """Print a formatted message to the console based on the log level.

        Core logging method that handles message formatting and console output.
        Includes timestamp, colored level indicators, and the actual message.
        Only outputs when debug_mode is enabled to conserve resources.

        Args:
            level (str): The log level identifier (INFO, DEBUG, WARNING, ERROR, CRITICAL).
            message (str): The message content to be logged.

        Examples:
            >>> logger = Logger()
            >>> logger.console_printing('INFO', 'System initialized successfully')
            >>> logger.console_printing('ERROR', 'Failed to connect to device')
        """
        if self.debug_mode:
            # Generate timestamp for log entry tracking
            timestamp = time.localtime()
            formatted_time = "{:02d}:{:02d}:{:02d}".format(
                timestamp[3], timestamp[4], timestamp[5]
            )

            # Apply color formatting if enabled
            color = self._get_color(level)
            reset_color = self.COLORS['RESET'] if self.use_colors else ''

            # Format final message with level indicator and colors
            formatted_message = f"[ {color}{level}{reset_color} ] {message}"
            print(formatted_message)

    def set_debug_mode(self, mode):
        """Set the debug mode of the logger.

        Controls whether log messages are output to console. Useful for
        production environments where logging overhead should be minimized.

        Args:
            mode (bool): True to enable debug mode, False to disable all output.

        Examples:
            >>> logger.set_debug_mode(False)  # Disable all logging output
            >>> logger.set_debug_mode(True)   # Enable logging output
        """
        self.debug_mode = mode

    def set_use_colors(self, use_colors):
        """Set whether to use ANSI colors in the console output.

        Controls ANSI color code usage for environments that don't support
        colored terminal output or when plain text logging is preferred.

        Args:
            use_colors (bool): True to enable colors, False for plain text output.

        Examples:
            >>> logger.set_use_colors(False)  # Plain text output
            >>> logger.set_use_colors(True)   # Colored output
        """
        self.use_colors = use_colors

    # Convenience methods for different log levels
    def info(self, message):
        """Log an informational message.

        Used for general information about application flow, successful operations,
        and normal system status updates.

        Args:
            message (str): The informational message to log.

        Examples:
            >>> logger.info("Configuration loaded successfully")
            >>> logger.info("Device connected on port /dev/ttyUSB0")
        """
        self.console_printing("INFO", message)

    def debug(self, message):
        """Log a debug message.

        Used for detailed diagnostic information typically only of interest
        during development or when troubleshooting specific issues.

        Args:
            message (str): The debug message to log.

        Examples:
            >>> logger.debug("Encoder value: 2048")
            >>> logger.debug("Touch coordinates: x=120, y=180")
        """
        self.console_printing("DEBUG", message)

    def warning(self, message):
        """Log a warning message.

        Used for situations that are unusual or potentially problematic
        but don't prevent normal operation from continuing.

        Args:
            message (str): The warning message to log.

        Examples:
            >>> logger.warning("Battery level below 20%")
            >>> logger.warning("Touch calibration may be inaccurate")
        """
        self.console_printing("WARNING", message)

    def error(self, message):
        """Log an error message.

        Used for error conditions that affect functionality but allow
        the application to continue running with degraded performance.

        Args:
            message (str): The error message to log.

        Examples:
            >>> logger.error("Failed to initialize LCD display")
            >>> logger.error("Touch sensor communication timeout")
        """
        self.console_printing("ERROR", message)

    def critical(self, message):
        """Log a critical error message.

        Used for severe error conditions that may cause the application
        to terminate or severely impact system functionality.

        Args:
            message (str): The critical error message to log.

        Examples:
            >>> logger.critical("Out of memory - system halt")
            >>> logger.critical("Hardware fault detected")
        """
        self.console_printing("CRITICAL", message)