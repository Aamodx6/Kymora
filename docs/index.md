# tsxtract

High-performance time-series feature extraction for Python, powered by a native Rust engine.

Extract curated statistical, temporal, spectral, multichannel, and multi-view features across large batches of time series. The Rust core operates directly on zero-copy NumPy buffers, releases the GIL, and maximizes throughput via SIMD vectorization and persistent low-latency worker pools.

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

- **Vectorized SIMD & SoA Transpositions**: First and second statistical passes, autocorrelations, and running aggregates run across SIMD lanes (AVX2/NEON) using Structure-of-Arrays (SoA) layouts.
- **$O(n)$ Multi-Select Quantiles**: Direct histogram/selection multi-quantile evaluation eliminates sorting overhead on Core33 and minimal profiles.
- **Persistent Spin-Then-Park Thread Pool**: Custom thread pool avoids operating system wake-up latencies by spin-waiting on high-frequency batches with automatic Rayon fallback.
- **Multi-View Transform Engine**: Multiply feature coverage across 8 mathematical domain views (`raw`, `diff`, `diff2`, `detrend`, `znorm`, `abs`, `logret`, `rank`) with automatic invariance pruning.
- **Multichannel & Cross-Channel Dynamics**: Full support for 3D time-series batches `(samples, channels, length)`, evaluating per-channel baselines and pairwise cross-correlation / covariance interactions.
- **Fleet Real-Time Streaming**: `MultiStreamExtractor` monitors thousands of live time-series streams simultaneously with sub-microsecond $O(1)$ state updates.
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
