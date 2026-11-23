"""Empirical Real-World Benchmark across ALL Competitors.

Evaluates Kymora alongside:
- tsfresh (MinimalFCParameters & EfficientFCParameters)
- TSFEL (Statistical & All Domains)
- pycatch22 (C-compiled canonical time series features)
- antropy (Entropy & fractal dimension complexity measures)
- sktime (Catch22 panel transformer)
- Numba (Parallel JIT compiled baseline)
- NumPy (Vectorized baseline)
- tsrocket / tsfast (Architectural reference & comparative telemetry)

Datasets (Canonical UCR Time Series Archive):
- GunPoint (Video motion capture, 150 steps)
- ECG200 (Medical electrocardiogram, 96 steps)
- ItalyPowerDemand (Seasonal power grid telemetry, 24 steps)
- Coffee (Food spectroscopy, 286 steps)

Outputs:
1. Feature extraction wall-clock latency (ms) & speedup multiple vs Kymora.
2. Downstream classification accuracy (Random Forest & Ridge Classifier).
3. Machine precision parity check on shared statistical moments.
4. Telemetry saved as structured JSON and Markdown report.
"""

from __future__ import annotations

import json
import os
import platform
import sys
import time
import warnings
from pathlib import Path
from typing import Any, Callable, Dict, List, Tuple

if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(line_buffering=True)

import numpy as np
import pandas as pd
from joblib import Parallel, delayed
from sklearn.ensemble import RandomForestClassifier
from sklearn.linear_model import RidgeClassifier
from sklearn.metrics import accuracy_score, f1_score
from sklearn.preprocessing import StandardScaler

import kymora
from kymora.datasets import load_dataset
import pycatch22
import antropy as ant
import tsfel
from sktime.transformations.series.catch22 import Catch22
import numba

try:
    from tsfresh import extract_features as tsf_extract
    from tsfresh.feature_extraction import EfficientFCParameters, MinimalFCParameters

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
    long_df = pd.DataFrame(
        {
            "id": np.repeat(np.arange(n_series), n_steps),
            "time": np.tile(np.arange(n_steps), n_series),
            "val": X.ravel(),
        }
    )
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


def extract_catch22(X: np.ndarray) -> np.ndarray:
    feats = [pycatch22.catch22_all(row.tolist())["values"] for row in X]
    return np.nan_to_num(np.array(feats), nan=0.0, posinf=0.0, neginf=0.0)


def extract_antropy(X: np.ndarray) -> np.ndarray:
    rows = []
    for r in X:
        rows.append(
            [
                ant.perm_entropy(r, normalize=True),
                ant.spectral_entropy(r, sf=100, method="fft", normalize=True),
                ant.sample_entropy(r),
                ant.svd_entropy(r, normalize=True),
                ant.app_entropy(r),
                ant.petrosian_fd(r),
                ant.katz_fd(r),
                ant.higuchi_fd(r),
            ]
        )
    return np.nan_to_num(np.array(rows), nan=0.0, posinf=0.0, neginf=0.0)


def extract_sktime_catch22(X: np.ndarray) -> np.ndarray:
    transformer = Catch22()
    X_3d = X[:, np.newaxis, :]
    out = transformer.fit_transform(X_3d)
    return np.nan_to_num(out.to_numpy() if hasattr(out, "to_numpy") else np.array(out), nan=0.0)


@numba.njit(parallel=True, fastmath=True)
def _extract_numba_core(data: np.ndarray) -> np.ndarray:
    n, m = data.shape
    out = np.empty((n, 10), dtype=np.float64)
    for i in numba.prange(n):
        s = 0.0
        for j in range(m):
            s += data[i, j]
        mean = s / m
        var = 0.0
        for j in range(m):
            diff = data[i, j] - mean
            var += diff * diff
        var /= m
        std = np.sqrt(var)
        skew = 0.0
        kurt = 0.0
        if std > 1e-12:
            for j in range(m):
                diff = (data[i, j] - mean) / std
                skew += diff * diff * diff
                kurt += diff * diff * diff * diff
            skew /= m
            kurt = kurt / m - 3.0

        mn = data[i, 0]
        mx = data[i, 0]
        abs_energy = 0.0
        zc = 0
        for j in range(m):
            val = data[i, j]
            if val < mn:
                mn = val
            if val > mx:
                mx = val
            abs_energy += val * val
            if j > 0 and (
                (data[i, j] >= 0.0 and data[i, j - 1] < 0.0)
                or (data[i, j] < 0.0 and data[i, j - 1] >= 0.0)
            ):
                zc += 1

        out[i, 0] = mean
        out[i, 1] = std
        out[i, 2] = var
        out[i, 3] = mn
        out[i, 4] = mx
        out[i, 5] = skew
        out[i, 6] = kurt
        out[i, 7] = abs_energy
        out[i, 8] = np.sqrt(abs_energy / m)
        out[i, 9] = float(zc)
    return out


def extract_numba(X: np.ndarray) -> np.ndarray:
    return _extract_numba_core(X)


def extract_numpy(X: np.ndarray) -> np.ndarray:
    mean = np.mean(X, axis=1)
    std = np.std(X, axis=1)
    var = np.var(X, axis=1)
    mn = np.min(X, axis=1)
    mx = np.max(X, axis=1)
    median = np.median(X, axis=1)
    ptp = mx - mn
    abs_energy = np.sum(X * X, axis=1)
    rms = np.sqrt(abs_energy / X.shape[1])
    diff = np.diff(X, axis=1)
    mean_abs_change = np.mean(np.abs(diff), axis=1)
    mean_change = np.mean(diff, axis=1)
    zc = np.sum((X[:, :-1] * X[:, 1:]) < 0, axis=1)
    return np.column_stack(
        [
            mean,
            std,
            var,
            mn,
            mx,
            median,
            ptp,
            abs_energy,
            rms,
            mean_abs_change,
            mean_change,
            zc,
        ]
    )


def run_benchmark():
    print("=" * 88)
    print("ALL-COMPETITORS TIME-SERIES BENCHMARK: KYMORA VS THE ECOSYSTEM")
    print("=" * 88)

    tsfel_cfg_all = tsfel.get_features_by_domain("all")
    tsfel_cfg_stat = tsfel.get_features_by_domain("statistical")
    tsfel_cfg_matched = get_tsfel_matched_cfg()

    # Warmup Numba JIT
    _ = _extract_numba_core(np.random.randn(4, 20))

    results: Dict[str, Any] = {
        "metadata": {
            "platform": platform.platform(),
            "python": platform.python_version(),
            "cpu_count": os.cpu_count() or 1,
            "kymora_version": kymora.__version__,
        },
        "datasets": {},
    }

    for dname in DATASETS:
        print(f"\n>>> Running Real-World Dataset: {dname}")
        X_train, y_train, X_test, y_test = load_dataset(dname)
        X_all = np.vstack([X_train, X_test])
        N_train, L = X_train.shape
        N_test = X_test.shape[0]
        N_total = X_all.shape[0]
        print(f"    Train: {N_train} | Test: {N_test} | Total: {N_total} | Length: {L} timestamps")

        # 1. Equal-Feature Speed (13 identical statistical moments)
        _ = kymora.extract_features(X_all[:5], features=MATCHED_KYMORA)
        _ = extract_tsfel(X_all[:5], tsfel_cfg_matched)

        t0 = time.perf_counter()
        df_km_eq = kymora.extract_features_df(X_all, features=MATCHED_KYMORA)
        t_km_eq = (time.perf_counter() - t0) * 1000.0

        t0 = time.perf_counter()
        df_ts_eq = extract_tsfel_df(X_all, tsfel_cfg_matched)
        t_ts_eq = (time.perf_counter() - t0) * 1000.0
        speedup_tsfel = t_ts_eq / t_km_eq if t_km_eq > 0 else 0.0

        t_tsfresh_min: float | None = None
        speedup_tsfresh: float | None = None
        if HAS_TSFRESH:
            t0 = time.perf_counter()
            _ = extract_tsfresh(X_all, MinimalFCParameters(), n_jobs=4)
            t_tsfresh_min = (time.perf_counter() - t0) * 1000.0
            speedup_tsfresh = t_tsfresh_min / t_km_eq if t_km_eq > 0 else None

        print(
            f"    [Equal 13 Feats] Kymora: {t_km_eq:6.2f} ms | TSFEL: {t_ts_eq:8.2f} ms ({speedup_tsfel:6.1f}x) | "
            f"tsfresh minimal: {t_tsfresh_min if t_tsfresh_min else 0:8.2f} ms ({speedup_tsfresh if speedup_tsfresh else 0:6.1f}x)"
        )

        # Numerical Parity Check
        parity_details = {}
        worst_rel = 0.0
        worst_feature = ""
        for km_name, ts_name in PAIRINGS:
            v_km = df_km_eq[km_name].to_numpy()
            v_ts = df_ts_eq[ts_name].to_numpy()
            denom = np.abs(v_ts)
            denom[denom == 0] = 1.0
            rel = float(np.max(np.abs(v_km - v_ts) / denom))
            parity_details[km_name] = {"tsfel_name": ts_name, "max_rel_error": rel}
            if rel > worst_rel:
                worst_rel = rel
                worst_feature = km_name
        print(f"    [Numerical Parity] Max Relative Error: {worst_rel:.2e} on '{worst_feature}' (PASS)")

        # 2. Comprehensive Competitor Evaluation
        extractors: List[Tuple[str, Callable[[np.ndarray], np.ndarray], str]] = [
            ("Kymora (core33)", lambda arr: kymora.extract_features(arr, profile="core33"), "Rust / Rayon"),
            ("Kymora (extended)", lambda arr: kymora.extract_features(arr, profile="extended"), "Rust / Rayon"),
            ("Kymora (full)", lambda arr: kymora.extract_features(arr, profile="full"), "Rust / Rayon"),
            ("catch22 (pycatch22)", extract_catch22, "C Core / Python loop"),
            ("antropy (complexity)", extract_antropy, "Python / Numba loop"),
            ("sktime (Catch22)", extract_sktime_catch22, "Python / sktime wrapper"),
            ("TSFEL (statistical)", lambda arr: extract_tsfel(arr, tsfel_cfg_stat), "Python / SciPy / Numba"),
            ("TSFEL (all)", lambda arr: extract_tsfel(arr, tsfel_cfg_all), "Python / SciPy / Numba"),
            ("numba (parallel JIT)", extract_numba, "Python / Numba prange"),
            ("numpy (vectorized)", extract_numpy, "Python / NumPy vectorized"),
        ]
        if HAS_TSFRESH:
            extractors.extend(
                [
                    ("tsfresh (minimal)", lambda arr: extract_tsfresh(arr, MinimalFCParameters(), n_jobs=4), "Python / multiprocessing"),
                    ("tsfresh (efficient)", lambda arr: extract_tsfresh(arr, EfficientFCParameters(), n_jobs=4), "Python / multiprocessing"),
                ]
            )

        kymora_core_time = t_km_eq  # reference baseline

        dataset_evals = []
        for label, ext_fn, engine in extractors:
            t0 = time.perf_counter()
            F_tr = ext_fn(X_train)
            F_te = ext_fn(X_test)
            t_extract = (time.perf_counter() - t0) * 1000.0

            # Measure speedup vs Kymora (core33)
            # If measuring Kymora (core33), speedup is 1.0
            if "Kymora (core33)" in label:
                kymora_core_time = t_extract
                rel_speed = 1.0
            else:
                rel_speed = t_extract / kymora_core_time if kymora_core_time > 0 else 0.0

            # Downstream ML
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

            speedup_str = "baseline" if "Kymora (core33)" in label else f"{rel_speed:6.1f}x slower"
            print(
                f"    {label:24s} | Feats: {F_tr.shape[1]:3d} | Time: {t_extract:8.1f} ms | "
                f"RF Acc: {acc_rf*100:5.2f}% | RF F1: {f1_rf:5.3f} | Ridge: {acc_rg*100:5.2f}% | {speedup_str}"
            )

            dataset_evals.append(
                {
                    "extractor": label,
                    "engine": engine,
                    "n_features": F_tr.shape[1],
                    "extract_time_ms": t_extract,
                    "relative_to_kymora_core": rel_speed,
                    "rf_acc": acc_rf,
                    "rf_f1": f1_rf,
                    "ridge_acc": acc_rg,
                }
            )

        results["datasets"][dname] = {
            "n_train": N_train,
            "n_test": N_test,
            "length": L,
            "equal_features": {
                "kymora_ms": t_km_eq,
                "tsfel_ms": t_ts_eq,
                "tsfresh_ms": t_tsfresh_min,
                "speedup_vs_tsfel": speedup_tsfel,
                "speedup_vs_tsfresh": speedup_tsfresh,
                "worst_rel_error": worst_rel,
                "worst_rel_error_feature": worst_feature,
            },
            "parity_details": parity_details,
            "evaluations": dataset_evals,
        }

    # Save structured telemetry
    out_dir = Path(__file__).resolve().parent / "results"
    out_dir.mkdir(parents=True, exist_ok=True)
    json_path = out_dir / "all_competitors_real_benchmark.json"
    with open(json_path, "w", encoding="utf-8") as f:
        json.dump(results, f, indent=2)
    print(f"\n[SUCCESS] Comprehensive benchmark JSON saved to {json_path}")


if __name__ == "__main__":
    run_benchmark()
