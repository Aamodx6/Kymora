"""Kymora Feature Extraction Subpackage.

Provides scientific domain feature configurations and extraction engines
compatible with TSFEL workflows.
"""

from .calc_features import (
    calc_features,
    extract_by_domain,
    time_series_features_extractor,
)
from .features import (
    ALL_DOMAINS,
    FRACTAL_CORE,
    FRACTAL_EXTENDED,
    FRACTAL_FEATURES,
    SPECTRAL_CORE,
    SPECTRAL_EXTENDED,
    SPECTRAL_FEATURES,
    STATISTICAL_CORE,
    STATISTICAL_EXTENDED,
    STATISTICAL_FEATURES,
    TEMPORAL_CORE,
    TEMPORAL_EXTENDED,
    TEMPORAL_FEATURES,
)
from .features_settings import get_features_by_domain, load_json

__all__ = [
    "time_series_features_extractor",
    "calc_features",
    "extract_by_domain",
    "get_features_by_domain",
    "load_json",
    "STATISTICAL_CORE",
    "STATISTICAL_EXTENDED",
    "STATISTICAL_FEATURES",
    "TEMPORAL_CORE",
    "TEMPORAL_EXTENDED",
    "TEMPORAL_FEATURES",
    "SPECTRAL_CORE",
    "SPECTRAL_EXTENDED",
    "SPECTRAL_FEATURES",
    "FRACTAL_CORE",
    "FRACTAL_EXTENDED",
    "FRACTAL_FEATURES",
    "ALL_DOMAINS",
]
