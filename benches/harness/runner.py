"""Subprocess-isolated, pyperf-style benchmark runner.

Ensures:
- Measurement in a fresh subprocess
- Warmup runs
- GC disabled during timed section
- Minimum runs (N>=15) or time budget (>=2.0s)
- Automatic peak RSS tracking
- Automatic rerun on CV > 5%
- Validated JSONL schema output
"""

from __future__ import annotations

import argparse
import gc
import json
import os
import subprocess
import sys
import time
from pathlib import Path
from typing import Any

import numpy as np

from benches.harness.schema import BenchmarkRecord, validate_record
from benches.harness.stats import compute_stats


def _worker_script() -> str:
    """Return inline python code executed by the isolated worker subprocess."""
    return """
import sys
import gc
import json
import time
import os
import psutil
import numpy as np
import importlib

def main():
    config = json.loads(sys.stdin.read())
    adapter_name = config["adapter"]
    feature_set = config.get("feature_set", "default")
    threads = int(config.get("threads", 1))
    n_series = int(config["n_series"])
    length = int(config["length"])
    dtype = config.get("dtype", "float64")
    dist = config.get("dist", "gaussian")
    seed = int(config.get("seed", 42))
    layout = config.get("layout", "C")
    min_runs = int(config.get("min_runs", 15))
    time_budget = float(config.get("time_budget", 2.0))

    # Set threading env variables inside process
    os.environ["RAYON_NUM_THREADS"] = str(threads)
    os.environ["OMP_NUM_THREADS"] = str(threads)
    os.environ["MKL_NUM_THREADS"] = str(threads)
    os.environ["OPENBLAS_NUM_THREADS"] = str(threads)

    # Generate synthetic input in worker
    rng = np.random.default_rng(seed)
    if dist == "gaussian":
        data = rng.standard_normal((n_series, length))
    elif dist == "constant":
        data = np.ones((n_series, length))
    elif dist == "all_zero":
        data = np.zeros((n_series, length))
    elif dist == "sinusoid":
        t = np.linspace(0, 10 * np.pi, length)
        data = np.sin(t) + 0.1 * rng.standard_normal((n_series, length))
    elif dist == "random_walk":
        data = np.cumsum(rng.standard_normal((n_series, length)), axis=1)
    elif dist == "ar1":
        phi = 0.7
        data = np.zeros((n_series, length), dtype=np.float64)
        noise = rng.standard_normal((n_series, length))
        for j in range(1, length):
            data[:, j] = phi * data[:, j-1] + noise[:, j]
    elif dist == "heavy_tail":
        data = rng.standard_t(df=3, size=(n_series, length))
    elif dist == "cancellation":
        data = 1e9 + rng.standard_normal((n_series, length))
    elif dist == "huge_scale":
        data = 1e150 * rng.standard_normal((n_series, length))
    elif dist == "tiny_scale":
        data = 1e-150 * rng.standard_normal((n_series, length))
    else:
        data = rng.standard_normal((n_series, length))

    if dtype == "float32":
        data = data.astype(np.float32)
    elif dtype == "int32":
        data = (data * 100).astype(np.int32)
    elif dtype == "int16":
        data = np.clip(data * 100, -32000, 32000).astype(np.int16)
    else:
        data = data.astype(np.float64)

    if layout == "F":
        data = np.asfortranarray(data)
    elif layout == "strided":
        # Step stride 2
        wide = np.repeat(data, 2, axis=1)
        data = wide[:, ::2]

    guarded = bool(config.get("guarded", True))
    fastmath = config.get("fastmath", None)
    extra_kwargs = {"guarded": guarded}
    if fastmath is not None:
        extra_kwargs["fastmath"] = fastmath

    # Import adapter
    try:
        mod = importlib.import_module(f"benches.adapters.{adapter_name}")
    except ModuleNotFoundError:
        mod = importlib.import_module(f"benches.adapters.{adapter_name}_")
    adapter_cls = getattr(mod, "Adapter", None)
    if adapter_cls is None:
        # Check for function
        adapter = getattr(mod, "adapter", None)
    else:
        adapter = adapter_cls()

    process = psutil.Process()
    rss_before = process.memory_info().rss

    # Warmup
    try:
        w_res = adapter.extract(data[:min(n_series, 4)], feature_set=feature_set, threads=threads, **extra_kwargs)
    except Exception as e:
        exc_type = type(e).__name__
        exc_msg = str(e)
        sys.stdout.write(json.dumps({
            "status": "error",
            "runs": [],
            "peak_rss_mb": 0.0,
            "error_msg": f"{exc_type}: {exc_msg}",
            "exception_type": exc_type,
            "exception_message": exc_msg,
        }))
        return

    # Timed runs
    runs = []
    total_time = 0.0
    res = None

    gc.disable()
    try:
        while len(runs) < min_runs or total_time < time_budget:
            t0 = time.perf_counter()
            res = adapter.extract(data, feature_set=feature_set, threads=threads, **extra_kwargs)
            t1 = time.perf_counter()
            elapsed = t1 - t0
            runs.append(elapsed)
            total_time += elapsed
            if len(runs) >= min_runs and total_time >= time_budget:
                break
            if len(runs) >= 100:  # safety cap
                break
    except Exception as e:
        exc_type = type(e).__name__
        exc_msg = str(e)
        sys.stdout.write(json.dumps({
            "status": "error",
            "runs": runs,
            "peak_rss_mb": 0.0,
            "error_msg": f"{exc_type}: {exc_msg}",
            "exception_type": exc_type,
            "exception_message": exc_msg,
        }))
        return
    finally:
        gc.enable()

    rss_after = process.memory_info().rss
    peak_rss_mb = max(0.0, (rss_after - rss_before) / (1024 * 1024))

    # Check for NaN / output validity
    status = "ok"
    error_msg = None
    if res is None:
        status = "error"
        error_msg = "Adapter returned None"
    elif isinstance(res, np.ndarray) and np.isnan(res).all():
        status = "nan"

    output_shape = list(res.shape) if hasattr(res, "shape") else []
    sample_val = float(res[0, 0]) if isinstance(res, np.ndarray) and res.size > 0 else None

    sys.stdout.write(json.dumps({
        "status": status,
        "runs": runs,
        "peak_rss_mb": peak_rss_mb,
        "output_shape": output_shape,
        "sample_val": sample_val,
        "error_msg": error_msg,
    }))

if __name__ == "__main__":
    main()
"""


def run_benchmark_subprocess(
    adapter: str,
    suite: str,
    case_id: str,
    feature_set: str = "default",
    n_series: int = 100,
    length: int = 500,
    dtype: str = "float64",
    dist: str = "gaussian",
    layout: str = "C",
    threads: int = 1,
    guarded: bool = True,
    fastmath: bool | None = None,
    min_runs: int = 15,
    time_budget: float = 2.0,
    python_bin: str | Path | None = None,
    env_ref: str = "env.json",
    seed: int = 42,
    rerun_on_high_cv: bool = True,
) -> BenchmarkRecord:
    """Run an isolated measurement in a fresh subprocess with stats and CV guard."""
    repo_root = Path(__file__).resolve().parents[2]
    if python_bin is None:
        # Check if an isolated venv exists for this adapter
        venv_name = adapter.rstrip("_")
        candidates = [
            repo_root / "benches" / ".venvs" / venv_name / "Scripts" / "python.exe",
            repo_root / "benches" / ".venvs" / venv_name / "bin" / "python",
            repo_root / "benches" / ".venvs" / adapter / "Scripts" / "python.exe",
            repo_root / "benches" / ".venvs" / adapter / "bin" / "python",
        ]
        for c in candidates:
            if c.exists():
                python_bin = c
                break

    py_exec = str(python_bin) if python_bin else sys.executable
    config = {
        "adapter": adapter,
        "suite": suite,
        "case_id": case_id,
        "feature_set": feature_set,
        "n_series": n_series,
        "length": length,
        "dtype": dtype,
        "dist": dist,
        "layout": layout,
        "threads": threads,
        "guarded": guarded,
        "fastmath": fastmath,
        "min_runs": min_runs,
        "time_budget": time_budget,
        "seed": seed,
    }
    worker_code = _worker_script()

    def _exec() -> dict[str, Any]:
        env = os.environ.copy()
        env["PYTHONPATH"] = str(repo_root) + (os.pathsep + env["PYTHONPATH"] if "PYTHONPATH" in env else "")
        proc = subprocess.run(
            [py_exec, "-c", worker_code],
            input=json.dumps(config),
            capture_output=True,
            text=True,
            cwd=repo_root,
            env=env,
            timeout=180,
        )
        if proc.returncode != 0:
            return {
                "status": "error",
                "runs": [],
                "peak_rss_mb": 0.0,
                "error_msg": f"Subprocess failed (exit {proc.returncode}): {proc.stderr.strip()}",
            }
        try:
            return json.loads(proc.stdout)
        except Exception as e:
            return {
                "status": "error",
                "runs": [],
                "peak_rss_mb": 0.0,
                "error_msg": f"Malformed worker output: {e}\nRaw stdout: {proc.stdout}\nStderr: {proc.stderr}",
            }

    raw = _exec()
    runs = raw.get("runs", [])
    stats = compute_stats(runs)

    # Rerun once if CV > 5%
    if rerun_on_high_cv and stats.get("high_cv", False) and raw.get("status") == "ok":
        raw_rerun = _exec()
        runs_rerun = raw_rerun.get("runs", [])
        if runs_rerun:
            stats_rerun = compute_stats(runs_rerun)
            # Pick the rerun if lower CV or valid
            if stats_rerun["cv"] < stats["cv"]:
                raw = raw_rerun
                runs = runs_rerun
                stats = stats_rerun

    extra: dict[str, Any] = {
        "output_shape": raw.get("output_shape"),
        "sample_val": raw.get("sample_val"),
    }
    if raw.get("exception_type"):
        extra["exception_type"] = raw.get("exception_type")
        extra["exception_message"] = raw.get("exception_message")
    if adapter == "numba_baseline":
        fm_val = fastmath if fastmath is not None else (feature_set not in ("strict", "no_fastmath", "agreement", "robustness"))
        extra["fastmath_variant"] = f"fastmath={fm_val}"

    record = BenchmarkRecord(
        suite=suite,
        case_id=case_id,
        lib=adapter,
        feature_set=feature_set,
        n_series=n_series,
        length=length,
        dtype=dtype,
        layout=layout,
        threads=threads,
        dist=dist,
        runs=runs,
        stats=stats,
        peak_rss_mb=float(raw.get("peak_rss_mb", 0.0)),
        status=raw.get("status", "error"),
        guarded=guarded,
        error_msg=raw.get("error_msg"),
        env_ref=env_ref,
        extra=extra,
    )

    valid, msg = validate_record(record.to_dict())
    if not valid:
        record.status = "error"
        record.error_msg = f"Schema validation failed: {msg}"

    return record


def append_record(record: BenchmarkRecord, jsonl_path: Path | str) -> None:
    """Append a record to a JSONL results file."""
    path = Path(jsonl_path)
    path.parent.mkdir(parents=True, exist_ok=True)
    with open(path, "a", encoding="utf-8") as f:
        f.write(json.dumps(record.to_dict()) + "\n")
