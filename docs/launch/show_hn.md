# Show HN Draft: Kymora — Fast Time-Series Feature Extraction in Rust & Python

> **STATUS:** PRE-LAUNCH DRAFT. DO NOT POST WITHOUT OWNER APPROVAL.  
> Target submission time: Tuesday or Wednesday 13:00 UTC (09:00 ET).

---

## Submission Details
- **Title:** Show HN: Kymora – Fast time-series feature extraction in Rust and Python
- **URL / Text Link:** https://github.com/Aamodx6/Kymora

---

## Post Body

Hi HN,

I built **Kymora**, a library for high-throughput time-series feature extraction. It computes statistical, temporal, and spectral features across batches of time series via a Rust engine with PyO3 bindings.

We wanted extraction fast enough for real-time sensor streams and million-series pipelines, without paying defensive buffer copies or manual GIL management.

### Parity-Gated Equal-Feature Performance
To make benchmarking fair, each library was restricted to definition-matched features (verified bit-identical or $\le 10^{-9}$ relative error before timing).

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
Faster features only matter if they predict well. We evaluated feature sets across 42 standardized UCR time-series classification datasets using identical Ridge and Random Forest pipelines:

- **Kymora `core33`**: 0.771 mean accuracy (mean rank 2.76), extracting features at ~100× lower runtime than `catch22` (0.767 accuracy, rank 2.69).
- **tsfresh** (0.824 accuracy, rank 1.48) and **TSFEL** (0.812 accuracy, rank 2.07) achieve higher raw accuracy, reflecting their substantially larger feature catalogs (777 and 285 features vs 33). For exploratory discovery where compute is unconstrained, larger sets hold an advantage; for production latency budgets, `core33` offers strong accuracy per millisecond.

### Architecture Highlights
- **Direct Buffer Borrowing**: Operates directly on contiguous NumPy arrays with no copy of the input.
- **Dynamic Fast Path**: Batches with $N \times L < 8,000$ points run sequentially inline on the caller thread to eliminate thread pool dispatch latency. Dedicated `extract_one` achieves 3.90 µs median latency ($1 \times 100$).
- **Streaming Moments**: `StreamingExtractor` maintains rolling shifted power sums in amortized $O(1)$ time ($0.20\ \mu\text{s}$ per push; $0.30\ \mu\text{s}$ fast evaluation; worst-case $O(W)$ during periodic drift-guard re-anchoring).
- **Integrations**: Scikit-learn transformer (`KymoraTransformer`), Polars support (`extract_features_polars`), and strict NaN policies.

### Honest Loss Ledger
We maintain a public record of all cases where Kymora is slower or scales sub-linearly:
1. **Tiny Batches ($1 \times 10$)**: Numba JIT is faster than Kymora (Numba 3.00 µs vs Kymora 5.90 µs) due to Python/Rust FFI crossing overhead.
2. **Hybrid P/E-Core Scaling**: On hybrid CPUs (Intel 13620H with 6P+4E cores), 16 threads (2.30 ms) is slower than 8 threads (2.22 ms) due to E-core dispatch asymmetry.
3. Every loss case and condition is cataloged in `CLAIMS.md`.

### Reproducibility
Everything can be verified on your own hardware with a single command:
```bash
git clone https://github.com/Aamodx6/Kymora.git
cd Kymora
./reproduce.sh
```

PyPI: `pip install kymora`  
Repository: https://github.com/Aamodx6/Kymora

Would love feedback on the streaming numerics, the Rust/PyO3 architecture, and what features you'd like to see next!

---

## First Comment (Author Context & Limitations)

Thanks for checking out Kymora! A few upfront notes on methodology, design boundaries, and trade-offs:

1. **Why not extract 1,000+ features?**  
   Large feature extraction packages (like tsfresh) compute hundreds of variants and combinations. This is great for open-ended exploration, but in high-frequency trading, IoT edge nodes, and large-scale manufacturing telemetry, extracting 700+ features per window is prohibitive. Kymora focuses on a curated set of 33 statistical, temporal, and spectral features that capture primary dynamics with minimal redundancy.

2. **Hardware Environment:**  
   The primary benchmark figures were collected on an Intel Core i7-13620H laptop under Windows 11 (High Performance plan, AC connected). To avoid cherry-picking, we ran 3 interleaved sessions with 90-second cooldowns, logged CPU frequencies and temperatures, and reported pooled medians with 95% bootstrap confidence intervals. We encourage running `./reproduce.sh` or `scripts/cloud_bench.sh` on dedicated Linux server hardware.

3. **When NOT to use Kymora:**  
   - If you need GPU acceleration (Kymora is strictly CPU-oriented using SIMD and Rayon).
   - If you only ever process single time series of length 10 in a loop (use an inlined Numba JIT function).
   - If your application strictly requires exhaustive automated hypothesis testing over 800+ candidate features.

---

## FAQ: Prepared Responses to Anticipated Objections

### Q1: "Why is Kymora faster than Numba? Isn't Numba already compiled native code?"
**A:** Numba generates efficient LLVM machine code, but standard Numba implementations compute features via individual vectorized passes or separate loops. Kymora fuses statistical passes into unified cache-resident scans (e.g. shifted power sums computing mean, variance, skewness, and kurtosis simultaneously in cache), leverages AVX2/NEON SIMD auto-vectorization in Rust, and uses Rayon's work-stealing scheduler without GIL interference. At tiny shapes ($1 \times 10$), Numba is indeed faster because it avoids FFI boundaries entirely.

### Q2: "tsfresh has 777 features and automated feature selection. How is this a fair comparison?"
**A:** That is why we report two separate comparisons:
1. **Equal-Feature Benchmark**: We restricted tsfresh and TSFEL to the exact identical feature definitions and verified numerical parity ($\le 10^{-9}$ relative error) before timing. This isolates pure engine efficiency.
2. **UCR-42 Predictive Benchmark**: We evaluated whether Kymora's 33 features are predictive compared to tsfresh's 777 features. tsfresh achieves higher accuracy (0.824 vs 0.771), which we report plainly in our README and documentation, but takes $>2,800\times$ longer to compute.

### Q3: "Why not write this in C++ or Julia?"
**A:** Rust gives us memory safety, direct buffer borrowing without defensive copies, fearless multithreading with Rayon, and clean PyO3 bindings with no external runtime. It also compiles cleanly across Linux, macOS, and Windows with ABI3 compatibility.

### Q4: "Are the benchmarks reproducible?"
**A:** Yes. Running `./reproduce.sh` sets up isolated environments, validates numerical parity, runs the benchmark suite, and outputs the comparison table. Every number quoted in our docs traces directly to a frozen JSON artifact in `CLAIMS.md`.
