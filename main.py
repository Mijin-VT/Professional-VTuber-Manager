"""VT Manager — Main entry point.
Professional VTuber management & content creation assistant.
"""

import sys
import os

# Disable Mem0 Telemetry to prevent PostHog library compatibility issues
os.environ["MEM0_TELEMETRY"] = "False"

sys.path.insert(0, os.path.dirname(__file__))

import customtkinter as ctk

# ─── DPI Awareness (fixes segfault on Windows) ───
try:
    from ctypes import windll
    windll.shcore.SetProcessDpiAwareness(1)
except Exception:
    pass

# ─── CustomTkinter init (MUST be before any CTk widget) ───
ctk.set_appearance_mode("Dark")
ctk.set_default_color_theme("blue")


from app.config_manager import ConfigManager
from app.hardware import detect_hardware, get_hardware_summary
from app.main_window import MainWindow


def main():
    """Application entry point."""
    config = ConfigManager()
    hardware = detect_hardware()

    print("=== VT Manager — Hardware Detection ===")
    print(get_hardware_summary(hardware))
    print("======================================")

    app = MainWindow(config, hardware)
    app.mainloop()


if __name__ == "__main__":
    main()
