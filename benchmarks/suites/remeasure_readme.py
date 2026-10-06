"""Re-measure the README dagger-marked rows (task 1.3).

Replaces the stale † rows with fresh measurements of the current build
using the F1 harness (subprocess-isolated runner):
  - Profile rows: minimal / core33 / extended / full at 1,000 x 500
  - Multi-core scaling: 1, 2, 4, 8, 16, 32 threads at 1,000 x 500
  - Memory: fresh-process peak RSS delta for kymora and tsfresh at
    identical shapes (100k x 500 for kymora; tsfresh at 1k/10k — the
    100k tsfresh cell is a multi-hour run, tracked as PENDING in CLAIMS.md)

Artifacts: benchmarks/results/<date>_remeasure/{profiles,scaling,memory}.jsonl
  + remeasure_summary.json (in-memory rollup of the three tables).
"""

from __future__ import annotations

import argparse
import json
import subprocess
import sys
from datetime import datetime
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[2]
if str(REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(REPO_ROOT))

from benchmarks.harness.env import save_env, snapshot_load  # noqa: E402
from benchmarks.harness.runner import run_benchmark_subprocess, append_record  # noqa: E402
from benchmarks.harness.stats import compute_stats  # noqa: E402

RESULTS_ROOT = REPO_ROOT / "benchmarks" / "results"

PROFILES = [("minimal", 10), ("core33", 33), ("extended", 143), ("full", 543)]
THREAD_COUNTS = [1, 2, 4, 8, 16, 32]

MEMORY_WORKER = r'''
import json, sys, os, gc
import numpy as np
import psutil

def main():
    cfg = json.loads(sys.stdin.read())
    os.environ["RAYON_NUM_THREADS"] = "16"
    lib = cfg["lib"]
    n, length = cfg["n_series"], cfg["length"]
    proc = psutil.Process()
    rss0 = proc.memory_info().rss

    rng = np.random.default_rng(42)
    X = rng.standard_normal((n, length))  # 8 bytes * n * length

    rss1 = proc.memory_info().rss
    gc.disable()
    if lib == "kymora":
        import kymora
        out = kymora.extract_features(X, profile=cfg["profile"])
        out_bytes = out.nbytes
    elif lib == "tsfresh":
        import pandas as pd
        from tsfresh import extract_features as tsf_extract
        from tsfresh.feature_extraction import EfficientFCParameters

        # fc must map to a real parameter object, never a bare string
        # (tsfresh iterates .items() on default_fc_parameters).
        fc_params = EfficientFCParameters() if cfg.get("fc") == "efficient" else None
        long_df = pd.DataFrame({"id": np.repeat(np.arange(n), length), "val": X.ravel()})
        rss_mid = proc.memory_info().rss
        df = tsf_extract(long_df, column_id="id",
                         default_fc_parameters=fc_params,
                         n_jobs=16, disable_progressbar=True)
        out = df.to_numpy(dtype=np.float64)
        out_bytes = out.nbytes
        _ = rss_mid
    else:
        raise ValueError(lib)
    rss2 = proc.memory_info().rss
    gc.enable()

    input_mb = (rss1 - rss0) / (1024 * 1024)
    peak_extra_mb = (rss2 - rss1) / (1024 * 1024)
    peak_total_mb = (rss2 - rss0) / (1024 * 1024)
    sys.stdout.write(json.dumps({
        "lib": lib, "n_series": n, "length": length,
        "profile": cfg.get("profile"), "n_features": int(out.shape[1]),
        "input_mb": input_mb,
        "extraction_peak_extra_mb": peak_extra_mb,
        "peak_total_mb": peak_total_mb,
        "output_mb_exact": out_bytes / (1024 * 1024),
    }))

if __name__ == "__main__":
    main()
'''


def _run_profile_rows(out_jsonl: Path) -> list[dict]:
    rows = []
    # Interleaved: one round per profile, repeated, so thermal state is shared
    for profile, n_feat in PROFILES:
        rec = run_benchmark_subprocess(
            adapter="kymora",
            suite="remeasure_profiles",
            case_id=f"profile_{profile}_1k_500",
            feature_set=profile,
            n_series=1000,
            length=500,
            dtype="float64",
            dist="gaussian",
            layout="C",
            threads=16,
            guarded=True,
            min_runs=50 if profile in ("minimal", "core33") else 20,
            time_budget=2.0,
            env_ref="env.json",
        )
        append_record(rec, out_jsonl)
        med = (rec.stats.get("median") or float("nan")) * 1e3
        best = (rec.stats.get("min") or float("nan")) * 1e3
        rows.append({
            "profile": profile, "n_features": n_feat,
            "median_ms": med, "best_ms": best,
            "series_per_s": 1000.0 / (med / 1e3) if med == med else float("nan"),
            "us_per_series": med,
            "us_per_series_feature": med * 1000.0 / (1000.0 * n_feat) if med == med else float("nan"),
            "status": rec.status,
        })
        print(f"  {profile}: med {med:.2f} ms  best {best:.2f} ms  ({rows[-1]['series_per_s']:,.0f} series/s)")
    return rows


def _run_thread_rows(out_jsonl: Path) -> list[dict]:
    rows = []
    base = None
    for threads in THREAD_COUNTS:
        rec = run_benchmark_subprocess(
            adapter="kymora",
            suite="remeasure_scaling",
            case_id=f"threads_{threads}_1k_500",
            feature_set="core33",
            n_series=1000,
            length=500,
            dtype="float64",
            dist="gaussian",
            layout="C",
            threads=threads,
            guarded=True,
            min_runs=50,
            time_budget=2.0,
            env_ref="env.json",
        )
        append_record(rec, out_jsonl)
        med = (rec.stats.get("median") or float("nan")) * 1e3
        if threads == 1:
            base = med
        speedup = base / med if base and med == med else float("nan")
        eff = speedup / threads if speedup == speedup else float("nan")
        rows.append({
            "threads": threads, "median_ms": med,
            "speedup": speedup, "efficiency": eff, "status": rec.status,
        })
        print(f"  {threads:>2} threads: med {med:.2f} ms  speedup {speedup:.2f}x  eta {eff * 100:.1f}%")
    return rows


def _run_memory_rows(out_jsonl: Path, skip_slow: bool) -> list[dict]:
    rows = []
    cases = [
        ("kymora", 100_000, 500, {"profile": "core33"}),
        ("kymora", 10_000, 500, {"profile": "core33"}),
        ("kymora", 10_000, 500, {"profile": "extended"}),
        ("kymora", 1_000, 500, {"profile": "full"}),
        ("tsfresh", 1_000, 500, {"fc": "efficient"}),
        ("tsfresh", 10_000, 500, {"fc": "efficient"}),
    ]
    if skip_slow:
        cases = [c for c in cases if not (c[0] == "tsfresh" and c[1] >= 10_000)]
    for lib, n, length, extra in cases:
        cfg = {"lib": lib, "n_series": n, "length": length, **extra}
        try:
            proc = subprocess.run(
                [sys.executable, "-c", MEMORY_WORKER],
                input=json.dumps(cfg), capture_output=True, text=True,
                cwd=str(REPO_ROOT), timeout=600.0,
                env={**dict(__import__("os").environ), "PYTHONPATH": str(REPO_ROOT)},
            )
            if proc.returncode != 0:
                row = {"lib": lib, "n_series": n, "length": length, "status": "error",
                       "error": proc.stderr.strip()[-400:], **extra}
            else:
                row = {**json.loads(proc.stdout), "status": "ok", **extra}
        except subprocess.TimeoutExpired:
            row = {"lib": lib, "n_series": n, "length": length, "status": "timeout", **extra}
        rows.append(row)
        if row["status"] == "ok":
            print(f"  {lib} {n}x{length}: peak +{row['peak_total_mb']:.1f} MiB total "
                  f"(input {row['input_mb']:.1f}, extraction +{row['extraction_peak_extra_mb']:.1f}, "
                  f"output {row['output_mb_exact']:.1f} MiB)")
        else:
            print(f"  {lib} {n}x{length}: {row['status']}")
        with open(out_jsonl, "a", encoding="utf-8") as f:
            f.write(json.dumps({**row, "timestamp": datetime.now().isoformat()}) + "\n")
    return rows


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--skip-slow", action="store_true", help="skip tsfresh 10k memory cell")
    args = parser.parse_args()

    out_dir = RESULTS_ROOT / f"{datetime.now().strftime('%Y-%m-%d')}_remeasure"
    out_dir.mkdir(parents=True, exist_ok=True)
    load_start = snapshot_load()

    print("== Profile rows (1,000 x 500, 16 threads) ==")
    profile_rows = _run_profile_rows(out_dir / "profiles.jsonl")
    print("\n== Thread scaling (core33, 1,000 x 500) ==")
    thread_rows = _run_thread_rows(out_dir / "scaling.jsonl")
    print("\n== Memory rows (fresh process peak RSS) ==")
    memory_rows = _run_memory_rows(out_dir / "memory.jsonl", skip_slow=args.skip_slow)

    report = {
        "generated": datetime.now().isoformat(),
        "profiles": profile_rows,
        "scaling": thread_rows,
        "memory": memory_rows,
    }
    with open(out_dir / "remeasure_summary.json", "w", encoding="utf-8") as f:
        json.dump(report, f, indent=2)
    save_env(
        out_dir / "env.json",
        extra={"load_start": load_start, "load_end": snapshot_load()},
    )
    print(f"\nArtifacts in {out_dir}")


if __name__ == "__main__":
    main()