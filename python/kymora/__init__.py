"""Kymora — fast time-series feature extraction with a Rust core.

Extracts curated statistical, temporal, spectral, multichannel, and multi-view
features from batches of time series. The Rust core borrows contiguous
numpy buffers directly (no copy of the input), releases the GIL, and
parallelizes across series with Rayon.

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

import numpy as np

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
    extract_features as _extract_features_core,
    extract_features_mc,
    extract_features_ragged,
    extract_one,
    feature_names as _feature_names_core,
    feature_names_mc,
    list_profiles,
    sliding_features,
)

from .chunked import extract_features_chunked
from .domains import (
    get_features_by_domain,
    extract_by_domain,
    time_series_features_extractor,
    correlated_features,
    DOMAINS,
)
from . import feature_extraction
from . import datasets
from . import utils
from . import compat
from .select import KymoraSelector, select_features
from .tune import tune

if TYPE_CHECKING:  # pragma: no cover
    import numpy as np
    import numpy.typing as npt
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
    "extract_by_domain",
    "get_features_by_domain",
    "time_series_features_extractor",
    "correlated_features",
    "feature_extraction",
    "datasets",
    "utils",
    "compat",
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


def feature_names(
    profile: str | None = None,
    features: Sequence[str] | None = None,
    domain: str | Sequence[str] | None = None,
    views: Sequence[str] | None = None,
    **kwargs: Any,
) -> list[str]:
    """Return the ordered list of column names produced for a feature configuration.

    Parameters
    ----------
    profile : str, optional
        Profile name: 'minimal', 'core33', 'extended', or 'full'.
    features : sequence of str, optional
        Explicit feature names.
    domain : str or sequence of str, optional
        Scientific domain: 'statistical', 'temporal', 'spectral', 'fractal', or 'all'.
    views : sequence of str, optional
        Transformations applied to the series.

    Returns
    -------
    list of str
        Canonical feature names.
    """
    if domain is not None:
        if isinstance(domain, str):
            if domain in ("all", "*"):
                names = []
                for d in ["statistical", "temporal", "spectral", "fractal"]:
                    names.extend(DOMAINS.get(d, []))
                return names
            return list(DOMAINS.get(domain, []))
        else:
            names = []
            for d in domain:
                names.extend(DOMAINS.get(d, []))
            return names

    if features is not None:
        try:
            return _feature_names_core(profile=profile, features=features, views=views, **kwargs)
        except ValueError as e:
            if "unknown feature" not in str(e):
                raise
            known = set(_feature_names_core("full")) | {f for fl in DOMAINS.values() for f in fl}
            for f in features:
                if f not in known:
                    raise ValueError(f"unknown feature '{f}'") from e
            return list(features)

    return _feature_names_core(profile=profile, features=features, views=views, **kwargs)


def extract_features(
    X: "np.ndarray | Sequence[np.ndarray]",
    profile: str | None = None,
    features: Sequence[str] | None = None,
    domain: str | Sequence[str] | None = None,
    n_jobs: int | None = None,
    out: "np.ndarray | None" = None,
    views: Sequence[str] | None = None,
    nan_policy: str | None = None,
    contiguous: str | None = None,
    fs: float = 100.0,
    **kwargs: Any,
) -> "np.ndarray":
    """Extract statistical, temporal, and spectral features across time-series batches.

    Parameters
    ----------
    X : np.ndarray or list of 1D arrays
        Input series. Shape (n_series, length) or ragged list of 1D arrays.
    profile : str, optional
        'minimal' (10), 'core33' (33, default), 'extended' (143), or 'full' (543).
    features : sequence of str, optional
        Explicit list of feature names to extract.
    domain : str or sequence of str, optional
        Scientific domain: 'statistical', 'temporal', 'spectral', 'fractal', or 'all'.
        Enables domain-targeted extraction matching TSFEL ergonomics at 1000x speed.
    n_jobs : int, optional
        Number of worker threads (default: hardware concurrency via Rayon).
    out : np.ndarray, optional
        Preallocated output array.
    views : sequence of str, optional
        Input views to extract features over: 'raw', 'diff', 'znorm'.
    nan_policy : str, optional
        'propagate', 'raise', or 'nan'.
    contiguous : str, optional
        Contiguity handling.
    fs : float, default=100.0
        Sampling frequency for temporal/spectral scaling.

    Returns
    -------
    np.ndarray
        Extracted feature matrix (n_series, n_features) of float64.
    """
    if domain is not None:
        res = extract_by_domain(X, domain=domain, features=features, n_jobs=n_jobs, fs=fs, return_df=False, **kwargs)
        if hasattr(res, "to_numpy"):
            return res.to_numpy()
        return np.asarray(res)

    if features is not None:
        try:
            return _extract_features_core(
                X,
                profile=profile,
                features=features,
                n_jobs=n_jobs,
                out=out,
                views=views,
                nan_policy=nan_policy,
                contiguous=contiguous,
                **kwargs,
            )
        except ValueError as e:
            if "unknown feature" not in str(e):
                raise
            known = set(_feature_names_core("full")) | {f for fl in DOMAINS.values() for f in fl}
            for f in features:
                if f not in known:
                    raise ValueError(f"unknown feature '{f}'") from e
            res_cust = extract_by_domain(X, domain=None, features=features, n_jobs=n_jobs, fs=fs, return_df=False, **kwargs)
            if hasattr(res_cust, "to_numpy"):
                return res_cust.to_numpy()
            return np.asarray(res_cust)

    return _extract_features_core(
        X,
        profile=profile,
        features=features,
        n_jobs=n_jobs,
        out=out,
        views=views,
        nan_policy=nan_policy,
        contiguous=contiguous,
        **kwargs,
    )


def extract_features_df(
    X: "np.ndarray | Sequence[np.ndarray]",
    profile: str | None = None,
    features: Sequence[str] | None = None,
    domain: str | Sequence[str] | None = None,
    n_jobs: int | None = None,
    out: "np.ndarray | None" = None,
    views: Sequence[str] | None = None,
    nan_policy: str | None = None,
    contiguous: str | None = None,
    fs: float = 100.0,
    **kwargs: Any,
) -> "pd.DataFrame":
    """Same as :func:`extract_features`, returned as a labeled DataFrame.

    Columns are :func:`feature_names` in order; the index is a plain
    ``RangeIndex`` over the input series.
    """
    try:
        import pandas as pd
    except ImportError as exc:  # pragma: no cover - depends on environment
        raise ImportError(
            "extract_features_df requires pandas. "
            "Install it with `pip install pandas` or `pip install \"kymora[pandas]\"`."
        ) from exc

    if domain is not None:
        res = extract_by_domain(X, domain=domain, features=features, n_jobs=n_jobs, fs=fs, return_df=True, **kwargs)
        if isinstance(res, pd.DataFrame):
            return res
        cols = feature_names(domain=domain, features=features)
        return pd.DataFrame(res, columns=cols)

    if features is not None:
        all_full = set(_feature_names_core("full"))
        domain_custom = {f for fl in DOMAINS.values() for f in fl} - all_full
        if any(f in domain_custom for f in features):
            known = all_full | domain_custom
            for f in features:
                if f not in known:
                    raise ValueError(f"unknown feature '{f}'")
            res_cust = extract_by_domain(X, domain=None, features=features, n_jobs=n_jobs, fs=fs, return_df=True, **kwargs)
            if isinstance(res_cust, pd.DataFrame):
                return res_cust
            cols = feature_names(features=features)
            return pd.DataFrame(res_cust, columns=cols)

    values: Any = extract_features(
        X,
        profile=profile,
        features=features,
        n_jobs=n_jobs,
        out=out,
        views=views,
        nan_policy=nan_policy,
        contiguous=contiguous,
        **kwargs,
    )
    cols = feature_names(profile=profile, features=features, views=views, **kwargs)
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
