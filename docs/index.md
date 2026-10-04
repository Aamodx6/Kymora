# tsxtract

High-performance time-series feature extraction for Python, powered by a native Rust engine.

Extract curated statistical, temporal, spectral, multichannel, and multi-view features across large batches of time series. The Rust core operates directly on zero-copy NumPy buffers, releases the GIL, and parallelizes across series with Rayon; per-series work runs through fused single-traversal passes over lazily computed shared intermediates.

```bash
pip install tsxtract-rs
```

```python
import numpy as np
import tsxtract

# Batch extraction over 100,000 series
X = np.random.randn(100_000, 500)
feats = tsxtract.extract_features(X)       # (100_000, 33) float64
df = tsxtract.extract_features_df(X)       # pandas DataFrame with labeled columns
```

---

## Architectural Highlights

- **Fused passes & shared intermediates**: moments, differences, crossings, peaks, autocorrelations, trend, ordinal patterns, and FFT each accumulate in as few traversals as possible; intermediates shared between features are computed at most once per series, and unrequested features cost nothing.
- **Rayon parallelism with serial fallback**: series are spread across worker threads (GIL released for the whole parallel region); batches below `SERIAL_THRESHOLD` (8 series) run serially to avoid pool wake-up overhead on small calls.
- **$O(n)$ multi-select quantiles**: histogram/selection multi-quantile evaluation avoids full sorting overhead on the core33 and minimal profiles.
- **Multi-View Transform Engine**: Multiply feature coverage across 8 mathematical domain views (`raw`, `diff`, `diff2`, `detrend`, `znorm`, `abs`, `logret`, `rank`) with automatic invariance pruning.
- **Multichannel & Cross-Channel Dynamics**: Full support for 3D time-series batches `(samples, channels, length)`, evaluating per-channel baselines and pairwise cross-correlation / covariance interactions.
- **Fleet Real-Time Streaming**: `MultiStreamExtractor` monitors thousands of live time-series streams simultaneously with incremental rolling-window updates; per-sample ingestion is amortized $O(1)$, and a fast 12-feature tier avoids sorting and FFT.
- **Supervised Feature Selection**: `select_features` and `TsxSelector` provide FDR-controlled hypothesis testing and correlation clustering directly within scikit-learn pipelines.

---

## Guarantees

| Surface | Guarantee |
|---|---|
| `feature_names()` order and length | Frozen across all minor releases within a major version |
| Output dtype | `float64` default (with fast `float32` pipeline support) |
| [NaN policy](nan-policy.md) | Exact and tested NaN propagation semantics |
| Panic safety | Rust panics are intercepted and translated into Python exceptions |

Numerical parity is validated feature by feature against NumPy and SciPy references.

---

## Where the speed comes from

Three compounding effects, in order of contribution:

1. **Parallelism across series.** The dominant term. Each series is independent, so throughput scales with core count while the GIL is released. (Conversely, a single series shows no *parallel* advantage — there is nothing to spread.)
2. **Fused per-series passes.** Feature groups share traversals and shared intermediates are computed at most once per series, so catalog breadth does not multiply cost.
3. **Zero-copy buffers.** Inputs are borrowed views of the caller's NumPy memory and the output array is allocated once and written in place — no defensive copies, no per-series allocation in the hot path.

What does *not* contribute (despite older wording that suggested otherwise): explicit SIMD intrinsics (there are none — only compiler auto-vectorization) and a custom spin-pool scheduler (the prototype in `src/pool.rs` is not wired up; scheduling is Rayon).

---

## When not to use this

- **Parameterized feature families.** The catalog is closed by design: no `fft_coefficient` at arbitrary indices, no `cwt_coefficients`, no `agg_linear_trend` grids. If your model depends on those, `tsfresh` is the right tool.
- **Non-CPU execution.** GPU and distributed backends are out of scope.
- **Single-series latency.** Fixed overhead per call is ~0.1 ms; for one short series a Numba loop can be faster. The advantage appears across batches.
- **Non-float or strided input.** Only contiguous `float64`/`float32` is accepted — anything else raises instead of copying silently, so cast with `X.astype(np.float64)` first.
