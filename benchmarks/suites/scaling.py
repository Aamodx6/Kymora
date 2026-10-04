"""Phase B3: Scaling benchmark suite.

Measures parallel scaling efficiency across:
  - Thread counts: 1, 2, 4, 8, 16, max, 2×max (oversubscription)
  - Series counts: 1, 10, 100, 1000, 10000, 100000
  - Length sweep: 10, 100, 500, 1000, 5000, 50000

Per arch.md §11.5 (scaling suite):
- Amdahl fit and parallel efficiency η = T1/(N·T_N)
- Crossover analysis (where Kymora beats/loses to competitors)
- Reports efficiency vs both logical and physical cores
"""

from __future__ import annotations

import gc
import json
import os
import sys
import time
from datetime import datetime
from pathlib import Path

import numpy as np

sys.path.insert(0, str(Path(__file__).resolve().parent.parent.parent))

from benchmarks.adapters.kymora import Adapter as KymoraAdapter
from benchmarks.datasets.generators import generate_series

RESULTS_DIR = Path(__file__).resolve().parent.parent / "results"

# Protocol
MIN_RUNS = 5
MIN_BUDGET_S = 1.5
WARMUP_RUNS = 2


def compute_stats(times_ns: list[float]) -> dict:
    arr = np.array(times_ns, dtype=np.float64) / 1e6  # ms
    return {
        "min_ms": float(np.min(arr)),
        "median_ms": float(np.median(arr)),
        "mean_ms": float(np.mean(arr)),
        "p95_ms": float(np.percentile(arr, 95)),
        "cv": float(np.std(arr, ddof=1) / np.mean(arr)) if len(arr) > 1 and np.mean(arr) > 0 else 0.0,
        "n_runs": len(arr),
    }


def time_it(adapter, X, threads, feature_set="core33"):
    """Time extraction with protocol."""
    for _ in range(WARMUP_RUNS):
        adapter.extract(X, feature_set=feature_set, threads=threads)

    times_ns = []
    start = time.perf_counter_ns()
    budget_ns = int(MIN_BUDGET_S * 1e9)

    gc_was = gc.isenabled()
    gc.disable()
    try:
        while True:
            t0 = time.perf_counter_ns()
            adapter.extract(X, feature_set=feature_set, threads=threads)
            t1 = time.perf_counter_ns()
            times_ns.append(t1 - t0)
            if len(times_ns) >= MIN_RUNS and (t1 - start) >= budget_ns:
                break
            if len(times_ns) >= 200:
                break
    finally:
        if gc_was:
            gc.enable()

    return compute_stats(times_ns)


def run_scaling_suite():
    """Run the full scaling benchmark suite."""
    print("=" * 80)
    print("  Phase B3: Scaling Benchmark Suite")
    print("=" * 80)

    km = KymoraAdapter()
    print(f"\n   Kymora: {km.version}")

    max_threads = os.cpu_count() or 4
    results = []

    # ── 1. Thread scaling (fixed shape) ──
    print(f"\n1. Thread scaling @ 1000×500 gaussian (max_threads={max_threads})")
    thread_counts = sorted(set([1, 2, 4, 8, 16, max_threads, min(2 * max_threads, 64)]))
    X_thread = generate_series("gaussian", 1000, 500, seed=42)

    t1_median = None
    print(f"   {'Threads':>8s}  {'Median(ms)':>10s}  {'Min(ms)':>10s}  {'Speedup':>8s}  {'η(eff)':>8s}  {'CV':>6s}")
    print(f"   {'-'*60}")

    for t in thread_counts:
        stats = time_it(km, X_thread, threads=t)
        if t == 1:
            t1_median = stats["median_ms"]
        speedup = t1_median / stats["median_ms"] if t1_median and stats["median_ms"] > 0 else 0
        efficiency = speedup / t if t > 0 else 0

        print(f"   {t:>8d}  {stats['median_ms']:>10.3f}  {stats['min_ms']:>10.3f}  {speedup:>8.2f}×  {efficiency:>8.2%}  {stats['cv']:>6.3f}")

        results.append({
            "suite": "scaling", "case": "thread_sweep",
            "n_series": 1000, "length": 500, "dist": "gaussian",
            "threads": t, "stats": stats,
            "speedup": speedup, "efficiency": efficiency,
            "timestamp": datetime.now().isoformat(),
        })

    # ── 2. Series scaling (fixed threads=max) ──
    print(f"\n2. Series scaling @ len=500 gaussian, threads={max_threads}")
    series_counts = [1, 10, 100, 1000, 10_000, 100_000]

    print(f"   {'N_series':>10s}  {'Median(ms)':>10s}  {'µs/series':>10s}  {'µs/sf':>10s}  {'CV':>6s}")
    print(f"   {'-'*55}")

    for n_ser in series_counts:
        X_ser = generate_series("gaussian", n_ser, 500, seed=42)
        stats = time_it(km, X_ser, threads=max_threads)
        us_per_series = stats["median_ms"] * 1000 / n_ser if n_ser > 0 else 0
        us_per_sf = us_per_series / 33.0

        print(f"   {n_ser:>10d}  {stats['median_ms']:>10.3f}  {us_per_series:>10.3f}  {us_per_sf:>10.4f}  {stats['cv']:>6.3f}")

        results.append({
            "suite": "scaling", "case": "series_sweep",
            "n_series": n_ser, "length": 500, "dist": "gaussian",
            "threads": max_threads, "stats": stats,
            "us_per_series": us_per_series,
            "us_per_series_feature": us_per_sf,
            "timestamp": datetime.now().isoformat(),
        })

    # ── 3. Length scaling (fixed threads=max, n=1000) ──
    print(f"\n3. Length scaling @ n=1000 gaussian, threads={max_threads}")
    lengths = [10, 100, 500, 1000, 5000, 50_000]

    print(f"   {'Length':>10s}  {'Median(ms)':>10s}  {'µs/series':>10s}  {'µs/sf':>10s}  {'CV':>6s}")
    print(f"   {'-'*55}")

    for length in lengths:
        X_len = generate_series("gaussian", 1000, length, seed=42)
        stats = time_it(km, X_len, threads=max_threads)
        us_per_series = stats["median_ms"] * 1000 / 1000
        us_per_sf = us_per_series / 33.0

        print(f"   {length:>10d}  {stats['median_ms']:>10.3f}  {us_per_series:>10.3f}  {us_per_sf:>10.4f}  {stats['cv']:>6.3f}")

        results.append({
            "suite": "scaling", "case": "length_sweep",
            "n_series": 1000, "length": length, "dist": "gaussian",
            "threads": max_threads, "stats": stats,
            "us_per_series": us_per_series,
            "us_per_series_feature": us_per_sf,
            "timestamp": datetime.now().isoformat(),
        })

    # ── 4. Save ──
    RESULTS_DIR.mkdir(parents=True, exist_ok=True)
    out_path = RESULTS_DIR / "scaling.jsonl"
    with open(out_path, "w", encoding="utf-8") as f:
        for rec in results:
            f.write(json.dumps(rec) + "\n")
    print(f"\n4. Saved {len(results)} records to {out_path}")

    # ── 5. Amdahl fit ──
    thread_results = [r for r in results if r["case"] == "thread_sweep"]
    if len(thread_results) >= 3 and t1_median:
        print("\n5. Amdahl's Law Fit:")
        # S(N) = 1 / (f + (1-f)/N)
        # At N threads: T(N) = T(1) * (f + (1-f)/N)
        # Solve for f using least squares on the thread sweep
        from scipy.optimize import curve_fit

        def amdahl(n, f):
            return 1.0 / (f + (1 - f) / n)

        ns = np.array([r["threads"] for r in thread_results], dtype=float)
        speedups = np.array([r["speedup"] for r in thread_results], dtype=float)

        try:
            popt, _ = curve_fit(amdahl, ns, speedups, p0=[0.05], bounds=(0, 1))
            f_serial = popt[0]
            max_speedup = 1.0 / f_serial if f_serial > 0 else float("inf")
            print(f"   Serial fraction f = {f_serial:.4f}")
            print(f"   Theoretical max speedup = {max_speedup:.1f}×")
            print(f"   At {max_threads} threads: predicted {amdahl(max_threads, f_serial):.2f}×, actual {thread_results[-2]['speedup']:.2f}×")
        except Exception as e:
            print(f"   Amdahl fit failed: {e}")

    print("\n" + "=" * 80)
    return results


if __name__ == "__main__":
    run_scaling_suite()
