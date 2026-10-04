"""tsxtract — fast time-series feature extraction with a Rust core.

Convenience alias for tsxtractor.
"""
from __future__ import annotations

import tsxtractor
from tsxtractor import (
    MultiStreamExtractor,
    StreamingExtractor,
    TsxSelector,
    __version__,
    describe_feature,
    extract_features,
    extract_features_df,
    extract_features_mc,
    extract_features_mc_df,
    extract_features_ragged,
    feature_names,
    feature_names_mc,
    list_profiles,
    select_features,
    sliding_features,
    tune,
)

__all__ = [
    "extract_features",
    "extract_features_mc",
    "extract_features_df",
    "extract_features_mc_df",
    "extract_features_ragged",
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
