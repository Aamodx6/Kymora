"""KymoraTransformer sklearn integration (Phase 4.1).

- Pipeline / clone / pickle / set_output(pandas|polars) behavior.
- Full `parametrize_with_checks` compliance; checks that cannot apply to a
  time-series panel transformer are xfailed with explicit reasons.
"""

import pickle

import numpy as np
import pytest

sklearn = pytest.importorskip("sklearn")
from sklearn.base import clone
from sklearn.pipeline import Pipeline
from sklearn.preprocessing import StandardScaler
from sklearn.utils.estimator_checks import parametrize_with_checks

from kymora.sklearn import KymoraTransformer


@pytest.fixture()
def panel():
    rng = np.random.default_rng(0)
    return np.ascontiguousarray(rng.standard_normal((20, 100)))


def test_fit_transform_names(panel):
    t = KymoraTransformer().fit(panel)
    assert t.n_output_features_ == 33
    out = t.transform(panel)
    assert out.shape == (20, 33)
    assert list(t.get_feature_names_out()) == list(
        __import__("kymora").feature_names()
    )


def test_profile_features_views(panel):
    t = KymoraTransformer(profile="minimal").fit(panel)
    assert t.transform(panel).shape == (20, 10)
    t = KymoraTransformer(features=["mean", "std"]).fit(panel)
    assert list(t.get_feature_names_out()) == ["mean", "std"]
    assert t.transform(panel).shape == (20, 2)


def test_clone_pickle(panel):
    t = KymoraTransformer(profile="minimal", n_jobs=2).fit(panel)
    assert clone(t).fit(panel).transform(panel).shape == (20, 10)
    t2 = pickle.loads(pickle.dumps(t))
    np.testing.assert_array_equal(t2.transform(panel), t.transform(panel))


def test_set_output(panel):
    pd = pytest.importorskip("pandas")
    t = KymoraTransformer().fit(panel)
    t.set_output(transform="pandas")
    df = t.transform(panel)
    assert isinstance(df, pd.DataFrame)
    assert list(df.columns) == list(t.get_feature_names_out())
    pl = pytest.importorskip("polars")
    t.set_output(transform="polars")
    lf = t.transform(panel)
    assert isinstance(lf, pl.DataFrame)
    assert lf.columns == list(t.get_feature_names_out())


def test_pipeline(panel):
    pipe = Pipeline(
        [("km", KymoraTransformer(profile="minimal")), ("sc", StandardScaler())]
    )
    out = pipe.fit_transform(panel)
    assert out.shape == (20, 10)


def test_nan_policy_raise(panel):
    bad = panel.copy()
    bad[3, 5] = np.nan
    with pytest.raises(ValueError, match="batch index 3"):
        KymoraTransformer(nan_policy="raise").fit_transform(bad)
    out = KymoraTransformer().fit_transform(bad)
    assert np.isnan(out[3]).all()


@parametrize_with_checks([KymoraTransformer()])
def test_estimator_checks(estimator, check):
    check(estimator)
