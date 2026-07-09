"""Model catalog.
Defines all available GGUF models organized by VRAM category with metadata.
URLs verified against HuggingFace repositories.
"""

from dataclasses import dataclass, field
from typing import Optional


@dataclass
class ModelEntry:
    """A single model entry in the catalog."""
    id: str
    name: str
    category: str
    description: str
    size_gb: float
    quantization: str = "Q4_K_M"
    huggingface_repo: str = ""
    huggingface_filename: str = ""
    model_family: str = ""  # For Jinja2 template selection
    warning: str = ""
    recommended_vram_mb: int = 0
    total_layers: int = 0


# Model catalog organized by VRAM category
# URLs verified against HuggingFace repositories
MODEL_CATALOG: list[ModelEntry] = [
    # ─── Large Models (24GB+ VRAM) ───
    ModelEntry(
        id="command-r-35b",
        name="Command-R 35B (Writer v2 i1)",
        category="large",
        description=(
            "The undisputed king for this role. Built specifically for human "
            "interaction, strategic planning, and complex role-playing. Has a "
            "massive context window to remember your entire VTuber storyline."
        ),
        size_gb=17.0,
        quantization="Q4_K_M",
        huggingface_repo="mradermacher/command-r-35b-writer-v2-i1-GGUF",
        huggingface_filename="command-r-35b-writer-v2.i1-Q4_K_M.gguf",
        model_family="hermes",
        recommended_vram_mb=24576,
        total_layers=72,
    ),
    ModelEntry(
        id="llama-3-70b-instruct",
        name="Llama-3-70B-Instruct (Hermes-3)",
        category="large",
        description=(
            "Maximum intelligence and realism. Provides highly professional "
            "business advice, contract guidance, and community growth strategies, "
            "acting as a strict but effective manager."
        ),
        size_gb=38.0,
        quantization="Q4_K_M",
        huggingface_repo="NousResearch/Hermes-3-Llama-3.1-70B-GGUF",
        huggingface_filename="Hermes-3-Llama-3.1-70B.Q4_K_M.gguf",
        model_family="hermes",
        recommended_vram_mb=48000,
        total_layers=80,
        warning=(
            "Note: 70B models require significant system RAM in addition to "
            "VRAM. Response speed will be lower."
        ),
    ),

    # ─── Medium Models (16GB VRAM) ───
    ModelEntry(
        id="mistral-nemo-12b",
        name="Mistral-Nemo-12B-Instruct",
        category="medium",
        description=(
            "Excellent Spanish language processing. Very fast, understands "
            "internet culture and streaming, offering a perfect balance between "
            "artistic creativity and marketing advice."
        ),
        size_gb=5.5,
        quantization="Q4_K_M",
        huggingface_repo="bartowski/Mistral-Nemo-Instruct-2407-GGUF",
        huggingface_filename="Mistral-Nemo-Instruct-2407-Q4_K_M.gguf",
        model_family="mistral",
        recommended_vram_mb=16384,
        total_layers=40,
    ),
    ModelEntry(
        id="hermes-3-llama-3-8b",
        name="Hermes-3-Llama-3.1-8B",
        category="medium",
        description=(
            "A Llama-3 modification designed for advanced role-playing. Ideal "
            "if you want a manager with a strong personality, empathetic, and "
            "actively collaborative in creating lore or dynamics for your streams."
        ),
        size_gb=4.9,
        quantization="Q4_K_M",
        huggingface_repo="bartowski/Hermes-3-Llama-3.1-8B-GGUF",
        huggingface_filename="Hermes-3-Llama-3.1-8B-Q4_K_M.gguf",
        model_family="hermes",
        recommended_vram_mb=16384,
        total_layers=32,
    ),

    # ─── Light Models (4GB-6GB VRAM, 1.5B-3B params) ───
    ModelEntry(
        id="hermes-3-llama-3.2-3b",
        name="Hermes-3-Llama-3.2-3B",
        category="light",
        description=(
            "Professional-level role-playing capabilities, maintains excellent "
            "long-term coherence, and assimilates complex personalities very "
            "naturally. Perfect for GTX 1050Ti, GTX 1650, or similar."
        ),
        size_gb=2.0,
        quantization="Q4_K_M",
        huggingface_repo="bartowski/Hermes-3-Llama-3.2-3B-GGUF",
        huggingface_filename="Hermes-3-Llama-3.2-3B-Q4_K_M.gguf",
        model_family="hermes",
        recommended_vram_mb=4096,
        total_layers=28,
    ),
    ModelEntry(
        id="qwen-2.5-1.5b-instruct",
        name="Qwen-2.5-1.5B-Instruct",
        category="light",
        description=(
            "Ideal for planning your VTuber streaming schedule, proposing "
            "collaboration ideas, or drafting social media posts for Twitter/X."
        ),
        size_gb=1.3,
        quantization="Q8_0",
        huggingface_repo="bartowski/Qwen2.5-1.5B-Instruct-GGUF",
        huggingface_filename="Qwen2.5-1.5B-Instruct-Q8_0.gguf",
        model_family="qwen",
        recommended_vram_mb=4096,
        total_layers=28,
    ),
    ModelEntry(
        id="coder-1.5b",
        name="Yi-Coder-1.5B-Chat",
        category="light",
        description=(
            "Specialized in code and programming. Ideal for auto-generating "
            "scripts, technical content planning, and assisting in developing "
            "streaming tools."
        ),
        size_gb=1.3,
        quantization="Q8_0",
        huggingface_repo="bartowski/Yi-Coder-1.5B-Chat-GGUF",
        huggingface_filename="Yi-Coder-1.5B-Chat-Q8_0.gguf",
        model_family="hermes",
        recommended_vram_mb=4096,
        total_layers=28,
    ),

    # ─── Light Models 2 (6GB-12GB VRAM, 7B-8B params) ───
    ModelEntry(
        id="llama-3-stheno-v32-8b",
        name="Saiga-llama3-L3-Stheno-8B-v3.2",
        category="light2",
        description=(
            "One of the most acclaimed community versions for interactive "
            "role-playing. Designed specifically to avoid repetitive responses, "
            "capture internet slang, and react naturally to a streamer's daily "
            "conversations. For RTX 3050, 2060, 3060, 4060, or RX 6600."
        ),
        size_gb=4.9,
        quantization="Q4_K_M",
        huggingface_repo="vladlen32230/Saiga-llama3-L3-Stheno-8B-v3.2-Q4_K_M-GGUF",
        huggingface_filename="saiga-llama3-l3-stheno-8b-v3.2-q4_k_m.gguf",
        model_family="llama",
        recommended_vram_mb=8192,
        total_layers=32,
    ),
    ModelEntry(
        id="llama-3.1-8b-instruct",
        name="Meta-Llama-3.1-8B-Instruct",
        category="light2",
        description=(
            "Meta's official optimized version. Features a massive native "
            "context window (up to 128k tokens), meaning the manager will "
            "remember months of entire streams, your favorite moderators' names, "
            "and your annual goals without losing track."
        ),
        size_gb=4.9,
        quantization="Q4_K_M",
        huggingface_repo="bartowski/Meta-Llama-3.1-8B-Instruct-GGUF",
        huggingface_filename="Meta-Llama-3.1-8B-Instruct-Q4_K_M.gguf",
        model_family="llama",
        recommended_vram_mb=8192,
        total_layers=32,
    ),
]


# Category metadata for UI display
CATEGORY_INFO: dict[str, dict] = {
    "large": {
        "title": "Large Models",
        "subtitle": "For powerful PCs with 24GB+ VRAM",
        "icon": "🚀",
    },
    "medium": {
        "title": "Medium Models",
        "subtitle": "For PCs with 16GB RAM/VRAM",
        "icon": "⚡",
    },
    "light": {
        "title": "Light Models",
        "subtitle": (
            "For entry-level PCs with 4GB-6GB VRAM. "
            "For cards like the GTX 1050Ti, GTX 1650, or similar."
        ),
        "icon": "📦",
    },
    "light2": {
        "title": "Light Models 2",
        "subtitle": (
            "For mid-low range PCs with 6GB-12GB VRAM. "
            "For cards like the RTX 3050, 2060, 3060, 4060, or RX 6600."
        ),
        "icon": "💎",
    },
}

# Jinja2 chat templates per model family
CHAT_TEMPLATES: dict[str, dict] = {
    "llama": {
        "bos_token": "<|begin_of_text|>",
        "eos_token": "<|eot_id|>",
        "template_chat": (
            "<|begin_of_text|>"
            "<|start_header_id|>system<|end_header_id|>\n\n{system_prompt}<|eot_id|>"
            "{history}"
            "<|start_header_id|>user<|end_header_id|>\n\n{user_message}<|eot_id|>"
            "<|start_header_id|>assistant<|end_header_id|>\n\n"
        ),
    },
    "hermes": {
        "bos_token": "",
        "eos_token": "</s>",
        "template_chat": (
            "θsystem\n{system_prompt}θ\nθuser\n{user_message}θ\nθassistant\n"
        ),
    },
    "mistral": {
        "bos_token": "<s>",
        "eos_token": "</s>",
        "template_chat": (
            "<s>[INST] {system_prompt} [/INST]\n{user_message}"
        ),
    },
    "qwen": {
        "bos_token": "",
        "eos_token": "</θ>",
        "template_chat": (
            "θsystem\n{system_prompt}\n</θsystem>\n"
            "θuser\n{user_message}\n</θuser>\n"
            "θassistant\n"
        ),
    },
    "cohere": {
        "bos_token": "",
        "eos_token": "",
        "template_chat": (
            "<|START_OF_TURN_TOKEN|><|SYSTEM_TOKEN|>{system_prompt}"
            "<|END_OF_TURN_TOKEN|>"
            "<|START_OF_TURN_TOKEN|><|USER_TOKEN|>{user_message}"
            "<|END_OF_TURN_TOKEN|><|START_OF_TURN_TOKEN|><|CHATBOT_TOKEN|>"
        ),
    },
}


def get_models_by_category(category: str) -> list[ModelEntry]:
    """Get all models in a specific category."""
    return [m for m in MODEL_CATALOG if m.category == category]


def get_all_models() -> list[ModelEntry]:
    """Get all models."""
    return list(MODEL_CATALOG)


def get_model_by_id(model_id: str) -> Optional[ModelEntry]:
    """Get a specific model by its ID."""
    for m in MODEL_CATALOG:
        if m.id == model_id:
            return m
    return None


def get_recommended_category(vram_mb: int) -> str:
    """Get the recommended category string based on VRAM."""
    if vram_mb >= 22000:
        return "large"
    elif vram_mb >= 14000:
        return "medium"
    elif vram_mb >= 6000:
        return "light2"
    else:
        return "light"


def get_template_for_model(model_family: str) -> Optional[dict]:
    """Get the Jinja2 chat template for a model family."""
    return CHAT_TEMPLATES.get(model_family)
