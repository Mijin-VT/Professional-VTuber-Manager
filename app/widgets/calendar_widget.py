"""Calendar Page — Modern design.
Streaming schedule calendar with a real month-grid view and event management.
"""

import calendar
import json
from pathlib import Path
import customtkinter as ctk
from tkinter import messagebox as msgbox
from app.widgets.signals import Signal
from app.theme import COLORS as C, SPACING, RADIUS, font, font_bold, font_subheading
from datetime import date


class StreamEvent:
    def __init__(self, title: str, date_obj: date,
                 platform: str = "twitch", duration_hours: int = 3,
                 notes: str = ""):
        self.title = title
        self.date = date_obj
        self.platform = platform
        self.duration_hours = duration_hours
        self.notes = notes

    def __str__(self) -> str:
        return (f"{self.date.strftime('%Y-%m-%d')}  |  {self.platform.upper()}  |  "
                f"{self.duration_hours}h  |  {self.title}")


PLATFORM_COLORS = {
    "twitch": "#9146FF",
    "youtube": "#FF0000",
    "kick": "#53FC18",
    "tiktok": "#FF0050",
}

MONTH_NAMES = ["January", "February", "March", "April", "May", "June", "July",
               "August", "September", "October", "November", "December"]
WEEKDAY_LABELS = ["Mon", "Tue", "Wed", "Thu", "Fri", "Sat", "Sun"]


class EventCard(ctk.CTkFrame):
    """A single event card with delete button."""

    def __init__(self, parent, event: StreamEvent, on_delete=None):
        platform_color = PLATFORM_COLORS.get(event.platform, C["accent"])
        super().__init__(
            parent, fg_color=C["bg_tertiary"], corner_radius=RADIUS["md"],
            border_width=1, border_color=C["border"],
        )
        self.grid_columnconfigure(1, weight=1)
        self._event = event
        self._on_delete = on_delete

        indicator = ctk.CTkFrame(
            self, width=4, fg_color=platform_color,
            corner_radius=2,
        )
        indicator.grid(row=0, column=0, rowspan=3, padx=(SPACING["md"], SPACING["sm"]),
                       pady=SPACING["md"], sticky="ns")

        ctk.CTkLabel(
            self, text=event.title,
            font=font_bold(12), text_color=C["text_primary"],
        ).grid(row=0, column=1, padx=(0, SPACING["md"]), pady=(SPACING["md"], 0), sticky="w")

        details = f"{event.platform.upper()}  •  {event.duration_hours}h  •  {event.date.strftime('%b %d, %Y')}"
        ctk.CTkLabel(
            self, text=details,
            font=font(10), text_color=C["text_muted"],
        ).grid(row=1, column=1, padx=(0, SPACING["md"]), pady=(0, SPACING["md"]), sticky="w")

        if on_delete:
            del_btn = ctk.CTkButton(
                self, text="✕", font=font_bold(10),
                fg_color="transparent", hover_color=C["accent_red"],
                text_color=C["text_muted"], corner_radius=RADIUS["sm"],
                height=22, width=22, command=self._delete,
            )
            del_btn.grid(row=0, column=2, padx=(SPACING["sm"], SPACING["md"]), pady=(SPACING["md"], 0), sticky="e")

    def _delete(self):
        if self._on_delete:
            self._on_delete(self._event)


class DayCell(ctk.CTkFrame):
    """A single clickable day cell inside the month grid."""

    CELL_HEIGHT = 56

    def __init__(self, parent, day_date: date, is_current_month: bool,
                 is_today: bool, is_selected: bool, platforms: list[str], on_click=None):
        super().__init__(
            parent,
            height=self.CELL_HEIGHT,
            fg_color=C["sidebar_active"] if is_selected else C["bg_tertiary"],
            corner_radius=RADIUS["sm"],
            border_width=2 if is_today else 1,
            border_color=C["accent"] if is_today else C["border"],
        )
        # CTkFrame reserves its own height even when children are packed —
        # keep the cell from growing to fit a default-sized child frame.
        self.pack_propagate(False)

        self._day_date = day_date
        self._on_click = on_click

        num_color = C["text_primary"] if is_current_month else C["text_muted"]
        if is_selected:
            num_color = C["text_primary"]

        num_label = ctk.CTkLabel(
            self, text=str(day_date.day),
            font=font_bold(11) if is_today else font(11),
            text_color=num_color,
            height=16,
        )
        num_label.pack(anchor="w", padx=SPACING["xs"], pady=(SPACING["xs"], 0))

        dots_frame = ctk.CTkFrame(self, fg_color="transparent", height=10, width=40)
        dots_frame.pack(anchor="w", padx=SPACING["xs"], pady=(2, SPACING["xs"]))
        dots_frame.pack_propagate(False)
        self._dots = []
        for platform in platforms[:4]:
            dot = ctk.CTkFrame(
                dots_frame, width=6, height=6, corner_radius=3,
                fg_color=PLATFORM_COLORS.get(platform, C["accent"]),
            )
            dot.pack(side="left", padx=1)
            self._dots.append(dot)

        # Make the whole cell (and its children) clickable
        for widget in (self, num_label, dots_frame, *self._dots):
            widget.bind("<Button-1>", self._handle_click)

    def _handle_click(self, _event=None):
        if self._on_click:
            self._on_click(self._day_date)


class CalendarPage(ctk.CTkScrollableFrame):
    """Streaming schedule — month-grid calendar with event management."""

    event_added = Signal(str, date)
    event_deleted = Signal(date)

    def __init__(self, parent):
        super().__init__(parent, fg_color=C["bg_primary"],
                         scrollbar_button_color=C["scrollbar"],
                         scrollbar_button_hover_color=C["border_hover"])
        self._events: dict[str, list[StreamEvent]] = {}

        self._data_dir = Path(__file__).parent.parent.parent / "data"
        self._events_path = self._data_dir / "calendar_events.json"

        today = date.today()
        self._today = today
        self._view_year = today.year
        self._view_month = today.month
        self._selected_date = today

        self._build_ui()
        self._load_events()

    # ─── Persistence ───

    def _save_events(self):
        try:
            self._data_dir.mkdir(parents=True, exist_ok=True)
            data = {}
            for date_key, event_list in self._events.items():
                event_data = [{
                    "title": ev.title,
                    "platform": ev.platform,
                    "duration_hours": ev.duration_hours,
                    "notes": ev.notes,
                } for ev in event_list]
                data[date_key] = event_data
            with open(self._events_path, "w", encoding="utf-8") as f:
                json.dump(data, f, indent=4, ensure_ascii=False)
        except Exception as e:
            print(f"[CalendarPage] Failed to save events: {e}")

    def _load_events(self):
        if not self._events_path.exists():
            return
        try:
            with open(self._events_path, "r", encoding="utf-8") as f:
                data = json.load(f)
            self._events = {}
            for date_key, event_list in data.items():
                try:
                    date_obj = date.fromisoformat(date_key)
                except ValueError:
                    continue
                parsed_events = [
                    StreamEvent(
                        title=item.get("title", ""),
                        date_obj=date_obj,
                        platform=item.get("platform", "twitch"),
                        duration_hours=item.get("duration_hours", 3),
                        notes=item.get("notes", ""),
                    )
                    for item in event_list
                ]
                self._events[date_key] = parsed_events
            self._refresh_month_grid()
            self._refresh_events()
        except Exception as e:
            print(f"[CalendarPage] Failed to load events: {e}")

    # ─── UI construction ───

    def _build_ui(self):
        self.grid_columnconfigure(0, weight=1)

        # ── Month navigation header ──
        nav_frame = ctk.CTkFrame(self, fg_color=C["bg_tertiary"], corner_radius=RADIUS["lg"],
                                  border_width=1, border_color=C["border"])
        nav_frame.pack(fill="x", padx=SPACING["xl"], pady=(SPACING["xl"], SPACING["md"]))
        nav_frame.grid_columnconfigure(1, weight=1)

        prev_btn = ctk.CTkButton(
            nav_frame, text="‹", font=font_bold(16), width=36, height=32,
            fg_color="transparent", hover_color=C["bg_hover"],
            text_color=C["text_primary"], corner_radius=RADIUS["sm"],
            command=self._go_prev_month,
        )
        prev_btn.grid(row=0, column=0, padx=(SPACING["md"], 0), pady=SPACING["md"])

        self._month_label = ctk.CTkLabel(
            nav_frame, text="", font=font_subheading(15), text_color=C["text_primary"],
        )
        self._month_label.grid(row=0, column=1, pady=SPACING["md"])

        next_btn = ctk.CTkButton(
            nav_frame, text="›", font=font_bold(16), width=36, height=32,
            fg_color="transparent", hover_color=C["bg_hover"],
            text_color=C["text_primary"], corner_radius=RADIUS["sm"],
            command=self._go_next_month,
        )
        next_btn.grid(row=0, column=2, pady=SPACING["md"])

        today_btn = ctk.CTkButton(
            nav_frame, text="Today", font=font_bold(11), width=64, height=32,
            fg_color=C["accent"], hover_color=C["accent_hover"],
            text_color="#FFFFFF", corner_radius=RADIUS["sm"],
            command=self._go_today,
        )
        today_btn.grid(row=0, column=3, padx=(0, SPACING["md"]), pady=SPACING["md"])

        # ── Weekday header row ──
        weekday_row = ctk.CTkFrame(self, fg_color="transparent")
        weekday_row.pack(fill="x", padx=SPACING["xl"], pady=(0, SPACING["xs"]))
        for i in range(7):
            weekday_row.grid_columnconfigure(i, weight=1, uniform="cal")
        for i, label in enumerate(WEEKDAY_LABELS):
            ctk.CTkLabel(
                weekday_row, text=label, font=font_bold(9), text_color=C["text_muted"],
            ).grid(row=0, column=i, sticky="ew")

        # ── Month grid ──
        self._grid_frame = ctk.CTkFrame(self, fg_color="transparent")
        self._grid_frame.pack(fill="x", padx=SPACING["xl"], pady=(0, SPACING["md"]))
        for i in range(7):
            self._grid_frame.grid_columnconfigure(i, weight=1, uniform="cal")

        # ── Selected day / events section ──
        events_header = ctk.CTkFrame(self, fg_color="transparent")
        events_header.pack(fill="x", padx=SPACING["xl"], pady=(SPACING["md"], SPACING["sm"]))

        self._events_title = ctk.CTkLabel(
            events_header, text="", font=font_subheading(13), text_color=C["text_primary"],
        )
        self._events_title.pack(anchor="w")

        self._events_frame = ctk.CTkFrame(self, fg_color="transparent")
        self._events_frame.pack(fill="x", padx=SPACING["xl"], pady=(0, SPACING["lg"]))

        # ── Add event form ──
        form_label = ctk.CTkLabel(
            self, text="Add New Event",
            font=font_subheading(13), text_color=C["text_primary"],
        )
        form_label.pack(anchor="w", padx=SPACING["xl"], pady=(0, SPACING["sm"]))

        form = ctk.CTkFrame(self, fg_color=C["bg_tertiary"], corner_radius=RADIUS["lg"],
                            border_width=1, border_color=C["border"])
        form.pack(fill="x", padx=SPACING["xl"], pady=(0, SPACING["xl"]))
        form.grid_columnconfigure(1, weight=1)

        ctk.CTkLabel(form, text="Title:", font=font(11), text_color=C["text_secondary"]).grid(
            row=0, column=0, padx=(SPACING["lg"], SPACING["sm"]), pady=SPACING["md"], sticky="w")
        self._event_title = ctk.CTkEntry(
            form, font=font(11), height=34,
            fg_color=C["input_bg"], text_color=C["text_primary"],
            border_color=C["input_border"], border_width=1,
            corner_radius=RADIUS["sm"],
            placeholder_text="Stream title...",
        )
        self._event_title.grid(row=0, column=1, columnspan=3, padx=(0, SPACING["lg"]), pady=SPACING["md"], sticky="ew")

        ctk.CTkLabel(form, text="Platform:", font=font(11), text_color=C["text_secondary"]).grid(
            row=1, column=0, padx=(SPACING["lg"], SPACING["sm"]), pady=(0, SPACING["md"]), sticky="w")
        self._event_platform = ctk.CTkComboBox(
            form, font=font(11), height=34, width=130,
            fg_color=C["input_bg"], text_color=C["text_primary"],
            border_color=C["input_border"], border_width=1,
            button_color=C["accent"], button_hover_color=C["accent_hover"],
            corner_radius=RADIUS["sm"],
            values=["twitch", "youtube", "kick", "tiktok"],
        )
        self._event_platform.grid(row=1, column=1, padx=(0, SPACING["md"]), pady=(0, SPACING["md"]), sticky="w")
        self._event_platform.set("twitch")

        ctk.CTkLabel(form, text="Duration:", font=font(11), text_color=C["text_secondary"]).grid(
            row=1, column=2, padx=(0, SPACING["sm"]), pady=(0, SPACING["md"]), sticky="w")
        self._event_duration = ctk.CTkEntry(
            form, font=font(11), height=34, width=60,
            fg_color=C["input_bg"], text_color=C["text_primary"],
            border_color=C["input_border"], border_width=1,
            corner_radius=RADIUS["sm"],
        )
        self._event_duration.grid(row=1, column=3, padx=(0, SPACING["lg"]), pady=(0, SPACING["md"]), sticky="w")
        self._event_duration.insert(0, "3")

        add_btn = ctk.CTkButton(
            form, text="Add Event",
            font=font_bold(11),
            fg_color=C["accent"], hover_color=C["accent_hover"],
            text_color="#FFFFFF", corner_radius=RADIUS["sm"],
            height=34, width=110,
            command=self._add_event,
        )
        add_btn.grid(row=2, column=3, padx=(0, SPACING["lg"]), pady=(0, SPACING["lg"]), sticky="e")

        self._refresh_month_grid()
        self._refresh_events()

    # ─── Month grid logic ───

    def _go_prev_month(self):
        self._view_month -= 1
        if self._view_month < 1:
            self._view_month = 12
            self._view_year -= 1
        self._refresh_month_grid()

    def _go_next_month(self):
        self._view_month += 1
        if self._view_month > 12:
            self._view_month = 1
            self._view_year += 1
        self._refresh_month_grid()

    def _go_today(self):
        self._view_year = self._today.year
        self._view_month = self._today.month
        self._select_date(self._today)

    def _select_date(self, d: date):
        self._selected_date = d
        if d.year != self._view_year or d.month != self._view_month:
            self._view_year = d.year
            self._view_month = d.month
        self._refresh_month_grid()
        self._refresh_events()

    def _refresh_month_grid(self):
        for widget in self._grid_frame.winfo_children():
            widget.destroy()

        self._month_label.configure(
            text=f"{MONTH_NAMES[self._view_month - 1]} {self._view_year}"
        )

        cal = calendar.Calendar(firstweekday=0)  # Monday first
        month_dates = list(cal.itermonthdates(self._view_year, self._view_month))

        for i in range(7):
            self._grid_frame.grid_columnconfigure(i, weight=1, uniform="cal")

        row = 0
        col = 0
        for day_date in month_dates:
            is_current_month = day_date.month == self._view_month
            is_today = day_date == self._today
            is_selected = day_date == self._selected_date
            date_key = day_date.isoformat()
            platforms = [ev.platform for ev in self._events.get(date_key, [])]

            cell = DayCell(
                self._grid_frame, day_date, is_current_month, is_today,
                is_selected, platforms, on_click=self._select_date,
            )
            cell.grid(row=row, column=col, sticky="nsew", padx=2, pady=2, ipady=2)

            col += 1
            if col > 6:
                col = 0
                row += 1

    # ─── Events section ───

    def _add_event(self):
        title = self._event_title.get().strip()
        if not title:
            return
        try:
            duration = int(self._event_duration.get())
        except ValueError:
            duration = 3
        platform = self._event_platform.get()

        d = self._selected_date
        date_key = d.isoformat()

        event = StreamEvent(title, d, platform, duration)
        if date_key not in self._events:
            self._events[date_key] = []
        self._events[date_key].append(event)
        self._refresh_month_grid()
        self._refresh_events()
        self._save_events()
        self._event_title.delete(0, "end")
        self.event_added.emit(title, d)

    def _refresh_events(self):
        for widget in self._events_frame.winfo_children():
            widget.destroy()

        date_label = self._selected_date.strftime("%A, %b %d, %Y")
        if self._selected_date == self._today:
            date_label += "  (Today)"
        self._events_title.configure(text=f"Events for {date_label}")

        date_key = self._selected_date.isoformat()
        events = self._events.get(date_key, [])
        if not events:
            ctk.CTkLabel(
                self._events_frame, text="No events scheduled for this date.",
                font=font(11), text_color=C["text_muted"],
            ).pack(anchor="w", pady=SPACING["sm"])
        else:
            for ev in events:
                card = EventCard(self._events_frame, ev, on_delete=self._delete_event)
                card.pack(fill="x", pady=SPACING["xs"])

    def _delete_event(self, event: StreamEvent):
        """Delete a single event after confirmation."""
        if not msgbox.askyesno("Confirm", f"Delete event '{event.title}'?"):
            return
        date_key = event.date.isoformat()
        if date_key in self._events:
            self._events[date_key] = [
                e for e in self._events[date_key] if e.title != event.title or e.date != event.date
            ]
            if not self._events[date_key]:
                del self._events[date_key]
            self._refresh_month_grid()
            self._refresh_events()
            self._save_events()
            self.event_deleted.emit(event.date)

    # ─── Public API (unchanged) ───

    def get_events_for_date(self, d: date) -> list[StreamEvent]:
        key = d.isoformat()
        return list(self._events.get(key, []))

    def get_all_events(self) -> list[StreamEvent]:
        all_events = []
        for events in self._events.values():
            all_events.extend(events)
        return all_events
