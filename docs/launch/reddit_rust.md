# /r/rust Launch Draft: Kymora — Fast Time-Series Feature Extraction in Rust & PyO3

> **STATUS:** PRE-LAUNCH DRAFT. DO NOT POST WITHOUT OWNER APPROVAL.  
> Target subreddit: /r/rust

---

## Submission Details
- **Title:** Kymora: High-throughput time-series feature extraction in Rust with PyO3 bindings
- **Link:** https://github.com/Aamodx6/Kymora

---

## Post Body

Hi r/rust,

I wanted to share **Kymora**, a project that uses Rust to bring high-performance time-series feature extraction to the Python data science ecosystem.

In Python, computing feature sets over thousands of time series often means running Python-level loops over NumPy or relying on heavy multiprocessing pools with large serialization overhead. We designed Kymora as a native Rust engine that borrows NumPy buffers directly, releases the Python GIL immediately, and evaluates features using Rayon and SIMD vectorization.

### Parity-Gated Equal-Feature Performance
To compare engines objectively, we implemented definition-matched feature sets across libraries and verified numerical parity ($\le 10^{-9}$ relative error) prior to benchmarking.

**Hardware:** Intel Core i7-13620H (10 cores [6P+4E] / 16 threads, Windows 11 High Performance, AC online), 1,000 series × 500 length, float64 C-contiguous:

| Library | Features | Pooled Median Latency | Speedup Ratio | 95% Bootstrap CI |
|---|---|---|---|---|
| **Kymora (Rust + Rayon)** | **33** | **2.24 ms** | **1.0× (ref)** | — |
| Numba multi-core JIT | 33 | 13.34 ms | **6.0×** | [5.7×, 6.5×] |
| NumPy vectorized | 33 | 361.33 ms | **165.1×** | [157.2×, 170.5×] |
| TSFEL | 13 (matched) | 2,145.73 ms | **1,089.1×** | [1,007.3×, 1,132.2×] |
| tsfresh | 13 (matched) | 6,580.57 ms | **2,812.4×** | [2,584.3×, 2,914.1×] |

*(Raw headline throughput on full default catalogs: pooled median 1.94 ms / 514,245 series/s, 95% CI [495,050, 529,605] series/s).*

### Predictive Accuracy vs Runtime Tradeoff (UCR-42)
Faster features are meaningless if they lack predictive power. We evaluated accuracy across 42 standardized UCR classification datasets:
- **Kymora `core33`**: 0.771 mean accuracy (mean rank 2.76), extracting features at ~100× lower runtime than `catch22` (0.767 accuracy, rank 2.69).
- **tsfresh** (0.824 accuracy, rank 1.48) and **TSFEL** (0.812 accuracy, rank 2.07) achieve higher raw accuracy, reflecting their massive candidate catalogs (777 and 285 features vs 33). For unconstrained exploratory search, larger sets hold an edge; for production inference pipelines, `core33` offers strong accuracy per millisecond.

### Rust Engine Architecture
1. **Direct Buffer Borrowing**: PyO3 borrows contiguous `PyArray` buffers as standard Rust slices `&[f64]` with no copy of the input data.
2. **Dynamic Sequential Fast Path**: To avoid Rayon dispatch overhead on small batches, calls where $N \times L < 8,000$ points execute sequentially inline on the caller thread. Dedicated `extract_one` achieves 3.90 µs median latency ($1 \times 100$).
3. **Amortized $O(1)$ Streaming Moments**: `StreamingExtractor` maintains rolling shifted power sums ($0.20\ \mu\text{s}$ per push; $0.30\ \mu\text{s}$ fast evaluation; worst-case $O(W)$ during periodic drift-guard re-anchoring).
4. **Memory Scratch Bounds**: Worker scratch is bounded at 2.29–3.33 MiB across 16 threads, eliminating GC churn and dynamic heap fragmentation.

### Honest Loss Ledger
We maintain an open ledger of all cases where Kymora loses or scales sub-linearly:
- **Tiny Batches ($1 \times 10$)**: Inlined Numba JIT is faster (Numba 3.00 µs vs Kymora 5.90 µs) because it avoids Python/Rust FFI crossing entirely.
- **Hybrid P/E-Core Scaling**: On hybrid CPUs (Intel 13620H), 16 threads (2.30 ms) saturates near physical P-core throughput (8 threads: 2.22 ms) due to E-core dispatch asymmetry.

### Reproducibility
The entire benchmark and numerical parity suite can be run via:
```bash
git clone https://github.com/Aamodx6/Kymora.git
cd Kymora
./reproduce.sh
```

PyPI: `pip install kymora`  
GitHub: https://github.com/Aamodx6/Kymora

Feedback on the Rust internals and crate architecture (planning to factor out `kymora-core` for pure-Rust users in v0.9.0) is very welcome!

---

## First Comment (Author Context & Rust Internals)

Hi everyone! A few details for Rustaceans on how the internals are organized:

- **Rayon chunking:** We use `par_chunks_mut` across output matrices. Each worker thread acquires a scratch arena for intermediate transforms (FFT, sorted percentiles) so heap allocations don't occur in the hot loop.
- **SIMD vectorization:** We write iterator-friendly loops allowing LLVM to emit AVX2 / NEON vector instructions automatically.
- **Roadmap:** We're currently factoring out the numerical core into a pure `kymora-core` crate (zero Python/PyO3 dependencies) so Rust users can depend on it directly in native Rust microservices and WASM edge nodes.
