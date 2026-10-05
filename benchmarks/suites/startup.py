"""Phase B3: Startup benchmark suite.

Per arch.md §11.5 (startup suite):
  - import wall time (fresh subprocess, repeated for stability)
  - `-X importtime` top cumulative modules (recorded per lib)
  - first-call time (cold extraction after fresh import)
  - installed size of the package (site-packages footprint)
  - numba JIT compile time reported separately (numba_baseline adapter)

Cold-cache install time is NOT measured here: it requires network access and
would be non-reproducible; it is recorded as an explicit "not measured" note
in the report (no silent gaps, arch.md §11.1).

Every row uses the §11.8 BenchmarkRecord schema and is appended to
results/startup.jsonl incrementally (resume-safe via --resume).
"""

from __future__ import annotations

import argparse
import json
import os
import subprocess
import sys
from pathlib import Path
from typing import Any

sys.path.insert(0, str(Path(__file__).resolve().parents[2]))

from benchmarks.harness.env import save_env
from benchmarks.harness.schema import BenchmarkRecord, validate_record
from benchmarks.harness.stats import compute_stats

RESULTS_DIR = Path(__file__).resolve().parents[1] / "results"
OUT_JSONL = RESULTS_DIR / "startup.jsonl"

# (label, adapter, import_module, timeout_s, size_targets...)
# first-call is measured via the adapter on a tiny input (1x64).
# size_targets default to import_module; kymora is the real package (with the
# native `_core` extension) and ships no shims.
CASES: list[tuple] = [
    ("kymora",       "kymora",       "kymora", 60.0,  ("kymora",)),
    ("numpy_baseline", "numpy_baseline", "numpy",    60.0,  ("numpy",)),
    ("numba_baseline", "numba_baseline", "numba",    180.0, ("numba",)),
    ("tsfresh",        "tsfresh_",       "tsfresh",  180.0, ("tsfresh",)),
    ("tsfel",          "tsfel_",         "tsfel",    180.0, ("tsfel",)),
    ("catch22",        "catch22_",       "pycatch22", 120.0, ("pycatch22",)),
]

IMPORT_REPEATS = 5
INSTALLED_SIZE_TOP = 15  # top-N modules reported


def _python_for(adapter: str) -> str:
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


# ── Worker 1: import wall time + first call ──────────────────────────────
_IMPORT_WORKER = r'''
import sys, json, time, os
cfg = json.loads(sys.stdin.read())
module = cfg["module"]
adapter_name = cfg["adapter"]
n_repeat = int(cfg.get("n_repeat", 5))
threads = int(cfg.get("threads", 16))

for var in ("RAYON_NUM_THREADS", "OMP_NUM_THREADS", "MKL_NUM_THREADS", "OPENBLAS_NUM_THREADS"):
    os.environ[var] = str(threads)

times = []
first_call_s = None
try:
    for i in range(n_repeat):
        # fresh interpreter per repeat is handled by the parent; here we time
        # the single import of this (already fresh) process.
        t0 = time.perf_counter()
        __import__(module)
        times.append(time.perf_counter() - t0)
        break  # one import per process; repeats are spawned by the parent

    # first call: cold extraction through the adapter on a tiny input
    import numpy as np
    try:
        import importlib
        try:
            mod = importlib.import_module(f"benchmarks.adapters.{adapter_name}")
        except ModuleNotFoundError:
            mod = importlib.import_module(f"benchmarks.adapters.{adapter_name}_")
        adapter = mod.Adapter() if hasattr(mod, "Adapter") else mod.adapter
        X = np.ascontiguousarray(np.random.default_rng(42).standard_normal((1, 64)))
        fs = cfg.get("feature_set", "default")
        t0 = time.perf_counter()
        adapter.extract(X, feature_set=fs, threads=threads)
        first_call_s = time.perf_counter() - t0
        # second call (warm) for comparison
        t0 = time.perf_counter()
        adapter.extract(X, feature_set=fs, threads=threads)
        warm_call_s = time.perf_counter() - t0
    except Exception as e:
        warm_call_s = None
        first_call_err = f"{type(e).__name__}: {e}"
    else:
        first_call_err = None

    sys.stdout.write(json.dumps({
        "status": "ok", "import_s": times[0],
        "first_call_s": first_call_s, "warm_call_s": warm_call_s,
        "first_call_err": first_call_err,
    }))
except Exception as e:
    sys.stdout.write(json.dumps({
        "status": "error",
        "error_msg": f"{type(e).__name__}: {e}",
    }))
'''


# ── Worker 2: -X importtime top modules (single process, stderr parse) ───
def run_importtime(py: str, module: str, repo_root: Path) -> list[dict[str, Any]]:
    env = os.environ.copy()
    env["PYTHONPATH"] = str(repo_root) + (os.pathsep + env["PYTHONPATH"] if env.get("PYTHONPATH") else "")
    try:
        proc = subprocess.run(
            [py, "-X", "importtime", "-c", f"import {module}"],
            capture_output=True, text=True, cwd=repo_root, env=env, timeout=300,
        )
    except subprocess.TimeoutExpired:
        return []
    rows: list[dict[str, Any]] = []
    for line in proc.stderr.splitlines():
        # format: import time: self [us] | cumulative | imported package
        if not line.startswith("import time:"):
            continue
        try:
            parts = line.split("|")
            self_us = float(parts[0].split("[us]")[0].replace("import time:", "").strip())
            cum_us = float(parts[1].replace("cumulative", "").strip())
            name = parts[2].strip() if len(parts) > 2 else ""
            rows.append({"module": name, "self_us": self_us, "cumulative_us": cum_us})
        except (ValueError, IndexError):
            continue
    return rows


# ── Worker 3: installed size ─────────────────────────────────────────────
_SIZE_WORKER = r'''
import sys, json, os
target = sys.argv[1]
try:
    # 1. distribution-based size (whole installed distribution; catches native
    #    .pyd/.so files that live OUTSIDE the package dir, e.g. pycatch22)
    try:
        from importlib.metadata import distribution
        dist = distribution(target)
        total = 0
        top = {}
        for f in dist.files or []:
            try:
                sz = f.size if f.size is not None else f.locate().stat().st_size
            except (OSError, AttributeError):
                continue
            total += sz
            top0 = str(f).replace(chr(92), "/").split("/")[0]
            top[top0] = top.get(top0, 0) + sz
        sys.stdout.write(json.dumps({
            "status": "ok", "method": "distribution",
            "root": dist.metadata.get("Name", target),
            "total_bytes": total,
            "top_subdirs": sorted(top.items(), key=lambda kv: -kv[1])[:15],
        }))
        raise SystemExit(0)
    except SystemExit:
        raise
    except Exception:
        pass

    # 2. fallback: walk the import package dir
    import importlib.util
    spec = importlib.util.find_spec(target)
    if spec is None or not spec.origin:
        sys.stdout.write(json.dumps({"status": "error", "error_msg": f"cannot locate {target}"}))
        raise SystemExit(0)
    root = os.path.dirname(spec.origin)
    total = 0
    per_sub = {}
    for dirpath, dirnames, filenames in os.walk(root):
        for fn in filenames:
            fp = os.path.join(dirpath, fn)
            try:
                sz = os.path.getsize(fp)
            except OSError:
                continue
            total += sz
            sub = os.path.relpath(dirpath, root).split(os.sep)[0]
            per_sub[sub] = per_sub.get(sub, 0) + sz
    sys.stdout.write(json.dumps({
        "status": "ok", "method": "walk", "root": root,
        "total_bytes": total,
        "top_subdirs": sorted(per_sub.items(), key=lambda kv: -kv[1])[:15],
    }))
except Exception as e:
    sys.stdout.write(json.dumps({"status": "error", "error_msg": f"{type(e).__name__}: {e}"}))
'''


def make_record(
    label: str, adapter: str, status: str, runs: list[float],
    error_msg: str | None, extra: dict[str, Any],
) -> BenchmarkRecord:
    rec = BenchmarkRecord(
        suite="startup", case_id=f"startup_{label}", lib=adapter, feature_set="default",
        n_series=1, length=64, dtype="float64", layout="C", threads=16, dist="gaussian",
        runs=runs, stats=compute_stats(runs), peak_rss_mb=0.0,
        status=status, guarded=True, error_msg=error_msg, env_ref="env.json", extra=extra,
    )
    valid, msg = validate_record(rec.to_dict())
    if not valid:
        rec.status = "error"
        rec.error_msg = f"Schema validation failed: {msg}"
    return rec


def run_case(label: str, adapter: str, module: str, tmo: float, threads: int,
              size_targets: tuple[str, ...] = ()) -> BenchmarkRecord:
    py = _python_for(adapter)
    repo_root = Path(__file__).resolve().parents[2]
    env = os.environ.copy()
    env["PYTHONPATH"] = str(repo_root) + (os.pathsep + env["PYTHONPATH"] if env.get("PYTHONPATH") else "")
    extra: dict[str, Any] = {"variant": label, "interpreter": py}

    # 1. import wall time — one fresh interpreter per repeat
    import_times: list[float] = []
    first_call_s: float | None = None
    warm_call_s: float | None = None
    first_call_err: str | None = None
    for _ in range(IMPORT_REPEATS):
        try:
            proc = subprocess.run(
                [py, "-c", _IMPORT_WORKER],
                input=json.dumps({"module": module, "adapter": adapter, "threads": threads}),
                capture_output=True, text=True, cwd=repo_root, env=env, timeout=tmo,
            )
        except subprocess.TimeoutExpired:
            return make_record(label, adapter, "timeout", [], f"TimeoutExpired: import/first-call exceeded {tmo:.0f}s", extra)
        if proc.returncode != 0:
            return make_record(label, adapter, "error", [], f"Subprocess failed (exit {proc.returncode}): {proc.stderr.strip()[-400:]}", extra)
        try:
            raw = json.loads(proc.stdout)
        except Exception as e:
            return make_record(label, adapter, "error", [], f"Malformed worker output: {e}; stderr: {proc.stderr[-300:]!r}", extra)
        if raw.get("status") != "ok":
            return make_record(label, adapter, "error", [], raw.get("error_msg", "unknown error"), extra)
        import_times.append(float(raw["import_s"]))
        if first_call_s is None:  # keep first fresh-process measurement
            first_call_s = raw.get("first_call_s")
            warm_call_s = raw.get("warm_call_s")
            first_call_err = raw.get("first_call_err")

    # 2. -X importtime (top cumulative modules)
    it_rows = run_importtime(py, module, repo_root)
    if it_rows:
        # self-time leaders
        top_self = sorted(it_rows, key=lambda r: -r["self_us"])[:INSTALLED_SIZE_TOP]
        # cumulative of the requested module itself
        target_cum = next((r["cumulative_us"] for r in it_rows if r["module"] == module), None)
        extra["importtime_top_self"] = top_self
        extra["importtime_cumulative_us"] = target_cum
        extra["importtime_total_us"] = sum(r["self_us"] for r in it_rows)

    # 3. installed size (sum across size_targets)
    if not size_targets:
        size_targets = (module,)
    total_bytes = 0
    for target in size_targets:
        try:
            proc = subprocess.run(
                [py, "-c", _SIZE_WORKER, target],
                capture_output=True, text=True, cwd=repo_root, env=env, timeout=120,
            )
            size_raw = json.loads(proc.stdout)
            if size_raw.get("status") == "ok":
                total_bytes += size_raw["total_bytes"]
                extra[f"installed_root_{target}"] = size_raw["root"]
                extra[f"installed_method_{target}"] = size_raw.get("method", "unknown")
                extra[f"installed_bytes_{target}"] = size_raw["total_bytes"]
                if len(size_targets) == 1:
                    extra["installed_root"] = size_raw["root"]
                    extra["installed_top_subdirs"] = [
                        {"name": k, "mb": v / 1e6} for k, v in size_raw["top_subdirs"]
                    ]
        except Exception as e:  # noqa: BLE001 - size measurement is best-effort
            extra[f"installed_size_error_{target}"] = f"{type(e).__name__}: {e}"
    extra["installed_bytes"] = total_bytes
    extra["installed_mb"] = total_bytes / 1e6
    extra["installed_targets"] = list(size_targets)

    extra["import_repeats"] = IMPORT_REPEATS
    extra["import_min_s"] = min(import_times)
    extra["first_call_s"] = first_call_s
    extra["warm_call_s"] = warm_call_s
    if first_call_err:
        extra["first_call_err"] = first_call_err

    status = "ok"
    error_msg = None
    if first_call_err:
        # import worked; first call failed -> keep row but flag it
        status = "ok"
        error_msg = None

    return make_record(label, adapter, status, import_times, error_msg, extra)


def main() -> int:
    parser = argparse.ArgumentParser(description="B3 startup suite")
    parser.add_argument("--threads", type=int, default=16)
    parser.add_argument("--resume", action="store_true", help="skip case_ids already in the output JSONL")
    parser.add_argument("--only", type=str, default=None, help="comma-separated label subset")
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
    print("  B3 Startup Suite (fresh interpreter per import repeat; importtime; installed size)")
    print("=" * 100, flush=True)

    total = len(cases)
    for i, case in enumerate(cases, 1):
        label, adapter, module, tmo = case[0], case[1], case[2], case[3]
        size_targets = tuple(case[4]) if len(case) > 4 else ()
        case_id = f"startup_{label}"
        if case_id in done_ids:
            print(f"  [{i}/{total}] {case_id:<28s} skip (already recorded)", flush=True)
            continue
        print(f"  [{i}/{total}] {case_id:<28s} (timeout {tmo:.0f}s)...", end=" ", flush=True)
        rec = run_case(label, adapter, module, tmo, args.threads, size_targets)
        if rec.status == "ok":
            e = rec.extra
            size = f"{e.get('installed_mb', 0):.1f} MB" if "installed_mb" in e else "n/a"
            fc = e.get("first_call_s")
            print(
                f"ok  import min={rec.stats['min']*1e3:>7.1f} ms  "
                f"first_call={(fc*1e3 if fc else float('nan')):>8.1f} ms  "
                f"installed={size}"
                + (f"  first_call_err={e['first_call_err'][:60]}" if e.get("first_call_err") else "")
            )
        else:
            print(f"{rec.status:<8s} {(rec.error_msg or '')[:110]}")

        with open(OUT_JSONL, "a", encoding="utf-8") as f:
            f.write(json.dumps(rec.to_dict()) + "\n")

    print(f"\nDone. Rows in {OUT_JSONL}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
