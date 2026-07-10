"""Chat Page — Modern design.
Clean chat interface inspired by ChatGPT/Claude with refined aesthetics.
"""
import os
import threading
import customtkinter as ctk
from tkinter import messagebox as msgbox
from app.widgets.signals import Signal
from app.theme import COLORS as C, SPACING, RADIUS, font, font_bold, font_mono
from app.config_manager import ConfigManager
from app.chat_interface import ChatManager


class MessageBubble(ctk.CTkFrame):
    """A single chat message with modern styling."""
    def __init__(self, parent, role: str, content: str):
        is_user = role == "user"
        
        bg_color = C["msg_user"] if is_user else C["msg_ai"]
        border_color = C["msg_user_border"] if is_user else C["msg_ai_border"]

        super().__init__(
            parent,
            fg_color=bg_color,
            corner_radius=RADIUS["lg"],
            border_width=1,
            border_color=border_color,
        )
        self.grid_columnconfigure(0, weight=1)

        # Role indicator
        role_text = "Tú" if is_user else "Asistente"
        role_color = C["accent"] if is_user else C["accent_purple"]

        self.role_label = ctk.CTkLabel(
            self,
            text=role_text,
            font=font_bold(11),
            text_color=role_color,
        )
        self.role_label.grid(row=0, column=0, padx=SPACING["lg"], pady=(SPACING["md"], 0), sticky="w")

        # Message content
        self.content_box = ctk.CTkTextbox(
            self,
            font=font(13),                    # Texto más visible
            text_color=C["text_primary"],
            fg_color="transparent",
            wrap="word",
            state="normal",                   # Temporal para insertar
            border_width=0,
        )
        
        self._insert_markdown(content)
        self.content_box.configure(state="disabled")

        self.content_box.grid(
            row=1, column=0,
            padx=SPACING["lg"],
            pady=(SPACING["xs"], SPACING["md"]),
            sticky="ew"
        )

        # Ajuste de altura dinámico por Configure y visibilidad inicial
        self.last_width = 0
        self._last_height_update = 0
        self.content_box.bind("<Configure>", self._on_configure)
        self.after(40, self._force_update)

    def _on_configure(self, event):
        if event.width != self.last_width:
            self.last_width = event.width
            self._force_update()

    def _force_update(self):
        """Fuerza la actualización visual y altura del mensaje"""
        try:
            self.content_box.update_idletasks()
            # Buscar el widget de texto subyacente de CustomTkinter
            text_widget = None
            if hasattr(self.content_box, "_textbox"):
                text_widget = self.content_box._textbox
            elif hasattr(self.content_box, "_text"):
                text_widget = self.content_box._text

            if text_widget is not None:
                display_info = text_widget.count("1.0", "end-1c", "displaylines")
                if isinstance(display_info, tuple):
                    num_lines = display_info[0] if display_info else 1
                elif isinstance(display_info, int):
                    num_lines = display_info
                else:
                    num_lines = 1
                num_lines = max(1, num_lines + 1)
                # 23 px por línea + 28 px de padding vertical
                height = max(70, min(1200, num_lines * 23 + 28))
            else:
                raise AttributeError("No text widget found")

            self.content_box.configure(height=height)
        except:
            # Fallback en caso de fallo inesperado
            try:
                text = self.content_box.get("0.0", "end-1c")
                char_count = len(text)
                estimated_lines = max(len(text.splitlines()), char_count // 75 + 1)
                height = max(70, min(1200, estimated_lines * 23 + 28))
                self.content_box.configure(height=height)
            except:
                pass

    def _configure_markdown_tags(self, text_widget):
        """Configura los tags de estilo de Tkinter para Markdown en el widget nativo."""
        text_widget.tag_configure("h1", font=font_bold(16), foreground=C["accent"], spacing1=8, spacing3=4)
        text_widget.tag_configure("h2", font=font_bold(14), foreground=C["accent_purple"], spacing1=6, spacing3=3)
        text_widget.tag_configure("h3", font=font_bold(13), foreground=C["accent_cyan"], spacing1=4, spacing3=2)
        text_widget.tag_configure("bold", font=font_bold(13))
        text_widget.tag_configure("inline_code", font=font_mono(11), foreground=C["accent_amber"], background=C["bg_tertiary"])
        text_widget.tag_configure("code_block", font=font_mono(11), foreground=C["text_primary"], background=C["bg_elevated"])
        text_widget.tag_configure("code_header", font=font_bold(10), foreground=C["text_secondary"], background=C["bg_tertiary"], spacing1=4)
        text_widget.tag_configure("list_bullet", font=font_bold(13), foreground=C["accent"])
        text_widget.tag_configure("link", font=font(13), foreground=C["accent"], underline=True)
        
        # Enlaces interactivos
        text_widget.tag_bind("link", "<Button-1>", self._on_link_click)
        text_widget.tag_bind("link", "<Enter>", lambda e: text_widget.config(cursor="hand2"))
        text_widget.tag_bind("link", "<Leave>", lambda e: text_widget.config(cursor="xterm"))

    def _on_link_click(self, event):
        """Abre el enlace en el navegador web al hacer clic."""
        import webbrowser
        try:
            text_widget = event.widget
            index = text_widget.index(f"@{event.x},{event.y}")
            ranges = text_widget.tag_ranges("link")
            for i in range(0, len(ranges), 2):
                start = ranges[i]
                end = ranges[i+1]
                if text_widget.compare(start, "<=", index) and text_widget.compare(index, "<=", end):
                    url = text_widget.get(start, end)
                    webbrowser.open(url)
                    break
        except:
            pass

    def _parse_inline(self, text: str):
        """Parsea recursivamente negritas, código inline y URLs."""
        import re
        parts = re.split(r'(\*\*.*?\*\*|`[^`\r\n]+`|https?://[^\s]+)', text)
        for part in parts:
            if not part:
                continue
            if part.startswith("**") and part.endswith("**"):
                yield part[2:-2], "bold"
            elif part.startswith("`") and part.endswith("`"):
                yield part[1:-1], "inline_code"
            elif part.startswith("http://") or part.startswith("https://"):
                url = part
                trail = ""
                while url and url[-1] in ".,;:!?()":
                    trail = url[-1] + trail
                    url = url[:-1]
                yield url, "link"
                if trail:
                    yield trail, None
            else:
                yield part, None

    def _insert_line_with_inline_tags(self, text_widget, text: str, base_tags: tuple):
        """Inserta texto parseando estilos inline e integrándolos con tags base."""
        for chunk, tag in self._parse_inline(text):
            tags = list(base_tags)
            if tag:
                tags.append(tag)
            text_widget.insert("end", chunk, tuple(tags))

    def _insert_markdown(self, content: str):
        """Analiza la estructura de Markdown e inserta el texto formateado línea a línea."""
        import re
        text_widget = None
        if hasattr(self.content_box, "_textbox"):
            text_widget = self.content_box._textbox
        elif hasattr(self.content_box, "_text"):
            text_widget = self.content_box._text

        if text_widget is None:
            self.content_box.insert("0.0", content)
            return

        self._configure_markdown_tags(text_widget)
        text_widget.delete("1.0", "end")

        lines = content.split("\n")
        in_code_block = False
        code_block_lines = []
        code_block_lang = ""

        for i, line in enumerate(lines):
            # Detección de bloques de código
            if line.strip().startswith("```"):
                if in_code_block:
                    if code_block_lang:
                        text_widget.insert("end", f" 💻 {code_block_lang.upper()} \n", "code_header")
                    
                    indented_code = ""
                    for cl in code_block_lines:
                        indented_code += f"  {cl}\n"
                    
                    if i == len(lines) - 1 and indented_code.endswith("\n"):
                        indented_code = indented_code[:-1]
                    
                    text_widget.insert("end", indented_code, "code_block")
                    in_code_block = False
                    code_block_lines = []
                else:
                    in_code_block = True
                    code_block_lang = line.strip()[3:].strip()
                continue

            if in_code_block:
                code_block_lines.append(line)
                continue

            # Cabeceras
            if line.startswith("# "):
                self._insert_line_with_inline_tags(text_widget, line[2:], ("h1",))
                if i < len(lines) - 1:
                    text_widget.insert("end", "\n")
            elif line.startswith("## "):
                self._insert_line_with_inline_tags(text_widget, line[3:], ("h2",))
                if i < len(lines) - 1:
                    text_widget.insert("end", "\n")
            elif line.startswith("### "):
                self._insert_line_with_inline_tags(text_widget, line[4:], ("h3",))
                if i < len(lines) - 1:
                    text_widget.insert("end", "\n")
            # Listas desordenadas
            elif line.strip().startswith("- ") or line.strip().startswith("* ") or line.strip().startswith("+ "):
                indent = len(line) - len(line.lstrip())
                prefix = " " * indent
                text_widget.insert("end", f"{prefix}• ", "list_bullet")
                content_part = line.lstrip()[2:]
                self._insert_line_with_inline_tags(text_widget, content_part, ())
                if i < len(lines) - 1:
                    text_widget.insert("end", "\n")
            # Listas ordenadas
            elif re.match(r'^\s*\d+\.\s', line):
                m = re.match(r'^(\s*)(\d+\.\s)(.*)', line)
                indent_spaces = m.group(1)
                num_prefix = m.group(2)
                content_part = m.group(3)
                text_widget.insert("end", f"{indent_spaces}{num_prefix}", "list_bullet")
                self._insert_line_with_inline_tags(text_widget, content_part, ())
                if i < len(lines) - 1:
                    text_widget.insert("end", "\n")
            else:
                # Línea común
                self._insert_line_with_inline_tags(text_widget, line, ())
                if i < len(lines) - 1:
                    text_widget.insert("end", "\n")

        if in_code_block and code_block_lines:
            code_text = "\n".join(code_block_lines)
            text_widget.insert("end", code_text, "code_block")

    def append_text(self, text: str):
        """Append raw text to the bubble during streaming."""
        self.content_box.configure(state="normal")
        text_widget = None
        if hasattr(self.content_box, "_textbox"):
            text_widget = self.content_box._textbox
        elif hasattr(self.content_box, "_text"):
            text_widget = self.content_box._text

        if text_widget is not None:
            text_widget.insert("end", text)
        else:
            self.content_box.insert("end", text)
        self.content_box.configure(state="disabled")
        
        # Throttle height recalculations to once every 250ms during streaming
        import time
        now = time.time()
        if now - self._last_height_update > 0.25:
            self._last_height_update = now
            self._force_update()

    def set_markdown_content(self, markdown_text: str):
        """Replace streaming content with formatted markdown once complete."""
        self.content_box.configure(state="normal")
        text_widget = None
        if hasattr(self.content_box, "_textbox"):
            text_widget = self.content_box._textbox
        elif hasattr(self.content_box, "_text"):
            text_widget = self.content_box._text

        if text_widget is not None:
            text_widget.delete("1.0", "end")
        else:
            self.content_box.delete("0.0", "end")
            
        self._insert_markdown(markdown_text)
        self.content_box.configure(state="disabled")
        self._force_update()

    def update_emotion(self, emotion: str):
        emojis = {
            "feliz": "😊",
            "divertida": "😜",
            "triste": "😢",
            "enojada": "😠",
            "seria": "😐",
            "sorprendida": "😮",
            "neutral": "😐"
        }
        emoji = emojis.get(emotion.lower(), "😐")
        role_text = f"Astra ({emotion.capitalize()}) {emoji}"
        self.role_label.configure(text=role_text)



class ChatPage(ctk.CTkFrame):
    """Chat page with message history and input — modern layout."""
    message_sent = Signal(str)

    def __init__(self, parent, config: ConfigManager, chat_mgr: ChatManager):
        super().__init__(parent, fg_color=C["bg_primary"])
        self._config = config
        self._chat_mgr = chat_mgr
        self._sending = False
        self._welcome = None
        self._mapped_once = False

        self.grid_columnconfigure(0, weight=1)
        self.grid_rowconfigure(1, weight=1)

        self._build_ui()
        self.bind("<Map>", self._on_map)

    def _build_ui(self):
        # ─── Top bar ───
        top_bar = ctk.CTkFrame(self, fg_color=C["bg_secondary"], corner_radius=0, height=44)
        top_bar.grid(row=0, column=0, sticky="ew")
        top_bar.grid_columnconfigure(2, weight=1)
        top_bar.grid_propagate(False)

        # Session selector
        self._session_combo = ctk.CTkComboBox(
            top_bar, font=font(11), height=30, width=180,
            fg_color=C["input_bg"], dropdown_fg_color=C["bg_tertiary"],
            text_color=C["text_primary"], button_color=C["accent"],
            button_hover_color=C["accent_hover"], border_color=C["input_border"],
            command=self._on_session_change,
        )
        self._session_combo.grid(row=0, column=0, padx=(SPACING["lg"], SPACING["sm"]), pady=SPACING["sm"])

        # Delete session button (next to "+ New")
        self._delete_btn = ctk.CTkButton(
            top_bar, text="🗑 Delete", font=font_bold(10),
            fg_color=C["accent_red"], hover_color="#D46B6B",
            text_color="#FFFFFF", corner_radius=RADIUS["sm"],
            height=28, width=90, command=self._delete_session,
        )
        self._delete_btn.grid(row=0, column=1, padx=(0, SPACING["sm"]), pady=SPACING["sm"])

        # New session button
        self._new_btn = ctk.CTkButton(
            top_bar, text="+ New", font=font_bold(10),
            fg_color=C["accent"], hover_color=C["accent_hover"],
            text_color="#FFFFFF", corner_radius=RADIUS["sm"],
            height=28, width=56, command=self._create_session,
        )
        self._new_btn.grid(row=0, column=2, padx=(0, SPACING["sm"]), pady=SPACING["sm"])

        # Model selector
        model_frame = ctk.CTkFrame(top_bar, fg_color="transparent")
        model_frame.grid(row=0, column=3, padx=(0, SPACING["lg"]), pady=SPACING["sm"], sticky="e")

        ctk.CTkLabel(model_frame, text="Model:", font=font(10), text_color=C["text_muted"]).pack(
            side="left", padx=(0, SPACING["xs"])
        )

        self._model_combo = ctk.CTkComboBox(
            model_frame, font=font(10), height=28, width=260,
            fg_color=C["input_bg"], dropdown_fg_color=C["bg_tertiary"],
            text_color=C["text_primary"], button_color=C["accent"],
            button_hover_color=C["accent_hover"], border_color=C["input_border"],
            command=self._on_model_change,
        )
        self._model_combo.pack(side="left")

        self._model_status = ctk.CTkLabel(
            model_frame, text="", font=font(9), text_color=C["accent_green"]
        )
        self._model_status.pack(side="left", padx=(SPACING["sm"], 0))

        self._refresh_models()

        # ─── Messages area ───
        self._messages_scroll = ctk.CTkScrollableFrame(
            self,
            fg_color=C["bg_primary"],
            scrollbar_button_color=C["scrollbar"],
            scrollbar_button_hover_color=C["border_hover"],
        )
        self._messages_scroll.grid(row=1, column=0, sticky="nsew", padx=0, pady=0)
        self._messages_scroll.grid_columnconfigure(0, weight=1)

        self._show_welcome_message()

        # ─── Input area ───
        input_container = ctk.CTkFrame(self, fg_color=C["bg_secondary"], height=120, corner_radius=0)
        input_container.grid(row=2, column=0, sticky="ew")
        input_container.grid_columnconfigure(0, weight=1)
        input_container.grid_propagate(False)

        input_wrapper = ctk.CTkFrame(
            input_container,
            fg_color=C["input_bg"],
            corner_radius=RADIUS["lg"],
            border_width=1,
            border_color=C["input_border"],
        )
        input_wrapper.grid(row=0, column=0, sticky="ew", padx=SPACING["xl"], pady=SPACING["md"])
        input_wrapper.grid_columnconfigure(0, weight=1)

        self._input = ctk.CTkTextbox(
            input_wrapper,
            font=font(12),
            height=60,
            fg_color="transparent",
            text_color=C["text_primary"],
            wrap="word",
        )
        self._input.grid(row=0, column=0, padx=SPACING["sm"], pady=SPACING["sm"], sticky="nsew")

        self._mic_btn = ctk.CTkButton(
            input_wrapper,
            text="🎤",
            font=font_bold(14),
            fg_color="transparent",
            hover_color=C["sidebar_hover"],
            text_color=C["accent"],
            corner_radius=RADIUS["sm"],
            height=34,
            width=34,
            border_width=1,
            border_color=C["input_border"],
            command=self._toggle_mic,
        )
        self._mic_btn.grid(row=0, column=1, padx=(0, SPACING["sm"]), pady=SPACING["sm"], sticky="se")

        self._send_btn = ctk.CTkButton(
            input_wrapper,
            text="Send",
            font=font_bold(11),
            fg_color=C["accent"],
            hover_color=C["accent_hover"],
            text_color="#FFFFFF",
            corner_radius=RADIUS["sm"],
            height=34,
            width=72,
            command=self._send_message,
        )
        self._send_btn.grid(row=0, column=2, padx=(0, SPACING["sm"]), pady=SPACING["sm"], sticky="se")

        # Hint & Hands-Free Row Frame
        bottom_row = ctk.CTkFrame(input_container, fg_color="transparent")
        bottom_row.grid(row=1, column=0, padx=0, pady=(0, SPACING["sm"]), sticky="ew")
        
        # Hint on the left
        ctk.CTkLabel(
            bottom_row,
            text="Press Enter to send • Shift+Enter for new line",
            font=font(9),
            text_color=C["text_muted"],
        ).pack(side="left", padx=SPACING["xl"])

        # Hands-Free status & toggle on the right
        hands_free_frame = ctk.CTkFrame(bottom_row, fg_color="transparent")
        hands_free_frame.pack(side="right", padx=SPACING["xl"])

        self._hands_free_status_lbl = ctk.CTkLabel(
            hands_free_frame,
            text="",
            font=font(10),
            text_color=C["text_muted"],
        )
        self._hands_free_status_lbl.pack(side="left", padx=(0, SPACING["sm"]))

        self._hands_free_var = ctk.BooleanVar(value=False)
        self._hands_free_switch = ctk.CTkSwitch(
            hands_free_frame,
            text="Modo Manos Libres 🎙️✨",
            font=font_bold(10),
            text_color=C["text_primary"],
            fg_color=C["border"],
            progress_color=C["accent"],
            variable=self._hands_free_var,
            command=self._toggle_hands_free,
        )
        self._hands_free_switch.pack(side="left")

        self._input.bind("<Return>", self._on_enter_key)
        self._refresh_sessions()

    def _show_welcome_message(self):
        if self._welcome and self._welcome.winfo_exists():
            self._welcome.destroy()

        self._welcome = ctk.CTkLabel(
            self._messages_scroll,
            text="Start a conversation with your AI assistant.\nWrite a message below to get started.",
            font=font(13),
            text_color=C["text_muted"],
            justify="center",
        )
        self._welcome.pack(expand=True, pady=SPACING["3xl"])

    def _hide_welcome_message(self):
        if self._welcome and self._welcome.winfo_exists():
            self._welcome.pack_forget()

    def _on_enter_key(self, event):
        if not event.state & 0x1:  # No Shift
            self._send_message()
            return "break"
        return None

    def _send_message(self):
        if self._sending:
            return

        text = self._input.get("0.0", "end-1c").strip()
        if not text:
            return

        self._input.delete("0.0", "end")
        self._hide_welcome_message()

        self._add_message("user", text)

        if not self._chat_mgr.current_session:
            self._chat_mgr.create_session(title="Chat 1")
            self._refresh_sessions()

        model_name = self._model_combo.get().strip()
        models_dir = self._config.get("paths.models_dir", "./models")
        model_path = os.path.join(models_dir, model_name) if model_name else ""

        if not model_path or not os.path.exists(model_path):
            self._add_message("assistant", "The selected model could not be found.\nPlease go to the Models page and download one.")
            return

        # Stop active voice playback when user starts sending new prompt
        if self.voice_mgr:
            self.voice_mgr.stop_speaking()

        self._sending = True
        self._send_btn.configure(state="disabled", text="Pensando...", text_color_disabled="#FFFFFF")

        # Create active streaming bubble
        self._active_bubble = MessageBubble(self._messages_scroll, "assistant", "")
        self._active_bubble.pack(fill="x", pady=SPACING["xs"], padx=(20, 80), anchor="w")
        self._scroll_to_bottom()

        # Buffering for streaming speech and emotion parsing
        self._stream_buffer = ""
        self._current_emotion = "seria"
        self._emotion_parsed = False
        self._emotion_buffer = ""

        def on_token(token):
            # If emotion has not been parsed yet, buffer and check
            if not self._emotion_parsed:
                self._emotion_buffer += token
                if "]" in self._emotion_buffer:
                    import re
                    match = re.search(r'\[EMOCION:\s*([a-zA-Z]+)\]', self._emotion_buffer)
                    if match:
                        self._current_emotion = match.group(1).lower().strip()
                        self._emotion_parsed = True
                        
                        # Update the role label with the parsed emotion!
                        self.after(0, lambda emo=self._current_emotion: self._active_bubble.update_emotion(emo))
                        
                        # The remaining text after "]" goes to the stream and speech buffers
                        parts = self._emotion_buffer.split("]", 1)
                        token = parts[1]
                    else:
                        if len(self._emotion_buffer) > 40:
                            self._emotion_parsed = True
                            token = self._emotion_buffer
                        else:
                            return
                else:
                    if len(self._emotion_buffer) > 40:
                        self._emotion_parsed = True
                        token = self._emotion_buffer
                    else:
                        return

            if token:
                # Update UI
                self.after(0, lambda t=token: self._active_bubble.append_text(t))
                
                # Speak buffering
                self._stream_buffer += token
                import re
                parts = re.split(r'(?<=[.!?。！？\n])', self._stream_buffer)
                if len(parts) > 1:
                    finished_parts = parts[:-1]
                    self._stream_buffer = parts[-1]
                    
                    # Speak each finished sentence
                    for s in finished_parts:
                        s_clean = s.strip()
                        if s_clean:
                            self.after(0, lambda text=s_clean: self._speak_sentence_realtime(text))

        def inference_thread():
            try:
                response = self._chat_mgr.send_message(
                    text,
                    model_path,
                    on_token_callback=on_token
                )
                self.after(0, lambda r=response: self._on_stream_complete(r))
            except Exception as e:
                self.after(0, lambda err=str(e): self._on_stream_error(err))

        threading.Thread(target=inference_thread, daemon=True).start()

    def _speak_sentence_realtime(self, sentence: str):
        mgr = self.voice_mgr
        if mgr and mgr.tts_enabled:
            # Robust language detection
            lang = "es"
            has_japanese = False
            for char in sentence:
                code = ord(char)
                # Hiragana, Katakana, Kanji
                if (0x3040 <= code <= 0x309F) or (0x30A0 <= code <= 0x30FF) or (0x4E00 <= code <= 0x9FBF):
                    has_japanese = True
                    break
            
            if has_japanese:
                lang = "ja"
            else:
                import re
                words = re.findall(r'\b[a-zA-Z]+\b', sentence.lower())
                english_words = {
                    "the", "you", "and", "of", "is", "that", "was", "are", "with", "this",
                    "they", "your", "hello", "what", "how", "good", "doing", "thanks", "thank"
                }
                english_count = sum(1 for w in words if w in english_words)
                if english_count > 0:
                    lang = "en"
            
            mgr.speak_chunk(sentence, lang, emotion=getattr(self, "_current_emotion", "seria"))

    def _on_stream_complete(self, response: str):
        self._sending = False
        try:
            self._send_btn.configure(state="normal", text="Send")
        except:
            pass

        # Speak whatever remains in the buffer
        last_chunk = self._stream_buffer.strip() if hasattr(self, "_stream_buffer") else ""
        if last_chunk:
            self._speak_sentence_realtime(last_chunk)

        # Apply final formatted markdown parsing
        if hasattr(self, "_active_bubble") and self._active_bubble:
            import re
            clean_response = re.sub(r'\[EMOCION:\s*([a-zA-Z]+)\]', '', response).strip()
            self._active_bubble.set_markdown_content(clean_response)

        self._scroll_to_bottom()

    def _on_stream_error(self, err_msg: str):
        self._sending = False
        try:
            self._send_btn.configure(state="normal", text="Send")
        except:
            pass
        if hasattr(self, "_active_bubble") and self._active_bubble:
            self._active_bubble.set_markdown_content(f"Error: {err_msg}")
        self._scroll_to_bottom()

    def _add_message(self, role: str, content: str):
        bubble = MessageBubble(self._messages_scroll, role, content)
        
        if role == "user":
            bubble.pack(fill="x", pady=SPACING["xs"], padx=(80, 20), anchor="e")
        else:
            bubble.pack(fill="x", pady=SPACING["xs"], padx=(20, 80), anchor="w")

        self.after(100, self._scroll_to_bottom)

    def _scroll_to_bottom(self):
        try:
            self._messages_scroll._parent_canvas.yview_moveto(1.0)
        except:
            pass

    def _create_session(self):
        self._chat_mgr.create_session(title=f"Chat {len(self._chat_mgr.list_sessions()) + 1}")
        self._refresh_sessions()
        self._reload_messages()

    def _delete_session(self):
        session = self._chat_mgr.current_session
        if not session:
            return
        title = session.title
        if not msgbox.askyesno("Confirmar", f"¿Eliminar '{title}'?"):
            return
        
        # Stop speaking when deleting the session
        mgr = self.voice_mgr
        if mgr:
            mgr.stop_speaking()

        self._chat_mgr.delete_session(session.id)
        self._refresh_sessions()
        self._reload_messages()

    def _on_session_change(self, value):
        selected_title = self._session_combo.get()
        if not selected_title:
            return
        for session in self._chat_mgr.list_sessions():
            if session.title == selected_title:
                self._chat_mgr.switch_session(session.id)
                self._reload_messages()
                break

    def _reload_messages(self):
        for widget in self._messages_scroll.winfo_children():
            widget.destroy()

        session = self._chat_mgr.current_session
        if session and session.messages:
            for msg in session.messages:
                self._add_message(msg.role, msg.content)
        else:
            self._show_welcome_message()

    def _on_map(self, event):
        """Called when the page is mapped on screen. Refreshes message geometry."""
        # Wait 50ms for geometry and sizes to settle, then reload.
        self.after(50, self._reload_messages)

    def _on_model_change(self, value):
        model_name = self._model_combo.get()
        if model_name:
            models_dir = self._config.get("paths.models_dir", "./models")
            model_path = os.path.join(models_dir, model_name)
            self._config.set("llama.selected_model_path", model_path)
            self._config.save()
            status = "Ready" if os.path.exists(model_path) else "Not found"
            color = C["accent_green"] if os.path.exists(model_path) else C["accent_red"]
            self._model_status.configure(text=status, text_color=color)

    def _refresh_models(self):
        models_dir = self._config.get("paths.models_dir", "./models")
        downloaded = []
        if os.path.isdir(models_dir):
            downloaded = [f for f in os.listdir(models_dir) if f.endswith(".gguf")]
        
        names = sorted(downloaded)
        self._model_combo.configure(values=names)

        current_path = self._config.get("llama.selected_model_path", "")
        current_name = os.path.basename(current_path)

        if current_name in names:
            self._model_combo.set(current_name)
            self._model_status.configure(text="Ready", text_color=C["accent_green"])
        elif names:
            self._model_combo.set(names[0])
            self._model_status.configure(text="Ready", text_color=C["accent_green"])

    def _refresh_sessions(self):
        sessions = self._chat_mgr.list_sessions()
        names = [s.title for s in sessions]
        self._session_combo.configure(values=names)

        if sessions and self._chat_mgr.current_session:
            current = self._chat_mgr.current_session
            if current.title in names:
                self._session_combo.set(current.title)

        # Render the current session's messages (handles the case where a
        # session with history was loaded from disk on startup).
        self._reload_messages()

    def add_assistant_message(self, content: str):
        self._add_message("assistant", content)

    @property
    def voice_mgr(self):
        """Busca el administrador de voz en la ventana principal."""
        current = self.master
        while current:
            if hasattr(current, "_voice_mgr"):
                return current._voice_mgr
            current = current.master
        return None

    def _toggle_mic(self):
        """Alterna el estado de grabación del micrófono."""
        import threading
        mgr = self.voice_mgr
        if not mgr or not mgr.stt_enabled:
            msgbox.showinfo("Entrada de voz deshabilitada", "Por favor habilita la Entrada de Voz en la pestaña de Ajustes.")
            return

        if mgr.is_recording():
            # Detener y transcribir
            self._mic_btn.configure(text="⌛", fg_color="transparent", text_color=C["accent_amber"])
            self._send_btn.configure(state="disabled")
            
            def process_recording():
                success, path_or_error = mgr.stop_recording()
                if success:
                    self.after(0, lambda: self._mic_btn.configure(text="🎙️..."))
                    text, lang = mgr.transcribe_audio(path_or_error)
                    self.after(0, lambda: self._on_voice_transcribed(text))
                else:
                    self.after(0, self._reset_mic_button)
                    self.after(0, lambda: msgbox.showerror("Error de Voz", f"Error al grabar audio: {path_or_error}"))
                    
            threading.Thread(target=process_recording, daemon=True).start()
        else:
            # Grabar
            success = mgr.start_recording()
            if success:
                self._mic_btn.configure(text="🔴", fg_color=C["accent_red"], text_color="#FFFFFF")
            else:
                msgbox.showerror("Error de Voz", "No se pudo iniciar la grabación. Revisa tu micrófono.")

    def _reset_mic_button(self):
        """Restaura el botón del micrófono a su estado inicial."""
        self._mic_btn.configure(text="🎤", fg_color="transparent", text_color=C["accent"], state="normal")
        self._send_btn.configure(state="normal")

    def _on_voice_transcribed(self, text: str):
        """Maneja el texto transcribido de voz."""
        self._reset_mic_button()
        if text.strip():
            self._input.delete("0.0", "end")
            self._input.insert("0.0", text)
            # Enviar mensaje
            self._send_message()

    def _toggle_hands_free(self):
        """Alterna el estado del Modo Manos Libres (Speech-to-Speech)."""
        mgr = self.voice_mgr
        if not mgr:
            msgbox.showerror("Error de Voz", "El administrador de voz no está inicializado.")
            self._hands_free_var.set(False)
            return

        enabled = self._hands_free_var.get()
        if enabled:
            # Forzar activar STT y TTS en config si están apagados, para que funcione
            if not mgr.stt_enabled or not mgr.tts_enabled:
                mgr.stt_enabled = True
                mgr.tts_enabled = True
                self._config.set("voice.stt_enabled", True)
                self._config.set("voice.tts_enabled", True)
                self._config.save()
                
            success = mgr.start_hands_free(self._on_hands_free_state_change, self._on_hands_free_text_received)
            if not success:
                self._hands_free_var.set(False)
                msgbox.showerror("Error de Voz", "No se pudo iniciar el Modo Manos Libres.")
        else:
            mgr.stop_hands_free()
            self._on_hands_free_state_change("idle")

    def _on_hands_free_state_change(self, state: str):
        """Callback del VoiceManager cuando cambia el estado del bucle manos libres."""
        self.after(0, lambda: self._update_hands_free_ui(state))

    def _update_hands_free_ui(self, state: str):
        """Actualiza los widgets de la UI según el estado del modo manos libres."""
        try:
            if state == "calibrating":
                self._mic_btn.configure(text="📏", fg_color=C["accent_amber"], text_color="#FFFFFF", state="disabled")
                self._hands_free_status_lbl.configure(text="Calibrando ruido...", text_color=C["accent_amber"])
                self._input.configure(state="disabled")
            elif state == "waiting_wake_word":
                self._mic_btn.configure(text="🤖", fg_color="transparent", text_color=C["accent"], state="disabled")
                self._hands_free_status_lbl.configure(text="Dí 'Astra' para activar...", text_color=C["text_muted"])
                self._input.configure(state="disabled")
            elif state == "listening":
                self._mic_btn.configure(text="🔴", fg_color=C["accent_red"], text_color="#FFFFFF", state="disabled")
                self._hands_free_status_lbl.configure(text="Astra te escucha...", text_color=C["accent_red"])
                self._input.configure(state="disabled")
            elif state == "processing":
                self._mic_btn.configure(text="⌛", fg_color="transparent", text_color=C["accent_amber"], state="disabled")
                self._hands_free_status_lbl.configure(text="Pensando...", text_color=C["accent_amber"])
                self._input.configure(state="disabled")
            elif state == "speaking":
                self._mic_btn.configure(text="🔊", fg_color="transparent", text_color=C["accent_green"], state="disabled")
                self._hands_free_status_lbl.configure(text="Astra hablando...", text_color=C["accent_green"])
                self._input.configure(state="disabled")
            else: # idle/off
                self._reset_mic_button()
                self._hands_free_status_lbl.configure(text="", text_color=C["text_muted"])
                self._input.configure(state="normal")
        except:
            pass

    def _on_hands_free_text_received(self, text: str):
        """Callback del VoiceManager cuando se recibe y transcribe el audio del usuario."""
        if text.strip():
            self.after(0, lambda: self._submit_hands_free_message(text))

    def _submit_hands_free_message(self, text: str):
        """Inyecta el texto transcribido y lo envía."""
        try:
            self._input.configure(state="normal")
            self._input.delete("0.0", "end")
            self._input.insert("0.0", text)
            self._send_message()
            if self._hands_free_var.get():
                self._input.configure(state="disabled")
        except Exception as e:
            import logging
            logger = logging.getLogger("VTManager.Chat")
            logger.error("Error submitting hands-free message: %s", e)