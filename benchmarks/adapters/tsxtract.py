"""Adapter for Tsxtract (Rust core)."""

from __future__ import annotations

from typing import Any
import numpy as np

from benchmarks.adapters.base import BaseAdapter


class Adapter(BaseAdapter):
    name = "tsxtract"

    # Frozen matched sets from benchmarks/agreement/feature_map.json (Phase B1).
    # feature_set="matched_<competitor>" extracts ONLY the features whose
    # definitions agree with that competitor -> matched-feature view (§11.6).
    MATCHED_SETS = {
        "matched_tsfresh": [
            "median", "quantile_10", "quantile_90", "abs_energy",
            "root_mean_square", "mean_abs_change", "mean_change",
            "mean_second_derivative_central", "longest_strike_above_mean",
            "longest_strike_below_mean", "autocorr_lag_1", "autocorr_lag_2",
            "autocorr_lag_5",
        ],
        "matched_tsfel": [
            "mean", "std", "var", "min", "max", "median", "skewness",
            "kurtosis", "abs_energy", "root_mean_square", "mean_abs_change",
            "mean_change", "zero_crossings",
        ],
    }

    def __init__(self) -> None:
        try:
            import tsxtract
            self.lib = tsxtract
            self.version = getattr(tsxtract, "__version__", "0.5.0")
        except ImportError:
            try:
                import tsxtractor
                self.lib = tsxtractor
                self.version = getattr(tsxtractor, "__version__", "0.5.0")
            except ImportError:
                self.lib = None
                self.version = "not_installed"

    def feature_names(self, feature_set: str = "default") -> list[str]:
        if self.lib is None:
            return []
        prof = "core33" if feature_set in ("default", "core33") else feature_set
        if hasattr(self.lib, "feature_names"):
            try:
                return list(self.lib.feature_names(profile=prof))
            except TypeError:
                return list(self.lib.feature_names())
        return []

    def extract(
        self,
        X: np.ndarray,
        feature_set: str = "default",
        threads: int = 1,
        **kwargs: Any,
    ) -> np.ndarray:
        if self.lib is None:
            raise RuntimeError("tsxtract / tsxtractor is not installed.")

        prof = "core33" if feature_set in ("default", "core33") else feature_set
        precision = kwargs.get("precision", "f64")

        # Matched-subset extraction (only definition-agreed features)
        if feature_set in self.MATCHED_SETS:
            return self.lib.extract_features(
                X,
                features=list(self.MATCHED_SETS[feature_set]),
                n_jobs=threads,
            )

        # Call native zero-copy extract_features
        try:
            return self.lib.extract_features(
                X,
                profile=prof,
                n_jobs=threads,
                precision=precision,
            )
        except TypeError:
            # Fallback if precision is not an accepted kwarg in this build
            return self.lib.extract_features(
                X,
                profile=prof,
                n_jobs=threads,
            )

    def tune_info(self) -> dict[str, Any]:
        return {
            "name": self.name,
            "version": self.version,
            "runtime": "Rust",
            "parallelism": "Rayon / Persistent SpinPool",
            "zero_copy": True,
            "allocations": "Single output matrix",
        }
