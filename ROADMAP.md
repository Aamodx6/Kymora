# Kymora Roadmap

This roadmap documents Kymora's current development priorities, known limitations, and future architectural plans.

---

## Known Limitations

1. **CPU Only (No GPU/TPU Support):**
   - Kymora is engineered explicitly for CPU execution using native SIMD and Rayon work-stealing parallelism. GPU batch feature extraction is an explicit non-goal for the core library.

2. **Single-Series Small-Batch Overhead at $N=1$ ($L \le 10$):**
   - While `kymora.extract_one` achieves 3.90 µs latency at $1 \times 100$, inlined scalar Numba loops outperform Kymora on tiny single series (e.g., $1 \times 10$, where Numba takes ~3.0 µs vs Kymora's 5.9 µs). Kymora is optimized for batch workloads ($N \ge 10$) and continuous streams.

3. **Curated Feature Set Size:**
   - The default `core33` profile provides 33 high-signal, non-redundant features (catch22-class classification accuracy). Users needing massive exploratory feature sets (e.g., tsfresh's 777 features) should note the accuracy-vs-runtime trade-off documented in our benchmarks.

4. **Thread Scaling on Hybrid Core Architectures:**
   - On Intel hybrid CPUs (P-cores + E-cores), scaling saturates near the physical P-core count (~8–10 threads) due to memory bus saturation and E-core scheduling latency.

---

## Short-Term Roadmap (v0.8.x - v0.9.x)

- [ ] **Python 3.13 Free-Threaded (cp313t) Wheels:**
  - Dedicated pre-built wheels for free-threaded CPython (`cp313t`) are not supported yet (planned for 0.9.x once upstream free-threaded ABI stabilizes in PyO3 and NumPy). Leverage Kymora's GIL-free Rust architecture once dependencies support it.
- [ ] **Pure Rust Crate (`kymora-core`):**
  - Factor out the numerical engine into an independent `kymora-core` crate on crates.io with optional Rayon support and zero PyO3 dependencies.
- [ ] **In-Browser WASM Feature Extraction:**
  - Build `kymora-wasm` for client-side evaluation in browsers and edge runtimes.
- [ ] **Arrow-Native Streaming:**
  - Add native Apache Arrow / PyArrow RecordBatch ingestion to `StreamingExtractor` and `extract_features_chunked`.

---

## Mid-Term Roadmap (v1.0.0+)

- [ ] **Supervised Feature Selection Enhancements:**
  - Expand `KymoraSelector` with mutual-information filtering and cluster-based redundancy elimination across multi-view profiles.
- [ ] **Additional Domain Views:**
  - Add wavelet decompositions and empirical mode decomposition views to the multi-view transform engine.
- [ ] **Expanded Multi-Channel Interactions:**
  - Add cross-spectral phase coherence and multivariate transfer entropy kernels.
- [ ] **Continuous Regression Tracking:**
  - Automated tracking of benchmark throughput and latency with strict regression budgets in CI.
