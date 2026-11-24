"""Scientific domain discovery and feature extraction orchestrator for Kymora.

Provides domain categorization ('statistical', 'temporal', 'spectral', 'fractal', 'all'),
and backward-compatible aliases for feature_extraction and utils subpackages.
"""

from __future__ import annotations

from typing import Any, Dict, List, Optional, Sequence, Union
import numpy as np

from . import _core
from .feature_extraction import (
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
    calc_features,
    extract_by_domain,
    get_features_by_domain,
    time_series_features_extractor,
)
from .feature_extraction.features import compute_derived_features as _calc_derived_features
from .utils import correlated_features

DOMAINS = ALL_DOMAINS

__all__ = [
    "DOMAINS",
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
    "get_features_by_domain",
    "extract_by_domain",
    "time_series_features_extractor",
    "calc_features",
    "correlated_features",
]
