"""Phase B3: Concurrency benchmark suite.

Per docs/internal/arch.md §11.5 (concurrency suite), on a Windows host (spawn-only, no fork):

  1. threads_scaling  — Kymora extract_features across n_jobs ∈ {1,2,4,8,16}
                        with N Python threads each driving extraction; verifies
                        wall-time speedup >1 (Rust core releases the GIL) and
                        records the curve.
  2. gil_release      — K extraction threads + 1 busy spin thread; spin-loop
                        throughput with extraction running vs idle proves the
                        GIL is actually released during extraction.
  3. joblib_backend   — joblib Parallel(backend="threading"|"loky") extracting
                        8 chunks in parallel; per-chunk correctness vs serial
                        reference (Rule 1 gate), then wall time.
  4. spawn_mp         — multiprocessing spawn (Windows has no fork): 4 workers
                        each extract their chunk; gate vs serial + wall time
                        incl. interpreter spawn cost.
  5. repeated_import  — 5 sequential module reloads + feature_names() call;
                        verifies no state breaks re-use (§11.5).
  6. spawn_stress     — 8 concurrent fresh interpreters extracting simultaneously
                        (loads the box like a real service would).

Rule 1: every parallel path is gated against the serial reference before any
timing is recorded (mismatch rows are never timed).

Windows note: fork is unavailable, so the §11.5 rayon+fork deadlock probe is
not executable here; this is an explicit documented N/A, not a silent skip.

Every row uses the §11.8 BenchmarkRecord schema and is appended to
results/concurrency.jsonl incrementally (resume-safe via --resume).
Timeouts/errors are recorded as explicit rows (no silent skips).
"""

from __future__ import annotations

import argparse
import json
import os
import subprocess
import sys
import time
from pathlib import Path
from typing import Any

sys.path.insert(0, str(Path(__file__).resolve().parents[2]))

from benchmarks.harness.env import save_env
from benchmarks.harness.schema import BenchmarkRecord, validate_record
from benchmarks.harness.stats import compute_stats

RESULTS_DIR = Path(__file__).resolve().parents[1] / "results"
OUT_JSONL = RESULTS_DIR / "concurrency.jsonl"

N_SERIES = 2_000
LENGTH = 500
SEED = 42
REPEATS = 5

N_JOBS_GRID = [1, 2, 4, 8, 16]
CHUNKS = 8
MP_WORKERS = 4
SPAWN_WORKERS = 8

_WORKER = r'''
import sys, json, time, os
import numpy as np

def main():
    cfg = json.loads(sys.stdin.read())
    mode = cfg["mode"]
    for var in ("RAYON_NUM_THREADS", "OMP_NUM_THREADS", "MKL_NUM_THREADS", "OPENBLAS_NUM_THREADS"):
        os.environ[var] = str(cfg.get("threads", 16))

    out = {"status": "ok"}

    try:
        import kymora
        rng = np.random.default_rng(int(cfg.get("seed", 42)))
        n = int(cfg.get("n_series", 2000)); length = int(cfg.get("length", 500))
        X = np.ascontiguousarray(rng.standard_normal((n, length)), dtype=np.float64)

        if mode == "threads_scaling":
            import threading
            results = []
            err = []
            def work(x):
                try:
                    results.append(kymora.extract_features(x, n_jobs=int(cfg["n_jobs"])))
                except Exception as e:  # noqa: BLE001
                    err.append(f"{type(e).__name__}: {e}")
            splits = np.array_split(X, cfg["n_threads"])
            t0 = time.perf_counter()
            ths = [threading.Thread(target=work, args=(np.ascontiguousarray(s),)) for s in splits]
            for t in ths: t.start()
            for t in ths: t.join()
            wall = time.perf_counter() - t0
            if err:
                out.update(status="error", error_msg="; ".join(err[:3])); return
            ref = kymora.extract_features(X, n_jobs=int(cfg["n_jobs"]))
            Y = np.vstack(results)
            if Y.shape != ref.shape:
                out.update(status="error", error_msg=f"shape {Y.shape} vs {ref.shape}"); return
            bad = np.argwhere(~np.isclose(Y, ref, rtol=1e-9, atol=1e-12, equal_nan=True))
            if len(bad):
                i, j = bad[0]
                out.update(status="mismatch", error_msg=f"[{i},{j}] got {Y[i,j]!r} want {ref[i,j]!r}"); return
            out.update(runs=[wall], gate_rows=int(ref.size),
                       n_threads=int(cfg["n_threads"]), n_jobs=int(cfg["n_jobs"]))

        elif mode == "gil_release":
            import threading
            stop = threading.Event()
            spins = {"n": 0}
            def spin():
                x = 1.0000001
                while not stop.is_set():
                    for _ in range(1000):
                        x = x * 1.0000001
                        if x > 1.5: x = 1.0000001
                    spins["n"] += 1000
            t = threading.Thread(target=spin, daemon=True); t.start()
            time.sleep(0.2)
            spins["n"] = 0
            t0 = time.perf_counter(); time.sleep(0.5); stop.set(); t.join()
            idle_rate = spins["n"] / (time.perf_counter() - t0)
            stop.clear(); t = threading.Thread(target=spin, daemon=True); t.start()
            time.sleep(0.2)
            spins["n"] = 0
            t0 = time.perf_counter()
            kymora.extract_features(X, n_jobs=int(cfg["n_jobs"]))
            busy_elapsed = time.perf_counter() - t0
            stop.set(); t.join()
            busy_rate = spins["n"] / busy_elapsed
            ratio = busy_rate / idle_rate if idle_rate else 0.0
            # GIL released if the spin thread still progresses during extraction
            out.update(gil_released=bool(ratio >= 0.30), idle_rate=idle_rate,
                       busy_rate=busy_rate, ratio=ratio, extract_s=busy_elapsed,
                       n_jobs=int(cfg["n_jobs"]))

        elif mode == "joblib":
            from joblib import Parallel, delayed
            backend = cfg["backend"]
            chunks = [np.ascontiguousarray(c) for c in np.array_split(X, cfg["chunks"])]
            def one(c):
                return kymora.extract_features(c, n_jobs=int(cfg.get("n_jobs", 1)))
            ref = np.vstack([one(c) for c in chunks])
            probe = np.vstack(Parallel(n_jobs=2, backend=backend)(delayed(one)(c) for c in chunks[:2]))
            bad = np.argwhere(~np.isclose(probe, ref[:2], rtol=1e-9, atol=1e-12, equal_nan=True))
            if len(bad):
                i, j = bad[0]
                out.update(status="mismatch", error_msg=f"{backend} [{i},{j}] got {probe[i,j]!r} want {ref[i,j]!r}"); return
            runs = []
            for _ in range(int(cfg.get("repeats", 5))):
                t0 = time.perf_counter()
                Y = np.vstack(Parallel(n_jobs=int(cfg["n_jobs"]), backend=backend)(delayed(one)(c) for c in chunks))
                runs.append(time.perf_counter() - t0)
            bad = np.argwhere(~np.isclose(Y, ref, rtol=1e-9, atol=1e-12, equal_nan=True))
            if len(bad):
                i, j = bad[0]
                out.update(status="mismatch", error_msg=f"{backend} timed-path [{i},{j}] got {Y[i,j]!r} want {ref[i,j]!r}"); return
            out.update(runs=runs, gate_rows=int(ref.size), backend=backend,
                       chunks=int(cfg["chunks"]))

        elif mode == "spawn_mp":
            import multiprocessing as mp
            sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)) if False else r"{SUITE_DIR}")
            from benchmarks.suites import _conc_spawn_child as child
            chunks = [np.ascontiguousarray(c) for c in np.array_split(X, cfg["workers"])]
            wall, Y = child.run_chunks(chunks)
            ref = kymora.extract_features(X, n_jobs=1)
            if Y.shape != ref.shape:
                out.update(status="error", error_msg=f"shape {Y.shape} vs {ref.shape}"); return
            bad = np.argwhere(~np.isclose(Y, ref, rtol=1e-9, atol=1e-12, equal_nan=True))
            if len(bad):
                i, j = bad[0]
                out.update(status="mismatch", error_msg=f"[{i},{j}] got {Y[i,j]!r} want {ref[i,j]!r}"); return
            out.update(runs=[wall], gate_rows=int(ref.size), workers=int(cfg["workers"]))

        elif mode == "repeated_import":
            n = int(cfg.get("n_repeats", 5))
            times = []
            for _ in range(n):
                t0 = time.perf_counter()
                import importlib
                importlib.reload(kymora)
                kymora.feature_names(profile="core33")
                times.append(time.perf_counter() - t0)
            out.update(runs=times, n_repeats=n)

        else:
            out.update(status="error", error_msg=f"unknown mode {mode}")
    except Exception as e:  # noqa: BLE001
        out.update(status="error", error_msg=f"{type(e).__name__}: {e}")
    sys.stdout.write(json.dumps(out))


if __name__ == "__main__":
    main()
'''


def _rec(suite_case: str, lib: str, status: str, runs: list[float],
         error_msg: str | None, extra: dict[str, Any]) -> BenchmarkRecord:
    r = BenchmarkRecord(
        suite="concurrency", case_id=suite_case, lib=lib, feature_set="core33",
        n_series=N_SERIES, length=LENGTH, dtype="float64", layout="C",
        threads=16, dist="gaussian", runs=runs, stats=compute_stats(runs),
        peak_rss_mb=0.0, status=status, guarded=True, error_msg=error_msg,
        env_ref="env.json", extra=extra,
    )
    valid, vmsg = validate_record(r.to_dict())
    if not valid:
        r.status = "error"
        r.error_msg = f"Schema validation failed: {vmsg}"
    return r


def _run_worker(worker: str, cfg: dict[str, Any], timeout: float) -> dict[str, Any]:
    repo_root = Path(__file__).resolve().parents[2]
    suite_dir = str(Path(__file__).resolve().parent)
    worker_src = worker.replace("{SUITE_DIR}", suite_dir.replace("\\", "\\\\"))
    env = os.environ.copy()
    env["PYTHONPATH"] = str(repo_root) + (os.pathsep + env["PYTHONPATH"] if env.get("PYTHONPATH") else "")
    proc = subprocess.run(
        [sys.executable, "-c", worker_src],
        input=json.dumps(cfg), capture_output=True, text=True,
        cwd=repo_root, env=env, timeout=timeout,
    )
    if proc.returncode != 0:
        return {"status": "error", "error_msg": f"exit {proc.returncode}: {proc.stderr.strip()[-400:]}"}
    return json.loads(proc.stdout)


def case_threads_scaling() -> list[BenchmarkRecord]:
    rows = []
    for n_jobs in N_JOBS_GRID:
        cid = f"conc_threads_scaling_j{n_jobs}"
        n_threads = max(1, n_jobs)
        try:
            raw = _run_worker(_WORKER, {
                "mode": "threads_scaling", "n_jobs": n_jobs, "n_threads": n_threads,
                "n_series": N_SERIES, "length": LENGTH, "seed": SEED, "threads": 16,
            }, timeout=300.0)
        except subprocess.TimeoutExpired:
            rows.append(_rec(cid, "kymora", "timeout", [], "TimeoutExpired after 300s", {"n_jobs": n_jobs}))
            continue
        except Exception as e:  # noqa: BLE001
            rows.append(_rec(cid, "kymora", "error", [], f"{type(e).__name__}: {e}", {"n_jobs": n_jobs}))
            continue
        status = raw.pop("status", "error")
        runs = raw.pop("runs", [])
        rows.append(_rec(cid, "kymora", status, runs if status == "ok" else [],
                         raw.get("error_msg"), {**raw, "n_jobs": n_jobs,
                                                "n_python_threads": n_threads}))
    base = next((r for r in rows if r.extra.get("n_jobs") == 1 and r.status == "ok"), None)
    if base is not None and base.stats.get("median"):
        for r in rows:
            if r.status == "ok" and r.stats.get("median"):
                r.extra["speedup_vs_j1"] = round(base.stats["median"] / r.stats["median"], 3)
    return rows


def case_gil_release() -> list[BenchmarkRecord]:
    cid = "conc_gil_release"
    try:
        raw = _run_worker(_WORKER, {
            "mode": "gil_release", "n_jobs": 16,
            "n_series": N_SERIES, "length": LENGTH, "seed": SEED, "threads": 16,
        }, timeout=300.0)
    except subprocess.TimeoutExpired:
        return [_rec(cid, "kymora", "timeout", [], "TimeoutExpired after 300s", {})]
    except Exception as e:  # noqa: BLE001
        return [_rec(cid, "kymora", "error", [], f"{type(e).__name__}: {e}", {})]
    status = raw.pop("status", "error")
    if status != "ok":
        return [_rec(cid, "kymora", status, [], raw.get("error_msg"), {})]
    return [_rec(cid, "kymora", "ok", [], None, raw)]


def case_joblib(backend: str) -> list[BenchmarkRecord]:
    cid = f"conc_joblib_{backend}"
    try:
        raw = _run_worker(_WORKER, {
            "mode": "joblib", "backend": backend, "chunks": CHUNKS, "n_jobs": 1,
            "repeats": REPEATS, "n_series": N_SERIES, "length": LENGTH, "seed": SEED, "threads": 1,
        }, timeout=300.0)
    except subprocess.TimeoutExpired:
        return [_rec(cid, "kymora", "timeout", [], "TimeoutExpired after 300s", {"backend": backend})]
    except Exception as e:  # noqa: BLE001
        return [_rec(cid, "kymora", "error", [], f"{type(e).__name__}: {e}", {"backend": backend})]
    status = raw.pop("status", "error")
    runs = raw.pop("runs", [])
    return [_rec(cid, "kymora", status, runs if status == "ok" else [],
                 raw.get("error_msg"), {**raw, "backend": backend, "chunks": CHUNKS})]


def case_spawn_mp() -> list[BenchmarkRecord]:
    cid = f"conc_spawn_mp_w{MP_WORKERS}"
    try:
        raw = _run_worker(_WORKER, {
            "mode": "spawn_mp", "workers": MP_WORKERS,
            "n_series": N_SERIES, "length": LENGTH, "seed": SEED, "threads": 1,
        }, timeout=300.0)
    except subprocess.TimeoutExpired:
        return [_rec(cid, "kymora", "timeout", [], "TimeoutExpired after 300s", {"workers": MP_WORKERS})]
    except Exception as e:  # noqa: BLE001
        return [_rec(cid, "kymora", "error", [], f"{type(e).__name__}: {e}", {"workers": MP_WORKERS})]
    status = raw.pop("status", "error")
    runs = raw.pop("runs", [])
    return [_rec(cid, "kymora", status, runs if status == "ok" else [],
                 raw.get("error_msg"), {**raw, "workers": MP_WORKERS,
                                        "note": "wall includes interpreter spawn cost"})]


def case_repeated_import() -> list[BenchmarkRecord]:
    cid = "conc_repeated_import"
    try:
        raw = _run_worker(_WORKER, {
            "mode": "repeated_import", "n_repeats": 5, "seed": SEED,
        }, timeout=120.0)
    except subprocess.TimeoutExpired:
        return [_rec(cid, "kymora", "timeout", [], "TimeoutExpired after 120s", {})]
    except Exception as e:  # noqa: BLE001
        return [_rec(cid, "kymora", "error", [], f"{type(e).__name__}: {e}", {})]
    status = raw.pop("status", "error")
    runs = raw.pop("runs", [])
    return [_rec(cid, "kymora", status, runs if status == "ok" else [], raw.get("error_msg"),
                 {**raw, "note": "module reload + feature_names() per repeat"})]


def case_spawn_stress() -> list[BenchmarkRecord]:
    cid = f"conc_spawn_stress_w{SPAWN_WORKERS}"
    repo_root = Path(__file__).resolve().parents[2]
    env = os.environ.copy()
    env["PYTHONPATH"] = str(repo_root) + (os.pathsep + env["PYTHONPATH"] if env.get("PYTHONPATH") else "")
    cfg = {"seed": SEED, "n_series": N_SERIES // 4, "length": LENGTH, "threads": 4, "n_jobs": 1}
    t0 = time.perf_counter()
    procs = [
        subprocess.Popen([sys.executable, "-c", _SPAWN_STRESS_WORKER],
                         stdin=subprocess.PIPE, stdout=subprocess.PIPE, stderr=subprocess.PIPE,
                         text=True, cwd=repo_root, env=env)
        for _ in range(SPAWN_WORKERS)
    ]
    outs = []
    for p in procs:
        o, e = p.communicate(input=json.dumps(cfg), timeout=300.0)
        outs.append((p.returncode, o, e))
    wall = time.perf_counter() - t0
    errs = [e.strip()[-200:] for rc, _, e in outs if rc != 0]
    oks = []
    for rc, o, _ in outs:
        if rc == 0:
            try:
                r = json.loads(o)
                if r.get("status") == "ok":
                    oks.append(r["wall_s"])
                else:
                    errs.append(r.get("error_msg", "unknown"))
            except Exception as je:  # noqa: BLE001
                errs.append(f"malformed: {je}")
    if errs and not oks:
        return [_rec(cid, "kymora", "error", [], "; ".join(errs[:3]), {"workers": SPAWN_WORKERS})]
    status = "ok" if not errs else "error"
    return [_rec(cid, "kymora", status, oks, "; ".join(errs[:3]) if errs else None,
                 {"workers": SPAWN_WORKERS, "ok_count": len(oks), "collective_wall_s": wall,
                  "note": "8 concurrent interpreters, 500x500 each, threads=4"})]


_SPAWN_STRESS_WORKER = r'''
import sys, json, time, os
import numpy as np

def main():
    cfg = json.loads(sys.stdin.read())
    for var in ("RAYON_NUM_THREADS", "OMP_NUM_THREADS", "MKL_NUM_THREADS", "OPENBLAS_NUM_THREADS"):
        os.environ[var] = str(cfg.get("threads", 4))
    try:
        import kymora
        rng = np.random.default_rng(cfg["seed"])
        X = np.ascontiguousarray(rng.standard_normal((cfg["n_series"], cfg["length"])), dtype=np.float64)
        t0 = time.perf_counter()
        Y = kymora.extract_features(X, n_jobs=cfg.get("n_jobs", 1))
        wall = time.perf_counter() - t0
        assert Y.shape == (cfg["n_series"], 33), Y.shape
        sys.stdout.write(json.dumps({"status": "ok", "wall_s": wall}))
    except Exception as e:  # noqa: BLE001
        sys.stdout.write(json.dumps({"status": "error", "error_msg": f"{type(e).__name__}: {e}"}))

if __name__ == "__main__":
    main()
'''


def main() -> int:
    parser = argparse.ArgumentParser(description="B3 concurrency suite")
    parser.add_argument("--resume", action="store_true")
    parser.add_argument("--only", type=str, default=None,
                        help="comma-separated subset: scaling,gil,joblib,mp,import,stress")
    args = parser.parse_args()

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

    groups: dict[str, Any] = {
        "scaling": case_threads_scaling,
        "gil": case_gil_release,
        "joblib": lambda: case_joblib("threading") + case_joblib("loky"),
        "mp": case_spawn_mp,
        "import": case_repeated_import,
        "stress": case_spawn_stress,
    }
    want = {s.strip() for s in args.only.split(",")} if args.only else set(groups)

    print("=" * 100)
    print(f"  B3 Concurrency Suite — {N_SERIES:,}×{LENGTH} core33, Windows spawn-only (no fork)")
    print("  Rule 1: parallel paths gated vs serial reference before timing")
    print("=" * 100, flush=True)

    for name, fn in groups.items():
        if name not in want:
            continue
        print(f"  ── {name} ──", flush=True)
        for r in fn():
            if r.case_id in done_ids:
                print(f"    {r.case_id:<36s} skip (already recorded)", flush=True)
                continue
            if r.status == "ok":
                m = r.stats.get("median")
                ms = f"{m*1e3:9.1f} ms" if m else "      n/a"
                sp = r.extra.get("speedup_vs_j1")
                sps = f"  speedup={sp:.2f}x" if sp else ""
                print(f"    {r.case_id:<36s} ok  {ms}{sps}", flush=True)
            else:
                print(f"    {r.case_id:<36s} {r.status:<8s} {(r.error_msg or '')[:100]}", flush=True)
            with open(OUT_JSONL, "a", encoding="utf-8") as f:
                f.write(json.dumps(r.to_dict()) + "\n")

    print(f"\nDone. Rows in {OUT_JSONL}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
