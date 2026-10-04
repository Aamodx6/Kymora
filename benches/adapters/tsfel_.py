"""Adapter for TSFEL (Time Series Feature Extraction Library)."""

from __future__ import annotations

from typing import Any
import numpy as np

from benches.adapters.base import BaseAdapter

try:
    import tsfel
    _HAS_TSFEL = True
    _VERSION = getattr(tsfel, "__version__", "0.2.0")
except ImportError:
    _HAS_TSFEL = False
    _VERSION = "not_installed"


class Adapter(BaseAdapter):
    name = "tsfel"
    version = _VERSION

    # The 13 TSFEL feature functions whose definitions agree with tsxtract
    # core33 (frozen in benches/agreement/feature_map.json, Phase B1).
    MATCHED_TSFEL_NAMES = [
        "Mean", "Standard deviation", "Variance", "Min", "Max", "Median",
        "Skewness", "Kurtosis", "Absolute energy", "Root mean square",
        "Mean absolute diff", "Mean diff", "Zero crossing rate",
    ]

    def __init__(self) -> None:
        self._cfg = None
        if _HAS_TSFEL:
            try:
                self._cfg = tsfel.get_features_by_domain()
            except Exception:
                pass

    def feature_names(self, feature_set: str = "default") -> list[str]:
        if not _HAS_TSFEL or self._cfg is None:
            return []
        cfg = self._matched_cfg() if feature_set == "matched" else self._cfg
        dummy = np.linspace(0.0, 10.0, 500)
        df = tsfel.time_series_features_extractor(cfg, dummy, verbose=0)
        return list(df.columns)

    def _matched_cfg(self):
        """Filter the full config down to the 13 definition-matched features."""
        cfg = {}
        for domain, funcs in (self._cfg or {}).items():
            kept = {name: settings for name, settings in funcs.items() if name in self.MATCHED_TSFEL_NAMES}
            if kept:
                cfg[domain] = kept
        return cfg

    def extract(
        self,
        X: np.ndarray,
        feature_set: str = "default",
        threads: int = 1,
        **kwargs: Any,
    ) -> np.ndarray:
        if not _HAS_TSFEL:
            raise RuntimeError("tsfel is not installed.")

        if feature_set == "matched":
            cfg = self._matched_cfg()
        else:
            cfg = self._cfg or tsfel.get_features_by_domain()
        n_series = X.shape[0]

        # TSFEL time_series_features_extractor operates on 1D series or 2D multichannel.
        # Across independent series in a batch, run extraction per row:
        if threads > 1:
            from joblib import Parallel, delayed
            def _extract_row(row: np.ndarray) -> np.ndarray:
                df = tsfel.time_series_features_extractor(cfg, row, verbose=0)
                return df.to_numpy().ravel()

            rows = Parallel(n_jobs=threads)(delayed(_extract_row)(X[i]) for i in range(n_series))
            return np.array(rows, dtype=np.float64)
        else:
            rows = []
            for i in range(n_series):
                df = tsfel.time_series_features_extractor(cfg, X[i], verbose=0)
                rows.append(df.to_numpy().ravel())
            return np.array(rows, dtype=np.float64)

    def tune_info(self) -> dict[str, Any]:
        return {
            "name": self.name,
            "version": self.version,
            "parallelism": "joblib Parallel(n_jobs=threads)",
            "config": "tsfel.get_features_by_domain() (statistical + temporal + spectral)",
        }
