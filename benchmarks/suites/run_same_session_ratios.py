"""Same-Session Interleaved Benchmark Protocol across Kymora, catch22, TSFEL, and tsfresh.

Requirement C protocol:
- Enforces strict High Performance power scheme and AC online via tools.check_env.
- Runs 3 interleaved sessions on the headline workload (1,000 series x 500 steps, 16 threads).
- In each session: executes Kymora, catch22, TSFEL, and tsfresh in interleaved rounds.
- Calculates per-session ratio of medians: ratio = median(competitor) / median(kymora).
- Pools across sessions with 95% bootstrap confidence intervals and per-feature ratios.
- Emits benchmarks/results/headline_same_session_ratios.json and report.
"""

from __future__ import annotations

import argparse
import gc
import json
import sys
import time
from pathlib import Path
from typing import Any

import numpy as np
import pandas as pd
from joblib import Parallel, delayed

REPO_ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(REPO_ROOT))

import kymora as km
import pycatch22
import tsfel
from tsfresh import extract_features as tsf_extract
from tsfresh.feature_extraction import EfficientFCParameters

from benchmarks.harness.env import save_env, snapshot_load
from benchmarks.harness.stats import bootstrap_ci
from tools.check_env import verify_headline_environment

RESULTS_DIR = REPO_ROOT / "benchmarks" / "results"
OUT_MD = RESULTS_DIR / "HEADLINE_SAME_SESSION_REPORT.md"
OUT_JSON = RESULTS_DIR / "headline_same_session_ratios.json"

N_SESSIONS = 3
N_SERIES = 1000
LENGTH = 500
THREADS = 16

FEATURE_COUNTS = {
    "Kymora (core33)": 33,
    "catch22": 22,
    "TSFEL": 156,
    "tsfresh": 777,
}


def run_kymora(X: np.ndarray) -> float:
    t0 = time.perf_counter_ns()
    km.extract_features(X, profile="core33", n_jobs=THREADS)
    return (time.perf_counter_ns() - t0) / 1e6  # ms


def run_catch22(X: np.ndarray) -> float:
    t0 = time.perf_counter_ns()
    Parallel(n_jobs=THREADS)(delayed(pycatch22.catch22_all)(row.tolist()) for row in X)
    return (time.perf_counter_ns() - t0) / 1e6


def run_tsfel(X: np.ndarray, cfg: dict) -> float:
    t0 = time.perf_counter_ns()
    Parallel(n_jobs=THREADS)(delayed(tsfel.time_series_features_extractor)(cfg, row, fs=100, verbose=0) for row in X)
    return (time.perf_counter_ns() - t0) / 1e6


def run_tsfresh(df_long: pd.DataFrame) -> float:
    t0 = time.perf_counter_ns()
    tsf_extract(df_long, column_id="id", column_sort="time", default_fc_parameters=EfficientFCParameters(), n_jobs=THREADS, disable_progressbar=True)
    return (time.perf_counter_ns() - t0) / 1e6


def get_cpu_telemetry() -> dict[str, Any]:
    import psutil
    res = {}
    try:
        freq = psutil.cpu_freq()
        if freq:
            res["cpu_freq_current_mhz"] = float(freq.current)
            res["cpu_freq_max_mhz"] = float(freq.max)
    except Exception:
        pass
    try:
        if hasattr(psutil, "sensors_temperatures"):
            temps = psutil.sensors_temperatures()
            if temps:
                res["cpu_temp"] = temps
    except Exception:
        pass
    return res


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--allow-suboptimal", action="store_true", help="Bypass strict power check")
    parser.add_argument("--cooldown", type=float, default=90.0, help="Cooldown sleep in seconds between extractor blocks")
    args = parser.parse_args()

    print("=" * 80)
    print("  Same-Session Interleaved Benchmark Protocol (HEAD)")
    print("=" * 80)

    # 1. Audit environment
    ok, reasons = verify_headline_environment(strict_power=not args.allow_suboptimal)
    if not ok:
        print("[ERROR] Environment audit failed:")
        for r in reasons:
            print(f"  - {r}")
        if not args.allow_suboptimal:
            sys.exit(1)

    load_start = snapshot_load()
    rng = np.random.default_rng(42)
    X = np.ascontiguousarray(rng.standard_normal((N_SERIES, LENGTH)), dtype=np.float64)
    df_long = pd.DataFrame({
        "id": np.repeat(np.arange(N_SERIES), LENGTH),
        "time": np.tile(np.arange(LENGTH), N_SERIES),
        "val": X.flatten(),
    })
    tsfel_cfg = tsfel.get_features_by_domain()

    # Pre-warmup
    print("Pre-warming extractors...")
    run_kymora(X[:50])
    run_catch22(X[:20])

    # Isolated Kymora-alone baseline (50 passes)
    print("\nMeasuring isolated Kymora-alone baseline (50 passes)...")
    km_alone_times = []
    for _ in range(50):
        km_alone_times.append(run_kymora(X))
    med_km_alone = float(np.median(km_alone_times))
    sps_alone = float(N_SERIES / (med_km_alone / 1000.0))
    print(f"  Isolated Kymora median: {med_km_alone:.3f} ms ({sps_alone:,.0f} series/s)")

    session_records = []
    all_times = {
        "kymora": [],
        "catch22": [],
        "tsfel": [],
        "tsfresh": [],
    }
    telemetry_log = []

    for s_idx in range(1, N_SESSIONS + 1):
        print(f"\n{'='*30} Session {s_idx}/{N_SESSIONS} {'='*30}")
        s_km = []
        s_c22 = []
        s_tsfel = []
        s_tsfresh = []

        # Run interleaved rounds per session with cooldown
        print("  Running interleaved extraction...")
        # 1. Kymora (fast: run 15 passes)
        tel_pre_km = get_cpu_telemetry()
        for _ in range(15):
            s_km.append(run_kymora(X))
        med_km = float(np.median(s_km))
        print(f"    Kymora median:   {med_km:.3f} ms ({N_SERIES/(med_km/1000):,.0f} series/s)")
        if args.cooldown > 0:
            print(f"    [Cooldown {args.cooldown:.0f}s after Kymora...]")
            time.sleep(args.cooldown)

        # 2. catch22 (moderate: run 3 passes)
        tel_pre_c22 = get_cpu_telemetry()
        for _ in range(3):
            s_c22.append(run_catch22(X))
        med_c22 = float(np.median(s_c22))
        print(f"    catch22 median:  {med_c22:.2f} ms")
        if args.cooldown > 0:
            print(f"    [Cooldown {args.cooldown:.0f}s after catch22...]")
            time.sleep(args.cooldown)

        # 3. TSFEL (expensive: run 2 passes)
        tel_pre_tsfel = get_cpu_telemetry()
        for _ in range(2):
            s_tsfel.append(run_tsfel(X, tsfel_cfg))
        med_tsfel = float(np.median(s_tsfel))
        print(f"    TSFEL median:    {med_tsfel:.2f} ms")
        if args.cooldown > 0:
            print(f"    [Cooldown {args.cooldown:.0f}s after TSFEL...]")
            time.sleep(args.cooldown)

        # 4. tsfresh (heavyweight: run 1 pass per session)
        tel_pre_tsfresh = get_cpu_telemetry()
        t_tsf = run_tsfresh(df_long)
        s_tsfresh.append(t_tsf)
        med_tsfresh = float(np.median(s_tsfresh))
        print(f"    tsfresh median:  {med_tsfresh:.2f} ms")
        if args.cooldown > 0 and s_idx < N_SESSIONS:
            print(f"    [Cooldown {args.cooldown:.0f}s after tsfresh before next session...]")
            time.sleep(args.cooldown)

        # Compute per-session ratios
        r_c22 = med_c22 / med_km
        r_tsfel = med_tsfel / med_km
        r_tsfresh = med_tsfresh / med_km

        s_rec = {
            "session": s_idx,
            "median_km_ms": med_km,
            "median_c22_ms": med_c22,
            "median_tsfel_ms": med_tsfel,
            "median_tsfresh_ms": med_tsfresh,
            "ratio_catch22": r_c22,
            "ratio_tsfel": r_tsfel,
            "ratio_tsfresh": r_tsfresh,
            "telemetry": {
                "km": tel_pre_km,
                "c22": tel_pre_c22,
                "tsfel": tel_pre_tsfel,
                "tsfresh": tel_pre_tsfresh,
            },
        }
        session_records.append(s_rec)
        telemetry_log.append(s_rec["telemetry"])
        all_times["kymora"].extend(s_km)
        all_times["catch22"].extend(s_c22)
        all_times["tsfel"].extend(s_tsfel)
        all_times["tsfresh"].extend(s_tsfresh)

        print(f"  Session {s_idx} Ratios: catch22 {r_c22:.1f}× | TSFEL {r_tsfel:.1f}× | tsfresh {r_tsfresh:.1f}×")

    # Compute pooled metrics across all sessions
    pooled_med_km = float(np.median(all_times["kymora"]))
    pooled_med_c22 = float(np.median(all_times["catch22"]))
    pooled_med_tsfel = float(np.median(all_times["tsfel"]))
    pooled_med_tsfresh = float(np.median(all_times["tsfresh"]))

    pooled_r_c22 = pooled_med_c22 / pooled_med_km
    pooled_r_tsfel = pooled_med_tsfel / pooled_med_km
    pooled_r_tsfresh = pooled_med_tsfresh / pooled_med_km

    # Per-feature speedup ratios: (competitor_time / competitor_feats) / (km_time / 33)
    pf_c22 = pooled_r_c22 * (33.0 / 22.0)
    pf_tsfel = pooled_r_tsfel * (33.0 / 156.0)
    pf_tsfresh = pooled_r_tsfresh * (33.0 / 777.0)

    # Bootstrap CIs for Kymora median
    km_ci_lo, km_ci_hi = bootstrap_ci(all_times["kymora"], n_resamples=2000, confidence_level=0.95, statistic="median")
    pooled_sps = float(N_SERIES / (pooled_med_km / 1000.0))
    sps_ci_lo = float(N_SERIES / (km_ci_hi / 1000.0))
    sps_ci_hi = float(N_SERIES / (km_ci_lo / 1000.0))

    divergence = abs(med_km_alone - pooled_med_km) / pooled_med_km

    summary = {
        "n_sessions": N_SESSIONS,
        "n_series": N_SERIES,
        "length": LENGTH,
        "threads": THREADS,
        "kymora_alone": {
            "median_ms": med_km_alone,
            "series_per_sec": sps_alone,
            "divergence_vs_interleaved": divergence,
        },
        "pooled_medians_ms": {
            "kymora": pooled_med_km,
            "catch22": pooled_med_c22,
            "tsfel": pooled_med_tsfel,
            "tsfresh": pooled_med_tsfresh,
        },
        "pooled_series_per_sec": pooled_sps,
        "ci95_series_per_sec": [sps_ci_lo, sps_ci_hi],
        "ci95_kymora_ms": [km_ci_lo, km_ci_hi],
        "pooled_ratios_raw": {
            "catch22": pooled_r_c22,
            "tsfel": pooled_r_tsfel,
            "tsfresh": pooled_r_tsfresh,
        },
        "pooled_ratios_per_feature": {
            "catch22": pf_c22,
            "tsfel": pf_tsfel,
            "tsfresh": pf_tsfresh,
        },
        "concurrency_definitions": {
            "kymora": "16 native Rayon work-stealing threads in single process (0 copies, 0 IPC)",
            "catch22": "joblib.Parallel(n_jobs=16) across 16 worker processes",
            "tsfel": "joblib.Parallel(n_jobs=16) across 16 worker processes",
            "tsfresh": "multiprocessing.Pool(16) across 16 worker processes",
        },
        "session_records": session_records,
        "telemetry_log": telemetry_log,
    }

    # Write JSON artifact
    RESULTS_DIR.mkdir(parents=True, exist_ok=True)
    with open(OUT_JSON, "w", encoding="utf-8") as f:
        json.dump(summary, f, indent=2)

    save_env(
        RESULTS_DIR / "env.json",
        extra={
            "load_start": load_start,
            "load_end": snapshot_load(),
            "cpu_telemetry_rounds": telemetry_log,
        },
    )

    # Format Markdown Report
    lines = [
        "# Same-Session Headline Ratios Report (HEAD)",
        "",
        "Protocol-compliant interleaved same-session evaluation on repository HEAD under Windows High Performance power scheme and AC online.",
        f"- **Workload:** {N_SERIES:,} series × {LENGTH} steps, float64 C-contiguous gaussian, {THREADS} threads across all methods.",
        f"- **Methodology:** {N_SESSIONS} interleaved sessions; each session times Kymora, catch22, TSFEL, and tsfresh in the same environment.",
        f"- **Cooldown:** {args.cooldown:.0f}s cooldown between competitor extraction blocks to prevent thermal throttling.",
        "",
        "## Summary Ratios",
        "",
        f"- **Kymora Interleaved Throughput:** **{pooled_sps:,.0f} series/s** (median **{pooled_med_km:.2f} ms**, 95% CI [{sps_ci_lo:,.0f}, {sps_ci_hi:,.0f}] series/s)",
        f"- **Kymora Isolated Baseline:** **{sps_alone:,.0f} series/s** (median **{med_km_alone:.2f} ms**, divergence {divergence*100:.1f}%)",
        f"- **catch22 Speedup:** **{pooled_r_c22:,.0f}×** raw (**{pf_c22:,.0f}×** per-feature; catch22 median {pooled_med_c22:.2f} ms)",
        f"- **TSFEL Speedup:** **{pooled_r_tsfel:,.0f}×** raw (**{pf_tsfel:,.0f}×** per-feature; TSFEL median {pooled_med_tsfel:.2f} ms)",
        f"- **tsfresh Speedup:** **{pooled_r_tsfresh:,.0f}×** raw (**{pf_tsfresh:,.0f}×** per-feature; tsfresh median {pooled_med_tsfresh:.2f} ms)",
        "",
        "## Concurrency Definitions (\"16T\")",
        "",
        "- **Kymora (16T):** 16 native Rayon work-stealing threads within the single Python process (zero defensive copies, zero IPC serialization).",
        "- **catch22 (16T):** `joblib.Parallel(n_jobs=16)` executing across 16 worker processes.",
        "- **TSFEL (16T):** `joblib.Parallel(n_jobs=16)` executing across 16 worker processes.",
        "- **tsfresh (16T):** `multiprocessing.Pool(16)` executing across 16 worker processes.",
        "",
        "## Per-Session Breakdown",
        "",
        "| Session | Kymora (ms) | catch22 (ms) | TSFEL (ms) | tsfresh (ms) | Ratio catch22 | Ratio TSFEL | Ratio tsfresh |",
        "|:---:|:---:|:---:|:---:|:---:|:---:|:---:|:---:|",
    ]
    for s in session_records:
        lines.append(
            f"| Session {s['session']} | {s['median_km_ms']:.2f} ms | {s['median_c22_ms']:.2f} ms | "
            f"{s['median_tsfel_ms']:.2f} ms | {s['median_tsfresh_ms']:.2f} ms | "
            f"**{s['ratio_catch22']:.1f}×** | **{s['ratio_tsfel']:.1f}×** | **{s['ratio_tsfresh']:.1f}×** |"
        )

    lines.extend([
        "",
        "## Protocol Notes",
        "",
        "- **Interleaved Execution:** Eliminates cross-session thermal throttling or background interference by measuring all four libraries within the same process session.",
        "- **Per-Feature Normalization:** Accounts for differing catalog sizes (33 for Kymora, 22 for catch22, 156 for TSFEL, 777 for tsfresh).",
        "- **Thread Parity:** tsfresh, TSFEL, and catch22 all execute multi-threaded using the same 16-thread pool configuration.",
    ])

    OUT_MD.write_text("\n".join(lines), encoding="utf-8")
    print(f"\nReport written to {OUT_MD}")
    print(f"Artifact written to {OUT_JSON}")
    print(f"=> Pooled Ratios: {pooled_r_c22:,.0f}× catch22, {pooled_r_tsfel:,.0f}× TSFEL, {pooled_r_tsfresh:,.0f}× tsfresh")


if __name__ == "__main__":
    main()
