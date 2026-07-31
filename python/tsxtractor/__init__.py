"""tsxtractor — fast time-series feature extraction with a Rust core.

Usage:
    import numpy as np, tsxtractor
    X = np.random.randn(1000, 500)
    feats = tsxtractor.extract_features(X)   # (1000, n_features)
    names = tsxtractor.feature_names()

NaN policy: any NaN in a series makes all its features NaN (no silent imputation).
"""

from ._core import extract_features, feature_names, sliding_features

__all__ = ["extract_features", "sliding_features", "feature_names"]
__version__ = "0.1.0"
