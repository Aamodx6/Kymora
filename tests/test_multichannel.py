"""Multichannel input surface (Phase 3.3).

- 3D `(n_samples, n_channels, length)` output is `(n, C * n_features + cross)`
  with `ch{c}__{feature}` per-channel blocks then cross columns.
- A list of 2D `(C, T_i)` arrays gives bit-identical results to the stacked
  3D equivalent and supports ragged lengths across samples.
- Labeled `extract_features_mc_df` columns match `feature_names_mc`.
"""

import numpy as np
import pytest

import kymora


def test_mc_output_layout_and_names():
    rng = np.random.default_rng(42)
    X = np.ascontiguousarray(rng.standard_normal((4, 3, 150)))
    feats = ["mean", "std", "kurtosis"]
    names = kymora.feature_names_mc(3, features=feats, cross=True)
    out = kymora.extract_features_mc(X, features=feats, cross=True)
    assert out.shape == (4, len(names))
    # per-channel blocks: ch{c}__{feature} in order
    assert names[:6] == [
        "ch0__mean", "ch0__std", "ch0__kurtosis",
        "ch1__mean", "ch1__std", "ch1__kurtosis",
    ]
    # per-channel values equal the batch pipeline on that channel
    for c in range(3):
        want = kymora.extract_features(np.ascontiguousarray(X[:, c, :]), features=feats)
        np.testing.assert_array_equal(out[:, c * 3 : (c + 1) * 3], want)


def test_mc_list_of_2d_matches_stacked():
    rng = np.random.default_rng(1)
    X = np.ascontiguousarray(rng.standard_normal((3, 4, 100)))
    elems = [np.ascontiguousarray(X[i]) for i in range(3)]
    for kwargs in ({}, {"cross": False}, {"features": ["mean", "var"]}, {"max_pairs": 2}):
        a = kymora.extract_features_mc(X, **kwargs)
        b = kymora.extract_features_mc(elems, **kwargs)
        np.testing.assert_array_equal(a, b)


def test_mc_list_ragged_lengths():
    rng = np.random.default_rng(2)
    lengths = [50, 100, 150]
    elems = [np.ascontiguousarray(rng.standard_normal((2, n))) for n in lengths]
    out = kymora.extract_features_mc(elems)
    names = kymora.feature_names_mc(2)
    assert out.shape == (3, len(names))
    for i, (el, n) in enumerate(zip(elems, lengths)):
        for c in range(2):
            want = kymora.extract_features(np.ascontiguousarray(el[c : c + 1, :]))[0]
            np.testing.assert_array_equal(out[i, c * 33 : (c + 1) * 33], want)


def test_mc_list_validation():
    rng = np.random.default_rng(3)
    good = np.ascontiguousarray(rng.standard_normal((2, 50)))
    with pytest.raises(ValueError, match="[Cc]hannels"):
        kymora.extract_features_mc(
            [good, np.ascontiguousarray(rng.standard_normal((3, 50)))]
        )
    with pytest.raises(ValueError):
        kymora.extract_features_mc([])
    # NOTE: Fortran-order elements are covered by the contiguity matrix in
    # test_input_surface.py (task 3.4); strict C-order is required everywhere.
    with pytest.raises(TypeError):
        kymora.extract_features_mc(np.zeros((2, 50), dtype=np.int64))


def test_mc_df_columns_match():
    rng = np.random.default_rng(4)
    elems = [np.ascontiguousarray(rng.standard_normal((2, n))) for n in (60, 90)]
    df = kymora.extract_features_mc_df(elems, features=["mean", "std"], cross=True)
    names = kymora.feature_names_mc(2, features=["mean", "std"], cross=True)
    assert list(df.columns) == names
    assert df.shape == (2, len(names))
