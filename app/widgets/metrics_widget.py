"""Metrics Page — Modern design.
Stream analytics with stats display and data table.
"""

import customtkinter as ctk
from app.widgets.signals import Signal
from app.theme import COLORS as C, SPACING, RADIUS, font, font_bold, font_subheading
from datetime import date, datetime


class StreamMetrics:
    def __init__(self, date_obj: date, platform: str, viewers_avg: int,
                 viewers_peak: int, followers_gained: int, subs: int,
                 donations: float, duration_minutes: int):
        self.date = date_obj
        self.platform = platform
        self.viewers_avg = viewers_avg
        self.viewers_peak = viewers_peak
        self.followers_gained = followers_gained
        self.subs = subs
        self.donations = donations
        self.duration_minutes = duration_minutes


class StatCard(ctk.CTkFrame):
    """A KPI stat card."""

    def __init__(self, parent, label: str, value: str, color: str = C["accent"]):
        super().__init__(
            parent, fg_color=C["bg_tertiary"], corner_radius=RADIUS["lg"],
            border_width=1, border_color=C["border"],
        )
        self._color = color
        self.grid_columnconfigure(0, weight=1)

        self._lbl = ctk.CTkLabel(
            self, text=label, font=font(10),
            text_color=C["text_muted"],
        )
        self._lbl.grid(row=0, column=0, padx=SPACING["lg"], pady=(SPACING["md"], 0), sticky="w")

        self._val = ctk.CTkLabel(
            self, text=value, font=font_bold(22),
            text_color=color,
        )
        self._val.grid(row=1, column=0, padx=SPACING["lg"], pady=(SPACING["xs"], SPACING["md"]), sticky="w")

    def set_value(self, value: str):
        self._val.configure(text=value)


class MetricsPage(ctk.CTkScrollableFrame):
    """Metrics analysis page."""

    metrics_added = Signal()

    def __init__(self, parent):
        super().__init__(parent, fg_color=C["bg_primary"],
                         scrollbar_button_color=C["scrollbar"],
                         scrollbar_button_hover_color=C["border_hover"])
        self._metrics: list[StreamMetrics] = []
        self._build_ui()

    def _build_ui(self):
        self.grid_columnconfigure(0, weight=1)

        # KPI Cards row
        stats_frame = ctk.CTkFrame(self, fg_color="transparent")
        stats_frame.pack(fill="x", padx=SPACING["xl"], pady=(SPACING["xl"], SPACING["lg"]))
        stats_frame.grid_columnconfigure((0, 1, 2, 3), weight=1)

        self._stat_avg = StatCard(stats_frame, "Avg Viewers", "0", C["accent"])
        self._stat_avg.grid(row=0, column=0, padx=(0, SPACING["sm"]), sticky="ew")

        self._stat_peak = StatCard(stats_frame, "Peak Viewers", "0", C["accent_green"])
        self._stat_peak.grid(row=0, column=1, padx=(0, SPACING["sm"]), sticky="ew")

        self._stat_total = StatCard(stats_frame, "Total Streams", "0", C["accent_amber"])
        self._stat_total.grid(row=0, column=2, padx=(0, SPACING["sm"]), sticky="ew")

        self._stat_revenue = StatCard(stats_frame, "Revenue", "$0", C["accent_purple"])
        self._stat_revenue.grid(row=0, column=3, sticky="ew")

        # ─── Live Stream Monitoring Card ───
        live_label = ctk.CTkLabel(
            self, text="Live Stream Monitoring (OBS, Twitch & Kick)",
            font=font_subheading(13), text_color=C["text_primary"],
        )
        live_label.pack(anchor="w", padx=SPACING["xl"], pady=(SPACING["md"], SPACING["sm"]))

        self._live_card = ctk.CTkFrame(self, fg_color=C["bg_tertiary"], corner_radius=RADIUS["lg"],
                                       border_width=1, border_color=C["border"])
        self._live_card.pack(fill="x", padx=SPACING["xl"], pady=(0, SPACING["lg"]))
        self._live_card.grid_columnconfigure((1, 2), weight=2)
        self._live_card.grid_columnconfigure((0, 3, 4), weight=1)

        # Column 0: Live Indicator + Status
        status_frame = ctk.CTkFrame(self._live_card, fg_color="transparent")
        status_frame.grid(row=0, column=0, padx=SPACING["md"], pady=SPACING["sm"])
        
        self._live_dot = ctk.CTkLabel(status_frame, text="●", font=font_bold(18), text_color=C["offline"])
        self._live_dot.pack(side="left", padx=(0, SPACING["xs"]))
        
        self._live_status_lbl = ctk.CTkLabel(status_frame, text="OFFLINE", font=font_bold(11), text_color=C["text_secondary"])
        self._live_status_lbl.pack(side="left")

        # Column 1: Live Viewers Stat
        self._live_viewers_lbl = StatCard(self._live_card, "Live Viewers (Twitch+Kick)", "0", C["accent"])
        self._live_viewers_lbl.grid(row=0, column=1, padx=(0, SPACING["sm"]), pady=SPACING["sm"], sticky="ew")

        # Column 2: Chat Rate Stat
        self._live_chat_rate_lbl = StatCard(self._live_card, "Chat Speed (msg/min)", "0", C["accent_purple"])
        self._live_chat_rate_lbl.grid(row=0, column=2, padx=(0, SPACING["sm"]), pady=SPACING["sm"], sticky="ew")

        # Column 3: OBS Scene Control
        obs_frame = ctk.CTkFrame(self._live_card, fg_color="transparent")
        obs_frame.grid(row=0, column=3, padx=SPACING["sm"], pady=SPACING["sm"], sticky="nsew")
        
        ctk.CTkLabel(obs_frame, text="Active OBS Scene", font=font(9), text_color=C["text_muted"]).pack(anchor="w")
        
        self._obs_scene_combo = ctk.CTkComboBox(
            obs_frame, font=font(10), height=28,
            fg_color=C["input_bg"], dropdown_fg_color=C["bg_tertiary"],
            text_color=C["text_primary"], button_color=C["accent"],
            button_hover_color=C["accent_hover"], border_color=C["input_border"],
            command=self._on_obs_scene_change
        )
        self._obs_scene_combo.pack(fill="x", pady=(SPACING["xs"], 0))
        self._obs_scene_combo.set("Disconnected")

        # Column 4: AI Advice Button
        advice_frame = ctk.CTkFrame(self._live_card, fg_color="transparent")
        advice_frame.grid(row=0, column=4, padx=SPACING["md"], pady=SPACING["sm"])
        
        self._live_advice_btn = ctk.CTkButton(
            advice_frame, text="✨ Ask Astra", font=font_bold(10),
            fg_color=C["accent_purple"], hover_color="#9333EA",
            text_color="#FFFFFF", corner_radius=RADIUS["sm"],
            height=32, width=80, command=self._ask_astra_live_advice
        )
        self._live_advice_btn.pack()

        # Start periodic update
        self.after(2000, self._update_live_metrics)

        # Add metrics form
        form_label = ctk.CTkLabel(
            self, text="Log Stream Metrics",
            font=font_subheading(13), text_color=C["text_primary"],
        )
        form_label.pack(anchor="w", padx=SPACING["xl"], pady=(0, SPACING["sm"]))

        form = ctk.CTkFrame(self, fg_color=C["bg_tertiary"], corner_radius=RADIUS["lg"],
                            border_width=1, border_color=C["border"])
        form.pack(fill="x", padx=SPACING["xl"], pady=(0, SPACING["lg"]))
        form.grid_columnconfigure((1, 3, 5), weight=1)

        # Row 1
        ctk.CTkLabel(form, text="Date:", font=font(10), text_color=C["text_secondary"]).grid(
            row=0, column=0, padx=(SPACING["lg"], SPACING["xs"]), pady=SPACING["md"], sticky="w")
        self._metric_date = ctk.CTkEntry(
            form, font=font(10), height=32, width=120,
            fg_color=C["input_bg"], text_color=C["text_primary"],
            border_color=C["input_border"], border_width=1,
            corner_radius=RADIUS["sm"],
        )
        self._metric_date.grid(row=0, column=1, padx=(0, SPACING["md"]), pady=SPACING["md"], sticky="w")
        self._metric_date.insert(0, date.today().isoformat())

        ctk.CTkLabel(form, text="Platform:", font=font(10), text_color=C["text_secondary"]).grid(
            row=0, column=2, padx=(0, SPACING["xs"]), pady=SPACING["md"], sticky="w")
        self._metric_platform = ctk.CTkComboBox(
            form, font=font(10), height=32, width=110,
            fg_color=C["input_bg"], text_color=C["text_primary"],
            border_color=C["input_border"], border_width=1,
            button_color=C["accent"], button_hover_color=C["accent_hover"],
            corner_radius=RADIUS["sm"],
            values=["twitch", "youtube", "kick", "tiktok"],
        )
        self._metric_platform.grid(row=0, column=3, padx=(0, SPACING["md"]), pady=SPACING["md"], sticky="w")
        self._metric_platform.set("twitch")

        ctk.CTkLabel(form, text="Duration (min):", font=font(10), text_color=C["text_secondary"]).grid(
            row=0, column=4, padx=(0, SPACING["xs"]), pady=SPACING["md"], sticky="w")
        self._metric_duration = ctk.CTkEntry(
            form, font=font(10), height=32, width=70,
            fg_color=C["input_bg"], text_color=C["text_primary"],
            border_color=C["input_border"], border_width=1,
            corner_radius=RADIUS["sm"],
        )
        self._metric_duration.grid(row=0, column=5, padx=(0, SPACING["lg"]), pady=SPACING["md"], sticky="w")
        self._metric_duration.insert(0, "180")

        # Row 2
        ctk.CTkLabel(form, text="Avg:", font=font(10), text_color=C["text_secondary"]).grid(
            row=1, column=0, padx=(SPACING["lg"], SPACING["xs"]), pady=(0, SPACING["md"]), sticky="w")
        self._metric_avg = ctk.CTkEntry(
            form, font=font(10), height=32, width=70,
            fg_color=C["input_bg"], text_color=C["text_primary"],
            border_color=C["input_border"], border_width=1,
            corner_radius=RADIUS["sm"],
        )
        self._metric_avg.grid(row=1, column=1, padx=(0, SPACING["md"]), pady=(0, SPACING["md"]), sticky="w")
        self._metric_avg.insert(0, "0")

        ctk.CTkLabel(form, text="Peak:", font=font(10), text_color=C["text_secondary"]).grid(
            row=1, column=2, padx=(0, SPACING["xs"]), pady=(0, SPACING["md"]), sticky="w")
        self._metric_peak = ctk.CTkEntry(
            form, font=font(10), height=32, width=70,
            fg_color=C["input_bg"], text_color=C["text_primary"],
            border_color=C["input_border"], border_width=1,
            corner_radius=RADIUS["sm"],
        )
        self._metric_peak.grid(row=1, column=3, padx=(0, SPACING["md"]), pady=(0, SPACING["md"]), sticky="w")
        self._metric_peak.insert(0, "0")

        ctk.CTkLabel(form, text="Followers:", font=font(10), text_color=C["text_secondary"]).grid(
            row=1, column=4, padx=(0, SPACING["xs"]), pady=(0, SPACING["md"]), sticky="w")
        self._metric_followers = ctk.CTkEntry(
            form, font=font(10), height=32, width=70,
            fg_color=C["input_bg"], text_color=C["text_primary"],
            border_color=C["input_border"], border_width=1,
            corner_radius=RADIUS["sm"],
        )
        self._metric_followers.grid(row=1, column=5, padx=(0, SPACING["lg"]), pady=(0, SPACING["md"]), sticky="w")
        self._metric_followers.insert(0, "0")

        # Row 3
        ctk.CTkLabel(form, text="Subs:", font=font(10), text_color=C["text_secondary"]).grid(
            row=2, column=0, padx=(SPACING["lg"], SPACING["xs"]), pady=(0, SPACING["md"]), sticky="w")
        self._metric_subs = ctk.CTkEntry(
            form, font=font(10), height=32, width=70,
            fg_color=C["input_bg"], text_color=C["text_primary"],
            border_color=C["input_border"], border_width=1,
            corner_radius=RADIUS["sm"],
        )
        self._metric_subs.grid(row=2, column=1, padx=(0, SPACING["md"]), pady=(0, SPACING["md"]), sticky="w")
        self._metric_subs.insert(0, "0")

        ctk.CTkLabel(form, text="Donations ($):", font=font(10), text_color=C["text_secondary"]).grid(
            row=2, column=2, padx=(0, SPACING["xs"]), pady=(0, SPACING["md"]), sticky="w")
        self._metric_donations = ctk.CTkEntry(
            form, font=font(10), height=32, width=80,
            fg_color=C["input_bg"], text_color=C["text_primary"],
            border_color=C["input_border"], border_width=1,
            corner_radius=RADIUS["sm"],
        )
        self._metric_donations.grid(row=2, column=3, padx=(0, SPACING["md"]), pady=(0, SPACING["md"]), sticky="w")
        self._metric_donations.insert(0, "0.00")

        add_btn = ctk.CTkButton(
            form, text="Log Metrics",
            font=font_bold(11),
            fg_color=C["accent"], hover_color=C["accent_hover"],
            text_color="#FFFFFF", corner_radius=RADIUS["sm"],
            height=32, width=110,
            command=self._add_metrics,
        )
        add_btn.grid(row=2, column=5, padx=(0, SPACING["lg"]), pady=(0, SPACING["md"]), sticky="e")

        # Data table
        table_label = ctk.CTkLabel(
            self, text="Stream History",
            font=font_subheading(13), text_color=C["text_primary"],
        )
        table_label.pack(anchor="w", padx=SPACING["xl"], pady=(0, SPACING["sm"]))

        self._table_container = ctk.CTkFrame(
            self, fg_color=C["bg_tertiary"], corner_radius=RADIUS["lg"],
            border_width=1, border_color=C["border"],
        )
        self._table_container.pack(fill="both", expand=True, padx=SPACING["xl"], pady=(0, SPACING["lg"]))
        self._table_container.grid_columnconfigure(0, weight=1)

        # Table header
        header_frame = ctk.CTkFrame(self._table_container, fg_color=C["bg_elevated"],
                                     corner_radius=0, height=32)
        header_frame.pack(fill="x", padx=2, pady=(2, 0))
        header_frame.grid_columnconfigure((0, 1, 2, 3, 4, 5, 6, 7), weight=1)

        headers = ["Date", "Platform", "Avg", "Peak", "Followers", "Subs", "Revenue", "Duration"]
        for i, h in enumerate(headers):
            ctk.CTkLabel(
                header_frame, text=h, font=font_bold(9),
                text_color=C["text_accent"], height=32,
            ).grid(row=0, column=i, padx=SPACING["xs"], sticky="ew")

        self._data_area = ctk.CTkFrame(self._table_container, fg_color="transparent")
        self._data_area.pack(fill="both", expand=True, padx=2, pady=2)

        # AI Analysis button
        ai_btn = ctk.CTkButton(
            self, text="AI Analysis",
            font=font_bold(11),
            fg_color=C["accent_purple"], hover_color="#9333EA",
            text_color="#FFFFFF", corner_radius=RADIUS["md"],
            height=36, width=140,
            command=self._analyze_metrics,
        )
        ai_btn.pack(anchor="e", padx=SPACING["xl"], pady=(0, SPACING["xl"]))

    def _add_metrics(self):
        try:
            d = date.fromisoformat(self._metric_date.get())
            platform = self._metric_platform.get()
            avg = int(self._metric_avg.get() or 0)
            peak = int(self._metric_peak.get() or 0)
            followers = int(self._metric_followers.get() or 0)
            subs = int(self._metric_subs.get() or 0)
            donations = float(self._metric_donations.get() or 0)
            duration = int(self._metric_duration.get() or 0)

            metrics = StreamMetrics(
                date_obj=d, platform=platform, viewers_avg=avg,
                viewers_peak=peak, followers_gained=followers,
                subs=subs, donations=donations, duration_minutes=duration,
            )
            self._metrics.append(metrics)
            self._refresh_table()
            self._update_stats()
        except (ValueError, TypeError):
            pass

    def _refresh_table(self):
        for widget in self._data_area.winfo_children():
            widget.destroy()

        for m in self._metrics:
            row_frame = ctk.CTkFrame(self._data_area, fg_color="transparent", height=28)
            row_frame.pack(fill="x", pady=1)
            row_frame.grid_columnconfigure((0, 1, 2, 3, 4, 5, 6, 7), weight=1)

            cells = [
                m.date.isoformat(), m.platform.upper(), str(m.viewers_avg),
                str(m.viewers_peak), str(m.followers_gained), str(m.subs),
                f"${m.donations:.2f}", f"{m.duration_minutes}m",
            ]
            for i, val in enumerate(cells):
                ctk.CTkLabel(
                    row_frame, text=val, font=font(10),
                    text_color=C["text_secondary"], height=28,
                ).grid(row=0, column=i, padx=SPACING["xs"], sticky="ew")

    def _update_stats(self):
        if not self._metrics:
            self._stat_avg.set_value("0")
            self._stat_peak.set_value("0")
            self._stat_total.set_value("0")
            self._stat_revenue.set_value("$0")
            return

        avg = sum(m.viewers_avg for m in self._metrics) / len(self._metrics)
        peak = max(m.viewers_peak for m in self._metrics)
        revenue = sum(m.donations for m in self._metrics)
        self._stat_avg.set_value(f"{avg:.0f}")
        self._stat_peak.set_value(str(peak))
        self._stat_total.set_value(str(len(self._metrics)))
        self._stat_revenue.set_value(f"${revenue:.2f}")

    def _analyze_metrics(self):
        """Usa el LLM local para analizar el historial de métricas cargado."""
        if not self._metrics:
            return
        
        # Generar un resumen de texto del historial
        history_summary = []
        for m in self._metrics:
            history_summary.append(
                f"Fecha: {m.date.isoformat()}, Plataforma: {m.platform}, Promedio: {m.viewers_avg}, Pico: {m.viewers_peak}, Followers: {m.followers_gained}, Subs: {m.subs}, Revenue: ${m.donations:.2f}, Duración: {m.duration_minutes}m"
            )
        
        prompt = (
            "Hola Astra, por favor analiza mi historial de transmisiones recientes y dame tus comentarios de VTuber manager "
            "sobre mis puntos fuertes, áreas de oportunidad y qué estrategias me recomiendas para crecer:\n\n"
            + "\n".join(history_summary)
        )

        # Enviar al chat manager
        try:
            main_win = self.master
            while main_win and not hasattr(main_win, "_select_page"):
                main_win = main_win.master
            if main_win:
                main_win._select_page("chat")
                chat_page = main_win._pages.get("chat")
                if chat_page:
                    chat_page._input.delete("0.0", "end")
                    chat_page._input.insert("0.0", prompt)
                    chat_page._send_message()
        except Exception as e:
            print(f"Error sending metrics analysis to chat: {e}")

    @property
    def stream_api(self):
        """Busca el administrador de la API de streaming en la ventana principal."""
        current = self.master
        while current:
            if hasattr(current, "_stream_api"):
                return current._stream_api
            current = current.master
        return None

    def _update_live_metrics(self):
        """Actualiza periódicamente el panel de métricas en directo."""
        import threading
        api = self.stream_api
        if not api:
            # Reintentar en 5 segundos
            self.after(5000, self._update_live_metrics)
            return

        try:
            metrics = api.get_live_metrics()
            
            # Actualizar estado de directo
            if metrics["is_live"]:
                self._live_dot.configure(text_color=C["accent_green"])
                self._live_status_lbl.configure(text="LIVE", text_color=C["accent_green"])
            else:
                self._live_dot.configure(text_color=C["offline"])
                self._live_status_lbl.configure(text="OFFLINE", text_color=C["text_secondary"])

            # Actualizar espectadores y chat rate
            self._live_viewers_lbl.set_value(str(metrics["total_viewers"]))
            self._live_chat_rate_lbl.set_value(str(metrics["chat_rate"]))

            # Actualizar escena de OBS
            if metrics["obs_connected"]:
                scenes = api.get_obs_scenes()
                # Actualizar valores del combo si cambiaron
                current_val = metrics["obs_scene"]
                if scenes:
                    self._obs_scene_combo.configure(values=scenes)
                    self._obs_scene_combo.set(current_val)
            else:
                self._obs_scene_combo.configure(values=["Disconnected"])
                self._obs_scene_combo.set("Disconnected")

        except Exception as e:
            print(f"[MetricsPage] Error updating live metrics: {e}")

        # Programar siguiente actualización en 5 segundos
        self.after(5000, self._update_live_metrics)

    def _on_obs_scene_change(self, value: str):
        """Manejador para cambiar la escena en OBS Studio."""
        import threading
        if value in ["Disconnected", "Unknown"]:
            return
        api = self.stream_api
        if api:
            threading.Thread(target=api.change_obs_scene, args=(value,), daemon=True).start()

    def _ask_astra_live_advice(self):
        """Envía el contexto de directo actual a Astra en el chat para obtener consejo."""
        api = self.stream_api
        if not api:
            return
        metrics = api.get_live_metrics()
        
        prompt = (
            f"Astra, estoy en directo ahora y necesito tu consejo rápido como mi manager. "
            f"Estas son las métricas reales actuales de mi transmisión:\n"
            f"- Espectadores totales: {metrics['total_viewers']} (Twitch: {metrics['twitch_viewers']}, Kick: {metrics['kick_viewers']})\n"
            f"- Velocidad del chat: {metrics['chat_rate']} mensajes por minuto\n"
            f"- Escena de OBS activa: '{metrics['obs_scene']}'\n"
            f"- Estado de transmisión: {'Transmitiendo' if metrics['obs_streaming'] else 'Offline/Preparándose'}\n\n"
            f"Dame un consejo rápido, directo y con tu personalidad de manager sobre qué debería hacer ahora para animar el directo."
        )
        
        try:
            main_win = self.master
            while main_win and not hasattr(main_win, "_select_page"):
                main_win = main_win.master
            if main_win:
                main_win._select_page("chat")
                chat_page = main_win._pages.get("chat")
                if chat_page:
                    chat_page._input.delete("0.0", "end")
                    chat_page._input.insert("0.0", prompt)
                    chat_page._send_message()
        except Exception as e:
            print(f"Error sending live advice prompt to chat: {e}")
