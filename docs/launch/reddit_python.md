# /r/Python Launch Draft: Kymora — Fast Time-Series Feature Extraction

> **STATUS:** PRE-LAUNCH DRAFT. DO NOT POST WITHOUT OWNER APPROVAL.  
> Target subreddit: /r/Python

---

## Submission Details
- **Title:** Kymora: High-throughput time-series feature extraction in Rust with scikit-learn & Polars integration
- **Link:** https://github.com/Aamodx6/Kymora

---

## Post Body

Hi r/Python,

I built **Kymora**, a library for extracting statistical, temporal, and spectral features from batches of time series.

Extracting tabular features from thousands of time-series signals is often a severe bottleneck in Python machine learning workflows. Existing packages either rely on slow Python-level loops, large multiprocessing worker pools with serialization overhead, or require extracting hundreds of noisy features when you only need a high-signal core set.

### Parity-Gated Equal-Feature Performance
To compare libraries fairly, we benchmarked definition-matched feature sets after verifying numerical agreement ($\le 10^{-9}$ relative error):

**Hardware:** Intel Core i7-13620H (10 cores [6P+4E] / 16 threads, Windows 11 High Performance, AC online), 1,000 series × 500 length, float64 C-contiguous:

| Library | Features | Pooled Median Latency | Speedup Ratio | 95% Bootstrap CI |
|---|---|---|---|---|
| **Kymora** | **33** | **2.24 ms** | **1.0× (ref)** | — |
| Numba multi-core JIT | 33 | 13.34 ms | **6.0×** | [5.7×, 6.5×] |
| NumPy vectorized | 33 | 361.33 ms | **165.1×** | [157.2×, 170.5×] |
| TSFEL | 13 (matched) | 2,145.73 ms | **1,089.1×** | [1,007.3×, 1,132.2×] |
| tsfresh | 13 (matched) | 6,580.57 ms | **2,812.4×** | [2,584.3×, 2,914.1×] |

*(Raw headline throughput on full default catalogs: pooled median 1.94 ms / 514,245 series/s, 95% CI [495,050, 529,605] series/s).*

### Predictive Accuracy vs Extraction Time (UCR-42)
Faster features only matter if they predict well. We evaluated feature sets across 42 standardized UCR time-series classification datasets using identical Ridge and Random Forest pipelines:
- **Kymora `core33`**: 0.771 mean accuracy (mean rank 2.76), extracting features at ~100× lower runtime than `catch22` (0.767 accuracy, rank 2.69).
- **tsfresh** (0.824 accuracy, rank 1.48) and **TSFEL** (0.812 accuracy, rank 2.07) achieve higher raw accuracy, reflecting their substantially larger feature catalogs (777 and 285 features vs 33). For unconstrained exploratory discovery, larger sets hold an advantage; for production inference latency budgets, `core33` offers strong accuracy per millisecond.

### Python Integration
```python
import numpy as np
import kymora as km

# 1. Batch extraction (borrows NumPy buffers directly, releases the GIL)
X = np.random.randn(1000, 500)
features = km.extract_features(X)  # shape: (1000, 33)

# 2. Dedicated single-series fast path (3.90 µs median latency)
f1 = km.extract_one(X[0])

# 3. Scikit-learn Transformer pipeline
from kymora.sklearn import KymoraTransformer
from sklearn.pipeline import Pipeline
from sklearn.ensemble import RandomForestClassifier

pipe = Pipeline([
    ("features", KymoraTransformer(profile="core33")),
    ("clf", RandomForestClassifier()),
])

# 4. Polars integration
import polars as pl
import kymora.polars as kmp

df = pl.DataFrame({"signal": X.tolist()})
df_features = df.with_columns(kmp.extract_features(pl.col("signal")).alias("feats"))
```

### Amortized $O(1)$ Streaming Moments
For rolling window telemetry, `StreamingExtractor` maintains shifted power sums in amortized $O(1)$ time ($0.20\ \mu\text{s}$ per push; $0.30\ \mu\text{s}$ fast evaluation; worst-case $O(W)$ during periodic drift-guard re-anchoring).

### Honest Loss Ledger
- **Tiny Batches ($1 \times 10$)**: Inlined Numba is faster (Numba 3.00 µs vs Kymora 5.90 µs) because it avoids Python/Rust FFI crossing entirely.
- **Hybrid P/E-Core Scaling**: On hybrid CPUs (Intel 13620H), 16 threads (2.30 ms) saturates near physical P-core throughput (8 threads: 2.22 ms) due to E-core dispatch asymmetry.

### Reproducibility
The entire benchmark and numerical parity suite can be verified on your own hardware with:
```bash
git clone https://github.com/Aamodx6/Kymora.git
cd Kymora
./reproduce.sh
```

PyPI: `pip install kymora`  
Repository: https://github.com/Aamodx6/Kymora
