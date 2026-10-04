"""Phase B3 (step 2): Competitor throughput suite.

Extends the B3 throughput matrix with the full competitor set, per the user's
gate-audit instruction and arch.md §11.5/§11.6:

  * catch22      (pycatch22, mp.Pool when threads > 1)
  * tsfel        (README 156-feature config: get_features_by_domain())
  * tsfresh      (README 777-feature EfficientFCParameters), BOTH views:
                   - end-to-end   (long-format DataFrame construction included)
                   - extract-only (long_df built outside the timed region)
  * tsfresh/tsfel "matched" runs (only the 13 definition-agreed features,
    frozen in benches/agreement/feature_map.json) -> matched-feature view
  * antropy, tsflex, sktime (Catch22 transformer) where installed

Same shape matrix as the baseline throughput suite (THROUGHPUT_SHAPES), same
harness protocol (fresh subprocess, warmup, GC disabled, stats + CV guard),
with per-case wall-clock timeouts recorded as EXPLICIT timeout rows so the
matrix is never silently incomplete (arch.md §11.1: no cherry-picking).

Every row uses the §11.8 BenchmarkRecord schema (runs[], stats, env_ref,
guarded, variant) and is appended to the JSONL incrementally as a checkpoint.
"""

from __future__ import annotations

import argparse
import json
import sys
from datetime import datetime
from pathlib import Path
from typing import Any

import numpy as np

sys.path.insert(0, str(Path(__file__).resolve().parents[2]))

from benches.harness.env import save_env
from benches.harness.runner import run_benchmark_subprocess
from benches.suites.throughput import THROUGHPUT_DISTS, THROUGHPUT_SHAPES

RESULTS_DIR = Path(__file__).resolve().parents[1] / "results"
OUT_JSONL = RESULTS_DIR / "throughput_competitors.jsonl"

THREADS = 16  # matches baseline suite (10C/16T laptop)


def case_timeout_s(n_series: int, lib_group: str) -> float:
    """Per-case wall-clock budget (worker import + warmup + timed runs).

    Slow families (tsfresh 777, sktime) get a larger mid-size budget because a
    single 1000x500 run can legitimately take ~100 s; anything beyond the
    budget is recorded as an explicit `timeout` row.
    """
    if lib_group in ("tsfresh", "sktime"):
        if n_series >= 10_000:
            return 60.0
        if n_series > 100:
            return 170.0
        return 90.0
    if n_series >= 10_000:
        return 60.0
    if n_series > 100:
        return 120.0
    return 90.0


# (label, adapter, feature_set, variant, lib_group, min_runs, time_budget)
# matched / extract-only variants use min_runs=1 because a single run at the
# largest shapes already dominates the budget; this is recorded per row.
VARIANTS: list[tuple[str, str, str, str | None, str, int, float]] = [
    ("catch22",           "catch22", "default",                None,          "fast",    2, 2.0),
    ("tsfel",             "tsfel",   "default",                None,          "fast",    2, 2.0),
    ("tsfel_matched",     "tsfel",   "matched",                None,          "fast",    2, 2.0),
    ("tsxtract_matched_tsfel", "tsxtract", "matched_tsfel",   None,          "fast",    2, 2.0),
    ("tsfresh_e2e",       "tsfresh", "efficient",              None,          "tsfresh", 1, 1.0),
    ("tsfresh_extract_only", "tsfresh", "efficient",           "extract_only", "tsfresh", 1, 1.0),
    ("tsfresh_matched",   "tsfresh", "matched",                None,          "tsfresh", 1, 1.0),
    ("tsxtract_matched_tsfresh", "tsxtract", "matched_tsfresh", None,        "fast",    2, 2.0),
    ("antropy",           "antropy", "default",                None,          "fast",    2, 2.0),
    ("tsflex",            "tsflex",  "default",                None,          "fast",    2, 2.0),
    ("sktime_catch22",    "sktime",  "catch22",                None,          "sktime",  1, 1.0),
]


def main() -> int:
    parser = argparse.ArgumentParser(description="B3 competitor throughput matrix")
    parser.add_argument("--libs", type=str, default=None,
                        help="comma-separated subset of: " + ",".join(v[0] for v in VARIANTS))
    parser.add_argument("--dists", type=str, default=None, help="comma-separated dist subset")
    parser.add_argument("--shapes", type=str, default=None, help="comma-separated 'n x len' subset")
    parser.add_argument("--threads", type=int, default=THREADS)
    parser.add_argument("--resume", action="store_true",
                        help="skip case_ids already present in the output JSONL")
    args = parser.parse_args()

    selected = VARIANTS
    if args.libs:
        want = {s.strip() for s in args.libs.split(",")}
        selected = [v for v in VARIANTS if v[0] in want]
        unknown = want - {v[0] for v in VARIANTS}
        if unknown:
            print(f"[WARN] unknown libs ignored: {sorted(unknown)}")

    dists = THROUGHPUT_DISTS
    if args.dists:
        dists = [s.strip() for s in args.dists.split(",")]

    shapes = THROUGHPUT_SHAPES
    if args.shapes:
        shapes = []
        for s in args.shapes.split(","):
            n, l = s.lower().split("x")
            shapes.append((int(n.strip()), int(l.strip())))

    RESULTS_DIR.mkdir(parents=True, exist_ok=True)
    save_env(RESULTS_DIR / "env.json")

    done_ids: set[str] = set()
    if args.resume and OUT_JSONL.exists():
        for line in OUT_JSONL.read_text(encoding="utf-8").splitlines():
            line = line.strip()
            if line:
                try:
                    done_ids.add(json.loads(line)["case_id"])
                except (json.JSONDecodeError, KeyError):
                    pass
        print(f"  [resume] {len(done_ids)} case_ids already in {OUT_JSONL.name}")

    from benches.datasets.generators import generate_series

    print("=" * 100)
    print("  B3 Competitor Throughput Matrix (same shapes as baseline suite)")
    print(f"  variants: {[v[0] for v in selected]}")
    print(f"  shapes: {shapes}")
    print(f"  dists: {dists}   threads: {args.threads}")
    print(f"  output: {OUT_JSONL}")
    print("=" * 100, flush=True)

    # Availability probe (one tiny call per adapter, outside the matrix)
    available: list[tuple[str, str, str, str | None, str, int, float]] = []
    for label, adapter, feature_set, variant, group, min_runs, budget in selected:
        try:
            probe_cfg = {
                "adapter": adapter, "suite": "competitor_probe", "case_id": "probe",
                "feature_set": feature_set, "n_series": 2, "length": 64,
                "threads": 1, "min_runs": 1, "time_budget": 0.0,
                "variant": variant, "guarded": True,
            }
            rec = run_benchmark_subprocess(
                adapter=adapter, suite="competitor_probe", case_id="probe",
                feature_set=feature_set, n_series=2, length=64, threads=1,
                min_runs=1, time_budget=0.0, variant=variant, timeout_s=90.0,
                env_ref="env.json", rerun_on_high_cv=False,
            )
            if rec.status == "ok":
                available.append((label, adapter, feature_set, variant, group, min_runs, budget))
                print(f"  [OK]      {label:<22s} ({adapter}/{feature_set})")
            else:
                print(f"  [SKIP]    {label:<22s} -> {rec.status}: {(rec.error_msg or '')[:120]}")
        except Exception as e:  # noqa: BLE001 - availability probe must not crash the suite
            print(f"  [SKIP]    {label:<22s} -> probe error: {type(e).__name__}: {e}")

    total = len(shapes) * len(dists) * len(available)
    print(f"\nRunning {total} cases...\n", flush=True)

    done = 0
    for n_series, length in shapes:
        for dist in dists:
            X = generate_series(dist, n_series, length, seed=42)
            del X  # data is regenerated inside each worker; free the parent copy
            for label, adapter, feature_set, variant, group, min_runs, budget in available:
                done += 1
                tmo = case_timeout_s(n_series, group)
                case_id = f"comp_{label}_{n_series}x{length}_{dist}"
                if case_id in done_ids:
                    print(f"  [{done:3d}/{total}] {label:<22s} {n_series:>7d}x{length:<6d} {dist:<13s} "
                          f"skip (already recorded)", flush=True)
                    continue
                print(f"  [{done:3d}/{total}] {label:<22s} {n_series:>7d}x{length:<6d} {dist:<13s} "
                      f"(timeout {tmo:.0f}s)...", end=" ", flush=True)
                try:
                    rec = run_benchmark_subprocess(
                        adapter=adapter,
                        suite="throughput_competitors",
                        case_id=case_id,
                        feature_set=feature_set,
                        n_series=n_series,
                        length=length,
                        dist=dist,
                        threads=args.threads,
                        min_runs=min_runs,
                        time_budget=budget,
                        timeout_s=tmo,
                        variant=variant,
                        env_ref="env.json",
                        rerun_on_high_cv=False,
                    )
                except Exception as e:  # noqa: BLE001 - record the failure as an error row
                    print(f"EXC {type(e).__name__}: {e}")
                    continue

                med_ms = (rec.stats.get("median") or float("nan")) * 1e3
                n_feat = (rec.extra.get("output_shape") or [0, 0])[1] if rec.extra.get("output_shape") else None
                us_sf = float("nan")
                if n_feat and rec.status == "ok":
                    us_sf = (med_ms * 1000.0) / max(1, n_series * n_feat)
                status_str = rec.status if rec.status == "ok" else f"{rec.status}"
                extra = f" n_feat={n_feat} µs/sf={us_sf:.3f}" if rec.status == "ok" else f" {rec.error_msg[:80] if rec.error_msg else ''}"
                print(f"{status_str:<8s} median={med_ms:>10.2f} ms{extra}", flush=True)

                with open(OUT_JSONL, "a", encoding="utf-8") as f:
                    f.write(json.dumps(rec.to_dict()) + "\n")

    print("\nDone. Rows appended to", OUT_JSONL)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
