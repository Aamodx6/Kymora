"""Adapter for tsfresh (supporting extract-only and end-to-end DataFrame construction)."""

from __future__ import annotations

from typing import Any
import numpy as np

from benchmarks.adapters.base import BaseAdapter

try:
    import pandas as pd
    import tsfresh
    from tsfresh import extract_features as tsf_extract
    from tsfresh.feature_extraction import ComprehensiveFCParameters, EfficientFCParameters, MinimalFCParameters
    _HAS_TSFRESH = True
    _VERSION = getattr(tsfresh, "__version__", "0.21.2")
except ImportError:
    _HAS_TSFRESH = False
    _VERSION = "not_installed"


class Adapter(BaseAdapter):
    name = "tsfresh"
    version = _VERSION

    # The 13 tsfresh features whose definitions agree with kymora core33
    # (frozen in benchmarks/agreement/feature_map.json, Phase B1). Used for the
    # matched-feature view (arch.md §11.6): time ONLY the agreed definitions.
    MATCHED_FC_PARAMS = {
        "median": None,
        "quantile": [{"q": 0.1}, {"q": 0.9}],
        "abs_energy": None,
        "root_mean_square": None,
        "mean_abs_change": None,
        "mean_change": None,
        "mean_second_derivative_central": None,
        "longest_strike_above_mean": None,
        "longest_strike_below_mean": None,
        "autocorrelation": [{"lag": 1}, {"lag": 2}, {"lag": 5}],
    }

    def feature_names(self, feature_set: str = "default") -> list[str]:
        if not _HAS_TSFRESH:
            return []
        if feature_set == "matched":
            dummy = pd.DataFrame({"id": [0, 0, 0, 0], "val": [1.0, 2.0, 3.0, 4.0]})
            df = tsf_extract(dummy, column_id="id", default_fc_parameters=dict(self.MATCHED_FC_PARAMS), disable_progressbar=True)
            return list(df.columns)
        dummy = pd.DataFrame({"id": [0, 0, 0, 0], "val": [1.0, 2.0, 3.0, 4.0]})
        params = EfficientFCParameters() if feature_set in ("default", "efficient") else MinimalFCParameters()
        df = tsf_extract(dummy, column_id="id", default_fc_parameters=params, disable_progressbar=True)
        return list(df.columns)

    def extract(
        self,
        X: np.ndarray,
        feature_set: str = "default",
        threads: int = 1,
        **kwargs: Any,
    ) -> np.ndarray:
        if not _HAS_TSFRESH:
            raise RuntimeError("tsfresh is not installed.")

        n_series, n_steps = X.shape

        # Select parameter set
        if feature_set in ("default", "efficient"):
            fc_params = EfficientFCParameters()
        elif feature_set in ("comprehensive", "full"):
            fc_params = ComprehensiveFCParameters()
        elif feature_set in ("minimal", "core"):
            fc_params = MinimalFCParameters()
        elif feature_set == "matched":
            # Only the 13 definition-matched features (B1 frozen set)
            fc_params = dict(self.MATCHED_FC_PARAMS)
        else:
            fc_params = EfficientFCParameters()

        # Check if preconstructed long_df passed (for extract-only vs end-to-end)
        long_df = kwargs.get("long_df", None)
        if long_df is None:
            # End-to-end: construct long DataFrame (what real users do)
            long_df = pd.DataFrame({
                "id": np.repeat(np.arange(n_series), n_steps),
                "val": X.ravel(),
            })

        df_out = tsf_extract(
            long_df,
            column_id="id",
            default_fc_parameters=fc_params,
            n_jobs=threads,
            disable_progressbar=True,
        )

        return df_out.to_numpy(dtype=np.float64)

    def tune_info(self) -> dict[str, Any]:
        return {
            "name": self.name,
            "version": self.version,
            "parallelism": "Multiprocessing inside tsfresh via n_jobs",
            "fc_parameters": "EfficientFCParameters default, Minimal / Comprehensive supported",
            "supports_extract_only": True,
        }
