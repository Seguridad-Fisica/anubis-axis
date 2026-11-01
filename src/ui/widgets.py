"""
WidgetManager module for Anubis Axis project.

This module provides the WidgetManager class for managing UI widgets on the LCD display,
including circular gauges, dot indicators, battery monitors, rounded buttons, and grid overlays.
The module handles theme-aware rendering with automatic color management and supports various
display formats for numeric values and battery status visualization.

Author: Seguridad Física
File: ui/widgets.py
"""

import math
from ui.format_text import FormatText
from ui.assets.icons import ICONS  # Import the icons module

class WidgetManager:
    """Manages UI widgets on the LCD display for the Anubis Axis project.

    This class provides a comprehensive set of methods for creating and rendering various
    UI components including circular gauges, battery monitors, dot indicators, and buttons.
    All widgets are theme-aware and automatically adapt to current color schemes.

    Attributes:
        format_text (FormatText): Text formatting utility for LCD display operations.
        lcd: LCD display driver instance for rendering operations.
        config: Application configuration instance containing settings.
        _colors (dict): Current theme colors dictionary from BaseScreen.
        power_supply: Power supply interface for battery monitoring.
    """

    def __init__(self, lcd, configuration, theme_colors):
        """Initialize WidgetManager with LCD interface and configuration.

        Sets up the widget manager with all necessary interfaces for rendering
        UI components with proper theme color support.

        Args:
            lcd: LCD display driver instance for screen rendering operations.
            configuration: Application configuration instance containing settings.
            theme_colors (dict): Theme colors dictionary from BaseScreen for consistent styling.
        """
        self.format_text = FormatText(lcd)
        self.lcd = lcd
        self.config = configuration
        self._colors = theme_colors or {}
        self.power_supply = self.config.power_supply

    @property
    def colors(self):
        """Safe getter for accessing theme colors.

        Returns:
            dict: Current theme colors dictionary, empty dict if not set.
        """
        return self._colors

    def draw_circle_from_value(self, value, center_x=120, center_y=120, orbit_radius=113,
                         orbit_width=None, orbit_color=None, show_orbit=False,
                         dot_style='simple', dot_rings=None, dot_rings_color=None,
                         indicator_radius=4, indicator_color=None,
                         label=None, label_size=2, label_color=None, label_position='down',
                         show_value=False, value_text=None, value_size=2,
                         value_color=None, value_offset_x=0, value_offset_y=0,
                         value_format='raw', decimal_separator=',',
                         show_fraction_separate=False, vertical_fraction=False,
                         fraction_offset_y=0, fraction_size=None,
                         show_empty_fraction=False, fraction_color=None):
        """Draw a circular gauge with optional orbital path and moving indicator.

        Creates a circular gauge widget with a value-driven indicator that moves along
        an orbital path. Supports various display formats, label positioning, and
        styling options for comprehensive data visualization.

        Args:
            value (int): Value between 0-4095 for determining indicator position.
            center_x (int): X coordinate of circle center. Defaults to 120.
            center_y (int): Y coordinate of circle center. Defaults to 120.
            orbit_radius (int): Radius of the orbital path. Defaults to 113.
            orbit_width (int): Width of the orbital track. Defaults to 2*indicator_radius.
            orbit_color (int): RGB565 color for orbital track. Defaults to theme shadow.
            show_orbit (bool): Whether to display the orbital track. Defaults to False.
            dot_style (str): Indicator style ('simple' or 'double'). Defaults to 'simple'.
            dot_rings (int): Number of rings for 'double' style. Defaults to indicator_radius.
            dot_rings_color (int): RGB565 color for indicator rings. Defaults to theme background.
            indicator_radius (int): Radius of the indicator dot. Defaults to 4.
            indicator_color (int): RGB565 color for indicator. Defaults to theme secondary.
            label (str): Optional label text to display. Defaults to None.
            label_size (int): Font size for label text. Defaults to 2.
            label_color (int): RGB565 color for label. Defaults to theme text_title.
            label_position (str): Label position ('up' or 'down'). Defaults to 'down'.
            show_value (bool): Whether to show value in center. Defaults to False.
            value_text (str): Custom text for value display. Defaults to str(value).
            value_size (int): Font size for value text. Defaults to 2.
            value_color (int): RGB565 color for value text. Defaults to theme text_body.
            value_offset_x (int): X offset from center for value. Defaults to 0.
            value_offset_y (int): Y offset from center for value. Defaults to 0.
            value_format (str): Format type ('raw', 'decimal', 'SCALE_0_99_*'). Defaults to 'raw'.
            decimal_separator (str): Decimal separator ('.' or ','). Defaults to ','.
            show_fraction_separate (bool): Show fraction separately from integer. Defaults to False.
            vertical_fraction (bool): Use vertical fraction format. Defaults to False.
            fraction_offset_y (int): Additional Y offset for fraction. Defaults to 0.
            fraction_size (int): Font size for fraction. Auto-calculated if None.
            show_empty_fraction (bool): Show empty fraction (1/X) in shadow color. Defaults to False.
            fraction_color (int): RGB565 color for fraction. Uses value_color if None.
        """
        # Apply default theme colors for consistent styling
        theme_colors = {
            'orbit': self.colors['shadow'],
            'dot_rings': self.colors['background'],
            'indicator': self.colors['secondary'],
            'label': self.colors['text_title'],
            'value': self.colors['text_body']
        }

        orbit_color = orbit_color if orbit_color is not None else theme_colors['orbit']
        dot_rings_color = dot_rings_color if dot_rings_color is not None else theme_colors['dot_rings']
        indicator_color = indicator_color if indicator_color is not None else theme_colors['indicator']
        label_color = label_color if label_color is not None else theme_colors['label']
        value_color = value_color if value_color is not None else theme_colors['value']

        # Set orbit width to match indicator diameter for perfect alignment
        orbit_width = orbit_width if orbit_width is not None else (indicator_radius * 2)

        # 1. Draw orbital track (bottom layer)
        if show_orbit:
            # Calculate radii for precise indicator alignment
            half_width = orbit_width // 2
            outer_radius = orbit_radius + half_width
            inner_radius = orbit_radius - (half_width + 1)  # Extra pixel for perfect fit

            # Draw outer circle
            self.lcd.ellipse(
                center_x,
                center_y,
                outer_radius,
                outer_radius,
                orbit_color,
                True
            )

            # Draw inner circle to create track
            self.lcd.ellipse(
                center_x,
                center_y,
                inner_radius,
                inner_radius,
                self.colors['background'],
                True
            )

        # 2. Draw label (middle layer)
        if label:
            # Calculate label position based on widget center
            label_x = center_x

            if label_position.lower() == 'up':
                label_y = int(center_y - orbit_radius - 4)
            else:
                label_y = int(center_y + orbit_radius - 4)

            # Calculate text dimensions for background
            text_width = 8 * label_size * len(label)
            text_height = 8 * label_size
            padding = 4

            # Draw background rectangle
            self.lcd.fill_rect(
                label_x - (text_width // 2) - padding,
                label_y - padding,
                text_width + (padding * 2),
                text_height + (padding * 2),
                self.colors['background']
            )

            # Draw label text
            self.format_text.center_or_position_text_cached(
                label,
                label_size,
                label_color,
                center_x=False,
                center_y=False,
                x=label_x - (text_width // 2),
                y=label_y
            )

        # 3. Calculate indicator position using circular math
        angle = 2 * math.pi * value / 4096 - math.pi / 2  # Convert value to radians
        x = int(center_x + orbit_radius * math.cos(angle))
        y = int(center_y + orbit_radius * math.sin(angle))

        # 4. Draw indicator rings for 'double' style (upper layer)
        if dot_style == 'double':
            num_rings = dot_rings if dot_rings is not None else indicator_radius
            outer_dot_radius = indicator_radius + num_rings

            self.lcd.ellipse(
                x,
                y,
                outer_dot_radius,
                outer_dot_radius,
                dot_rings_color,
                True
            )

        # 5. Draw main indicator (top layer)
        self.lcd.ellipse(
            x,
            y,
            indicator_radius,
            indicator_radius,
            indicator_color,
            True
        )

        # 6. Draw center value if enabled
        if show_value:
            # Format value based on specified format type
            if value_text is None:
                if value_format == 'decimal':
                    # Convert to 0-99.9 decimal format
                    decimal_val = (value / 4095) * 99.9
                    integer_part = int(decimal_val)
                    decimal_digit = round((decimal_val - integer_part) * 10)

                    # Handle decimal overflow
                    if decimal_digit == 10:
                        integer_part += 1
                        decimal_digit = 0

                    # Handle integer overflow
                    if integer_part >= 100:
                        integer_part = 0
                        decimal_digit = 0

                    value_text = f"{integer_part}{decimal_separator}{decimal_digit}"

                elif value_format in ['SCALE_0_99_QUARTER', 'SCALE_0_99_EIGHTH', 'SCALE_0_99_TENTH', 'SCALE_0_99_TWENTIETH']:
                    # Calculate scaled value with fractional display
                    scaled_val = (value / 4096) * 100
                    integer_part = int(scaled_val)
                    decimal_part = scaled_val - integer_part

                    # Determine fraction denominator
                    denominator = {
                        'SCALE_0_99_QUARTER': 4,
                        'SCALE_0_99_EIGHTH': 8,
                        'SCALE_0_99_TENTH': 10,
                        'SCALE_0_99_TWENTIETH': 20
                    }[value_format]

                    numerator = int(decimal_part * denominator)

                    # Handle fraction overflow
                    if numerator == denominator:
                        integer_part += 1
                        numerator = 0

                    # Handle integer wrap at 100
                    if integer_part >= 100:
                        integer_part = 0
                        numerator = 0

                    if show_fraction_separate:
                        value_text = str(integer_part)

                        # Display fraction separately if there's a numerator or empty fractions are enabled
                        if numerator > 0 or show_empty_fraction:
                            fraction_x = center_x + value_offset_x
                            fraction_y = center_y + value_offset_y + 12 + fraction_offset_y

                            actual_fraction_size = fraction_size if fraction_size is not None else max(1, value_size - 1)

                            # Use shadow color for empty fractions
                            if numerator == 0 and show_empty_fraction:
                                actual_fraction_color = self.colors['shadow']
                            else:
                                actual_fraction_color = fraction_color if fraction_color is not None else value_color

                            if vertical_fraction:
                                # Vertical fraction format (numerator over denominator)
                                numerator_text = str(numerator)
                                denominator_text = str(denominator)

                                num_width = 8 * actual_fraction_size * len(numerator_text)
                                denom_width = 8 * actual_fraction_size * len(denominator_text)
                                digit_height = 8 * actual_fraction_size
                                max_width = max(num_width, denom_width)

                                # Draw numerator (centered)
                                num_x = fraction_x - (num_width // 2)
                                self.format_text.center_or_position_text(
                                    numerator_text,
                                    actual_fraction_size,
                                    actual_fraction_color,
                                    center_x=False,
                                    center_y=False,
                                    x=num_x,
                                    y=fraction_y
                                )

                                # Draw division line
                                line_y = fraction_y + digit_height + 2
                                line_length = max_width + 4
                                self.lcd.hline(
                                    fraction_x - (line_length // 2),
                                    line_y,
                                    line_length,
                                    actual_fraction_color
                                )

                                # Draw denominator (centered)
                                denom_y = line_y + 4
                                denom_x = fraction_x - (denom_width // 2)
                                self.format_text.center_or_position_text(
                                    denominator_text,
                                    actual_fraction_size,
                                    actual_fraction_color,
                                    center_x=False,
                                    center_y=False,
                                    x=denom_x,
                                    y=denom_y
                                )
                            else:
                                # Horizontal fraction format (numerator/denominator)
                                fraction_text = f"{numerator}/{denominator}"
                                fraction_width = 8 * actual_fraction_size * len(fraction_text)
                                fraction_height = 8 * actual_fraction_size

                                self.format_text.center_or_position_text(
                                    fraction_text,
                                    actual_fraction_size,
                                    actual_fraction_color,
                                    center_x=False,
                                    center_y=False,
                                    x=fraction_x - (fraction_width // 2),
                                    y=fraction_y - (fraction_height // 2)
                                )
                    else:
                        # Combined format (e.g., "15 3/4")
                        if numerator > 0:
                            value_text = f"{integer_part} {numerator}/{denominator}"
                        else:
                            value_text = str(integer_part)
                else:
                    # Default raw format
                    value_text = str(value)

            # Calculate value position with offset
            value_x = center_x + value_offset_x
            value_y = center_y + value_offset_y

            text_width = 8 * value_size * len(value_text)
            text_height = 8 * value_size

            # Draw centered value text
            self.format_text.center_or_position_text(
                value_text,
                value_size,
                value_color,
                center_x=False,
                center_y=False,
                x=value_x - (text_width // 2),
                y=value_y - (text_height // 2)
            )

    def draw_dot_indicator(self, num_pages, active_page, dot_size, arc_radius, arc_span=40):
        """Draw page indicators arranged in an arc pattern.

        Creates a visual indicator system using dots arranged in an arc to show
        current page position within a multi-page interface.

        Args:
            num_pages (int): Total number of pages/dots to display.
            active_page (int): Index of active page (0 to num_pages-1).
            dot_size (int): Base diameter of each dot in pixels.
            arc_radius (int): Radius of the arc for dot placement.
            arc_span (int): Total angle in degrees for the arc. Defaults to 40.
        """
        # Apply theme colors for consistent styling
        colors = {
            'active': self.colors['text_body'],
            'inactive': self.colors['shadow']
        }

        # Screen center for 240x240 LCD
        cx, cy = 120, 120

        # Calculate angle positions for dots
        if num_pages <= 1:
            angles = [180]  # Single dot at bottom center
        else:
            start_angle = 180 + arc_span / 2
            step = arc_span / (num_pages - 1)
            angles = [start_angle - i * step for i in range(num_pages)]

        # Draw each dot at calculated position
        for i, angle in enumerate(angles):
            angle_rad = math.radians(angle) - math.pi / 2
            x = int(cx + arc_radius * math.cos(angle_rad))
            y = int(cy + arc_radius * math.sin(angle_rad))

            # Style active dot differently
            if i == active_page:
                color = colors['active']
                r = dot_size // 3  # Larger radius for active dot
            else:
                color = colors['inactive']
                r = dot_size // 4  # Smaller radius for inactive dots

            self.lcd.ellipse(x, y, r, r, color, True)

    def show_battery_icons(self, center_x=120, center_y=40):
        """Display battery status using themed icons based on current voltage.

        Shows appropriate battery icon from the ICONS dictionary based on current
        battery voltage levels, with special handling for USB power connection.

        Args:
            center_x (int): X coordinate for icon center. Defaults to 120.
            center_y (int): Y coordinate for icon center. Defaults to 40.

        Returns:
            str: Battery level displayed ('full', '75', '50', 'low', 'very_low', 'empty', 'usb', 'error').

        Note:
            Icons are 26x26 pixels and will be centered at the given coordinates.
            USB connection is detected when voltage > 4.5V.
        """
        # Get current battery voltage from power supply
        voltage = self.power_supply.read_battery_voltage

        # Handle USB connection (voltage > 4.5V indicates USB power)
        if voltage > 4.5:
            self.format_text.center_or_position_text_cached(
                "USB",
                2,
                self.colors['text_body'],
                center_x=True,
                x=center_x,
                center_y=False,
                y=center_y - 8
            )
            return "usb"

        # Determine battery level and icon based on voltage thresholds
        if voltage > 4.0:
            icon_key = "full"
            icon_color = self.colors['shadow']
        elif voltage > 3.8:
            icon_key = "75"
            icon_color = self.colors['shadow']
        elif voltage > 3.6:
            icon_key = "50"
            icon_color = self.colors['shadow']
        elif voltage > 3.4:
            icon_key = "low"
            icon_color = self.colors['shadow']
        elif voltage > 3.0:
            icon_key = "very_low"
            icon_color = self.colors['shadow']
        else:
            icon_key = "empty"
            icon_color = self.colors['warning']  # Critical level uses warning color

        # Render battery icon from ICONS dictionary
        if "battery" in ICONS and icon_key in ICONS["battery"]:
            icon_data = ICONS["battery"][icon_key]

            # Calculate position to center 26x26 pixel icon
            icon_x = center_x - 13
            icon_y = center_y - 13

            self.lcd.draw_bitmap_data(icon_data, icon_x, icon_y, icon_color)
            return icon_key
        else:
            # Error fallback if icon not found
            self.format_text.center_or_position_text(
                "Error",
                1,
                self.lcd.red,
                center_x=True,
                x=center_x,
                center_y=False,
                y=center_y - 8
            )
            return "error"

    def show_battery_monitor(self, center_x=120, center_y=40, size='M', style='default'):
        """Display battery status monitor with themed styling.

        Creates a visual battery level indicator using either segmented display
        or line-fill styles with automatic voltage-based level calculation.

        Args:
            center_x (int): X coordinate of monitor center. Defaults to 120.
            center_y (int): Y coordinate of monitor center. Defaults to 40.
            size (str): Monitor size - 'S', 'M', 'L'. Defaults to 'M'.
            style (str): Monitor style - 'default' or 'line'. Defaults to 'default'.
        """
        # Apply theme colors for consistent styling
        colors = {
            'charged': self.colors['text_body'],
            'discharged': self.colors['shadow'],
            'outline': self.colors['text_body'],
            'text': self.colors['shadow']
        }

        if style == 'line':
            # Line-fill style battery monitor
            SCALE_FACTORS = {
                'S': 0.5,
                'M': 0.75,
                'L': 1.0
            }

            BASE_DIMENSIONS = {
                'WIDTH': 40,
                'HEIGHT': 20,
                'PIN_WIDTH': 4,
                'PIN_HEIGHT': 8
            }

            # Apply size scaling
            scale = SCALE_FACTORS.get(size.upper(), 1.0)
            dims = {k: int(v * scale) for k, v in BASE_DIMENSIONS.items()}

            # Calculate battery outline position
            x_start = center_x - (dims['WIDTH'] // 2)
            y_start = center_y - (dims['HEIGHT'] // 2)

            voltage = self.power_supply.read_battery_voltage

            # Handle USB connection display
            if voltage > 4.5:
                text_size = max(1, int(2 * scale))
                self.format_text.center_or_position_text_cached(
                    "USB", text_size, self.colors['text_body'],
                    center_x=True, x=center_x, center_y=False, y=center_y
                )
                return

            # Calculate battery charge level (0-100%)
            if voltage > 4.0:
                level = 1.0
            elif voltage > 3.8:
                level = 0.8
            elif voltage > 3.6:
                level = 0.6
            elif voltage > 3.4:
                level = 0.4
            elif voltage > 3.0:
                level = 0.2
            else:
                level = 0.0

            # Calculate fill width including pin
            fill_width = int((dims['WIDTH'] + dims['PIN_WIDTH']) * level)

            # Draw battery outline (discharged state)
            self.lcd.fill_rect(
                x_start,
                y_start,
                dims['WIDTH'],
                dims['HEIGHT'],
                colors['discharged']
            )

            # Draw battery pin
            self.lcd.fill_rect(
                x_start + dims['WIDTH'],
                y_start + (dims['HEIGHT'] - dims['PIN_HEIGHT'])//2,
                dims['PIN_WIDTH'],
                dims['PIN_HEIGHT'],
                colors['discharged']
            )

            # Draw charged portion
            if fill_width > 0:
                # Fill main body first
                body_fill = min(fill_width, dims['WIDTH'])
                if body_fill > 0:
                    self.lcd.fill_rect(
                        x_start,
                        y_start,
                        body_fill,
                        dims['HEIGHT'],
                        colors['charged']
                    )

                # Fill pin if charge level extends to it
                if fill_width > dims['WIDTH']:
                    pin_fill = fill_width - dims['WIDTH']
                    self.lcd.fill_rect(
                        x_start + dims['WIDTH'],
                        y_start + (dims['HEIGHT'] - dims['PIN_HEIGHT'])//2,
                        pin_fill,
                        dims['PIN_HEIGHT'],
                        colors['charged']
                    )

        else:
            # Segmented style battery monitor (default)
            SCALE_FACTORS = {
                'S': 0.5,
                'M': 0.75,
                'L': 1.0
            }

            BASE_DIMENSIONS = {
                'BATTERY_WIDTH': 56,
                'BATTERY_HEIGHT': 24,
                'PIN_WIDTH': 6,
                'PIN_HEIGHT': 10,
                'SEGMENT_WIDTH': 8,
                'SEGMENT_HEIGHT': 16,
                'SEGMENT_SPACING': 10,
                'SEGMENT_MARGIN': 4
            }

            # Apply size scaling
            scale = SCALE_FACTORS.get(size.upper(), 1.0)
            dimensions = {k: int(v * scale) for k, v in BASE_DIMENSIONS.items()}

            TOTAL_SEGMENTS = 5
            voltage = self.power_supply.read_battery_voltage

            # Handle USB connection display
            if voltage > 4.5:
                text_size = max(1, int(2 * scale))
                self.format_text.center_or_position_text_cached(
                    "USB",
                    text_size,
                    self.colors['text_body'],
                    center_x=True,
                    x=center_x,
                    center_y=False,
                    y=center_y
                )
                return

            # Calculate battery position for centering
            x_initial = center_x - (dimensions['BATTERY_WIDTH'] // 2)
            y_initial = center_y - (dimensions['BATTERY_HEIGHT'] // 2)

            # Determine active segments based on voltage levels
            if voltage > 4.0:
                active_segments = 5
            elif voltage > 3.8:
                active_segments = 4
            elif voltage > 3.6:
                active_segments = 3
            elif voltage > 3.4:
                active_segments = 2
            elif voltage > 3.0:
                active_segments = 1
            else:
                active_segments = 0

            # Draw battery outline with double border
            self.lcd.rect(x_initial, y_initial,
                        dimensions['BATTERY_WIDTH'],
                        dimensions['BATTERY_HEIGHT'],
                        colors['outline'])

            # Inner border for better definition
            inner_margin = max(1, int(1 * scale))
            self.lcd.rect(x_initial + inner_margin,
                        y_initial + inner_margin,
                        dimensions['BATTERY_WIDTH'] - (2 * inner_margin),
                        dimensions['BATTERY_HEIGHT'] - (2 * inner_margin),
                        colors['outline'])

            # Draw battery pin/terminal
            pin_y = y_initial + (dimensions['BATTERY_HEIGHT'] - dimensions['PIN_HEIGHT']) // 2
            self.lcd.fill_rect(x_initial + dimensions['BATTERY_WIDTH'],
                            pin_y,
                            dimensions['PIN_WIDTH'],
                            dimensions['PIN_HEIGHT'],
                            colors['outline'])

            # Draw charge level segments
            for i in range(TOTAL_SEGMENTS):
                segment_x = x_initial + dimensions['SEGMENT_MARGIN'] + (i * dimensions['SEGMENT_SPACING'])
                segment_y = y_initial + (dimensions['BATTERY_HEIGHT'] - dimensions['SEGMENT_HEIGHT']) // 2
                color = colors['charged'] if i < active_segments else colors['discharged']
                self.lcd.fill_rect(segment_x,
                                segment_y,
                                dimensions['SEGMENT_WIDTH'],
                                dimensions['SEGMENT_HEIGHT'],
                                color)

    def draw_rounded_button(self, x, y, text, text_size=2, button_color=None, text_color=None):
        """Draw a rounded rectangular button with centered text.

        Creates a pill-shaped button using semicircles and a rectangle with properly
        centered text content and theme-aware styling.

        Args:
            x (int): X coordinate for button center.
            y (int): Y coordinate for button center.
            text (str): Text to display inside the button.
            text_size (int): Font size for button text. Defaults to 2.
            button_color (int, optional): RGB565 color for button background.
                Defaults to theme primary color.
            text_color (int, optional): RGB565 color for button text.
                Defaults to theme on_primary color.
        """
        # Button styling constants
        BUTTON = {
            'HEIGHT': 52,
            'PADDING': 20,
            'RADIUS': 26,  # HEIGHT/2 for perfect semicircles
            'MASK_RIGHT': 0x9,  # Quadrants 1 and 4 for right semicircle
            'MASK_LEFT': 0x6    # Quadrants 2 and 3 for left semicircle
        }

        # Apply default theme colors
        button_color = button_color if button_color is not None else self.colors['primary']
        text_color = text_color if text_color is not None else self.colors['on_primary']

        # Calculate text dimensions and button width
        text_width = 8 * text_size * len(text)
        button_width = text_width + (BUTTON['PADDING'] * 2)

        # Calculate button position for centering
        button_x = x - (button_width // 2)
        button_y = y - (BUTTON['HEIGHT'] // 2)

        # Draw central rectangle
        self.lcd.rect(
            button_x + BUTTON['RADIUS'],
            button_y,
            button_width - (BUTTON['RADIUS'] * 2),
            BUTTON['HEIGHT'] + 1,
            button_color,
            True
        )

        # Draw left semicircle
        self.lcd.ellipse(
            button_x + BUTTON['RADIUS'],
            y,
            BUTTON['RADIUS'],
            BUTTON['RADIUS'],
            button_color,
            True,
            BUTTON['MASK_LEFT']
        )

        # Draw right semicircle
        self.lcd.ellipse(
            button_x + button_width - BUTTON['RADIUS'],
            y,
            BUTTON['RADIUS'],
            BUTTON['RADIUS'],
            button_color,
            True,
            BUTTON['MASK_RIGHT']
        )

        # Draw centered text
        text_x = x - (text_width // 2)
        text_y = y - (8 * text_size // 2)

        self.format_text.center_or_position_text(
            text,
            text_size,
            text_color,
            center_x=False,
            center_y=False,
            x=text_x,
            y=text_y
        )

    def draw_split_value(self, value, x=120, y=120, integer_size=5, fraction_size=6,
                        single_size=7, text_color=None):
        """Display a value with separate integer and fractional parts.

        Renders numeric values with distinct styling for integer and fractional
        components, useful for displaying precise measurements or calculations.

        Args:
            value (str): Value to display with integer and decimal parts separated by space.
            x (int): X coordinate of display center. Defaults to 120.
            y (int): Y coordinate of display center. Defaults to 120.
            integer_size (int): Font size for integer part. Defaults to 5.
            fraction_size (int): Font size for fractional part. Defaults to 6.
            single_size (int): Font size for single value. Defaults to 7.
            text_color (int, optional): RGB565 color for text. Defaults to theme text_title.
        """
        # Apply default theme color
        display_color = text_color if text_color is not None else self.colors['text_title']

        if value and " " in value:
            integer_part, fraction_part = value.split(" ")

            # Display integer part with secondary theme color
            self.format_text.center_or_position_text(
                integer_part,
                integer_size,
                self.colors['text_body'],
                center_x=True,
                center_y=False,
                y=45
            )

            # Display fractional part with specified or primary theme color
            self.format_text.center_or_position_text(
                fraction_part,
                fraction_size,
                display_color,
                center_x=True,
                center_y=True
            )
        else:
            # Display single value with specified color
            self.format_text.center_or_position_text(
                value,
                single_size,
                display_color,
                center_x=True,
                center_y=True
            )

    def show_grid(self):
        """Display a development grid overlay on the LCD.

        Draws a 10x10 pixel grid with center lines for layout assistance
        during development and debugging phases.

        Examples:
            >>> widget_manager.show_grid()
        """
        # Use theme text color for grid lines
        grid_color = self.colors['text_title']

        # Draw center cross lines
        self.lcd.vline(119, 0, 240, grid_color)  # Vertical center line
        self.lcd.hline(0, 119, 240, grid_color)  # Horizontal center line

        # Draw 10-pixel grid overlay
        for i in range(0, 240, 10):
            self.lcd.hline(0, i, 240, grid_color)
            self.lcd.vline(i, 0, 240, grid_color)

    def draw_circle_button(self, x, y, icon_key, button_color=None, background_color=None, size="default", icon_offset_x=0, icon_offset_y=0):
        """Draw a circular button with centered icon from ICONS dictionary.

        Creates a circular button with precise icon positioning and size-aware
        icon selection for consistent UI element styling.

        Args:
            x (int): X coordinate of button center.
            y (int): Y coordinate of button center.
            icon_key (str): Key for icon in ICONS dictionary.
            button_color (int, optional): RGB565 color for button.
                Defaults to theme primary color.
            background_color (int, optional): RGB565 color for icon.
                Defaults to theme background color.
            size (str): Button size ("default" = 52px, "large" = 60px). Defaults to "default".
            icon_offset_x (int): X offset for icon positioning. Defaults to 0.
            icon_offset_y (int): Y offset for icon positioning. Defaults to 0.

        Returns:
            tuple: Button position and radius (x, y, radius) for touch detection.

        Examples:
            >>> # Draw accept button with check icon
            >>> button_pos = widget_manager.draw_circle_button(120, 200, "check", 0x07E0, 0x0000)
            >>> # Draw large button with adjusted icon position
            >>> button_pos = widget_manager.draw_circle_button(120, 200, "check", size="large", icon_offset_x=2)
        """
        # Define size-specific constants
        if size == "large":
            BUTTON_RADIUS = 30  # 60px diameter
            ICON_SUFFIX = "_30"
            ICON_OFFSET_X = 7     # Half of 30px icon width
            ICON_OFFSET_Y = 15     # Half of 30px icon height
        else:  # default
            BUTTON_RADIUS = 26  # 52px diameter
            ICON_SUFFIX = "_26"
            ICON_OFFSET_X = 7     # Half of 26px icon width
            ICON_OFFSET_Y = 13     # Half of 26px icon height

        # Apply default theme colors
        button_color = button_color if button_color is not None else self.colors['primary']
        background_color = background_color if background_color is not None else self.colors['background']

        # Select appropriate icon based on size with fallback logic
        icon_with_size = f"{icon_key}{ICON_SUFFIX}" if not icon_key.endswith(ICON_SUFFIX) else icon_key

        if icon_with_size in ICONS:
            icon_data = ICONS[icon_with_size]
        elif icon_key in ICONS:
            icon_data = ICONS[icon_key]
        else:
            # Fallback to default check icon
            default_icon = f"check{ICON_SUFFIX}"
            icon_data = ICONS[default_icon]

        # Draw button circle
        self.lcd.ellipse(
            x,
            y,
            BUTTON_RADIUS,
            BUTTON_RADIUS,
            button_color,
            True
        )

        # Draw icon with precise centering and optional offset
        icon_x = x - ICON_OFFSET_X + icon_offset_x
        icon_y = y - ICON_OFFSET_Y + icon_offset_y
        self.lcd.draw_bitmap_data(icon_data, icon_x, icon_y, background_color)

        # Return position data for touch detection
        return (x, y, BUTTON_RADIUS)