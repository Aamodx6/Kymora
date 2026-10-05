"""Build the Phase 2.4 streaming artifact from B3 suite rows.

Reads the rows appended to benchmarks/results/streaming.jsonl by the most
recent `benchmarks/suites/streaming.py` run (all rows after SKIP_ROWS), and
writes:
  benchmarks/results/2026-10-05_streaming/streaming.jsonl  (frozen copy)
  benchmarks/results/2026-10-05_streaming/env.json          (frozen copy)
  benchmarks/results/2026-10-05_streaming/STREAMING_PUSH_REPORT.md
  docs/img/streaming_push_cost.png                          (log-log plot)

Usage: python tools/streaming_report.py [skip_rows]
"""

from __future__ import annotations

import json
import shutil
import sys
from pathlib import Path

REPO = Path(__file__).resolve().parents[1]
RESULTS = REPO / "benchmarks" / "results"
OUT_DIR = RESULTS / "2026-10-05_streaming"
SKIP_ROWS = int(sys.argv[1]) if len(sys.argv) > 1 else 0


def main() -> int:
    rows = [
        json.loads(line)
        for line in (RESULTS / "streaming.jsonl").read_text(encoding="utf-8").splitlines()
        if line.strip()
    ]
    new_rows = rows[SKIP_ROWS:]
    print(f"total rows: {len(rows)}, new rows: {len(new_rows)}")
    assert new_rows, "no new rows found"

    OUT_DIR.mkdir(parents=True, exist_ok=True)
    with open(OUT_DIR / "streaming.jsonl", "w", encoding="utf-8") as f:
        for r in new_rows:
            f.write(json.dumps(r) + "\n")
    env_src = RESULTS / "env.json"
    if env_src.exists():
        shutil.copy(env_src, OUT_DIR / "env.json")

    by_case = {r["case_id"]: r for r in new_rows}
    caps = [64, 256, 4096, 65536]

    lines = [
        "# Streaming per-push cost vs window size (Phase 2.4)",
        "",
        "Suite: `benchmarks/suites/streaming.py` (B3), run 2026-10-05 on",
        "i7-13620H laptop (10 cores / 16 threads), Windows 11, Performance plan,",
        "AC online, single thread. Every capacity parity-gated before timing",
        "(`compute(all) == core33`, `compute(fast) == fast subset`, max rel err",
        "shown). Exploratory single-machine numbers, not fleet evidence.",
        "",
        "| Capacity | Gate max rel | push (µs) | compute fast p50 (µs) | compute all p50 (µs) | naive recompute p50 (µs) |",
        "| --- | --- | --- | --- | --- | --- |",
    ]
    push_us, fast_us, all_us = [], [], []
    for cap in caps:
        gate = by_case[f"stream_cap{cap}_gate"]["extra"]["gate_rel_diff"]
        push = by_case[f"stream_cap{cap}_push"]["extra"]["us_per_push"]
        fast = by_case[f"stream_cap{cap}_compute_fast"]["extra"]["us_p50"]
        allc = by_case[f"stream_cap{cap}_compute_all"]["extra"]["us_p50"]
        naive = by_case[f"stream_cap{cap}_naive_recompute"]["extra"]["us_p50"]
        push_us.append(push)
        fast_us.append(fast)
        all_us.append(allc)
        lines.append(
            f"| {cap} | {gate:.2e} | {push:.3f} | {fast:.2f} | {allc:.1f} | {naive:.1f} |"
        )
    e2e = by_case["stream_end_to_end"]["extra"]
    lines += [
        "",
        f"End-to-end (cap 256, {e2e['stream_points']:,} points, compute every "
        f"{e2e['compute_every']}): streaming {e2e['stream_s']:.3f}s vs naive "
        f"{e2e['naive_s']:.3f}s = {e2e['speedup']:.1f}x speedup.",
        "",
        "Reading: `push` and `compute(fast)` are flat across 64..65536 (O(1));",
        "`compute(all)` grows linearly with W (O(W) batch pipeline).",
        "",
        "![per-push and compute cost vs window size](../../docs/img/streaming_push_cost.png)",
    ]
    (OUT_DIR / "STREAMING_PUSH_REPORT.md").write_text("\n".join(lines) + "\n", encoding="utf-8")

    # Plot (real data only).
    import matplotlib

    matplotlib.use("Agg")
    import matplotlib.pyplot as plt

    img_dir = REPO / "docs" / "img"
    img_dir.mkdir(parents=True, exist_ok=True)
    fig, ax = plt.subplots(figsize=(7, 4.2))
    ax.loglog(caps, push_us, "o-", label="push (per sample)")
    ax.loglog(caps, fast_us, "s-", label="compute(kind='fast')")
    ax.loglog(caps, all_us, "^-", label="compute(kind='all')")
    ax.set_xlabel("window size W")
    ax.set_ylabel("microseconds (median)")
    ax.set_title("Streaming cost vs window size (i7-13620H, exploratory)")
    ax.legend()
    ax.grid(True, which="both", alpha=0.3)
    fig.tight_layout()
    fig.savefig(img_dir / "streaming_push_cost.png", dpi=120)
    print("wrote", OUT_DIR / "STREAMING_PUSH_REPORT.md")
    print("wrote", img_dir / "streaming_push_cost.png")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
