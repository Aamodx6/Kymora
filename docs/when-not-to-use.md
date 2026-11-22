# When NOT to Use Kymora

Engineering honesty is a core principle of Kymora. While Kymora provides orders-of-magnitude faster feature extraction for batch and streaming time series on CPUs, there are specific scenarios where alternative tools or architectures are a better choice.

---

## 1. Single-Series Tiny Workloads ($N = 1, L \le 10$)

If your workload evaluates only a single, very short time series at a time (e.g., $1 \times 10$ points):

- **Why:** Every Python extension incurs a fixed C-API call overhead (~1.5–3 µs) for argument inspection, NumPy array type validation, and C FFI transition. On tiny single series ($1 \times 10$), an inlined JIT-compiled scalar loop (such as Numba with `@njit(fastmath=True)`) runs in ~3.0 µs, whereas Kymora takes ~5.9 µs (or 3.90 µs using `kymora.extract_one`).
- **Where Kymora wins instead:** As soon as batch size reaches $N \ge 10$, Kymora's Rayon parallelism and fused single-pass SIMD vectorization win decisively (e.g., 2.4× faster at $10 \times 500$, and 6×–12× faster at $N \ge 1,000$ on identical features).
- **Recommendation:** For embedded scalar processing of single points or $L \le 10$ series in pure Python/JIT loops, use Numba.

---

## 2. Massive Exploratory Feature Searches (500+ Features)

If your project requires computing hundreds of parameterized feature variations without prior domain knowledge:

- **Why:** Kymora's default `core33` profile was intentionally curated to provide 33 high-signal, mathematically non-redundant features ($|r| < 0.70$ for 83.3% of pairs), achieving catch22-class classification accuracy (79.96% RF on 42 UCR datasets) at over 100× lower extraction cost.
- **Where Kymora wins instead:** When latency, throughput, and memory matter (production inference, streaming pipelines, large training sets), or when using Kymora's multi-view transforms.
- **Recommendation:** If you need 700+ parameterized features (e.g., custom continuous wavelet grids or extensive autoregressive lag sweeps) and have hours of batch compute budget, use `tsfresh`.

---

## 3. GPU Batch Extraction

If your infrastructure relies on GPU or TPU hardware acceleration:

- **Why:** Kymora is engineered strictly for multi-core CPUs. It uses cache-aware single-traversal loops, Rayon work-stealing, and CPU SIMD auto-vectorization (AVX2/FMA/NEON). It does not maintain CUDA kernels or PyTorch/JAX GPU execution graphs.
- **Recommendation:** For GPU-native time series feature extraction, evaluate GPU-accelerated libraries or custom PyTorch/CuPy tensor operations.

---

## 4. Streaming Windows of Fewer than 4 Points ($W < 4$)

If you are using `StreamingExtractor` with a rolling window size $W \le 3$:

- **Why:** Higher-order statistical moments (skewness and kurtosis) require sufficient degrees of freedom. On a 2-point window, skewness is mathematically undefined or numerically near-degenerate, and kurtosis degenerates to $-2.0$.
- **Recommendation:** For micro-windows ($W = 2$ or $W = 3$), compute rolling mean and variance using simple scalar sliding sums rather than full statistical shape extractors.
