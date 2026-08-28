# Benchmarks

## What is actually being measured

Wall-clock time to turn a batch of `n_series` equal-length series into one
feature row per series — the shape of work a real feature pipeline does.

Each library is timed end to end, **including the input reshaping it requires**:
`tsfresh` needs a long-format DataFrame, `catch22` and `TSFEL` need a per-series
Python loop. That reshaping is a cost users pay, so excluding it would flatter
the Python libraries in a way no production pipeline ever sees.

This is deliberately not a per-feature microbenchmark. `catch22` (a C core) and
`TSFEL` (view-based Python) are competitive on cost per feature; the claim here
is throughput across a whole batch, because the extraction is parallelised across
the series dimension in native code with the GIL released.

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
- **A single series shows no advantage.** Expected, not a bug. See
  [where the speed comes from](index.md#where-the-speed-comes-from).
- **Debug builds are roughly an order of magnitude slower.** Always
  `maturin develop --release` before timing anything.
