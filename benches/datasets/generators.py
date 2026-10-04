"""Deterministic synthetic time-series dataset generator.

Generates realistic, challenging, and adversarial time-series shapes and distributions:
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

    else:
        # Default gaussian
        data = rng.standard_normal((n_series, length))

    if dtype == "float32":
        data = data.astype(np.float32)
    elif dtype == "int32":
        data = np.clip(data * 100, -2e9, 2e9).astype(np.int32)
    elif dtype == "int16":
        data = np.clip(data * 100, -32768, 32767).astype(np.int16)
    else:
        data = data.astype(np.float64)

    return data


def array_sha256(arr: np.ndarray) -> str:
    """Compute sha256 checksum of raw numpy array buffer."""
    return hashlib.sha256(arr.tobytes()).hexdigest()
