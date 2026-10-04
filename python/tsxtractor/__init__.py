"""tsxtractor — fast time-series feature extraction with a Rust core.

Extracts curated statistical, temporal, spectral, multichannel, and multi-view
features from batches of time series. The Rust core takes zero-copy views of
numpy buffers, releases the GIL, and parallelizes across series with persistent
spin workers and Rayon.

Usage:
    import numpy as np, tsxtractor

    X = np.random.randn(1000, 500)
    feats = tsxtractor.extract_features(X)                      # (1000, 33) float64
    names = tsxtractor.feature_names()                          # stable column order
    df = tsxtractor.extract_features_df(X)                      # labeled DataFrame

    # Multi-view multiplicative extraction
    df_views = tsxtractor.extract_features_df(X, views=["raw", "diff", "znorm"])

    # Multichannel time series
    X_mc = np.random.randn(100, 4, 500)                         # (samples, channels, length)
    df_mc = tsxtractor.extract_features_mc_df(X_mc, cross=True)

    # Supervised feature selection
    selected_idx, report = tsxtractor.select_features(feats, y, task="auto")
"""

from __future__ import annotations

from typing import TYPE_CHECKING, Any, Sequence

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
from .select import TsxSelector, select_features
from .tune import tune

if TYPE_CHECKING:  # pragma: no cover
    import numpy as np
    import pandas as pd

__all__ = [
    "extract_features",
    "extract_features_mc",
    "extract_features_ragged",
    "extract_features_df",
    "extract_features_mc_df",
    "sliding_features",
    "StreamingExtractor",
    "MultiStreamExtractor",
    "feature_names",
    "feature_names_mc",
    "list_profiles",
    "describe_feature",
    "select_features",
    "TsxSelector",
    "tune",
    "__version__",
]


def _resolve_version() -> str:
    from importlib.metadata import PackageNotFoundError, version

    for dist_name in ("tsxtract-rs", "tsxtractor", "tsxtract"):
        try:
            return version(dist_name)
        except PackageNotFoundError:
            continue
    return "0.5.0"


#: Package version, read from the installed distribution metadata.
__version__: str = _resolve_version()


def extract_features_df(
    X: "np.ndarray | Sequence[np.ndarray]",
    profile: str | None = None,
    features: Sequence[str] | None = None,
    n_jobs: int | None = None,
    out: "np.ndarray | None" = None,
    views: Sequence[str] | None = None,
) -> "pd.DataFrame":
    """Same as :func:`extract_features`, returned as a labeled DataFrame.

    Columns are :func:`feature_names` in order; the index is a plain
    ``RangeIndex`` over the input series.
    """
    try:
        import pandas as pd
    except ImportError as exc:  # pragma: no cover - depends on environment
        raise ImportError(
            "extract_features_df requires pandas, which tsxtract-rs does not "
            'install by default. Install it with: pip install "tsxtract-rs[pandas]"'
        ) from exc

    values: Any = extract_features(
        X,
        profile=profile,
        features=features,
        n_jobs=n_jobs,
        out=out,
        views=views,
    )
    cols = feature_names(profile=profile, features=features, views=views)
    return pd.DataFrame(values, columns=cols)


def extract_features_mc_df(
    X: "np.ndarray | Sequence[np.ndarray]",
    profile: str | None = None,
    features: Sequence[str] | None = None,
    cross: bool = True,
    max_pairs: int = 8,
    n_jobs: int | None = None,
    views: Sequence[str] | None = None,
) -> "pd.DataFrame":
    """Extract multichannel and cross-channel features returned as a labeled DataFrame."""
    try:
        import pandas as pd
    except ImportError as exc:  # pragma: no cover - depends on environment
        raise ImportError(
            "extract_features_mc_df requires pandas, which tsxtract-rs does not "
            'install by default. Install it with: pip install "tsxtract-rs[pandas]"'
        ) from exc

    values = extract_features_mc(
        X,
        profile=profile,
        features=features,
        cross=cross,
        max_pairs=max_pairs,
        n_jobs=n_jobs,
        views=views,
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
