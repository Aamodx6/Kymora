# /r/MachineLearning Launch Draft: Fast Time-Series Feature Extraction

> **STATUS:** PRE-LAUNCH DRAFT. DO NOT POST WITHOUT OWNER APPROVAL.  
> Target subreddit: /r/MachineLearning (Tag: [P] Project)

---

## Submission Details
- **Title:** [P] Kymora: High-throughput time-series feature extraction with scikit-learn & Polars integration
- **Link:** https://github.com/Aamodx6/Kymora

---

## Post Body

Hi r/MachineLearning,

We built **Kymora**, a library for high-throughput time-series feature extraction. It computes statistical, temporal, and spectral features across batches of time series via a native Rust core with PyO3 bindings.

### Motivation & Empirical Tradeoffs
Feature extraction from raw time-series data is a cornerstone of tabular and classical machine learning pipelines. Existing solutions present distinct trade-offs:
- **Exhaustive Candidate Sets (`tsfresh`, `TSFEL`)**: Extract 200–800 features. Excellent for automated discovery, but runtimes reach tens of seconds per batch, creating severe bottlenecks during cross-validation, hyperparameter tuning, and real-time inference.
- **Minimal Canonical Sets (`catch22`)**: 22 carefully selected features. Much faster, but standard Python bindings still incur serialization and looping overhead across series.

We designed Kymora around `core33`, a 33-feature curated catalog covering statistical moments, autocorrelation, energy distribution, and spectral characteristics, with direct buffer borrowing and multithreaded Rayon parallelism.

### Parity-Gated Equal-Feature Performance
To isolate execution efficiency from feature set size, we benchmarked definition-matched feature sets after verifying numerical agreement ($\le 10^{-9}$ relative error):

**Hardware:** Intel Core i7-13620H (10 cores [6P+4E] / 16 threads, Windows 11 High Performance, AC online), 1,000 series × 500 length, float64 C-contiguous:

| Library | Features | Pooled Median Latency | Speedup Ratio | 95% Bootstrap CI |
|---|---|---|---|---|
| **Kymora** | **33** | **2.24 ms** | **1.0× (ref)** | — |
| Numba multi-core JIT | 33 | 13.34 ms | **6.0×** | [5.7×, 6.5×] |
| NumPy vectorized | 33 | 361.33 ms | **165.1×** | [157.2×, 170.5×] |
| TSFEL | 13 (matched) | 2,145.73 ms | **1,089.1×** | [1,007.3×, 1,132.2×] |
| tsfresh | 13 (matched) | 6,580.57 ms | **2,812.4×** | [2,584.3×, 2,914.1×] |

*(Raw headline throughput on full default catalogs: pooled median 1.94 ms / 514,245 series/s, 95% CI [495,050, 529,605] series/s).*

### Predictive Accuracy vs Runtime on UCR-42
We evaluated feature sets across 42 standardized UCR time-series classification benchmarks using identical RidgeClassifier and RandomForest pipelines:
- **Kymora `core33`**: 0.771 mean accuracy (mean rank 2.76), extracting features at ~100× lower runtime than `catch22` (0.767 accuracy, rank 2.69).
- **tsfresh** (0.824 accuracy, rank 1.48) and **TSFEL** (0.812 accuracy, rank 2.07) achieve higher raw accuracy, reflecting their substantially larger feature catalogs (777 and 285 features vs 33).

For offline discovery where compute is unconstrained, larger sets hold an advantage; for production latency budgets and iterative ML workflows, `core33` offers strong predictive accuracy per millisecond.

### Loss Ledger & Limitations
We publish all cases where Kymora is slower or scales sub-linearly:
- **Tiny Batches ($1 \times 10$)**: Inlined Numba is faster (Numba 3.00 µs vs Kymora 5.90 µs) because it avoids Python/Rust FFI crossing entirely.
- **Hybrid P/E-Core Scaling**: On hybrid CPUs (Intel 13620H), 16 threads (2.30 ms) saturates near physical P-core throughput (8 threads: 2.22 ms) due to E-core dispatch asymmetry.

### Reproducibility
The full benchmark suite is reproducible on your own machines:
```bash
git clone https://github.com/Aamodx6/Kymora.git
cd Kymora
./reproduce.sh
```

PyPI: `pip install kymora`  
Repository: https://github.com/Aamodx6/Kymora
