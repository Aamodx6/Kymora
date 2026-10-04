"""Report generator: parses benchmark JSONL and outputs REPORT.md, results.json, and SVG charts."""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any

REPORT_DIR = Path(__file__).resolve().parent
RESULTS_ROOT = Path(__file__).resolve().parents[1] / "results"
CHARTS_DIR = REPORT_DIR / "charts"


def generate_svg_bar_chart(
    title: str,
    categories: list[str],
    values: list[float],
    unit: str,
    out_path: Path,
) -> None:
    """Generate clean, publication-ready SVG bar chart without matplotlib dependency."""
    out_path.parent.mkdir(parents=True, exist_ok=True)
    if not values or max(values) <= 0:
        return

    width = 800
    row_height = 40
    margin_left = 180
    margin_right = 80
    margin_top = 60
    margin_bottom = 30
    chart_width = width - margin_left - margin_right
    height = margin_top + margin_bottom + len(categories) * row_height

    max_val = max(values)

    svg = [
        f'<svg width="{width}" height="{height}" xmlns="http://www.w3.org/2000/svg" font-family="-apple-system, BlinkMacSystemFont, Segoe UI, Roboto, Helvetica, Arial, sans-serif">',
        f'  <rect width="100%" height="100%" fill="#ffffff" />',
        f'  <text x="{width/2}" y="32" text-anchor="middle" font-size="16" font-weight="bold" fill="#111827">{title}</text>',
    ]

    for idx, (cat, val) in enumerate(zip(categories, values)):
        y = margin_top + idx * row_height
        bar_len = (val / max_val) * chart_width if max_val > 0 else 0
        is_tsx = "tsxtract" in cat.lower()
        bar_color = "#2563eb" if is_tsx else "#94a3b8"

        svg.append(f'  <text x="{margin_left - 12}" y="{y + 24}" text-anchor="end" font-size="13" fill="#374151">{cat}</text>')
        svg.append(f'  <rect x="{margin_left}" y="{y + 8}" width="{max(2.0, bar_len)}" height="24" rx="3" fill="{bar_color}" />')
        svg.append(f'  <text x="{margin_left + bar_len + 8}" y="{y + 25}" font-size="12" font-weight="600" fill="#1e293b">{val:.2f} {unit}</text>')

    svg.append('</svg>')
    out_path.write_text("\n".join(svg), encoding="utf-8")


def generate_report(results_path: Path | None = None) -> None:
    # Locate latest results dir
    if results_path is None:
        subdirs = [p for p in RESULTS_ROOT.iterdir() if p.is_dir() and not p.name.startswith(".")]
        if not subdirs:
            print("No results directory found.")
            return
        subdirs.sort(key=lambda p: p.stat().st_mtime, reverse=True)
        results_dir = subdirs[0]
    else:
        results_dir = results_path

    env_file = results_dir / "env.json"
    env_data = json.loads(env_file.read_text(encoding="utf-8")) if env_file.exists() else {}

    records: list[dict[str, Any]] = []
    for f in results_dir.glob("*.jsonl"):
        for line in f.read_text(encoding="utf-8").splitlines():
            line = line.strip()
            if line:
                try:
                    records.append(json.loads(line))
                except Exception:
                    pass

    if not records:
        print("No valid JSONL records found to report.")
        return

    from benchmarks.harness.env import check_environment_warnings

    warnings = check_environment_warnings(env_data)

    cpu_info = env_data.get("cpu", {})
    phys_cores = cpu_info.get("physical_cores", 1) or 1
    log_cores = cpu_info.get("logical_cores", 1) or 1
    p_cores = cpu_info.get("p_cores")
    e_cores = cpu_info.get("e_cores")
    topo_str = f"{phys_cores} physical ({p_cores}P + {e_cores}E), {log_cores} logical threads" if p_cores is not None else f"{phys_cores} physical, {log_cores} logical cores"

    power_info = env_data.get("power", {})
    freq_info = env_data.get("cpu_freq", {})

    # Generate REPORT.md
    md = [
        "# Tsxtract Performance Benchmark Report",
        "",
        f"**Date:** {results_dir.name}  ",
        f"**Machine:** {cpu_info.get('model', 'Unknown')}  ",
        f"**Topology:** {topo_str}  ",
        f"**Power Plan:** `{power_info.get('scheme', 'Unknown')}` (AC Plugged: {power_info.get('ac_plugged', True)})  ",
        f"**CPU Freq:** {freq_info.get('current_mhz', 'N/A')} MHz (Max: {freq_info.get('max_mhz', 'N/A')} MHz)  ",
        f"**OS:** {env_data.get('os', {}).get('platform_str', 'Unknown')}  ",
        f"**Tsxtract Commit:** `{env_data.get('git', {}).get('commit', 'unknown')[:8]}`  ",
        "",
    ]

    if warnings:
        md.append("> [!WARNING]")
        for w in warnings:
            md.append(f"> - {w}")
        md.append("")

    md.extend([
        "---",
        "",
        "## Summary Results Table",
        "",
        "| Library | Profile / Set | Series × Len | Median (ms) | Best-of (ms) | Peak RSS (MB) | Guarded | Status |",
        "|---|---|---|---|---|---|---|---|",
    ])

    cats = []
    vals = []
    collision_records = []

    # Filter out tsxtract_jax from win/loss and main charts (Amendment A8)
    main_records = []
    for r in records:
        if r.get("lib") == "tsxtract_jax":
            collision_records.append(r)
        else:
            main_records.append(r)

    for r in main_records:
        lib = r.get("lib", "unknown")
        fset = r.get("feature_set", "default")
        shape = f"{r.get('n_series', 0)} × {r.get('length', 0)}"
        status = r.get("status", "unknown")
        stats = r.get("stats", {})
        med = stats.get("median", float("nan"))
        med_ms = f"{med * 1e3:.2f}" if med == med else "N/A"
        mn = stats.get("min", float("nan"))
        mn_ms = f"{mn * 1e3:.2f}" if mn == mn else "N/A"
        rss = f"{r.get('peak_rss_mb', 0.0):.2f}"
        guarded = "Yes" if r.get("guarded", True) else "No"

        md.append(f"| {lib} | {fset} | {shape} | {med_ms} | {mn_ms} | {rss} | {guarded} | {status} |")

        if status == "ok" and med == med:
            cats.append(f"{lib} ({fset})")
            vals.append(med * 1e3)

    # Multi-threading parallel efficiency section
    multithread_records = [r for r in main_records if r.get("threads", 1) > 1 and r.get("status") == "ok"]
    if multithread_records:
        md.extend([
            "",
            "## Parallel Efficiency Analysis",
            "",
            "Parallel efficiency evaluated against both physical cores and logical hyper-threads:",
            "",
            "| Library | Case | Threads | Median (ms) | Speedup vs 1T | η (Logical) | η (Physical) |",
            "|---|---|---|---|---|---|---|",
        ])
        # Find 1T baseline for each lib + case
        single_thread_map = {}
        for r in main_records:
            if r.get("threads", 1) == 1 and r.get("status") == "ok":
                key = (r.get("lib"), r.get("case_id"), r.get("feature_set"))
                single_thread_map[key] = r.get("stats", {}).get("median", 0.0)

        for r in multithread_records:
            key = (r.get("lib"), r.get("case_id"), r.get("feature_set"))
            t1 = single_thread_map.get(key)
            tk = r.get("stats", {}).get("median", 0.0)
            threads = r.get("threads", 1)
            if t1 and tk and tk > 0:
                speedup = t1 / tk
                eff_log = (speedup / threads) * 100
                eff_phys = (speedup / min(threads, phys_cores)) * 100
                md.append(f"| {r.get('lib')} | {r.get('case_id')} | {threads} | {tk*1e3:.2f} | {speedup:.2f}x | {eff_log:.1f}% | {eff_phys:.1f}% |")

    if collision_records:
        md.extend([
            "",
            "## PyPI Name-Collision Diagnostic (tsxtract JAX)",
            "",
            "The following records correspond to the unrelated JAX-based `tsxtract` package on PyPI. They are tracked for namespace awareness and excluded from win/loss counts and loss ledgers:",
            "",
            "| Library | Status | Diagnostic Message |",
            "|---|---|---|",
        ])
        for cr in collision_records:
            md.append(f"| tsxtract_jax | {cr.get('status')} | {cr.get('error_msg', 'N/A')[:100]} |")

    md.extend([
        "",
        "---",
        "",
        "## Visual Comparison",
        "",
        "![Smoke Benchmark Runtime](charts/smoke_runtime.svg)",
        "",
        "---",
        "*Report generated automatically by Tsxtract Benchmark Harness.*",
    ])

    report_md_path = REPORT_DIR / "REPORT.md"
    report_md_path.write_text("\n".join(md), encoding="utf-8")
    print(f"[Report] Generated {report_md_path}")

    # Generate results.json for website
    results_json_path = REPORT_DIR / "results.json"
    results_json_path.write_text(json.dumps({
        "environment": env_data,
        "records": records,
    }, indent=2), encoding="utf-8")
    print(f"[Report] Generated {results_json_path}")

    # Generate SVG chart
    if cats and vals:
        chart_path = CHARTS_DIR / "smoke_runtime.svg"
        generate_svg_bar_chart(
            title="Benchmark Runtime on Test Batch (Lower is Faster)",
            categories=cats,
            values=vals,
            unit="ms",
            out_path=chart_path,
        )
        print(f"[Report] Generated {chart_path}")


if __name__ == "__main__":
    generate_report()
