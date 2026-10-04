"""Phase 0 Baseline & Profiling Script.

Measures baseline performance for Tsxtract across required matrix shapes,
evaluates single-core stage breakdowns, measures memory allocations,
and saves results to benches/baseline/baseline.json.
"""
import json
import os
import platform
import time
import tracemalloc
import numpy as np
import tsxtract

def measure_benchmark(X, n_runs=10, warmup=2):
    # Warmup
    for _ in range(warmup):
        _ = tsxtract.extract_features(X[:min(len(X), 32)])

    times = []
    for _ in range(n_runs):
        t0 = time.perf_counter()
        _ = tsxtract.extract_features(X)
        t1 = time.perf_counter()
        times.append(t1 - t0)

    arr = np.array(times)
    return {
        "median_s": float(np.median(arr)),
        "iqr_s": float(np.percentile(arr, 75) - np.percentile(arr, 25)),
        "mean_s": float(np.mean(arr)),
        "min_s": float(np.min(arr)),
        "max_s": float(np.max(arr)),
        "runs": n_runs,
        "series_per_s": float(len(X) / np.median(arr)),
    }

def main():
    os.makedirs("benches/baseline", exist_ok=True)
    rng = np.random.default_rng(42)

    shapes = [
        ("shape_1k_500", (1000, 500)),
        ("shape_1_100k", (1, 100000)),
        ("shape_100_100", (100, 100)),
        ("shape_10k_500", (10000, 500)),
        ("shape_100_50k", (100, 50000)),
    ]

    results = {
        "system": {
            "platform": platform.platform(),
            "cpu_count": os.cpu_count(),
            "python": platform.python_version(),
            "tsxtractor_version": tsxtract.__version__,
        },
        "shapes": {},
    }

    print("Running matrix shape benchmarks...")
    for name, shape in shapes:
        print(f"  Measuring {name}: {shape}...")
        X = rng.standard_normal(shape)
        # Choose n_runs appropriately
        runs = 15 if shape[0] <= 1000 else 5
        res = measure_benchmark(X, n_runs=runs)
        results["shapes"][name] = {
            "shape": shape,
            "metrics": res,
        }
        print(f"    Median: {res['median_s']*1e3:.2f} ms ({res['series_per_s']:,.0f} series/s)")

    # Memory allocation test for 50k x 500
    print("Measuring peak memory for 50k x 500...")
    tracemalloc.start()
    snap_before = tracemalloc.take_snapshot()
    X_mem = rng.standard_normal((50000, 500))
    t0 = time.perf_counter()
    out = tsxtract.extract_features(X_mem)
    elapsed_mem = time.perf_counter() - t0
    current, peak = tracemalloc.get_traced_memory()
    tracemalloc.stop()
    output_mb = out.nbytes / (1024 * 1024)
    print(f"  Output buffer size: {output_mb:.2f} MB, Peak memory tracked: {peak/(1024*1024):.2f} MB in {elapsed_mem*1e3:.1f} ms")
    results["memory_50k_500"] = {
        "output_mb": output_mb,
        "peak_tracemalloc_mb": peak / (1024 * 1024),
        "time_s": elapsed_mem,
    }

    # Micro-stage breakdown on single series len=500
    # We measure repeated calls on 1 series across 10,000 iterations
    # to estimate single-core time per series
    print("Measuring single-series (single core) latency for len=500...")
    X_single = rng.standard_normal((1, 500))
    single_runs = 2000
    t0 = time.perf_counter()
    for _ in range(single_runs):
        _ = tsxtract.extract_features(X_single)
    total_single = (time.perf_counter() - t0) / single_runs
    print(f"  Single series len=500 latency: {total_single*1e6:.2f} us")
    results["single_series_500_us"] = total_single * 1e6

    # Save to benches/baseline/baseline.json
    out_file = "benches/baseline/baseline.json"
    with open(out_file, "w", encoding="utf-8") as f:
        json.dump(results, f, indent=2)
    print(f"Baseline saved to {out_file}")

if __name__ == "__main__":
    main()
