"""Batch-throughput benchmark: kymora vs tsfresh vs catch22 vs TSFEL.

What this measures: wall-clock time to turn a batch of `n_series` equal-length
series into one feature row per series, which is the shape of work a feature
pipeline actually does. It is deliberately *not* a per-feature microbenchmark --
catch22 and TSFEL are competitive there, and the kymora claim is throughput
across a whole batch (rayon parallelises over the series dimension).

Every library gets the same input matrix and is timed end to end, including the
input reshaping it requires (tsfresh needs a long DataFrame, catch22 and TSFEL
need per-series Python loops). That reshaping is part of the cost a user pays,
so excluding it would flatter the Python libraries in a way real pipelines never
see.

Install the comparison set with:  pip install -e ".[bench]"
Missing libraries are reported as skipped rather than failing the run.

Usage:
    python benchmarks/bench_libraries.py --n-series 1000 --n-steps 500 \
        --json benchmarks/results/latest.json --markdown benchmarks/results/latest.md
"""

from __future__ import annotations

import argparse
import json
import os
import platform
import sys
import time
from dataclasses import asdict, dataclass, field
from typing import Callable

import numpy as np


@dataclass
class Result:
    library: str
    n_features: int | None
    seconds: float | None  # median seconds
    iqr_seconds: float | None = None
    mean_seconds: float | None = None
    std_seconds: float | None = None
    min_seconds: float | None = None
    max_seconds: float | None = None
    skipped: str | None = None
    notes: str = ""
    runs: int = 1
    raw_times: list[float] = field(default_factory=list)

    @property
    def per_feature_ms(self) -> float | None:
        if self.seconds is None or not self.n_features:
            return None
        return self.seconds / self.n_features * 1e3

    @property
    def per_feature_iqr_ms(self) -> float | None:
        if self.iqr_seconds is None or not self.n_features:
            return None
        return self.iqr_seconds / self.n_features * 1e3


@dataclass
class Report:
    n_series: int
    n_steps: int
    platform: str
    python: str
    cpu_count: int
    results: list[Result] = field(default_factory=list)


def timed(
    fn: Callable[[], object], min_total: float = 2.0, min_runs: int = 3, max_runs: int = 10
) -> tuple[object, float, float, float, float, float, float, int, list[float]]:
    """Warm-up followed by repeated runs collecting median, IQR, mean, std, min, max."""
    # Warm-up run
    out = fn()

    times: list[float] = []
    spent = 0.0
    runs = 0
    while runs < max_runs:
        t0 = time.perf_counter()
        out = fn()
        elapsed = time.perf_counter() - t0
        times.append(elapsed)
        spent += elapsed
        runs += 1
        if runs >= min_runs and spent >= min_total:
            break

    arr = np.array(times)
    median = float(np.median(arr))
    iqr = float(np.percentile(arr, 75) - np.percentile(arr, 25))
    mean = float(np.mean(arr))
    std = float(np.std(arr))
    minimum = float(np.min(arr))
    maximum = float(np.max(arr))
    return out, median, iqr, mean, std, minimum, maximum, runs, times


def bench_kymora(X: np.ndarray) -> Result:
    import kymora

    kymora.extract_features(X[: min(64, len(X))])  # warm the thread pool
    feats, med, iqr, mean, std, mn, mx, runs, times = timed(lambda: kymora.extract_features(X))
    return Result(
        library=f"kymora {kymora.__version__}",
        n_features=int(feats.shape[1]),  # type: ignore[union-attr]
        seconds=med,
        iqr_seconds=iqr,
        mean_seconds=mean,
        std_seconds=std,
        min_seconds=mn,
        max_seconds=mx,
        runs=runs,
        raw_times=times,
        notes="Rust core, rayon across series, zero-copy input",
    )


def bench_tsfresh(X: np.ndarray) -> Result:
    try:
        import pandas as pd
        from tsfresh import extract_features as tsf_extract
        from tsfresh.feature_extraction import EfficientFCParameters
    except ImportError as exc:
        return Result("tsfresh", None, None, skipped=str(exc))

    n_series, n_steps = X.shape

    def run():
        long_df = pd.DataFrame(
            {
                "id": np.repeat(np.arange(n_series), n_steps),
                "value": X.ravel(),
            }
        )
        return tsf_extract(
            long_df,
            column_id="id",
            default_fc_parameters=EfficientFCParameters(),
            disable_progressbar=True,
        )

    out, med, iqr, mean, std, mn, mx, runs, times = timed(run, min_runs=1, max_runs=2)
    return Result(
        library="tsfresh (EfficientFCParameters)",
        n_features=int(out.shape[1]),  # type: ignore[union-attr]
        seconds=med,
        iqr_seconds=iqr,
        mean_seconds=mean,
        std_seconds=std,
        min_seconds=mn,
        max_seconds=mx,
        runs=runs,
        raw_times=times,
        notes="includes the long-format reshape, its required input form",
    )


def bench_catch22(X: np.ndarray) -> Result:
    try:
        import pycatch22
    except ImportError as exc:
        return Result("catch22", None, None, skipped=str(exc))

    n_features = len(pycatch22.catch22_all(X[0].tolist())["names"])

    def run():
        return [pycatch22.catch22_all(row.tolist()) for row in X]

    _, med, iqr, mean, std, mn, mx, runs, times = timed(run, min_runs=2, max_runs=3)
    return Result(
        library="catch22 (pycatch22)",
        n_features=n_features,
        seconds=med,
        iqr_seconds=iqr,
        mean_seconds=mean,
        std_seconds=std,
        min_seconds=mn,
        max_seconds=mx,
        runs=runs,
        raw_times=times,
        notes="C core, single-threaded Python loop over series",
    )


def bench_tsfel(X: np.ndarray) -> Result:
    try:
        import pandas as pd
        import tsfel
    except ImportError as exc:
        return Result("TSFEL", None, None, skipped=str(exc))

    cfg = tsfel.get_features_by_domain()

    def run():
        frames = [
            tsfel.time_series_features_extractor(
                cfg, pd.DataFrame({"value": row}), verbose=0
            )
            for row in X
        ]
        return pd.concat(frames, ignore_index=True)

    out, med, iqr, mean, std, mn, mx, runs, times = timed(run, min_runs=1, max_runs=2)
    return Result(
        library="TSFEL (all domains)",
        n_features=int(out.shape[1]),  # type: ignore[union-attr]
        seconds=med,
        iqr_seconds=iqr,
        mean_seconds=mean,
        std_seconds=std,
        min_seconds=mn,
        max_seconds=mx,
        runs=runs,
        raw_times=times,
        notes="Python/numba, per-series extractor calls",
    )


def render_markdown(report: Report) -> str:
    ran = [r for r in report.results if r.seconds is not None]
    baseline = next((r for r in ran if r.library.startswith("kymora")), None)

    lines = [
        "# Batch-throughput benchmark",
        "",
        f"{report.n_series} series x {report.n_steps} steps, "
        f"{report.cpu_count} worker threads, {report.platform}, Python {report.python}.",
        "",
        "Time is reported as Median ± IQR across repeated runs, including input reshaping.",
        "",
        "| library | features | median time | IQR | mean time | series/s | ms/feature | vs kymora |",
        "|---|---:|---:|---:|---:|---:|---:|---:|",
    ]
    for r in report.results:
        if r.seconds is None:
            lines.append(f"| {r.library} | - | not installed | - | - | - | - | - |")
            continue
        rel = "-"
        if r is baseline:
            rel = "baseline"
        elif baseline and baseline.seconds:
            rel = f"{r.seconds / baseline.seconds:,.0f}x slower"
        total = (
            f"{r.seconds * 1e3:,.2f} ms" if r.seconds < 1.0 else f"{r.seconds:,.2f} s"
        )
        iqr_str = (
            f"{r.iqr_seconds * 1e3:,.2f} ms" if r.iqr_seconds and r.iqr_seconds < 1.0 else f"{r.iqr_seconds:,.2f} s"
        ) if r.iqr_seconds is not None else "-"
        mean_str = (
            f"{r.mean_seconds * 1e3:,.2f} ms" if r.mean_seconds and r.mean_seconds < 1.0 else f"{r.mean_seconds:,.2f} s"
        ) if r.mean_seconds is not None else "-"
        lines.append(
            f"| {r.library} | {r.n_features} | {total} | {iqr_str} | {mean_str} | "
            f"{report.n_series / r.seconds:,.0f} | "
            f"{r.per_feature_ms:,.4f} | {rel} |"
        )

    lines += [
        "",
        "Read this honestly: these libraries compute different numbers of "
        "features, so total time is not a like-for-like comparison. The "
        "kymora advantage is parallelising across series in native code; on "
        "a single short series it will not look meaningfully faster than "
        "catch22.",
        "",
    ]
    lines += [f"- **{r.library}** -- {r.notes}" for r in report.results if r.notes]
    return "\n".join(lines) + "\n"


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--n-series", type=int, default=1000)
    ap.add_argument("--n-steps", type=int, default=500)
    ap.add_argument("--seed", type=int, default=0)
    ap.add_argument("--json", type=str, default=None, help="write JSON results here")
    ap.add_argument("--markdown", type=str, default=None, help="write a table here")
    ap.add_argument(
        "--only",
        nargs="*",
        choices=["kymora", "tsfresh", "catch22", "tsfel"],
        default=None,
        help="run a subset (default: all available)",
    )
    args = ap.parse_args()

    rng = np.random.default_rng(args.seed)
    X = np.ascontiguousarray(rng.standard_normal((args.n_series, args.n_steps)))

    benchmarks = {
        "kymora": bench_kymora,
        "catch22": bench_catch22,
        "tsfel": bench_tsfel,
        "tsfresh": bench_tsfresh,
    }
    selected = args.only or list(benchmarks)

    report = Report(
        n_series=args.n_series,
        n_steps=args.n_steps,
        platform=platform.platform(),
        python=platform.python_version(),
        cpu_count=os.cpu_count() or 0,
    )

    for name in selected:
        print(f"running {name}...", flush=True)
        result = benchmarks[name](X)
        if result.skipped:
            print(f"  skipped: {result.skipped}", flush=True)
        else:
                print(
                f"  {result.n_features} features in {result.seconds * 1e3:.1f} ms"
                f" (best of {result.runs})",
                flush=True,
            )
        report.results.append(result)

    markdown = render_markdown(report)
    print()
    print(markdown)

    if args.json:
        payload = asdict(report)
        for src, dst in zip(report.results, payload["results"]):
            dst["per_feature_ms"] = src.per_feature_ms
        os.makedirs(os.path.dirname(os.path.abspath(args.json)), exist_ok=True)
        with open(args.json, "w", encoding="utf-8") as fh:
            json.dump(payload, fh, indent=2)
        print(f"wrote {args.json}")
    if args.markdown:
        os.makedirs(os.path.dirname(os.path.abspath(args.markdown)), exist_ok=True)
        with open(args.markdown, "w", encoding="utf-8") as fh:
            fh.write(markdown)
        print(f"wrote {args.markdown}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
