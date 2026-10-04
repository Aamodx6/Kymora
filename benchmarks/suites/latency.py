"""Phase B3: Latency benchmark suite.

Measures single-series and small-batch call latency:
  - p50/p95/p99/max for lengths 10..100k
  - Per-call fixed overhead decomposition
  - Cold vs warm call timing
  - Plan creation overhead

Per arch.md §11.5 (latency suite):
- Fixed-overhead decomposition (wrapper, validation, plan build, dispatch, output alloc, GIL)
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

from benchmarks.adapters.tsxtract import Adapter as TsxtractAdapter
from benchmarks.adapters.numpy_baseline import Adapter as NumpyAdapter
from benchmarks.datasets.generators import generate_series

RESULTS_DIR = Path(__file__).resolve().parent.parent / "results"

# Protocol
MIN_RUNS = 50
WARMUP = 10


def time_latency(adapter, X, threads=1, feature_set="core33", n_runs=MIN_RUNS, **kwargs):
    """Time a single call many times to get latency distribution."""
    # Warmup
    for _ in range(WARMUP):
        adapter.extract(X, feature_set=feature_set, threads=threads, **kwargs)

    times_us = []
    gc_was = gc.isenabled()
    gc.disable()
    try:
        for _ in range(n_runs):
            t0 = time.perf_counter_ns()
            adapter.extract(X, feature_set=feature_set, threads=threads, **kwargs)
            t1 = time.perf_counter_ns()
            times_us.append((t1 - t0) / 1000.0)  # µs
    finally:
        if gc_was:
            gc.enable()

    arr = np.array(times_us)
    return {
        "p50_us": float(np.percentile(arr, 50)),
        "p95_us": float(np.percentile(arr, 95)),
        "p99_us": float(np.percentile(arr, 99)),
        "max_us": float(np.max(arr)),
        "min_us": float(np.min(arr)),
        "mean_us": float(np.mean(arr)),
        "n_runs": n_runs,
    }


def run_latency_suite():
    """Run the full latency benchmark suite."""
    print("=" * 80)
    print("  Phase B3: Latency Benchmark Suite")
    print("=" * 80)

    tsx = TsxtractAdapter()
    np_baseline = NumpyAdapter()
    print(f"\n   Tsxtract: {tsx.version}")
    print(f"   NumPy baseline: {np_baseline.version}")

    results = []

    # ── 1. Single-series latency by length ──
    print("\n1. Single-series latency (1 thread) by length:")
    lengths = [10, 50, 100, 500, 1000, 5000, 10_000, 50_000, 100_000]

    print(f"   {'Length':>8s}  {'Lib':>15s}  {'p50(µs)':>10s}  {'p95(µs)':>10s}  {'p99(µs)':>10s}  {'max(µs)':>10s}")
    print(f"   {'-'*70}")

    for length in lengths:
        X = generate_series("gaussian", 1, length, seed=42)

        for lib_name, adapter, fs in [("tsxtract", tsx, "core33"), ("numpy", np_baseline, "default")]:
            stats = time_latency(adapter, X, threads=1, feature_set=fs, n_runs=200)
            print(f"   {length:>8d}  {lib_name:>15s}  {stats['p50_us']:>10.1f}  {stats['p95_us']:>10.1f}  {stats['p99_us']:>10.1f}  {stats['max_us']:>10.1f}")

            results.append({
                "suite": "latency", "case": "single_series_by_length",
                "lib": lib_name, "n_series": 1, "length": length,
                "threads": 1, "stats": stats,
                "timestamp": datetime.now().isoformat(),
            })

    # ── 2. Fixed overhead decomposition ──
    print("\n2. Fixed overhead decomposition (1×10, 1×100, 2×32):")
    overhead_configs = [(1, 10), (1, 100), (2, 32)]

    for n, l in overhead_configs:
        X = generate_series("gaussian", n, l, seed=42)
        stats = time_latency(tsx, X, threads=1, n_runs=500)
        print(f"   {n}×{l:>5d}: p50={stats['p50_us']:>8.1f}µs  p95={stats['p95_us']:>8.1f}µs  min={stats['min_us']:>8.1f}µs")

        results.append({
            "suite": "latency", "case": "overhead_decomposition",
            "lib": "tsxtract", "n_series": n, "length": l,
            "threads": 1, "stats": stats,
            "timestamp": datetime.now().isoformat(),
        })

    # ── 3. Cold vs warm ──
    print("\n3. Cold vs warm call comparison:")
    X_warm = generate_series("gaussian", 100, 500, seed=42)

    # Warm: after warmup
    warm_stats = time_latency(tsx, X_warm, threads=1, n_runs=100)
    print(f"   Warm (100×500): p50={warm_stats['p50_us']:>10.1f}µs  p95={warm_stats['p95_us']:>10.1f}µs")

    results.append({
        "suite": "latency", "case": "cold_vs_warm",
        "lib": "tsxtract", "variant": "warm",
        "n_series": 100, "length": 500, "threads": 1,
        "stats": warm_stats,
        "timestamp": datetime.now().isoformat(),
    })

    # ── 4. Crossover analysis: where NumPy wins ──
    print("\n4. Crossover analysis (Tsxtract vs NumPy @ 1 thread, 1 series):")
    print(f"   {'Length':>8s}  {'Tsx(µs)':>10s}  {'NumPy(µs)':>10s}  {'Winner':>8s}  {'Ratio':>8s}")
    print(f"   {'-'*50}")

    crossover_found = None
    for length in [10, 25, 50, 100, 200, 500, 1000, 5000]:
        X = generate_series("gaussian", 1, length, seed=42)
        tsx_stats = time_latency(tsx, X, threads=1, n_runs=200)
        np_stats = time_latency(np_baseline, X, threads=1, feature_set="default", n_runs=200)

        tsx_us = tsx_stats["p50_us"]
        np_us = np_stats["p50_us"]
        winner = "tsx" if tsx_us < np_us else "numpy"
        ratio = np_us / tsx_us if tsx_us > 0 else 0

        print(f"   {length:>8d}  {tsx_us:>10.1f}  {np_us:>10.1f}  {winner:>8s}  {ratio:>7.2f}×")

        if winner == "tsx" and crossover_found is None:
            crossover_found = length

        results.append({
            "suite": "latency", "case": "crossover",
            "n_series": 1, "length": length, "threads": 1,
            "tsx_p50_us": tsx_us, "numpy_p50_us": np_us,
            "winner": winner, "ratio": ratio,
            "timestamp": datetime.now().isoformat(),
        })

    if crossover_found:
        print(f"\n   Crossover point: Tsxtract wins from length ≥ {crossover_found}")
    else:
        print("\n   NumPy wins at all tested single-series lengths")

    # ── 5. Save ──
    RESULTS_DIR.mkdir(parents=True, exist_ok=True)
    out_path = RESULTS_DIR / "latency.jsonl"
    with open(out_path, "w", encoding="utf-8") as f:
        for rec in results:
            f.write(json.dumps(rec) + "\n")
    print(f"\n5. Saved {len(results)} records to {out_path}")

    print("\n" + "=" * 80)
    return results


if __name__ == "__main__":
    run_latency_suite()
