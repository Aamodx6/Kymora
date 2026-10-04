"""Reproduce README benchmarks suite.

Runs the exact benchmark configuration reported in README.md:
- 1,000 series × 500 points
- 16 worker threads
- Competitors pinned to README configurations:
  * tsxtract: core33 (33 features)
  * catch22: default (22 features)
  * tsfel: get_features_by_domain() (156 features)
  * tsfresh: EfficientFCParameters (777 features)
- Reports best-of-N (README methodology) alongside median
- Flags any figure deviating by >20% from README and logs to LOSS_LEDGER.md
"""

from __future__ import annotations

import json
import os
import sys
import time
from datetime import datetime
from pathlib import Path
from typing import Any

REPO_ROOT = Path(__file__).resolve().parents[2]
if str(REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(REPO_ROOT))

from benchmarks.harness.env import capture_env, check_environment_warnings, measure_cpu_freq, save_env
from benchmarks.harness.runner import append_record, run_benchmark_subprocess
from benchmarks.harness.schema import BenchmarkRecord

README_TARGETS = {
    "tsxtract": {
        "adapter": "tsxtract",
        "feature_set": "core33",
        "expected_features": 33,
        "readme_ms": 1.80,
        "min_runs": 25,
        "time_budget": 2.0,
    },
    "catch22": {
        "adapter": "catch22",
        "feature_set": "default",
        "expected_features": 22,
        "readme_ms": 1045.8,
        "min_runs": 3,
        "time_budget": 4.0,
    },
    "tsfel": {
        "adapter": "tsfel",
        "feature_set": "default",
        "expected_features": 156,
        "readme_ms": 9806.6,
        "min_runs": 2,
        "time_budget": 25.0,
    },
    "tsfresh": {
        "adapter": "tsfresh",
        "feature_set": "efficient",
        "expected_features": 777,
        "readme_ms": 100500.0,
        "min_runs": 1,
        "time_budget": 120.0,
    },
}


def run_readme_reproduce(results_dir: Path | None = None, skip_slow: bool = False) -> list[BenchmarkRecord]:
    repo_root = Path(__file__).resolve().parents[2]
    if results_dir is None:
        today = datetime.now().strftime("%Y-%m-%d")
        results_dir = repo_root / "benchmarks" / "results" / f"{today}_reproduce_readme"
    results_dir.mkdir(parents=True, exist_ok=True)

    env_path = results_dir / "env.json"
    env_data = save_env(env_path)
    warnings = check_environment_warnings(env_data)
    if warnings:
        print("\n[WARN] Environment warnings:")
        for w in warnings:
            print(f"  - {w}")

    out_jsonl = results_dir / "readme_reproduce.jsonl"
    ledger_path = repo_root / "benchmarks" / "results" / "LOSS_LEDGER.md"

    freq_before = measure_cpu_freq()
    print(f"\n================================================================================")
    print(f"  Tsxtract README Reproduction Benchmark Suite (1,000 × 500, 16 Threads)")
    print(f"  CPU Frequency: {freq_before.get('current_mhz')} MHz")
    print(f"================================================================================\n")

    records: list[BenchmarkRecord] = []
    comparison_rows = []

    for key, target in README_TARGETS.items():
        if skip_slow and key in ("tsfresh", "tsfel"):
            print(f"Skipping {key} (--skip-slow flag active)")
            continue

        adapter = target["adapter"]
        feature_set = target["feature_set"]
        expected_feats = target["expected_features"]
        readme_ms = target["readme_ms"]
        min_runs = target["min_runs"]
        budget = target["time_budget"]

        print(f"--> Running {adapter} ({feature_set}, target: {expected_feats} feats, README: {readme_ms:.1f} ms)...", flush=True)

        rec = run_benchmark_subprocess(
            adapter=adapter,
            suite="reproduce_readme",
            case_id=f"readme_1k_500_{adapter}",
            feature_set=feature_set,
            n_series=1000,
            length=500,
            dtype="float64",
            dist="gaussian",
            layout="C",
            threads=16,
            guarded=True,
            min_runs=min_runs,
            time_budget=budget,
            env_ref="env.json",
        )
        append_record(rec, out_jsonl)
        records.append(rec)

        stats = rec.stats
        best_ms = (stats.get("min") or float("nan")) * 1e3
        med_ms = (stats.get("median") or float("nan")) * 1e3
        n_feats = rec.extra.get("n_features") or (rec.extra.get("output_shape", [0, 0])[1] if rec.extra.get("output_shape") else None)

        dev_pct = ((best_ms - readme_ms) / readme_ms) * 100 if best_ms == best_ms else float("nan")

        discrepancy = abs(dev_pct) > 20.0 if dev_pct == dev_pct else False

        comparison_rows.append({
            "lib": adapter,
            "feature_set": feature_set,
            "n_feats": n_feats,
            "expected_feats": expected_feats,
            "readme_ms": readme_ms,
            "best_ms": best_ms,
            "med_ms": med_ms,
            "dev_pct": dev_pct,
            "discrepancy": discrepancy,
            "status": rec.status,
            "error_msg": rec.error_msg,
        })

        status_str = f"Best: {best_ms:.2f} ms | Med: {med_ms:.2f} ms | Dev: {dev_pct:+.1f}%" if rec.status == "ok" else f"FAILED: {rec.error_msg}"
        print(f"    Result: {status_str}\n")

    freq_after = measure_cpu_freq()
    print(f"\nSuite completed. CPU Frequency after suite: {freq_after.get('current_mhz')} MHz")

    # Display comparison table
    print("\n" + "=" * 95)
    print(f"{'Library':<12} | {'Features':<10} | {'README Best':<12} | {'Meas Best':<12} | {'Meas Med':<12} | {'Deviation':<10} | {'Discrepancy'}")
    print("-" * 95)
    for row in comparison_rows:
        dev_str = f"{row['dev_pct']:+.1f}%" if row['dev_pct'] == row['dev_pct'] else "N/A"
        disc_str = "YES (>20%)" if row['discrepancy'] else "No (<=20%)"
        print(
            f"{row['lib']:<12} | {str(row['n_feats']):<10} | {row['readme_ms']:>10.2f} ms | {row['best_ms']:>10.2f} ms | {row['med_ms']:>10.2f} ms | {dev_str:>10} | {disc_str}"
        )
    print("=" * 95)

    # Check for discrepancies and update LOSS_LEDGER.md if needed
    discrepancies = [r for r in comparison_rows if r["discrepancy"]]
    if discrepancies:
        print(f"\n[!] Detected {len(discrepancies)} figures deviating from README by >20%. Updating LOSS_LEDGER.md...")
        ledger_lines = [
            "\n### README Reproduction Discrepancy Ledger Entries\n",
            f"**Audit Run Date:** {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}  \n",
            "| Item ID | Library | Target Feats | README ms | Meas Best ms | Meas Med ms | Dev % | Status |\n",
            "|---|---|---|---|---|---|---|---|\n",
        ]
        for d in discrepancies:
            item_id = f"README-DISCREPANCY-{d['lib'].upper()}"
            ledger_lines.append(
                f"| `{item_id}` | {d['lib']} | {d['n_feats']} | {d['readme_ms']:.2f} | {d['best_ms']:.2f} | {d['med_ms']:.2f} | {d['dev_pct']:+.1f}% | OPEN |\n"
            )
        ledger_lines.append("\n**Investigation Requirement:** Competitor methodology, core pinning, and multiprocessing pool overhead must be investigated before Phase B3.\n")

        with open(ledger_path, "a", encoding="utf-8") as f:
            f.writelines(ledger_lines)
        print(f"[!] Appended entries to {ledger_path}")

    return records


if __name__ == "__main__":
    skip = "--skip-slow" in sys.argv
    run_readme_reproduce(skip_slow=skip)
