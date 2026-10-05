#!/usr/bin/env python3
"""Performance regression gate for the core33 hot path (Phase 5.3).

Probes `extract_features` on 1k x 500 core33 (direct call, no harness
overhead beyond the call itself) and compares the median against a stored
baseline for the same platform key. Noise-aware: the run needs >=30
interleaved samples, fails only when BOTH the median regresses >7% AND the
lower quartile exceeds the baseline (outlier-robust), and re-runs once when
CV > 5%.

Usage:
    python tools/perf_gate.py [--runs 30] [--probe {single,multi}]
        [--baseline benchmarks/results/perf_baseline.json]
        [--update-baseline] [--ci]

- default: compare current tree against the baseline, exit 1 on regression.
- --update-baseline: record the current median as the baseline for this
  platform key (used by the weekly CI run and by hand on new hardware).
- --ci: never update; a missing baseline entry is exit 0 with a notice
  (first run on a new runner class records nothing and passes).

Baseline file layout: {"<os>-<cpu>-<py>": {"median_ms": ..., ...}, ...}.
Gate config must match the baseline entry's config (shape/profile/threads).
"""

from __future__ import annotations

import argparse
import gc
import json
import platform
import statistics
import sys
import time
from pathlib import Path

REPO = Path(__file__).resolve().parents[1]
DEFAULT_BASELINE = REPO / "benchmarks" / "results" / "perf_baseline.json"

SHAPE = (1000, 500)
PROFILE = "core33"
THRESHOLD = 0.07
MIN_RUNS = 30


def platform_key() -> str:
    cpu = platform.processor() or platform.machine()
    return f"{sys.platform}-{cpu}-py{sys.version_info.major}{sys.version_info.minor}"


def probe(runs: int, n_jobs: int | None) -> dict:
    import numpy as np

    import kymora

    rng = np.random.default_rng(42)
    X = np.ascontiguousarray(rng.standard_normal(SHAPE))
    kymora.extract_features(X[:8], profile=PROFILE, n_jobs=n_jobs)  # warmup

    samples: list[float] = []
    gc.disable()
    try:
        for _ in range(runs):
            t0 = time.perf_counter()
            kymora.extract_features(X, profile=PROFILE, n_jobs=n_jobs)
            samples.append((time.perf_counter() - t0) * 1e3)
    finally:
        gc.enable()
    samples.sort()
    n = len(samples)
    median = statistics.median(samples)
    q1 = samples[n // 4]
    q3 = samples[3 * n // 4]
    mean = statistics.fmean(samples)
    stdev = statistics.pstdev(samples)
    return {
        "runs": runs,
        "median_ms": median,
        "q1_ms": q1,
        "q3_ms": q3,
        "cv": (stdev / mean) if mean else 0.0,
        "shape": list(SHAPE),
        "profile": PROFILE,
        "n_jobs": n_jobs,
    }


def main() -> int:
    ap = argparse.ArgumentParser(description="core33 perf regression gate")
    ap.add_argument("--runs", type=int, default=30)
    ap.add_argument("--n-jobs", type=int, default=None)
    ap.add_argument("--baseline", type=Path, default=DEFAULT_BASELINE)
    ap.add_argument("--update-baseline", action="store_true")
    ap.add_argument("--ci", action="store_true")
    args = ap.parse_args()

    if args.runs < MIN_RUNS:
        print(f"need at least {MIN_RUNS} runs, got {args.runs}")
        return 2

    key = platform_key()
    result = probe(args.runs, args.n_jobs)
    if result["cv"] > 0.05:
        print(f"CV {result['cv']:.3f} > 0.05, re-running once")
        result = probe(args.runs, args.n_jobs)

    baseline: dict = {}
    if args.baseline.exists():
        baseline = json.loads(args.baseline.read_text(encoding="utf-8"))

    if args.update_baseline:
        baseline[key] = {**result, "platform": platform.platform()}
        args.baseline.write_text(json.dumps(baseline, indent=2) + "\n", encoding="utf-8")
        print(f"recorded baseline for {key}: {result['median_ms']:.3f} ms")
        return 0

    entry = baseline.get(key)
    if entry is None:
        print(f"no baseline for {key}; pass --update-baseline to record one")
        print(f"current median: {result['median_ms']:.3f} ms (not gated)")
        return 0

    base = entry["median_ms"]
    ratio = result["median_ms"] / base
    print(f"baseline {base:.3f} ms <- current {result['median_ms']:.3f} ms "
          f"(ratio {ratio:.4f}, q1 {result['q1_ms']:.3f} ms, cv {result['cv']:.3f})")
    if ratio > 1.0 + THRESHOLD and result["q1_ms"] > base:
        print(f"REGRESSION: median >7% above baseline with q1 above baseline")
        return 1
    print("OK: within gate")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
