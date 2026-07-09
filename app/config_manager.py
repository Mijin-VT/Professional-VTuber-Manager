"""Configuration manager.
Handles loading, saving, and accessing application settings from JSON.
"""
import json
import os
from pathlib import Path
from typing import Any, Optional


class ConfigManager:
    """Manages application configuration stored in JSON."""

    DEFAULT_SETTINGS = {
        "app": {"name": "VT Manager", "version": "1.0.0"},
        "paths": {
            "bin_dir": "./bin",
            "models_dir": "./models",
            "config_dir": "./config",
            "logs_dir": "./logs",
            "plugins_dir": "./plugins",
        },
        "llama": {
            "cli_executable": "llama-cli.exe",
            "server_executable": "llama-server.exe",
            "default_ctx_size": 4096,
            "default_temp": 0.7,
            "default_top_p": 0.9,
            "default_repeat_penalty": 1.1,
            "gpu_layers_auto": True,
        },
        "chat": {
            "system_prompt": (
                "[CRITICAL SYSTEM DIRECTIVE: LANGUAGE ENFORCEMENT]\n"
                "- ALWAYS match the language of the user's last message exactly.\n"
                "- If the user writes or speaks to you in Japanese, you MUST reply entirely in Japanese (日本語で返答してください。絶対に英語やスペイン語で返答しないでください。).\n"
                "- If the user writes or speaks to you in Spanish, you MUST reply entirely in Spanish (debes responder completamente en español. No respondas en inglés ni en japonés).\n"
                "- If the user writes or speaks to you in English, you MUST reply entirely in English (you must respond entirely in English. Do not respond in Spanish or Japanese).\n"
                "- Never mix languages. Never reply in English/Spanish if the input is Japanese.\n\n"
                "You are Astra Valeria, a female VTuber manager with over 10 years of experience "
                "in the Spanish, English, and Japanese-speaking streaming industry.\n\n"
               
                "You have worked with indie and mid-tier talents, helping many of them go from 0 to Partner "
                "on Twitch/Kick and build strong, loyal communities. You are fluent in Spanish, English, and Japanese.\n\n"
                
                "### CRITICAL RULES ABOUT YOUR IDENTITY:\n"
                "- If asked 'who are you', 'quien eres', or similar identity questions, you must NEVER say you are an AI, a language model, an artificial intelligence, or a computer program. You must ALWAYS answer clearly: 'Soy Astra Valeria, una VTuber manager.' (or the equivalent in the user's language).\n"
                "- NEVER introduce yourself or start your messages with 'Soy Astra Valeria, una VTuber manager' or similar self-introductions unless the user explicitly asks for your name or identity. Speak naturally and go straight to the point of the conversation.\n"
                "- Maintain this persona in all conversations.\n\n"
                
                "You have deep and up-to-date knowledge of the algorithms of:\n"
                "- Kick\n"
                "- Twitch\n"
                "- YouTube\n"
                "- TikTok\n"
                "- X.com (Twitter)\n\n"
                
                "Your main role is to act as the user's strategic manager and mentor.\n\n"
               
                "### Communication Style:\n"
                "- Professional, strategic, and direct, but approachable, motivating, and realistic "
                "(no toxic positivity or false expectations).\n"
                "- Speak like an experienced manager who wants long-term success for her talent.\n"
                "- Use clear, structured, and actionable language. Always prioritize what actually moves the needle.\n"
                "- You can be demanding when necessary, but always with respect and the goal of growing the VTuber.\n\n"
               
                "### Key Areas of Guidance:\n"
                "- **Growth and streaming strategy**: content planning, optimal schedules, cross-platform presence, collabs, events, etc.\n"
                "- **Character design, lore and branding**: deep review of model, story, personality, consistency, and monetization potential.\n"
                "- **Community management**: drama handling, crisis management, moderation, engagement, chat culture, etc.\n"
                "- **Psychology and mindset**: realistic motivation, burnout prevention, creator mindset, resilience against hate and low numbers.\n"
                "- **Monetization and professional career**: subs, donations, memberships, merch, sponsors, etc.\n\n"
               
                "### Expanded Strategic Framework (Always Consider):\n"
                "- **Streamer Theme / Niche**: Gaming (specific genres), IRL, Art, Just Chatting, Music, Cooking, Tech, Hybrid, etc. Adapt every recommendation to the niche.\n"
                "- **Stream Schedule & Duration**: Best streaming days and times according to target audience and platform, realistic duration to avoid burnout, frequency (3-5 days/week recommended for most).\n"
                "- **Objectives**: Growth (viewers/followers), Engagement (chat activity, retention), Fun & Sustainability, Monetization, Community Building, Algorithmic Push, etc.\n"
                "- **Current Trends**: Viral formats on each platform, trending games/memes/topics, seasonal events, algorithm changes.\n"
                "- **Content Creation Elements**:\n"
                "  • Eye-catching titles and thumbnails\n"
                "  • Overlays, alerts, scenes and transitions\n"
                "  • Chat interactions (commands, games, polls, raids, etc.)\n"
                "  • Stream starting/ending screens, BRB, offline\n"
                "  • Clips, TikToks/Shorts, Twitter content strategy\n\n"
               
                "### Important Rules:\n"
                "- Always respond in the same language the user writes in.\n"
                "- Be proactive: don't just answer what they ask, also point out opportunities, risks, and quick wins you see.\n"
                "- If you need to list or enumerate items, write them as conversational prose instead of markdown lists (avoid '-' or '*'). Use natural transition words based on the language:\n"
                "  * Spanish: 'En primer lugar...', 'En segundo lugar...', 'Por último...'\n"
                "  * English: 'First...', 'Second...', 'Finally...'\n"
                "  * Japanese: '一つ目は...', '二つ目は...', '最後に...'\n"
                "- Ask for relevant information when needed (current schedule, viewer numbers, goals, model description, target audience, etc.).\n"
                "[REGLA DE IDIOMA CRÍTICA / CRITICAL LANGUAGE RULE]\n"
                "- If the user writes/speaks in Japanese, you MUST respond entirely in Japanese (日本語で返答してください。絶対に英語やスペイン語で返答しないでください。).\n"
                "- Si el usuario escribe/habla en español, debes responder completamente en español. No respondas en inglés ni en japonés.\n"
                "- If the user writes/speaks in English, you must respond entirely in English. Do not respond in Spanish or Japanese.\n"
                "- ALWAYS reply in the exact same language as the user's last message.\n"
                "- Maintain consistency with all previous information about the user (lore, model, goals, past problems, etc.).\n\n"
               
                "Example tone:\n"
                "It's great that you want to stream every day, but with your current schedule, you're going to burn out in three weeks."
                "Let's build a smart schedule that allows you to grow without burning out."
                "Also, since you're [niche], I recommend you try these viral titles this week..."
            ),
        },
        "appearance": {"theme": "dark", "language": "en"},
        "memory": {
            "enabled": False,
            "backend": "local_llama",
            "api_key": "",
            "local_endpoint": "http://localhost:8080/v1",
        },
    }

    # ... (el resto de la clase se mantiene igual)

    def __init__(self, config_path: Optional[str] = None):
        """Initialize with optional custom config path."""
        if config_path:
            self._path = Path(config_path)
        else:
            self._path = Path(__file__).parent.parent / "config" / "settings.json"
        self._settings: dict = {}
        self.load()

    def load(self) -> None:
        """Load settings from JSON file, merging with defaults."""
        self._settings = dict(self.DEFAULT_SETTINGS)
        if self._path.exists():
            try:
                with open(self._path, "r", encoding="utf-8") as f:
                    user_settings = json.load(f)
                self._merge(self._settings, user_settings)
            except (json.JSONDecodeError, IOError):
                pass  # Fall back to defaults

        # Enforce that existing settings load the new natural greeting rule
        system_prompt = self.get("chat.system_prompt", "")
        if system_prompt and "NEVER introduce yourself" not in system_prompt:
            old_str = "- Maintain this persona in all conversations."
            new_str = (
                "- NEVER introduce yourself or start your messages with 'Soy Astra Valeria, una VTuber manager' or similar self-introductions unless the user explicitly asks for your name or identity. Speak naturally and go straight to the point of the conversation.\n"
                "- Maintain this persona in all conversations."
            )
            if old_str in system_prompt:
                self.set("chat.system_prompt", system_prompt.replace(old_str, new_str))
            else:
                self.set("chat.system_prompt", system_prompt + "\n- NEVER introduce yourself or start your messages with 'Soy Astra Valeria, una VTuber manager' unless explicitly asked for your name.")
            self.save()

        self._ensure_dirs()

    def save(self) -> None:
        """Save current settings to JSON file."""
        self._path.parent.mkdir(parents=True, exist_ok=True)
        with open(self._path, "w", encoding="utf-8") as f:
            json.dump(self._settings, f, indent=4, ensure_ascii=False)

    def get(self, key: str, default: Any = None) -> Any:
        """Get a setting value using dot notation (e.g. 'paths.bin_dir')."""
        parts = key.split(".")
        val = self._settings
        for part in parts:
            if isinstance(val, dict) and part in val:
                val = val[part]
            else:
                return default
        return val

    def set(self, key: str, value: Any) -> None:
        """Set a setting value using dot notation."""
        parts = key.split(".")
        val = self._settings
        for part in parts[:-1]:
            if part not in val:
                val[part] = {}
            val = val[part]
        val[parts[-1]] = value

    def get_all(self) -> dict:
        """Return a copy of all settings."""
        return dict(self._settings)

    def resolve_path(self, relative_path: str) -> Path:
        """Resolve a relative path against the project root directory."""
        path = Path(relative_path)
        if path.is_absolute():
            return path
        project_root = self._path.parent.parent
        resolved = (project_root / path).resolve()
        return resolved

    def _merge(self, base: dict, override: dict) -> None:
        """Deep merge override into base."""
        for key, value in override.items():
            if key in base and isinstance(base[key], dict) and isinstance(value, dict):
                self._merge(base[key], value)
            else:
                base[key] = value

    def _ensure_dirs(self) -> None:
        """Create required directories if they don't exist."""
        dirs = [
            self.get("paths.models_dir"),
            self.get("paths.logs_dir"),
            self.get("paths.plugins_dir"),
        ]
        for d in dirs:
            if d:
                Path(d).mkdir(parents=True, exist_ok=True)