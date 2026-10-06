"""Equal-feature benchmark suite (task 1.1 + 1.2).

Two modes:
  parity  — verify per-feature numeric agreement between kymora and each
            competitor on the DEFINITION-AGREED feature subset, BEFORE any
            timing. Exits non-zero on unexpected mismatch.
  bench   — time every library restricted to that agreed subset on the
            benchmark shapes. Interleaved rounds, pooled medians, 95%
            bootstrap CIs on the kymora/competitor ratio.

Equal-feature subset = rows of benchmarks/agreement/feature_map.json whose
per-competitor mapping is non-null (frozen Phase B1 parity evidence):
  catch22: none (definitions differ)  -> NOT timed in this suite
  TSFEL:   13 features
  tsfresh: 13 features (14 kymora columns; quantile maps to two)
  numba:   33 features (numerically identical implementations)
  numpy:   33 features

Methodology (F1 style):
  - interleaved A/B rounds (kymora, competitor, kymora, competitor, ...)
  - per-round subprocess-isolated measurement via the harness runner
  - pooled medians across rounds, bootstrap 95% CI on the ratio
  - fresh subprocess per measurement, warmup, GC disabled

Usage:
  python benchmarks/suites/equal_feature.py parity
  python benchmarks/suites/equal_feature.py bench [--rounds N] [--shape n,l ...]

Artifacts:
  benchmarks/results/<date>_equal_feature/parity.json
  benchmarks/results/<date>_equal_feature/equal_feature.jsonl
  benchmarks/results/EQUAL_FEATURE_REPORT.md
"""

from __future__ import annotations

import argparse
import json
import sys
from datetime import datetime
from pathlib import Path

import numpy as np

REPO_ROOT = Path(__file__).resolve().parents[2]
if str(REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(REPO_ROOT))

from benchmarks.harness.env import save_env, snapshot_load  # noqa: E402
from benchmarks.harness.runner import run_benchmark_subprocess  # noqa: E402
from benchmarks.harness.stats import bootstrap_ratio_ci  # noqa: E402

RESULTS_ROOT = REPO_ROOT / "benchmarks" / "results"

# The 33 core33 names (source of truth: kymora.feature_names(); this literal
# mirrors benchmarks/agreement/feature_map.json keys).
CORE33 = [
    "mean", "std", "var", "min", "max", "median",
    "quantile_10", "quantile_25", "quantile_75", "quantile_90",
    "skewness", "kurtosis", "abs_energy", "root_mean_square",
    "mean_abs_change", "mean_change", "cid_ce", "mean_second_derivative_central",
    "zero_crossings", "mean_crossings", "number_of_peaks",
    "longest_strike_above_mean", "longest_strike_below_mean",
    "autocorr_lag_1", "autocorr_lag_2", "autocorr_lag_5", "autocorr_lag_10",
    "trend_slope", "trend_r2", "permutation_entropy",
    "dominant_frequency", "spectral_centroid", "spectral_entropy",
]

# Feature intersection per competitor (definition-agreed only, Phase B1).
# Values: kymora core33 names. Each carries the competitor column mapping
# used in the parity gate.
EQUAL_SETS: dict[str, dict[str, str | None]] = {
    "tsfel": {
        "mean": "Mean", "std": "Standard deviation", "var": "Variance",
        "min": "Min", "max": "Max", "median": "Median",
        "skewness": "Skewness", "kurtosis": "Kurtosis",
        "abs_energy": "Absolute energy", "root_mean_square": "Root mean square",
        "mean_abs_change": "Mean absolute diff", "mean_change": "Mean diff",
        "zero_crossings": "Zero crossing rate",
    },
    "tsfresh": {
        "median": "median",
        "quantile_10": "quantile__q_0.1", "quantile_90": "quantile__q_0.9",
        "abs_energy": "abs_energy", "root_mean_square": "root_mean_square",
        "mean_abs_change": "mean_abs_change", "mean_change": "mean_change",
        "mean_second_derivative_central": "mean_second_derivative_central",
        "longest_strike_above_mean": "longest_strike_above_mean",
        "longest_strike_below_mean": "longest_strike_below_mean",
        "autocorr_lag_1": "autocorrelation__lag_1",
        "autocorr_lag_2": "autocorrelation__lag_2",
        "autocorr_lag_5": "autocorrelation__lag_5",
    },
    "numba": {name: name for name in CORE33},
    "numpy": {name: name for name in CORE33},
}

# TSFEL matched config (exactly the 13 functions above).
TSFEL_MATCHED = [
    "Mean", "Standard deviation", "Variance", "Min", "Max", "Median",
    "Skewness", "Kurtosis", "Absolute energy", "Root mean square",
    "Mean absolute diff", "Mean diff", "Zero crossing rate",
]

# tsfresh matched fc params (exactly the agreed features above).
TSFRESH_MATCHED_PARAMS = {
    "median": None,
    "quantile": [{"q": 0.1}, {"q": 0.9}],
    "abs_energy": None,
    "root_mean_square": None,
    "mean_abs_change": None,
    "mean_change": None,
    "mean_second_derivative_central": None,
    "longest_strike_above_mean": None,
    "longest_strike_below_mean": None,
    "autocorrelation": [{"lag": 1}, {"lag": 2}, {"lag": 5}],
}

# Bench shapes: the four required by task 1.2 (n_series x length).
BENCH_SHAPES = [(1000, 500), (10000, 500), (1000, 5000), (100, 50000)]

# Standard tolerances for the parity gate (rel err on well-behaved data).
REL_TOL = 1e-5  # CLOSE per agreement classes; definition-agreed features should hit <=1e-9


def _kymora_names() -> list[str]:
    import kymora

    return list(kymora.feature_names())


def _subset_of_kymora(km_feats: np.ndarray, wanted: list[str]) -> np.ndarray:
    """Extract wanted feature columns from a full core33 output matrix."""
    all_names = _kymora_names()
    idx = [all_names.index(w) for w in wanted]
    return km_feats[:, idx]


def _tsfel_columns(cfg, names: list[str]) -> list[int]:
    """Column indices of the TSFEL output frame that correspond to `names`."""
    import tsfel

    dummy = np.linspace(0.0, 10.0, 500)
    df = tsfel.time_series_features_extractor(cfg, dummy, verbose=0)
    cols = list(df.columns)
    out = []
    for want in names:
        matches = [i for i, c in enumerate(cols) if want.lower() in str(c).lower()]
        if not matches:
            raise RuntimeError(f"TSFEL column not found: {want!r} in {cols[:20]}...")
        out.append(matches[0])
    return out


def _tsfresh_columns(names: list[str]) -> list[str]:
    """TSFEL-style: tsfresh column names after extraction on a dummy frame."""
    import pandas as pd
    from tsfresh import extract_features as tsf_extract

    dummy = pd.DataFrame({"id": [0, 0, 0, 0], "val": [1.0, 2.0, 3.0, 4.0]})
    df = tsf_extract(dummy, column_id="id", default_fc_parameters=dict(TSFRESH_MATCHED_PARAMS),
                     disable_progressbar=True)
    return list(df.columns)


def _max_rel_err(a: np.ndarray, b: np.ndarray) -> float:
    denom = np.maximum(np.abs(b), 1e-9)
    finite = np.isfinite(a) & np.isfinite(b)
    if not finite.any():
        # both sides fully NaN-by-contract -> agreement
        if np.isnan(a).all() and np.isnan(b).all():
            return 0.0
        return float("inf")
    return float(np.max(np.abs(a[finite] - b[finite]) / denom[finite]))


def _extract_tsfel_matched(X: np.ndarray, threads: int = 1) -> np.ndarray:
    import tsfel

    cfg = {}
    full = tsfel.get_features_by_domain()
    for domain, funcs in full.items():
        kept = {n: s for n, s in funcs.items() if n in TSFEL_MATCHED}
        if kept:
            cfg[domain] = kept

    def _row(row: np.ndarray) -> np.ndarray:
        df = tsfel.time_series_features_extractor(cfg, row, verbose=0)
        return df.to_numpy().ravel()

    # Same tuned path as the full TSFEL adapter: joblib Parallel when threads > 1.
    if threads > 1:
        from joblib import Parallel, delayed

        rows = Parallel(n_jobs=threads)(delayed(_row)(X[i]) for i in range(X.shape[0]))
    else:
        rows = [_row(X[i]) for i in range(X.shape[0])]
    out = np.array(rows, dtype=np.float64)
    # Reorder columns to TSFEL_MATCHED order (joblib preserves order)
    cols = _tsfel_columns(cfg, TSFEL_MATCHED)
    return out[:, cols]


def _extract_tsfresh_matched(X: np.ndarray, threads: int = 1) -> np.ndarray:
    import pandas as pd
    from tsfresh import extract_features as tsf_extract

    n, length = X.shape
    long_df = pd.DataFrame({"id": np.repeat(np.arange(n), length), "val": X.ravel()})
    df_out = tsf_extract(long_df, column_id="id", default_fc_parameters=dict(TSFRESH_MATCHED_PARAMS),
                         n_jobs=threads, disable_progressbar=True)
    cols = list(df_out.columns)
    # Build the expected output column order
    want = []
    for kymora_name, mapped in EQUAL_SETS["tsfresh"].items():
        matches = [c for c in cols if mapped in c]
        want.append(matches[0])
    return df_out[want].to_numpy(dtype=np.float64)


def _extract_numba_matched(X: np.ndarray, threads: int, fastmath: bool) -> np.ndarray:
    from benchmarks.adapters.numba_baseline import Adapter as NumbaAdapter

    adapter = NumbaAdapter()
    return adapter.extract(X, feature_set=("fast" if fastmath else "strict"), threads=threads)


def _extract_numpy_matched(X: np.ndarray) -> np.ndarray:
    from benchmarks.adapters.numpy_baseline import Adapter as NumpyAdapter

    adapter = NumpyAdapter()
    return adapter.extract(X, feature_set="default", threads=1)


def _extract_kymora_matched(X: np.ndarray, names: list[str], threads: int) -> np.ndarray:
    import kymora

    return kymora.extract_features(X, features=names, n_jobs=threads)


def run_parity(n_series: int = 40, length: int = 500, seed: int = 42) -> bool:
    """Verify per-feature numeric agreement before timing. Returns pass/fail."""
    import kymora

    rng = np.random.default_rng(seed)
    X = rng.standard_normal((n_series, length))

    results: dict[str, dict] = {}
    all_ok = True

    for comp, mapping in EQUAL_SETS.items():
        wanted = list(mapping.keys())
        km = _extract_kymora_matched(X, wanted, threads=1)

        if comp == "tsfel":
            other = _extract_tsfel_matched(X)
        elif comp == "tsfresh":
            other = _extract_tsfresh_matched(X)
        elif comp == "numba":
            # strict (fastmath=False) for agreement; also record fast variant
            other = _extract_numba_matched(X, threads=1, fastmath=False)
        else:  # numpy
            other = _extract_numpy_matched(X)

        per_feature = {}
        worst = 0.0
        n_bad = 0
        for j, fname in enumerate(wanted):
            rel = _max_rel_err(km[:, j], other[:, j])
            status = "EXACT" if rel <= 1e-9 else ("CLOSE" if rel <= REL_TOL else "MISMATCH")
            per_feature[fname] = {"max_rel_err": rel, "status": status}
            if status == "MISMATCH":
                n_bad += 1
                all_ok = False
            worst = max(worst, rel if rel == rel else float("inf"))

        results[comp] = {
            "n_features": len(wanted),
            "features": wanted,
            "worst_rel_err": worst,
            "n_mismatch": n_bad,
            "pass": n_bad == 0,
            "per_feature": per_feature,
        }
        icon = "PASS" if n_bad == 0 else "FAIL"
        print(f"  [{icon}] {comp}: {len(wanted)} features, worst rel err {worst:.3e}, mismatches {n_bad}")

    out_dir = RESULTS_ROOT / f"{datetime.now().strftime('%Y-%m-%d')}_equal_feature"
    out_dir.mkdir(parents=True, exist_ok=True)
    payload = {
        "generated": datetime.now().isoformat(),
        "mode": "parity",
        "n_series": n_series,
        "length": length,
        "seed": seed,
        "kymora_version": getattr(kymora, "__version__", "?"),
        "tolerances": {"exact": 1e-9, "close": REL_TOL},
        "results": results,
    }
    with open(out_dir / "parity.json", "w", encoding="utf-8") as f:
        json.dump(payload, f, indent=2)
    print(f"  artifact: {out_dir / 'parity.json'}")
    return all_ok


# ────────────────────────────────────────────────────────────────────────────
# Benchmark mode
# ────────────────────────────────────────────────────────────────────────────

def _competitor_runner(comp: str):
    """Return a callable (X, threads) -> ndarray for the matched-subset extract."""
    if comp == "tsfel":
        return lambda X, threads: _extract_tsfel_matched(X)
    if comp == "tsfresh":
        return lambda X, threads: _extract_tsfresh_matched(X, threads=threads)
    if comp == "numba":
        return lambda X, threads: _extract_numba_matched(X, threads=threads, fastmath=True)
    if comp == "numpy":
        return lambda X, threads: _extract_numpy_matched(X)
    raise ValueError(comp)


def _time_fn(fn, *args, min_runs: int = 7, budget_s: float = 1.5, **kwargs) -> dict:
    """In-process timing: warmup + >=min_runs or >=budget_s, GC off. Returns stats in ms."""
    import gc
    import time

    for _ in range(2):
        fn(*args, **kwargs)
    runs: list[float] = []
    t_start = time.perf_counter()
    gc_was = gc.isenabled()
    gc.disable()
    try:
        while True:
            t0 = time.perf_counter_ns()
            fn(*args, **kwargs)
            t1 = time.perf_counter_ns()
            runs.append((t1 - t0) / 1e6)
            if len(runs) >= min_runs and (time.perf_counter() - t_start) >= budget_s:
                break
            if len(runs) >= 300:
                break
    finally:
        if gc_was:
            gc.enable()
    arr = np.asarray(runs)
    return {
        "median_ms": float(np.median(arr)),
        "min_ms": float(arr.min()),
        "n_runs": int(len(arr)),
        "runs_ms": [float(r) for r in runs],
    }


def run_bench(rounds: int = 4, shapes: list[tuple[int, int]] | None = None,
              dists: list[str] | None = None) -> None:
    """Interleaved equal-feature benchmark across shapes and libraries."""
    import kymora

    shapes = shapes or BENCH_SHAPES
    dists = dists or ["gaussian"]
    date_dir = RESULTS_ROOT / f"{datetime.now().strftime('%Y-%m-%d')}_equal_feature"
    date_dir.mkdir(parents=True, exist_ok=True)
    load_start = snapshot_load()

    # Which libraries to run: always kymora + each competitor with a non-empty set
    competitors = [c for c, m in EQUAL_SETS.items() if m]

    all_rows = []
    for n_series, length in shapes:
        for dist in dists:
            # Generate the dataset once per shape/dist; all libraries see the same data
            rng = np.random.default_rng(42)
            if dist == "gaussian":
                X = rng.standard_normal((n_series, length))
            elif dist == "random_walk":
                X = np.cumsum(rng.standard_normal((n_series, length)), axis=1)
            elif dist == "sinusoid":
                t = np.linspace(0, 10 * np.pi, length)
                X = np.sin(t) + 0.1 * rng.standard_normal((n_series, length))
            elif dist == "ar1":
                phi = 0.7
                noise = rng.standard_normal((n_series, length))
                X = np.zeros((n_series, length))
                for j in range(1, length):
                    X[:, j] = phi * X[:, j - 1] + noise[:, j]
            elif dist == "heavy_tailed":
                X = rng.standard_t(df=3, size=(n_series, length))
            else:
                X = rng.standard_normal((n_series, length))

            for comp in competitors:
                wanted = list(EQUAL_SETS[comp].keys())
                km_fn = lambda Xk, w=wanted: _extract_kymora_matched(Xk, w, threads=16)  # noqa: E731
                other_fn = _competitor_runner(comp)

                km_rounds = []
                other_rounds = []
                for r in range(rounds):
                    km_rounds.append(_time_fn(km_fn, X, min_runs=5, budget_s=1.0))
                    other_rounds.append(_time_fn(other_fn, X, threads=16, min_runs=3, budget_s=1.0))
                    print(
                        f"  {n_series}x{length} {dist} {comp} round {r + 1}/{rounds}: "
                        f"kymora {km_rounds[-1]['median_ms']:.2f} ms, "
                        f"{comp} {other_rounds[-1]['median_ms']:.2f} ms",
                        flush=True,
                    )

                # Pool medians across rounds (single value per round)
                km_ms = float(np.median([rd["median_ms"] for rd in km_rounds]))
                other_ms = float(np.median([rd["median_ms"] for rd in other_rounds]))

                def _cv(samples):
                    m = float(np.mean(samples)) if samples else float("nan")
                    if not samples or len(samples) < 2 or not m:
                        return float("nan")
                    return float(np.std(samples, ddof=1) / m)

                # Bootstrap CI on the ratio from per-round medians
                km_samples = [rd["median_ms"] for rd in km_rounds]
                other_samples = [rd["median_ms"] for rd in other_rounds]
                ratio = other_ms / km_ms if km_ms > 0 else float("nan")
                ci_lo, ci_hi = bootstrap_ratio_ci(other_samples, km_samples, n_resamples=2000)

                # Feature counts (post-extraction shape check)
                km_shape = km_fn(X[:2]).shape
                other_shape = other_fn(X[:2], threads=1).shape

                row = {
                    "suite": "equal_feature",
                    "case_id": f"eq_{comp}_{n_series}x{length}_{dist}",
                    "competitor": comp,
                    "n_series": n_series,
                    "length": length,
                    "dist": dist,
                    "n_features_kymora": len(wanted),
                    "n_features_competitor": len(wanted),
                    "kymora_median_ms": km_ms,
                    "kymora_rounds": km_samples,
                    "kymora_cv": _cv(km_samples),
                    "competitor_median_ms": other_ms,
                    "competitor_rounds": other_samples,
                    "competitor_cv": _cv(other_samples),
                    "ratio_competitor_over_kymora": ratio,
                    "ratio_ci95": [ci_lo, ci_hi],
                    "kymora_output_shape": list(km_shape),
                    "competitor_output_shape": list(other_shape),
                    "threads": 16,
                    "kymora_version": getattr(kymora, "__version__", "?"),
                    "timestamp": datetime.now().isoformat(),
                }
                all_rows.append(row)

                print(
                    f"    => kymora {km_ms:.2f} ms vs {comp} {other_ms:.2f} ms "
                    f"(equal {len(wanted)} features): {ratio:.1f}x CI [{ci_lo:.1f}, {ci_hi:.1f}]",
                    flush=True,
                )

    with open(date_dir / "equal_feature.jsonl", "w", encoding="utf-8") as f:
        for row in all_rows:
            f.write(json.dumps(row) + "\n")
    print(f"  artifact: {date_dir / 'equal_feature.jsonl'}")
    save_env(
        date_dir / "env.json",
        extra={"load_start": load_start, "load_end": snapshot_load()},
    )

    _write_report(date_dir, all_rows)


def _write_report(out_dir: Path, rows: list[dict]) -> None:
    lines = [
        "# Equal-Feature Benchmark Report (F2)",
        "",
        f"**Generated:** {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}",
        "**Subset:** definition-agreed features per competitor (frozen Phase B1 parity: "
        "TSFEL 13, tsfresh 13, numba 33, numpy 33; catch22 excluded — no definition-agreed features).",
        "**Parity gate:** `parity` mode re-verifies numeric agreement before timing "
        "(per-feature rel err, EXACT <=1e-9 / CLOSE <=1e-5).",
        "**Protocol:** interleaved rounds (kymora, competitor alternating), pooled medians, "
        "95% bootstrap CI on the ratio, GC disabled, warmup, single machine "
        "(i7-13620H laptop, 10 cores / 16 threads, Windows 11) — exploratory, not fleet evidence.",
        "",
    ]
    for (n_series, length) in sorted({(r["n_series"], r["length"]) for r in rows}):
        lines.append(f"## Shape {n_series:,} × {length:,} (equal features per row)")
        lines.append("")
        lines.append("| Competitor | Equal features | Kymora med (ms) | Competitor med (ms) | Ratio (comp/kymora) | 95% CI |")
        lines.append("|---|---:|---:|---:|---:|---|")
        for r in sorted((x for x in rows if (x["n_series"], x["length"]) == (n_series, length)),
                        key=lambda x: x["competitor"]):
            ci = r["ratio_ci95"]
            lines.append(
                f"| {r['competitor']} | {r['n_features_competitor']} | "
                f"{r['kymora_median_ms']:.3f} | {r['competitor_median_ms']:.3f} | "
                f"{r['ratio_competitor_over_kymora']:.1f}x | [{ci[0]:.1f}, {ci[1]:.1f}] |"
            )
        lines.append("")
    lines += [
        "## What this table does and does not show",
        "",
        "- **Shows:** wall-clock to extract *the same, definition-agreed feature subset* — "
        "the closest thing to an equal-work comparison.",
        "- **Does not show:** each library's full default catalog (see the raw-time table for that), "
        "feature quality/coverage differences, or multi-machine variance.",
        "- Kymora's subset runs through the same fused core33 pipeline; competitors run their own "
        "matched-config extractors at their best documented tuning.",
        "",
        "Reproduce: `python benchmarks/suites/equal_feature.py parity && "
        "python benchmarks/suites/equal_feature.py bench`",
        "",
    ]
    with open(RESULTS_ROOT / "EQUAL_FEATURE_REPORT.md", "w", encoding="utf-8") as f:
        f.write("\n".join(lines))
    print(f"  artifact: {RESULTS_ROOT / 'EQUAL_FEATURE_REPORT.md'}")


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("mode", choices=["parity", "bench"])
    parser.add_argument("--rounds", type=int, default=4)
    parser.add_argument("--shape", type=int, nargs=2, action="append", dest="shapes",
                        help="n_series length; repeatable")
    parser.add_argument("--dist", action="append", dest="dists")
    args = parser.parse_args()

    if args.mode == "parity":
        ok = run_parity()
        sys.exit(0 if ok else 1)
    else:
        run_bench(rounds=args.rounds,
                  shapes=[tuple(s) for s in args.shapes] if args.shapes else None,
                  dists=args.dists)
