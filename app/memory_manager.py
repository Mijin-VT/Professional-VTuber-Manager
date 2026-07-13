import os
import json
import logging
import threading
import requests

logger = logging.getLogger("MemoryManager")

class MemoryManager:
    """A lightweight JSON-based long-term memory system inspired by LILY-VIRTUAL-2.0."""
    def __init__(self, config_dir: str = "config"):
        self.config_dir = config_dir
        self.memory_path = os.path.join(config_dir, "astra_memory.json")
        self.facts = self.load_memory()

    def load_memory(self):
        if os.path.exists(self.memory_path):
            try:
                with open(self.memory_path, "r", encoding="utf-8") as f:
                    return json.load(f)
            except Exception as e:
                logger.error("Failed to load long-term memory: %s", e)
        return []

    def save_memory(self):
        try:
            os.makedirs(self.config_dir, exist_ok=True)
            with open(self.memory_path, "w", encoding="utf-8") as f:
                json.dump(self.facts, f, ensure_ascii=False, indent=4)
        except Exception as e:
            logger.error("Failed to save memory: %s", e)

    def get_memory_prompt_suffix(self) -> str:
        if not self.facts:
            return ""
        facts_str = "\n".join(f"- {f}" for f in self.facts)
        return f"\n\n### MEMORIA DE LARGO PLAZO (Datos importantes que recuerdas sobre el streamer):\n{facts_str}"

    def update_memory_async(self, conversation_text: str, model_port: int = 8080):
        """Spawns a background thread to reflect on conversation and update memory."""
        thread = threading.Thread(
            target=self._update_memory_worker,
            args=(conversation_text, model_port),
            daemon=True
        )
        thread.start()

    def _update_memory_worker(self, conversation_text: str, model_port: int):
        try:
            url = f"http://127.0.0.1:{model_port}/v1/chat/completions"
            
            existing_facts = "\n".join(f"- {f}" for f in self.facts) if self.facts else "Ninguno todavía."
            
            messages = [
                {
                    "role": "system",
                    "content": (
                        "Eres un asistente extractor de información personal. Tu única tarea es extraer datos "
                        "clave del streamer (como su nombre, apodo, temas que le gustan, metas de canal, lore de personaje, "
                        "redes sociales, problemas de los que te habló) a partir de la nueva conversación proporcionada.\n"
                        "Reglas:\n"
                        "1. Responde únicamente con una lista de viñetas claras (iniciando con '- ').\n"
                        "2. Integra los hechos antiguos con los nuevos si es necesario.\n"
                        "3. Sé extremadamente conciso. Máximo 10 viñetas en total.\n"
                        "4. Responde en español.\n"
                        "5. Si no hay datos nuevos importantes, responde exactamente con la lista antigua."
                    )
                },
                {
                    "role": "user",
                    "content": (
                        f"### LISTA DE HECHOS ACTUALES QUE RECUERDAS:\n{existing_facts}\n\n"
                        f"### NUEVA CONVERSACIÓN:\n{conversation_text}\n\n"
                        "Extrae y actualiza la lista de hechos:"
                    )
                }
            ]
            
            headers = {"Content-Type": "application/json"}
            payload = {
                "messages": messages,
                "temperature": 0.0,
                "max_tokens": 300,
            }
            
            response = requests.post(url, json=payload, headers=headers, timeout=12)
            if response.status_code == 200:
                result = response.json()
                reply = result["choices"][0]["message"]["content"].strip()
                
                # Parse bullet points
                new_facts = []
                for line in reply.split("\n"):
                    line_clean = line.strip()
                    if line_clean.startswith("-") or line_clean.startswith("*"):
                        fact = line_clean[1:].strip()
                        if fact:
                            new_facts.append(fact)
                            
                if new_facts and new_facts != self.facts:
                    self.facts = new_facts
                    self.save_memory()
                    print(f"[MemoryManager] Memory updated: {self.facts}")
        except Exception as e:
            # Fail silently to avoid interrupting the main app if server isn't responsive
            pass
