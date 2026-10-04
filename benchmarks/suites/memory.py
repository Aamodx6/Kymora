"""Phase B3: Memory benchmark suite.

Per arch.md §11.5 (memory suite):
  - steady-state peak RSS delta (fresh subprocess per case)
  - separate "first call incl. imports" (cold path)
  - output size + overhead (delta minus output bytes)
  - Python-side allocation peak via tracemalloc where enabled

Every row uses the §11.8 BenchmarkRecord schema and is appended to
results/memory.jsonl incrementally (resume-safe via --resume).
Timeouts/errors are recorded as explicit rows (no silent skips).
"""

from __future__ import annotations

import argparse
import json
import os
import subprocess
import sys
import time
from datetime import datetime
from pathlib import Path
from typing import Any

sys.path.insert(0, str(Path(__file__).resolve().parents[2]))

from benchmarks.harness.env import save_env
from benchmarks.harness.schema import BenchmarkRecord, validate_record
from benchmarks.harness.stats import compute_stats

RESULTS_DIR = Path(__file__).resolve().parents[1] / "results"
OUT_JSONL = RESULTS_DIR / "memory.jsonl"

# (case_label, adapter, feature_set, n_series, length, min_steady_runs, tracemalloc, timeout_s)
CASES: list[tuple[str, str, str, int, int, int, bool, float]] = [
    # Tsxtract profiles — incl. the §14.3 memory-budget verification at 100k×500
    ("tsxtract_core33",   "tsxtract", "core33",   1_000, 500, 5, True, 120.0),
    ("tsxtract_core33",   "tsxtract", "core33",  10_000, 500, 5, True, 120.0),
    ("tsxtract_core33",   "tsxtract", "core33", 100_000, 500, 3, True, 300.0),
    ("tsxtract_extended", "tsxtract", "extended", 10_000, 500, 3, True, 180.0),
    ("tsxtract_extended", "tsxtract", "extended", 100_000, 500, 2, False, 300.0),
    ("tsxtract_full",     "tsxtract", "full",      1_000, 500, 3, True, 180.0),
    ("tsxtract_full",     "tsxtract", "full",     10_000, 500, 2, False, 300.0),
    # Baselines
    ("numpy_baseline",    "numpy_baseline", "default", 1_000, 500, 3, True, 120.0),
    ("numpy_baseline",    "numpy_baseline", "default", 10_000, 500, 2, False, 180.0),
    ("numpy_baseline",    "numpy_baseline", "default", 100_000, 500, 2, False, 300.0),
    # Competitors (equal-tuning families; heavy Python libs get fewer steady runs)
    ("tsfresh_efficient", "tsfresh", "efficient", 1_000, 500, 2, False, 300.0),
    ("tsfresh_efficient", "tsfresh", "efficient", 10_000, 500, 1, False, 600.0),
    ("tsfel_156",         "tsfel", "default",     1_000, 500, 2, False, 300.0),
    ("tsfel_156",         "tsfel", "default",    10_000, 500, 1, False, 600.0),
    ("catch22",           "catch22", "default",   1_000, 500, 2, False, 300.0),
    ("catch22",           "catch22", "default",  10_000, 500, 1, False, 600.0),
]


def _python_for(adapter: str) -> str:
    """Pick the isolated venv interpreter for an adapter when one exists."""
    repo_root = Path(__file__).resolve().parents[2]
    venv_name = adapter.rstrip("_")
    for c in (
        repo_root / "benchmarks" / ".venvs" / venv_name / "Scripts" / "python.exe",
        repo_root / "benchmarks" / ".venvs" / venv_name / "bin" / "python",
        repo_root / "benchmarks" / ".venvs" / adapter / "Scripts" / "python.exe",
        repo_root / "benchmarks" / ".venvs" / adapter / "bin" / "python",
    ):
        if c.exists():
            return str(c)
    return sys.executable


_WORKER = r'''
import sys, json, time, gc, os, importlib, tracemalloc
import numpy as np
import psutil

def main():
    cfg = json.loads(sys.stdin.read())
    adapter_name = cfg["adapter"]
    feature_set = cfg.get("feature_set", "default")
    n = int(cfg["n_series"]); length = int(cfg["length"])
    threads = int(cfg.get("threads", 1)); seed = int(cfg.get("seed", 42))
    min_runs = int(cfg.get("min_runs", 3))
    use_tm = bool(cfg.get("tracemalloc", False))

    for var in ("RAYON_NUM_THREADS", "OMP_NUM_THREADS", "MKL_NUM_THREADS", "OPENBLAS_NUM_THREADS"):
        os.environ[var] = str(threads)

    proc = psutil.Process()
    out = {"status": "ok"}

    try:
        # ── cold path: interpreter+numpy baseline -> adapter import ──
        rss_interp = proc.memory_info().rss
        t_imp0 = time.perf_counter()
        try:
            mod = importlib.import_module(f"benchmarks.adapters.{adapter_name}")
        except ModuleNotFoundError:
            mod = importlib.import_module(f"benchmarks.adapters.{adapter_name}_")
        adapter = mod.Adapter() if hasattr(mod, "Adapter") else mod.adapter
        import_s = time.perf_counter() - t_imp0
        rss_import = proc.memory_info().rss

        # ── data (outside measured allocation window) ──
        rng = np.random.default_rng(seed)
        data = np.ascontiguousarray(rng.standard_normal((n, length)), dtype=np.float64)
        rss_data = proc.memory_info().rss

        def peak_wset():
            try:
                return proc.memory_info().peak_wset
            except AttributeError:  # non-Windows
                return proc.memory_info().peak_rss

        if use_tm:
            tracemalloc.start()

        # ── first call (cold extraction: plans, pools, scratch) ──
        gc.disable()
        t0 = time.perf_counter()
        res = adapter.extract(data, feature_set=feature_set, threads=threads)
        first_call_s = time.perf_counter() - t0
        rss_first = proc.memory_info().rss
        peak_after_first = peak_wset()

        # ── steady state ──
        steady_times = []
        steady_max_rss = rss_first
        for _ in range(min_runs):
            t0 = time.perf_counter()
            res = adapter.extract(data, feature_set=feature_set, threads=threads)
            steady_times.append(time.perf_counter() - t0)
            steady_max_rss = max(steady_max_rss, proc.memory_info().rss)
        gc.enable()

        tm_peak_mb = 0.0
        if use_tm:
            _, tm_peak = tracemalloc.get_traced_memory()
            tracemalloc.stop()
            tm_peak_mb = tm_peak / (1024 * 1024)

        out_mb = float(res.nbytes) / 1e6 if isinstance(res, np.ndarray) and res.nbytes else 0.0
        out_shape = list(res.shape) if hasattr(res, "shape") else []

        out.update({
            "runs": steady_times,
            "import_s": import_s,
            "first_call_s": first_call_s,
            "cold_total_s": import_s + first_call_s,
            "rss_interp_mb": rss_interp / 1e6,
            "rss_import_mb": rss_import / 1e6,
            "import_delta_mb": max(0.0, rss_import - rss_interp) / 1e6,
            "rss_data_mb": rss_data / 1e6,
            "rss_after_first_mb": rss_first / 1e6,
            "steady_peak_rss_mb": steady_max_rss / 1e6,
            # steady-state delta over baseline *after data allocation*
            "steady_delta_mb": max(0.0, steady_max_rss - rss_data) / 1e6,
            "first_call_delta_mb": max(0.0, rss_first - rss_data) / 1e6,
            "peak_wset_after_first_mb": peak_after_first / 1e6,
            "output_mb": out_mb,
            "output_shape": out_shape,
            "python_peak_alloc_mb": tm_peak_mb,
            "tracemalloc": use_tm,
        })
    except Exception as e:
        out = {
            "status": "error", "runs": [],
            "error_msg": f"{type(e).__name__}: {e}",
            "exception_type": type(e).__name__,
            "exception_message": str(e),
        }
    sys.stdout.write(json.dumps(out))

if __name__ == "__main__":
    main()
'''


def run_case(case: tuple[str, str, str, int, int, int, bool, float], threads: int) -> BenchmarkRecord:
    label, adapter, feature_set, n, length, min_runs, use_tm, tmo = case
    case_id = f"mem_{label}_{n}x{length}"
    py = _python_for(adapter)
    repo_root = Path(__file__).resolve().parents[2]

    config = {
        "adapter": adapter, "feature_set": feature_set,
        "n_series": n, "length": length, "threads": threads,
        "min_runs": min_runs, "tracemalloc": use_tm, "seed": 42,
    }
    env = os.environ.copy()
    env["PYTHONPATH"] = str(repo_root) + (os.pathsep + env["PYTHONPATH"] if env.get("PYTHONPATH") else "")

    def err(status: str, msg: str, runs: list[float] | None = None) -> BenchmarkRecord:
        return BenchmarkRecord(
            suite="memory", case_id=case_id, lib=adapter, feature_set=feature_set,
            n_series=n, length=length, dtype="float64", layout="C", threads=threads,
            dist="gaussian", runs=runs or [], stats=compute_stats(runs or []),
            peak_rss_mb=0.0, status=status, guarded=True, error_msg=msg,
            env_ref="env.json",
            extra={"variant": label, "measure_tracemalloc": use_tm},
        )

    try:
        proc = subprocess.run(
            [py, "-c", _WORKER],
            input=json.dumps(config), capture_output=True, text=True,
            cwd=repo_root, env=env, timeout=tmo,
        )
    except subprocess.TimeoutExpired:
        return err("timeout", f"TimeoutExpired: case exceeded {tmo:.0f}s wall clock (recorded as explicit timeout row)")

    if proc.returncode != 0:
        return err("error", f"Subprocess failed (exit {proc.returncode}): {proc.stderr.strip()[-500:]}")
    try:
        raw = json.loads(proc.stdout)
    except Exception as e:
        return err("error", f"Malformed worker output: {e}; stdout: {proc.stdout[:300]!r}; stderr: {proc.stderr[-300:]!r}")

    if raw.get("status") != "ok":
        return err("error", raw.get("error_msg", "unknown error"))

    runs = raw.pop("runs", [])
    extra = dict(raw)
    extra["variant"] = label
    extra["measure_tracemalloc"] = use_tm

    rec = BenchmarkRecord(
        suite="memory", case_id=case_id, lib=adapter, feature_set=feature_set,
        n_series=n, length=length, dtype="float64", layout="C", threads=threads,
        dist="gaussian", runs=runs, stats=compute_stats(runs),
        peak_rss_mb=float(raw.get("steady_delta_mb", 0.0)),
        status="ok", guarded=True, error_msg=None, env_ref="env.json", extra=extra,
    )
    valid, msg = validate_record(rec.to_dict())
    if not valid:
        rec.status = "error"
        rec.error_msg = f"Schema validation failed: {msg}"
    return rec


def main() -> int:
    parser = argparse.ArgumentParser(description="B3 memory suite")
    parser.add_argument("--threads", type=int, default=16)
    parser.add_argument("--resume", action="store_true", help="skip case_ids already in the output JSONL")
    parser.add_argument("--only", type=str, default=None, help="comma-separated case label subset")
    args = parser.parse_args()

    cases = CASES
    if args.only:
        want = {s.strip() for s in args.only.split(",")}
        cases = [c for c in CASES if c[0] in want]

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

    print("=" * 100)
    print("  B3 Memory Suite (fresh subprocess per case; steady-state RSS delta + cold first call)")
    print("=" * 100, flush=True)

    total = len(cases)
    for i, case in enumerate(cases, 1):
        label, adapter, feature_set, n, length, min_runs, use_tm, tmo = case
        case_id = f"mem_{label}_{n}x{length}"
        if case_id in done_ids:
            print(f"  [{i:2d}/{total}] {case_id:<42s} skip (already recorded)", flush=True)
            continue
        print(f"  [{i:2d}/{total}] {case_id:<42s} (timeout {tmo:.0f}s)...", end=" ", flush=True)
        rec = run_case(case, args.threads)

        if rec.status == "ok":
            e = rec.extra
            print(
                f"ok  steadyΔ={e['steady_delta_mb']:>8.1f} MB  out={e['output_mb']:>7.1f} MB  "
                f"firstΔ={e['first_call_delta_mb']:>7.1f} MB  import={e['import_s']*1e3:>7.1f} ms  "
                f"first_call={e['first_call_s']*1e3:>8.1f} ms"
            )
        else:
            print(f"{rec.status:<7s} {(rec.error_msg or '')[:110]}")

        with open(OUT_JSONL, "a", encoding="utf-8") as f:
            f.write(json.dumps(rec.to_dict()) + "\n")

    print(f"\nDone. Rows in {OUT_JSONL}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
