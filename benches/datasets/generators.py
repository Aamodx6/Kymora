"""Deterministic synthetic time-series dataset generator.

Generates realistic, challenging, and adversarial time-series shapes and distributions
per arch.md §11.4:
- Gaussian white noise
- Random walk
- Sinusoid + noise (multiple SNR)
- AR(1) processes (phi in {0.1, 0.7, 0.9, 0.99})
- Trend + seasonality
- Heavy-tailed (Student-t 3 df, Cauchy)
- Spikes / outliers
- Step changes
- Piecewise constant
- Quantized / integer-like (8-bit, 16-bit ADC, many ties)
- Sparse (mostly zeros)
- Bimodal mixtures
- Exact constant
- Near-constant with offset 1e9 (cancellation stress)
- Tiny scale (1e-150, underflow/denormals)
- Huge scale (1e150, sum of squares overflow)
- Mixed magnitudes

Ensures: seed -> identical bitwise output (identical SHA-256).
"""

from __future__ import annotations

import hashlib
import numpy as np


# ────────────────────────────────────────────────────────────
#  All supported distribution names
# ────────────────────────────────────────────────────────────

ALL_DISTRIBUTIONS = [
    "gaussian",
    "random_walk",
    "sinusoid",
    "ar1",          # phi=0.7 (default)
    "ar1_0.1",
    "ar1_0.9",
    "ar1_0.99",
    "trend_seasonality",
    "heavy_tailed",
    "cauchy",
    "spikes",
    "step_changes",
    "piecewise_constant",
    "quantized_8bit",
    "quantized_16bit",
    "sparse",
    "bimodal",
    "constant",
    "cancellation",
    "tiny_scale",
    "huge_scale",
    "mixed_magnitudes",
]

# Benchmark shapes per arch.md §11.4
BENCHMARK_SHAPES = [
    (1, 10), (1, 100), (1, 100_000), (1, 1_000_000),
    (10, 500), (100, 100), (100, 500),
    (1000, 100), (1000, 500), (1000, 5000),
    (10_000, 500), (100_000, 500), (100_000, 100),
    (1_000_000, 100), (100, 50_000),
]

# Odd / adversarial lengths per arch.md §11.4
ODD_LENGTHS = [7, 31, 499, 500, 503, 997, 1000, 1024, 2047, 4093, 65536, 100003]


def generate_series(
    dist: str,
    n_series: int,
    length: int,
    dtype: str = "float64",
    seed: int = 42,
    **kwargs,
) -> np.ndarray:
    """Generate deterministic 2D synthetic time-series array of shape (n_series, length)."""
    rng = np.random.default_rng(seed)

    if dist == "gaussian":
        data = rng.standard_normal((n_series, length))

    elif dist == "random_walk":
        steps = rng.standard_normal((n_series, length))
        data = np.cumsum(steps, axis=1)

    elif dist == "sinusoid":
        snr = float(kwargs.get("snr", 10.0))
        t = np.linspace(0, 8 * np.pi, length)
        signal = np.sin(t)
        noise = rng.standard_normal((n_series, length)) / snr
        data = signal[None, :] + noise

    elif dist.startswith("ar1"):
        # e.g. ar1_0.9 or default phi=0.7
        phi = float(kwargs.get("phi", 0.7))
        if "_" in dist:
            try:
                phi = float(dist.split("_")[1])
            except ValueError:
                pass
        data = np.zeros((n_series, length), dtype=np.float64)
        noise = rng.standard_normal((n_series, length))
        data[:, 0] = noise[:, 0]
        for t in range(1, length):
            data[:, t] = phi * data[:, t - 1] + noise[:, t]

    elif dist == "trend_seasonality":
        t = np.linspace(0, 1, length)
        trend = 5.0 * t
        seasonal = 2.0 * np.sin(2 * np.pi * 10 * t)
        noise = 0.5 * rng.standard_normal((n_series, length))
        data = (trend + seasonal)[None, :] + noise

    elif dist in ("heavy_tailed", "t3"):
        data = rng.standard_t(df=3, size=(n_series, length))

    elif dist == "cauchy":
        data = rng.standard_cauchy(size=(n_series, length))
        # Clip extreme outliers to prevent immediate inf
        data = np.clip(data, -1e6, 1e6)

    elif dist == "spikes":
        data = rng.standard_normal((n_series, length))
        # Add 1% high-magnitude spikes
        mask = rng.random((n_series, length)) < 0.01
        data[mask] += rng.choice([-50.0, 50.0], size=int(np.sum(mask)))

    elif dist == "step_changes":
        data = np.zeros((n_series, length), dtype=np.float64)
        for i in range(n_series):
            n_steps = rng.integers(2, 6)
            change_points = np.sort(rng.choice(length, size=n_steps, replace=False))
            levels = rng.standard_normal(n_steps + 1) * 3.0
            idx = np.searchsorted(change_points, np.arange(length))
            data[i] = levels[idx]
        data += 0.05 * rng.standard_normal((n_series, length))

    elif dist == "piecewise_constant":
        data = np.zeros((n_series, length), dtype=np.float64)
        for i in range(n_series):
            n_segments = max(2, length // 20)
            cuts = np.sort(rng.choice(length - 1, size=n_segments - 1, replace=False)) + 1
            bounds = np.concatenate([[0], cuts, [length]])
            for k in range(len(bounds) - 1):
                val = float(rng.integers(-5, 6))
                data[i, bounds[k]:bounds[k+1]] = val

    elif dist == "quantized_8bit":
        # 8-bit ADC simulation: many ties
        continuous = 127.5 * (1.0 + np.sin(np.linspace(0, 6 * np.pi, length)))
        noise = rng.standard_normal((n_series, length)) * 5.0
        noisy = continuous[None, :] + noise
        data = np.clip(np.round(noisy), 0, 255)

    elif dist == "quantized_16bit":
        # 16-bit ADC simulation: ties but more dynamic range
        continuous = 32767.5 * (1.0 + np.sin(np.linspace(0, 6 * np.pi, length)))
        noise = rng.standard_normal((n_series, length)) * 100.0
        noisy = continuous[None, :] + noise
        data = np.clip(np.round(noisy), 0, 65535)

    elif dist == "sparse":
        # 95% zeros
        mask = rng.random((n_series, length)) > 0.95
        data = np.zeros((n_series, length), dtype=np.float64)
        data[mask] = rng.standard_normal(int(np.sum(mask)))

    elif dist == "bimodal":
        # 50/50 mixture of N(-3, 1) and N(+3, 1)
        choices = rng.random((n_series, length)) > 0.5
        noise = rng.standard_normal((n_series, length))
        data = np.where(choices, 3.0 + noise, -3.0 + noise)

    elif dist == "constant":
        data = np.full((n_series, length), 3.141592653589793)

    elif dist == "cancellation":
        # 1e9 + small noise -> tests numerical cancellation in variance
        data = 1e9 + rng.standard_normal((n_series, length))

    elif dist == "tiny_scale":
        data = 1e-150 * rng.standard_normal((n_series, length))

    elif dist == "huge_scale":
        data = 1e150 * rng.standard_normal((n_series, length))

    elif dist == "mixed_magnitudes":
        # Each series has a vastly different scale from 1e-50 to 1e50
        scales = 10.0 ** rng.uniform(-50, 50, size=(n_series, 1))
        data = rng.standard_normal((n_series, length)) * scales

    elif dist == "quantized":
        # Alias for quantized_8bit
        continuous = 127.5 * (1.0 + np.sin(np.linspace(0, 6 * np.pi, length)))
        noise = rng.standard_normal((n_series, length)) * 5.0
        noisy = continuous[None, :] + noise
        data = np.clip(np.round(noisy), 0, 255)

    else:
        # Default gaussian
        data = rng.standard_normal((n_series, length))

    if dtype == "float32":
        data = data.astype(np.float32)
    elif dtype == "int32":
        data = np.clip(data * 100, -2e9, 2e9).astype(np.int32)
    elif dtype == "int16":
        data = np.clip(data * 100, -32768, 32767).astype(np.int16)
    elif dtype == "uint8":
        data = np.clip(data, 0, 255).astype(np.uint8)
    else:
        data = data.astype(np.float64)

    return data


def array_sha256(arr: np.ndarray) -> str:
    """Compute sha256 checksum of raw numpy array buffer."""
    return hashlib.sha256(arr.tobytes()).hexdigest()


def verify_determinism(
    dist: str = "gaussian",
    n_series: int = 100,
    length: int = 500,
    seed: int = 42,
) -> tuple[bool, str, str]:
    """Verify that the same seed produces identical output. Returns (match, sha1, sha2)."""
    a = generate_series(dist, n_series, length, seed=seed)
    b = generate_series(dist, n_series, length, seed=seed)
    h1 = array_sha256(a)
    h2 = array_sha256(b)
    return h1 == h2, h1, h2


def generate_benchmark_matrix(
    distributions: list[str] | None = None,
    shapes: list[tuple[int, int]] | None = None,
    seed: int = 42,
) -> dict[str, dict[str, np.ndarray]]:
    """Generate the full benchmark dataset matrix: {dist: {shape_key: array}}.

    Only generates shape/dist combos that fit in memory (< 2 GB).
    """
    if distributions is None:
        distributions = ["gaussian", "random_walk", "ar1", "heavy_tailed"]
    if shapes is None:
        shapes = BENCHMARK_SHAPES

    matrix = {}
    for dist in distributions:
        matrix[dist] = {}
        for n, l in shapes:
            # Skip shapes > ~2 GB (n * l * 8 bytes)
            mem_bytes = n * l * 8
            if mem_bytes > 2e9:
                continue
            key = f"{n}x{l}"
            matrix[dist][key] = generate_series(dist, n, l, seed=seed)
    return matrix
