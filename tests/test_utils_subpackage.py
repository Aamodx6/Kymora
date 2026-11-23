"""Tests for kymora.utils subpackage."""

import numpy as np
import pandas as pd
import pytest
import kymora.utils as ku


def test_correlated_features_dataframe():
    rng = np.random.default_rng(42)
    x1 = rng.standard_normal(50)
    x2 = x1 * 1.0 + rng.standard_normal(50) * 1e-6  # r ~ 1.0
    x3 = rng.standard_normal(50)                     # independent

    df = pd.DataFrame({"feat_1": x1, "feat_2": x2, "feat_3": x3})
    clean = ku.correlated_features(df, threshold=0.95)
    assert clean.shape[1] == 2
    assert "feat_1" in clean.columns
    assert "feat_2" not in clean.columns
    assert "feat_3" in clean.columns


def test_correlated_features_numpy():
    rng = np.random.default_rng(42)
    x1 = rng.standard_normal((50, 1))
    x2 = x1 * 0.9999 + rng.standard_normal((50, 1)) * 1e-4
    x3 = rng.standard_normal((50, 1))

    mat = np.hstack([x1, x2, x3])
    clean = ku.correlated_features(mat, threshold=0.95)
    assert clean.shape[1] == 2
