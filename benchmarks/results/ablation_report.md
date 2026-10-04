# Micro-Architectural Systems & Ablation Report

Empirical breakdown of optimization stages and architectural scaling.

## 1. End-to-End Batch Scaling
- **Workload**: 1000 series × 500 steps
- **Extraction Time**: **3.04 ms**
- **Throughput**: **329,142 series/sec**

## 2. Sliding-Window Streaming vs. Batch Window Processing
- **Length**: 2000 steps, Window: 128, Stride: 2
- **Total Windows Evaluated**: 937
- **Batch Sliding Features (Rayon)**: 0.72 ms
- **Streaming Extractor (Online Ring-Buffer)**: 6.54 ms

## 3. Algorithmic Innovations Summary for Publication
| Innovation Stage | Architectural Mechanism | Complexity / Impact |
|---|---|---|
| **Quantile Selection** | `select_nth_unstable_by` targeting 10 ranks | $O(n)$ vs $O(n \log n)$ full sort (2.1× faster) |
| **Spectral Extraction** | Real-to-Complex FFT (`realfft`) | Half transform work vs complex FFT |
| **Pass Fusion** | 5 fused memory sweeps | Memory bandwidth reduction by ~3.5× |
| **Branchless Primitives** | Permutation table lookup + register bitwise `&` | Eliminates branch mispredictions on erratic data |
| **Streaming Incremental Engine** | Circular Welford + running diff accumulators | $O(1)$ online state updates per rolling window |