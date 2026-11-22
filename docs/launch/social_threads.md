# Social Media Launch Drafts: X (Twitter) & LinkedIn

> **STATUS:** PRE-LAUNCH DRAFT. DO NOT POST WITHOUT OWNER APPROVAL.

---

## 1. X (Twitter) Launch Thread

**1/7**  
Excited to announce Kymora 0.8.2: high-throughput time-series feature extraction in Rust with Python bindings.

Extracts statistical, temporal & spectral features at sub-millisecond latencies with direct buffer borrowing & Rayon parallelism.

GitHub: https://github.com/Aamodx6/Kymora

**2/7**  
To make benchmarks fair, we evaluated definition-matched feature sets (verified bit-identical or $\le 10^{-9}$ rel-error before timing).

On 1,000 series × 500 length (16 threads, Intel 13620H):
• 6.0× vs Numba multi-core JIT
• 165.1× vs NumPy
• 1,089.1× vs TSFEL
• 2,812.4× vs tsfresh

**3/7**  
Does speed sacrifice accuracy? We tested across 42 UCR classification datasets:
• Kymora `core33`: 0.771 accuracy (~100× lower extraction time than catch22 at 0.767).
• tsfresh (0.824) and TSFEL (0.812) achieve higher accuracy reflecting their 777 & 285 features vs 33.

**4/7**  
New in 0.8.2:
• Dedicated `extract_one` achieving 3.90 µs median latency ($1 \times 100$)
• Dynamic sequential execution fast path for batches $<8,000$ points
• Amortized O(1) rolling streaming moments ($0.20\ \mu\text{s}$ push, $0.30\ \mu\text{s}$ compute)
• Scikit-learn transformer (`KymoraTransformer`) & Polars interop

**5/7**  
We believe in honest benchmarking, so our Loss Ledger lists where we fall short:
• Tiny batches ($1 \times 10$): Numba JIT is faster (3.0 µs vs 5.9 µs) due to Python/Rust FFI crossing.
• Hybrid P/E-core scaling: 16T plateaus near 8T throughput due to E-core dispatch asymmetry.

**6/7**  
Everything is reproducible on your own hardware with one command:
```bash
git clone https://github.com/Aamodx6/Kymora.git
cd Kymora
./reproduce.sh
```

**7/7**  
Try it out:
`pip install kymora`

Docs & benchmarks: https://github.com/Aamodx6/Kymora
Feedback on the Rust internals and streaming numerics is very welcome!

---

## 2. LinkedIn Launch Post

Today we are releasing **Kymora 0.8.2**, an open-source library for high-throughput time-series feature extraction built in Rust with Python bindings.

In industrial IoT, telemetry monitoring, and quantitative finance, computing summary features over thousands of time series is often the slowest bottleneck in production ML pipelines.

### Key Highlights:
1. **Parity-Gated Equal-Feature Performance:** In definition-matched benchmarks on $1,000 \times 500$ series (16 threads), Kymora is **6.0× faster than Numba JIT**, **165.1× faster than NumPy**, **1,089.1× faster than TSFEL**, and **2,812.4× faster than tsfresh**.
2. **Predictive Accuracy on UCR-42:** On 42 standardized UCR datasets, Kymora `core33` delivers 0.771 accuracy at ~100× lower extraction runtime than catch22. Libraries extracting 285–777 features achieve higher raw accuracy (0.812–0.824), illustrating the accuracy-vs-latency Pareto frontier.
3. **Amortized $O(1)$ Streaming Engine:** Pushes rolling window updates in $0.20\ \mu\text{s}$ with a $0.30\ \mu\text{s}$ fast evaluation latency.
4. **Seamless Python Ecosystem Integration:** Native Scikit-Learn transformer (`KymoraTransformer`) and Polars expression plugin (`kymora.polars`).

We publish an honest loss ledger detailing every scenario where Kymora is slower (e.g., $1 \times 10$ batches where inlined Numba leads), and provide a one-command reproduction script (`./reproduce.sh`) to verify all claims on your own hardware.

Read the full release notes and try it out:
- PyPI: `pip install kymora`
- GitHub: https://github.com/Aamodx6/Kymora
