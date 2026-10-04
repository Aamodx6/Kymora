"""Adapter for pycatch22 (per-series loop and multiprocessing.Pool variants)."""

from __future__ import annotations

import multiprocessing as mp
from typing import Any
import numpy as np

from benchmarks.adapters.base import BaseAdapter

try:
    import pycatch22
    _HAS_CATCH22 = True
    _VERSION = getattr(pycatch22, "__version__", "0.5.0")
except ImportError:
    _HAS_CATCH22 = False
    _VERSION = "not_installed"


def _extract_one_series(series: np.ndarray) -> list[float]:
    res = pycatch22.catch22_all(series.tolist() if isinstance(series, np.ndarray) else series)
    return res["values"]


class Adapter(BaseAdapter):
    name = "catch22"
    version = _VERSION

    def feature_names(self, feature_set: str = "default") -> list[str]:
        if not _HAS_CATCH22:
            return []
        # Return canonical catch22 names from a dummy series
        dummy = [1.0, 2.0, 3.0, 4.0, 5.0, 6.0, 7.0, 8.0, 9.0, 10.0]
        res = pycatch22.catch22_all(dummy)
        return list(res["names"])

    def extract(
        self,
        X: np.ndarray,
        feature_set: str = "default",
        threads: int = 1,
        **kwargs: Any,
    ) -> np.ndarray:
        if not _HAS_CATCH22:
            raise RuntimeError("pycatch22 is not installed.")

        n_series = X.shape[0]

        # Mode A: Parallel multiprocessing.Pool variant if threads > 1 or explicitly requested
        use_pool = threads > 1 or feature_set == "multiprocessing"

        if use_pool and n_series > 1:
            chunksize = max(1, n_series // (threads * 4))
            with mp.Pool(processes=threads) as pool:
                rows = pool.map(_extract_one_series, [X[i] for i in range(n_series)], chunksize=chunksize)
            return np.array(rows, dtype=np.float64)

        # Mode B: Standard per-series loop
        rows = []
        for i in range(n_series):
            res = pycatch22.catch22_all(X[i])
            rows.append(res["values"])

        return np.array(rows, dtype=np.float64)

    def tune_info(self) -> dict[str, Any]:
        return {
            "name": self.name,
            "version": self.version,
            "parallelism": "multiprocessing.Pool when threads > 1, else serial per-series loop",
            "recommended_fast_config": "Pool(threads) with chunksize dynamic batching",
        }
