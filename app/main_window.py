"""Main application window — CustomTkinter version.
Modern dark-themed UI with refined sidebar navigation.
"""

import os
import customtkinter as ctk
from pathlib import Path

from app.config_manager import ConfigManager
from app.hardware import HardwareInfo
from app.download_manager import DownloadManager
from app.chat_interface import ChatManager
from app.model_catalog import get_model_by_id
from app.theme import COLORS as C, SPACING, RADIUS, font, font_bold, font_heading

from app.widgets.model_selection import ModelSelectionPage
from app.widgets.chat_widget import ChatPage
from app.widgets.tasks_widget import TasksPage
from app.widgets.calendar_widget import CalendarPage
from app.widgets.stream_planning import PlanningPage
from app.widgets.metrics_widget import MetricsPage
from app.widgets.settings_widget import SettingsPage
from app.widgets.user_manual_widget import UserManualPage


NAV_ITEMS = [
    ("model", "Models", ""),
    ("chat", "AI Chat Manager", ""),
    ("calendar", "Schedule", ""),
    ("tasks", "Tasks", ""),
    ("planning", "Planning", ""),
    ("metrics", "Metrics", ""),
]


class NavButton(ctk.CTkButton):
    """Custom navigation button with indicator."""

    def __init__(self, parent, text, nav_id, command, **kwargs):
        super().__init__(
            parent,
            text=f"   {text}",
            font=font(13),
            fg_color="transparent",
            text_color=C["text_secondary"],
            hover_color=C["sidebar_hover"],
            height=42,
            corner_radius=RADIUS["md"],
            anchor="w",
            command=command,
            **kwargs,
        )
        self.nav_id = nav_id
        self._active = False

    def set_active(self, active: bool):
        self._active = active
        if active:
            self.configure(
                fg_color=C["sidebar_active"],
                text_color=C["text_primary"],
            )
        else:
            self.configure(
                fg_color="transparent",
                text_color=C["text_secondary"],
            )


class MainWindow(ctk.CTk):
    """Main application window."""

    def __init__(self, config: ConfigManager, hardware: HardwareInfo):
        super().__init__()

        self._config = config
        self._hardware = hardware
        self._download_mgr = DownloadManager(
            str(config.get("paths.models_dir", "./models"))
        )
        self._chat_mgr = ChatManager(config)

        from app.task_manager import TaskManager
        self._task_mgr = TaskManager(config)
        self._chat_mgr.set_task_mgr(self._task_mgr)

        from app.streaming_api import StreamingAPIManager
        self._stream_api = StreamingAPIManager(config)
        self._chat_mgr.set_stream_api(self._stream_api)
        self._stream_api.start()

        from app.voice_manager import VoiceManager
        self._voice_mgr = VoiceManager(config)
        
        # Restore and verify previously selected model on startup
        model_id = config.get("llama.selected_model", "")
        model_path = config.get("llama.selected_model_path", "")
        if model_id and model_path:
            p = config.resolve_path(model_path)
            if p.exists() and p.stat().st_size > 0:
                self._selected_model_id = model_id
                self._selected_model_path = str(p)
            else:
                self._selected_model_id = ""
                self._selected_model_path = ""
                config.set("llama.selected_model", "")
                config.set("llama.selected_model_path", "")
                config.save()
        else:
            self._selected_model_id = ""
            self._selected_model_path = ""

        self.title("VT Manager")
        self._set_window_icon()
        self.geometry("1280x800")
        self.minsize(1000, 650)
        self.configure(fg_color=C["bg_primary"])

        self.grid_columnconfigure(1, weight=1)
        self.grid_rowconfigure(0, weight=1)

        self._create_sidebar()
        self._create_main_area()
        self._connect_signals()
        self._switch_page("chat")
        self.protocol("WM_DELETE_WINDOW", self._on_close)

    def _set_window_icon(self):
        """Apply the VT Manager branding icon to the window and taskbar."""
        icons_dir = Path(__file__).parent.parent / "icons"

        ico_path = icons_dir / "vtmanager.ico"
        if ico_path.exists():
            try:
                self.iconbitmap(str(ico_path))
            except Exception as e:
                print(f"[MainWindow] Failed to set .ico window icon: {e}")

        # iconphoto as a cross-platform fallback / Alt-Tab preview source.
        # Keep a reference on self so it isn't garbage-collected.
        png_path = icons_dir / "vtmanager_64.png"
        if png_path.exists():
            try:
                import tkinter as tk
                self._icon_photo = tk.PhotoImage(file=str(png_path))
                self.iconphoto(True, self._icon_photo)
            except Exception as e:
                print(f"[MainWindow] Failed to set iconphoto: {e}")

    def _create_sidebar(self):
        """Create the left sidebar navigation."""
        self.sidebar = ctk.CTkFrame(
            self, width=200, fg_color=C["sidebar_bg"],
            corner_radius=0, border_width=0,
        )
        self.sidebar.grid(row=0, column=0, sticky="nsew")
        self.sidebar.grid_propagate(False)

        # App branding
        brand_frame = ctk.CTkFrame(self.sidebar, fg_color="transparent")
        brand_frame.pack(fill="x", padx=SPACING["lg"], pady=(SPACING["2xl"], SPACING["sm"]))

        ctk.CTkLabel(
            brand_frame, text="VT Manager",
            font=font_bold(18),
            text_color=C["accent"],
        ).pack(anchor="w")

        ctk.CTkLabel(
            brand_frame, text="AI-Powered VTuber Tools",
            font=font(10),
            text_color=C["text_muted"],
        ).pack(anchor="w", pady=(2, 0))

        # Separator
        sep = ctk.CTkFrame(self.sidebar, height=1, fg_color=C["border"])
        sep.pack(fill="x", padx=SPACING["lg"], pady=(SPACING["md"], SPACING["lg"]))

        # Navigation section label
        ctk.CTkLabel(
            self.sidebar, text="NAVIGATION",
            font=font_bold(9),
            text_color=C["text_muted"],
        ).pack(anchor="w", padx=SPACING["xl"], pady=(0, SPACING["sm"]))

        # Navigation buttons
        self._nav_buttons: dict[str, NavButton] = {}
        for nav_id, label, _ in NAV_ITEMS:
            btn = NavButton(
                self.sidebar, text=label, nav_id=nav_id,
                command=lambda nid=nav_id: self._switch_page(nid),
            )
            btn.pack(fill="x", padx=SPACING["sm"], pady=1)
            self._nav_buttons[nav_id] = btn

        # Spacer
        spacer = ctk.CTkFrame(self.sidebar, fg_color="transparent")
        spacer.pack(fill="both", expand=True)

        # Bottom section
        sep2 = ctk.CTkFrame(self.sidebar, height=1, fg_color=C["border"])
        sep2.pack(fill="x", padx=SPACING["lg"], pady=(0, SPACING["sm"]))

        # Settings button
        settings_btn = NavButton(
            self.sidebar, text="Settings", nav_id="settings",
            command=lambda: self._switch_page("settings"),
        )
        settings_btn.pack(fill="x", padx=SPACING["sm"], pady=1)
        self._nav_buttons["settings"] = settings_btn

        # User Manual button
        manual_btn = NavButton(
            self.sidebar, text="User Manual", nav_id="manual",
            command=lambda: self._switch_page("manual"),
        )
        manual_btn.pack(fill="x", padx=SPACING["sm"], pady=1)
        self._nav_buttons["manual"] = manual_btn

        # Hardware status
        hw_frame = ctk.CTkFrame(self.sidebar, fg_color=C["bg_tertiary"], corner_radius=RADIUS["md"])
        hw_frame.pack(fill="x", padx=SPACING["md"], pady=(SPACING["sm"], SPACING["lg"]))

        gpu_name = self._hardware.gpu_name or "Unknown GPU"
        if len(gpu_name) > 22:
            gpu_name = gpu_name[:20] + "..."

        ctk.CTkLabel(
            hw_frame, text=gpu_name,
            font=font(10),
            text_color=C["text_secondary"],
        ).pack(anchor="w", padx=SPACING["md"], pady=(SPACING["sm"], 2))

        vram_text = f"{self._hardware.vram_total_mb // 1024}GB VRAM"
        ctk.CTkLabel(
            hw_frame, text=vram_text,
            font=font(9),
            text_color=C["text_muted"],
        ).pack(anchor="w", padx=SPACING["md"], pady=(0, SPACING["sm"]))

    def _create_main_area(self):
        """Create the main content area."""
        self.main_frame = ctk.CTkFrame(
            self, fg_color=C["bg_primary"], corner_radius=0,
        )
        self.main_frame.grid(row=0, column=1, sticky="nsew", padx=0, pady=0)
        self.main_frame.grid_columnconfigure(0, weight=1)
        self.main_frame.grid_rowconfigure(1, weight=1)

        # Header bar
        self.header = ctk.CTkFrame(
            self.main_frame, height=52, fg_color=C["header_bg"],
            corner_radius=0, border_width=0,
        )
        self.header.grid(row=0, column=0, sticky="ew")
        self.header.grid_propagate(False)
        self.header.grid_columnconfigure(0, weight=1)

        self.header_title = ctk.CTkLabel(
            self.header,
            text="AI Chat Manager",
            font=font_heading(16),
            text_color=C["text_primary"],
        )
        self.header_title.grid(row=0, column=0, padx=SPACING["xl"], pady=SPACING["md"], sticky="w")

        # Status indicator
        self._status_label = ctk.CTkLabel(
            self.header,
            text="Ready",
            font=font(10),
            text_color=C["accent_green"],
        )
        self._status_label.grid(row=0, column=1, padx=SPACING["xl"], pady=SPACING["md"], sticky="e")

        # Content area with subtle border on left
        content_wrapper = ctk.CTkFrame(
            self.main_frame, fg_color=C["bg_primary"], corner_radius=0,
            border_width=1, border_color=C["border"],
        )
        content_wrapper.grid(row=1, column=0, sticky="nsew", padx=0, pady=0)
        content_wrapper.grid_columnconfigure(0, weight=1)
        content_wrapper.grid_rowconfigure(0, weight=1)

        # Pages
        self._pages = {}
        self._page_order = []

        self._pages["model"] = ModelSelectionPage(
            content_wrapper, self._config, self._hardware, self._download_mgr
        )
        self._page_order.append("model")

        self._pages["chat"] = ChatPage(
            content_wrapper, self._config, self._chat_mgr
        )
        self._page_order.append("chat")

        self._pages["calendar"] = CalendarPage(content_wrapper)
        self._page_order.append("calendar")

        self._pages["tasks"] = TasksPage(content_wrapper, self._task_mgr)
        self._page_order.append("tasks")

        self._pages["planning"] = PlanningPage(content_wrapper, self._config, self._chat_mgr)
        self._page_order.append("planning")

        self._pages["metrics"] = MetricsPage(content_wrapper)
        self._page_order.append("metrics")

        self._pages["settings"] = SettingsPage(content_wrapper, self._config)
        self._page_order.append("settings")

        self._pages["manual"] = UserManualPage(content_wrapper)
        self._page_order.append("manual")

        # Show first page
        for pid in self._page_order:
            self._pages[pid].grid(row=0, column=0, sticky="nsew")
            if pid != "chat":
                self._pages[pid].grid_remove()

    def _switch_page(self, page_id: str):
        """Switch to the given page."""
        for pid in self._page_order:
            self._pages[pid].grid_remove()

        self._pages[page_id].grid(row=0, column=0, sticky="nsew")

        # Refresh tasks page when switching to it
        if page_id == "tasks" and hasattr(self._pages["tasks"], "refresh_ui"):
            self._pages["tasks"].refresh_ui()

        titles = {
            "model": "Model Selection",
            "chat": "AI Chat Manager",
            "calendar": "Streaming Schedule",
            "tasks": "Tasks & To-Do",
            "planning": "Stream Planning",
            "metrics": "Metrics & Analytics",
            "settings": "Settings",
            "manual": "User Manual",
        }
        self.header_title.configure(text=titles.get(page_id, ""))

        for btn in self._nav_buttons.values():
            btn.set_active(btn.nav_id == page_id)

    def _connect_signals(self):
        """Connect download signals."""
        self._pages["model"].download_started.connect(self._on_download_started)
        self._pages["model"].download_cancelled.connect(self._on_download_cancelled)
        self._pages["model"].download_progress.connect(self._on_download_progress)
        self._pages["model"].download_completed.connect(self._on_download_completed)
        self._pages["model"].download_failed.connect(self._on_download_failed)
        self._pages["model"].model_deleted.connect(self._on_model_deleted)

    # ─── Download Handlers ───

    def _on_download_started(self, model_id: str):
        model = get_model_by_id(model_id)
        if model:
            self._selected_model_id = model_id
            self._status_label.configure(text="Downloading...", text_color=C["accent_amber"])

    def _on_download_cancelled(self, model_id: str):
        self._status_label.configure(text="Cancelled", text_color=C["text_muted"])

    def _on_download_progress(self, model_id: str, percent: float, status: str):
        self._pages["model"].update_progress(model_id, percent, status)

    def _on_download_completed(self, model_id: str):
        self._pages["model"].complete_download(model_id)
        model = get_model_by_id(model_id)
        if model:
            model_path = str(Path(
                self._config.get("paths.models_dir", "./models")
            ) / model.huggingface_filename)
            self._selected_model_id = model_id
            self._selected_model_path = model_path
            self._status_label.configure(text="Ready", text_color=C["accent_green"])
            self._config.set("llama.selected_model", model_id)
            self._config.set("llama.selected_model_path", model_path)
            self._config.save()

    def _on_download_failed(self, model_id: str, error: str):
        self._pages["model"].fail_download(model_id, error)
        self._status_label.configure(text="Error", text_color=C["accent_red"])

    def _on_model_deleted(self, model_id: str):
        self._pages["model"].reset_download(model_id)
        self._selected_model_id = ""
        self._selected_model_path = ""
        self._config.set("llama.selected_model", "")
        self._config.set("llama.selected_model_path", "")
        self._config.save()
        self._status_label.configure(text="Ready", text_color=C["accent_green"])

    def _on_close(self):
        """Handle window close event."""
        self.destroy()

    def destroy(self):
        """Stop local server, streaming manager, and voice manager on close."""
        try:
            self._chat_mgr.stop_server()
        except Exception:
            pass
        try:
            self._stream_api.stop()
        except Exception:
            pass
        try:
            if hasattr(self, "_voice_mgr"):
                if self._voice_mgr.is_recording():
                    self._voice_mgr.stop_recording()
                if self._voice_mgr.is_hands_free_running():
                    self._voice_mgr.stop_hands_free()
                if hasattr(self._voice_mgr, "stop_moss_tts_server"):
                    self._voice_mgr.stop_moss_tts_server()
        except Exception:
            pass
        super().destroy()
        # Force-terminate the entire Python process tree to avoid leaks or zombies
        import os
        os._exit(0)


