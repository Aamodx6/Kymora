---
title: "bench: Add Polars LazyFrame extraction benchmark"
labels: ["polars", "benchmarks", "good first issue"]
---

## Context
Kymora provides native integration with Polars via `kymora.extract_features_polars` and chunked streaming. Polars users often operate on `LazyFrame` query plans rather than eager DataFrames.

## Acceptance Criteria
1. Create a benchmark in `benchmarks/suites/bench_polars.py` measuring extraction overhead on eager `pl.DataFrame` vs `pl.LazyFrame` with varying batch chunk sizes.
2. Verify zero unnecessary memory re-allocations during expression evaluation.
3. Compare against standard Polars expressions computing equivalent mean/variance features.

## Files to Touch
- `benchmarks/suites/bench_polars.py`
- `docs/polars.md`

## Tests to Add
- Benchmark suite verification test in `tests/test_benchmarks.py`.
