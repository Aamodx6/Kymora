# Blog post draft: batch time-series features without the dispatch tax (DO NOT PUBLISH YET)

*Style: short technical post. No hype words, every number linked.*

Time-series feature extraction in Python usually means a per-series loop:
tsfresh builds DataFrames, catch22 dispatches C once per series, TSFEL
loops in Python. On 1,000 series × 500 steps that dispatch dominates —
before any math runs.

Kymora moves the loop into Rust: one FFI crossing for the whole batch,
zero-copy buffer borrows, GIL released, Rayon across series, per-series
work fused into a handful of passes with shared intermediates. The API is
one function:

```python
feats = kymora.extract_features(X)  # (n_series, 33)
```

To compare honestly you have to separate three questions: how long does
each library's natural setup take (raw time), how efficient is each
computed value (per series-feature), and who computes *the same work*
fastest (matched features, definitions verified first). On 1,000 × 500
(i7-13620H, 16 threads, pooled medians + 95% CIs):

- matched: 3.4× vs numba, 61× vs numpy, 565× vs TSFEL, 1,694× vs tsfresh
- raw as-is: 3.18 ms vs catch22 833 ms, TSFEL 2,542 ms, tsfresh 20,891 ms
- per series-feature: 0.096 µs vs 37.9 / 16.3 / 26.9 µs

The streaming side was the harder numerics problem. Rolling moments from
raw power sums cancel catastrophically on offset series, so the extractor
keeps anchored shifted sums and re-anchors on drift — O(1) pushes that
match batch output to 1e-9, with the one ill-conditioned corner
(large-offset skew/kurt) bounded and documented instead of hidden.

Limitations, because they matter more than the wins: single-machine
exploratory numbers (`./reproduce.sh` regenerates everything; artifacts in
`benchmarks/results/`); numba wins tiny batches by up to ~40×; scaling
stops at physical cores; float32 covers core33-class features only.

Links: repo (https://github.com/Aamodx6/Kymora), docs
(https://aamodx6.github.io/Kymora/), claim→artifact map (CLAIMS.md).
