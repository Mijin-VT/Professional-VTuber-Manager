"""Debug runner — captures all exceptions and writes to debug_log.txt"""
import sys
import os
import traceback
import logging

# Disable Mem0 Telemetry to prevent PostHog library compatibility issues
os.environ["MEM0_TELEMETRY"] = "False"

# Set up file logging
logging.basicConfig(
    filename="debug_log.txt",
    level=logging.DEBUG,
    format="%(asctime)s [%(levelname)s] %(name)s: %(message)s",
    force=True,
)
logger = logging.getLogger("VTManager")

# Also log to console
console = logging.StreamHandler()
console.setLevel(logging.DEBUG)
logger.addHandler(console)

# Redirect stderr to file as well
class StderrLogger:
    def __init__(self, original):
        self.original = original
        self.log_file = open("debug_stderr.txt", "w", encoding="utf-8")
    def write(self, msg):
        self.original.write(msg)
        self.log_file.write(msg)
        self.log_file.flush()
    def flush(self):
        self.original.flush()
        self.log_file.flush()

sys.stderr = StderrLogger(sys.stderr)

sys.path.insert(0, os.path.dirname(__file__))

def main():
    logger.info("Starting VT Manager in debug mode...")
    
    try:
        import customtkinter as ctk
        logger.info("CustomTkinter imported OK")
    except Exception as e:
        logger.error(f"Failed to import customtkinter: {e}")
        return

    try:
        from ctypes import windll
        windll.shcore.SetProcessDpiAwareness(1)
    except Exception:
        pass

    ctk.set_appearance_mode("Dark")
    ctk.set_default_color_theme("blue")

    try:
        from app.config_manager import ConfigManager
        from app.hardware import detect_hardware, get_hardware_summary
        from app.main_window import MainWindow
        logger.info("All modules imported OK")
    except Exception as e:
        logger.error(f"Import error: {e}\n{traceback.format_exc()}")
        return

    try:
        config = ConfigManager()
        hardware = detect_hardware()
        logger.info(f"Hardware: {get_hardware_summary(hardware)}")
    except Exception as e:
        logger.error(f"Config/Hardware error: {e}\n{traceback.format_exc()}")
        return

    try:
        app = MainWindow(config, hardware)
        logger.info("MainWindow created successfully")
        
        # Add global exception handler for Tkinter
        def report_callback_exception(exc_type, exc_value, exc_tb):
            error_msg = "".join(traceback.format_exception(exc_type, exc_value, exc_tb))
            logger.error(f"TKINTER EXCEPTION:\n{error_msg}")
            with open("debug_crash.txt", "a", encoding="utf-8") as f:
                f.write(f"\n{'='*60}\n")
                f.write(error_msg)
                f.write(f"\n{'='*60}\n")
        
        app.report_callback_exception = report_callback_exception
        
        logger.info("Starting mainloop...")
        app.mainloop()
        logger.info("App closed normally")
        
    except Exception as e:
        error_msg = traceback.format_exc()
        logger.error(f"FATAL ERROR:\n{error_msg}")
        with open("debug_crash.txt", "w", encoding="utf-8") as f:
            f.write(error_msg)

if __name__ == "__main__":
    main()
