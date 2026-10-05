"""Phase B3 (step 2): Competitor report — the three honest-claims views.

Reads the raw JSONL artifacts and produces benchmarks/results/COMPETITOR_REPORT.md
with, for every row (docs/internal/arch.md §11.6):
  1. raw runtime (median ms, plus best-of)
  2. µs per series-feature
  3. matched-feature runtime (only definition-agreed features; N/A where the
     frozen matched set is empty, e.g. catch22/antropy/tsflex/sktime)

Timeout / error cases are listed explicitly — the matrix is never silently
incomplete (docs/internal/arch.md §11.1).
"""

from __future__ import annotations

import json
import math
import sys
from datetime import datetime
from pathlib import Path
from typing import Any

RESULTS_DIR = Path(__file__).resolve().parents[1] / "results"
BASELINE_JSONL = RESULTS_DIR / "throughput.jsonl"
COMPETITOR_JSONL = RESULTS_DIR / "throughput_competitors.jsonl"
OUT_MD = RESULTS_DIR / "COMPETITOR_REPORT.md"

SHAPES = [(1, 100), (1, 10_000), (10, 500), (100, 100), (100, 500), (100, 5_000), (1_000, 100), (1_000, 500), (10_000, 500)]

# display order + label
VARIANT_LABELS = {
    "kymora": "Kymora core33",
    "catch22": "catch22 (22)",
    "tsfel": "TSFEL (156, README cfg)",
    "tsfel_matched": "TSFEL matched (13)",
    "tsxtract_matched_tsfel": "Kymora matched-tsfel (13)",
    "tsfresh_e2e": "tsfresh (777, e2e)",
    "tsfresh_extract_only": "tsfresh (777, extract-only)",
    "tsfresh_matched": "tsfresh matched (13)",
    "tsxtract_matched_tsfresh": "Kymora matched-tsfresh (13)",
    "antropy": "antropy (8)",
    "tsflex": "tsflex (7 stats)",
    "sktime_catch22": "sktime Catch22 (22)",
}


def load_rows() -> dict[tuple, dict]:
    """key = (variant, n_series, length, dist) -> row dict (latest wins)."""
    out: dict[tuple, dict] = {}
    for path in (BASELINE_JSONL, COMPETITOR_JSONL):
        if not path.exists():
            continue
        for line in path.read_text(encoding="utf-8").splitlines():
            if not line.strip():
                continue
            r = json.loads(line)
            if r.get("suite") == "reproduce_readme":
                continue
            lib = r.get("lib")
            fset = r.get("feature_set", "default")
            v = r.get("extra", {}).get("variant")
            if lib == "kymora" and fset == "core33":
                variant = "kymora"
            elif lib == "kymora":
                variant = f"tsxtract_{fset}"
            elif lib == "numba_baseline":
                variant = "numba_baseline_fast"
            elif lib == "numpy_baseline":
                variant = "numpy_baseline"
            elif lib == "tsfresh":
                if v == "extract_only":
                    variant = "tsfresh_extract_only"
                elif fset == "matched":
                    variant = "tsfresh_matched"
                else:
                    variant = "tsfresh_e2e"
            elif lib == "tsfel":
                variant = "tsfel_matched" if fset == "matched" else "tsfel"
            elif lib == "sktime":
                variant = "sktime_catch22"
            else:
                variant = lib
            key = (variant, r.get("n_series"), r.get("length"), r.get("dist"))
            out[key] = r
    return out


def fmt(v: float, nd: int = 2) -> str:
    if v is None or (isinstance(v, float) and (math.isnan(v) or math.isinf(v))):
        return "—"
    return f"{v:,.{nd}f}"


def main() -> int:
    rows = load_rows()

    def med_ms(r: dict | None) -> float:
        if r is None or r.get("status") != "ok":
            return math.nan
        s = r.get("stats", {})
        m = s.get("median")
        if m is None:
            m = s.get("median_ms")
        if m is None:
            return math.nan
        # runner stores seconds; suite stores ms
        if "median_ms" in s:
            return float(m)
        return float(m) * 1e3

    def best_ms(r: dict | None) -> float:
        if r is None or r.get("status") != "ok":
            return math.nan
        s = r.get("stats", {})
        m = s.get("min", s.get("min_ms"))
        if m is None:
            return math.nan
        return float(m) * 1e3 if "min_ms" not in s else float(m)

    def n_features(r: dict | None) -> int | None:
        if r is None:
            return None
        if r.get("n_features"):
            return int(r["n_features"])
        shape = r.get("extra", {}).get("output_shape")
        if shape and len(shape) == 2:
            return int(shape[1])
        return None

    lines: list[str] = []
    lines.append("# Phase B3 Step 2: Competitor Throughput Matrix — Three Views\n")
    lines.append(f"**Generated:** {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}  ")
    lines.append("**Hardware:** 13th Gen Intel i7-13620H (10C/16T hybrid), Windows 11, 16 threads, f64 C-contiguous  ")
    lines.append("**Views per row (docs/internal/arch.md §11.6):** raw median ms · µs/series-feature · matched-feature (definition-agreed subset only)  ")
    lines.append("**Protocol:** fresh subprocess per case, warmup, GC disabled; per-case wall-clock timeout recorded as an explicit `timeout` row; tsfresh/sktime slow families use min_runs=1 (single full run dominates); see `benchmarks/suites/throughput_competitors.py`.\n")

    dists = ["gaussian", "random_walk", "ar1", "heavy_tailed", "sinusoid"]
    variants = ["kymora", "catch22", "tsfel", "tsfresh_e2e", "tsfresh_extract_only",
                "antropy", "tsflex", "sktime_catch22"]

    # ── View 1+2 table per shape (gaussian + all dists aggregated min) ─────
    for n, length in SHAPES:
        lines.append(f"## Shape {n:,} × {length:,}\n")
        lines.append("| Library | n_feat | raw med (ms) | raw best (ms) | µs/series-feat | matched med (ms) | matched µs/sf | ratio raw | ratio matched |")
        lines.append("|---|---|---|---|---|---|---|---|---|")

        def get(variant: str, dist: str) -> dict | None:
            return rows.get((variant, n, length, dist))

        km_row = get("kymora", "gaussian")
        km_med = med_ms(km_row)
        km_nf = n_features(km_row) or 33

        for variant in variants:
            agg_med = [med_ms(get(variant, d)) for d in dists]
            agg_med_ok = [v for v in agg_med if v == v]
            if not agg_med_ok:
                # not run on any dist -> check status rows for explicit note
                statuses = {d: (get(variant, d) or {}).get("status", "missing") for d in dists}
                lines.append(f"| {VARIANT_LABELS.get(variant, variant)} | — | — | — | — | — | — | — | — | "
                             f"not run: {set(statuses.values())} |")
                continue
            med = min(agg_med_ok)  # best dist (documented)
            nf = n_features(get(variant, "gaussian")) or 0
            us_sf = med * 1000 / max(1, n * nf) if med == med else math.nan
            raw_ratio = med / km_med if med == med and km_med == km_med else math.nan
            if variant == "kymora":
                raw_ratio = 1.0

            matched_col = "—"
            matched_ratio = "—"
            matched_us = "—"
            pair = {
                "tsfel": ("tsfel_matched", "tsxtract_matched_tsfel", 13),
                "tsfresh_e2e": ("tsfresh_matched", "tsxtract_matched_tsfresh", 13),
                "tsfresh_extract_only": ("tsfresh_matched", "tsxtract_matched_tsfresh", 13),
            }.get(variant)
            if pair:
                mvar, tvar, mcount = pair
                m_med = min([v for v in (med_ms(get(mvar, d)) for d in dists) if v == v], default=math.nan)
                t_med = min([v for v in (med_ms(get(tvar, d)) for d in dists) if v == v], default=math.nan)
                if m_med == m_med:
                    matched_col = fmt(m_med)
                    matched_us = fmt(m_med * 1000 / (n * mcount), 3)
                    if t_med == t_med and t_med > 0:
                        matched_ratio = fmt(m_med / t_med) + "×"
            lines.append(
                f"| {VARIANT_LABELS.get(variant, variant)} | {nf} | {fmt(med)} | {fmt(best_ms(get(variant, 'gaussian')))} "
                f"| {fmt(us_sf, 3)} | {matched_col} | {matched_us} | {fmt(raw_ratio, 1)}× | {matched_ratio} |")
        lines.append("")

    # ── Per-dist detail for the headline shapes ────────────────────────────
    for n, length in ((1_000, 500), (10_000, 500)):
        lines.append(f"## Per-distribution detail — {n:,} × {length:,}\n")
        lines.append("| Library | " + " | ".join(dists) + " |")
        lines.append("|---" * (len(dists) + 1) + "|")
        for variant in variants:
            cells = []
            for d in dists:
                r = rows.get((variant, n, length, d))
                m = med_ms(r)
                if m == m:
                    cells.append(f"{m:,.1f}")
                elif r is not None:
                    cells.append(f"**{r.get('status', '?')}**")
                else:
                    cells.append("missing")
            lines.append(f"| {VARIANT_LABELS.get(variant, variant)} | " + " | ".join(cells) + " |")
        lines.append("")

    # ── Explicit timeout / error rows ──────────────────────────────────────
    lines.append("## Explicit timeout / error rows (no silent skips)\n")
    lines.append("| Library | Case | dist | Status | Detail |")
    lines.append("|---|---|---|---|---|")
    any_bad = False
    for (variant, n, length, d), r in sorted(rows.items()):
        if variant not in variants:
            continue
        if r.get("status") not in ("ok", None):
            any_bad = True
            detail = (r.get("error_msg") or "")[:110].replace("|", "/")
            lines.append(f"| {VARIANT_LABELS.get(variant, variant)} | {n:,}×{length:,} | {d} | {r.get('status')} | {detail} |")
    if not any_bad:
        lines.append("| (none) | | | | |")
    lines.append("")

    # ── Methodology notes ──────────────────────────────────────────────────
    lines.append("""## Methodology notes (equal tuning, documented)

- **catch22**: pycatch22 serial per-series loop; `multiprocessing.Pool(16)` variant is what runs at threads=16 (adapter default fast config).
- **TSFEL**: `get_features_by_domain()` (README 156-feature config), joblib `Parallel(n_jobs=16)`.
- **tsfresh**: `EfficientFCParameters` (README 777-feature config), `n_jobs=16`. End-to-end includes long-format DataFrame construction; extract-only builds the DataFrame outside the timed region (`variant=extract_only`).
- **Matched-feature runs**: only the 13 definition-agreed features per competitor (frozen in `benchmarks/agreement/feature_map.json`); Kymora matched runs use the same 13 via the `features=` subset API.
- **antropy / tsflex / sktime**: included where installed; matched set vs core33 is empty (B1), so matched view is N/A.
- Per-case subprocess import overhead (numba/pandas/tsfresh) is *included* in competitor wall times — a conservative choice against Kymora.
- Dist aggregation in the per-shape tables reports the **best** dist median per library (worst-case vs Kymora); per-dist detail tables above give all five.
""")
    OUT_MD.write_text("\n".join(lines), encoding="utf-8")
    print(f"Wrote {OUT_MD} ({len(lines)} lines)")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
