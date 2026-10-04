"""Deprecated alias for :mod:`kymora`.

The canonical import name is ``kymora`` (installed via
``pip install kymora``). This module exists only for backwards
compatibility, emits a :class:`DeprecationWarning` on first import, and will
be removed no earlier than version 0.8.0.
"""

from __future__ import annotations

import warnings as _warnings

_warnings.warn(
    "The 'tsxtractor' import name is deprecated and will be removed no earlier "
    "than version 0.8.0; use 'import kymora' instead "
    "(pip install kymora).",
    DeprecationWarning,
    stacklevel=2,
)

from kymora import (  # noqa: E402
    KymoraSelector,
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
    "KymoraSelector",
    "TsxSelector",
    "tune",
    "__version__",
]
