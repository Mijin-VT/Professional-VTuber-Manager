"""Mem0 Manager Module.
Integrates the mem0 long-term memory system with a local llama-cli LLM backend.
No API keys or background servers are used; everything runs on-demand via subprocess.
"""

import os
import threading
from pathlib import Path
from typing import Any, Optional, List

from app.config_manager import ConfigManager

# Safe import to prevent crash if mem0 is not installed or broken
try:
    from mem0.llms.base import LLMBase
except Exception:
    # Dummy class to avoid NameError during definition
    class LLMBase:
        def __init__(self, config=None):
            pass


class LlamaCliLLM(LLMBase):
    """Custom LLM provider that runs llama-cli.exe on-demand for memory extraction."""

    def __init__(self, config=None, chat_mgr=None):
        super().__init__(config)
        self.chat_mgr = chat_mgr

    def _validate_config(self):
        pass

    def generate_response(self, messages: List[dict], tools=None, tool_choice="auto", **kwargs) -> str:
        """Format messages and execute local server or llama-cli.exe to extract memories."""
        if not self.chat_mgr:
            return "[]"

        # Try local server first
        response = self.chat_mgr._run_inference_server(messages, max_tokens=self.config.max_tokens or 500)
        if response is not None:
            return response

        # Fallback to CLI
        system_prompt = ""
        user_message = ""
        history_lines = []

        for msg in messages:
            role = msg.get("role")
            content = msg.get("content") or ""
            if role == "system":
                system_prompt = content
            elif role == "user":
                user_message = content
                history_lines.append(f"User: {content}")
            elif role == "assistant":
                history_lines.append(f"Assistant: {content}")

        model_path = self.chat_mgr._config.get("llama.selected_model_path", "")
        if model_path:
            model_path = str(self.chat_mgr._config.resolve_path(model_path))
        if not model_path:
            # Fallback to first .gguf in models directory
            models_dir = str(self.chat_mgr._config.resolve_path(self.chat_mgr._config.get("paths.models_dir", "./models")))
            if os.path.isdir(models_dir):
                ggufs = [f for f in os.listdir(models_dir) if f.endswith(".gguf")]
                if ggufs:
                    model_path = os.path.join(models_dir, ggufs[0])

        if model_path:
            model_path = str(self.chat_mgr._config.resolve_path(model_path))
        if not model_path or not os.path.exists(model_path):
            print("[LlamaCliLLM] No valid GGUF model path found for memory extraction.")
            return "[]"

        print(f"[LlamaCliLLM] Extracting memories in background using model: {os.path.basename(model_path)}...")
        
        # Build extra context from history (excluding the very last user message)
        extra_context = ""
        if len(history_lines) > 1:
            extra_context = "\n".join(history_lines[:-1])

        response = self.chat_mgr._run_inference_cli(
            user_message=user_message,
            model_path=model_path,
            system_prompt_override=system_prompt,
            extra_context=extra_context,
            max_tokens=self.config.max_tokens or 500
        )
        print(f"[LlamaCliLLM] Background memory extraction complete. Response size: {len(response)} chars.")
        return response


class Mem0Manager:
    """Manages the mem0 memory instance and operations."""

    def __init__(self, config: ConfigManager, chat_mgr=None):
        self._config = config
        self.chat_mgr = chat_mgr
        self._memory = None
        self.enabled = False
        self._initialize()

    def _initialize(self) -> None:
        """Initialize the mem0 instance based on configuration."""
        if not self._config.get("memory.enabled", False):
            self.enabled = False
            return

        try:
            # Safe import to prevent crash if not installed or broken
            from mem0 import Memory
        except Exception as e:
            print(f"[Mem0Manager] Failed to import mem0. Please run pip install mem0ai. Error: {e}")
            self.enabled = False
            return

        db_path = str(Path(__file__).parent.parent / "data" / "mem0_db")
        os.makedirs(db_path, exist_ok=True)

        mem0_config = {
            "vector_store": {
                "provider": "chroma",
                "config": {
                    "collection_name": "vtuber_memories",
                    "path": db_path,
                }
            },
            "embedder": {
                "provider": "huggingface",
                "config": {
                    "model": "sentence-transformers/all-MiniLM-L6-v2",
                }
            },
            "llm": {
                "provider": "openai",
                "config": {
                    "model": "openai/local-model",
                    "api_key": "dummy",
                }
            }
        }

        try:
            print("[Mem0Manager] Initializing Mem0 with local chroma/sentence-transformers...")
            self._memory = Memory.from_config(mem0_config)
            
            # Override LLM engine with custom on-demand LlamaCliLLM subclass
            if self.chat_mgr is not None:
                self._memory.llm = LlamaCliLLM(chat_mgr=self.chat_mgr)
                
            self.enabled = True
            print("[Mem0Manager] Mem0 initialized successfully (offline mode).")
        except Exception as e:
            print(f"[Mem0Manager] Failed to initialize Mem0: {e}")
            self.enabled = False

    def reload(self) -> None:
        """Reload configuration and re-initialize memory."""
        self._initialize()

    def add_memory(
        self,
        user_message: str,
        assistant_response: str,
        user_id: str = "vtuber_user",
        callback: Optional[callable] = None,
    ) -> None:
        """Add a memory exchange in the background to avoid blocking the main UI thread."""
        if not self.enabled or self._memory is None:
            if callback:
                callback(False)
            return

        def task():
            try:
                messages = [
                    {"role": "user", "content": user_message},
                    {"role": "assistant", "content": assistant_response}
                ]
                print(f"[Mem0Manager] Extracting and storing facts for user '{user_id}'...")
                self._memory.add(messages, user_id=user_id)
                print("[Mem0Manager] Facts added to memory database.")
                if callback:
                    callback(True)
            except Exception as e:
                print(f"[Mem0Manager] Error adding memory: {e}")
                if callback:
                    callback(False)

        threading.Thread(target=task, daemon=True).start()

    def search_memories(self, query: str, user_id: str = "vtuber_user") -> List[str]:
        """Search relevant memories for the given query (run synchronously before LLM call)."""
        if not self.enabled or self._memory is None:
            return []

        try:
            print(f"[Mem0Manager] Searching memories for query: '{query}'...")
            results = self._memory.search(query, filters={"user_id": user_id})
            memories = []

            items = []
            if isinstance(results, list):
                items = results
            elif isinstance(results, dict):
                items = results.get("results", [])

            for item in items:
                if isinstance(item, dict) and "memory" in item:
                    memories.append(item["memory"])
                elif isinstance(item, str):
                    memories.append(item)

            print(f"[Mem0Manager] Found {len(memories)} relevant memories.")
            return memories
        except Exception as e:
            print(f"[Mem0Manager] Error searching memories: {e}")
            return []

    def clear_memories(self, user_id: str = "vtuber_user") -> bool:
        """Clear all memories for the user."""
        if not self.enabled or self._memory is None:
            self.reload()
            if self._memory is None:
                return False

        try:
            print(f"[Mem0Manager] Clearing all memories for user '{user_id}'...")
            self._memory.delete_all(user_id=user_id)
            print("[Mem0Manager] Memory database cleared successfully.")
            return True
        except Exception as e:
            print(f"[Mem0Manager] Error clearing memories: {e}")
            return False
