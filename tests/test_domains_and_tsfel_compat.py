import numpy as np
import pytest
import kymora
from kymora.compat import tsfel as km_tsfel


def test_domains_discovery():
    cfg = kymora.get_features_by_domain()
    assert "statistical" in cfg
    assert "temporal" in cfg
    assert "spectral" in cfg
    
    cfg_stat = kymora.get_features_by_domain("statistical")
    assert len(cfg_stat["statistical"]) > 30
    
    cfg_all = kymora.get_features_by_domain("all")
    assert "fractal" in cfg_all
    assert len(cfg_all["statistical"]) + len(cfg_all["temporal"]) + len(cfg_all["spectral"]) + len(cfg_all["fractal"]) > 100


def test_extract_by_domain_shapes():
    rng = np.random.default_rng(42)
    X = rng.standard_normal((15, 250))
    
    # Statistical
    res_s = kymora.extract_features(X, domain="statistical")
    assert res_s.shape[0] == 15
    assert res_s.shape[1] > 30
    assert np.all(np.isfinite(res_s))
    
    # Temporal
    res_t = kymora.extract_features(X, domain="temporal")
    assert res_t.shape[0] == 15
    assert res_t.shape[1] >= 15
    
    # Spectral
    res_spec = kymora.extract_features(X, domain="spectral")
    assert res_spec.shape[0] == 15
    assert res_spec.shape[1] > 10
    
    # All
    df_all = kymora.extract_features_df(X, domain="all")
    assert df_all.shape[0] == 15
    assert df_all.shape[1] > 100
    assert isinstance(df_all.columns[0], str)


def test_tsfel_compat_extractor():
    rng = np.random.default_rng(123)
    X = rng.standard_normal((10, 300))
    
    cfg = km_tsfel.get_features_by_domain("statistical")
    df = km_tsfel.time_series_features_extractor(cfg, X)
    assert df.shape[0] == 10
    assert df.shape[1] > 30
    
    # Unsupervised correlation filtering
    clean_df = km_tsfel.correlated_features(df, threshold=0.90)
    assert clean_df.shape[0] == 10
    assert clean_df.shape[1] <= df.shape[1]


def test_multichannel_compat():
    rng = np.random.default_rng(999)
    # Multichannel sensor signal: (500 time steps, 3 axes)
    X_sensor = rng.standard_normal((500, 3))
    df = km_tsfel.time_series_features_extractor("statistical", X_sensor)
    assert df.shape[0] == 1
    # Check that columns have channel prefixes like '0_mean', '1_mean', '2_mean'
    cols = list(df.columns)
    assert any(c.startswith("0_") for c in cols)
    assert any(c.startswith("1_") for c in cols)
    assert any(c.startswith("2_") for c in cols)


def test_cepstral_and_wavelet_features():
    rng = np.random.default_rng(777)
    X = rng.standard_normal((8, 400))
    
    # Extract MFCC, LPCC, and Wavelet features
    feats = [
        "mean", "std",
        "mfcc_0", "mfcc_1", "mfcc_11",
        "lpcc_0", "lpcc_1", "lpcc_11",
        "wavelet_energy_scale_1", "wavelet_abs_mean_scale_1",
        "wavelet_std_scale_1", "wavelet_var_scale_1", "wavelet_entropy"
    ]
    df = kymora.extract_features_df(X, features=feats)
    assert df.shape == (8, len(feats))
    assert np.all(np.isfinite(df.to_numpy()))
    assert list(df.columns) == feats


def test_real_world_dataset_extraction():
    import sys
    from pathlib import Path
    bench_dir = Path(__file__).resolve().parent.parent
    if str(bench_dir) not in sys.path:
        sys.path.insert(0, str(bench_dir))
    from benchmarks.datasets.real import load_ucr_dataset
    
    # Test on real patient ECG heartbeat dataset
    X_ecg, y_ecg = load_ucr_dataset("ECG200", "TRAIN")
    assert X_ecg.shape == (100, 96)
    
    # 1. Test extraction across all domains
    df_stat = kymora.extract_features_df(X_ecg[:10], domain="statistical")
    assert df_stat.shape[0] == 10
    assert df_stat.shape[1] > 30
    assert np.all(np.isfinite(df_stat.to_numpy()))
    
    # 2. Test Cepstral (MFCC & LPCC) and Wavelet on real ECG signals
    audio_feats = [f"mfcc_{i}" for i in range(12)] + [f"lpcc_{i}" for i in range(12)] + [
        "wavelet_energy_scale_1", "wavelet_energy_scale_2", "wavelet_entropy"
    ]
    df_audio = kymora.extract_features_df(X_ecg[:10], features=audio_feats, fs=100.0)
    assert df_audio.shape == (10, len(audio_feats))
    assert np.all(np.isfinite(df_audio.to_numpy()))
    
    # 3. Test drop-in TSFEL replacement on real GunPoint video tracking dataset
    X_gun, y_gun = load_ucr_dataset("GunPoint", "TRAIN")
    cfg = km_tsfel.get_features_by_domain("statistical")
    df_gun = km_tsfel.time_series_features_extractor(cfg, X_gun[:10])
    assert df_gun.shape[0] == 10
    
    clean_gun = km_tsfel.correlated_features(df_gun, threshold=0.90)
    assert clean_gun.shape[0] == 10
    assert clean_gun.shape[1] <= df_gun.shape[1]

