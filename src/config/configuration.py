"""
Configuration module for Anubis Axis project.

This module manages the application's configuration, including UI settings,
theme colors, language translations, and hardware parameters for the measurement
and calibration system on Raspberry Pi Pico 2. It handles persistent storage
of user preferences in JSON format and provides centralized access to all
system configuration parameters.

The module integrates with the PowerSupply driver for battery monitoring
and the Logger system for consistent error reporting and diagnostics.

Author: Seguridad Física
File: config/configuration.py
"""

import json
from drivers.powersupply import PowerSupply
from common.constants import VBAT_PIN
from ui.logger import Logger

# Default configuration dictionary with theme colors and UI settings
DEFAULT_CONFIG = {
    "ui": {
        "brightness": 32768,  # PWM brightness value (0-65535 range)
        "dark_mode": True,    # Default to dark theme for better contrast
        "colors": {
            "light_theme": {
                "background": "#FFFFFF",
                "primary": "#0091ff",
                "primary_shadow": "#CCE9FF",
                "secondary": "#EE6600",
                "secondary_shadow": "#331500",
                "shadow": "#F2F2F2",
                "shadow_2": "#BCBCBC",
                "warning": "#FF0000",
                "text_title": "#181818",
                "text_body": "#4C4C4C",
                "on_primary": "#FFFFFF",
                "on_secondary": "#000000",
                "on_background": "#000000"
            },
            "dark_theme": {
                "background": "#000000",
                "primary": "#0091FF",
                "primary_shadow": "#00111E",
                "secondary": "#EE6600",
                "secondary_shadow": "#1C0C00",
                "shadow": "#181818",
                "shadow_2": "#3F3F3F",
                "warning": "#FF0000",
                "text_title": "#F6F8F8",
                "text_body": "#AEAFAF",
                "on_primary": "#FFFFFF",
                "on_secondary": "#000000",
                "on_background": "#FFFFFF"
            }
        }
    },
    "default_language": "en",
    "debug_mode": True,
    "languages": {
        "es": {
            "logo_screen": {
                "logo": "Anubis Axis",
                "designer": "by SEGURIDAD FISICA"
            },
            "set_zero_screen": {
                "title": "ENCODER",
                "set_zero": "Ajuste a 0",
                "press": "Ajustar"
            }
        },
        "en": {
            "logo_screen": {
                "logo": "Anubis Axis",
                "designer": "by SEGURIDAD FISICA"
            },
            "set_zero_screen": {
                "title": "ENCODER",
                "set_zero": "Set to Zero",
                "press": "Set"
            }
        }
    }
}

class Configuration:
    """Manage application configuration settings for Anubis Axis project.

    This class handles configuration loading, saving, and provides centralized access
    to UI settings, theme colors, language translations, and hardware parameters.
    It manages persistent storage of user preferences while maintaining defaults
    for system-critical settings that should not be user-modifiable.

    The configuration system separates user-configurable settings (brightness,
    theme mode, language) from system constants (debug mode, translations structure)
    to prevent corruption of essential application functionality.

    Attributes:
        dark_mode (bool): Whether dark theme mode is currently enabled.
        brightness (int): LCD backlight brightness level (0-65535 PWM range).
        default_language (str): Current language code for UI text display.
        translations (dict): UI text translations for the selected language.
        colors (dict): Color themes dictionary containing light and dark mode palettes.
        debug_mode (bool): Whether debug logging is enabled (system setting).
        use_colors (bool): Whether ANSI colors are used in console output (system setting).
        logger (Logger): Logger instance for configuration-related messages.
        power_supply (PowerSupply): Power supply monitoring instance for battery status.
    """

    def __init__(self):
        """Initialize the Configuration instance with hardware and logger setup.

        Sets up temporary default values, initializes the logger system, loads
        user configuration from persistent storage, and initializes the power
        supply monitoring system for battery voltage tracking.

        The initialization process follows a specific sequence to ensure proper
        dependency resolution between logger, configuration, and hardware drivers.
        """
        # Step 1: Set temporary default values for logger initialization
        self.dark_mode = DEFAULT_CONFIG["ui"]["dark_mode"]
        self.brightness = DEFAULT_CONFIG["ui"]["brightness"]
        self.default_language = DEFAULT_CONFIG["default_language"]
        self.translations = DEFAULT_CONFIG["languages"][self.default_language]
        self.colors = DEFAULT_CONFIG["ui"]["colors"]
        self.debug_mode = DEFAULT_CONFIG.get("debug_mode", False)
        self.use_colors = DEFAULT_CONFIG.get("use_colors", True)

        # Step 2: Initialize logger with default configuration values
        self.logger = Logger()
        self.logger.update_config(
            default_language=self.default_language,
            debug_mode=self.debug_mode,
            use_colors=self.use_colors
        )

        # Step 3: Load user configuration which may override defaults
        self.load_configuration()

        # Step 4: Update logger with potentially new configuration values
        self.logger.update_config(
            default_language=self.default_language,
            debug_mode=self.debug_mode,
            use_colors=self.use_colors
        )

        # Step 5: Initialize power supply monitoring after configuration load
        try:
            self.power_supply = PowerSupply(VBAT_PIN)
            # Log initial battery voltage with precision for diagnostics
            self.logger.console_printing("INFO", f"PowerSupply initialized. Battery voltage: {self.power_supply.read_battery_voltage:.2f}V")
        except Exception as e:
            self.logger.console_printing("ERROR", f"Failed to initialize power supply: {str(e)}")

        # Step 6: Confirm successful configuration initialization
        self.logger.console_printing("INFO", "Configuration initialization completed")

    def load_configuration(self):
        """Load user-configurable settings from persistent JSON storage.

        Loads only user-modifiable values from the configuration file,
        using default values for system settings and missing parameters.
        Creates a minimal configuration file with defaults if none exists.

        This method ensures system stability by protecting critical settings
        while allowing user customization of UI preferences.

        Raises:
            Exception: Logs error and falls back to defaults if configuration loading fails.
        """
        # Stored at the filesystem root (not inside a "config/" folder): a
        # device-side "config" directory would shadow the frozen config.configuration
        # package for every import (filesystem takes priority over frozen modules).
        config_file = "config.json"
        try:
            # Check if configuration file exists, create minimal version if not
            if not self._file_exists(config_file):
                # Create file with only user-configurable settings
                config = {
                    "ui": {
                        "brightness": DEFAULT_CONFIG["ui"]["brightness"],
                        "dark_mode": DEFAULT_CONFIG["ui"]["dark_mode"],
                        "colors": DEFAULT_CONFIG["ui"]["colors"]
                    },
                    "default_language": DEFAULT_CONFIG["default_language"]
                }
                self._create_config_file(config_file, config)
                self.logger.console_printing("INFO", "Minimal configuration file created with default values.")
            else:
                # Load existing configuration file
                with open(config_file, "r") as file:
                    config = json.load(file)

            # Apply only user-configurable values, preserve system defaults
            ui_config = config.get("ui", {})

            # Load runtime-changeable UI settings
            self.dark_mode = ui_config.get("dark_mode", DEFAULT_CONFIG["ui"]["dark_mode"])
            self.brightness = ui_config.get("brightness", DEFAULT_CONFIG["ui"]["brightness"])

            # Load language preference for UI text
            self.default_language = config.get("default_language", DEFAULT_CONFIG["default_language"])

            # Always use translations from DEFAULT_CONFIG to prevent corruption
            self.translations = DEFAULT_CONFIG.get("languages", {}).get(self.default_language, {})

            # Validate color theme completeness before loading
            if ('colors' in ui_config and
                'light_theme' in ui_config.get('colors', {}) and
                'dark_theme' in ui_config.get('colors', {})):
                self.colors = ui_config.get("colors")
            else:
                self.colors = DEFAULT_CONFIG["ui"]["colors"]

            # System settings always use defaults to prevent configuration corruption
            self.debug_mode = DEFAULT_CONFIG.get("debug_mode", True)
            self.use_colors = DEFAULT_CONFIG.get("use_colors", True)

            # Update logger with current configuration
            self.logger.update_config(
                default_language=self.default_language,
                debug_mode=self.debug_mode,
                use_colors=self.use_colors
            )

            self.logger.console_printing(
                "INFO",
                f"Configuration loaded: Dark Mode: {self.dark_mode}, Brightness: {self.brightness}, Language: {self.default_language}"
            )

        except Exception as e:
            # Fallback to complete default configuration on any error
            default_ui = DEFAULT_CONFIG.get("ui", {})
            self.dark_mode = default_ui.get("dark_mode", False)
            self.brightness = default_ui.get("brightness", 32768)
            self.default_language = DEFAULT_CONFIG.get("default_language", "en")
            self.translations = DEFAULT_CONFIG.get("languages", {}).get(self.default_language, {})
            self.colors = default_ui.get("colors", {})
            self.debug_mode = DEFAULT_CONFIG.get("debug_mode", True)
            self.use_colors = DEFAULT_CONFIG.get("use_colors", True)

            # Update logger with fallback defaults
            self.logger.update_config(
                default_language=self.default_language,
                debug_mode=self.debug_mode,
                use_colors=self.use_colors
            )

            self.logger.console_printing("ERROR", f"Error loading configuration, using defaults: {str(e)}")

    def _file_exists(self, file_path):
        """Check if a file exists in the filesystem.

        Safely checks file existence without raising exceptions for missing files.
        Used for configuration file detection before attempting to load.

        Args:
            file_path (str): Path to the file to check for existence.

        Returns:
            bool: True if file exists and is readable, False otherwise.
        """
        try:
            with open(file_path, "r"):
                pass
            return True
        except OSError:
            return False

    def _create_config_file(self, file_path, config):
        """Create a configuration file with provided data.

        Safely creates JSON configuration file with error handling for
        filesystem operations that may fail on flash storage.

        Args:
            file_path (str): Path where configuration file should be created.
            config (dict): Configuration data to serialize and write to file.
        """
        try:
            with open(file_path, "w") as file:
                json.dump(config, file)
        except Exception as e:
            self.logger.console_printing("ERROR", f"Error creating configuration file: {str(e)}")

    def save_configuration(self):
        """Save user-configurable settings to persistent JSON storage.

        Saves only settings that can be modified during runtime, preserving
        system-critical configuration values. Creates directory structure
        if needed and handles filesystem errors gracefully.

        Returns:
            bool: True if configuration was saved successfully, False if error occurred.

        Examples:
            >>> config = Configuration()
            >>> config.brightness = 45000
            >>> config.dark_mode = False
            >>> success = config.save_configuration()
        """
        # Package only user-configurable values for persistence
        user_config = {
            "ui": {
                "brightness": self.brightness,
                "dark_mode": self.dark_mode,
                "colors": self.colors
            },
            "default_language": self.default_language
        }

        # Attempt to save configuration with error handling
        try:
            with open("config.json", "w") as file:
                json.dump(user_config, file)
                self.logger.console_printing("INFO", "Configuration saved successfully to config.json")
                return True
        except Exception as e:
            self.logger.console_printing("ERROR", f"Error saving configuration: {str(e)}")
            return False