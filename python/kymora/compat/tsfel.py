"""Drop-in 1000x faster replacement module for TSFEL (Time Series Feature Extraction Library).

Allows existing TSFEL pipelines to run directly on Kymora with zero code changes:

    # Before:
    # import tsfel

    # After (up to 1,000x faster):
    from kymora.compat import tsfel

    cfg = tsfel.get_features_by_domain()
    features = tsfel.time_series_features_extractor(cfg, signal)
    clean_features = tsfel.correlated_features(features)
"""

from __future__ import annotations

from .. import datasets
from .. import feature_extraction
from .. import utils
from ..feature_extraction import (
    calc_features,
    extract_by_domain,
    get_features_by_domain,
    time_series_features_extractor,
)
from ..utils import correlated_features

__version__ = "0.3.0+kymora"

__all__ = [
    "get_features_by_domain",
    "time_series_features_extractor",
    "calc_features",
    "correlated_features",
    "extract_by_domain",
    "feature_extraction",
    "datasets",
    "utils",
    "__version__",
]
