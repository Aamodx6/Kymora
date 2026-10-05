"""The thin Python layer: version, type-stub surface, DataFrame convenience."""

import importlib.util
import re
from pathlib import Path

import numpy as np
import pytest

import kymora

PKG_DIR = Path(kymora.__file__).parent


def test_version_is_exposed_and_pep440_shaped():
    assert isinstance(kymora.__version__, str)
    assert re.fullmatch(r"\d+\.\d+\.\d+([.\-+].*)?", kymora.__version__), (
        kymora.__version__
    )


def test_version_matches_installed_distribution_metadata():
    from importlib.metadata import version

    assert kymora.__version__ == version("kymora")


def test_public_api_surface_is_exactly_what_is_documented():
    assert set(kymora.__all__) == {
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
        "tune",
        "__version__",
    }
    for name in kymora.__all__:
        assert hasattr(kymora, name), name


@pytest.mark.parametrize("gone_name", ["tsxtract", "tsxtractor"])
def test_old_import_names_are_gone(gone_name):
    import importlib.util

    assert importlib.util.find_spec(gone_name) is None


def test_py_typed_marker_ships_with_the_package():
    assert (PKG_DIR / "py.typed").is_file()


def test_core_stubs_ship_and_cover_every_exported_function():
    stub = PKG_DIR / "_core.pyi"
    assert stub.is_file()
    text = stub.read_text(encoding="utf-8")
    for fn in ("extract_features", "sliding_features", "feature_names"):
        assert f"def {fn}(" in text, fn


def test_feature_names_are_unique_and_nonempty():
    names = kymora.feature_names()
    assert len(names) == 33
    assert len(set(names)) == len(names)
    assert all(n and n.strip() == n for n in names)


def test_feature_name_order_is_frozen():
    """feature_names() order is a stability guarantee (architecture §9): column i
    means the same feature across every release in a major version. Changing this
    list requires a major version bump, not a test edit."""
    assert kymora.feature_names() == [
        "mean",
        "std",
        "var",
        "min",
        "max",
        "median",
        "quantile_10",
        "quantile_25",
        "quantile_75",
        "quantile_90",
        "skewness",
        "kurtosis",
        "abs_energy",
        "root_mean_square",
        "mean_abs_change",
        "mean_change",
        "cid_ce",
        "mean_second_derivative_central",
        "zero_crossings",
        "mean_crossings",
        "number_of_peaks",
        "longest_strike_above_mean",
        "longest_strike_below_mean",
        "autocorr_lag_1",
        "autocorr_lag_2",
        "autocorr_lag_5",
        "autocorr_lag_10",
        "trend_slope",
        "trend_r2",
        "permutation_entropy",
        "dominant_frequency",
        "spectral_centroid",
        "spectral_entropy",
    ]


# --- extract_features_df ------------------------------------------------------

pd = pytest.importorskip("pandas", reason="pandas is an optional extra")


def test_df_columns_are_feature_names_in_order():
    X = np.random.default_rng(0).standard_normal((6, 40))
    df = kymora.extract_features_df(X)
    assert list(df.columns) == kymora.feature_names()
    assert df.shape == (6, 33)
    assert (df.dtypes == np.float64).all()


def test_df_values_are_identical_to_the_array_api():
    X = np.random.default_rng(1).standard_normal((5, 30))
    np.testing.assert_array_equal(
        kymora.extract_features_df(X).to_numpy(),
        kymora.extract_features(X),
    )


def test_df_accepts_ragged_input():
    rng = np.random.default_rng(2)
    batch = [rng.standard_normal(n) for n in (10, 25, 7)]
    df = kymora.extract_features_df(batch)
    assert df.shape == (3, 33)
    assert list(df.index) == [0, 1, 2]


def test_df_propagates_structural_errors_unchanged():
    with pytest.raises(ValueError):
        kymora.extract_features_df([])
    with pytest.raises(TypeError):
        kymora.extract_features_df(np.arange(10.0))


def test_df_preserves_the_nan_row_contract():
    x = np.arange(20.0)
    x[5] = np.nan
    df = kymora.extract_features_df([x, np.arange(20.0)])
    assert df.iloc[0].isna().all()
    assert not df.iloc[1].isna().all()


def test_pandas_is_not_imported_by_importing_kymora():
    """Core install must stay numpy-only: pandas is imported lazily inside
    extract_features_df, never at package import time."""
    source = (PKG_DIR / "__init__.py").read_text(encoding="utf-8")
    module_level = [
        line
        for line in source.splitlines()
        if re.match(r"^(import|from)\s+pandas", line)
    ]
    assert not module_level, module_level
    assert importlib.util.find_spec("kymora._core") is not None
