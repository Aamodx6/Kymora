"""Kymora Quickstart: High-Throughput Time-Series Feature Extraction.

Demonstrates:
1. Native profile extraction ('core33', 'extended', 'full') with Rust-native SIMD.
2. Domain-targeted extraction ('statistical', 'temporal', 'spectral', 'fractal').
3. Multi-view feature expansion ('raw', 'diff', 'znorm').
"""

import time
import kymora
from kymora.datasets import load_dataset


def main():
    print("=" * 75)
    print("KYMORA QUICKSTART: REAL-WORLD TIME SERIES EXTRACTION")
    print("=" * 75)

    # 1. Load real-world patient ECG heartbeats
    X_train, y_train, X_test, y_test = load_dataset("ECG200")
    print(f"Loaded ECG200: {X_train.shape[0]} train heartbeats, {X_test.shape[0]} test heartbeats (length {X_train.shape[1]})")

    # 2. Extract default profile (core33)
    t0 = time.perf_counter()
    df_core = kymora.extract_features_df(X_train, profile="core33")
    t_core = (time.perf_counter() - t0) * 1000.0
    print(f"\n[Profile 'core33']: Extracted {df_core.shape[1]} features for {len(X_train)} series in {t_core:.2f} ms")
    print("First 5 features:")
    print(df_core.iloc[:3, :5].round(4).to_string())

    # 3. Domain extraction (spectral & audio)
    t0 = time.perf_counter()
    df_spectral = kymora.extract_features_df(X_train, domain="spectral", fs=100.0)
    t_spec = (time.perf_counter() - t0) * 1000.0
    print(f"\n[Domain 'spectral']: Extracted {df_spectral.shape[1]} features in {t_spec:.2f} ms")
    print("Spectral columns preview:", list(df_spectral.columns)[:6])

    # 4. Multi-view feature expansion
    df_views = kymora.extract_features_df(X_train[:10], profile="minimal", views=["raw", "diff", "znorm"])
    print(f"\n[Multi-View]: Extracted {df_views.shape[1]} features across 3 views for 10 series")


if __name__ == "__main__":
    main()
