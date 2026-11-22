import numpy as np
import pytest
import kymora as km

try:
    import polars as pl
except ImportError:
    pl = None


@pytest.mark.skipif(pl is None, reason="polars not installed")
def test_extract_features_polars_numpy():
    X = np.random.randn(10, 50)
    df = km.extract_features_polars(X)
    assert isinstance(df, pl.DataFrame)
    assert df.shape == (10, 33)
    assert df.columns == km.feature_names()

    # Values match numpy
    expected = km.extract_features(X)
    np.testing.assert_allclose(df.to_numpy(), expected)


@pytest.mark.skipif(pl is None, reason="polars not installed")
def test_extract_features_polars_from_polars_df():
    X = np.random.randn(10, 50)
    pl_in = pl.DataFrame(X)
    df = km.extract_features_polars(pl_in)
    assert isinstance(df, pl.DataFrame)
    assert df.shape == (10, 33)

    expected = km.extract_features(X)
    np.testing.assert_allclose(df.to_numpy(), expected)
