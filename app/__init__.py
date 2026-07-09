import os

# Disable Mem0 Telemetry to prevent PostHog library compatibility issues globally
os.environ["MEM0_TELEMETRY"] = "False"

from app.config_manager import ConfigManager
from app.hardware import detect_hardware, HardwareInfo
from app.model_catalog import MODEL_CATALOG, CATEGORY_INFO, get_model_by_id
from app.download_manager import DownloadManager, DownloadStatus
from app.chat_interface import ChatManager

__all__ = [
    "ConfigManager",
    "HardwareInfo",
    "detect_hardware",
    "MODEL_CATALOG",
    "CATEGORY_INFO",
    "get_model_by_id",
    "DownloadManager",
    "DownloadStatus",
    "ChatManager",
]
