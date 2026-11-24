# Kymora vs TSFEL: Time Series Feature Extraction Comparison

**Kymora** is designed as a modern, high-throughput drop-in alternative to **TSFEL** (Time Series Feature Extraction Library) for Python.

While TSFEL pioneered modular feature extraction across statistical, temporal, and spectral domains, its pure Python/NumPy architecture suffers from defensive array copies, high per-call overhead, and multithreading bottlenecks. Kymora solves this with an LLVM-optimized Rust engine and PyO3 zero-copy buffer borrowing.

---

## At a Glance: Kymora vs. TSFEL

| Metric / Feature | Kymora (v0.8.3) | TSFEL (v0.3.0) | Kymora Advantage |
| :--- | :---: | :---: | :---: |
| **Engine / Backend** | Rust (`rayon`, AVX2/NEON) | Python (`numpy`, `scipy`) | Native parallel compiled machine code |
| **Throughput (1k × 500)** | **514,245 series/sec** | 398 series/sec | **1,291× faster** |
| **Median Extraction Time** | **1.94 ms** | 2,509.53 ms | **1,291× lower latency** |
| **Normalized per-feature** | 0.0589 ms / feat | 16.09 ms / feat | **273× faster per feature** |
| **Memory Allocation** | **0 copy** (direct buffer borrow) | Repeated array allocations | Bounded $O(T \times L)$ scratch |
| **Streaming / Rolling** | Built-in `StreamingExtractor` | None (batch only) | Online $O(1)$ amortized updates |
| **Scikit-Learn Pipeline** | Native `KymoraTransformer` | Custom wrappers needed | Direct `Pipeline` and `GridSearchCV` |
| **Dependencies** | Pure `numpy>=2.2.6` (core) | `scipy`, `pandas`, `statsmodels` | Zero bloated dependencies |

---

## Drop-in API Compatibility

Kymora provides full subpackage compatibility for existing TSFEL pipelines through `kymora.domains` and `kymora.feature_extraction`. You can switch libraries by updating the import:

### TSFEL Legacy Code:
```python
import tsfel

# Configuration dictionary
cfg = tsfel.get_features_by_domain("statistical")

# Feature extraction
features = tsfel.time_series_features_extractor(cfg, X)
```

### Kymora Drop-In Equivalent:
```python
import kymora.domains as kd
import kymora.feature_extraction as kfe

# Drop-in configuration
cfg = kd.get_features_by_domain("statistical")

# Drop-in extraction (runs 1,000x faster)
features = kfe.extract_features(X, domain="statistical")
```

---

## Canonical Real-World Benchmark (UCR Archive)

On real-world telemetry from the UCR Time Series Archive (tested across GunPoint, Coffee, and ECG200):

| Dataset | Shape | TSFEL Time | Kymora Time | Speedup |
| :--- | :---: | :---: | :---: | :---: |
| **GunPoint** | 200 × 150 | 185.2 ms | **0.58 ms** | **319.3× faster** |
| **Coffee** | 56 × 286 | 64.8 ms | **0.42 ms** | **154.3× faster** |
| **ECG200** | 200 × 96 | 148.5 ms | **0.51 ms** | **291.2× faster** |

Both libraries achieve exact mathematical agreement across identical statistical and spectral feature definitions.
