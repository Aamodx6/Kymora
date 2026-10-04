"""Deprecated alias for :mod:`tsxtract`.

The canonical import name is ``tsxtract`` (installed via
``pip install tsxtract-rs``). This module exists only for backwards
compatibility, emits a :class:`DeprecationWarning` on first import, and will
be removed no earlier than version 0.7.0.
"""

from __future__ import annotations

import warnings as _warnings

_warnings.warn(
    "The 'tsxtractor' import name is deprecated and will be removed no earlier "
    "than version 0.7.0; use 'import tsxtract' instead "
    "(pip install tsxtract-rs).",
    DeprecationWarning,
    stacklevel=2,
)

from tsxtract import (  # noqa: E402
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
