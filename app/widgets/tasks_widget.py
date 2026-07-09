"""Tasks Page — Modern design.
Task management with priorities, add/complete/delete.
"""

import customtkinter as ctk
from app.widgets.signals import Signal
from app.theme import COLORS as C, SPACING, RADIUS, font, font_bold, font_subheading
from datetime import datetime


from app.task_manager import TaskItem


PRIORITY_COLORS = {
    "high": C["accent_red"],
    "medium": C["accent_amber"],
    "low": C["accent_green"],
}

PRIORITY_LABELS = {
    "high": "HIGH",
    "medium": "MED",
    "low": "LOW",
}


class TaskRow(ctk.CTkFrame):
    """A single task row with modern styling."""

    def __init__(self, parent, task: TaskItem, on_toggle, on_delete):
        super().__init__(
            parent, fg_color=C["bg_tertiary"], corner_radius=RADIUS["md"],
            border_width=1, border_color=C["border"],
            height=44,
        )
        self._task = task
        self._on_toggle = on_toggle
        self._on_delete = on_delete
        self._build_ui()

    def _build_ui(self):
        self.grid_columnconfigure(1, weight=1)
        self.grid_propagate(False)

        color = PRIORITY_COLORS.get(self._task.priority, C["text_muted"])

        self._checkbox = ctk.CTkCheckBox(
            self, text="", font=font(11),
            fg_color=color, hover_color=color,
            checkmark_color="#FFFFFF",
            corner_radius=4, height=20, width=20,
            border_width=2, border_color=color,
            command=self._toggle,
        )
        self._checkbox.grid(row=0, column=0, padx=(SPACING["md"], SPACING["sm"]), pady=SPACING["md"], sticky="w")
        if self._task.completed:
            self._checkbox.select()

        title_color = C["text_muted"] if self._task.completed else C["text_primary"]
        self._title = ctk.CTkLabel(
            self, text=self._task.title,
            font=font(12),
            text_color=title_color,
        )
        self._title.grid(row=0, column=1, padx=(0, SPACING["sm"]), pady=SPACING["md"], sticky="w")

        # Priority badge
        badge_text = PRIORITY_LABELS.get(self._task.priority, "MED")
        badge = ctk.CTkLabel(
            self, text=badge_text,
            font=font_bold(8),
            text_color=color,
            fg_color=C["bg_elevated"],
            corner_radius=4, height=20, width=36,
        )
        badge.grid(row=0, column=2, padx=(0, SPACING["sm"]), pady=SPACING["md"])

        del_btn = ctk.CTkButton(
            self, text="x", font=font(11),
            fg_color="transparent", hover_color=C["bg_hover"],
            text_color=C["text_muted"], corner_radius=RADIUS["sm"],
            height=24, width=24,
            command=self._delete,
        )
        del_btn.grid(row=0, column=3, padx=(0, SPACING["md"]), pady=SPACING["md"])

    def _toggle(self):
        self._on_toggle()

    def _delete(self):
        self._on_delete()


class TasksPage(ctk.CTkScrollableFrame):
    """Task management page."""

    task_added = Signal(str)
    task_completed = Signal(int)
    task_deleted = Signal(int)

    def __init__(self, parent, task_mgr):
        super().__init__(parent, fg_color=C["bg_primary"],
                         scrollbar_button_color=C["scrollbar"],
                         scrollbar_button_hover_color=C["border_hover"])
        self._task_mgr = task_mgr
        self._build_ui()
        self.refresh_ui()

    def _build_ui(self):
        self.grid_columnconfigure(0, weight=1)

        # Input section
        input_frame = ctk.CTkFrame(self, fg_color=C["bg_tertiary"], corner_radius=RADIUS["lg"],
                                    border_width=1, border_color=C["border"])
        input_frame.pack(fill="x", padx=SPACING["xl"], pady=(SPACING["xl"], SPACING["lg"]))
        input_frame.grid_columnconfigure(0, weight=1)

        self._task_input = ctk.CTkEntry(
            input_frame, font=font(12), height=38,
            fg_color=C["input_bg"], text_color=C["text_primary"],
            border_color=C["input_border"], border_width=1,
            corner_radius=RADIUS["sm"],
            placeholder_text="Add a new task...",
        )
        self._task_input.grid(row=0, column=0, padx=SPACING["md"], pady=SPACING["md"], sticky="ew")

        self._priority_combo = ctk.CTkComboBox(
            input_frame, font=font(11), height=38, width=100,
            fg_color=C["input_bg"], dropdown_fg_color=C["bg_tertiary"],
            text_color=C["text_primary"],
            border_color=C["input_border"], border_width=1,
            button_color=C["accent"], button_hover_color=C["accent_hover"],
            corner_radius=RADIUS["sm"],
            values=["high", "medium", "low"],
        )
        self._priority_combo.grid(row=0, column=1, padx=(0, SPACING["sm"]), pady=SPACING["md"])
        self._priority_combo.set("medium")

        add_btn = ctk.CTkButton(
            input_frame, text="Add",
            font=font_bold(11),
            fg_color=C["accent"], hover_color=C["accent_hover"],
            text_color="#FFFFFF", corner_radius=RADIUS["sm"],
            height=38, width=70,
            command=self._add_task,
        )
        add_btn.grid(row=0, column=2, padx=(0, SPACING["md"]), pady=SPACING["md"])

        # Bind Enter
        self._task_input.bind("<Return>", lambda e: self._add_task())

        # Stats
        self._stats = ctk.CTkLabel(
            self, text="0 tasks",
            font=font(10), text_color=C["text_muted"],
        )
        self._stats.pack(anchor="w", padx=SPACING["xl"], pady=(0, SPACING["sm"]))

        # Task list
        self._task_list = ctk.CTkFrame(self, fg_color="transparent")
        self._task_list.pack(fill="both", expand=True, padx=SPACING["xl"], pady=(0, SPACING["xl"]))
        self._task_list.grid_columnconfigure(0, weight=1)

    def _add_task(self):
        text = self._task_input.get().strip()
        if not text:
            return
        priority = self._priority_combo.get()
        self._task_mgr.add_task(text, priority)
        self.refresh_ui()
        self._task_input.delete(0, "end")

    def refresh_ui(self):
        for widget in self._task_list.winfo_children():
            widget.destroy()

        for i, task in enumerate(self._task_mgr.tasks):
            row = TaskRow(
                self._task_list, task,
                on_toggle=lambda idx=i: self._toggle_complete(idx),
                on_delete=lambda idx=i: self._delete_task(idx),
            )
            row.pack(fill="x", pady=2)

        completed = sum(1 for t in self._task_mgr.tasks if t.completed)
        total = len(self._task_mgr.tasks)
        self._stats.configure(text=f"{completed}/{total} completed" if total else "No tasks yet")

    def _toggle_complete(self, idx: int):
        self._task_mgr.toggle_task(idx)
        self.refresh_ui()

    def _delete_task(self, idx: int):
        self._task_mgr.delete_task(idx)
        self.refresh_ui()

    def get_tasks(self) -> list[TaskItem]:
        return list(self._task_mgr.tasks)
