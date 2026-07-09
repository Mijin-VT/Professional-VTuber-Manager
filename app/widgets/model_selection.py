"""Model Selection Page — Modern design.
Elegant model browser with cards, progress bars, and category filtering.
"""

import customtkinter as ctk
from app.widgets.signals import Signal
from typing import Optional

from app.config_manager import ConfigManager
from app.hardware import HardwareInfo
from app.download_manager import DownloadManager, DownloadStatus
from app.model_catalog import MODEL_CATALOG, CATEGORY_INFO, get_model_by_id
from app.theme import COLORS as C, SPACING, RADIUS, font, font_bold, font_heading, font_subheading


class ModelCard(ctk.CTkFrame):
    """A single model card with modern styling."""

    def __init__(self, model_entry, parent, on_accept, on_cancel, on_delete):
        super().__init__(
            parent, fg_color=C["bg_tertiary"], corner_radius=RADIUS["lg"],
            border_width=1, border_color=C["border"],
        )
        self._model = model_entry
        self._on_accept = on_accept
        self._on_cancel = on_cancel
        self._on_delete_cb = on_delete
        self._build_ui()

    def _build_ui(self):
        self.grid_columnconfigure(0, weight=1)

        # Header row
        header = ctk.CTkFrame(self, fg_color="transparent")
        header.grid(row=0, column=0, sticky="ew", padx=SPACING["lg"], pady=(SPACING["lg"], 0))
        header.grid_columnconfigure(0, weight=1)

        title = ctk.CTkLabel(
            header, text=self._model.name,
            font=font_bold(14),
            text_color=C["text_primary"],
        )
        title.grid(row=0, column=0, sticky="w")

        # Size badge
        size_badge = ctk.CTkLabel(
            header, text=f"{self._model.size_gb:.1f} GB",
            font=font_bold(9),
            text_color=C["accent"],
            fg_color=C["border_accent"],
            corner_radius=RADIUS["sm"],
            height=22, width=60,
        )
        size_badge.grid(row=0, column=1, sticky="e")

        # Description
        desc = ctk.CTkLabel(
            self, text=self._model.description,
            font=font(11), text_color=C["text_secondary"],
            wraplength=600, justify="left",
        )
        desc.grid(row=1, column=0, padx=SPACING["lg"], pady=(SPACING["xs"], SPACING["sm"]), sticky="w")

        # Metadata row
        meta_text = f"Quantization: {self._model.quantization}   |   VRAM: {self._model.recommended_vram_mb // 1024}GB+   |   Layers: {self._model.total_layers}"
        meta = ctk.CTkLabel(
            self, text=meta_text,
            font=font(9), text_color=C["text_muted"],
        )
        meta.grid(row=2, column=0, padx=SPACING["lg"], pady=(0, SPACING["sm"]), sticky="w")

        # Warning
        if self._model.warning:
            warn = ctk.CTkLabel(
                self, text=f"  {self._model.warning}",
                font=font(9), text_color=C["accent_amber"],
            )
            warn.grid(row=3, column=0, padx=SPACING["lg"], pady=(0, SPACING["sm"]), sticky="w")

        # Progress bar
        self._progress = ctk.CTkProgressBar(
            self, corner_radius=RADIUS["sm"], height=4,
            progress_color=C["accent"], fg_color=C["border"],
        )
        self._progress.grid(row=4, column=0, padx=SPACING["lg"], pady=(0, SPACING["xs"]), sticky="ew")
        self._progress.set(0)

        # Bottom row: status + buttons
        bottom = ctk.CTkFrame(self, fg_color="transparent")
        bottom.grid(row=5, column=0, sticky="ew", padx=SPACING["lg"], pady=(SPACING["xs"], SPACING["lg"]))
        bottom.grid_columnconfigure(0, weight=1)

        self._status = ctk.CTkLabel(
            bottom, text="Ready to download", font=font(9),
            text_color=C["text_muted"],
        )
        self._status.grid(row=0, column=0, sticky="w")

        btn_frame = ctk.CTkFrame(bottom, fg_color="transparent")
        btn_frame.grid(row=0, column=1, sticky="e")

        self._accept_btn = ctk.CTkButton(
            btn_frame, text="Download",
            font=font_bold(11),
            fg_color=C["accent"], hover_color=C["accent_hover"],
            text_color="#FFFFFF", corner_radius=RADIUS["sm"],
            height=30, width=100,
            command=lambda: self._on_accept(self._model.id),
        )
        self._accept_btn.pack(side="left")

        self._cancel_btn = ctk.CTkButton(
            btn_frame, text="Cancel",
            font=font(11),
            fg_color="transparent", hover_color=C["bg_hover"],
            text_color=C["accent_red"], corner_radius=RADIUS["sm"],
            height=30, width=70, state="disabled",
            border_width=1, border_color=C["accent_red"],
            command=lambda: self._on_cancel(self._model.id),
        )
        self._cancel_btn.pack(side="left", padx=(SPACING["sm"], 0))

        self._delete_btn = ctk.CTkButton(
            btn_frame, text="Delete",
            font=font(11),
            fg_color="transparent", hover_color=C["bg_hover"],
            text_color=C["accent_amber"], corner_radius=RADIUS["sm"],
            height=30, width=70, state="disabled",
            border_width=1, border_color=C["accent_amber"],
            command=lambda: self._on_delete(self._model.id),
        )
        self._delete_btn.pack(side="left", padx=(SPACING["sm"], 0))

    def update_progress(self, percent: float, status: str):
        self._progress.set(percent)
        self._status.configure(text=status, text_color=C["text_secondary"])

    def mark_complete(self):
        self._accept_btn.configure(state="disabled", text="Downloaded")
        self._cancel_btn.configure(state="disabled")
        self._delete_btn.configure(state="normal")
        self._progress.set(1.0)
        self._progress.configure(progress_color=C["accent_green"])
        self._status.configure(text="Downloaded & Verified", text_color=C["accent_green"])

    def mark_failed(self, error: str):
        self._accept_btn.configure(state="normal")
        self._cancel_btn.configure(state="disabled")
        self._delete_btn.configure(state="disabled")
        self._progress.configure(progress_color=C["accent_red"])
        self._status.configure(text=f"Failed: {error}", text_color=C["accent_red"])

    def _on_delete(self, model_id: str):
        self._on_delete_cb(model_id)


class ModelSelectionPage(ctk.CTkScrollableFrame):
    """Model selection page with category tabs and model cards."""

    download_started = Signal(str)
    download_cancelled = Signal(str)
    download_progress = Signal(str, float, str)
    download_completed = Signal(str)
    download_failed = Signal(str, str)
    model_deleted = Signal(str)

    def __init__(self, parent, config: ConfigManager, hardware: HardwareInfo,
                 download_mgr: DownloadManager):
        super().__init__(parent, fg_color=C["bg_primary"],
                         scrollbar_button_color=C["scrollbar"],
                         scrollbar_button_hover_color=C["border_hover"])
        self._config = config
        self._hardware = hardware
        self._download_mgr = download_mgr
        self._recommended = hardware.recommended_category
        self._selected_cat = self._recommended
        self._model_cards: dict[str, ModelCard] = {}
        self._build_ui()

    def _build_ui(self):
        self.grid_columnconfigure(0, weight=1)

        # Header section
        header_frame = ctk.CTkFrame(self, fg_color="transparent")
        header_frame.pack(fill="x", padx=SPACING["xl"], pady=(SPACING["xl"], SPACING["sm"]))

        ctk.CTkLabel(
            header_frame,
            text=f"Your GPU: {self._hardware.gpu_name}  —  {self._hardware.vram_total_mb}MB VRAM",
            font=font(11), text_color=C["text_secondary"],
        ).pack(anchor="w")

        ctk.CTkLabel(
            header_frame,
            text=f"Recommended tier: {self._recommended.upper()}",
            font=font_bold(11), text_color=C["accent"],
        ).pack(anchor="w", pady=(SPACING["xs"], 0))

        # Category tabs
        tab_frame = ctk.CTkFrame(self, fg_color="transparent")
        tab_frame.pack(fill="x", padx=SPACING["xl"], pady=(SPACING["md"], SPACING["lg"]))

        self._cat_buttons = {}
        for cat_id in ["large", "medium", "light2", "light"]:
            info = CATEGORY_INFO[cat_id]
            is_active = cat_id == self._selected_cat
            btn = ctk.CTkButton(
                tab_frame,
                text=info['title'],
                font=font_bold(11) if is_active else font(11),
                fg_color=C["accent"] if is_active else "transparent",
                hover_color=C["accent_hover"] if is_active else C["bg_hover"],
                text_color="#FFFFFF" if is_active else C["text_secondary"],
                corner_radius=RADIUS["pill"], height=32, width=120,
                border_width=1,
                border_color=C["accent"] if is_active else C["border"],
                command=lambda c=cat_id: self._select_category(c),
            )
            btn.pack(side="left", padx=(0, SPACING["sm"]))
            btn._cat_id = cat_id
            self._cat_buttons[cat_id] = btn

        # Model cards container
        self._cards_layout = ctk.CTkFrame(self, fg_color="transparent")
        self._cards_layout.pack(fill="both", expand=True, padx=SPACING["xl"], pady=(0, SPACING["xl"]))

        self._populate_cards()

    def _select_category(self, cat_id: str):
        self._selected_cat = cat_id
        for btn in self._cat_buttons.values():
            cid = btn._cat_id
            is_active = cid == cat_id
            btn.configure(
                fg_color=C["accent"] if is_active else "transparent",
                text_color="#FFFFFF" if is_active else C["text_secondary"],
                hover_color=C["accent_hover"] if is_active else C["bg_hover"],
                border_color=C["accent"] if is_active else C["border"],
            )

        for card in self._model_cards.values():
            cat = card._model.category
            if cat == cat_id:
                card.pack(fill="x", pady=SPACING["sm"])
            else:
                card.pack_forget()

    def _populate_cards(self):
        for model in MODEL_CATALOG:
            card = ModelCard(
                model, self._cards_layout,
                on_accept=self._on_accept,
                on_cancel=self._on_cancel,
                on_delete=self._on_delete,
            )
            self._model_cards[model.id] = card
            
            # Check if model file already exists on disk
            dest = self._download_mgr._models_dir / model.huggingface_filename
            if dest.exists() and dest.stat().st_size > 0:
                self._download_mgr.add_task(
                    model_id=model.id,
                    url=f"https://huggingface.co/{model.huggingface_repo}/resolve/main/{model.huggingface_filename}",
                    sha256_url=(
                        f"https://huggingface.co/{model.huggingface_repo}/resolve/"
                        f"main/{model.huggingface_filename}.sha256"
                    ),
                    filename=model.huggingface_filename,
                )
                task = self._download_mgr.get_task(model.id)
                task.status = DownloadStatus.COMPLETED
                task.progress = 1.0
                task.total_size = dest.stat().st_size
                task.downloaded_bytes = task.total_size
                card.mark_complete()

            if model.category == self._selected_cat:
                card.pack(fill="x", pady=SPACING["sm"])

    def _on_accept(self, model_id: str):
        model = get_model_by_id(model_id)
        if not model:
            return

        def progress_cb(pct, downloaded, total, speed_mbps=0.0, eta_str="Calculating..."):
            self.download_progress.emit(
                model_id, pct,
                f"Downloading... {speed_mbps:.1f} MB/s | {downloaded // 1024 // 1024}MB / {total // 1024 // 1024}MB | ETA: {eta_str}"
            )

        def status_cb(status: str):
            if status == "verifying":
                self.download_progress.emit(model_id, 1.0, "Verifying SHA256...")
            elif status == "completed":
                self.download_completed.emit(model_id)
            elif status == "failed":
                self.download_failed.emit(model_id, "Download failed")

        task = self._download_mgr.add_task(
            model_id=model.id,
            url=f"https://huggingface.co/{model.huggingface_repo}/resolve/main/{model.huggingface_filename}",
            sha256_url=(
                f"https://huggingface.co/{model.huggingface_repo}/resolve/"
                f"main/{model.huggingface_filename}.sha256"
            ),
            progress_callback=progress_cb,
            status_callback=status_cb,
            filename=model.huggingface_filename,
        )
        self._download_mgr.start_download(model.id)

    def _on_cancel(self, model_id: str):
        self._download_mgr.cancel_download(model_id)
        self.download_cancelled.emit(model_id)

    def _on_delete(self, model_id: str):
        self._download_mgr.delete_model(model_id)
        self.model_deleted.emit(model_id)

    def reset_download(self, model_id: str):
        card = self._model_cards.get(model_id)
        if card:
            card._accept_btn.configure(state="normal", text="Download")
            card._delete_btn.configure(state="disabled")
            card.update_progress(0, "Ready to download")

    def update_progress(self, model_id: str, percent: float, status: str):
        card = self._model_cards.get(model_id)
        if card:
            card.update_progress(percent, status)

    def complete_download(self, model_id: str):
        card = self._model_cards.get(model_id)
        if card:
            card.mark_complete()

    def fail_download(self, model_id: str, error: str):
        card = self._model_cards.get(model_id)
        if card:
            card.mark_failed(error)
