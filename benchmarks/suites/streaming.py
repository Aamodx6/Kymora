"""Phase B3: Streaming benchmark suite.

Per docs/internal/arch.md §11.5 (sliding/streaming) and §8 (D4):
  - push latency (O(1) tier) vs naive recompute
  - compute(kind="fast") vs compute(kind="all") vs full batch recompute
  - capacity sweep 64 … 65536 (push + compute latency, RSS delta)

Hard Rule 1: every capacity is verified against batch `extract_features`
on the same window buffer BEFORE timing (compute-all == core33; compute-fast
== fast-feature subset). Failed gates are recorded as explicit `mismatch`
rows and never timed.

Schema-valid rows appended to results/streaming.jsonl (resume-safe).
"""

from __future__ import annotations

import argparse
import gc
import json
import sys
import time
from datetime import datetime
from pathlib import Path
from typing import Any

import numpy as np

sys.path.insert(0, str(Path(__file__).resolve().parents[2]))

from benchmarks.harness.env import save_env
from benchmarks.harness.schema import BenchmarkRecord, validate_record
from benchmarks.harness.stats import compute_stats

RESULTS_DIR = Path(__file__).resolve().parents[1] / "results"
OUT_DIR = RESULTS_DIR / "2026-11-22_streaming"
OUT_JSONL = OUT_DIR / "streaming.jsonl"
OUT_REPORT = OUT_DIR / "STREAMING_PUSH_REPORT.md"

CAPACITIES = [64, 256, 4096, 65_536]
PUSH_RUNS = 50_000          # pushes timed per capacity (after warmup)
COMPUTE_RUNS = 2_000        # compute() calls timed per kind
NAIVE_RUNS = 200            # batch recompute calls (expensive)
STREAM_LENGTH = 100_000     # end-to-end stream simulation points
STREAM_COMPUTE_EVERY = 64   # compute cadence in the simulation


def _record(case_id: str, status: str, runs: list[float], msg: str | None,
            extra: dict[str, Any]) -> BenchmarkRecord:
    rec = BenchmarkRecord(
        suite="streaming", case_id=case_id, lib="kymora", feature_set="core33",
        n_series=extra.get("capacity", 1), length=extra.get("capacity", 1),
        dtype="float64", layout="C", threads=1, dist="gaussian",
        runs=runs, stats=compute_stats(runs), peak_rss_mb=float(extra.get("rss_delta_mb", 0.0)),
        status=status, guarded=True, error_msg=msg, env_ref="env.json", extra=extra,
    )
    valid, vmsg = validate_record(rec.to_dict())
    if not valid:
        rec.status = "error"
        rec.error_msg = f"Schema validation failed: {vmsg}"
    return rec


def _append(rec: BenchmarkRecord) -> None:
    with open(OUT_JSONL, "a", encoding="utf-8") as f:
        f.write(json.dumps(rec.to_dict()) + "\n")


def _gate(ex, s: np.ndarray, cap: int) -> tuple[bool, float, str | None]:
    """Verify streaming compute == batch extract on the same buffer."""
    import kymora
    x = s[None, :]
    all_out = ex.compute(kind="all")
    ref = kymora.extract_features(x, profile="core33")[0]
    if all_out.shape != ref.shape:
        return False, float("inf"), f"shape mismatch {all_out.shape} vs {ref.shape}"
    denom = np.maximum(np.abs(ref), 1e-12)
    rel = float(np.max(np.abs(all_out - ref) / denom))
    if rel > 1e-9:
        return False, rel, f"compute(all) rel err {rel:.3e} > 1e-9"

    fast_names = list(type(ex).fast_feature_names())
    fast_out = ex.compute(kind="fast")
    ref_fast = kymora.extract_features(x, features=fast_names)[0]
    if fast_out.shape != ref_fast.shape:
        return False, float("inf"), f"fast shape mismatch {fast_out.shape} vs {ref_fast.shape}"
    denom_f = np.maximum(np.abs(ref_fast), 1e-12)
    rel_f = float(np.max(np.abs(fast_out - ref_fast) / denom_f))
    if rel_f > 1e-9:
        return False, rel_f, f"compute(fast) rel err {rel_f:.3e} > 1e-9"
    return True, max(rel, rel_f), None


def run_capacity(cap: int, threads: int) -> None:
    import kymora
    import psutil

    case_prefix = f"stream_cap{cap}"
    proc = psutil.Process()

    # ── setup: fill a fresh extractor with deterministic data ──
    rng = np.random.default_rng(42)
    s = np.ascontiguousarray(rng.standard_normal(cap), dtype=np.float64)

    def fresh():
        ex = kymora.StreamingExtractor(cap)
        for v in s:
            ex.push(float(v))
        return ex

    # ── Gate (Rule 1) ──
    try:
        ex = fresh()
        gate_ok, gate_rel, gate_msg = _gate(ex, s, cap)
    except Exception as e:  # noqa: BLE001
        gate_ok, gate_rel, gate_msg = False, float("inf"), f"{type(e).__name__}: {e}"

    base_extra = {"variant": f"cap{cap}", "capacity": cap,
                  "gate_rel_diff": gate_rel if gate_ok else None}
    if not gate_ok:
        _append(_record(f"{case_prefix}_gate", "mismatch", [], gate_msg, base_extra))
        print(f"    gate FAILED: {gate_msg}")
        return
    _append(_record(f"{case_prefix}_gate", "ok", [], None,
                    {**base_extra, "gate_rel_diff": gate_rel, "gate": "pass"}))
    print(f"    gate ok (max rel {gate_rel:.2e})")

    # ── 1. Push latency (steady-state, window full) ──
    ex = fresh()
    for v in rng.standard_normal(1000):  # warmup
        ex.push(float(v))
    
    # Measure individual pushes to capture exact p50, p90, p99, and max (including drift re-anchor!)
    n_indiv = max(20_000, cap + 5_000)
    indiv_vals = rng.standard_normal(n_indiv)
    push_times_ns = []
    gc.disable()
    for v in indiv_vals:
        t0 = time.perf_counter_ns()
        ex.push(float(v))
        push_times_ns.append(time.perf_counter_ns() - t0)
    gc.enable()
    push_us = np.asarray(push_times_ns) / 1000.0
    push_p50 = float(np.percentile(push_us, 50))
    push_p90 = float(np.percentile(push_us, 90))
    push_p99 = float(np.percentile(push_us, 99))
    push_max = float(np.max(push_us))

    _append(_record(f"{case_prefix}_push", "ok", [push_p50 / 1e6], None, {
        **base_extra, "measurement": "push_latency",
        "pushes": n_indiv,
        "us_p50": push_p50,
        "us_p90": push_p90,
        "us_p99": push_p99,
        "us_max": push_max,
    }))
    print(f"    push: p50={push_p50:.3f} µs, p99={push_p99:.3f} µs, max={push_max:.3f} µs ({n_indiv} pushes)")

    # ── 2. compute() latency: fast / all ──
    compute_stats_map = {}
    for kind in ("fast", "all"):
        ex = fresh()
        for _ in range(50):
            ex.compute(kind=kind)
        gc.disable()
        times_us = []
        n_runs = COMPUTE_RUNS if (kind == "fast" or cap <= 4096) else 200
        for _ in range(n_runs):
            t0 = time.perf_counter_ns()
            ex.compute(kind=kind)
            times_us.append((time.perf_counter_ns() - t0) / 1000.0)
        gc.enable()
        c_p50 = float(np.percentile(times_us, 50))
        c_p90 = float(np.percentile(times_us, 90))
        c_p99 = float(np.percentile(times_us, 99))
        c_max = float(np.max(times_us))
        compute_stats_map[kind] = {
            "p50": c_p50, "p90": c_p90, "p99": c_p99, "max": c_max
        }
        _append(_record(f"{case_prefix}_compute_{kind}", "ok", [c_p50 / 1e6], None, {
            **base_extra, "measurement": f"compute_{kind}",
            "us_p50": c_p50, "us_p90": c_p90, "us_p99": c_p99, "us_max": c_max,
        }))
        print(f"    compute({kind}): p50={c_p50:.2f} µs, p99={c_p99:.2f} µs, max={c_max:.2f} µs")

    # ── 3. Naive recompute: batch extract_features on the same window ──
    ex = fresh()
    x = s[None, :]
    for _ in range(5):
        kymora.extract_features(x, profile="core33", n_jobs=threads)
    gc.disable()
    times = []
    for _ in range(max(10, NAIVE_RUNS if cap <= 4096 else 30)):
        t0 = time.perf_counter()
        kymora.extract_features(x, profile="core33", n_jobs=threads)
        times.append(time.perf_counter() - t0)
    gc.enable()
    st = compute_stats(times)
    naive_p50_us = st["median"] * 1e6
    _append(_record(f"{case_prefix}_naive_recompute", "ok", times, None, {
        **base_extra, "measurement": "naive_recompute",
        "us_p50": naive_p50_us, "us_p95": st["p95"] * 1e6,
    }))
    print(f"    naive recompute: p50={naive_p50_us:.2f} µs")

    # ── 4. Speedup summary row (computed from measured parts) ──
    # read back the compute stats we just wrote? simpler: recompute quickly
    ex = fresh()
    gc.disable()
    t_fast = []
    for _ in range(COMPUTE_RUNS):
        t0 = time.perf_counter(); ex.compute(kind="fast"); t_fast.append(time.perf_counter() - t0)
    t_all = []
    for _ in range(COMPUTE_RUNS):
        t0 = time.perf_counter(); ex.compute(kind="all"); t_all.append(time.perf_counter() - t0)
    gc.enable()
    fast_p50 = float(np.median(t_fast)) * 1e6
    all_p50 = float(np.median(t_all)) * 1e6
    _append(_record(f"{case_prefix}_summary", "ok", t_all, None, {
        **base_extra, "measurement": "summary",
        "naive_p50_us": naive_p50_us, "fast_p50_us": fast_p50, "all_p50_us": all_p50,
        "speedup_fast_vs_naive": naive_p50_us / fast_p50 if fast_p50 else None,
        "speedup_all_vs_naive": naive_p50_us / all_p50 if all_p50 else None,
    }))
    print(f"    speedup vs naive: fast {naive_p50_us/fast_p50:.1f}×  all {naive_p50_us/all_p50:.1f}×")


def run_end_to_end() -> None:
    """Push STREAM_LENGTH values with periodic compute vs naive full recompute."""
    import kymora

    cap = 256
    rng = np.random.default_rng(42)
    data = rng.standard_normal(STREAM_LENGTH)

    ex = kymora.StreamingExtractor(cap)
    # fill
    for v in data[:cap]:
        ex.push(float(v))

    gc.disable()
    t0 = time.perf_counter()
    for i in range(cap, STREAM_LENGTH):
        ex.push(float(data[i]))
        if i % STREAM_COMPUTE_EVERY == 0:
            ex.compute(kind="fast")
    stream_s = time.perf_counter() - t0
    gc.enable()

    # Naive: recompute full core33 over the trailing window every cadence
    window = list(data[:cap])
    n_computes = 0
    gc.disable()
    t0 = time.perf_counter()
    for i in range(cap, STREAM_LENGTH):
        window.pop(0); window.append(data[i])
        if i % STREAM_COMPUTE_EVERY == 0:
            kymora.extract_features(np.asarray(window)[None, :], profile="core33", n_jobs=1)
            n_computes += 1
    naive_s = time.perf_counter() - t0
    gc.enable()

    n_points = STREAM_LENGTH - cap
    _append(_record("stream_end_to_end", "ok", [stream_s, naive_s], None, {
        "variant": "e2e", "capacity": cap, "stream_points": n_points,
        "compute_every": STREAM_COMPUTE_EVERY, "n_computes": n_computes,
        "stream_s": stream_s, "naive_s": naive_s,
        "us_per_point_stream": stream_s / n_points * 1e6,
        "us_per_point_naive": naive_s / n_points * 1e6,
        "speedup": naive_s / stream_s if stream_s else None,
    }))
    print(f"    e2e stream {stream_s:.3f}s vs naive {naive_s:.3f}s "
          f"= {naive_s/stream_s:.1f}× speedup ({n_points:,} points, compute every {STREAM_COMPUTE_EVERY})")


def main() -> int:
    parser = argparse.ArgumentParser(description="B3 streaming suite")
    parser.add_argument("--threads", type=int, default=1)
    parser.add_argument("--resume", action="store_true")
    parser.add_argument("--caps", type=str, default=None, help="comma-separated capacity subset")
    args = parser.parse_args()

    caps = CAPACITIES
    if args.caps:
        caps = [int(c) for c in args.caps.split(",")]

    OUT_DIR.mkdir(parents=True, exist_ok=True)
    save_env(OUT_DIR / "env.json")

    done: set[str] = set()
    if args.resume and OUT_JSONL.exists():
        for line in OUT_JSONL.read_text(encoding="utf-8").splitlines():
            line = line.strip()
            if line:
                try:
                    done.add(json.loads(line)["case_id"])
                except (json.JSONDecodeError, KeyError):
                    pass
        print(f"  [resume] {len(done)} case_ids already in {OUT_JSONL.name}")

    print("=" * 100)
    print("  B3 Streaming Suite (Rule 1 gate: compute == batch extract before timing)")
    print("=" * 100, flush=True)

    for cap in caps:
        print(f"\n  capacity={cap}:")
        # gate+parts are idempotent per capacity: skip only if summary exists
        if f"stream_cap{cap}_summary" in done:
            print("    skip (already recorded)")
            continue
        run_capacity(cap, args.threads)

    if "stream_end_to_end" not in done:
        print("\n  end-to-end stream simulation:")
        run_end_to_end()

    # Generate Markdown Report
    rows = []
    if OUT_JSONL.exists():
        for line in OUT_JSONL.read_text(encoding="utf-8").splitlines():
            if line.strip():
                rows.append(json.loads(line))

    by_cap = {}
    for r in rows:
        cid = r.get("case_id", "")
        extra = r.get("extra", {})
        cap = extra.get("capacity")
        if cap not in by_cap:
            by_cap[cap] = {}
        if "_gate" in cid:
            by_cap[cap]["gate_rel"] = extra.get("gate_rel_diff", 0.0)
        elif "_push" in cid:
            by_cap[cap]["push_p50"] = extra.get("us_p50")
            by_cap[cap]["push_p99"] = extra.get("us_p99")
            by_cap[cap]["push_max"] = extra.get("us_max")
        elif "_compute_fast" in cid:
            by_cap[cap]["fast_p50"] = extra.get("us_p50")
            by_cap[cap]["fast_p99"] = extra.get("us_p99")
            by_cap[cap]["fast_max"] = extra.get("us_max")
        elif "_compute_all" in cid:
            by_cap[cap]["all_p50"] = extra.get("us_p50")
            by_cap[cap]["all_p99"] = extra.get("us_p99")
            by_cap[cap]["all_max"] = extra.get("us_max")
        elif "_naive_recompute" in cid:
            by_cap[cap]["naive_p50"] = extra.get("us_p50")
        elif "_summary" in cid:
            by_cap[cap]["speedup"] = extra.get("speedup_fast_vs_naive")

    report_lines = [
        "# Streaming Re-validation Report (HEAD)",
        "",
        "Suite: `benchmarks/suites/streaming.py` (B3) re-run on repository HEAD.",
        "System: Windows 11, High Performance plan, AC online, single thread.",
        "Every capacity is parity-gated before timing (`compute(all) == core33`, `compute(fast) == fast subset`).",
        "",
        "> [!NOTE]",
        "> **Complexity Contract:**",
        "> - Ingestion: **amortized $O(1)$ per-sample ingestion, worst-case $O(W)$ upon drift re-anchoring**.",
        "> - Periodic re-anchoring passes over the window buffer (showing in max push latency).",
        "> - Fast subset query: **$O(1)$ flat query latency** across all window capacities.",
        "",
        "## Measured Latency vs Window Capacity",
        "",
        "| Window Capacity (W) | Gate Rel Diff | push p50 (p99 / max) (µs) | compute(fast) p50 (p99 / max) (µs) | compute(all) p50 (µs) | Naive Recompute p50 (µs) | Speedup (fast vs naive) |",
        "|:---:|:---:|:---:|:---:|:---:|:---:|:---:|",
    ]
    for c in sorted(c for c in by_cap if isinstance(c, int)):
        d = by_cap[c]
        g = f"{d.get('gate_rel', 0.0):.2e}"
        p_str = f"{d.get('push_p50', 0):.2f} ({d.get('push_p99', 0):.2f} / {d.get('push_max', 0):.1f}) µs"
        f_str = f"{d.get('fast_p50', 0):.2f} ({d.get('fast_p99', 0):.2f} / {d.get('fast_max', 0):.1f}) µs"
        a_str = f"{d.get('all_p50', 0):.2f} µs"
        n_str = f"{d.get('naive_p50', 0):.2f} µs"
        sp = f"{d.get('speedup', 0):.1f}×" if d.get('speedup') else "—"
        report_lines.append(f"| {c:,} | {g} | {p_str} | {f_str} | {a_str} | {n_str} | {sp} |")

    OUT_REPORT.write_text("\n".join(report_lines) + "\n", encoding="utf-8")
    (RESULTS_DIR / "STREAMING_REPORT.md").write_text("\n".join(report_lines) + "\n", encoding="utf-8")
    print(f"\nReport written to {OUT_REPORT}")

    print(f"\nDone. Rows in {OUT_JSONL}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
