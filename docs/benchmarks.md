# Benchmarks

## What is actually being measured

Wall-clock time to turn a batch of `n_series` equal-length series into one
feature row per series — the shape of work a real feature pipeline does.

Each library is timed end to end, **including the input reshaping it requires**:
`tsfresh` needs a long-format DataFrame, `catch22` and `TSFEL` need a per-series
Python loop. That reshaping is a cost users pay, so excluding it would flatter
the Python libraries in a way no production pipeline ever sees.

This is deliberately not a per-feature microbenchmark. The headline claim is
throughput across a whole batch, because extraction is parallelised across the
series dimension in native code with the GIL released. Cost per feature is
reported alongside it, and is a separate matter: it reflects which features a
library computes, not only how well it computes them.

## Running it yourself

```bash
pip install -e ".[bench]"
python benches/bench_libraries.py --n-series 1000 --n-steps 500 \
    --json results.json --markdown results.md
```

Libraries that are not installed are reported as skipped rather than failing the
run, so you can benchmark a subset:

```bash
python benches/bench_libraries.py --only tsxtractor catch22
```

Useful flags: `--seed` (input reproducibility), `--json` / `--markdown` (write
machine- and human-readable results).

## A measured run

1000 series x 500 steps, 16 cores, Windows 11, Python 3.14, best of as many runs
as fit in a two-second budget per library:

| library | features | total time | series/s | ms/feature |
|---|---:|---:|---:|---:|
| **tsxtractor 0.2.1** | 33 | **1.2 ms** | 800,256 | 0.0379 |
| `catch22` (pycatch22) | 22 | 1.02 s | 976 | 46.58 |
| `TSFEL` (all domains) | 156 | 7.15 s | 140 | 45.86 |
| `tsfresh` (EfficientFCParameters) | 777 | 17.68 s | 57 | 22.76 |

The batch gap has two independent causes. One is parallelism plus a single FFI
crossing instead of a thousand Python calls. The other is that all 33 features
here are O(n) or O(n log n), while `catch22` includes costlier estimators -- on
one 500-point series, `catch22_all` takes 945 us against 9.4 us for
`extract_features` (best of 200 runs each). If you need those specific
estimators, that difference is not overhead you can optimise away.

## Published numbers

The [Benchmark workflow](https://github.com/Aamod007/Tsxtract/actions/workflows/benchmark.yml)
runs this on a GitHub Linux runner weekly and on demand, recording the runner's
core count alongside the timings, and uploads both the JSON and the Markdown
table as artifacts. The most recent committed run lives in
[`benches/results/`](https://github.com/Aamod007/Tsxtract/tree/main/benches/results).

Numbers measured on one laptop are not evidence anyone else can act on, which is
why the reproducible-runner result is the one published rather than a local best
case.

## Reading the results honestly

- **Total time across libraries is not like-for-like.** 33 features against
  1 558 features is not the same amount of work. Read the per-feature column
  next to the total.
- **Core count dominates.** The advantage is parallelism across series, so a
  4-core runner and a 64-core machine tell very different stories. The recorded
  core count is part of the result.
- **A single series shows no *parallel* advantage.** Expected, not a bug: with
  one series there is nothing to spread across cores, and what is left is the
  cost of the feature set itself. See
  [where the speed comes from](index.md#where-the-speed-comes-from).
- **Debug builds are roughly an order of magnitude slower.** Always
  `maturin develop --release` before timing anything.
