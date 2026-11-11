"""Hardware-adaptive CUDA batching and OOM fallback helpers for MKCurve-Py."""

from __future__ import annotations

import os
from typing import Any

GIB = 1024 ** 3
MIB = 1024 ** 2


def query_cuda_free_total_bytes(device: Any = None) -> tuple[int, int] | None:
    """Return ``(free_bytes, total_bytes)`` for ``device``, or ``None`` if unavailable."""
    try:
        import torch

        if not torch.cuda.is_available():
            return None
        dev = torch.device("cuda" if device is None else device)
        if dev.type != "cuda":
            return None
        idx = torch.cuda.current_device() if dev.index is None else int(dev.index)
        free_b, total_b = torch.cuda.mem_get_info(idx)
        cap_env = (
            os.environ.get("MKCURVE_MAX_VRAM_GIB", "").strip()
            or os.environ.get("SLICERDSPACE_MAX_VRAM_GIB", "").strip()
        )
        if cap_env:
            try:
                cap_b = int(float(cap_env) * GIB)
                if cap_b > 0:
                    used_b = max(0, int(torch.cuda.memory_allocated(idx)))
                    total_b = min(int(total_b), cap_b)
                    free_b = min(int(free_b), max(int(64 * MIB), cap_b - used_b))
            except ValueError:
                pass
        return int(free_b), int(total_b)
    except Exception:
        return None


def is_cuda_oom(exc: BaseException) -> bool:
    """Return True when ``exc`` represents a CUDA out-of-memory condition."""
    msg = str(exc).lower()
    if "out of memory" in msg and ("cuda" in msg or "cublas" in msg or "cudnn" in msg or "alloc" in msg):
        return True
    return "outofmemory" in type(exc).__name__.lower()


def empty_cuda_cache_safely() -> None:
    try:
        import torch

        if torch.cuda.is_available() and torch.cuda.is_initialized():
            torch.cuda.empty_cache()
    except Exception:
        pass


def adaptive_cuda_scaled_batch(
    per_item_bytes: int,
    default_batch: int,
    *,
    min_batch: int = 128,
    max_batch: int = 16384,
    safety_fraction: float = 0.30,
    device: Any = None,
) -> int:
    """Scale batch size down on low-VRAM GPUs while keeping ``default_batch`` when VRAM suffices."""
    base = max(int(min_batch), min(int(max_batch), int(default_batch)))
    info = query_cuda_free_total_bytes(device)
    if info is None:
        return base
    free_b, _ = info
    budget = max(int(32 * MIB), int(free_b * float(safety_fraction)))
    max_safe = max(int(min_batch), budget // max(1, int(per_item_bytes)))
    return max(int(min_batch), min(base, max_safe))
