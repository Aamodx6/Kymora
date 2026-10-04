"""Phase B3: Throughput benchmark suite.

Measures raw throughput (wall-clock, µs/series-feature) across:
  shapes × distributions × libraries × feature_sets

Per arch.md §11.5 (throughput suite) and §11.2 (harness protocol):
- Warmup runs, GC disabled during timing
- ≥15 runs or ≥2s budget (whichever is larger)
- Records min/median/IQR/mean/p95/CV
- Three views: raw runtime, µs/series-feature, matched-feature runtime
- Result schema per §11.8 (JSONL)
"""

from __future__ import annotations

import gc
import json
import os
import sys
import time
from datetime import datetime
from pathlib import Path
from typing import Any

import numpy as np

# Add project root to path
sys.path.insert(0, str(Path(__file__).resolve().parent.parent.parent))

from benches.adapters.tsxtract import Adapter as TsxtractAdapter
from benches.adapters.numpy_baseline import Adapter as NumpyAdapter
from benches.adapters.numba_baseline import Adapter as NumbaAdapter
from benches.datasets.generators import generate_series, ALL_DISTRIBUTIONS

RESULTS_DIR = Path(__file__).resolve().parent.parent / "results"

# ── Configuration ──

# Default throughput shapes (subset of arch.md §11.4 for practical runtime)
THROUGHPUT_SHAPES = [
    (10, 500),
    (100, 500),
    (1000, 500),
    (10_000, 500),
    (100, 100),
    (1000, 100),
    (100, 5000),
    (1, 100),
    (1, 10_000),
]

# Distributions to benchmark (subset for throughput; full set in agreement)
THROUGHPUT_DISTS = [
    "gaussian",
    "random_walk",
    "ar1",
    "heavy_tailed",
    "sinusoid",
]

# Minimum timing protocol
MIN_RUNS = 7
MIN_BUDGET_S = 2.0
WARMUP_RUNS = 3


def compute_stats(times_ns: list[float]) -> dict[str, float]:
    """Compute summary statistics from a list of timing measurements (nanoseconds)."""
    arr = np.array(times_ns, dtype=np.float64)
    arr_ms = arr / 1e6  # Convert to milliseconds

    n = len(arr_ms)
    sorted_ms = np.sort(arr_ms)

    mean = float(np.mean(arr_ms))
    median = float(np.median(arr_ms))
    mn = float(sorted_ms[0])
    p95 = float(np.percentile(arr_ms, 95))
    q1 = float(np.percentile(arr_ms, 25))
    q3 = float(np.percentile(arr_ms, 75))
    iqr = q3 - q1
    std = float(np.std(arr_ms, ddof=1)) if n > 1 else 0.0
    cv = std / mean if mean > 0 else 0.0

    return {
        "min_ms": mn,
        "median_ms": median,
        "mean_ms": mean,
        "p95_ms": p95,
        "iqr_ms": iqr,
        "cv": cv,
        "n_runs": n,
        "raw_ms": sorted_ms.tolist(),
    }


def time_extraction(
    adapter,
    X: np.ndarray,
    feature_set: str,
    threads: int,
    n_warmup: int = WARMUP_RUNS,
    min_runs: int = MIN_RUNS,
    min_budget_s: float = MIN_BUDGET_S,
    **kwargs,
) -> dict[str, Any]:
    """Time a feature extraction call with proper benchmarking protocol."""
    # Warmup
    for _ in range(n_warmup):
        adapter.extract(X, feature_set=feature_set, threads=threads, **kwargs)

    # Timed runs
    times_ns = []
    start_budget = time.perf_counter_ns()
    budget_ns = int(min_budget_s * 1e9)

    gc_was_enabled = gc.isenabled()
    gc.disable()
    try:
        while True:
            t0 = time.perf_counter_ns()
            result = adapter.extract(X, feature_set=feature_set, threads=threads, **kwargs)
            t1 = time.perf_counter_ns()
            times_ns.append(t1 - t0)

            elapsed = t1 - start_budget
            if len(times_ns) >= min_runs and elapsed >= budget_ns:
                break
            # Safety cap
            if len(times_ns) >= 200:
                break
    finally:
        if gc_was_enabled:
            gc.enable()

    stats = compute_stats(times_ns)
    n_series, length = X.shape
    n_features = result.shape[1] if result.ndim == 2 else 1

    # Compute µs/series-feature
    us_per_sf = (stats["median_ms"] * 1000) / (n_series * n_features) if n_series > 0 and n_features > 0 else float("nan")

    stats["us_per_series_feature"] = us_per_sf
    stats["n_features"] = n_features
    stats["n_series"] = n_series
    stats["length"] = length

    return stats


def load_competitor_adapters() -> dict[str, Any]:
    """Load all available competitor adapters."""
    competitors = {}

    try:
        from benches.adapters.tsfresh_ import Adapter as TsfreshAdapter
        competitors["tsfresh"] = TsfreshAdapter()
    except Exception:
        pass

    try:
        from benches.adapters.tsfel_ import Adapter as TsfelAdapter
        competitors["tsfel"] = TsfelAdapter()
    except Exception:
        pass

    try:
        from benches.adapters.catch22_ import Adapter as Catch22Adapter
        competitors["catch22"] = Catch22Adapter()
    except Exception:
        pass

    return competitors


def run_throughput_suite(
    shapes: list[tuple[int, int]] | None = None,
    distributions: list[str] | None = None,
    threads: int | None = None,
    include_competitors: bool = True,
    output_file: str | None = None,
):
    """Run the full throughput benchmark suite."""
    if shapes is None:
        shapes = THROUGHPUT_SHAPES
    if distributions is None:
        distributions = THROUGHPUT_DISTS
    if threads is None:
        threads = min(os.cpu_count() or 4, 16)

    print("=" * 80)
    print("  Phase B3: Throughput Benchmark Suite")
    print("=" * 80)
    print()

    # ── 1. Initialize adapters ──
    print("1. Initializing adapters...")
    tsx = TsxtractAdapter()
    np_baseline = NumpyAdapter()
    nb_baseline = NumbaAdapter()
    print(f"   Tsxtract: {tsx.version}")
    print(f"   NumPy baseline: {np_baseline.version}")
    print(f"   Numba baseline: {nb_baseline.version}")

    adapters = {
        "tsxtract": (tsx, "core33", {}),
        "numpy_baseline": (np_baseline, "default", {}),
        "numba_baseline_fast": (nb_baseline, "fast", {"fastmath": True}),
    }

    if include_competitors:
        print("\n2. Loading competitors...")
        competitors = load_competitor_adapters()
        for name, adapter in competitors.items():
            adapters[name] = (adapter, "default", {})
            print(f"   ✅ {name}: {adapter.version}")
    else:
        print("\n2. Competitors: skipped")

    # ── 3. Run benchmarks ──
    print(f"\n3. Running throughput benchmarks...")
    print(f"   Shapes: {len(shapes)}")
    print(f"   Distributions: {len(distributions)}")
    print(f"   Libraries: {len(adapters)}")
    print(f"   Threads: {threads}")
    print(f"   Protocol: ≥{MIN_RUNS} runs, ≥{MIN_BUDGET_S}s budget, {WARMUP_RUNS} warmup")
    print()

    all_results = []
    total_combos = len(shapes) * len(distributions) * len(adapters)
    combo_idx = 0

    for n_series, length in shapes:
        for dist in distributions:
            # Generate data once per (shape, dist)
            X = generate_series(dist, n_series, length, seed=42)

            for lib_name, (adapter, feature_set, extra_kwargs) in adapters.items():
                combo_idx += 1
                label = f"[{combo_idx:3d}/{total_combos}] {lib_name:20s} {n_series:>7d}×{length:<6d} {dist}"
                print(f"   {label}...", end=" ", flush=True)

                try:
                    stats = time_extraction(
                        adapter, X,
                        feature_set=feature_set,
                        threads=threads,
                        **extra_kwargs,
                    )

                    record = {
                        "suite": "throughput",
                        "lib": lib_name,
                        "feature_set": feature_set,
                        "n_features": stats["n_features"],
                        "n_series": n_series,
                        "length": length,
                        "dist": dist,
                        "threads": threads,
                        "guarded": True,
                        "stats": {
                            "min_ms": stats["min_ms"],
                            "median_ms": stats["median_ms"],
                            "mean_ms": stats["mean_ms"],
                            "p95_ms": stats["p95_ms"],
                            "iqr_ms": stats["iqr_ms"],
                            "cv": stats["cv"],
                            "n_runs": stats["n_runs"],
                        },
                        "us_per_series_feature": stats["us_per_series_feature"],
                        "status": "ok",
                        "timestamp": datetime.now().isoformat(),
                    }

                    all_results.append(record)

                    # Print compact result
                    print(
                        f"median={stats['median_ms']:>10.3f}ms  "
                        f"µs/sf={stats['us_per_series_feature']:>8.3f}  "
                        f"CV={stats['cv']:>5.2f}  "
                        f"n={stats['n_runs']}"
                    )

                except Exception as e:
                    record = {
                        "suite": "throughput",
                        "lib": lib_name,
                        "feature_set": feature_set,
                        "n_series": n_series,
                        "length": length,
                        "dist": dist,
                        "threads": threads,
                        "guarded": True,
                        "status": "error",
                        "error_msg": f"{type(e).__name__}: {e}",
                        "timestamp": datetime.now().isoformat(),
                    }
                    all_results.append(record)
                    print(f"ERROR: {type(e).__name__}: {e}")

    # ── 4. Save results ──
    RESULTS_DIR.mkdir(parents=True, exist_ok=True)
    if output_file is None:
        output_file = RESULTS_DIR / "throughput.jsonl"
    else:
        output_file = Path(output_file)

    with open(output_file, "w", encoding="utf-8") as f:
        for rec in all_results:
            f.write(json.dumps(rec) + "\n")

    print(f"\n4. Saved {len(all_results)} records to {output_file}")

    # ── 5. Summary table ──
    print("\n" + "=" * 80)
    print("  Summary: Median throughput (ms) per library @ key shapes")
    print("=" * 80)

    # Pivot: lib × shape
    summary_shapes = [(100, 500), (1000, 500), (10_000, 500)]
    lib_names = list(adapters.keys())

    header = f"{'Library':25s}"
    for n, l in summary_shapes:
        header += f"  {n}×{l:>5d}"
    header += "  µs/sf(1k×500)"
    print(header)
    print("-" * len(header))

    for lib in lib_names:
        row = f"{lib:25s}"
        for n, l in summary_shapes:
            matching = [
                r for r in all_results
                if r["lib"] == lib and r["n_series"] == n and r["length"] == l
                and r["status"] == "ok" and r["dist"] == "gaussian"
            ]
            if matching:
                row += f"  {matching[0]['stats']['median_ms']:>10.3f}"
            else:
                row += f"  {'N/A':>10s}"

        # µs/sf at 1k×500
        matching_1k = [
            r for r in all_results
            if r["lib"] == lib and r["n_series"] == 1000 and r["length"] == 500
            and r["status"] == "ok" and r["dist"] == "gaussian"
        ]
        if matching_1k:
            row += f"  {matching_1k[0]['us_per_series_feature']:>13.3f}"
        else:
            row += f"  {'N/A':>13s}"

        print(row)

    # ── 6. Ratio table ──
    print("\n" + "-" * 80)
    print("  Speedup ratios vs Tsxtract @ 1000×500 gaussian (median)")
    print("-" * 80)

    tsx_1k = [
        r for r in all_results
        if r["lib"] == "tsxtract" and r["n_series"] == 1000 and r["length"] == 500
        and r["status"] == "ok" and r["dist"] == "gaussian"
    ]
    if tsx_1k:
        tsx_median = tsx_1k[0]["stats"]["median_ms"]
        for lib in lib_names:
            if lib == "tsxtract":
                continue
            matching = [
                r for r in all_results
                if r["lib"] == lib and r["n_series"] == 1000 and r["length"] == 500
                and r["status"] == "ok" and r["dist"] == "gaussian"
            ]
            if matching:
                lib_median = matching[0]["stats"]["median_ms"]
                raw_ratio = lib_median / tsx_median if tsx_median > 0 else float("inf")
                n_feat_lib = matching[0].get("n_features", 33)
                n_feat_tsx = tsx_1k[0].get("n_features", 33)
                pf_ratio = (lib_median / n_feat_lib) / (tsx_median / n_feat_tsx) if n_feat_tsx > 0 and n_feat_lib > 0 else float("nan")
                print(f"  {lib:25s}  raw={raw_ratio:>8.1f}×  per-feat={pf_ratio:>8.1f}×")

    print("\n" + "=" * 80)
    return all_results


if __name__ == "__main__":
    import argparse

    parser = argparse.ArgumentParser(description="B3 Throughput Suite")
    parser.add_argument("--no-competitors", action="store_true", help="Skip competitor libraries")
    parser.add_argument("--quick", action="store_true", help="Quick mode: fewer shapes/dists")
    parser.add_argument("--threads", type=int, default=None, help="Thread count")
    args = parser.parse_args()

    if args.quick:
        shapes = [(100, 500), (1000, 500)]
        dists = ["gaussian"]
    else:
        shapes = None
        dists = None

    run_throughput_suite(
        shapes=shapes,
        distributions=dists,
        threads=args.threads,
        include_competitors=not args.no_competitors,
    )
