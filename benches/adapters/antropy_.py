"""Adapter for antropy (Entropy and complexity metrics for time series)."""

from __future__ import annotations

from typing import Any
import numpy as np

from benches.adapters.base import BaseAdapter

try:
    import antropy
    _HAS_ANTROPY = True
    _VERSION = getattr(antropy, "__version__", "unknown")
except ImportError:
    _HAS_ANTROPY = False
    _VERSION = "not_installed"

ANTROPY_FEATURES = [
    "perm_entropy",
    "spectral_entropy",
    "svd_entropy",
    "app_entropy",
    "sample_entropy",
    "hjorth_mobility",
    "hjorth_complexity",
    "num_zerocross",
]


class Adapter(BaseAdapter):
    name = "antropy"
    version = _VERSION

    def feature_names(self, feature_set: str = "default") -> list[str]:
        if not _HAS_ANTROPY:
            return []
        if feature_set == "perm_entropy_only":
            return ["perm_entropy"]
        return list(ANTROPY_FEATURES)

    def extract(
        self,
        X: np.ndarray,
        feature_set: str = "default",
        threads: int = 1,
        **kwargs: Any,
    ) -> np.ndarray:
        if not _HAS_ANTROPY:
            raise RuntimeError("antropy is not installed.")

        n_series = X.shape[0]

        if feature_set == "perm_entropy_only":
            # Matched comparison for permutation entropy
            out = np.empty((n_series, 1), dtype=np.float64)
            for i in range(n_series):
                out[i, 0] = antropy.perm_entropy(X[i], order=3, delay=1, normalize=True)
            return out

        out = np.empty((n_series, len(ANTROPY_FEATURES)), dtype=np.float64)
        for i in range(n_series):
            x = X[i]
            # Permutation entropy (order 3, delay 1)
            out[i, 0] = antropy.perm_entropy(x, order=3, delay=1, normalize=True)
            # Spectral entropy
            try:
                out[i, 1] = antropy.spectral_entropy(x, sf=1.0, method="fft", normalize=True)
            except Exception:
                out[i, 1] = np.nan
            # SVD entropy
            try:
                out[i, 2] = antropy.svd_entropy(x, order=3, delay=1, normalize=True)
            except Exception:
                out[i, 2] = np.nan
            # Approximate entropy
            try:
                out[i, 3] = antropy.app_entropy(x, order=2, metric="chebyshev")
            except Exception:
                out[i, 3] = np.nan
            # Sample entropy
            try:
                out[i, 4] = antropy.sample_entropy(x, order=2, metric="chebyshev")
            except Exception:
                out[i, 4] = np.nan
            # Hjorth mobility & complexity
            try:
                mob, comp = antropy.hjorth_params(x)
                out[i, 5] = mob
                out[i, 6] = comp
            except Exception:
                out[i, 5] = np.nan
                out[i, 6] = np.nan
            # Zero crossings
            try:
                out[i, 7] = float(antropy.num_zerocross(x))
            except Exception:
                out[i, 7] = np.nan

        return out

    def tune_info(self) -> dict[str, Any]:
        return {
            "name": self.name,
            "version": self.version,
            "algorithm": "Numba-accelerated entropy calculation where supported",
        }
