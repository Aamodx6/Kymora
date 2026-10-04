"""Statistical utilities for the Tsxtract benchmark harness.

Provides pyperf-style metrics:
- min, median, IQR (q75 - q25), mean, std, p95, CV
- Flagging when CV > 5%
- Bootstrap 95% confidence intervals for single series and ratios
- Clean separation of "best-of" (min) vs "median"
"""

from __future__ import annotations

import math
from typing import Sequence
import numpy as np


def compute_stats(runs: Sequence[float]) -> dict[str, float | bool]:
    """Compute benchmark statistics from an array of wall-clock times in seconds."""
    if not runs:
        return {
            "n_runs": 0,
            "min": math.nan,
            "median": math.nan,
            "mean": math.nan,
            "std": math.nan,
            "iqr": math.nan,
            "p95": math.nan,
            "cv": math.nan,
            "high_cv": False,
        }

    arr = np.asarray(runs, dtype=np.float64)
    n = len(arr)
    min_val = float(np.min(arr))
    median_val = float(np.median(arr))
    mean_val = float(np.mean(arr))
    std_val = float(np.std(arr, ddof=1)) if n > 1 else 0.0
    q25 = float(np.percentile(arr, 25))
    q75 = float(np.percentile(arr, 75))
    iqr_val = float(q75 - q25)
    p95_val = float(np.percentile(arr, 95))
    cv_val = float(std_val / mean_val) if mean_val > 0 else 0.0

    return {
        "n_runs": n,
        "min": min_val,
        "median": median_val,
        "mean": mean_val,
        "std": std_val,
        "iqr": iqr_val,
        "p95": p95_val,
        "cv": cv_val,
        "high_cv": bool(cv_val > 0.05),
    }


def bootstrap_ci(
    samples: Sequence[float],
    n_resamples: int = 2000,
    confidence_level: float = 0.95,
    statistic: str = "median",
    seed: int = 42,
) -> tuple[float, float]:
    """Compute bootstrap confidence interval for a statistic on a single sample."""
    arr = np.asarray(samples, dtype=np.float64)
    if len(arr) < 2:
        val = float(arr[0]) if len(arr) == 1 else math.nan
        return val, val

    rng = np.random.default_rng(seed)
    stat_fn = np.median if statistic == "median" else np.mean
    boot_stats = np.empty(n_resamples, dtype=np.float64)

    for i in range(n_resamples):
        resample = rng.choice(arr, size=len(arr), replace=True)
        boot_stats[i] = stat_fn(resample)

    alpha = (1.0 - confidence_level) / 2.0
    low = float(np.percentile(boot_stats, 100.0 * alpha))
    high = float(np.percentile(boot_stats, 100.0 * (1.0 - alpha)))
    return low, high


def bootstrap_ratio_ci(
    numerator_samples: Sequence[float],
    denominator_samples: Sequence[float],
    n_resamples: int = 2000,
    confidence_level: float = 0.95,
    statistic: str = "median",
    seed: int = 42,
) -> tuple[float, float]:
    """Compute bootstrap 95% CI for the ratio: num_stat / denom_stat."""
    num_arr = np.asarray(numerator_samples, dtype=np.float64)
    denom_arr = np.asarray(denominator_samples, dtype=np.float64)
    if len(num_arr) == 0 or len(denom_arr) == 0:
        return math.nan, math.nan

    rng = np.random.default_rng(seed)
    stat_fn = np.median if statistic == "median" else np.mean
    ratios = np.empty(n_resamples, dtype=np.float64)

    for i in range(n_resamples):
        num_res = rng.choice(num_arr, size=len(num_arr), replace=True)
        denom_res = rng.choice(denom_arr, size=len(denom_arr), replace=True)
        denom_val = stat_fn(denom_res)
        if denom_val <= 0 or math.isnan(denom_val):
            ratios[i] = math.nan
        else:
            ratios[i] = stat_fn(num_res) / denom_val

    valid = ratios[~np.isnan(ratios)]
    if len(valid) == 0:
        return math.nan, math.nan

    alpha = (1.0 - confidence_level) / 2.0
    low = float(np.percentile(valid, 100.0 * alpha))
    high = float(np.percentile(valid, 100.0 * (1.0 - alpha)))
    return low, high
