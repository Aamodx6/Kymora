"""Honest baseline: pure NumPy/SciPy vectorized implementation of the 33 core features."""

from __future__ import annotations

import math
from typing import Any
import numpy as np
import scipy.stats

from benches.adapters.base import BaseAdapter

CORE33_NAMES = [
    "mean", "std", "var", "min", "max", "median",
    "quantile_10", "quantile_25", "quantile_75", "quantile_90",
    "skewness", "kurtosis", "abs_energy", "root_mean_square",
    "mean_abs_change", "mean_change", "cid_ce", "mean_second_derivative_central",
    "zero_crossings", "mean_crossings", "number_of_peaks",
    "longest_strike_above_mean", "longest_strike_below_mean",
    "autocorr_lag_1", "autocorr_lag_2", "autocorr_lag_5", "autocorr_lag_10",
    "trend_slope", "trend_r2", "permutation_entropy",
    "dominant_frequency", "spectral_centroid", "spectral_entropy",
]


def _longest_strike_row(mask: np.ndarray) -> int:
    best = cur = 0
    for v in mask:
        cur = cur + 1 if v else 0
        if cur > best:
            best = cur
    return best


def _perm_entropy_row(x: np.ndarray) -> float:
    n = len(x)
    if n < 3:
        return math.nan
    counts: dict[tuple[bool, bool, bool], int] = {}
    for a, b, c in zip(x, x[1:], x[2:]):
        key = (bool(a <= b), bool(b <= c), bool(a <= c))
        counts[key] = counts.get(key, 0) + 1
    p = np.array(list(counts.values()), dtype=np.float64) / (n - 2)
    return float(-(p * np.log(p)).sum() / math.log(6))


class Adapter(BaseAdapter):
    name = "numpy_baseline"
    version = f"numpy_{np.__version__}"

    def feature_names(self, feature_set: str = "default") -> list[str]:
        return list(CORE33_NAMES)

    def extract(
        self,
        X: np.ndarray,
        feature_set: str = "default",
        threads: int = 1,
        **kwargs: Any,
    ) -> np.ndarray:
        n_series, n_steps = X.shape
        out = np.empty((n_series, 33), dtype=np.float64)

        # 1. Moments & basic stats
        mean = X.mean(axis=1)
        var = X.var(axis=1)
        std = np.sqrt(var)
        min_val = X.min(axis=1)
        max_val = X.max(axis=1)

        # Handle exact constant series
        const_mask = (min_val == max_val)
        var[const_mask] = 0.0
        std[const_mask] = 0.0

        out[:, 0] = mean
        out[:, 1] = std
        out[:, 2] = var
        out[:, 3] = min_val
        out[:, 4] = max_val

        # 2. Quantiles
        out[:, 5] = np.median(X, axis=1)
        out[:, 6] = np.quantile(X, 0.10, axis=1)
        out[:, 7] = np.quantile(X, 0.25, axis=1)
        out[:, 8] = np.quantile(X, 0.75, axis=1)
        out[:, 9] = np.quantile(X, 0.90, axis=1)

        # 3. Skewness and Kurtosis
        skew = scipy.stats.skew(X, axis=1, bias=True)
        kurt = scipy.stats.kurtosis(X, axis=1, bias=True)
        skew[std == 0] = np.nan
        kurt[std == 0] = np.nan
        out[:, 10] = skew
        out[:, 11] = kurt

        # 4. Energy & RMS
        sq = X**2
        out[:, 12] = sq.sum(axis=1)
        out[:, 13] = np.sqrt(sq.mean(axis=1))

        # 5. Differences & changes
        if n_steps >= 2:
            diff = np.diff(X, axis=1)
            out[:, 14] = np.abs(diff).mean(axis=1)
            out[:, 15] = (X[:, -1] - X[:, 0]) / (n_steps - 1)
            
            with np.errstate(divide="ignore", invalid="ignore"):
                diff_norm = diff / np.where(std[:, None] > 0, std[:, None], np.nan)
                cid = np.sqrt(np.nansum(diff_norm**2, axis=1))
                cid[std == 0] = 0.0
            out[:, 16] = cid
        else:
            out[:, 14:17] = np.nan

        # 6. Central second derivative
        if n_steps >= 3:
            d2 = (X[:, 2:] - 2 * X[:, 1:-1] + X[:, :-2]).sum(axis=1) / (2 * (n_steps - 2))
            out[:, 17] = d2
        else:
            out[:, 17] = np.nan

        # 7. Crossings
        out[:, 18] = ((X[:, :-1] > 0) != (X[:, 1:] > 0)).sum(axis=1)
        m_2d = mean[:, None]
        out[:, 19] = ((X[:, :-1] > m_2d) != (X[:, 1:] > m_2d)).sum(axis=1)

        # 8. Number of peaks (support = 3)
        if n_steps >= 7:
            p_cond = (
                (X[:, 3:-3] > X[:, 2:-4]) & (X[:, 3:-3] > X[:, 4:-2]) &
                (X[:, 3:-3] > X[:, 1:-5]) & (X[:, 3:-3] > X[:, 5:-1]) &
                (X[:, 3:-3] > X[:, :-6]) & (X[:, 3:-3] > X[:, 6:])
            )
            out[:, 20] = p_cond.sum(axis=1)
        else:
            out[:, 20] = 0.0

        # 9. Longest strikes
        strikes_above = np.empty(n_series, dtype=np.float64)
        strikes_below = np.empty(n_series, dtype=np.float64)
        for i in range(n_series):
            m_i = mean[i]
            strikes_above[i] = _longest_strike_row(X[i] > m_i)
            strikes_below[i] = _longest_strike_row(X[i] < m_i)
        out[:, 21] = strikes_above
        out[:, 22] = strikes_below

        # 10. Autocorrelations
        for col_idx, lag in enumerate([1, 2, 5, 10], start=23):
            if n_steps > lag:
                centered = X - mean[:, None]
                cov = (centered[:, :n_steps - lag] * centered[:, lag:]).sum(axis=1) / (n_steps - lag)
                with np.errstate(divide="ignore", invalid="ignore"):
                    ac = cov / var
                ac[const_mask] = np.nan
                out[:, col_idx] = ac
            else:
                out[:, col_idx] = np.nan

        # 11. Linear trend
        if n_steps >= 2:
            t = np.arange(n_steps, dtype=np.float64)
            t_m = t.mean()
            t_diff = t - t_m
            s_xx = (t_diff**2).sum()
            s_xy = (X * t_diff).sum(axis=1)
            slope = s_xy / s_xx
            slope[const_mask] = 0.0
            out[:, 27] = slope
            
            with np.errstate(divide="ignore", invalid="ignore"):
                r2 = (slope**2 * s_xx) / (n_steps * var)
            r2[const_mask] = np.nan
            out[:, 28] = np.clip(r2, 0.0, 1.0)
        else:
            out[:, 27:29] = np.nan

        # 12. Permutation entropy
        perms = np.empty(n_series, dtype=np.float64)
        for i in range(n_series):
            perms[i] = _perm_entropy_row(X[i])
        out[:, 29] = perms

        # 13. Spectral features (mean removed FFT)
        if n_steps >= 2:
            centered = X - mean[:, None]
            fft = np.fft.rfft(centered, axis=1)
            nbins = n_steps // 2
            # slice frequencies 1..nbins
            power = np.abs(fft[:, 1:nbins + 1])**2
            total_power = power.sum(axis=1)
            
            freqs = np.arange(1, nbins + 1, dtype=np.float64) / n_steps
            dom_idx = np.argmax(power, axis=1)
            dom_freq = freqs[dom_idx]
            dom_freq[total_power == 0] = np.nan
            out[:, 30] = dom_freq

            with np.errstate(divide="ignore", invalid="ignore"):
                centroid = (power * freqs).sum(axis=1) / total_power
            centroid[total_power == 0] = np.nan
            out[:, 31] = centroid

            # Spectral entropy
            spec_ent = np.empty(n_series, dtype=np.float64)
            if nbins == 1:
                spec_ent.fill(0.0)
            else:
                log_bins = math.log(nbins)
                for i in range(n_series):
                    tot = total_power[i]
                    if tot == 0 or np.isnan(tot):
                        spec_ent[i] = np.nan
                    else:
                        p_norm = power[i][power[i] > 0] / tot
                        spec_ent[i] = float(-(p_norm * np.log(p_norm)).sum() / log_bins)
            out[:, 32] = spec_ent
        else:
            out[:, 30:33] = np.nan

        return out

    def tune_info(self) -> dict[str, Any]:
        return {
            "name": self.name,
            "version": self.version,
            "vectorization": "Vectorized along series axis for moments, FFT, and differences",
            "reference_standard": "Pure NumPy / SciPy",
        }
