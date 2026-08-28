"""Batch-throughput benchmark: tsxtractor vs tsfresh vs catch22 vs TSFEL.

What this measures: wall-clock time to turn a batch of `n_series` equal-length
series into one feature row per series, which is the shape of work a feature
pipeline actually does. It is deliberately *not* a per-feature microbenchmark --
catch22 and TSFEL are competitive there, and the tsxtractor claim is throughput
across a whole batch (rayon parallelises over the series dimension).

Every library gets the same input matrix and is timed end to end, including the
input reshaping it requires (tsfresh needs a long DataFrame, catch22 and TSFEL
need per-series Python loops). That reshaping is part of the cost a user pays,
so excluding it would flatter the Python libraries in a way real pipelines never
see.

Install the comparison set with:  pip install -e ".[bench]"
Missing libraries are reported as skipped rather than failing the run.

Usage:
    python benches/bench_libraries.py --n-series 1000 --n-steps 500 \
        --json benches/results/latest.json --markdown benches/results/latest.md
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
    seconds: float | None
    skipped: str | None = None
    notes: str = ""

    @property
    def per_feature_ms(self) -> float | None:
        if self.seconds is None or not self.n_features:
            return None
        return self.seconds / self.n_features * 1e3


@dataclass
class Report:
    n_series: int
    n_steps: int
    platform: str
    python: str
    cpu_count: int
    results: list[Result] = field(default_factory=list)


def timed(fn: Callable[[], object]) -> tuple[object, float]:
    t0 = time.perf_counter()
    out = fn()
    return out, time.perf_counter() - t0


def bench_tsxtractor(X: np.ndarray) -> Result:
    import tsxtractor

    tsxtractor.extract_features(X[: min(64, len(X))])  # warm the thread pool
    feats, seconds = timed(lambda: tsxtractor.extract_features(X))
    return Result(
        library=f"tsxtractor {tsxtractor.__version__}",
        n_features=int(feats.shape[1]),  # type: ignore[union-attr]
        seconds=seconds,
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

    out, seconds = timed(run)
    return Result(
        library="tsfresh (EfficientFCParameters)",
        n_features=int(out.shape[1]),  # type: ignore[union-attr]
        seconds=seconds,
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

    _, seconds = timed(run)
    return Result(
        library="catch22 (pycatch22)",
        n_features=n_features,
        seconds=seconds,
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

    out, seconds = timed(run)
    return Result(
        library="TSFEL (all domains)",
        n_features=int(out.shape[1]),  # type: ignore[union-attr]
        seconds=seconds,
        notes="Python/numba, per-series extractor calls",
    )


def render_markdown(report: Report) -> str:
    ran = [r for r in report.results if r.seconds is not None]
    baseline = next((r for r in ran if r.library.startswith("tsxtractor")), None)

    lines = [
        "# Batch-throughput benchmark",
        "",
        f"{report.n_series} series x {report.n_steps} steps, "
        f"{report.cpu_count} cores, {report.platform}, Python {report.python}.",
        "",
        "Time is wall clock for the whole batch, including the input reshaping "
        "each library requires.",
        "",
        "| library | features | total time | ms/feature | vs tsxtractor |",
        "|---|---:|---:|---:|---:|",
    ]
    for r in report.results:
        if r.seconds is None:
            lines.append(f"| {r.library} | - | not installed | - | - |")
            continue
        rel = "-"
        if r is baseline:
            rel = "baseline"
        elif baseline and baseline.seconds:
            rel = f"{r.seconds / baseline.seconds:,.0f}x slower"
        lines.append(
            f"| {r.library} | {r.n_features} | {r.seconds:,.3f} s | "
            f"{r.per_feature_ms:,.4f} | {rel} |"
        )

    lines += [
        "",
        "Read this honestly: these libraries compute different numbers of "
        "features, so total time is not a like-for-like comparison. The "
        "tsxtractor advantage is parallelising across series in native code; on "
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
        choices=["tsxtractor", "tsfresh", "catch22", "tsfel"],
        default=None,
        help="run a subset (default: all available)",
    )
    args = ap.parse_args()

    rng = np.random.default_rng(args.seed)
    X = np.ascontiguousarray(rng.standard_normal((args.n_series, args.n_steps)))

    benches = {
        "tsxtractor": bench_tsxtractor,
        "catch22": bench_catch22,
        "tsfel": bench_tsfel,
        "tsfresh": bench_tsfresh,
    }
    selected = args.only or list(benches)

    report = Report(
        n_series=args.n_series,
        n_steps=args.n_steps,
        platform=platform.platform(),
        python=platform.python_version(),
        cpu_count=os.cpu_count() or 0,
    )

    for name in selected:
        print(f"running {name}...", flush=True)
        result = benches[name](X)
        if result.skipped:
            print(f"  skipped: {result.skipped}", flush=True)
        else:
            print(f"  {result.n_features} features in {result.seconds:.3f}s", flush=True)
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
