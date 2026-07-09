"""Chat interface module.
Handles chat history, message formatting, and llama.cpp CLI invocation.
"""

import json
import os
import requests
import subprocess
import tempfile
import threading
from dataclasses import dataclass, field
from datetime import datetime
from pathlib import Path
from typing import Optional

from app.config_manager import ConfigManager
from app.model_catalog import get_template_for_model, get_model_by_id, MODEL_CATALOG
from app.mem0_manager import Mem0Manager


@dataclass
class ChatMessage:
    """A single chat message."""
    role: str  # "user", "assistant", "system"
    content: str
    timestamp: str = field(default_factory=lambda: datetime.now().isoformat())


@dataclass
class ChatSession:
    """A chat session with history."""
    id: str
    title: str = "New Chat"
    messages: list[ChatMessage] = field(default_factory=list)
    model_id: str = ""
    created_at: str = field(default_factory=lambda: datetime.now().isoformat())


class ChatManager:
    """Manages chat sessions and communicates with llama.cpp."""

    def __init__(self, config: ConfigManager):
        self._config = config
        self.mem0_mgr = Mem0Manager(config, chat_mgr=self)
        
        from app.web_search_manager import WebSearchManager
        self.search_mgr = WebSearchManager(config)
        
        self._sessions: dict[str, ChatSession] = {}
        self._current_session_id: Optional[str] = None
        self._sessions_dir = Path(__file__).parent.parent / "data" / "chats"
        self._sessions_dir.mkdir(parents=True, exist_ok=True)
        self._load_sessions()

        # Server variables
        self.server_process = None
        self.server_port = 8080
        self.server_model_path = ""
        self._stream_api = None
        self._task_mgr = None

    def set_task_mgr(self, task_mgr):
        """Asigna la referencia al administrador de tareas activo."""
        self._task_mgr = task_mgr

    def set_stream_api(self, stream_api):
        """Asigna la referencia al administrador de streaming activo."""
        self._stream_api = stream_api

        # Eagerly start server in a background thread if model path exists
        model_path = self._config.get("llama.selected_model_path", "")
        if model_path and os.path.exists(model_path):
            threading.Thread(target=self.start_server, args=(model_path,), daemon=True).start()

    def start_server(self, model_path: str):
        """Start llama-server.exe with the specified model."""
        if model_path:
            model_path = str(self._config.resolve_path(model_path))
        if not model_path or not os.path.exists(model_path):
            print(f"[ChatManager] Cannot start server: model path '{model_path}' does not exist.")
            return False

        # If already running with the same model, do nothing
        if self.server_process and self.server_model_path == model_path:
            if self.server_process.poll() is None:
                return True

        # Stop existing server first
        self.stop_server()

        # Resolve paths
        bin_dir = self._config.get("paths.bin_dir", "./bin")
        server_exec = self._config.get("llama.server_executable", "llama-server.exe")
        project_dir = Path(__file__).parent.parent
        server_path = str((project_dir / bin_dir / server_exec).resolve())
        model_abs = str(Path(model_path).resolve())

        if not os.path.isfile(server_path):
            print(f"[ChatManager] Server executable not found at: {server_path}")
            return False

        # Get server parameters
        ctx_size = self._config.get("llama.default_ctx_size", 4096)
        
        # Determine n_gpu_layers
        model_entry = None
        model_filename = os.path.basename(model_path).lower()
        for m in MODEL_CATALOG:
            if m.huggingface_filename.lower() in model_filename or \
               model_filename in m.huggingface_filename.lower():
                model_entry = m
                break
        n_gpu = 40  # Default
        if model_entry and model_entry.total_layers > 0:
            n_gpu = model_entry.total_layers

        cmd = [
            server_path,
            "-m", model_abs,
            "-c", str(ctx_size),
            "-ngl", str(n_gpu),
            "--host", "127.0.0.1",
            "--port", str(self.server_port),
            "--log-disable"
        ]

        print(f"[ChatManager] Starting local server: {' '.join(cmd)}")
        try:
            self.server_process = subprocess.Popen(
                cmd,
                stdout=subprocess.DEVNULL,
                stderr=subprocess.DEVNULL,
                cwd=str(project_dir),
                creationflags=subprocess.CREATE_NO_WINDOW if os.name == 'nt' else 0,
            )
            self.server_model_path = model_path
            
            # Wait for server to become ready
            import time
            start_time = time.time()
            while time.time() - start_time < 12:
                if self.server_process.poll() is not None:
                    print("[ChatManager] Server process exited unexpectedly during startup.")
                    self.server_process = None
                    self.server_model_path = ""
                    return False
                try:
                    r = requests.get(f"http://127.0.0.1:{self.server_port}/health", timeout=1)
                    if r.status_code == 200:
                        print(f"[ChatManager] Local server started successfully on port {self.server_port}!")
                        return True
                except requests.RequestException:
                    pass
                time.sleep(0.5)
            
            print("[ChatManager] Server startup timed out.")
            return False
        except Exception as e:
            print(f"[ChatManager] Failed to start server process: {e}")
            self.server_process = None
            self.server_model_path = ""
            return False

    def stop_server(self):
        """Stop the running llama-server.exe process and clean up zombie port bindings."""
        if self.server_process:
            print("[ChatManager] Stopping local server...")
            try:
                self.server_process.terminate()
                self.server_process.wait(timeout=5)
            except subprocess.TimeoutExpired:
                try:
                    self.server_process.kill()
                except Exception:
                    pass
            except Exception:
                pass
            self.server_process = None
            self.server_model_path = ""
            print("[ChatManager] Local server stopped.")

        # Clean up any other processes bound to port 8080 (zombies)
        try:
            cmd = f"netstat -ano | findstr :{self.server_port}"
            out = subprocess.check_output(cmd, shell=True).decode("utf-8", errors="ignore")
            pids = set()
            for line in out.splitlines():
                if "LISTENING" in line:
                    parts = line.strip().split()
                    if len(parts) >= 5:
                        pids.add(parts[-1])
            for pid in pids:
                try:
                    pid_int = int(pid)
                    if pid_int > 0:
                        print(f"[ChatManager] Killing zombie process {pid_int} occupying port {self.server_port}...")
                        subprocess.run(f"taskkill /F /PID {pid_int}", shell=True, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
                except Exception:
                    pass
        except Exception:
            pass

    def sanitize_messages(self, messages: list[dict]) -> list[dict]:
        """Sanitize messages list to satisfy strict Jinja template alternation rules."""
        if not messages:
            return []

        sanitized = []
        system_contents = []

        for msg in messages:
            role = msg.get("role")
            content = msg.get("content") or ""
            if role == "system" and content:
                system_contents.append(content)

        if system_contents:
            sanitized.append({"role": "system", "content": "\n\n".join(system_contents)})

        for msg in messages:
            role = msg.get("role")
            if role == "system":
                continue
            content = msg.get("content") or ""
            if not content:
                continue

            if sanitized and sanitized[-1]["role"] == role:
                sanitized[-1]["content"] += "\n" + content
            else:
                sanitized.append({"role": role, "content": content})

        final_messages = []
        start_idx = 0
        if sanitized and sanitized[0]["role"] == "system":
            final_messages.append(sanitized[0])
            start_idx = 1

        expected_role = "user"
        for msg in sanitized[start_idx:]:
            if msg["role"] == expected_role:
                final_messages.append(msg)
                expected_role = "assistant" if expected_role == "user" else "user"
            else:
                if final_messages and final_messages[-1]["role"] == msg["role"]:
                    final_messages[-1]["content"] += "\n" + msg["content"]
                else:
                    msg["role"] = "user"
                    final_messages.append(msg)
                    expected_role = "assistant"

        return final_messages

    def _run_inference_server(self, messages: list[dict], max_tokens: int = 512, on_token_callback: Optional[callable] = None) -> Optional[str]:
        """Send a completions request to local server, starting it if not running."""
        model_path = self._config.get("llama.selected_model_path", "")
        if not self.server_process or self.server_model_path != model_path:
            success = self.start_server(model_path)
            if not success:
                return None

        url = f"http://127.0.0.1:{self.server_port}/v1/chat/completions"
        temp = self._config.get("llama.default_temp", 0.7)
        top_p = self._config.get("llama.default_top_p", 0.9)
        sanitized = self.sanitize_messages(messages)

        stream_enabled = on_token_callback is not None
        payload = {
            "messages": sanitized,
            "temperature": temp,
            "top_p": top_p,
            "max_tokens": max_tokens,
            "stream": stream_enabled
        }

        try:
            if stream_enabled:
                r = requests.post(url, json=payload, stream=True, timeout=300)
                if r.status_code == 200:
                    response_chunks = []
                    for line in r.iter_lines():
                        if line:
                            decoded_line = line.decode('utf-8').strip()
                            if decoded_line.startswith("data:"):
                                data_str = decoded_line[5:].strip()
                                if data_str == "[DONE]":
                                    break
                                try:
                                    chunk_json = json.loads(data_str)
                                    token = chunk_json["choices"][0]["delta"].get("content", "")
                                    if token:
                                        response_chunks.append(token)
                                        on_token_callback(token)
                                except Exception:
                                    pass
                    return "".join(response_chunks)
                else:
                    print(f"[ChatManager] Server error {r.status_code}: {r.text}")
                    return None
            else:
                r = requests.post(url, json=payload, timeout=300)
                if r.status_code == 200:
                    result = r.json()
                    return result["choices"][0]["message"]["content"]
                else:
                    print(f"[ChatManager] Server error {r.status_code}: {r.text}")
                    return None
        except Exception as e:
            print(f"[ChatManager] Server request failed: {e}")
            return None

    @property
    def current_session(self) -> Optional[ChatSession]:
        """Get the currently active chat session."""
        if self._current_session_id:
            return self._sessions.get(self._current_session_id)
        return None

    def create_session(self, title: str = "New Chat", model_id: str = "") -> ChatSession:
        """Create a new chat session."""
        session_id = datetime.now().strftime("%Y%m%d_%H%M%S")
        session = ChatSession(
            id=session_id,
            title=title,
            model_id=model_id,
        )
        self._sessions[session_id] = session
        self._current_session_id = session_id
        self._save_sessions()
        return session

    def get_session(self, session_id: str) -> Optional[ChatSession]:
        """Get a session by ID."""
        return self._sessions.get(session_id)

    def list_sessions(self) -> list[ChatSession]:
        """List all chat sessions."""
        return list(self._sessions.values())

    def switch_session(self, session_id: str) -> bool:
        """Switch to a different session."""
        if session_id in self._sessions:
            self._current_session_id = session_id
            return True
        return False

    def delete_session(self, session_id: str) -> bool:
        """Delete a session."""
        if session_id in self._sessions:
            del self._sessions[session_id]
            if self._current_session_id == session_id:
                self._current_session_id = None
            self._save_sessions()
            return True
        return False

    def add_message(self, role: str, content: str) -> ChatMessage:
        """Add a message to the current session."""
        session = self.current_session
        if not session:
            return ChatMessage(role=role, content=content)
        msg = ChatMessage(role=role, content=content)
        session.messages.append(msg)
        self._save_sessions()
        return msg

    def send_message(
        self,
        user_message: str,
        model_path: str,
        callback: Optional[callable] = None,
        on_token_callback: Optional[callable] = None,
    ) -> str:
        """Send a message to the model in the current chat session."""
        session = self.current_session
        if not session:
            session = self.create_session(title="Chat 1")

        # Add the user message to history
        self.add_message("user", user_message)

        # Get system prompt
        system_prompt = self._config.get("chat.system_prompt", "")

        # Inject instruction for autonomous task management
        task_instruction = (
            "\n\n[SYSTEM: TASK AUTOMATION]\n"
            "You have the capability to manage the streamer's To-Do list autonomously.\n"
            "If the streamer asks you to remember something, schedule a collaboration, create a task, or if you strategically suggest a task for their channel, you must inject a command tag at the end of your message in the exact format:\n"
            "`[ADD_TASK: Task description | priority]`\n"
            "Where 'priority' must be high, medium, or low.\n"
            "Examples:\n"
            "- If they ask to remember a collaboration: `[ADD_TASK: Collaboration with Valeria tomorrow at 5:00 PM | high]`\n"
            "- If you suggest editing clips: `[ADD_TASK: Cut and edit 3 clips from the last stream | medium]`\n"
            "You can inject multiple tasks at the end of your response (one per line) if necessary. Do not use this format for general discussion; only use it for actual tasks to be saved in their list."
        )
        system_prompt += task_instruction

        # Inject instruction for Emotional Intelligence
        emotion_instruction = (
            "\n\n[SYSTEM: EMOTIONAL INTELLIGENCE]\n"
            "You MUST start your response with an emotion tag that reflects your current emotional state regarding the conversation.\n"
            "The tag must have exactly this format: `[EMOCION: <emotion>]` at the very beginning of your message (before any other word).\n"
            "Choose '<emotion>' strictly from the following Spanish options in lowercase:\n"
            "- `feliz` (cheerful, excited, motivating)\n"
            "- `divertida` (playful, joking, funny)\n"
            "- `triste` (empathizing with problems, sorry, melancholic)\n"
            "- `enojada` (frustrated, demanding, annoyed with streamer's bad habits)\n"
            "- `sorprendida` (astonished, shocked by news)\n"
            "- `seria` (neutral, professional, direct)\n"
            "Example format:\n"
            "`[EMOCION: feliz] I think that's a fantastic goal for this week! Let's do it.`\n"
            "Never forget to start with this tag, as it is critical for the voice modulator system."
        )
        system_prompt += emotion_instruction

        # Buscar información sobre crecimiento de VTubers si el usuario lo solicita
        try:
            search_context = self.search_mgr.search_vtuber_growth(user_message)
            if search_context:
                system_prompt += search_context
        except Exception as e:
            print(f"[ChatManager] Web search execution failed: {e}")

        # Inject live streaming context if the user asks about it
        if self._stream_api and (self._stream_api.twitch_enabled or self._stream_api.kick_enabled or self._stream_api.obs_enabled):
            keywords = ["directo", "streaming", "obs", "espectadores", "viewers", "transmisión", "stream", "canal", "live", "scene"]
            if any(k in user_message.lower() for k in keywords):
                try:
                    metrics = self._stream_api.get_live_metrics()
                    status_str = "LIVE 🔴" if metrics["is_live"] else "OFFLINE 💤"
                    stream_context = (
                        f"\n\n[Current Live Stream Context for your analysis]\n"
                        f"- Current status: {status_str}\n"
                        f"- Current viewers: {metrics['total_viewers']} (Twitch: {metrics['twitch_viewers']}, Kick: {metrics['kick_viewers']})\n"
                        f"- Chat speed: {metrics['chat_rate']} messages per minute\n"
                        f"- Active OBS scene: '{metrics['obs_scene']}'\n"
                        f"- OBS connected: {'Yes' if metrics['obs_connected'] else 'No'}\n"
                        f"Use these real-time metrics if the user asks about the stream status or asks for streaming advice."
                    )
                    system_prompt += stream_context
                except Exception as e:
                    print(f"[ChatManager] Failed to inject stream metrics: {e}")

        # 1. Retrieve memories from Mem0
        if self.mem0_mgr.enabled:
            try:
                memories = self.mem0_mgr.search_memories(user_message, user_id="vtuber_user")
                if memories:
                    memory_context = "\n".join([f"- {m}" for m in memories])
                    system_prompt = system_prompt + f"\n\n[Relevant information in your memory about the user]\n{memory_context}"
            except Exception as e:
                print(f"[ChatManager] Mem0 search failed: {e}")

        # Inyectar regla crítica de idioma al final del prompt del sistema para máxima prioridad
        language_rule = (
            "\n\n[REGLA DE IDIOMA CRÍTICA / CRITICAL LANGUAGE RULE]\n"
            "- If the user writes or speaks to you in Japanese, you MUST respond entirely in Japanese (日本語で返答してください。絶対に英語やスペイン語で返答しないでください。).\n"
            "- Si el usuario te escribe o habla en español, debes responder completamente en español. No respondas en inglés ni en japonés.\n"
            "- If the user writes or speaks to you in English, you must respond entirely in English. Do not respond in Spanish or Japanese.\n"
            "- ALWAYS reply in the exact same language as the user's last message. This is an absolute requirement."
        )
        system_prompt += language_rule

        # Try server first
        response_text = None
        server_messages = []
        if system_prompt:
            server_messages.append({"role": "system", "content": system_prompt})
        for m in session.messages:
            server_messages.append({"role": m.role, "content": m.content})

        response_text = self._run_inference_server(server_messages, on_token_callback=on_token_callback)

        if response_text is None:
            print("[ChatManager] Server response unavailable. Falling back to llama-cli.exe...")
            # 2. Run inference via llama-cli.exe (fallback)
            history_messages = session.messages[:-1]
            history_lines = []
            for m in history_messages[-6:]:
                if m.role == "user":
                    history_lines.append(f"User: {m.content}")
                elif m.role == "assistant":
                    history_lines.append(f"Assistant: {m.content}")
            extra_context = "\n".join(history_lines) if history_lines else ""

            response_text = self._run_inference_cli(
                user_message=user_message,
                model_path=model_path,
                system_prompt_override=system_prompt,
                extra_context=extra_context,
            )

        # Save assistant response to session
        if response_text and not response_text.startswith("✗"):
            # Parse [ADD_TASK: title | priority] tags
            import re
            task_tags = re.findall(r'\[ADD_TASK:\s*(.*?)\s*\|\s*(high|medium|low)\s*\]', response_text, re.IGNORECASE)
            added_any = False
            for title, priority in task_tags:
                if self._task_mgr:
                    self._task_mgr.add_task(title.strip(), priority.lower().strip())
                    print(f"[ChatManager] Auto-added task from AI: {title} ({priority})")
                    added_any = True
            
            # Clean response_text to remove the command tags
            response_clean = re.sub(r'\[ADD_TASK:\s*.*?\s*\|\s*(high|medium|low)\s*\]', '', response_text).strip()
            if response_clean:
                response_text = response_clean

            # Append task confirmation if any were added
            if added_any:
                response_text += "\n\n(La tarea fue agregada con éxito)"

            self.add_message("assistant", response_text)
            
            # 3. Save memories to Mem0 in background
            if self.mem0_mgr.enabled:
                try:
                    self.mem0_mgr.add_memory(user_message, response_text, user_id="vtuber_user")
                except Exception as e:
                    print(f"[ChatManager] Mem0 add failed: {e}")

        if callback and response_text:
            callback(response_text)

        return response_text if response_text else "✗ No response received from model."

    def generate(
        self,
        prompt: str,
        model_path: str,
        max_tokens: int = 512,
        system_prompt: str = "",
    ) -> str:
        """Run a one-shot inference using local server if available, else llama-cli.exe."""
        server_messages = []
        if system_prompt:
            server_messages.append({"role": "system", "content": system_prompt})
        server_messages.append({"role": "user", "content": prompt})

        response_text = self._run_inference_server(server_messages, max_tokens=max_tokens)
        if response_text is not None:
            return response_text

        print("[ChatManager] generate: Falling back to llama-cli.exe...")
        return self._run_inference_cli(
            user_message=prompt,
            model_path=model_path,
            system_prompt_override=system_prompt,
            extra_context="",
            max_tokens=max_tokens,
        )



    def _run_inference_cli(
        self,
        user_message: str,
        model_path: str,
        system_prompt_override: Optional[str] = None,
        extra_context: str = "",
        max_tokens: int = 512,
    ) -> str:
        """Run a single llama-cli inference and return the parsed response."""
        # Get configuration values
        ctx_size = self._config.get("llama.default_ctx_size", 4096)
        temp = self._config.get("llama.default_temp", 0.7)
        top_p = self._config.get("llama.default_top_p", 0.9)
        repeat_penalty = self._config.get("llama.default_repeat_penalty", 1.1)
        bin_dir = self._config.get("paths.bin_dir", "./bin")
        cli_exec = self._config.get("llama.cli_executable", "llama-cli.exe")
        if system_prompt_override is None:
            system_prompt = self._config.get("chat.system_prompt", "")
        else:
            system_prompt = system_prompt_override

        # Determine model entry for GPU layers
        model_entry = None
        session = self.current_session
        if session and session.model_id:
            model_entry = get_model_by_id(session.model_id)
        if not model_entry and model_path:
            model_filename = os.path.basename(model_path).lower()
            for m in MODEL_CATALOG:
                if m.huggingface_filename.lower() in model_filename or \
                   model_filename in m.huggingface_filename.lower():
                    model_entry = m
                    break

        # Compute n_gpu_layers
        n_gpu = 40  # Default for Mistral-Nemo-12B
        if model_entry and model_entry.total_layers > 0:
            n_gpu = model_entry.total_layers

        # Resolve paths
        project_dir = Path(__file__).parent.parent
        model_abs = str(self._config.resolve_path(model_path))
        cli_path = str((project_dir / bin_dir / cli_exec).resolve())

        if not os.path.isfile(cli_path):
            return f"✗ llama-cli not found at: {cli_path}"
        if not os.path.isfile(model_abs):
            return f"✗ Model file not found at: {model_abs}"

        # Append optional conversation context to the system prompt
        if extra_context:
            system_prompt = system_prompt + f"\n\n[Previous conversation context]\n{extra_context}"

        # Write system prompt to a temp file to avoid command-line length limits
        sys_prompt_path = None
        try:
            sys_prompt_file = tempfile.NamedTemporaryFile(
                mode='w', suffix='.txt', delete=False,
                encoding='utf-8', dir=str(project_dir)
            )
            sys_prompt_file.write(system_prompt)
            sys_prompt_file.close()
            sys_prompt_path = sys_prompt_file.name
        except Exception:
            sys_prompt_path = None

        # Build command using -cnv --single-turn mode
        cmd = [
            cli_path,
            "-m", model_abs,
            "-c", str(ctx_size),
            "--temp", str(temp),
            "--top-p", str(top_p),
            "--repeat-penalty", str(repeat_penalty),
            "-n", str(max_tokens),
            "-ngl", str(n_gpu),
            "--no-mmap",
            "--no-warmup",
            "--no-display-prompt",
            "-cnv",
            "--single-turn",
        ]

        # Add system prompt via file (-sysf) or inline (-sys)
        if sys_prompt_path:
            cmd.extend(["-sysf", sys_prompt_path])
        elif system_prompt:
            # Truncate if too long for command line
            short_prompt = system_prompt[:500] if len(system_prompt) > 500 else system_prompt
            cmd.extend(["-sys", short_prompt])

        # Run the command — pipe user message via stdin
        response_text = ""
        error_text = None

        try:
            proc = subprocess.run(
                cmd,
                input=user_message + "\n",
                capture_output=True,
                text=True,
                timeout=300,
                encoding="utf-8",
                errors="replace",
                cwd=str(project_dir),
                creationflags=subprocess.CREATE_NO_WINDOW if os.name == 'nt' else 0,
            )

            if proc.returncode == 0:
                response_text = self._parse_response(proc.stdout)
            else:
                error_text = proc.stderr.strip() if proc.stderr else f"Exit code {proc.returncode}"
                # Sometimes stderr has useful info even on success
                if not response_text and proc.stdout:
                    response_text = self._parse_response(proc.stdout)
                if response_text:
                    error_text = None  # Got a response, ignore error code

        except subprocess.TimeoutExpired:
            error_text = "Response timed out (300s). The model may be too large for your GPU."
        except FileNotFoundError as e:
            error_text = f"Executable not found: {str(e)}"
        except Exception as e:
            error_text = f"Error: {str(e)}"
        finally:
            # Clean up temp file
            if sys_prompt_path:
                try:
                    os.unlink(sys_prompt_path)
                except Exception:
                    pass

        if error_text and not response_text:
            return f"✗ {error_text}"

        return response_text if response_text else "✗ No response received from model."

    def _parse_response(self, output: str) -> str:
        """Parse llama-cli output to extract the assistant response.

        With --no-display-prompt and -cnv --single-turn, the output should be
        relatively clean. We need to strip:
        - Model loading info / ASCII art logo
        - The "> " prompt marker
        - Performance stats line [ Prompt: ... | Generation: ... ]
        - "Exiting..." line
        """
        if not output:
            return ""

        lines = output.split("\n")
        response_lines = []
        in_response = False

        for line in lines:
            stripped = line.strip()

            # Skip empty lines at the start
            if not in_response and not stripped:
                continue

            # Skip model loading and logo lines
            if stripped.startswith("Loading model"):
                continue
            if stripped.startswith("build") and ":" in stripped:
                continue
            if stripped.startswith("model") and ":" in stripped:
                continue
            if stripped.startswith("modalities"):
                continue
            if stripped.startswith("using custom"):
                continue
            if stripped.startswith("available commands:"):
                continue
            if stripped.startswith("/exit") or stripped.startswith("/regen") or \
               stripped.startswith("/clear") or stripped.startswith("/read") or \
               stripped.startswith("/glob"):
                continue

            # Skip ASCII art (contains box-drawing characters)
            if any(c in stripped for c in "╔╗╚╝║═█▀▄▐▌▓░▒"):
                continue
            # Also skip garbled ASCII art (CP437 encoding issues)
            if "Γû" in stripped:
                continue

            # Skip prompt marker
            if stripped == ">" or stripped == "> ":
                in_response = True
                continue
            if stripped.startswith("> "):
                in_response = True
                continue

            # Skip performance stats
            if stripped.startswith("[ Prompt:") or stripped.startswith("[Prompt:"):
                continue

            # Skip exit message
            if stripped == "Exiting...":
                continue

            # If we've passed the header, collect response lines
            if in_response and stripped:
                response_lines.append(stripped)
            elif not in_response and stripped and not any(
                stripped.startswith(x) for x in ["Loading", "build", "model", "modalities"]
            ):
                # Sometimes response comes without clear ">" marker
                # Check if it looks like actual content
                if len(stripped) > 2 and not stripped.startswith("["):
                    in_response = True
                    response_lines.append(stripped)

        result = "\n".join(response_lines).strip()

        # If we still got nothing, try a simpler approach
        if not result:
            # Find content between ">" and "[ Prompt:" or "Exiting..."
            full_text = output
            # Remove everything before the last ">"
            if ">" in full_text:
                idx = full_text.rfind(">")
                full_text = full_text[idx + 1:]
            # Remove stats and exit
            if "[ Prompt:" in full_text:
                full_text = full_text[:full_text.rfind("[ Prompt:")]
            if "Exiting..." in full_text:
                full_text = full_text[:full_text.rfind("Exiting...")]
            result = full_text.strip()

        return result

    def _save_sessions(self) -> None:
        """Save all sessions to JSON."""
        data = {}
        for sid, session in self._sessions.items():
            data[sid] = {
                "id": session.id,
                "title": session.title,
                "model_id": session.model_id,
                "created_at": session.created_at,
                "messages": [
                    {"role": m.role, "content": m.content, "timestamp": m.timestamp}
                    for m in session.messages
                ],
            }
        path = self._sessions_dir / "sessions.json"
        try:
            with open(path, "w", encoding="utf-8") as f:
                json.dump(data, f, indent=2, ensure_ascii=False)
        except (IOError, OSError) as e:
            print(f"[ChatManager] Failed to save sessions: {e}")

    def _load_sessions(self) -> None:
        """Load sessions from JSON."""
        path = self._sessions_dir / "sessions.json"
        if not path.exists():
            return
        try:
            with open(path, "r", encoding="utf-8") as f:
                data = json.load(f)
            for sid, sdata in data.items():
                messages = [
                    ChatMessage(
                        role=m["role"],
                        content=m["content"],
                        timestamp=m.get("timestamp", ""),
                    )
                    for m in sdata.get("messages", [])
                ]
                session = ChatSession(
                    id=sdata["id"],
                    title=sdata.get("title", "Chat"),
                    model_id=sdata.get("model_id", ""),
                    created_at=sdata.get("created_at", ""),
                    messages=messages,
                )
                self._sessions[sid] = session
            if self._sessions:
                self._current_session_id = max(
                    self._sessions,
                    key=lambda k: self._sessions[k].created_at,
                )
        except (json.JSONDecodeError, IOError):
            pass
