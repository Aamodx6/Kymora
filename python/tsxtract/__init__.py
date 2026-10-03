"""tsxtract — fast time-series feature extraction with a Rust core.

Convenience alias for tsxtractor.
"""
from __future__ import annotations

import tsxtractor
from tsxtractor import (
    StreamingExtractor,
    __version__,
    extract_features,
    extract_features_df,
    feature_names,
    sliding_features,
)

__all__ = [
    "extract_features",
    "extract_features_df",
    "sliding_features",
    "StreamingExtractor",
    "feature_names",
    "__version__",
]
