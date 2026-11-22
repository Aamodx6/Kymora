# Blog Post Draft: Engineering Kymora — Fast Time-Series Feature Extraction in Rust & Python

> **STATUS:** PRE-LAUNCH DRAFT. DO NOT POST WITHOUT OWNER APPROVAL.

---

## Title: Engineering Kymora: Sub-Millisecond Time-Series Feature Extraction in Rust

### Introduction
Time-series feature extraction is an essential foundation of modern forecasting, predictive maintenance, financial modeling, and sensor anomaly detection. Turning a continuous 1D raw signal into tabular descriptors—such as variance, spectral energy, autocorrelation, and skewness—allows practitioners to deploy powerful tabular ML models (LightGBM, XGBoost, CatBoost) on sequential signals.

However, existing feature extraction tools in the Python data ecosystem often force an unpleasant compromise:
1. **Speed vs. Redundancy:** Libraries like `tsfresh` and `TSFEL` extract hundreds of candidate features, taking seconds or minutes per batch.
2. **Looping Overhead:** Libraries like `catch22` offer a compact feature set, but standard Python wrappers still incur per-series looping and serialization overhead.
3. **Streaming Bottlenecks:** Naive rolling window implementations recompute features over the entire window ($O(W)$ per sample), failing hard real-time latency budgets.

We built **Kymora** to solve these problems. It is a native Rust engine with zero-overhead PyO3 bindings, Rayon parallelism, and an amortized $O(1)$ streaming engine.

---

### Fair Benchmarking: The Parity-Gated Equal-Feature Protocol
Benchmarking across different libraries is notoriously difficult because feature definitions vary subtly across packages. Comparing an extractor computing 22 features against one computing 777 features is fundamentally flawed.

To make benchmarking fair and transparent, we adopted a two-tier protocol:
1. **Equal-Feature Benchmark**: We implemented definition-matched feature sets across libraries and verified numerical parity ($\le 10^{-9}$ relative error) before timing.
2. **Predictive Accuracy Benchmark**: We evaluated whether Kymora's 33 features are predictive compared to larger competitor catalogs on standardized UCR datasets.

#### Equal-Feature Benchmark Results
**Hardware:** Intel Core i7-13620H (10 cores [6P+4E] / 16 threads, Windows 11 High Performance scheme, AC connected), $1,000 \text{ series} \times 500 \text{ length}$, float64 C-contiguous:

| Library | Features | Pooled Median Latency | Speedup Ratio | 95% Bootstrap CI |
|---|---|---|---|---|
| **Kymora** | **33** | **2.24 ms** | **1.0× (ref)** | — |
| Numba multi-core JIT | 33 | 13.34 ms | **6.0×** | [5.7×, 6.5×] |
| NumPy vectorized | 33 | 361.33 ms | **165.1×** | [157.2×, 170.5×] |
| TSFEL | 13 (matched) | 2,145.73 ms | **1,089.1×** | [1,007.3×, 1,132.2×] |
| tsfresh | 13 (matched) | 6,580.57 ms | **2,812.4×** | [2,584.3×, 2,914.1×] |

*(Raw headline throughput on full default catalogs: pooled median 1.94 ms / 514,245 series/s, 95% CI [495,050, 529,605] series/s).*

---

### Accuracy vs Extraction Time Pareto Frontier (UCR-42)
Faster features only matter if they predict well. We evaluated feature sets across 42 standardized UCR time-series classification benchmarks using identical RidgeClassifier and RandomForest pipelines:

- **Kymora `core33`**: 0.771 mean accuracy (mean rank 2.76), extracting features at ~100× lower runtime than `catch22` (0.767 accuracy, rank 2.69).
- **tsfresh** (0.824 accuracy, rank 1.48) and **TSFEL** (0.812 accuracy, rank 2.07) achieve higher raw accuracy, reflecting their substantially larger feature catalogs (777 and 285 features vs 33).

For offline discovery where compute is unconstrained, larger sets hold an advantage; for production latency budgets and iterative ML workflows, `core33` offers strong predictive accuracy per millisecond.

---

### Architectural Deep Dive

#### 1. Direct Buffer Borrowing
Kymora borrows contiguous C-order NumPy arrays directly into Rust slices `&[f64]` with no copy of the input data. When arrays are already C-contiguous, zero memory allocations occur during ingestion.

#### 2. Dynamic Sequential Execution Fast Path
Rayon work-stealing parallelism is ideal for large batches, but dispatching tiny tasks to a thread pool incurs overhead. In Kymora, when total points $N \times L < 8,000$ (configurable via `KYMORA_SERIAL_THRESHOLD`) or $N < \text{threads}$, calls execute inline on the caller thread. Dedicated `extract_one` achieves 3.90 µs median latency ($1 \times 100$).

#### 3. Amortized $O(1)$ Streaming Moments
Streaming time-series data requires rolling window updates. Rather than rescanning the window ($O(W)$), Kymora's `StreamingExtractor` maintains shifted power sums:
- Pushing a new sample runs in **0.20 µs** flat across all window capacities ($W \in [64, 65536]$).
- `compute(kind="fast")` reads current moments in **0.30 µs** flat.
- To prevent catastrophic numerical cancellation from floating-point roundoff, a drift guard triggers periodic re-anchoring (measured at 3.6 µs for $W=64$ to 182.4 µs for $W=65,536$), delivering true **amortized $O(1)$** updates with worst-case $O(W)$ rescan.

#### 4. Bounded Worker Scratch
Kymora worker scratch is bounded at 2.29–3.33 MiB across 16 threads (0.20–2.52 MiB across 4 threads) for $N \le 10,000$, preventing memory bloat and garbage collection pauses.

---

### The Honest Loss Ledger
We document where Kymora is slower:
1. **Tiny Batches ($1 \times 10$)**: Inlined Numba is faster (Numba 3.00 µs vs Kymora 5.90 µs) because it avoids Python/Rust FFI crossing entirely.
2. **Hybrid P/E-Core Scaling**: On hybrid CPUs (Intel 13620H), 16 threads (2.30 ms) saturates near physical P-core throughput (8 threads: 2.22 ms) due to E-core dispatch asymmetry.

---

### One-Command Reproduction
To reproduce every benchmark claim and verify numerical parity on your own machine:
```bash
git clone https://github.com/Aamodx6/Kymora.git
cd Kymora
./reproduce.sh
```

PyPI: `pip install kymora`  
Repository: https://github.com/Aamodx6/Kymora
