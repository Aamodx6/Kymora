"""Benchmark tsxtractor vs tsfresh on synthetic data.

Usage: python benches/bench_vs_tsfresh.py [n_series] [n_timesteps]
"""
import sys
import time

import numpy as np
import tsxtractor


def main():
    n_series = int(sys.argv[1]) if len(sys.argv) > 1 else 5000
    n_steps = int(sys.argv[2]) if len(sys.argv) > 2 else 500

    rng = np.random.default_rng(0)
    X = rng.standard_normal((n_series, n_steps))

    # warmup + timed run
    tsxtractor.extract_features(X[:100])
    t0 = time.perf_counter()
    feats = tsxtractor.extract_features(X)
    t_rust = time.perf_counter() - t0
    n_feat = feats.shape[1]
    print(f"tsxtractor: {n_series} series x {n_steps} steps, "
          f"{n_feat} features: {t_rust:.3f}s", flush=True)

    try:
        import pandas as pd
        from tsfresh import extract_features as tsf_extract
        from tsfresh.feature_extraction import EfficientFCParameters
    except ImportError:
        print("tsfresh not installed; skipping comparison")
        return

    df = pd.DataFrame({
        "id": np.repeat(np.arange(n_series), n_steps),
        "value": X.ravel(),
    })
    t0 = time.perf_counter()
    tsf = tsf_extract(df, column_id="id",
                      default_fc_parameters=EfficientFCParameters(),
                      disable_progressbar=True)
    t_tsfresh = time.perf_counter() - t0
    print(f"tsfresh (EfficientFCParameters, {tsf.shape[1]} features): {t_tsfresh:.3f}s")
    print(f"speedup: {t_tsfresh / t_rust:.0f}x  "
          f"(per-feature: {t_tsfresh / tsf.shape[1] / (t_rust / n_feat):.0f}x)")


if __name__ == "__main__":
    main()
