"""Headline throughput protocol runner.

Per requirement 3:
- Verifies power scheme is High performance and AC is online via tools.check_env.
- Executes >=3 interleaved sessions x >=4 rounds (1,000 series x 500 points, 16 threads, float64).
- Computes pooled median, 95% bootstrap confidence intervals, and min/max across sessions.
- Generates benchmarks/results/HEADLINE_THROUGHPUT_REPORT.md and headline_results.json.
"""

from __future__ import annotations

import json
import sys
import time
from pathlib import Path

import numpy as np

REPO_ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(REPO_ROOT))

import kymora as km
from benchmarks.harness.env import save_env, snapshot_load
from benchmarks.harness.stats import bootstrap_ci
from tools.check_env import verify_headline_environment

RESULTS_DIR = REPO_ROOT / "benchmarks" / "results"
OUT_MD = RESULTS_DIR / "HEADLINE_THROUGHPUT_REPORT.md"
OUT_JSON = RESULTS_DIR / "headline_results.json"

N_SESSIONS = 3
ROUNDS_PER_SESSION = 4
RUNS_PER_ROUND = 30
N_SERIES = 1000
LENGTH = 500
THREADS = 16


def main():
    print("=" * 80)
    print("  Kymora Headline Throughput Protocol (HEAD)")
    print("=" * 80)

    # 1. Enforce strict environment (High Performance + AC online + HEAD version)
    ok, reasons = verify_headline_environment(strict_power=True)
    if not ok:
        print("[ERROR] Environment validation failed:")
        for r in reasons:
            print(f"  - {r}")
        sys.exit(1)

    load_start = snapshot_load()
    rng = np.random.default_rng(42)
    X = np.ascontiguousarray(rng.standard_normal((N_SERIES, LENGTH)), dtype=np.float64)

    # Warmup
    for _ in range(15):
        km.extract_features(X, profile="core33", n_jobs=THREADS)

    session_results = []
    all_runs_ms = []

    for s_idx in range(1, N_SESSIONS + 1):
        print(f"\n[Session {s_idx}/{N_SESSIONS}] Running {ROUNDS_PER_SESSION} rounds...")
        s_runs = []
        for r_idx in range(1, ROUNDS_PER_SESSION + 1):
            r_times = []
            for _ in range(RUNS_PER_ROUND):
                t0 = time.perf_counter_ns()
                km.extract_features(X, profile="core33", n_jobs=THREADS)
                r_times.append((time.perf_counter_ns() - t0) / 1e6)  # ms
            s_runs.extend(r_times)
            r_med = float(np.median(r_times))
            print(f"  Round {r_idx}: median = {r_med:.3f} ms ({N_SERIES/(r_med/1000):,.0f} series/s)")
            time.sleep(0.05)  # slight breathing room between rounds

        s_med = float(np.median(s_runs))
        session_results.append({
            "session": s_idx,
            "median_ms": s_med,
            "series_per_sec": float(N_SERIES / (s_med / 1000)),
            "min_ms": float(np.min(s_runs)),
            "max_ms": float(np.max(s_runs)),
            "n_runs": len(s_runs),
        })
        all_runs_ms.extend(s_runs)

    all_arr = np.asarray(all_runs_ms)
    pooled_median_ms = float(np.median(all_arr))
    pooled_best_ms = float(np.min(all_arr))
    pooled_series_per_sec = float(N_SERIES / (pooled_median_ms / 1000.0))
    best_series_per_sec = float(N_SERIES / (pooled_best_ms / 1000.0))

    ci_lo_ms, ci_hi_ms = bootstrap_ci(all_runs_ms, n_resamples=2000, confidence_level=0.95, statistic="median")
    ci_sps_hi = float(N_SERIES / (ci_lo_ms / 1000.0))
    ci_sps_lo = float(N_SERIES / (ci_hi_ms / 1000.0))

    session_meds_ms = [s["median_ms"] for s in session_results]
    min_session_sps = float(N_SERIES / (max(session_meds_ms) / 1000.0))
    max_session_sps = float(N_SERIES / (min(session_meds_ms) / 1000.0))

    summary = {
        "pooled_median_ms": pooled_median_ms,
        "pooled_series_per_sec": pooled_series_per_sec,
        "ci95_ms": [ci_lo_ms, ci_hi_ms],
        "ci95_series_per_sec": [ci_sps_lo, ci_sps_hi],
        "best_ms": pooled_best_ms,
        "best_series_per_sec": best_series_per_sec,
        "session_range_series_per_sec": [min_session_sps, max_session_sps],
        "total_runs": len(all_runs_ms),
        "sessions": session_results,
    }

    # Save JSON artifact
    RESULTS_DIR.mkdir(parents=True, exist_ok=True)
    with open(OUT_JSON, "w", encoding="utf-8") as f:
        json.dump(summary, f, indent=2)

    save_env(RESULTS_DIR / "env.json", extra={"load_start": load_start, "load_end": snapshot_load()})

    # Format Markdown Report
    lines = [
        "# Headline Throughput Protocol Report (HEAD)",
        "",
        "Rigorous multi-session protocol on repository HEAD under strict High Performance power scheme and AC online.",
        f"- **Protocol:** {N_SESSIONS} interleaved sessions × {ROUNDS_PER_SESSION} rounds × {RUNS_PER_ROUND} runs ({len(all_runs_ms)} total measurements).",
        f"- **Workload:** {N_SERIES:,} series × {LENGTH} steps, float64 C-contiguous gaussian, {THREADS} threads.",
        "",
        "## Summary Metrics",
        "",
        f"- **Pooled Headline Throughput:** **{pooled_series_per_sec:,.0f} series/s** (median **{pooled_median_ms:.2f} ms**)",
        f"- **95% Bootstrap Confidence Interval:** **[{ci_sps_lo:,.0f}, {ci_sps_hi:,.0f}] series/s** ([{ci_lo_ms:.2f}, {ci_hi_ms:.2f}] ms)",
        f"- **Best Single Run:** **{best_series_per_sec:,.0f} series/s** ({pooled_best_ms:.2f} ms)",
        f"- **Inter-Session Range:** **{min_session_sps:,.0f} – {max_session_sps:,.0f} series/s**",
        "",
        "## Per-Session Breakdown",
        "",
        "| Session | Runs | Median (ms) | Throughput (series/s) | Min (ms) | Max (ms) |",
        "|:---:|:---:|:---:|:---:|:---:|:---:|",
    ]
    for s in session_results:
        lines.append(
            f"| Session {s['session']} | {s['n_runs']} | {s['median_ms']:.3f} ms | "
            f"{s['series_per_sec']:,.0f} series/s | {s['min_ms']:.3f} ms | {s['max_ms']:.3f} ms |"
        )

    OUT_MD.write_text("\n".join(lines) + "\n", encoding="utf-8")
    print(f"\nReport written to {OUT_MD}")
    print(f"Artifact written to {OUT_JSON}")
    print(f"\n=> Pooled Headline: {pooled_series_per_sec:,.0f} series/s (95% CI [{ci_sps_lo:,.0f}, {ci_sps_hi:,.0f}])")


if __name__ == "__main__":
    main()
