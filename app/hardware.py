"""Hardware detection module.
Detects VRAM, CUDA availability, and system resources to guide model selection.
"""

import subprocess
import psutil
import platform
from dataclasses import dataclass, field
from typing import Optional


@dataclass
class HardwareInfo:
    """Collected hardware information."""
    vram_total_mb: int = 0
    vram_available_mb: int = 0
    ram_total_mb: int = 0
    ram_available_mb: int = 0
    cuda_available: bool = False
    gpu_name: str = ""
    gpu_driver_version: str = ""
    os_name: str = ""
    os_arch: str = ""
    recommended_category: str = ""
    gpu_layers_for_model: dict = field(default_factory=dict)


def detect_hardware() -> HardwareInfo:
    """Detect all relevant hardware information."""
    info = HardwareInfo()
    info.os_name = platform.system()
    info.os_arch = platform.machine()

    _detect_gpu(info)
    _detect_ram(info)
    _detect_cuda(info)
    _recommend_category(info)
    _compute_gpu_layers(info)

    return info


def _detect_gpu(info: HardwareInfo) -> None:
    """Detect GPU information using multiple methods."""
    # Try nvidia-smi first (Windows + Linux)
    try:
        if info.os_name == "Windows":
            result = subprocess.run(
                ["nvidia-smi", "--query-gpu=name,memory.total,memory.free,driver_version",
                 "--format=csv,noheader,nounits"],
                capture_output=True, text=True, timeout=5
            )
            if result.returncode == 0 and result.stdout.strip():
                line = result.stdout.strip().split("\n")[0]
                parts = [p.strip() for p in line.split(",")]
                if len(parts) >= 4:
                    info.gpu_name = parts[0]
                    info.vram_total_mb = int(float(parts[1]))
                    info.vram_available_mb = int(float(parts[2]))
                    info.gpu_driver_version = parts[3]
                    return
    except (FileNotFoundError, subprocess.TimeoutExpired, ValueError):
        pass

    # Try PowerShell on Windows
    try:
        result = subprocess.run(
            ["powershell", "-Command",
             "(Get-CimInstance Win32_VideoController).Name"],
            capture_output=True, text=True, timeout=5
        )
        if result.returncode == 0 and result.stdout.strip():
            info.gpu_name = result.stdout.strip()
            # AdapterRAM is in bytes; 0 means integrated/no dedicated VRAM
            result2 = subprocess.run(
                ["powershell", "-Command",
                 "(Get-CimInstance Win32_VideoController).AdapterRAM"],
                capture_output=True, text=True, timeout=5
            )
            if result2.returncode == 0:
                adapter_bytes = int(result2.stdout.strip())
                if adapter_bytes > 0:
                    info.vram_total_mb = adapter_bytes // (1024 * 1024)
    except (FileNotFoundError, subprocess.TimeoutExpired, ValueError):
        pass

    # Try lshw on Linux
    try:
        result = subprocess.run(
            ["lshw", "-C", "display", "-json"],
            capture_output=True, text=True, timeout=5
        )
        if result.returncode == 0:
            import json
            data = json.loads(result.stdout)
            if data and len(data) > 0:
                gpu = data[0]
                info.gpu_name = gpu.get("description", "")
    except (FileNotFoundError, subprocess.TimeoutExpired, json.JSONDecodeError):
        pass


def _detect_ram(info: HardwareInfo) -> None:
    """Detect system RAM using psutil."""
    mem = psutil.virtual_memory()
    info.ram_total_mb = mem.total // (1024 * 1024)
    info.ram_available_mb = mem.available // (1024 * 1024)


def _detect_cuda(info: HardwareInfo) -> None:
    """Detect CUDA availability."""
    try:
        # Try python cuda check
        import torch
        info.cuda_available = torch.cuda.is_available()
    except ImportError:
        pass

    # Fallback: check for CUDA DLLs in bin directory
    if not info.cuda_available:
        import os
        bin_dir = os.path.join(os.path.dirname(__file__), "..", "bin")
        bin_dir = os.path.normpath(bin_dir)
        cuda_dlls = ["ggml-cuda.dll", "cublas64_13.dll", "cudart64_13.dll"]
        info.cuda_available = all(
            os.path.isfile(os.path.join(bin_dir, dll))
            for dll in cuda_dlls
        )


def _recommend_category(info: HardwareInfo) -> None:
    """Recommend model category based on VRAM."""
    vram = info.vram_total_mb

    if vram >= 22000:  # 22GB+
        info.recommended_category = "large"
    elif vram >= 14000:  # 14GB+
        info.recommended_category = "medium"
    elif vram >= 6000:  # 6GB+
        info.recommended_category = "lightweight2"
    elif vram >= 4000:  # 4GB+
        info.recommended_category = "lightweight"
    else:
        info.recommended_category = "lightweight"  # default to smallest models


def _compute_gpu_layers(info: HardwareInfo) -> None:
    """Precompute GPU layer counts for known model sizes."""
    model_sizes = {
        "1.5b": 1.0, "3b": 2.0, "8b": 4.9, "12b": 7.0,
        "35b": 19.0, "70b": 39.0,
    }
    for name, size_gb in model_sizes.items():
        info.gpu_layers_for_model[name] = compute_gpu_layers_for_model(
            info.vram_total_mb, size_gb
        )


def compute_gpu_layers_for_model(
    vram_mb: int, model_size_gb: float, ctx_size: int = 4096
) -> int:
    """Compute optimal n_gpu_layers based on available VRAM and model size.

    Rules:
    - 8GB or less: leave 1GB safety margin, load what fits
    - 12GB+: aggressive, try to load entire model
    - 24GB+: load everything
    """
    if vram_mb <= 0:
        return 0

    # Estimate total memory needed (model + context overhead)
    model_mem_mb = model_size_gb * 1024
    context_overhead_mb = ctx_size * 2  # rough estimate per layer

    # Available VRAM for the model
    if vram_mb >= 12288:  # 12GB+
        # Aggressive: use all VRAM minus small OS margin
        available = vram_mb - 512  # 512MB OS margin
    elif vram_mb >= 8192:  # 8GB+
        # Conservative: leave 1GB safety margin
        available = vram_mb - 1024
    else:
        # Entry-level: leave 1.5GB safety margin
        available = vram_mb - 1536

    if available <= 0:
        return 0

    # Estimate total layers from model size
    # Typical: 8B Q4 ~ 5GB, 12B ~ 7GB, 35B ~ 18GB, 70B ~ 38GB
    # Most models have 32-80 layers; we'll estimate based on size
    total_layers = _estimate_total_layers(model_size_gb)
    if total_layers <= 0:
        return 0

    # Fraction of model that fits in VRAM
    fraction = min(available / model_mem_mb, 1.0)
    layers = int(total_layers * fraction)

    return layers


def _estimate_total_layers(model_size_gb: float) -> int:
    """Estimate total layers based on model size."""
    if model_size_gb >= 35:
        return 80  # 35B+ models typically have ~80 layers
    elif model_size_gb >= 12:
        return 40  # 12B models typically have ~40 layers
    elif model_size_gb >= 7:
        return 32  # 7-8B models typically have 32 layers
    elif model_size_gb >= 3:
        return 32  # 3B models
    else:
        return 24  # 1.5B models


def get_hardware_summary(info: HardwareInfo) -> str:
    """Get a human-readable hardware summary."""
    lines = [
        f"GPU: {info.gpu_name or 'Unknown'}",
        f"VRAM: {info.vram_total_mb}MB total, {info.vram_available_mb}MB free",
        f"RAM: {info.ram_total_mb}MB total, {info.ram_available_mb}MB free",
        f"CUDA: {'Available' if info.cuda_available else 'Not detected'}",
        f"OS: {info.os_name} {info.os_arch}",
        f"Recommended category: {info.recommended_category}",
    ]
    return "\n".join(lines)
