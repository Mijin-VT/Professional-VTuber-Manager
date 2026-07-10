"""Settings Page — Modern design.
Application configuration and hardware info display.
"""

import customtkinter as ctk
from tkinter import filedialog as fd, messagebox as msgbox

from app.config_manager import ConfigManager
from app.hardware import detect_hardware
from app.theme import COLORS as C, SPACING, RADIUS, font, font_bold, font_subheading


class SettingsPage(ctk.CTkScrollableFrame):
    """Settings page with hardware info, paths, and system prompt."""

    def __init__(self, parent, config: ConfigManager):
        super().__init__(parent, fg_color=C["bg_primary"],
                         scrollbar_button_color=C["scrollbar"],
                         scrollbar_button_hover_color=C["border_hover"])
        self._config = config
        self._hardware = detect_hardware()
        self._build_ui()

    def _build_ui(self):
        self.grid_columnconfigure(0, weight=1)

        # ─── Hardware Info Card ───
        hw_card = ctk.CTkFrame(self, fg_color=C["bg_tertiary"], corner_radius=RADIUS["lg"],
                                border_width=1, border_color=C["border"])
        hw_card.pack(fill="x", padx=SPACING["xl"], pady=(SPACING["xl"], SPACING["lg"]))
        hw_card.grid_columnconfigure(1, weight=1)

        ctk.CTkLabel(
            hw_card, text="Hardware Information",
            font=font_subheading(13), text_color=C["accent"],
        ).grid(row=0, column=0, padx=SPACING["lg"], pady=(SPACING["lg"], SPACING["sm"]),
               columnspan=2, sticky="w")

        hw_info = [
            ("GPU", self._hardware.gpu_name or "Unknown"),
            ("VRAM", f"{self._hardware.vram_total_mb} MB"),
            ("RAM", f"{self._hardware.ram_total_mb} MB"),
            ("CUDA", "Available" if self._hardware.cuda_available else "Not available"),
            ("Recommended Tier", self._hardware.recommended_category.upper()),
        ]

        for i, (label, value) in enumerate(hw_info):
            row = i + 1
            ctk.CTkLabel(
                hw_card, text=label, font=font(11),
                text_color=C["text_muted"],
            ).grid(row=row, column=0, padx=(SPACING["lg"], SPACING["md"]), pady=3, sticky="w")
            ctk.CTkLabel(
                hw_card, text=value, font=font(11),
                text_color=C["text_primary"],
            ).grid(row=row, column=1, padx=(0, SPACING["lg"]), pady=3, sticky="w")

        # Padding at bottom of card
        ctk.CTkFrame(hw_card, fg_color="transparent", height=SPACING["md"]).grid(
            row=len(hw_info) + 1, column=0, columnspan=2)

        # ─── Paths Card ───
        paths_card = ctk.CTkFrame(self, fg_color=C["bg_tertiary"], corner_radius=RADIUS["lg"],
                                   border_width=1, border_color=C["border"])
        paths_card.pack(fill="x", padx=SPACING["xl"], pady=(0, SPACING["lg"]))
        paths_card.grid_columnconfigure(1, weight=1)

        ctk.CTkLabel(
            paths_card, text="Paths",
            font=font_subheading(13), text_color=C["accent"],
        ).grid(row=0, column=0, padx=SPACING["lg"], pady=(SPACING["lg"], SPACING["sm"]),
               columnspan=2, sticky="w")

        bin_dir = self._config.get("paths.bin_dir", "./bin")
        models_dir = self._config.get("paths.models_dir", "./models")

        ctk.CTkLabel(paths_card, text="Bin directory", font=font(11),
                      text_color=C["text_muted"]).grid(row=1, column=0, padx=(SPACING["lg"], SPACING["md"]), pady=3, sticky="w")
        ctk.CTkLabel(paths_card, text=bin_dir, font=font(11),
                      text_color=C["text_primary"]).grid(row=1, column=1, padx=(0, SPACING["lg"]), pady=3, sticky="w")

        ctk.CTkLabel(paths_card, text="Models directory", font=font(11),
                      text_color=C["text_muted"]).grid(row=2, column=0, padx=(SPACING["lg"], SPACING["md"]), pady=(3, SPACING["lg"]), sticky="w")
        ctk.CTkLabel(paths_card, text=models_dir, font=font(11),
                      text_color=C["text_primary"]).grid(row=2, column=1, padx=(0, SPACING["lg"]), pady=(3, SPACING["lg"]), sticky="w")

        # ─── Memory Settings Card ───
        mem_card = ctk.CTkFrame(self, fg_color=C["bg_tertiary"], corner_radius=RADIUS["lg"],
                                border_width=1, border_color=C["border"])
        mem_card.pack(fill="x", padx=SPACING["xl"], pady=(0, SPACING["lg"]))
        mem_card.grid_columnconfigure(1, weight=1)

        ctk.CTkLabel(
            mem_card, text="Long-Term Memory Configuration (Mem0)",
            font=font_subheading(13), text_color=C["accent"],
        ).grid(row=0, column=0, padx=SPACING["lg"], pady=(SPACING["lg"], SPACING["sm"]),
               columnspan=2, sticky="w")

        # 1. Enabled Switch
        self._mem_enabled_var = ctk.BooleanVar(value=self._config.get("memory.enabled", False))
        self._mem_enabled_switch = ctk.CTkSwitch(
            mem_card, text="Enable Long-Term Memory (Requires GGUF model loaded)", font=font(11),
            text_color=C["text_primary"], fg_color=C["border"], progress_color=C["accent"],
            variable=self._mem_enabled_var, command=self._on_mem_toggle
        )
        self._mem_enabled_switch.grid(row=1, column=0, columnspan=2, padx=SPACING["lg"], pady=SPACING["sm"], sticky="w")

        # 2. Info Label for Backend
        ctk.CTkLabel(
            mem_card, text="Memory Backend", font=font(11), text_color=C["text_muted"]
        ).grid(row=2, column=0, padx=(SPACING["lg"], SPACING["md"]), pady=SPACING["sm"], sticky="w")

        ctk.CTkLabel(
            mem_card, text="Llama CLI (Local, offline via llama-cli.exe)", font=font(11), text_color=C["text_primary"]
        ).grid(row=2, column=1, padx=(0, SPACING["lg"]), pady=SPACING["sm"], sticky="w")

        # 3. Clear button
        self._clear_mem_btn = ctk.CTkButton(
            mem_card, text="Clear Memory Database", font=font_bold(10),
            fg_color=C["accent_red"], hover_color="#D46B6B",
            text_color="#FFFFFF", corner_radius=RADIUS["sm"],
            height=30, command=self._clear_memory_db
        )
        self._clear_mem_btn.grid(row=3, column=0, columnspan=2, padx=SPACING["lg"], pady=(SPACING["sm"], SPACING["lg"]), sticky="w")

        # ─── Streaming API Settings Card ───
        stream_card = ctk.CTkFrame(self, fg_color=C["bg_tertiary"], corner_radius=RADIUS["lg"],
                                   border_width=1, border_color=C["border"])
        stream_card.pack(fill="x", padx=SPACING["xl"], pady=(0, SPACING["lg"]))
        stream_card.grid_columnconfigure((1, 3), weight=1)

        ctk.CTkLabel(
            stream_card, text="Streaming API Configuration (OBS, Twitch, Kick)",
            font=font_subheading(13), text_color=C["accent"],
        ).grid(row=0, column=0, padx=SPACING["lg"], pady=(SPACING["lg"], SPACING["sm"]),
               columnspan=4, sticky="w")

        # 1. Twitch Config
        self._twitch_enabled_var = ctk.BooleanVar(value=self._config.get("streaming.twitch_enabled", False))
        self._twitch_switch = ctk.CTkSwitch(
            stream_card, text="Enable Twitch Chat Monitoring", font=font(11),
            text_color=C["text_primary"], fg_color=C["border"], progress_color=C["accent"],
            variable=self._twitch_enabled_var, command=self._save_stream_settings
        )
        self._twitch_switch.grid(row=1, column=0, columnspan=2, padx=SPACING["lg"], pady=SPACING["xs"], sticky="w")

        ctk.CTkLabel(stream_card, text="Twitch Channel:", font=font(10), text_color=C["text_secondary"]).grid(
            row=2, column=0, padx=(SPACING["lg"], SPACING["md"]), pady=SPACING["xs"], sticky="w")
        
        self._twitch_channel_entry = ctk.CTkEntry(
            stream_card, font=font(10), height=28,
            fg_color=C["input_bg"], text_color=C["text_primary"],
            border_color=C["input_border"], border_width=1,
            corner_radius=RADIUS["sm"],
        )
        self._twitch_channel_entry.grid(row=2, column=1, padx=(0, SPACING["lg"]), pady=SPACING["xs"], sticky="ew")
        self._twitch_channel_entry.insert(0, self._config.get("streaming.twitch_channel", ""))
        self._twitch_channel_entry.bind("<KeyRelease>", lambda e: self._save_stream_settings())

        # 2. Kick Config
        self._kick_enabled_var = ctk.BooleanVar(value=self._config.get("streaming.kick_enabled", False))
        self._kick_switch = ctk.CTkSwitch(
            stream_card, text="Enable Kick Metrics", font=font(11),
            text_color=C["text_primary"], fg_color=C["border"], progress_color=C["accent"],
            variable=self._kick_enabled_var, command=self._save_stream_settings
        )
        self._kick_switch.grid(row=1, column=2, columnspan=2, padx=SPACING["lg"], pady=SPACING["xs"], sticky="w")

        ctk.CTkLabel(stream_card, text="Kick Channel:", font=font(10), text_color=C["text_secondary"]).grid(
            row=2, column=2, padx=(SPACING["lg"], SPACING["md"]), pady=SPACING["xs"], sticky="w")
        
        self._kick_channel_entry = ctk.CTkEntry(
            stream_card, font=font(10), height=28,
            fg_color=C["input_bg"], text_color=C["text_primary"],
            border_color=C["input_border"], border_width=1,
            corner_radius=RADIUS["sm"],
        )
        self._kick_channel_entry.grid(row=2, column=3, padx=(0, SPACING["lg"]), pady=SPACING["xs"], sticky="ew")
        self._kick_channel_entry.insert(0, self._config.get("streaming.kick_channel", ""))
        self._kick_channel_entry.bind("<KeyRelease>", lambda e: self._save_stream_settings())

        # Separator line
        ctk.CTkFrame(stream_card, fg_color=C["border"], height=1).grid(
            row=3, column=0, columnspan=4, padx=SPACING["lg"], pady=SPACING["sm"], sticky="ew")

        # 3. OBS Config
        self._obs_enabled_var = ctk.BooleanVar(value=self._config.get("streaming.obs_enabled", False))
        self._obs_switch = ctk.CTkSwitch(
            stream_card, text="Enable OBS Studio Connection", font=font(11),
            text_color=C["text_primary"], fg_color=C["border"], progress_color=C["accent"],
            variable=self._obs_enabled_var, command=self._save_stream_settings
        )
        self._obs_switch.grid(row=4, column=0, columnspan=4, padx=SPACING["lg"], pady=SPACING["xs"], sticky="w")

        # OBS details
        ctk.CTkLabel(stream_card, text="Host:Port:", font=font(10), text_color=C["text_secondary"]).grid(
            row=5, column=0, padx=(SPACING["lg"], SPACING["md"]), pady=SPACING["xs"], sticky="w")
        
        self._obs_host_entry = ctk.CTkEntry(
            stream_card, font=font(10), height=28,
            fg_color=C["input_bg"], text_color=C["text_primary"],
            border_color=C["input_border"], border_width=1,
            corner_radius=RADIUS["sm"],
        )
        self._obs_host_entry.grid(row=5, column=1, padx=(0, SPACING["lg"]), pady=SPACING["xs"], sticky="ew")
        host = self._config.get("streaming.obs_host", "localhost")
        port = self._config.get("streaming.obs_port", "4455")
        self._obs_host_entry.insert(0, f"{host}:{port}")
        self._obs_host_entry.bind("<KeyRelease>", lambda e: self._save_stream_settings())

        ctk.CTkLabel(stream_card, text="Password:", font=font(10), text_color=C["text_secondary"]).grid(
            row=5, column=2, padx=(SPACING["lg"], SPACING["md"]), pady=SPACING["xs"], sticky="w")
        
        self._obs_password_entry = ctk.CTkEntry(
            stream_card, font=font(10), height=28, show="*",
            fg_color=C["input_bg"], text_color=C["text_primary"],
            border_color=C["input_border"], border_width=1,
            corner_radius=RADIUS["sm"],
        )
        self._obs_password_entry.grid(row=5, column=3, padx=(0, SPACING["lg"]), pady=SPACING["xs"], sticky="ew")
        self._obs_password_entry.insert(0, self._config.get("streaming.obs_password", ""))
        self._obs_password_entry.bind("<KeyRelease>", lambda e: self._save_stream_settings())

        # Test button
        test_obs_btn = ctk.CTkButton(
            stream_card, text="🔌 Test OBS Connection", font=font_bold(10),
            fg_color=C["accent"], hover_color=C["accent_hover"],
            text_color="#FFFFFF", corner_radius=RADIUS["sm"],
            height=28, width=150, command=self._test_obs_connection
        )
        test_obs_btn.grid(row=6, column=0, columnspan=4, padx=SPACING["lg"], pady=(SPACING["sm"], SPACING["lg"]), sticky="w")

        # ─── Voice Settings Card ───
        voice_card = ctk.CTkFrame(self, fg_color=C["bg_tertiary"], corner_radius=RADIUS["lg"],
                                  border_width=1, border_color=C["border"])
        voice_card.pack(fill="x", padx=SPACING["xl"], pady=(0, SPACING["lg"]))
        voice_card.grid_columnconfigure((1, 3), weight=1)

        ctk.CTkLabel(
            voice_card, text="Voice Interaction Settings (VAD, STT & TTS)",
            font=font_subheading(13), text_color=C["accent"],
        ).grid(row=0, column=0, padx=SPACING["lg"], pady=(SPACING["lg"], SPACING["sm"]),
               columnspan=4, sticky="w")

        # Switches
        self._stt_enabled_var = ctk.BooleanVar(value=self._config.get("voice.stt_enabled", False))
        self._stt_switch = ctk.CTkSwitch(
            voice_card, text="Enable Voice Input (Microphone -> STT)", font=font(11),
            text_color=C["text_primary"], fg_color=C["border"], progress_color=C["accent"],
            variable=self._stt_enabled_var, command=self._save_voice_settings
        )
        self._stt_switch.grid(row=1, column=0, columnspan=2, padx=SPACING["lg"], pady=SPACING["xs"], sticky="w")

        self._tts_enabled_var = ctk.BooleanVar(value=self._config.get("voice.tts_enabled", False))
        self._tts_switch = ctk.CTkSwitch(
            voice_card, text="Enable Voice Output (Astra TTS)", font=font(11),
            text_color=C["text_primary"], fg_color=C["border"], progress_color=C["accent"],
            variable=self._tts_enabled_var, command=self._save_voice_settings
        )
        self._tts_switch.grid(row=1, column=2, columnspan=2, padx=SPACING["lg"], pady=SPACING["xs"], sticky="w")

        # Engine & Language
        ctk.CTkLabel(voice_card, text="TTS Engine:", font=font(10), text_color=C["text_secondary"]).grid(
            row=2, column=0, padx=(SPACING["lg"], SPACING["md"]), pady=SPACING["xs"], sticky="w")
        
        self._tts_engine_segmented = ctk.CTkSegmentedButton(
            voice_card, font=font(10), height=28,
            fg_color=C["input_bg"], selected_color=C["accent"],
            selected_hover_color=C["accent_hover"], text_color=C["text_primary"],
            values=["Lily-TTS (gTTS + pydub)", "SAPI5 (Windows Native)"],
            command=lambda v: self._save_voice_settings()
        )
        self._tts_engine_segmented.grid(row=2, column=1, padx=(0, SPACING["lg"]), pady=SPACING["xs"], sticky="ew")
        
        current_engine = self._config.get("voice.tts_engine", "lily-tts")
        if current_engine == "sapi5":
            self._tts_engine_segmented.set("SAPI5 (Windows Native)")
        else:
            self._tts_engine_segmented.set("Lily-TTS (gTTS + pydub)")

        ctk.CTkLabel(voice_card, text="Voice Language:", font=font(10), text_color=C["text_secondary"]).grid(
            row=2, column=2, padx=(SPACING["lg"], SPACING["md"]), pady=SPACING["xs"], sticky="w")
        
        self._voice_lang_combo = ctk.CTkComboBox(
            voice_card, font=font(10), height=28,
            fg_color=C["input_bg"], dropdown_fg_color=C["bg_tertiary"],
            text_color=C["text_primary"], button_color=C["accent"],
            button_hover_color=C["accent_hover"], border_color=C["input_border"],
            values=["auto", "es", "en", "ja"],
            command=lambda v: self._save_voice_settings()
        )
        self._voice_lang_combo.grid(row=2, column=3, padx=(0, SPACING["lg"]), pady=SPACING["xs"], sticky="ew")
        self._voice_lang_combo.set(self._config.get("voice.language", "auto"))

        # Row 3: Wake Word & VAD Threshold (Sensitivity)
        ctk.CTkLabel(voice_card, text="Wake Word:", font=font(9), text_color=C["text_muted"]).grid(
            row=3, column=0, padx=(SPACING["lg"], SPACING["md"]), pady=(SPACING["xs"], SPACING["lg"]), sticky="w")
        self._wake_word_entry = ctk.CTkEntry(
            voice_card, font=font(9), height=24,
            fg_color=C["input_bg"], text_color=C["text_primary"],
            border_color=C["input_border"], border_width=1,
            corner_radius=RADIUS["sm"],
        )
        self._wake_word_entry.grid(row=3, column=1, padx=(0, SPACING["lg"]), pady=(SPACING["xs"], SPACING["lg"]), sticky="ew")
        self._wake_word_entry.insert(0, self._config.get("voice.wake_word", "astra"))
        self._wake_word_entry.bind("<KeyRelease>", lambda e: self._save_voice_settings())

        # VAD Slider Frame
        ctk.CTkLabel(voice_card, text="VAD Threshold:", font=font(9), text_color=C["text_muted"]).grid(
            row=3, column=2, padx=(SPACING["lg"], SPACING["md"]), pady=(SPACING["xs"], SPACING["lg"]), sticky="w")
        
        slider_frame = ctk.CTkFrame(voice_card, fg_color="transparent")
        slider_frame.grid(row=3, column=3, padx=(0, SPACING["lg"]), pady=(SPACING["xs"], SPACING["lg"]), sticky="ew")
        slider_frame.grid_columnconfigure(0, weight=1)

        self._vad_threshold_slider = ctk.CTkSlider(
            slider_frame, from_=100, to=2000, number_of_steps=19,
            height=16, fg_color=C["border"], progress_color=C["accent"],
            command=self._on_vad_slider_change
        )
        self._vad_threshold_slider.grid(row=0, column=0, sticky="ew")
        self._vad_threshold_slider.set(self._config.get("voice.vad_threshold", 500))

        self._vad_val_lbl = ctk.CTkLabel(
            slider_frame, text=str(int(self._vad_threshold_slider.get())),
            font=font(9), text_color=C["text_primary"], width=30
        )
        self._vad_val_lbl.grid(row=0, column=1, padx=(SPACING["xs"], 0))

        # ─── System Prompt Card ───
        prompt_card = ctk.CTkFrame(self, fg_color=C["bg_tertiary"], corner_radius=RADIUS["lg"],
                                    border_width=1, border_color=C["border"])
        prompt_card.pack(fill="both", expand=True, padx=SPACING["xl"], pady=(0, SPACING["xl"]))
        prompt_card.grid_columnconfigure(0, weight=1)
        prompt_card.grid_rowconfigure(1, weight=1)

        ctk.CTkLabel(
            prompt_card, text="System Prompt",
            font=font_subheading(13), text_color=C["accent"],
        ).grid(row=0, column=0, padx=SPACING["lg"], pady=(SPACING["lg"], SPACING["sm"]), sticky="w")

        self._prompt_editor = ctk.CTkTextbox(
            prompt_card, font=font(11),
            fg_color=C["input_bg"], text_color=C["text_primary"],
            border_color=C["input_border"], border_width=1,
            corner_radius=RADIUS["md"], wrap="word",
        )
        self._prompt_editor.grid(row=1, column=0, padx=SPACING["lg"], pady=(0, SPACING["sm"]), sticky="nsew")
        self._prompt_editor.insert("0.0", self._config.get("chat.system_prompt", ""))

        save_btn = ctk.CTkButton(
            prompt_card, text="Save System Prompt",
            font=font_bold(11),
            fg_color=C["accent"], hover_color=C["accent_hover"],
            text_color="#FFFFFF", corner_radius=RADIUS["sm"],
            height=34, width=160,
            command=self._save_system_prompt,
        )
        save_btn.grid(row=2, column=0, padx=SPACING["lg"], pady=(0, SPACING["lg"]), sticky="e")



    def _save_system_prompt(self):
        self._config.set("chat.system_prompt", self._prompt_editor.get("0.0", "end-1c"))
        self._config.save()

    def _on_mem_toggle(self):
        enabled = self._mem_enabled_var.get()
        self._config.set("memory.enabled", enabled)
        self._config.save()

        # Try to reload the memory manager on the active chat page if it exists
        try:
            current = self.master
            while current and not hasattr(current, "_chat_mgr"):
                current = current.master
            if current and hasattr(current, "_chat_mgr"):
                current._chat_mgr.mem0_mgr.reload()
                print("[SettingsPage] Reloaded active ChatManager Mem0 instance.")
        except Exception as e:
            print(f"[SettingsPage] Could not reload mem0 manager dynamically: {e}")

    def _clear_memory_db(self):
        if not msgbox.askyesno("Confirm", "Are you sure you want to clear all stored memories? This cannot be undone."):
            return

        try:
            chat_mgr = None
            current = self.master
            while current and not hasattr(current, "_chat_mgr"):
                current = current.master
            if current and hasattr(current, "_chat_mgr"):
                chat_mgr = current._chat_mgr

            from app.mem0_manager import Mem0Manager
            mem_mgr = Mem0Manager(self._config, chat_mgr=chat_mgr)
            # Force enable to run clear
            mem_mgr.enabled = True
            success = mem_mgr.clear_memories(user_id="vtuber_user")
            if success:
                msgbox.showinfo("Success", "Memory database cleared successfully!")
            else:
                msgbox.showerror("Error", "Failed to clear memory database.")
        except Exception as e:
            msgbox.showerror("Error", f"Failed to clear memory database: {str(e)}")

    def _save_stream_settings(self):
        """Lee los campos de la UI y los guarda en config."""
        self._config.set("streaming.twitch_enabled", self._twitch_enabled_var.get())
        self._config.set("streaming.twitch_channel", self._twitch_channel_entry.get().strip())
        self._config.set("streaming.kick_enabled", self._kick_enabled_var.get())
        self._config.set("streaming.kick_channel", self._kick_channel_entry.get().strip())
        self._config.set("streaming.obs_enabled", self._obs_enabled_var.get())
        
        # Parsear Host:Port
        hp = self._obs_host_entry.get().strip()
        if ":" in hp:
            parts = hp.split(":", 1)
            host = parts[0]
            try:
                port = int(parts[1])
            except ValueError:
                port = 4455
        else:
            host = hp
            port = 4455
            
        self._config.set("streaming.obs_host", host)
        self._config.set("streaming.obs_port", port)
        self._config.set("streaming.obs_password", self._obs_password_entry.get())
        self._config.save()

        # Recargar manager de streaming dinámicamente en la ventana principal
        try:
            current = self.master
            while current and not hasattr(current, "_stream_api"):
                current = current.master
            if current and hasattr(current, "_stream_api"):
                current._stream_api.stop()
                current._stream_api.twitch_enabled = self._twitch_enabled_var.get()
                current._stream_api.twitch_channel = self._twitch_channel_entry.get().strip()
                current._stream_api.kick_enabled = self._kick_enabled_var.get()
                current._stream_api.kick_channel = self._kick_channel_entry.get().strip()
                current._stream_api.obs_enabled = self._obs_enabled_var.get()
                current._stream_api.obs_host = host
                current._stream_api.obs_port = port
                current._stream_api.obs_password = self._obs_password_entry.get()
                current._stream_api.start()
                print("[SettingsPage] Reconfigured active StreamingAPIManager dynamically.")
        except Exception as e:
            print(f"[SettingsPage] Could not reload streaming api dynamically: {e}")

    def _test_obs_connection(self):
        """Prueba de forma síncrona la conexión a OBS."""
        self._save_stream_settings()
        from app.streaming_api import StreamingAPIManager
        api_mgr = StreamingAPIManager(self._config)
        success, msg = api_mgr.test_obs_connection()
        if success:
            msgbox.showinfo("OBS Connection", msg)
        else:
            msgbox.showerror("OBS Connection", msg)

    def _on_vad_slider_change(self, value):
        self._vad_val_lbl.configure(text=str(int(value)))
        self._save_voice_settings()

    def _save_voice_settings(self):
        """Lee los campos de la UI de voz y los guarda en config."""
        engine_display = self._tts_engine_segmented.get()
        engine_val = "sapi5" if "SAPI5" in engine_display else "lily-tts"
            
        self._config.set("voice.stt_enabled", self._stt_enabled_var.get())
        self._config.set("voice.tts_enabled", self._tts_enabled_var.get())
        self._config.set("voice.tts_engine", engine_val)
        self._config.set("voice.language", self._voice_lang_combo.get())
        self._config.set("voice.wake_word", self._wake_word_entry.get().strip())
        self._config.set("voice.vad_threshold", int(self._vad_threshold_slider.get()))
        self._config.save()

        # Recargar configuración en el VoiceManager dinámicamente
        try:
            current = self.master
            while current and not hasattr(current, "_voice_mgr"):
                current = current.master
            if current and hasattr(current, "_voice_mgr"):
                if hasattr(current._voice_mgr, "reconfigure_tts"):
                    current._voice_mgr.reconfigure_tts(
                        stt_enabled=self._stt_enabled_var.get(),
                        tts_enabled=self._tts_enabled_var.get(),
                        tts_engine=engine_val,
                        language=self._voice_lang_combo.get(),
                        wake_word=self._wake_word_entry.get().strip(),
                        vad_threshold=int(self._vad_threshold_slider.get())
                    )
                else:
                    current._voice_mgr.stt_enabled = self._stt_enabled_var.get()
                    current._voice_mgr.tts_enabled = self._tts_enabled_var.get()
                    current._voice_mgr.tts_engine = engine_val
                    current._voice_mgr.language = self._voice_lang_combo.get()
                    current._voice_mgr.wake_word = self._wake_word_entry.get().strip()
                    current._voice_mgr.vad_threshold = int(self._vad_threshold_slider.get())
                print("[SettingsPage] Reconfigured active VoiceManager dynamically.")
        except Exception as e:
            print(f"[SettingsPage] Could not reload voice manager config dynamically: {e}")
