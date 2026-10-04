"""Adapter for tsflex (Flexible and efficient time-series feature extraction and windowing)."""

from __future__ import annotations

from typing import Any
import numpy as np

from benchmarks.adapters.base import BaseAdapter

try:
    import pandas as pd
    import tsflex
    from tsflex.features import FeatureCollection, MultipleFeatureDescriptors
    _HAS_TSFLEX = True
    _VERSION = getattr(tsflex, "__version__", "unknown")
except ImportError:
    _HAS_TSFLEX = False
    _VERSION = "not_installed"


class Adapter(BaseAdapter):
    name = "tsflex"
    version = _VERSION

    def feature_names(self, feature_set: str = "default") -> list[str]:
        return ["mean", "std", "var", "min", "max", "skew", "kurt"]

    def extract(
        self,
        X: np.ndarray,
        feature_set: str = "default",
        threads: int = 1,
        **kwargs: Any,
    ) -> np.ndarray:
        if not _HAS_TSFLEX:
            raise RuntimeError("tsflex is not installed.")

        import scipy.stats
        funcs = [np.mean, np.std, np.var, np.min, np.max, scipy.stats.skew, scipy.stats.kurtosis]
        n_series, n_steps = X.shape

        w_str = f"{max(1, n_steps - 1)}s"
        fc = FeatureCollection(
            MultipleFeatureDescriptors(
                functions=funcs,
                series_names=["val"],
                windows=[w_str],
                strides=[w_str],
            )
        )

        n_jobs_val = threads if threads > 1 else None
        rows = []
        for i in range(n_series):
            # Create a 1D time-indexed pandas Series
            s = pd.Series(X[i], index=pd.date_range("2026-01-01", periods=n_steps, freq="1s"), name="val")
            df = fc.calculate(s, return_df=True, n_jobs=n_jobs_val)
            rows.append(df.iloc[-1].values)

        return np.array(rows, dtype=np.float64)

    def extract_sliding(
        self,
        signal: np.ndarray,
        window: int,
        stride: int,
        threads: int = 1,
    ) -> np.ndarray:
        """Extract sliding window features over 1D continuous signal."""
        if not _HAS_TSFLEX:
            raise RuntimeError("tsflex is not installed.")

        funcs = [np.mean, np.std, np.var, np.min, np.max]
        fc = FeatureCollection(
            MultipleFeatureDescriptors(
                functions=funcs,
                series_names=["val"],
                windows=[f"{window}s"],
                strides=[f"{stride}s"],
            )
        )
        n_jobs_val = threads if threads > 1 else None
        s = pd.Series(signal, index=pd.date_range("2026-01-01", periods=len(signal), freq="1s"), name="val")
        df = fc.calculate(s, return_df=True, n_jobs=n_jobs_val)
        return df.to_numpy(dtype=np.float64)

    def tune_info(self) -> dict[str, Any]:
        return {
            "name": self.name,
            "version": self.version,
            "engine": "tsflex FeatureCollection with multiprocessing n_jobs",
            "supports_sliding": True,
        }
