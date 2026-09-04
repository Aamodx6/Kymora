"""Downstream Machine Learning Benchmark: Time-Series Classification Utility.

Evaluates the downstream classification utility of features extracted by Tsxtract
versus pycatch22 and standard baseline representations on canonical time-series
benchmark archetypes with realistic, non-trivial difficulty:
  1. Synthetic Control (6-class dynamic patterns with noise overlap)
  2. Arrhythmia ECG Simulation (2-class physiological morphology with baseline wander)
  3. Kinematic Motion Gesture (2-class inertial sensor archetype, GunPoint equivalent)
  4. Diurnal Power Demand (2-class weekday vs weekend telemetry load)

Produces metrics required for academic peer review:
  - Feature Extraction Wall-Clock Time (ms)
  - Random Forest Classification Accuracy & Macro F1-Score
  - Ridge Classification Accuracy & Macro F1-Score

Resolves Review Critique #7 and #8.
"""

from __future__ import annotations

import argparse
import os
import time
from dataclasses import dataclass
from typing import Callable, Dict, List, Tuple

import numpy as np
from sklearn.ensemble import RandomForestClassifier
from sklearn.linear_model import RidgeClassifier
from sklearn.metrics import accuracy_score, f1_score
from sklearn.model_selection import StratifiedKFold

import tsxtractor


@dataclass
class BenchmarkResult:
    dataset: str
    extractor_name: str
    n_features: int
    extract_time_ms: float
    accuracy_rf: float
    f1_rf: float
    accuracy_ridge: float
    f1_ridge: float


# ---------------------------------------------------------------------
# Dataset Generators (Realistic, Non-Trivial Dynamic Benchmarks)
# ---------------------------------------------------------------------

def generate_synthetic_control(n_samples: int = 600, length: int = 150) -> Tuple[np.ndarray, np.ndarray]:
    """Generates 6 distinct time-series classes with realistic noise overlap."""
    rng = np.random.default_rng(42)
    per_class = n_samples // 6
    X_list = []
    y_list = []
    t = np.linspace(0, 1, length)

    # Class 0: Normal
    X_list.append(rng.normal(0, 1.0, size=(per_class, length)))
    y_list.append(np.zeros(per_class, dtype=int))

    # Class 1: Cyclic
    cyclic = 1.2 * np.sin(2 * np.pi * 4 * t) + rng.normal(0, 0.9, size=(per_class, length))
    X_list.append(cyclic)
    y_list.append(np.ones(per_class, dtype=int))

    # Class 2: Increasing trend
    trend_up = 1.8 * t + rng.normal(0, 0.9, size=(per_class, length))
    X_list.append(trend_up)
    y_list.append(np.full(per_class, 2, dtype=int))

    # Class 3: Decreasing trend
    trend_down = -1.8 * t + rng.normal(0, 0.9, size=(per_class, length))
    X_list.append(trend_down)
    y_list.append(np.full(per_class, 3, dtype=int))

    # Class 4: Upward shift
    shift_up = rng.normal(0, 0.9, size=(per_class, length))
    shift_up[:, length // 2 :] += 1.4
    X_list.append(shift_up)
    y_list.append(np.full(per_class, 4, dtype=int))

    # Class 5: Downward shift
    shift_down = rng.normal(0, 0.9, size=(per_class, length))
    shift_down[:, length // 2 :] -= 1.4
    X_list.append(shift_down)
    y_list.append(np.full(per_class, 5, dtype=int))

    return np.vstack(X_list), np.concatenate(y_list)


def generate_ecg_simulation(n_samples: int = 500, length: int = 150) -> Tuple[np.ndarray, np.ndarray]:
    """Simulated normal sinus rhythm vs arrhythmic/tachycardic ECG waveforms."""
    rng = np.random.default_rng(123)
    half = n_samples // 2
    t = np.linspace(0, 3, length)

    # Normal Sinus: regular periodic QRS spikes with baseline wander
    wander = 0.5 * np.sin(2 * np.pi * 0.2 * t)
    normal = np.sin(2 * np.pi * 1.2 * t) + 1.2 * np.sin(2 * np.pi * 2.4 * t) ** 4 + wander + rng.normal(0, 0.35, size=(half, length))
    y_normal = np.zeros(half, dtype=int)

    # Arrhythmia: irregular frequency modulation + noise
    arrhythmia = np.sin(2 * np.pi * (2.2 + 0.8 * np.sin(t)) * t) + wander + rng.normal(0, 0.45, size=(half, length))
    y_arrhythmia = np.ones(half, dtype=int)

    X = np.vstack([normal, arrhythmia])
    # Per-series z-normalization to prevent trivial mean/variance separation
    X = (X - np.mean(X, axis=1, keepdims=True)) / np.std(X, axis=1, keepdims=True)
    y = np.concatenate([y_normal, y_arrhythmia])
    return X, y


def generate_motion_gesture(n_samples: int = 400, length: int = 150) -> Tuple[np.ndarray, np.ndarray]:
    """Kinematic acceleration gesture archetype (GunPoint equivalent)."""
    rng = np.random.default_rng(456)
    half = n_samples // 2
    t = np.linspace(0, 1, length)

    # Gesture A: Smooth reach and return
    reach = 2.0 * np.exp(-((t - 0.5) ** 2) / 0.03) + rng.normal(0, 0.4, size=(half, length))
    y_a = np.zeros(half, dtype=int)

    # Gesture B: Draw and aim (preceded by holster dip)
    dip = -1.5 * np.exp(-((t - 0.25) ** 2) / 0.015)
    aim = 2.2 * np.exp(-((t - 0.65) ** 2) / 0.03)
    draw = dip + aim + rng.normal(0, 0.4, size=(half, length))
    y_b = np.ones(half, dtype=int)

    X = np.vstack([reach, draw])
    X = (X - np.mean(X, axis=1, keepdims=True)) / np.std(X, axis=1, keepdims=True)
    y = np.concatenate([y_a, y_b])
    return X, y


def generate_power_demand(n_samples: int = 400, length: int = 150) -> Tuple[np.ndarray, np.ndarray]:
    """Diurnal power demand telemetry: Weekday (2 peaks) vs Weekend (flat daytime peak)."""
    rng = np.random.default_rng(789)
    half = n_samples // 2
    t = np.linspace(0, 24, length)

    # Weekday: morning peak (8am) + evening peak (7pm)
    peak1 = 1.5 * np.exp(-((t - 8) ** 2) / 8)
    peak2 = 1.8 * np.exp(-((t - 19) ** 2) / 10)
    weekday = 1.0 + peak1 + peak2 + rng.normal(0, 0.35, size=(half, length))
    y_weekday = np.zeros(half, dtype=int)

    # Weekend: broad afternoon peak (12pm - 4pm)
    weekend_peak = 1.6 * np.exp(-((t - 14) ** 2) / 25)
    weekend = 0.8 + weekend_peak + rng.normal(0, 0.35, size=(half, length))
    y_weekend = np.ones(half, dtype=int)

    X = np.vstack([weekday, weekend])
    X = (X - np.mean(X, axis=1, keepdims=True)) / np.std(X, axis=1, keepdims=True)
    y = np.concatenate([y_weekday, y_weekend])
    return X, y


# ---------------------------------------------------------------------
# Feature Extraction Functions
# ---------------------------------------------------------------------

def extract_tsxtractor(X: np.ndarray) -> np.ndarray:
    return tsxtractor.extract_features(X)


def extract_catch22(X: np.ndarray) -> np.ndarray | None:
    try:
        import pycatch22
        out = []
        for row in X:
            res = pycatch22.catch22_all(row.tolist())
            out.append(res["values"])
        return np.array(out, dtype=np.float64)
    except ImportError:
        return None


def extract_naive_stats(X: np.ndarray) -> np.ndarray:
    """Baseline naive summary: mean, std, min, max, median."""
    return np.column_stack([
        np.mean(X, axis=1),
        np.std(X, axis=1),
        np.min(X, axis=1),
        np.max(X, axis=1),
        np.median(X, axis=1),
    ])


# ---------------------------------------------------------------------
# Cross-Validation Evaluation (5-Fold Stratified)
# ---------------------------------------------------------------------

def evaluate_features(X_feats: np.ndarray, y: np.ndarray) -> Tuple[float, float, float, float]:
    X_clean = np.nan_to_num(X_feats, nan=0.0, posinf=0.0, neginf=0.0)
    # Z-score normalize features
    mean = np.mean(X_clean, axis=0)
    std = np.std(X_clean, axis=0)
    std[std == 0.0] = 1.0
    X_norm = (X_clean - mean) / std

    cv = StratifiedKFold(n_splits=5, shuffle=True, random_state=42)
    rf_accs, rf_f1s = [], []
    ridge_accs, ridge_f1s = [], []

    for train_idx, test_idx in cv.split(X_norm, y):
        X_train, X_test = X_norm[train_idx], X_norm[test_idx]
        y_train, y_test = y[train_idx], y[test_idx]

        # Random Forest
        rf = RandomForestClassifier(n_estimators=100, random_state=42, n_jobs=-1)
        rf.fit(X_train, y_train)
        pred_rf = rf.predict(X_test)
        rf_accs.append(accuracy_score(y_test, pred_rf))
        rf_f1s.append(f1_score(y_test, pred_rf, average="macro"))

        # Ridge Classifier
        ridge = RidgeClassifier(alpha=1.0, random_state=42)
        ridge.fit(X_train, y_train)
        pred_ridge = ridge.predict(X_test)
        ridge_accs.append(accuracy_score(y_test, pred_ridge))
        ridge_f1s.append(f1_score(y_test, pred_ridge, average="macro"))

    return (
        float(np.mean(rf_accs)),
        float(np.mean(rf_f1s)),
        float(np.mean(ridge_accs)),
        float(np.mean(ridge_f1s)),
    )


def run_all_downstream(output_md: str | None = None) -> List[BenchmarkResult]:
    datasets = {
        "Synthetic Control (6-class)": generate_synthetic_control(600, 150),
        "Simulated ECG (2-class)": generate_ecg_simulation(500, 150),
        "Kinematic Gesture (2-class)": generate_motion_gesture(400, 150),
        "Power Demand (2-class)": generate_power_demand(400, 150),
    }

    extractors = {
        "Tsxtract (33 feats)": extract_tsxtractor,
        "Naive Stats (5 feats)": extract_naive_stats,
    }
    if extract_catch22(np.zeros((2, 10))) is not None:
        extractors["catch22 (22 feats)"] = extract_catch22

    results: List[BenchmarkResult] = []

    for dname, (X, y) in datasets.items():
        print(f"\n--- Evaluating {dname} (N={len(X)}, Length={X.shape[1]}) ---")
        for ename, fn in extractors.items():
            # Time extraction across 5 runs
            times = []
            feats = None
            for _ in range(5):
                t0 = time.perf_counter()
                feats = fn(X)
                times.append(time.perf_counter() - t0)
            ext_ms = float(np.median(times)) * 1000.0

            assert feats is not None
            acc_rf, f1_rf, acc_ridge, f1_ridge = evaluate_features(feats, y)

            res = BenchmarkResult(
                dataset=dname,
                extractor_name=ename,
                n_features=feats.shape[1],
                extract_time_ms=ext_ms,
                accuracy_rf=acc_rf,
                f1_rf=f1_rf,
                accuracy_ridge=acc_ridge,
                f1_ridge=f1_ridge,
            )
            results.append(res)
            print(
                f"  [{ename:<20}] Ext: {ext_ms:6.2f} ms | "
                f"RF: {acc_rf*100:5.1f}% (F1={f1_rf:.3f}) | "
                f"Ridge: {acc_ridge*100:5.1f}% (F1={f1_ridge:.3f})"
            )

    return results


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--output-md", type=str, default="benches/results/downstream_report.md")
    args = parser.parse_args()

    results = run_all_downstream(args.output_md)

    lines = [
        "# Downstream Machine Learning Utility Benchmark Report",
        "",
        "Evaluation of feature representations on standard dynamic classification benchmarks (5-fold stratified CV).",
        "",
        "| Dataset | Representation | Feats | Extract Time (ms) | RF Acc (%) | RF F1 | Ridge Acc (%) | Ridge F1 |",
        "|---|---|---:|---:|---:|---:|---:|---:|",
    ]
    for r in results:
        lines.append(
            f"| {r.dataset} | **{r.extractor_name}** | {r.n_features} | "
            f"{r.extract_time_ms:.2f} ms | {r.accuracy_rf * 100:.1f}% | {r.f1_rf:.4f} | "
            f"{r.accuracy_ridge * 100:.1f}% | {r.f1_ridge:.4f} |"
        )

    os.makedirs(os.path.dirname(args.output_md), exist_ok=True)
    with open(args.output_md, "w", encoding="utf-8") as f:
        f.write("\n".join(lines))

    print(f"\nReport written to: {args.output_md}")


if __name__ == "__main__":
    main()
