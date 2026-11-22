#!/usr/bin/env python3
"""Instruction-count regression gate comparing Base vs Head.

Executes core33 instruction benchmark under valgrind --tool=callgrind
for workloads:
- 1000x500 f64 input
- 1x100 f64 input
- 100x100 f64 input

Fails on >2% instruction-count regression unless override label 'perf-ok' is present.
"""

from __future__ import annotations

import argparse
import json
import os
import re
import subprocess
import sys
from pathlib import Path

WORKLOADS = ["1000x500", "1x100", "100x100"]
THRESHOLD_PCT = 2.0  # Max allowed regression percentage


def parse_callgrind_summary(out_file: Path) -> int:
    """Extract instruction read count (Ir) from callgrind output file."""
    candidates = [out_file]
    candidates.extend(sorted(out_file.parent.glob(f"{out_file.name}.*")))
    for target in candidates:
        if not target.exists():
            continue
        content = target.read_text(encoding="utf-8", errors="replace")
        for line in content.splitlines():
            if line.startswith("summary:"):
                parts = line.split()
                if len(parts) >= 2 and parts[1].isdigit():
                    val = int(parts[1])
                    if val > 0:
                        return val
        for line in content.splitlines():
            if line.startswith("totals:"):
                parts = line.split()
                if len(parts) >= 2 and parts[1].isdigit():
                    val = int(parts[1])
                    if val > 0:
                        return val

    # Print debug info if primary file exists
    if out_file.exists():
        content = out_file.read_text(encoding="utf-8", errors="replace")
        print(f"Debug {out_file} (header):\n{content[:500]}", file=sys.stderr)
    raise ValueError(f"Could not find positive instruction count in {out_file} (checked: {[str(c) for c in candidates]})")


def run_callgrind(binary: Path, workload: str, out_file: Path) -> int:
    """Run binary under valgrind callgrind and return total instruction count."""
    cmd = [
        "valgrind",
        "--tool=callgrind",
        f"--callgrind-out-file={out_file}",
        str(binary),
        workload,
    ]
    env = os.environ.copy()
    env["RAYON_NUM_THREADS"] = "1"  # Strict serial execution for determinism
    proc = subprocess.run(cmd, env=env, capture_output=True, text=True)
    if proc.returncode != 0:
        print(f"Error running callgrind on {binary} {workload}:\n{proc.stderr}", file=sys.stderr)
        raise RuntimeError(f"Valgrind call failed with code {proc.returncode}")
    if proc.stdout:
        print(f"[{workload}] {proc.stdout.strip()}")
    return parse_callgrind_summary(out_file)


def check_override() -> bool:
    """Check if 'perf-ok' override is requested via PR label, env var, or commit msg."""
    if os.environ.get("PERF_OK") == "1" or os.environ.get("OVERRIDE_PERF") == "true":
        return True

    # Check GITHUB_EVENT_PATH for PR labels
    event_path = os.environ.get("GITHUB_EVENT_PATH")
    if event_path and Path(event_path).exists():
        try:
            data = json.loads(Path(event_path).read_text(encoding="utf-8"))
            labels = data.get("pull_request", {}).get("labels", [])
            for lbl in labels:
                if lbl.get("name") == "perf-ok":
                    return True
        except Exception as e:
            print(f"Notice: could not read event json: {e}")

    # Check commit message
    commit_msg = os.environ.get("COMMIT_MESSAGE", "")
    if "perf-ok" in commit_msg.lower():
        return True

    return False


def main() -> int:
    parser = argparse.ArgumentParser(description="Compare instruction counts between base and head")
    parser.add_argument("--head-bin", type=Path, required=True, help="Path to head benchmark binary")
    parser.add_argument("--base-bin", type=Path, default=None, help="Path to base benchmark binary")
    parser.add_argument("--workloads", nargs="+", default=WORKLOADS, help="Workloads to test")
    parser.add_argument("--override", action="store_true", help="Force override of regression gate")
    args = parser.parse_args()

    override_active = args.override or check_override()
    tmp_dir = Path(os.environ.get("RUNNER_TEMP", "/tmp")) / "callgrind_runs"
    tmp_dir.mkdir(parents=True, exist_ok=True)

    if not args.workloads:
        print("Error: No workloads specified.", file=sys.stderr)
        return 1
    valid_workloads = set(WORKLOADS)
    for wl in args.workloads:
        if wl not in valid_workloads:
            print(f"Error: Invalid workload '{wl}'. Valid options: {WORKLOADS}", file=sys.stderr)
            return 1

    base_available = bool(args.base_bin)
    if base_available and not args.base_bin.exists():
        print(f"Error: Base binary specified but file does not exist: {args.base_bin}", file=sys.stderr)
        return 1

    results = []
    has_regression = False

    print("=" * 70)
    print("  Kymora Instruction-Count Performance Gate (core33)")
    print("=" * 70)
    print(f"Head binary: {args.head_bin}")
    print(f"Base binary: {args.base_bin} (available: {base_available})")
    print(f"Override label 'perf-ok': {'ACTIVE' if override_active else 'inactive'}")
    print("-" * 70)

    for wl in args.workloads:
        head_out = tmp_dir / f"callgrind_head_{wl}.out"
        head_ir = run_callgrind(args.head_bin, wl, head_out)

        if base_available:
            base_out = tmp_dir / f"callgrind_base_{wl}.out"
            base_ir = run_callgrind(args.base_bin, wl, base_out)
        else:
            base_ir = None

        if base_ir is not None and base_ir > 0:
            pct_change = ((head_ir - base_ir) / base_ir) * 100.0
            regressed = pct_change > THRESHOLD_PCT
            if regressed:
                has_regression = True
                status = "REGRESSION"
            elif pct_change < -0.5:
                status = "IMPROVED"
            else:
                status = "OK"
        else:
            pct_change = 0.0
            status = "BASE_MISSING"

        results.append({
            "workload": wl,
            "base_ir": base_ir,
            "head_ir": head_ir,
            "pct_change": pct_change,
            "status": status,
        })

    # Generate Markdown Summary
    md_lines = [
        "## Instruction-Count Benchmark Results (`core33`)",
        "",
        "| Workload | Base Instructions | Head Instructions | Change (%) | Status |",
        "| :--- | :--- | :--- | :--- | :--- |",
    ]

    for r in results:
        base_str = f"{r['base_ir']:,}" if r['base_ir'] is not None else "N/A"
        head_str = f"{r['head_ir']:,}"
        if r['base_ir'] is not None:
            sign = "+" if r['pct_change'] > 0 else ""
            change_str = f"{sign}{r['pct_change']:.2f}%"
        else:
            change_str = "—"

        status_str = r['status']
        if r['status'] == "REGRESSION":
            status_str = "**REGRESSION** ❌"
        elif r['status'] == "IMPROVED":
            status_str = "IMPROVED ⚡"
        elif r['status'] == "OK":
            status_str = "OK ✅"

        md_lines.append(f"| `{r['workload']}` | {base_str} | {head_str} | {change_str} | {status_str} |")
        print(f"Workload {r['workload']:10s}: Base={base_str:>12s}, Head={head_str:>12s}, Change={change_str:>8s} -> {r['status']}")

    if override_active:
        md_lines.append("")
        md_lines.append("> ℹ️ **Notice:** Override label `perf-ok` is active; regressions are permitted for this change.")

    # Write to GITHUB_STEP_SUMMARY if present
    step_summary = os.environ.get("GITHUB_STEP_SUMMARY")
    if step_summary:
        with open(step_summary, "a", encoding="utf-8") as f:
            f.write("\n" + "\n".join(md_lines) + "\n")

    print("=" * 70)
    if has_regression and not override_active:
        print(f"FAILED: Instruction count regressed > {THRESHOLD_PCT}%.")
        print("To override this gate for intended architectural changes, add label 'perf-ok' to the PR.")
        return 1
    elif has_regression and override_active:
        print(f"PASSED (OVERRIDE): Instruction count regressed, but 'perf-ok' label is present.")
        return 0

    print("PASSED: All instruction count benchmarks within tolerance.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
