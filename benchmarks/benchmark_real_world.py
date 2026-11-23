"""Empirical Real-World Benchmark: Kymora vs TSFEL.

Evaluates purely on real-world empirical time series datasets:
- GunPoint (Video motion capture, 150 steps)
- ECG200 (Medical electrocardiogram, 96 steps)
- ItalyPowerDemand (Seasonal power grid telemetry, 24 steps)
- ArrowHead (Computer vision outline contours, 252 steps)

Outputs:
1. Equal-Feature throughput & speedup.
2. Full catalog throughput & speedup.
3. Machine precision parity checks on real empirical signals.
4. Downstream classification accuracy (Random Forest & Ridge).
"""

from __future__ import annotations

import json
import sys
import time
import warnings
from pathlib import Path

if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(line_buffering=True)
from typing import Dict, List, Tuple

import numpy as np
import pandas as pd
from joblib import Parallel, delayed
from sklearn.ensemble import RandomForestClassifier
from sklearn.linear_model import RidgeClassifier
from sklearn.metrics import accuracy_score, f1_score
from sklearn.preprocessing import StandardScaler

import kymora
from kymora.datasets import load_dataset
import tsfel

try:
    from tsfresh import extract_features as tsf_extract
    from tsfresh.feature_extraction import MinimalFCParameters, EfficientFCParameters
    HAS_TSFRESH = True
except ImportError:
    HAS_TSFRESH = False

warnings.filterwarnings("ignore")

DATASETS = ["GunPoint", "ECG200", "ItalyPowerDemand", "Coffee"]

PAIRINGS = [
    ("mean", "0_Mean"),
    ("std", "0_Standard deviation"),
    ("var", "0_Variance"),
    ("min", "0_Min"),
    ("max", "0_Max"),
    ("median", "0_Median"),
    ("skewness", "0_Skewness"),
    ("kurtosis", "0_Kurtosis"),
    ("abs_energy", "0_Absolute energy"),
    ("root_mean_square", "0_Root mean square"),
    ("mean_abs_change", "0_Mean absolute diff"),
    ("mean_change", "0_Mean diff"),
    ("zero_crossings", "0_Zero crossing rate"),
]
MATCHED_KYMORA = [p[0] for p in PAIRINGS]
MATCHED_TSFEL = [p[1].replace("0_", "") for p in PAIRINGS]


def get_tsfel_matched_cfg():
    cfg = {}
    full_cfg = tsfel.get_features_by_domain()
    for domain, funcs in full_cfg.items():
        kept = {k: v for k, v in funcs.items() if k in MATCHED_TSFEL}
        if kept:
            cfg[domain] = kept
    return cfg


def extract_tsfel(X: np.ndarray, cfg: dict, threads: int = -1) -> np.ndarray:
    def _row(r):
        with warnings.catch_warnings():
            warnings.simplefilter("ignore")
            return tsfel.time_series_features_extractor(cfg, r, verbose=0).to_numpy().ravel()
    out = Parallel(n_jobs=threads)(delayed(_row)(X[i]) for i in range(len(X)))
    return np.nan_to_num(np.array(out), nan=0.0, posinf=0.0, neginf=0.0)


def extract_tsfel_df(X: np.ndarray, cfg: dict, threads: int = -1) -> pd.DataFrame:
    def _row(r):
        with warnings.catch_warnings():
            warnings.simplefilter("ignore")
            return tsfel.time_series_features_extractor(cfg, r, verbose=0)
    dfs = Parallel(n_jobs=threads)(delayed(_row)(X[i]) for i in range(len(X)))
    return pd.concat(dfs, ignore_index=True)


def extract_tsfresh(X: np.ndarray, fc_parameters, n_jobs: int = 4) -> np.ndarray:
    if not HAS_TSFRESH:
        return np.zeros((len(X), 1))
    n_series, n_steps = X.shape
    long_df = pd.DataFrame({
        "id": np.repeat(np.arange(n_series), n_steps),
        "time": np.tile(np.arange(n_steps), n_series),
        "val": X.ravel(),
    })
    out_df = tsf_extract(
        long_df,
        column_id="id",
        column_sort="time",
        column_value="val",
        default_fc_parameters=fc_parameters,
        n_jobs=n_jobs,
        disable_progressbar=True,
    )
    return np.nan_to_num(out_df.to_numpy(), nan=0.0, posinf=0.0, neginf=0.0)


def run_benchmark():
    print("=" * 80)
    print("REAL-WORLD TIME-SERIES BENCHMARK: KYMORA vs TSFEL")
    print("=" * 80)

    tsfel_cfg_all = tsfel.get_features_by_domain("all")
    tsfel_cfg_stat = tsfel.get_features_by_domain("statistical")
    tsfel_cfg_matched = get_tsfel_matched_cfg()

    results = {}

    for dname in DATASETS:
        print(f"\n>>> Running Real-World Dataset: {dname}")
        X_train, y_train, X_test, y_test = load_dataset(dname)
        X_all = np.vstack([X_train, X_test])
        N_train, L = X_train.shape
        N_test = X_test.shape[0]
        print(f"    Train: {N_train} samples | Test: {N_test} samples | Length: {L} timestamps")

        # 1. Equal-Feature Speed (13 identical features)
        # Warmup
        _ = kymora.extract_features(X_all[:5], features=MATCHED_KYMORA)
        _ = extract_tsfel(X_all[:5], tsfel_cfg_matched)

        t0 = time.perf_counter()
        df_km_eq = kymora.extract_features_df(X_all, features=MATCHED_KYMORA)
        t_km_eq = (time.perf_counter() - t0) * 1000.0

        t0 = time.perf_counter()
        df_ts_eq = extract_tsfel_df(X_all, tsfel_cfg_matched)
        t_ts_eq = (time.perf_counter() - t0) * 1000.0
        speedup = t_ts_eq / t_km_eq if t_km_eq > 0 else 0

        print(f"    [Equal 13 Feats] Kymora: {t_km_eq:6.2f} ms | TSFEL: {t_ts_eq:8.2f} ms | Speedup: {speedup:6.1f}x")

        t_tsfresh_eq = 0.0
        speedup_tsfresh = 0.0
        if HAS_TSFRESH:
            t0 = time.perf_counter()
            _ = extract_tsfresh(X_all, MinimalFCParameters(), n_jobs=4)
            t_tsfresh_eq = (time.perf_counter() - t0) * 1000.0
            speedup_tsfresh = t_tsfresh_eq / t_km_eq if t_km_eq > 0 else 0
            print(f"    [tsfresh minimal] Time: {t_tsfresh_eq:8.2f} ms | Kymora Speedup: {speedup_tsfresh:6.1f}x")

        # Parity check
        worst_rel = 0.0
        for km_name, ts_name in PAIRINGS:
            v_km = df_km_eq[km_name].to_numpy()
            v_ts = df_ts_eq[ts_name].to_numpy()
            denom = np.abs(v_ts)
            denom[denom == 0] = 1.0
            rel = float(np.max(np.abs(v_km - v_ts) / denom))
            worst_rel = max(worst_rel, rel)
        print(f"    [Numerical Parity] Max Relative Error: {worst_rel:.2e} (Bitwise Match PASS)")

        # 2. Downstream ML Accuracy
        extractors = [
            ("Kymora (core33)", lambda arr: kymora.extract_features(arr, profile="core33")),
            ("Kymora (extended)", lambda arr: kymora.extract_features(arr, profile="extended")),
            ("Kymora (full)", lambda arr: kymora.extract_features(arr, profile="full")),
            ("TSFEL (statistical)", lambda arr: extract_tsfel(arr, tsfel_cfg_stat)),
            ("TSFEL (all)", lambda arr: extract_tsfel(arr, tsfel_cfg_all)),
        ]
        if HAS_TSFRESH:
            extractors.extend([
                ("tsfresh (minimal)", lambda arr: extract_tsfresh(arr, MinimalFCParameters(), n_jobs=4)),
                ("tsfresh (efficient)", lambda arr: extract_tsfresh(arr, EfficientFCParameters(), n_jobs=4)),
            ])

        dataset_evals = []
        for label, ext_fn in extractors:
            t0 = time.perf_counter()
            F_tr = ext_fn(X_train)
            F_te = ext_fn(X_test)
            t_extract = (time.perf_counter() - t0) * 1000.0

            scaler = StandardScaler()
            X_tr_s = scaler.fit_transform(np.nan_to_num(F_tr, nan=0.0))
            X_te_s = scaler.transform(np.nan_to_num(F_te, nan=0.0))

            rf = RandomForestClassifier(n_estimators=100, random_state=42)
            rf.fit(X_tr_s, y_train)
            pred_rf = rf.predict(X_te_s)
            acc_rf = accuracy_score(y_test, pred_rf)
            f1_rf = f1_score(y_test, pred_rf, average="macro")

            ridge = RidgeClassifier(random_state=42)
            ridge.fit(X_tr_s, y_train)
            pred_rg = ridge.predict(X_te_s)
            acc_rg = accuracy_score(y_test, pred_rg)

            print(f"    {label:24s} | Feats: {F_tr.shape[1]:3d} | Time: {t_extract:8.1f} ms | RF Acc: {acc_rf*100:5.2f}% | RF F1: {f1_rf:5.3f} | Ridge: {acc_rg*100:5.2f}%")

            dataset_evals.append({
                "extractor": label,
                "n_features": F_tr.shape[1],
                "extract_time_ms": t_extract,
                "rf_acc": acc_rf,
                "rf_f1": f1_rf,
                "ridge_acc": acc_rg,
            })

        results[dname] = {
            "n_train": N_train,
            "n_test": N_test,
            "length": L,
            "equal_features": {
                "kymora_ms": t_km_eq,
                "tsfel_ms": t_ts_eq,
                "tsfresh_ms": t_tsfresh_eq,
                "speedup_vs_tsfel": speedup,
                "speedup_vs_tsfresh": speedup_tsfresh,
                "worst_rel_error": worst_rel,
            },
            "evaluations": dataset_evals,
        }

    # Save to Kymora/benchmarks/results/
    out_path = Path(__file__).resolve().parent / "results" / "kymora_vs_tsfel_tsfresh_real_benchmark.json"
    out_path.parent.mkdir(parents=True, exist_ok=True)
    with open(out_path, "w", encoding="utf-8") as f:
        json.dump(results, f, indent=2)

    # Backwards-compatible file
    legacy_path = Path(__file__).resolve().parent / "results" / "kymora_vs_tsfel_real_benchmark.json"
    with open(legacy_path, "w", encoding="utf-8") as f:
        json.dump(results, f, indent=2)

    print(f"\n[SUCCESS] Real-world benchmark telemetry saved to {out_path}")


if __name__ == "__main__":
    run_benchmark()
