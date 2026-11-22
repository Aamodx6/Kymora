# PyData / scikit-learn Discourse Draft: Kymora — Fast Time-Series Feature Extraction

> **STATUS:** PRE-LAUNCH DRAFT. DO NOT POST WITHOUT OWNER APPROVAL.  
> Target forum: PyData Discourse / scikit-learn Community

---

## Topic Details
- **Title:** Kymora: Fast time-series feature extraction with native scikit-learn transformer integration
- **Tags:** time-series, scikit-learn, feature-extraction, performance, rust

---

## Post Body

Hello PyData community,

I'd like to share **Kymora**, a library designed to make time-series feature extraction fast and seamlessly compatible with scikit-learn pipelines.

### Motivation
Extracting statistical and spectral summary features from raw signals is common across IoT telemetry, financial forecasting, and healthcare diagnostics. However, running standard extractors across thousands of series often becomes the slowest component in model validation loops.

Kymora combines a multithreaded Rust engine with a fully compliant scikit-learn estimator:
- `KymoraTransformer` passes 50/50 standard scikit-learn estimator checks.
- Compatible with `clone()`, `pickle`, and scikit-learn `Pipeline` / `GridSearchCV`.
- Supports `set_output(transform="pandas")` and `set_output(transform="polars")`.
- Direct buffer borrowing: operates directly on contiguous NumPy arrays with no copy of the input.

### Parity-Gated Equal-Feature Performance
To compare engines objectively, we implemented definition-matched feature sets across libraries and verified numerical agreement ($\le 10^{-9}$ relative error) before timing:

**Hardware:** Intel Core i7-13620H (10 cores [6P+4E] / 16 threads, Windows 11 High Performance, AC online), 1,000 series × 500 length, float64 C-contiguous:

| Library | Features | Pooled Median Latency | Speedup Ratio | 95% Bootstrap CI |
|---|---|---|---|---|
| **Kymora** | **33** | **2.24 ms** | **1.0× (ref)** | — |
| Numba multi-core JIT | 33 | 13.34 ms | **6.0×** | [5.7×, 6.5×] |
| NumPy vectorized | 33 | 361.33 ms | **165.1×** | [157.2×, 170.5×] |
| TSFEL | 13 (matched) | 2,145.73 ms | **1,089.1×** | [1,007.3×, 1,132.2×] |
| tsfresh | 13 (matched) | 6,580.57 ms | **2,812.4×** | [2,584.3×, 2,914.1×] |

*(Raw headline throughput on full default catalogs: pooled median 1.94 ms / 514,245 series/s, 95% CI [495,050, 529,605] series/s).*

### Classification Accuracy vs Extraction Time (UCR-42)
We evaluated predictive performance across 42 standardized UCR classification datasets:
- **Kymora `core33`**: 0.771 mean accuracy (mean rank 2.76), extracting features at ~100× lower runtime than `catch22` (0.767 accuracy, rank 2.69).
- **tsfresh** (0.824 accuracy, rank 1.48) and **TSFEL** (0.812 accuracy, rank 2.07) achieve higher raw accuracy, reflecting their substantially larger candidate catalogs (777 and 285 features vs 33). For unconstrained exploration, larger sets hold an edge; for production inference latency budgets, `core33` offers strong accuracy per millisecond.

### Example: Scikit-learn Pipeline
```python
import numpy as np
from kymora.sklearn import KymoraTransformer
from sklearn.ensemble import HistGradientBoostingClassifier
from sklearn.pipeline import Pipeline
from sklearn.model_selection import cross_val_score

X = np.random.randn(500, 200) # 500 series of length 200
y = np.random.randint(0, 2, size=500)

pipe = Pipeline([
    ("extract", KymoraTransformer(profile="core33", n_jobs=4)),
    ("clf", HistGradientBoostingClassifier(random_state=42)),
])

scores = cross_val_score(pipe, X, y, cv=5)
print(f"Mean CV score: {scores.mean():.3f}")
```

### Limitations & Loss Ledger
- **Tiny Batches ($1 \times 10$)**: Inlined Numba is faster (Numba 3.00 µs vs Kymora 5.90 µs) because it avoids Python/Rust FFI crossing entirely.
- **Hybrid P/E-Core Scaling**: On hybrid CPUs (Intel 13620H), 16 threads (2.30 ms) saturates near physical P-core throughput (8 threads: 2.22 ms) due to E-core dispatch asymmetry.

### Reproducibility
```bash
git clone https://github.com/Aamodx6/Kymora.git
cd Kymora
./reproduce.sh
```

PyPI: `pip install kymora`  
Repository: https://github.com/Aamodx6/Kymora
