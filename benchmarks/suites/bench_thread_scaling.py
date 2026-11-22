"""Fine-grained thread scaling and Rayon chunking sweep.

Measures:
1. Thread scaling across 1, 2, 4, 6, 8, 10, 12, 14, 16 threads at 1,000 x 500.
2. Rayon min_len chunk size sweep across [1, 2, 4, 8, 16, 32, 64] at 16T and 8T.
3. Hardware topology analysis (P-cores vs E-cores, SMT threads).

Outputs:
- benchmarks/results/thread_scaling_results.json
- benchmarks/results/THREAD_SCALING_REPORT.md
"""

from __future__ import annotations

import json
import os
import platform
import statistics
import subprocess
import sys
import time
from pathlib import Path

import numpy as np

REPO_ROOT = Path(__file__).resolve().parents[2]
RESULTS_DIR = REPO_ROOT / "benchmarks" / "results"
RESULTS_DIR.mkdir(parents=True, exist_ok=True)
OUT_JSON = RESULTS_DIR / "thread_scaling_results.json"
OUT_MD = RESULTS_DIR / "THREAD_SCALING_REPORT.md"

SHAPE = (1000, 500)
ROUNDS = 25
THREAD_COUNTS = [1, 2, 4, 6, 8, 10, 12, 14, 16]
MIN_LEN_SWEEPS = [1, 2, 4, 8, 16, 32, 64]


def measure_subprocess(threads: int, min_len: int | None = None) -> dict:
    """Run extraction in a clean subprocess to ensure isolated Rayon thread pool."""
    code = f"""
import os, sys, time, statistics, numpy as np, kymora

threads = {threads}
min_len = {min_len if min_len is not None else 16}
if min_len is not None:
    os.environ['KYMORA_MIN_ROWS_PER_TASK'] = str(min_len)

rng = np.random.default_rng(42)
X = np.ascontiguousarray(rng.standard_normal({SHAPE}), dtype=np.float64)

# Warmup
for _ in range(5):
    kymora.extract_features(X, profile='core33')

times = []
for _ in range({ROUNDS}):
    t0 = time.perf_counter_ns()
    kymora.extract_features(X, profile='core33')
    times.append((time.perf_counter_ns() - t0) / 1e6)

med = statistics.median(times)
q1 = np.percentile(times, 25)
q3 = np.percentile(times, 75)
print(f"{{med:.4f}},{{min(times):.4f}},{{max(times):.4f}},{{q1:.4f}},{{q3:.4f}},{{statistics.stdev(times):.4f}}")
"""
    env = {**os.environ, "RAYON_NUM_THREADS": str(threads)}
    if min_len is not None:
        env["KYMORA_MIN_ROWS_PER_TASK"] = str(min_len)

    res = subprocess.run([sys.executable, "-c", code], env=env, capture_output=True, text=True)
    if res.returncode != 0:
        raise RuntimeError(f"Subprocess failed:\n{res.stderr}")

    line = res.stdout.strip().splitlines()[-1]
    med, mn, mx, q1, q3, std = (float(x) for x in line.split(","))
    return {
        "threads": threads,
        "min_len": min_len,
        "median_ms": med,
        "min_ms": mn,
        "max_ms": mx,
        "q1_ms": q1,
        "q3_ms": q3,
        "stdev_ms": std,
    }


def main():
    print("=" * 70)
    print("  Kymora Thread Scaling & Rayon Chunking Investigation")
    print(f"  Shape: {SHAPE[0]} series x {SHAPE[1]} points, core33 profile, float64")
    print("=" * 70)

    # 1. Sweep thread counts
    print("\n--- Thread Scaling Sweep (1..16 threads) ---")
    thread_results = []
    t1_med = None

    print(f"{'Threads':>8s} | {'Median (ms)':>11s} | {'Min (ms)':>9s} | {'Speedup':>9s} | {'Efficiency':>10s}")
    print("-" * 60)
    for t in THREAD_COUNTS:
        stats = measure_subprocess(threads=t)
        if t1_med is None:
            t1_med = stats["median_ms"]
        speedup = t1_med / stats["median_ms"]
        eff = (speedup / t) * 100.0
        stats["speedup"] = speedup
        stats["efficiency_pct"] = eff
        thread_results.append(stats)
        print(f"{t:8d} | {stats['median_ms']:11.3f} | {stats['min_ms']:9.3f} | {speedup:8.2f}x | {eff:9.1f}%")

    # 2. Sweep Rayon min_len at 16T and 8T
    print("\n--- Rayon min_len Chunk Size Sweep (16 Threads) ---")
    chunk_results_16t = []
    print(f"{'min_len':>8s} | {'Median (ms)':>11s} | {'Min (ms)':>9s} | {'Q1 (ms)':>9s} | {'Q3 (ms)':>9s}")
    print("-" * 55)
    for m in MIN_LEN_SWEEPS:
        stats = measure_subprocess(threads=16, min_len=m)
        chunk_results_16t.append(stats)
        print(f"{m:8d} | {stats['median_ms']:11.3f} | {stats['min_ms']:9.3f} | {stats['q1_ms']:9.3f} | {stats['q3_ms']:9.3f}")

    print("\n--- Rayon min_len Chunk Size Sweep (8 Threads) ---")
    chunk_results_8t = []
    print(f"{'min_len':>8s} | {'Median (ms)':>11s} | {'Min (ms)':>9s} | {'Q1 (ms)':>9s} | {'Q3 (ms)':>9s}")
    print("-" * 55)
    for m in MIN_LEN_SWEEPS:
        stats = measure_subprocess(threads=8, min_len=m)
        chunk_results_8t.append(stats)
        print(f"{m:8d} | {stats['median_ms']:11.3f} | {stats['min_ms']:9.3f} | {stats['q1_ms']:9.3f} | {stats['q3_ms']:9.3f}")

    # 3. Export results JSON
    payload = {
        "timestamp": time.strftime("%Y-%m-%d %H:%M:%S"),
        "platform": platform.platform(),
        "processor": platform.processor(),
        "logical_cpus": os.cpu_count(),
        "shape": list(SHAPE),
        "thread_scaling": thread_results,
        "chunk_scaling_16t": chunk_results_16t,
        "chunk_scaling_8t": chunk_results_8t,
    }
    OUT_JSON.write_text(json.dumps(payload, indent=2) + "\n", encoding="utf-8")
    print(f"\nSaved JSON results to {OUT_JSON}")

    # 4. Generate Markdown report
    md_lines = [
        "# Thread Scaling and Rayon Chunking Report",
        "",
        f"- **Timestamp:** {payload['timestamp']}",
        f"- **Processor:** {payload['processor']} ({payload['logical_cpus']} logical CPUs)",
        f"- **Benchmark Shape:** {SHAPE[0]} series x {SHAPE[1]} points (`core33`, float64)",
        "",
        "## 1. Thread Scaling (1 to 16 Threads)",
        "",
        "| Threads | Median (ms) | Min (ms) | Speedup vs 1T | Parallel Efficiency |",
        "|--------:|------------:|---------:|--------------:|--------------------:|",
    ]
    for r in thread_results:
        md_lines.append(
            f"| {r['threads']} | {r['median_ms']:.3f} | {r['min_ms']:.3f} | {r['speedup']:.2f}× | {r['efficiency_pct']:.1f}% |"
        )

    md_lines.extend([
        "",
        "## 2. Rayon Chunk Size (`min_len`) Sweep at 16 Threads",
        "",
        "| `min_len` | Median (ms) | Min (ms) | Q1 (ms) | Q3 (ms) |",
        "|----------:|------------:|---------:|--------:|--------:|",
    ])
    for r in chunk_results_16t:
        md_lines.append(
            f"| {r['min_len']} | {r['median_ms']:.3f} | {r['min_ms']:.3f} | {r['q1_ms']:.3f} | {r['q3_ms']:.3f} |"
        )

    md_lines.extend([
        "",
        "## 3. Rayon Chunk Size (`min_len`) Sweep at 8 Threads",
        "",
        "| `min_len` | Median (ms) | Min (ms) | Q1 (ms) | Q3 (ms) |",
        "|----------:|------------:|---------:|--------:|--------:|",
    ])
    for r in chunk_results_8t:
        md_lines.append(
            f"| {r['min_len']} | {r['median_ms']:.3f} | {r['min_ms']:.3f} | {r['q1_ms']:.3f} | {r['q3_ms']:.3f} |"
        )

    OUT_MD.write_text("\n".join(md_lines) + "\n", encoding="utf-8")
    print(f"Saved Markdown report to {OUT_MD}")


if __name__ == "__main__":
    main()
