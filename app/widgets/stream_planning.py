"""Stream Planning Page — Modern design.
Content ideation and collaboration tracking.
"""

import os
import re
import json
import threading
from pathlib import Path
import tkinter as tk
import customtkinter as ctk
from app.widgets.signals import Signal
from app.theme import COLORS as C, SPACING, RADIUS, font, font_bold, font_subheading
from app.config_manager import ConfigManager
from app.chat_interface import ChatManager
from datetime import datetime


STREAM_CATEGORIES = [
    "Entertainment", "Gaming", "IRL", "ASMR", "RP",
    "Collab", "Event", "Just Chatting", "Music", "Creative",
]

CATEGORY_COLORS = {
    "Entertainment": "#F59E0B",
    "Gaming": "#10B981",
    "IRL": "#06B6D4",
    "ASMR": "#A855F7",
    "RP": "#EC4899",
    "Collab": "#6366F1",
    "Event": "#EF4444",
    "Just Chatting": "#8B5CF6",
    "Music": "#14B8A6",
    "Creative": "#F97316",
}


class PlanningIdea:
    def __init__(self, title: str, category: str, description: str,
                 status: str = "idea", date_planned: str = ""):
        self.title = title
        self.category = category
        self.description = description
        self.status = status
        self.date_planned = date_planned or datetime.now().isoformat()


class IdeaCard(ctk.CTkFrame):
    """A stream planning idea card."""

    def __init__(self, parent, idea: PlanningIdea, on_delete=None):
        super().__init__(
            parent, fg_color=C["bg_tertiary"], corner_radius=RADIUS["lg"],
            border_width=1, border_color=C["border"],
        )
        self._idea = idea
        self._on_delete = on_delete
        self._build_ui()

    def _build_ui(self):
        self.grid_columnconfigure(0, weight=1)

        # Header with title, category badge and delete button
        header = ctk.CTkFrame(self, fg_color="transparent")
        header.grid(row=0, column=0, sticky="ew", padx=SPACING["lg"], pady=(SPACING["md"], 0))
        header.grid_columnconfigure(0, weight=1)

        ctk.CTkLabel(
            header, text=self._idea.title,
            font=font_bold(13), text_color=C["text_primary"],
        ).grid(row=0, column=0, sticky="w")

        cat_color = CATEGORY_COLORS.get(self._idea.category, C["accent"])
        ctk.CTkLabel(
            header, text=self._idea.category,
            font=font_bold(9), text_color=cat_color,
            fg_color=C["bg_elevated"], corner_radius=4,
            height=20,
        ).grid(row=0, column=1, sticky="e", padx=(SPACING["sm"], 0))

        copy_btn = ctk.CTkButton(
            header, text="📋", font=font(11),
            fg_color="transparent", hover_color=C["bg_hover"],
            text_color=C["text_muted"], corner_radius=RADIUS["sm"],
            height=24, width=28,
            command=self._copy,
        )
        copy_btn.grid(row=0, column=2, padx=(SPACING["sm"], 0), sticky="e")

        del_btn = ctk.CTkButton(
            header, text="x", font=font(11),
            fg_color="transparent", hover_color=C["bg_hover"],
            text_color=C["text_muted"], corner_radius=RADIUS["sm"],
            height=24, width=24,
            command=self._delete,
        )
        del_btn.grid(row=0, column=3, padx=(SPACING["xs"], 0), sticky="e")

        # Description
        if self._idea.description:
            ctk.CTkLabel(
                self, text=self._idea.description,
                font=font(11), text_color=C["text_secondary"],
                wraplength=580, justify="left",
            ).grid(row=1, column=0, padx=SPACING["lg"], pady=(SPACING["xs"], 0), sticky="nw")

        # Status
        status_color = C["accent_green"] if self._idea.status == "planned" else C["text_muted"]
        ctk.CTkLabel(
            self, text=f"Status: {self._idea.status.capitalize()}",
            font=font(9), text_color=status_color,
        ).grid(row=2, column=0, padx=SPACING["lg"], pady=(SPACING["xs"], SPACING["md"]), sticky="w")

    def _copy(self):
        parts = [self._idea.title]
        if self._idea.description:
            parts.append(self._idea.description)
        text = "\n".join(parts)
        self.clipboard_clear()
        self.clipboard_append(text)

    def _delete(self):
        if self._on_delete:
            self._on_delete()


class PlanningPage(ctk.CTkScrollableFrame):
    """Stream planning page."""

    idea_created = Signal(str)
    idea_deleted = Signal(int)

    def __init__(self, parent, config: ConfigManager, chat_mgr: ChatManager):
        super().__init__(parent, fg_color=C["bg_primary"],
                         scrollbar_button_color=C["scrollbar"],
                         scrollbar_button_hover_color=C["border_hover"])
        self._config = config
        self._chat_mgr = chat_mgr
        self._ideas: list[PlanningIdea] = []
        self._generating = False
        self._data_dir = Path(__file__).parent.parent.parent / "data"
        self._ideas_path = self._data_dir / "planning_ideas.json"
        self._build_ui()
        self._load_ideas()

    def _save_ideas(self):
        """Save planning ideas list to JSON."""
        try:
            self._data_dir.mkdir(parents=True, exist_ok=True)
            data = []
            for idea in self._ideas:
                data.append({
                    "title": idea.title,
                    "category": idea.category,
                    "description": idea.description,
                    "status": idea.status,
                    "date_planned": idea.date_planned
                })
            with open(self._ideas_path, "w", encoding="utf-8") as f:
                json.dump(data, f, indent=4, ensure_ascii=False)
        except Exception as e:
            print(f"[PlanningPage] Failed to save ideas: {e}")

    def _load_ideas(self):
        """Load planning ideas list from JSON."""
        if not self._ideas_path.exists():
            return
        try:
            with open(self._ideas_path, "r", encoding="utf-8") as f:
                data = json.load(f)
            self._ideas = []
            for item in data:
                idea = PlanningIdea(
                    title=item.get("title", ""),
                    category=item.get("category", "Entertainment"),
                    description=item.get("description", ""),
                    status=item.get("status", "idea"),
                    date_planned=item.get("date_planned", "")
                )
                self._ideas.append(idea)
            self._refresh()
        except Exception as e:
            print(f"[PlanningPage] Failed to load ideas: {e}")

    def _build_ui(self):
        self.grid_columnconfigure(0, weight=1)

        # AI Generate button
        ai_frame = ctk.CTkFrame(self, fg_color="transparent")
        ai_frame.pack(fill="x", padx=SPACING["xl"], pady=(SPACING["xl"], SPACING["md"]))

        self._ai_btn = ctk.CTkButton(
            ai_frame, text="✨ Generate Ideas with AI",
            font=font_bold(11),
            fg_color=C["accent_purple"], hover_color="#9333EA",
            text_color="#FFFFFF", text_color_disabled="#FFFFFF", corner_radius=RADIUS["md"],
            height=36, width=200,
            command=self._generate_ideas,
        )
        self._ai_btn.pack(side="right")

        # Form
        form = ctk.CTkFrame(self, fg_color=C["bg_tertiary"], corner_radius=RADIUS["lg"],
                            border_width=1, border_color=C["border"])
        form.pack(fill="x", padx=SPACING["xl"], pady=(0, SPACING["lg"]))
        form.grid_columnconfigure(1, weight=1)

        ctk.CTkLabel(form, text="Title:", font=font(11), text_color=C["text_secondary"]).grid(
            row=0, column=0, padx=(SPACING["lg"], SPACING["sm"]), pady=SPACING["md"], sticky="w")
        self._idea_title = ctk.CTkEntry(
            form, font=font(11), height=34,
            fg_color=C["input_bg"], text_color=C["text_primary"],
            border_color=C["input_border"], border_width=1,
            corner_radius=RADIUS["sm"],
            placeholder_text="Stream idea title...",
        )
        self._idea_title.grid(row=0, column=1, columnspan=3, padx=(0, SPACING["lg"]), pady=SPACING["md"], sticky="ew")

        ctk.CTkLabel(form, text="Category:", font=font(11), text_color=C["text_secondary"]).grid(
            row=1, column=0, padx=(SPACING["lg"], SPACING["sm"]), pady=(0, SPACING["md"]), sticky="w")
        self._idea_category = ctk.CTkComboBox(
            form, font=font(11), height=34, width=160,
            fg_color=C["input_bg"], text_color=C["text_primary"],
            border_color=C["input_border"], border_width=1,
            button_color=C["accent"], button_hover_color=C["accent_hover"],
            corner_radius=RADIUS["sm"],
            values=STREAM_CATEGORIES,
        )
        self._idea_category.grid(row=1, column=1, padx=(0, SPACING["md"]), pady=(0, SPACING["md"]), sticky="w")
        self._idea_category.set(STREAM_CATEGORIES[0])

        ctk.CTkLabel(form, text="Description:", font=font(11), text_color=C["text_secondary"]).grid(
            row=2, column=0, padx=(SPACING["lg"], SPACING["sm"]), pady=(0, SPACING["sm"]), sticky="nw")
        self._idea_desc = ctk.CTkTextbox(
            form, font=font(11), height=70,
            fg_color=C["input_bg"], text_color=C["text_primary"],
            border_color=C["input_border"], border_width=1,
            corner_radius=RADIUS["sm"], wrap="word",
        )
        self._idea_desc.grid(row=2, column=1, columnspan=3, padx=(0, SPACING["lg"]), pady=(0, SPACING["sm"]), sticky="nsew")

        save_btn = ctk.CTkButton(
            form, text="Save Idea",
            font=font_bold(11),
            fg_color=C["accent"], hover_color=C["accent_hover"],
            text_color="#FFFFFF", corner_radius=RADIUS["sm"],
            height=34, width=110,
            command=self._save_idea,
        )
        save_btn.grid(row=3, column=3, padx=(0, SPACING["lg"]), pady=(0, SPACING["lg"]), sticky="e")

        # Ideas list
        ideas_label = ctk.CTkLabel(
            self, text="Your Ideas",
            font=font_subheading(13), text_color=C["text_primary"],
        )
        ideas_label.pack(anchor="w", padx=SPACING["xl"], pady=(0, SPACING["sm"]))

        self._ideas_frame = ctk.CTkFrame(self, fg_color="transparent")
        self._ideas_frame.pack(fill="both", expand=True, padx=SPACING["xl"], pady=(0, SPACING["xl"]))
        self._ideas_frame.grid_columnconfigure(0, weight=1)

    def _save_idea(self):
        title = self._idea_title.get().strip()
        if not title:
            return
        category = self._idea_category.get()
        desc = self._idea_desc.get("0.0", "end-1c").strip()
        idea = PlanningIdea(title, category, desc)
        self._ideas.append(idea)
        self._refresh()
        self._save_ideas()
        self._idea_title.delete(0, "end")
        self._idea_desc.delete("0.0", "end")

    def _refresh(self):
        for widget in self._ideas_frame.winfo_children():
            widget.destroy()
        for i, idea in enumerate(self._ideas):
            card = IdeaCard(
                self._ideas_frame, idea,
                on_delete=lambda idx=i: self._delete_idea(idx),
            )
            card.pack(fill="x", pady=SPACING["xs"])

    def _delete_idea(self, idx: int):
        if 0 <= idx < len(self._ideas):
            self._ideas.pop(idx)
            self.idea_deleted.emit(idx)
            self._refresh()
            self._save_ideas()

    def _generate_ideas(self):
        if self._generating:
            return

        models_dir = self._config.get("paths.models_dir", "./models")
        model_path = self._config.get("paths.models_dir", "./models")

        # Resolve model path from config
        selected_model_path = self._config.get("llama.selected_model_path", "")
        if selected_model_path and os.path.exists(selected_model_path):
            model_path = selected_model_path
        elif os.path.isabs(models_dir):
            model_path = models_dir
        else:
            project_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
            model_path = os.path.join(project_dir, models_dir)

        if not model_path or not os.path.exists(model_path):
            self._ideas.append(PlanningIdea(
                title="⚠ AI Unavailable",
                category="Entertainment",
                description="No model found. Please go to the Models page and download a model first.",
                status="idea",
            ))
            self._refresh()
            return

        self._generating = True
        self._ai_btn.configure(state="disabled", text="Generating...")

        prompt = (
            "As the VTuber manager, generate exactly ONE creative stream idea for your talent.\n\n"
            "Respond naturally as the manager, with a brief intro (1-2 sentences), then present the idea "
            "using these three labeled lines:\n"
            "- Stream Title: <a catchy, short title>\n"
            "- Concept: <2-3 sentences describing the idea>\n"
            "- Interaction: <1-2 sentences on how viewers participate>\n\n"
            "Do NOT use any markdown formatting, headers, or bold. Use plain text only. Be specific and creative."
        )

        def inference_thread():
            try:
                response = self._chat_mgr.generate(prompt, model_path)
                self.after(0, lambda: self._on_ideas_generated(response or ""))
            except Exception as e:
                self.after(0, lambda: self._on_ideas_generated(""))

        threading.Thread(target=inference_thread, daemon=True).start()

    def _on_ideas_generated(self, response: str):
        self._generating = False
        try:
            self._ai_btn.configure(state="normal", text="✨ Generate Ideas with AI")
        except Exception:
            pass

        if not response or not response.strip():
            self._ideas.append(PlanningIdea(
                title="⚠ AI Error",
                category="Entertainment",
                description="No response received from the model. Please try again.",
                status="idea",
            ))
            self._refresh()
            self._save_ideas()
            return

        ideas = self._parse_ai_response(response)
        if not ideas:
            self._ideas.append(PlanningIdea(
                title="AI Suggestions",
                category="Entertainment",
                description=response[:500],
                status="suggestion",
            ))
        else:
            self._ideas.extend(ideas)

        self._refresh()
        self._save_ideas()

    @staticmethod
    def _parse_ai_response(response: str) -> list[PlanningIdea]:
        """Parse AI response into individual PlanningIdea objects.

        Expected format (natural, like a manager's email):
          <optional intro paragraph>

          1. VTuber Game Show Extravaganza
          Stream Title: VTuber Games: Battle Royale Edition
          Concept: Host a game show-style event...
          Interaction: Allow viewers to vote...

          2. ...
        """
        # Split into idea blocks at numbered list markers (e.g. "1.", "2.")
        blocks = re.split(r"\n\s*\n(?=\d+[\.\)])", response.strip())
        ideas: list[PlanningIdea] = []

        for block in blocks:
            block = block.strip()
            if not block:
                continue

            # Skip the intro paragraph (any block that doesn't start with a number)
            if not re.match(r"\d+[\.\)]", block):
                continue

            title = ""
            concept = ""
            interaction = ""

            for line in block.splitlines():
                stripped = line.strip()
                if not stripped:
                    continue

                title_match = re.match(
                    r"(?:Stream\s+)?Title\s*:\s*(.+)", stripped, re.IGNORECASE
                )
                concept_match = re.match(
                    r"Concept\s*:\s*(.+)", stripped, re.IGNORECASE
                )
                interaction_match = re.match(
                    r"Interaction\s*:\s*(.+)", stripped, re.IGNORECASE
                )

                if title_match:
                    title = title_match.group(1).strip()
                elif concept_match:
                    concept = concept_match.group(1).strip()
                elif interaction_match:
                    interaction = interaction_match.group(1).strip()

            # Fallback: use the numbered line heading if no "Stream Title:" found
            if not title:
                heading = re.match(r"\d+[\.\)]\s*(.+)", block, re.MULTILINE)
                if heading:
                    title = heading.group(1).strip()

            if title:
                desc_parts = []
                if concept:
                    desc_parts.append(f"Concept: {concept}")
                if interaction:
                    desc_parts.append(f"Interaction: {interaction}")
                description = "\n".join(desc_parts) if desc_parts else ""

                ideas.append(PlanningIdea(
                    title=title[:80],
                    category="Entertainment",
                    description=description,
                    status="suggestion",
                ))

        return ideas
