"""tsxtractor — fast time-series feature extraction with a Rust core.

Extracts 33 curated statistical, temporal, and spectral features from batches of
time series. The Rust core takes zero-copy views of your numpy buffers, releases
the GIL, and parallelizes across the *series* dimension with rayon — so the
speedup shows up on batches, not on a single short series.

Usage:
    import numpy as np, tsxtractor

    X = np.random.randn(1000, 500)
    feats = tsxtractor.extract_features(X)      # (1000, 33) float64
    names = tsxtractor.feature_names()          # stable column order
    df = tsxtractor.extract_features_df(X)      # same, as a labeled DataFrame

Error model — two separate categories:

* Structural problems raise an exception: no series at all, a zero-length
  series, a non-contiguous array, ``window``/``stride`` < 1, or ``window``
  longer than the series all raise ``ValueError``; a wrong dtype or shape raises
  ``TypeError``.
* NaN is a value, not an error. Any NaN in a series makes all 33 of that
  series' features NaN (no silent imputation). Features that are individually
  undefined for an otherwise-valid series — autocorrelation or spectral features
  of a constant series, change features of a length-1 series — are NaN on their
  own while the rest compute normally.

``feature_names()`` order is a stability guarantee: column ``i`` means the same
feature for every release within a major version.
"""

from __future__ import annotations

from typing import TYPE_CHECKING, Any, Sequence

from ._core import (
    StreamingExtractor,
    describe_feature,
    extract_features,
    extract_features_ragged,
    feature_names,
    list_profiles,
    sliding_features,
)

if TYPE_CHECKING:  # pragma: no cover
    import numpy as np
    import pandas as pd

__all__ = [
    "extract_features",
    "extract_features_ragged",
    "extract_features_df",
    "sliding_features",
    "StreamingExtractor",
    "feature_names",
    "list_profiles",
    "describe_feature",
    "__version__",
]


def _resolve_version() -> str:
    from importlib.metadata import PackageNotFoundError, version

    for dist_name in ("tsxtract-rs", "tsxtractor", "tsxtract"):
        try:
            return version(dist_name)
        except PackageNotFoundError:
            continue
    return "0.4.0"


#: Package version, read from the installed distribution metadata (which maturin
#: fills from ``pyproject.toml``/``Cargo.toml`` at build time).
__version__: str = _resolve_version()


def extract_features_df(
    X: "np.ndarray | Sequence[np.ndarray]",
    profile: str | None = None,
    features: Sequence[str] | None = None,
    n_jobs: int | None = None,
    out: "np.ndarray | None" = None,
) -> "pd.DataFrame":
    """Same as :func:`extract_features`, returned as a labeled DataFrame.

    Columns are :func:`feature_names` in order; the index is a plain
    ``RangeIndex`` over the input series.

    Requires pandas, which is an optional extra::

        pip install "tsxtract-rs[pandas]"

    Args:
        X: 2D float64/float32 array of shape ``(n_series, length)``, or a sequence of 1D
            arrays for ragged series.
        profile: Optional feature profile name ("minimal", "core33", "extended", "full").
        features: Optional explicit sequence of feature names or aliases.
        n_jobs: Optional number of worker threads to use. None uses all available cores.
        out: Optional pre-allocated C-contiguous float64 array.

    Returns:
        A ``(n_series, n_features)`` DataFrame of float64 features.

    Raises:
        ImportError: if pandas is not installed.
        ValueError: on structural problems with the input (see module docstring).
        TypeError: on a wrong dtype or shape.
    """
    try:
        import pandas as pd
    except ImportError as exc:  # pragma: no cover - depends on environment
        raise ImportError(
            "extract_features_df requires pandas, which tsxtract-rs does not "
            'install by default. Install it with: pip install "tsxtract-rs[pandas]"'
        ) from exc

    values: Any = extract_features(X, profile=profile, features=features, n_jobs=n_jobs, out=out)
    return pd.DataFrame(values, columns=feature_names(profile=profile, features=features))
