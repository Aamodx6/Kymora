"""Phase B0 Smoke Test: Runs every adapter on one tiny case end-to-end and writes valid JSONL."""

from __future__ import annotations

import datetime
import json
import platform
import sys
from pathlib import Path

# Ensure repo root is on sys.path
_repo_root = Path(__file__).resolve().parents[1]
if str(_repo_root) not in sys.path:
    sys.path.insert(0, str(_repo_root))

from benchmarks.harness.env import capture_env, save_env
from benchmarks.harness.runner import append_record, run_benchmark_subprocess
from benchmarks.harness.schema import validate_record

ADAPTERS = [
    ("kymora", "core33"),
    ("numpy_baseline", "default"),
    ("numba_baseline", "default"),
    ("catch22_", "default"),
    ("tsfresh_", "minimal"),
    ("tsfel_", "default"),
    ("antropy_", "default"),
    ("tsflex_", "default"),
    ("sktime_", "default"),
    ("tsxtract_jax", "default"),
]


def run_smoke(results_dir: Path | None = None) -> Path:
    date_str = datetime.date.today().strftime("%Y-%m-%d")
    machine_name = platform.node() or "machine"
    out_dir = results_dir or (Path(__file__).resolve().parent / "results" / f"{date_str}_{machine_name}")
    out_dir.mkdir(parents=True, exist_ok=True)

    # 1. Capture environment
    env_path = out_dir / "env.json"
    save_env(env_path)
    print(f"[Smoke] Saved environment to {env_path}")

    # 2. Results file
    jsonl_path = out_dir / "smoke.jsonl"
    if jsonl_path.exists():
        jsonl_path.unlink()

    print(f"[Smoke] Running all {len(ADAPTERS)} adapters on tiny test case (n_series=2, length=32)...")
    success_count = 0

    for adapter_name, feature_set in ADAPTERS:
        print(f"  -> Testing adapter '{adapter_name}' ({feature_set})...", end=" ", flush=True)
        try:
            record = run_benchmark_subprocess(
                adapter=adapter_name,
                suite="smoke",
                case_id=f"smoke_{adapter_name}",
                feature_set=feature_set,
                n_series=2,
                length=32,
                dtype="float64",
                dist="gaussian",
                layout="C",
                threads=1,
                min_runs=1,
                time_budget=0.05,
                env_ref="env.json",
                rerun_on_high_cv=False,
            )
            append_record(record, jsonl_path)
            valid, msg = validate_record(record.to_dict())
            if not valid:
                print(f"FAILED (Schema invalid: {msg})")
            elif record.status == "ok":
                print(f"OK (runs={len(record.runs)}, median={record.stats['median']*1e3:.2f}ms)")
                success_count += 1
            else:
                # E.g. expected placeholder error for tsxtract_jax
                print(f"{record.status.upper()} ({record.error_msg or 'No error message'})")
                success_count += 1
        except Exception as e:
            print(f"EXCEPTION ({e})")

    print(f"\n[Smoke] Complete. {success_count}/{len(ADAPTERS)} adapters processed and logged to {jsonl_path}")
    return jsonl_path


if __name__ == "__main__":
    run_smoke()
