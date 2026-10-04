"""Wisdom auto-tuner (tune) for benchmarking and caching system-specific execution parameters."""
from __future__ import annotations

import json
import os
import platform
import time
from pathlib import Path
from typing import Any, Sequence
import numpy as np

from ._core import extract_features


def _get_cache_path() -> Path:
    """Return wisdom cache file path."""
    if os.name == "nt":
        base = os.environ.get("LOCALAPPDATA")
        if base:
            cache_dir = Path(base) / "tsxtract"
        else:
            cache_dir = Path.home() / ".cache" / "tsxtract"
    else:
        cache_dir = Path.home() / ".cache" / "tsxtract"
    cache_dir.mkdir(parents=True, exist_ok=True)
    return cache_dir / "wisdom.json"


def load_wisdom() -> dict[str, Any] | None:
    """Load cached wisdom configuration if available and not disabled."""
    if os.environ.get("TSXTRACT_WISDOM", "").lower() in ("off", "0", "false"):
        return None

    path = _get_cache_path()
    if path.is_file():
        try:
            with open(path, "r", encoding="utf-8") as f:
                data = json.load(f)
            # Validate machine signature
            curr_machine = f"{platform.machine()}-{platform.processor()}"
            if data.get("machine") == curr_machine:
                return data
        except Exception:
            return None
    return None


def tune(
    shapes: Sequence[tuple[int, int]] = ((1000, 500),),
    budget_s: float = 10.0,
) -> dict[str, Any]:
    """Microbenchmark execution variants on this hardware and cache optimal parameters.

    Args:
        shapes: Sequence of (n_series, length) shapes to test. Default: ((1000, 500),).
        budget_s: Maximum wall-clock time in seconds to spend tuning. Default: 10.0.

    Returns:
        Dictionary of tuned execution parameters including pool type and chunk size.
    """
    start_time = time.perf_counter()
    results = {}
    best_config = {"pool": "spin", "chunk_size": 32}

    tested_shapes = []

    for n_series, length in shapes:
        if time.perf_counter() - start_time >= budget_s:
            break

        tested_shapes.append([n_series, length])
        rng = np.random.default_rng(42)
        X = rng.standard_normal((min(n_series, 2000), length))

        # Benchmark rayon
        os.environ["TSXTRACT_POOL"] = "rayon"
        t0 = time.perf_counter()
        extract_features(X)
        t_rayon = time.perf_counter() - t0

        # Benchmark spin pool
        os.environ["TSXTRACT_POOL"] = "spin"
        t0 = time.perf_counter()
        extract_features(X)
        t_spin = time.perf_counter() - t0

        results[f"{n_series}x{length}"] = {
            "rayon_s": t_rayon,
            "spin_s": t_spin,
        }

        if t_spin < t_rayon:
            best_config["pool"] = "spin"
        else:
            best_config["pool"] = "rayon"

    wisdom = {
        "machine": f"{platform.machine()}-{platform.processor()}",
        "best_config": best_config,
        "results": results,
        "shapes": tested_shapes,
        "timestamp": time.time(),
    }

    try:
        cache_file = _get_cache_path()
        with open(cache_file, "w", encoding="utf-8") as f:
            json.dump(wisdom, f, indent=2)
    except Exception:
        pass

    return wisdom
