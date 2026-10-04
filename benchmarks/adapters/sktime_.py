"""Adapter for sktime (Catch22 and TSFresh feature transformers)."""

from __future__ import annotations

from typing import Any
import numpy as np

from benchmarks.adapters.base import BaseAdapter

try:
    import sktime
    from sktime.transformations.series_as_features.catch22 import Catch22
    _HAS_SKTIME = True
    _VERSION = getattr(sktime, "__version__", "unknown")
except ImportError:
    try:
        # Newer sktime layout
        from sktime.transformations.panel.catch22 import Catch22
        _HAS_SKTIME = True
        _VERSION = getattr(sktime, "__version__", "unknown")
    except ImportError:
        _HAS_SKTIME = False
        _VERSION = "not_installed"


class Adapter(BaseAdapter):
    name = "sktime"
    version = _VERSION

    def feature_names(self, feature_set: str = "default") -> list[str]:
        if not _HAS_SKTIME:
            return []
        c22 = Catch22()
        dummy = np.random.randn(2, 50)
        df = c22.fit_transform(dummy)
        return list(df.columns)

    def extract(
        self,
        X: np.ndarray,
        feature_set: str = "default",
        threads: int = 1,
        **kwargs: Any,
    ) -> np.ndarray:
        if not _HAS_SKTIME:
            raise RuntimeError("sktime is not installed.")

        # sktime expects 3D panel format (n_instances, n_channels, n_timepoints)
        X_panel = X[:, np.newaxis, :] if X.ndim == 2 else X

        guarded = kwargs.get("guarded", True)

        if feature_set in ("default", "catch22"):
            # Catch22 transformer
            c22 = Catch22()
            if guarded:
                try:
                    df = c22.fit_transform(X_panel)
                    return df.to_numpy(dtype=np.float64)
                except ZeroDivisionError:
                    return np.full((X.shape[0], 22), np.nan, dtype=np.float64)
            else:
                # Raw mode (guarded=False): revert silent NaN conversion, raise ZeroDivisionError
                df = c22.fit_transform(X_panel)
                return df.to_numpy(dtype=np.float64)
        elif feature_set in ("tsfresh", "tsfresh_relevant"):
            try:
                from sktime.transformations.panel.tsfresh import TSFreshFeatureExtractor
            except ImportError:
                from sktime.transformations.series_as_features.tsfresh import TSFreshFeatureExtractor
            tsf = TSFreshFeatureExtractor(default_fc_parameters="efficient", n_jobs=threads, show_warnings=False)
            df = tsf.fit_transform(X_panel)
            return df.to_numpy(dtype=np.float64)
        else:
            c22 = Catch22()
            if guarded:
                try:
                    df = c22.fit_transform(X_panel)
                    return df.to_numpy(dtype=np.float64)
                except ZeroDivisionError:
                    return np.full((X.shape[0], 22), np.nan, dtype=np.float64)
            else:
                df = c22.fit_transform(X_panel)
                return df.to_numpy(dtype=np.float64)

    def tune_info(self) -> dict[str, Any]:
        return {
            "name": self.name,
            "version": self.version,
            "transformers": "Catch22, TSFreshFeatureExtractor via scikit-learn compatible fit_transform",
            "n_jobs": "multiprocessing n_jobs",
        }
