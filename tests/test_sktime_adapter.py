"""sktime adapter check (Phase 4.3). Optional: skips without sktime/pandas."""

import numpy as np
import pytest

sktime = pytest.importorskip("sktime")
pytest.importorskip("pandas")

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "docs" / "examples"))

from sktime_adapter import KymoraFeatures

import kymora


def _panel(n=6, length=80, seed=0):
    rng = np.random.default_rng(seed)
    return np.ascontiguousarray(rng.standard_normal((n, 1, length)))


def test_adapter_panel_to_primitives():
    X = _panel()
    tr = KymoraFeatures(profile="minimal")
    out = tr.fit_transform(X)
    assert list(out.columns) == kymora.feature_names(profile="minimal")
    assert out.shape == (6, 10)
    # Values equal the direct call on the unwrapped panel.
    want = kymora.extract_features(np.ascontiguousarray(X[:, 0, :]), profile="minimal")
    np.testing.assert_array_equal(np.asarray(out), want)


def test_adapter_feeds_sklearn_pipeline():
    from sklearn.linear_model import LogisticRegression
    from sklearn.pipeline import Pipeline as SkPipeline
    from sklearn.preprocessing import StandardScaler

    X = _panel(n=10)
    y = np.array([0, 1] * 5)
    feats = KymoraFeatures(profile="minimal").fit_transform(X)
    pipe = SkPipeline([("sc", StandardScaler()), ("clf", LogisticRegression())])
    pipe.fit(feats, y)
    assert pipe.predict(feats).shape == (10,)


def test_adapter_multivariate_channels():
    X = np.ascontiguousarray(np.random.default_rng(0).standard_normal((4, 2, 50)))
    out = KymoraFeatures().fit_transform(X)
    assert list(out.columns) == kymora.feature_names_mc(2, cross=False)
    assert out.shape == (4, 66)
