"""Main module for Anubis Axis project.

This module serves as the entry point for the Anubis Axis application on Raspberry Pi Pico 2.
It initializes all hardware components (LCD display, touchscreen, encoder), configures
system parameters, and manages the main application lifecycle through the screen mediator
pattern. The module handles system diagnostics, hardware initialization, and launches
the primary user interface for the measurement and calibration system.

Memory management is critical on the 520KB SRAM RP2350: garbage collection runs periodically
in the main loop, and a cleanup handler ensures proper thread and resource release on exit.

Author: Seguridad Física
File: main.py
"""
import machine
import gc
import time

# Configure CPU frequency to 150MHz for optimal performance with GC9A01A LCD
machine.freq(150_000_000, 150_000_000)

from ui.logger import Logger  # Import Logger class for consistent logging
# Initialize logger early for system messages
logger = Logger()

# Import USB CDC data interface from boot.py
import usb.device
cdc_data = usb.device.cdc_data

# Memory management constants
MEMORY_CHECK_INTERVAL_MS = 2000  # Check memory every 2 seconds
MEMORY_CRITICAL_THRESHOLD = 40000  # Bytes - trigger warning
MEMORY_LOW_THRESHOLD = 50000  # Bytes - trigger aggressive GC
GC_ITERATION_COUNT = 20  # Run GC every N loop iterations (~2 seconds at 10ms per iteration)

def print_memory_info():
    """Display current memory usage statistics with threshold warnings.
    
    Performs garbage collection and logs detailed memory information including
    free, allocated, and total memory with percentage calculations. Includes
    critical threshold warnings for memory-constrained RP2350 operation.
    
    Essential for monitoring memory usage on the 520KB SRAM Raspberry Pi Pico 2.
    
    Returns:
        int: Free memory in bytes for programmatic checks
    
    Examples:
        >>> free_bytes = print_memory_info()
        # Logs: "Memory stats: free=450560, used=69440, total=520000, % free=86.6%"
        # Returns: 450560
    """
    gc.collect()  # Force garbage collection before measurement
    free = gc.mem_free()
    alloc = gc.mem_alloc()
    total = free + alloc
    pct_free = (free / total) * 100
    
    logger.info(f"Memory: {pct_free:.1f}% free ({free}/{total} bytes)")
    
    # Threshold warnings
    if free < MEMORY_CRITICAL_THRESHOLD:
        logger.critical(f"CRITICAL: Only {free} bytes free!")
    elif free < MEMORY_LOW_THRESHOLD:
        logger.warning(f"LOW MEMORY: Only {free} bytes free")
    
    return free

def show_clock_speed():
    """Display current CPU frequency in MHz.
    
    Reads and logs the current CPU frequency, useful for verifying the
    150MHz configuration required for stable LCD and touchscreen operation.
    
    Examples:
        >>> show_clock_speed()
        # Logs: "CPU frequency: 150 MHz"
    """
    freq = machine.freq()  # Returns frequency in Hz
    logger.info(f"CPU frequency: {freq/1000000:.0f} MHz")

def cleanup():
    """Graceful shutdown and resource cleanup.
    
    Performs critical cleanup operations before program termination:
    - Stops the encoder background thread to prevent orphaned threads
    - Forces final garbage collection to free resources
    - Turns off LCD backlight to prevent power drain
    - Clears display to prevent stuck pixels
    
    This function MUST be called before program exit to ensure proper
    hardware state and prevent resource leaks.
    
    Examples:
        >>> cleanup()
        # Logs cleanup messages, stops threads, powers down hardware
    """
    logger.info("=== SHUTDOWN: Starting cleanup ===")
    
    try:
        # Stop encoder thread to prevent orphaned background thread
        logger.info("Stopping encoder thread...")
        encoder.stop()
        time.sleep_ms(50)  # Allow thread time to exit gracefully
    except Exception as e:
        logger.error(f"Error stopping encoder: {e}")
    
    try:
        # Final garbage collection
        logger.info("Running final garbage collection...")
        gc.collect()
        free = gc.mem_free()
        logger.info(f"Memory after cleanup: {free} bytes free")
    except Exception as e:
        logger.error(f"Error during GC: {e}")
    
    try:
        # Turn off LCD backlight to prevent power drain
        logger.info("Turning off LCD backlight...")
        lcd.set_bl_pwm(0)
    except Exception as e:
        logger.error(f"Error turning off backlight: {e}")
    
    try:
        # Clear display
        logger.info("Clearing display...")
        lcd.fill(0x0000)  # Black
        lcd.show()
    except Exception as e:
        logger.error(f"Error clearing display: {e}")
    
    logger.info("=== Cleanup complete ===")

def memory_monitor():
    """Monitor memory and trigger aggressive cleanup if needed.
    
    Periodically checks available memory and takes action if below thresholds:
    - Below MEMORY_LOW_THRESHOLD: runs immediate GC
    - Below MEMORY_CRITICAL_THRESHOLD: logs critical warning
    
    Returns:
        bool: True if memory is healthy, False if critical
    """
    free = gc.mem_free()
    
    if free < MEMORY_CRITICAL_THRESHOLD:
        logger.critical(f"MEMORY CRITICAL: {free} bytes (< {MEMORY_CRITICAL_THRESHOLD})")
        gc.collect()
        free = gc.mem_free()
        if free < MEMORY_CRITICAL_THRESHOLD:
            logger.critical("GC did not free enough memory - app may crash!")
            return False
    
    elif free < MEMORY_LOW_THRESHOLD:
        logger.warning(f"Memory low: {free} bytes (< {MEMORY_LOW_THRESHOLD})")
        gc.collect()
    
    return True
    
# Log initial system information for diagnostics
print_memory_info()
show_clock_speed() 

# Import hardware pin constants for peripheral initialization
from common.constants import SSI_CSN_PIN, SSI_CLK_PIN, SSI_D0_PIN # AS5311 encoder SSI pins
from common.constants import SPI_CS_PIN, SPI_DC_PIN, SPI_SCK_PIN, SPI_MOSI_PIN, SPI_RST_PIN, PWM_BACKLIGHT_PIN # GC9A01A LCD SPI and PWM pins
from common.constants import I2C_SDA_PIN, I2C_SDL_PIN, I2C_INT_PIN, I2C_RST_PIN # CST816T touchscreen I2C pins

from config.configuration import Configuration  # Configuration management class
# Initialize configuration early for hardware setup parameters
configuration = Configuration()

from drivers.lcd import GC9A01ALCD  # GC9A01A LCD driver class
# Initialize 1.28" 240x240 LCD display with SPI interface
lcd = GC9A01ALCD(
    cs_pin = SPI_CS_PIN,
    rst_pin = SPI_RST_PIN,
    sck_pin = SPI_SCK_PIN,
    mosi_pin = SPI_MOSI_PIN,
    dc_pin = SPI_DC_PIN,
    bl_pin = PWM_BACKLIGHT_PIN
)
# Apply configured brightness level to LCD backlight
lcd.set_bl_pwm(configuration.brightness)

from drivers.touchscreen import CST816TTouchScreen  # CST816T touchscreen driver class
# Initialize capacitive touchscreen with I2C interface
touch = CST816TTouchScreen(
    mode=2,  # Gesture detection mode
    i2c_sda=I2C_SDA_PIN,
    i2c_scl=I2C_SDL_PIN,
    int_pin=I2C_INT_PIN,
    rst_pin=I2C_RST_PIN
)
# Configure touchscreen for gesture recognition mode
touch.Mode = 2
touch.Set_Mode(touch.Mode)

# Import threaded encoder driver for non-blocking operation
from drivers.threaded_encoder import ThreadedAS5311Encoder
# Initialize 12-bit absolute encoder with SSI interface and threading support
encoder = ThreadedAS5311Encoder(
    CSn_pin=SSI_CSN_PIN,
    CLK_pin=SSI_CLK_PIN,
    D0_pin = SSI_D0_PIN,
    resolution= 12,  # 12-bit resolution (0-4095 values)
    speed_hz=1800,   # SSI communication speed
    hysteresis=1,    # Noise filtering threshold
    delay_s=0.01     # Background thread polling interval
)

from managers.screen_touch_mediator import ScreenTouchMediator # Screen coordination class
# Initialize mediator pattern for coordinating screen and input interactions
screen_touch_mediator = ScreenTouchMediator(lcd, touch, encoder, configuration)

from screens.logo_screen import LogoScreen # Initial logo display screen

# USB communication manager (currently disabled)
#from managers.usb_manager import USBManager
#usb_manager = USBManager(cdc_data, encoder=encoder, lcd=lcd, configuration=configuration)
#usb_manager.start()

def main():
    """Manage the lifecycle of the Anubis Axis application.

    This function initializes the logo screen, displays it for the configured duration,
    and then enters the main application loop managed by the screen touch mediator.
    The mediator handles all screen transitions, user interactions, and system states.

    The main loop continuously processes:
    - Screen rendering and updates
    - Touch gesture recognition
    - Encoder value changes
    - Screen state transitions
    - Periodic garbage collection for memory management
    - Memory threshold monitoring

    Memory Management:
    - Runs gc.collect() every GC_ITERATION_COUNT iterations (~2 seconds)
    - Monitors available memory against MEMORY_LOW_THRESHOLD and MEMORY_CRITICAL_THRESHOLD
    - Triggers aggressive cleanup if memory drops below safe levels
    - Ensures proper cleanup on exit or exception

    Examples:
        >>> main()
        # Displays logo screen, then enters interactive application mode with memory management
    """
    iteration_count = 0
    last_memory_check = 0
    
    try:
        # Create and display initial logo screen
        logger.info("Initializing logo screen...")
        logo_screen = LogoScreen(lcd, touch, encoder, configuration, screen_touch_mediator)
        logo_screen.show()  # Display logo for configured duration
        
        # Log memory usage after initialization
        logger.info("Application started - entering main loop")
        print_memory_info()
        
        # Enter main application loop - handles all user interactions and screen management
        while True:
            # Process current screen state and inputs
            screen_touch_mediator.run_current_screen()
            #usb_manager.process()  # Handle USB communications (disabled)
            
            # Periodic garbage collection - every GC_ITERATION_COUNT iterations
            iteration_count += 1
            if iteration_count >= GC_ITERATION_COUNT:
                gc.collect()
                iteration_count = 0
            
            # Periodic memory monitoring - every MEMORY_CHECK_INTERVAL_MS
            current_time = time.ticks_ms()
            if current_time - last_memory_check >= MEMORY_CHECK_INTERVAL_MS:
                memory_ok = memory_monitor()
                if not memory_ok:
                    logger.critical("Memory check failed - forcing cleanup")
                    break  # Exit loop to trigger cleanup
                last_memory_check = current_time
    
    except KeyboardInterrupt:
        logger.info("User interrupt detected (Ctrl+C)")
        cleanup()
        logger.info("Program terminated by user")
        return
    
    except Exception as e:
        logger.error(f"Fatal error in main loop: {e}")
        logger.error("Attempting emergency cleanup...")
        try:
            cleanup()
        except:
            logger.critical("Cleanup failed!")
        raise  # Re-raise to allow debugging

# Application entry point - run main function when script is executed directly
if __name__=='__main__':
    try:
        main()
    except KeyboardInterrupt:
        pass
    except Exception as e:
        logger.critical(f"Unhandled exception: {e}")
        cleanup()