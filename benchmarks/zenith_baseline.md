# Zenith Architecture Baseline Report (`benchmarks/zenith_baseline.md`)

This baseline report records measured execution performance for Tsxtract on an AVX2-class CPU prior to the Zenith optimizations, verifying the decision gates defined in `arch_zenith.md` §1, §5, and §7.

---

## 1. Measured Per-Stage Profile (Single Core, n=500, 1000 Series)

| Stage | Baseline Time (ms) | Time per Series (µs) | Share (%) | Decision Gate Threshold | Gate Status |
|---|---|---|---|---|---|
| Fused moments & reductions | 6.50 ms | 6.50 µs | 12.7% | - | Baseline established |
| **Quantiles / Sorting** | **18.57 ms** | **18.57 µs** | **36.2%** | **> 25%** | **GATED IN (Z1)** |
| Spectral / FFT | 10.54 ms | 10.54 µs | 20.6% | > 35% after Z1 | Deferred to post-Z1 |
| Autocorrelation (ACF) | 11.77 ms | 11.77 µs | 23.0% | - | Evaluated with SoA (Z2) |
| Permutation entropy | 3.90 ms | 3.90 µs | 7.6% | - | SIMD LUT target |
| **Total (Isolated Stages)** | **51.27 ms** | **51.27 µs** | **100.0%** | - | - |
| **Fused core33 pipeline** | **20.52 ms** | **20.52 µs** | - | - | Baseline reference |

---

## 2. Parallel Scaling and Efficiency $\eta$ at (1,000 × 500)

Parallel efficiency is evaluated as $\eta = \frac{T_1}{N \cdot T_N}$ for $N \in \{1, 2, 4, 8, 16\}$ threads:

| Thread Count ($N$) | Execution Time ($T_N$) | Speedup vs 1T | Parallel Efficiency ($\eta$) | Status vs $\eta \ge 0.85$ |
|---|---|---|---|---|
| 1 thread | 20.52 ms | 1.00× | 1.000 | Baseline |
| 2 threads | 12.63 ms | 1.62× | 0.812 | Below 0.85 threshold |
| 4 threads | 8.75 ms | 2.34× | 0.586 | Below 0.85 threshold |
| 8 threads | 5.85 ms | 3.51× | 0.438 | Below 0.85 threshold |
| 16 threads | 5.75 ms | 3.57× | 0.223 | Below 0.85 threshold |

### Conclusion on Thread Pool Overhead
For short batch runs (1,000 series × 500 points), thread pool synchronization, worker wake-up latency, and dynamic stealing in general-purpose pools consume significant overhead.
The condition $\eta < 0.85$ at $(1,000 \times 500)$ is **TRUE**. Therefore, **Z6 (Persistent spin-then-park thread pool)** is **GATED IN**.

---

## 3. Decision Gate Summary Table (§7)

| Condition | Observation | Action | Status |
|---|---|---|---|
| SORT/quantile stage > 25% of time | 36.2% of per-series stage runtime | Implement Z1 histogram multi-select | **Gated In (Priority 1)** |
| $\eta < 0.85$ at (1k × 500) | $\eta = 0.22$ at 16 threads, $\eta = 0.81$ at 2 threads | Implement Z6 persistent spin pool with rayon fallback | **Gated In (Priority 1)** |
| Output Breadth & Selection | Crucial for domain applicability and downstream ML | Implement Z11 (Views), Z12 (Multichannel), Z13 (Feature Selection), Z14 (MultiStream) | **Gated In (Priority 1)** |
| Single-precision fast mode | Half memory bandwidth, AVX-512/AVX2 float width | Implement Z4 `precision="f32"` opt-in mode | **Gated In (Priority 2)** |
| Hardware specialization & wisdom | System-specific thread and tuning parameters | Implement Z9 wisdom cache with CI static table | **Gated In (Priority 2)** |
| Ragged scheduling | Plan switching on ragged batches | Implement Z10 length-bucketed scheduling | **Gated In (Priority 2)** |
