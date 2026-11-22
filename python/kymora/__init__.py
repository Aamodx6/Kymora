"""Kymora — fast time-series feature extraction with a Rust core.

Extracts curated statistical, temporal, spectral, multichannel, and multi-view
features from batches of time series. The Rust core takes zero-copy views of
numpy buffers, releases the GIL, and parallelizes across series with Rayon.

Usage:
    import numpy as np, kymora

    X = np.random.randn(1000, 500)
    feats = kymora.extract_features(X)                      # (1000, 33) float64
    names = kymora.feature_names()                          # stable column order
    df = kymora.extract_features_df(X)                      # labeled DataFrame

    # Multi-view multiplicative extraction
    df_views = kymora.extract_features_df(X, views=["raw", "diff", "znorm"])

    # Multichannel time series
    X_mc = np.random.randn(100, 4, 500)                         # (samples, channels, length)
    df_mc = kymora.extract_features_mc_df(X_mc, cross=True)

    # Supervised feature selection
    selected_idx, report = kymora.select_features(feats, y, task="auto")

.. note::
    The PyPI distribution name is ``kymora`` (``pip install kymora``).
    There are no alternate import names: ``import kymora`` is the only
    supported spelling.
"""

from __future__ import annotations

from typing import TYPE_CHECKING, Any, Sequence

from . import _core

try:
    from ._core import _exec_mode
except ImportError:  # pragma: no cover
    def _exec_mode(n_series: int, length: int) -> str:
        return "parallel" if (n_series >= 16 and (n_series * length) >= 8000) else "sequential"

    setattr(_core, "_exec_mode", _exec_mode)

from ._core import (
    MultiStreamExtractor,
    StreamingExtractor,
    describe_feature,
    extract_features,
    extract_features_mc,
    extract_features_ragged,
    feature_names,
    feature_names_mc,
    list_profiles,
    sliding_features,
)

try:
    from ._core import extract_one
except ImportError:  # pragma: no cover
    def extract_one(x: Any, profile: str | None = None) -> np.ndarray:
        import numpy as np
        arr = np.asarray(x)
        if arr.ndim != 1:
            raise ValueError(f"extract_one requires a 1D array, got shape {arr.shape}")
        if arr.dtype not in (np.float64, np.float32):
            arr = arr.astype(np.float64)
        arr_2d = arr.reshape(1, -1)
        res = extract_features(arr_2d, profile=profile or "core33", n_jobs=1)
        return res[0]

from .chunked import extract_features_chunked
from .select import KymoraSelector, select_features
from .tune import tune

if TYPE_CHECKING:  # pragma: no cover
    import numpy as np
    import pandas as pd
    import polars as pl

__all__ = [
    "extract_features",
    "extract_one",
    "extract_features_mc",
    "extract_features_ragged",
    "extract_features_df",
    "extract_features_mc_df",
    "extract_features_chunked",
    "extract_features_polars",
    "sliding_features",
    "StreamingExtractor",
    "MultiStreamExtractor",
    "feature_names",
    "feature_names_mc",
    "list_profiles",
    "describe_feature",
    "select_features",
    "KymoraSelector",
    "tune",
    "__version__",
]


def _resolve_version() -> str:
    from importlib.metadata import PackageNotFoundError, version

    try:
        return version("kymora")
    except PackageNotFoundError:
        return "0.0.0+unknown"


#: Package version, read from the installed distribution metadata.
__version__: str = _resolve_version()


def extract_features_df(
    X: "np.ndarray | Sequence[np.ndarray]",
    profile: str | None = None,
    features: Sequence[str] | None = None,
    n_jobs: int | None = None,
    out: "np.ndarray | None" = None,
    views: Sequence[str] | None = None,
    nan_policy: str | None = None,
    contiguous: str | None = None,
) -> "pd.DataFrame":
    """Same as :func:`extract_features`, returned as a labeled DataFrame.

    Columns are :func:`feature_names` in order; the index is a plain
    ``RangeIndex`` over the input series.
    """
    try:
        import pandas as pd
    except ImportError as exc:  # pragma: no cover - depends on environment
        raise ImportError(
            "extract_features_df requires pandas, which kymora does not "
            'install by default. Install it with: pip install "kymora[pandas]"'
        ) from exc

    values: Any = extract_features(
        X,
        profile=profile,
        features=features,
        n_jobs=n_jobs,
        out=out,
        views=views,
        nan_policy=nan_policy,
        contiguous=contiguous,
    )
    cols = feature_names(profile=profile, features=features, views=views)
    return pd.DataFrame(values, columns=cols)


def extract_features_polars(
    X: Any,
    profile: str | None = None,
    features: Sequence[str] | None = None,
    n_jobs: int | None = None,
    views: Sequence[str] | None = None,
    nan_policy: str | None = None,
    contiguous: str | None = None,
) -> "pl.DataFrame":
    """Same as :func:`extract_features`, returned as a native Polars DataFrame.

    Accepts 2D NumPy array, Polars DataFrame, or PyArrow Table. Output is
    constructed without intermediate copies.
    """
    try:
        import polars as pl
        import numpy as np
    except ImportError as exc:  # pragma: no cover
        raise ImportError(
            "extract_features_polars requires polars: "
            'pip install "kymora[polars]"'
        ) from exc

    if isinstance(X, pl.DataFrame):
        X_arr = np.ascontiguousarray(X.to_numpy(), dtype=np.float64)
    elif hasattr(X, "to_pandas"):
        X_arr = np.ascontiguousarray(X.to_pandas().to_numpy(), dtype=np.float64)
    elif hasattr(X, "to_numpy"):
        X_arr = np.ascontiguousarray(X.to_numpy(), dtype=np.float64)
    else:
        X_arr = X

    values = extract_features(
        X_arr,
        profile=profile,
        features=features,
        n_jobs=n_jobs,
        views=views,
        nan_policy=nan_policy,
        contiguous=contiguous,
    )
    cols = feature_names(profile=profile, features=features, views=views)
    return pl.from_numpy(values, schema=cols)


def extract_features_mc_df(
    X: "np.ndarray | Sequence[np.ndarray]",
    profile: str | None = None,
    features: Sequence[str] | None = None,
    cross: bool = True,
    max_pairs: int = 8,
    n_jobs: int | None = None,
    views: Sequence[str] | None = None,
    nan_policy: str | None = None,
    contiguous: str | None = None,
) -> "pd.DataFrame":
    """Extract multichannel and cross-channel features returned as a labeled DataFrame."""
    try:
        import pandas as pd
    except ImportError as exc:  # pragma: no cover - depends on environment
        raise ImportError(
            "extract_features_mc_df requires pandas, which kymora does not "
            'install by default. Install it with: pip install "kymora[pandas]"'
        ) from exc

    values = extract_features_mc(
        X,
        profile=profile,
        features=features,
        cross=cross,
        max_pairs=max_pairs,
        n_jobs=n_jobs,
        views=views,
        nan_policy=nan_policy,
        contiguous=contiguous,
    )
    if hasattr(X, "shape") and len(X.shape) == 3:
        n_channels = X.shape[1]
    else:
        n_channels = len(X[0])

    cols = feature_names_mc(
        n_channels,
        profile=profile,
        features=features,
        cross=cross,
        max_pairs=max_pairs,
        views=views,
    )
    return pd.DataFrame(values, columns=cols)
