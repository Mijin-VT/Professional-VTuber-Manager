"""User Manual Widget for VT Manager.
Provides a comprehensive, paginated, and beautifully styled guide for all features.
"""
import customtkinter as ctk
from app.theme import COLORS as C, SPACING, RADIUS, font, font_bold, font_heading, font_subheading

class UserManualPage(ctk.CTkScrollableFrame):
    """User Manual page with comprehensive details about the application."""

    def __init__(self, parent):
        super().__init__(parent, fg_color=C["bg_primary"],
                         scrollbar_button_color=C["scrollbar"],
                         scrollbar_button_hover_color=C["border_hover"])
        self._current_page = 0
        self._pages_list = []
        self._build_ui()

    def _build_ui(self):
        self.grid_columnconfigure(0, weight=1)

        # ─── Welcome Header ───
        header_card = ctk.CTkFrame(self, fg_color=C["bg_tertiary"], corner_radius=RADIUS["lg"],
                                   border_width=1, border_color=C["border"])
        header_card.pack(fill="x", padx=SPACING["xl"], pady=(SPACING["xl"], SPACING["lg"]))
        header_card.grid_columnconfigure(0, weight=1)

        ctk.CTkLabel(
            header_card, text="📖 VT Manager — User Manual",
            font=font_heading(18), text_color=C["accent"]
        ).grid(row=0, column=0, padx=SPACING["lg"], pady=(SPACING["lg"], 4), sticky="w")

        ctk.CTkLabel(
            header_card, 
            text="Welcome to the help center. Use the pagination controls below to navigate through the technical and operational details of VT Manager's features.",
            font=font(12), text_color=C["text_secondary"], wraplength=800, justify="left", anchor="w"
        ).grid(row=1, column=0, padx=SPACING["lg"], pady=(0, SPACING["lg"]), sticky="ew")

        # ─── Content Container (Holds cards) ───
        self.content_container = ctk.CTkFrame(self, fg_color="transparent")
        self.content_container.pack(fill="both", expand=True)

        # ─── Page 0: Overview of Application Tools ───
        tools_card = self._create_section_card("0. 🛠️ Overview of Application Tools (Sidebar Pages)")
        self._add_bullet(tools_card, "Models selection Page (Models):", "Allows you to scan, download, and load GGUF models locally. It shows memory estimates (RAM/VRAM) and lets you download models directly from HuggingFace with live speed and ETA indicators.")
        self._add_bullet(tools_card, "AI Chat Manager (AI Chat Manager):", "The central interface to chat with Astra Valeria. Supports text chat, suggestions, voice-to-text input (STT), cloned speech responses (TTS), long-term semantic memory, and continuous hands-free dialogue.")
        self._add_bullet(tools_card, "Streaming Schedule (Schedule):", "A calendar-based planner to manage your streams. Supports custom titles, dates, platform filters (Twitch, YouTube, Kick, TikTok), and duration, persisting all data locally.")
        self._add_bullet(tools_card, "Tasks & To-Do (Tasks):", "A checklist manager to track goals and priorities. You can check off items, set priorities, and let Astra autonomously add tasks directly from your chat conversations.")
        self._add_bullet(tools_card, "Stream Planning (Planning):", "A brainstorming board to capture and categorize creative content, collab notes, and game ideas. Features copy buttons to quickly share ideas with Astra.")
        self._add_bullet(tools_card, "Metrics & Analytics (Metrics):", "A live dashboard displaying active viewer counts, sub rates, stream status, and chat events by connecting directly to OBS, Twitch, and simulated Kick APIs.")
        self._add_bullet(tools_card, "System Settings (Settings):", "The control center to toggle long-term memory, calibrate mic thresholds, choose speech synthesizers (SAPI5/MOSS), set wake words, and test OBS connections.")
        self._pages_list.append(tools_card)

        # ─── Page 1: AI Chat & Local Memory ───
        chat_card = self._create_section_card("1. 💬 AI Chat & Long-Term Memory (Mem0)")
        self._add_bullet(chat_card, "Interacting with Astra:", "Astra Valeria is programmed with a demanding but motivating personality, with over 10 years of experience in the industry. She is not a generic chatbot: she will give you strategic advice based on metrics and your lore.")
        self._add_bullet(chat_card, "Natural Conversational Flow:", "Astra is configured via system prompts to speak fluidly and directly. She will never start her responses with repetitive self-introductions (like 'Hello! I am Astra...'), allowing for natural dialogue.")
        self._add_bullet(chat_card, "Semantic Memory (Mem0):", "Features a local vector database system (Chroma DB) in `data/mem0_db`. It asynchronously saves important details about your streams, moderator names, or annual goals.")
        self._add_bullet(chat_card, "Memory Management:", "You can activate, deactivate, or clear the local memory database instantly from the **Settings** tab.")
        self._add_note(chat_card, "The memory system runs 100% locally via `llama-cli.exe` using the 'sentence-transformers/all-MiniLM-L6-v2' embedding model. It does not require an internet connection or API keys.")
        self._pages_list.append(chat_card)

        # ─── Page 2: Voice Module & Hands-Free Interaction ───
        voice_card = self._create_section_card("2. 🎙️ Voice Module & Hands-Free Interaction (Speech-to-Speech)")
        self._add_bullet(voice_card, "Voice Input and Output:", "Allows transcribing your microphone to text using local Whisper (`faster-whisper`) and playing back Astra's cloned voice in Spanish, English, or Japanese.")
        self._add_bullet(voice_card, "Synthesis Engines (TTS):", "Supports **MOSS-TTS** (for zero-shot cloning with reference audio) and **Windows SAPI5** (native offline fallback that generates dynamic PowerShell scripts without requiring heavy downloads).")
        self._add_bullet(voice_card, "Automatic Language Detection:", "The speech synthesizer scans the AI response searching for kanji/kana characters, accents, or pronouns to automatically speak to you in the correct language.")
        self._add_bullet(voice_card, "Hands-Free Mode (S2S Continuous Loop):", "Activated via the toggle switch in the chat screen. It follows the following operational logic:")
        self._add_sub_bullet(voice_card, "📏 Silence Calibration:", "Upon activation, it measures room noise for 1 second to establish the optimal microphone threshold dynamically.")
        self._add_sub_bullet(voice_card, "🤖 Wake Word Standby:", "Listens passively in a lightweight 2-second loop. When you say 'Astra' or 'Hello Astra', it emits a beep and enters active conversation mode.")
        self._add_sub_bullet(voice_card, "🔴 Active Conversation (VAD):", "Records your voice. The moment you stop speaking for more than 1.5 seconds, it cuts the stream, transcribes, generates the response with the LLM, plays it back, and returns to active listening (🔴) without you having to touch the mouse.")
        self._add_sub_bullet(voice_card, "👋 Auto Disconnect:", "If you remain silent for 3 consecutive turns, Astra will emit an exit beep, say goodbye, and return to the wake word standby state (🤖) to conserve resources.")
        self._add_note(voice_card, "If the application does not detect any connected microphone or there are sound hardware issues, the system will gracefully degrade to 'Simulation Mode', allowing you to test the interactive UI without crashes.")
        self._pages_list.append(voice_card)

        # ─── Page 3: Autonomous AI Task Management ───
        tasks_card = self._create_section_card("3. 📋 Autonomous AI Task Management")
        self._add_bullet(tasks_card, "Task Database:", "Your commitments and goals are saved in the local `data/tasks.json` file with support for priorities (High, Medium, Low) and completion statuses.")
        self._add_bullet(tasks_card, "Astra's Autonomous Planning:", "You can ask Astra to remind you of a stream, note down a follower goal, or plan a collaboration. During the chat, Astra will inject instructions in the form of hidden tags (e.g. `[ADD_TASK: Collaboration with Valeria | High]`).")
        self._add_bullet(tasks_card, "Interception & Async Registration:", "The chat manager detects these tags, silently saves them to the task database, and removes them from the final text bubble to keep the UI clean.")
        self._add_bullet(tasks_card, "Hot Syncing:", "The **Tasks** tab updates its list automatically every time you access it, ensuring immediate consistency.")
        self._pages_list.append(tasks_card)

        # ─── Page 4: OBS and Streaming Networks Integration ───
        stream_card = self._create_section_card("4. 🔌 OBS Studio, Twitch, and Kick Integration")
        self._add_bullet(stream_card, "OBS Studio Control:", "Connect to your OBS Studio WebSocket port (usually localhost:4455). You can verify the connection using the 'Test OBS Connection' button in Settings.")
        self._add_bullet(stream_card, "Live Stream Monitoring:", "The **Metrics** tab features stream status indicators, active viewer counts on Twitch/Kick, new follower rate, and stream duration.")
        self._add_bullet(stream_card, "Real-Time Context Ingestion:", "Live stream statistics (e.g., whether the stream is active or if there is a drastic drop in viewership) are dynamically injected into Astra's prompt. This allows her to alert you live if she detects issues with the broadcast.")
        self._pages_list.append(stream_card)

        # ─── Page 5: GGUF Models & GPU Layer Allocation Guide ───
        models_card = self._create_section_card("5. ⚙️ GGUF Models & GPU Layer Allocation Guide")
        self._add_bullet(models_card, "🚀 Large Models (VRAM 24GB+):", "Heavy models like Command-R 35B or Hermes-3-Llama-3-70B. They offer maximum coherence and business intelligence.")
        self._add_bullet(models_card, "⚡ Medium Models (VRAM 16GB):", "Models like Mistral-Nemo-12B (with excellent Spanish fluency) and Hermes-3-8B. They offer the best balance of speed and wit.")
        self._add_bullet(models_card, "💎 Light Models 2 (VRAM 6GB-12GB):", "Models like Saiga-Stheno-8B (specialized in internet slang and informal chat) and Meta-Llama-3.1-8B (with a giant 128k context window).")
        self._add_bullet(models_card, "📦 Light Models (VRAM 4GB-6GB):", "Lightweight models like Hermes-3-Llama-3.2-3B, Qwen-2.5-1.5B, or Yi-Coder-1.5B (programming assistant).")
        self._add_bullet(models_card, "GPU Layer Allocation Logic:", "The system dynamically determines how many neural network layers to offload to the graphics card (VRAM) based on:")
        self._add_sub_bullet(models_card, "Low-end card (<=8GB VRAM):", "Maintains a strict 1.5GB safety margin to ensure OBS and games run smoothly.")
        self._add_sub_bullet(models_card, "Mid-range card (8GB-12GB VRAM):", "Maintains a 1.0GB safety margin.")
        self._add_sub_bullet(models_card, "High-end card (>=12GB VRAM):", "Aggressive allocation, leaving only 512MB free for the operating system.")
        self._add_note(models_card, "If a model is larger than your available VRAM, the remaining layers will be processed by your PC's CPU. This allows running giant models at lower speeds instead of crashing.")
        self._pages_list.append(models_card)

        # ─── Page 6: Stream Schedule & Calendar ───
        calendar_card = self._create_section_card("6. 📅 Stream Schedule & Calendar (Schedule)")
        self._add_bullet(calendar_card, "Schedule Organization:", "Register your upcoming broadcasts by setting the event title, date, platform (Twitch, YouTube, Kick, or TikTok), and estimated duration in hours.")
        self._add_bullet(calendar_card, "Visual Color Codes:", "Identify at a single glance which platform you will stream on, thanks to the lateral color bars associated with each service (Purple for Twitch, Red for YouTube, Green for Kick, etc.).")
        self._add_bullet(calendar_card, "Local Persistence:", "All planned events are securely stored in `data/calendar_events.json` to persist information locally without external servers.")
        self._pages_list.append(calendar_card)

        # ─── Page 7: Content Ideation ───
        planning_card = self._create_section_card("7. 💡 Content Ideation & Collaboration (Stream Planning)")
        self._add_bullet(planning_card, "Concept Management:", "A clean area for brainstorming new stream mechanics, challenges, giveaways, or dynamics with your community.")
        self._add_bullet(planning_card, "Thematic Categorization:", "Group your ideas into key categories (Gaming, IRL, ASMR, RP, Collab, Creative, Just Chatting, etc.) with dynamic colors to maintain production order.")
        self._add_bullet(planning_card, "Copy & Share:", "Each idea has a quick button to copy its content to the clipboard, allowing you to quickly inject it into your planning dialogues with Astra.")
        self._pages_list.append(planning_card)

        # ─── Page 8: Complete Settings Guide ───
        settings_card = self._create_section_card("8. ⚙️ Complete Settings Configuration Guide")
        self._add_bullet(settings_card, "Hardware Information:", "Displays detected hardware assets: GPU name, total VRAM, system RAM, CUDA availability, and the recommended category of models (Large, Medium, Light 2, Light) optimized for your setup.")
        self._add_bullet(settings_card, "Paths & Folders:", "Shows the local binary executables path and allows you to change the directory where GGUF model files are downloaded, stored, and scanned on startup.")
        self._add_bullet(settings_card, "Long-Term Memory (Mem0):", "Allows toggling long-term semantic memory. You can also completely purge the Chroma vector database by clicking 'Clear Memory Database'.")
        self._add_bullet(settings_card, "Streaming API Config:", "Enter your Twitch/Kick channels to monitor chat/metrics. Set the OBS websocket host, port (e.g., localhost:4455), password, and test the connection in real-time.")
        self._add_bullet(settings_card, "Voice Settings (STT/TTS):", "Toggle voice inputs/outputs. Select your engine: SAPI5 (Windows offline) or MOSS-TTS (zero-shot voice cloning). Set your preferred voice language (auto, es, en, ja).")
        self._add_bullet(settings_card, "MOSS & VAD Config:", "Set MOSS-TTS server URLs and reference audio paths. Define the wake word key (e.g., 'Astra') and adjust the VAD Threshold slider (100 to 2000) to fine-tune mic silence detection.")
        self._add_bullet(settings_card, "System Prompt Editor:", "An editor to modify and save the system prompt that defines Astra's personality, lore constraints, task command abilities, and Spanish/English conversational style.")
        self._pages_list.append(settings_card)

        # ─── Create Top and Bottom Pagination Bars ───
        self._create_pagination_bar(is_top=True)
        self._create_pagination_bar(is_top=False)

        # ─── Initial Page Show ───
        self._show_page(0)

    def _create_pagination_bar(self, is_top=True):
        nav_frame = ctk.CTkFrame(self, fg_color="transparent")
        if is_top:
            nav_frame.pack(fill="x", padx=SPACING["xl"], pady=(SPACING["sm"], SPACING["md"]), before=self.content_container)
        else:
            nav_frame.pack(fill="x", padx=SPACING["xl"], pady=(SPACING["md"], SPACING["xl"]))
        
        nav_inner = ctk.CTkFrame(nav_frame, fg_color="transparent")
        nav_inner.pack(anchor="center")
        
        prev_btn = ctk.CTkButton(
            nav_inner, text="◀ Prev", width=70, height=28, font=font_bold(11),
            fg_color=C["bg_tertiary"], hover_color=C["sidebar_hover"],
            text_color=C["text_primary"], corner_radius=RADIUS["sm"],
            command=self._prev_page
        )
        prev_btn.pack(side="left", padx=SPACING["xs"])
        
        if is_top:
            self._top_prev_btn = prev_btn
        else:
            self._bot_prev_btn = prev_btn
            
        page_btns = []
        for i in range(9):
            btn = ctk.CTkButton(
                nav_inner, text=str(i + 1), width=32, height=28, font=font_bold(11),
                fg_color=C["bg_tertiary"], hover_color=C["sidebar_hover"],
                text_color=C["text_secondary"], corner_radius=RADIUS["sm"],
                command=lambda idx=i: self._show_page(idx)
            )
            btn.pack(side="left", padx=2)
            page_btns.append(btn)
            
        if is_top:
            self._top_page_btns = page_btns
        else:
            self._bot_page_btns = page_btns
            
        next_btn = ctk.CTkButton(
            nav_inner, text="Next ▶", width=70, height=28, font=font_bold(11),
            fg_color=C["bg_tertiary"], hover_color=C["sidebar_hover"],
            text_color=C["text_primary"], corner_radius=RADIUS["sm"],
            command=self._next_page
        )
        next_btn.pack(side="left", padx=SPACING["xs"])
        
        if is_top:
            self._top_next_btn = next_btn
        else:
            self._bot_next_btn = next_btn

    def _show_page(self, index: int):
        if index < 0 or index >= len(self._pages_list):
            return
        
        # Hide all pages
        for page in self._pages_list:
            page.pack_forget()
            
        # Show selected page
        self._current_page = index
        self._pages_list[index].pack(fill="x", padx=SPACING["xl"], pady=(0, SPACING["lg"]))
        
        # Update pagination buttons state & highlights
        self._update_pagination_ui()
        
        # Scroll scrollable frame back to the top
        try:
            self._parent_canvas.yview_moveto(0.0)
        except Exception:
            pass

    def _prev_page(self):
        if self._current_page > 0:
            self._show_page(self._current_page - 1)

    def _next_page(self):
        if self._current_page < len(self._pages_list) - 1:
            self._show_page(self._current_page + 1)

    def _update_pagination_ui(self):
        idx = self._current_page
        total = len(self._pages_list)
        
        # Update Prev buttons
        prev_state = "disabled" if idx == 0 else "normal"
        prev_color = C["text_muted"] if idx == 0 else C["text_primary"]
        self._top_prev_btn.configure(state=prev_state, text_color=prev_color)
        self._bot_prev_btn.configure(state=prev_state, text_color=prev_color)
        
        # Update Next buttons
        next_state = "disabled" if idx == total - 1 else "normal"
        next_color = C["text_muted"] if idx == total - 1 else C["text_primary"]
        self._top_next_btn.configure(state=next_state, text_color=next_color)
        self._bot_next_btn.configure(state=next_state, text_color=next_color)
        
        # Highlight active page button
        for i in range(total):
            if i == idx:
                self._top_page_btns[i].configure(fg_color=C["accent"], text_color="#FFFFFF")
                self._bot_page_btns[i].configure(fg_color=C["accent"], text_color="#FFFFFF")
            else:
                self._top_page_btns[i].configure(fg_color=C["bg_tertiary"], text_color=C["text_secondary"])
                self._bot_page_btns[i].configure(fg_color=C["bg_tertiary"], text_color=C["text_secondary"])

    def _create_section_card(self, title: str) -> ctk.CTkFrame:
        """Helper to create a structured section card."""
        card = ctk.CTkFrame(self.content_container, fg_color=C["bg_tertiary"], corner_radius=RADIUS["lg"],
                            border_width=1, border_color=C["border"])
        card.grid_columnconfigure(1, weight=1)

        ctk.CTkLabel(
            card, text=title,
            font=font_subheading(13), text_color=C["accent"],
        ).grid(row=0, column=0, columnspan=2, padx=SPACING["lg"], pady=(SPACING["lg"], SPACING["md"]), sticky="w")
        
        # Add internal grid row tracker
        card.current_row = 1
        return card

    def _add_bullet(self, card: ctk.CTkFrame, bold_txt: str, normal_txt: str):
        """Helper to add bullet points inside cards."""
        row = card.current_row
        ctk.CTkLabel(
            card, text="•", font=font_bold(14), text_color=C["accent"]
        ).grid(row=row, column=0, padx=(SPACING["lg"], SPACING["xs"]), pady=3, sticky="nw")

        lbl = ctk.CTkLabel(
            card, text=f"{bold_txt} {normal_txt}", font=font(11), text_color=C["text_primary"],
            wraplength=800, justify="left", anchor="w"
        )
        lbl.grid(row=row, column=1, padx=(0, SPACING["lg"]), pady=3, sticky="ew")
        
        card.current_row += 1

    def _add_sub_bullet(self, card: ctk.CTkFrame, bold_txt: str, normal_txt: str):
        """Helper to add indented sub-bullet points inside cards."""
        row = card.current_row
        ctk.CTkLabel(
            card, text="  ○", font=font_bold(11), text_color=C["accent_purple"]
        ).grid(row=row, column=0, padx=(SPACING["2xl"], SPACING["xs"]), pady=2, sticky="nw")

        lbl = ctk.CTkLabel(
            card, text=f"{bold_txt} {normal_txt}", font=font(10), text_color=C["text_secondary"],
            wraplength=800, justify="left", anchor="w"
        )
        lbl.grid(row=row, column=1, padx=(0, SPACING["lg"]), pady=2, sticky="ew")

        card.current_row += 1

    def _add_note(self, card: ctk.CTkFrame, text: str):
        """Helper to add alert-like notes inside cards."""
        row = card.current_row
        note_frame = ctk.CTkFrame(card, fg_color=C["sidebar_active"], corner_radius=RADIUS["sm"],
                                  border_width=1, border_color=C["msg_ai_border"])
        note_frame.grid(row=row, column=0, columnspan=2, padx=SPACING["lg"], pady=SPACING["md"], sticky="ew")
        note_frame.grid_columnconfigure(0, weight=1)

        ctk.CTkLabel(
            note_frame, text=f"💡 NOTE: {text}", font=font(10), text_color=C["accent_cyan"],
            wraplength=800, justify="left", anchor="w"
        ).grid(row=0, column=0, padx=SPACING["md"], pady=SPACING["sm"], sticky="ew")

        card.current_row += 1
