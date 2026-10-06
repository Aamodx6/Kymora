"""Phase B3: Sliding-window benchmark suite.

Per docs/internal/arch.md §11.5 (sliding/streaming): windows 64/256/1024 × strides
1/8/64/window vs tsflex, `sliding_window_view` + baseline, pandas rolling.

Hard Rule 1 (correctness before speed): every mode is verified against
direct per-window recomputation on sampled rows BEFORE timing; a failed
gate is recorded as an explicit `mismatch` row and never timed.

Modes (n_features differ — recorded per row, §11.8):
  - kymora   sliding_features core33 (33 features)
  - swv        np.lib.stride_tricks.sliding_window_view + numpy baseline (33)
  - pandas     .rolling(w).agg mean/std/var/min/max ddof=0 (5)
  - tsflex     tsflex FeatureCollection windows/strides (5, alphabetical cols)

Fresh subprocess per case (tsflex runs in its own venv), warmup + min_runs +
budget protocol, explicit timeout rows. Appended to results/sliding.jsonl
(resume-safe via --resume).
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
OUT_JSONL = RESULTS_DIR / "sliding.jsonl"

N_POINTS = 10_000
WINDOWS = [64, 256, 1024]
STRIDES = [1, 8, 64, "window"]  # "window" == stride == window (non-overlapping)
MODES = ["kymora", "swv", "pandas", "tsflex"]

SAMPLED_ROWS = 6  # correctness gate samples per case


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


_WORKER = r'''
import sys, json, time, gc, os, importlib
import numpy as np

def main():
    cfg = json.loads(sys.stdin.read())
    mode = cfg["mode"]
    w = int(cfg["window"]); st = int(cfg["stride"])
    n = int(cfg["points"]); threads = int(cfg.get("threads", 16))
    seed = int(cfg.get("seed", 42)); min_runs = int(cfg.get("min_runs", 3))
    budget = float(cfg.get("time_budget", 1.0))
    for var in ("RAYON_NUM_THREADS", "OMP_NUM_THREADS", "MKL_NUM_THREADS", "OPENBLAS_NUM_THREADS"):
        os.environ[var] = str(threads)

    rng = np.random.default_rng(seed)
    s = np.ascontiguousarray(rng.standard_normal(n), dtype=np.float64)

    def starts():
        return list(range(0, n - w + 1, st))

    out = {"status": "ok"}
    try:
        if mode == "kymora":
            import kymora
            n_feat = len(kymora.feature_names(profile="core33"))
            def compute():
                return kymora.sliding_features(s, w, st, profile="core33", n_jobs=threads)
            def ref_row(i):
                a = starts()[i]
                return kymora.extract_features(s[a:a+w][None, :], profile="core33")[0]
        elif mode == "swv":
            sys.path.insert(0, cfg["repo_root"])
            mod = importlib.import_module("benchmarks.adapters.numpy_baseline")
            ad = mod.Adapter()
            n_feat = 33
            def compute():
                slv = np.lib.stride_tricks.sliding_window_view(s, w)[::st]
                return ad.extract(slv, feature_set="default", threads=threads)
            def ref_row(i):
                a = starts()[i]
                return ad.extract(s[a:a+w][None, :], feature_set="default", threads=1)[0]
        elif mode == "pandas":
            import pandas as pd
            n_feat = 5
            def compute():
                r = pd.Series(s).rolling(w)
                mat = np.column_stack([
                    r.mean().to_numpy(), r.std(ddof=0).to_numpy(), r.var(ddof=0).to_numpy(),
                    r.min().to_numpy(), r.max().to_numpy(),
                ])
                return mat[w-1::st]
            def ref_row(i):
                a = starts()[i]
                win = s[a:a+w]
                return np.array([win.mean(), win.std(), win.var(), win.min(), win.max()])
        elif mode == "tsflex":
            sys.path.insert(0, cfg["repo_root"])
            mod = importlib.import_module("benchmarks.adapters.tsflex_")
            ad = mod.Adapter()
            n_feat = 5
            def compute():
                return ad.extract_sliding(s, w, st, threads=threads)
            def ref_row(i):
                # tsflex columns are alphabetical: max, mean, min, std, var
                a = starts()[i]
                win = s[a:a+w]
                return np.array([win.max(), win.mean(), win.min(), win.std(), win.var()])
        else:
            raise ValueError(f"unknown mode {mode}")

        # ── Rule 1: correctness gate BEFORE timing ──
        res = compute()
        ns = len(starts())
        n_rows = int(res.shape[0])
        # tsflex may drop the final boundary window (timestamp alignment) — allowed
        allowed_rows = n_rows if mode == "tsflex" else ns
        row_mismatch = abs(n_rows - ns) if mode != "tsflex" else (0 if n_rows in (ns, ns - 1) else abs(n_rows - ns))
        gate_ok = row_mismatch == 0
        gate_max_abs = 0.0
        gate_max_rel = 0.0
        gate_bad_row = None
        if gate_ok:
            idxs = sorted({0, 1, ns // 2, ns - 3, ns - 2, ns - 1,
                           *np.linspace(0, n_rows - 1, SAMPLED if False else 6).astype(int).tolist()})
            idxs = [i for i in idxs if 0 <= i < n_rows and i < ns]
            for i in idxs:
                a = starts()[i]
                r = ref_row(i)
                d = np.abs(res[i] - r)
                denom = np.maximum(np.abs(r), 1e-12)
                rel = float(np.max(d / denom))
                absd = float(np.max(d))
                if rel > gate_max_rel:
                    gate_max_rel = rel
                    gate_max_abs = absd
                if rel > 1e-6:
                    gate_ok = False
                    gate_bad_row = i
                    break
        out.update({
            "gate_ok": bool(gate_ok), "gate_rows_expected": ns, "gate_rows_actual": n_rows,
            "gate_max_abs_diff": gate_max_abs, "gate_max_rel_diff": gate_max_rel,
            "gate_bad_row": gate_bad_row, "n_features": n_feat,
            "output_shape": list(res.shape),
        })
        if not gate_ok:
            out["status"] = "mismatch"
            out["error_msg"] = (
                f"correctness gate failed: rows {n_rows} vs expected {ns}"
                if gate_bad_row is None else
                f"correctness gate failed at row {gate_bad_row}: rel={gate_max_rel:.3e}"
            )
            sys.stdout.write(json.dumps(out)); return

        # ── timing ──
        compute()  # warmup
        gc.disable()
        runs = []
        t_budget = time.perf_counter()
        while True:
            t0 = time.perf_counter()
            compute()
            runs.append(time.perf_counter() - t0)
            if len(runs) >= min_runs and time.perf_counter() - t_budget >= budget:
                break
            if len(runs) >= 50:
                break
        gc.enable()
        out["runs"] = runs
        sys.stdout.write(json.dumps(out))
    except Exception as e:
        out = {"status": "error", "runs": [],
               "error_msg": f"{type(e).__name__}: {e}",
               "exception_type": type(e).__name__}
        sys.stdout.write(json.dumps(out))

if __name__ == "__main__":
    main()
'''


def run_case(mode: str, window: int, stride: int, threads: int) -> BenchmarkRecord:
    stride_label = "window" if stride == window else str(stride)
    case_id = f"slide_{mode}_w{window}_s{stride_label}"
    py = _python_for("tsflex" if mode == "tsflex" else "kymora")
    repo_root = Path(__file__).resolve().parents[2]

    tmo = 300.0 if (mode in ("swv", "tsflex") and window >= 256 and stride == 1) else 180.0
    config = {
        "mode": mode, "window": window, "stride": stride, "points": N_POINTS,
        "threads": threads, "min_runs": 3, "time_budget": 1.0, "seed": 42,
        "repo_root": str(repo_root),
    }
    env = os.environ.copy()
    env["PYTHONPATH"] = str(repo_root) + (os.pathsep + env["PYTHONPATH"] if env.get("PYTHONPATH") else "")

    def rec(status: str, msg: str | None, runs: list[float], extra: dict[str, Any]) -> BenchmarkRecord:
        r = BenchmarkRecord(
            suite="sliding", case_id=case_id, lib=mode, feature_set="default",
            n_series=N_POINTS, length=window, dtype="float64", layout="C",
            threads=threads, dist="gaussian", runs=runs, stats=compute_stats(runs),
            peak_rss_mb=0.0, status=status, guarded=True, error_msg=msg,
            env_ref="env.json", extra=extra,
        )
        valid, vmsg = validate_record(r.to_dict())
        if not valid:
            r.status = "error"
            r.error_msg = f"Schema validation failed: {vmsg}"
        return r

    base_extra: dict[str, Any] = {"variant": mode, "window": window, "stride": stride,
                                  "stride_label": stride_label, "n_points": N_POINTS}
    try:
        proc = subprocess.run(
            [py, "-c", _WORKER],
            input=json.dumps(config), capture_output=True, text=True,
            cwd=repo_root, env=env, timeout=tmo,
        )
    except subprocess.TimeoutExpired:
        return rec("timeout", f"TimeoutExpired: case exceeded {tmo:.0f}s wall clock (recorded as explicit timeout row)", [], base_extra)

    if proc.returncode != 0:
        return rec("error", f"Subprocess failed (exit {proc.returncode}): {proc.stderr.strip()[-500:]}", [], base_extra)
    try:
        raw = json.loads(proc.stdout)
    except Exception as e:
        return rec("error", f"Malformed worker output: {e}; stderr: {proc.stderr[-300:]!r}", [], base_extra)

    runs = raw.pop("runs", [])
    status = raw.get("status", "error")
    msg = raw.pop("error_msg", None)
    extra = {**base_extra, **raw}

    # µs per window-feature (the honest per-unit view)
    if status == "ok" and runs:
        st = compute_stats(runs)
        n_rows = raw.get("gate_rows_actual", 0)
        n_feat = raw.get("n_features", 0)
        if n_rows and n_feat:
            extra["us_per_window_feature"] = st["median"] * 1e6 / (n_rows * n_feat)
        # single-core-equivalent is not derivable here; threads recorded separately
    return rec(status, msg, runs, extra)


def main() -> int:
    parser = argparse.ArgumentParser(description="B3 sliding suite")
    parser.add_argument("--threads", type=int, default=16)
    parser.add_argument("--resume", action="store_true")
    parser.add_argument("--modes", type=str, default=None, help="comma-separated mode subset")
    parser.add_argument("--quick", action="store_true", help="one window/stride only")
    args = parser.parse_args()

    modes = MODES
    if args.modes:
        modes = [m.strip() for m in args.modes.split(",")]
    windows = [64] if args.quick else WINDOWS
    strides_spec = [8] if args.quick else STRIDES

    cases = []
    for w in windows:
        for s in strides_spec:
            st = w if s == "window" else s
            if st > w:
                continue  # stride > window skips windows; only stride == window is meaningful
            if s == "window" and st != w:
                continue
            for m in modes:
                cases.append((m, w, st))

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
    print(f"  B3 Sliding Suite — {N_POINTS:,}-point signal, windows {windows}, modes {modes}")
    print("  Rule 1: correctness gate (vs per-window recompute) before every timed run")
    print("=" * 100, flush=True)

    total = len(cases)
    for i, (mode, w, st) in enumerate(cases, 1):
        stride_label = "window" if st == w else str(st)
        case_id = f"slide_{mode}_w{w}_s{stride_label}"
        if case_id in done_ids:
            print(f"  [{i:2d}/{total}] {case_id:<34s} skip (already recorded)", flush=True)
            continue
        print(f"  [{i:2d}/{total}] {case_id:<34s}...", end=" ", flush=True)
        r = run_case(mode, w, st, args.threads)
        if r.status == "ok":
            e = r.extra
            print(
                f"ok  rows={e['gate_rows_actual']:>5d}  feat={e['n_features']:>2d}  "
                f"gate_rel={e['gate_max_rel_diff']:.1e}  median={r.stats['median']*1e3:>8.1f} ms  "
                f"µs/wf={e.get('us_per_window_feature', float('nan')):>8.3f}"
            )
        else:
            print(f"{r.status:<9s} {(r.error_msg or '')[:110]}")
        with open(OUT_JSONL, "a", encoding="utf-8") as f:
            f.write(json.dumps(r.to_dict()) + "\n")

    print(f"\nDone. Rows in {OUT_JSONL}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
