"""Tests for kymora.feature_extraction subpackage."""

import numpy as np
import pytest
import kymora
from kymora.feature_extraction import (
    calc_features,
    extract_by_domain,
    get_features_by_domain,
    load_json,
    time_series_features_extractor,
    STATISTICAL_FEATURES,
    TEMPORAL_FEATURES,
    SPECTRAL_FEATURES,
    FRACTAL_FEATURES,
)


def test_feature_extraction_domain_discovery():
    cfg = get_features_by_domain()
    assert "statistical" in cfg
    assert "temporal" in cfg
    assert "spectral" in cfg
    assert "fractal" in cfg

    cfg_stat = get_features_by_domain("statistical")
    assert "statistical" in cfg_stat
    assert len(cfg_stat["statistical"]) > 30

    cfg_spec = get_features_by_domain("spectral")
    assert "spectral" in cfg_spec
    assert "MFCC" in cfg_spec["spectral"] or "mfcc_0" in cfg_spec["spectral"]


def test_time_series_features_extractor_execution():
    X = np.random.randn(5, 200)
    cfg = get_features_by_domain("statistical")
    df = time_series_features_extractor(cfg, X, fs=100.0)
    assert df.shape[0] == 5
    assert df.shape[1] > 20
    assert np.all(np.isfinite(df.to_numpy()))


def test_calc_features_alias():
    X = np.random.randn(4, 150)
    cfg = get_features_by_domain("temporal")
    df = calc_features(cfg, X, fs=50.0)
    assert df.shape[0] == 4
    assert df.shape[1] >= 10


def test_extract_by_domain_all():
    X = np.random.randn(3, 250)
    res_arr = extract_by_domain(X, domain="all", as_df=False)
    assert isinstance(res_arr, np.ndarray)
    assert res_arr.shape[0] == 3
    assert res_arr.shape[1] > 100

    res_df = extract_by_domain(X, domain="all", as_df=True)
    assert res_df.shape[0] == 3
    assert res_df.shape[1] > 100
