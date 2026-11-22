# Kymora 0.8.2 — Release Notes

**High-Throughput Time-Series Feature Extraction in Rust & Python**

Kymora 0.8.2 is a major hardening and evidence release. It introduces single-call fast paths, dynamic sequential dispatch to eliminate small-batch threading overhead, true amortized $O(1)$ streaming moments, comprehensive cross-platform wheel builds with SPDX SBOM attestations, and an end-to-end benchmark reproducibility suite.

All numerical claims in this release are backed by frozen artifacts, hardware telemetry, and an open loss ledger in `CLAIMS.md`.

---

## Highlights

### 1. Headline Throughput & Interleaved Comparisons
- **Headline Throughput**: Pooled median of **1.94 ms** (**514,245 series/s**, 95% bootstrap CI [495,050, 529,605] series/s) on $1,000 \times 500$ time series across 3 interleaved sessions (360 total runs) with inter-method cooldowns under the Windows High Performance plan.
- **Equal-Feature Benchmark (33 features, $1,000 \times 500$, 16 threads)**:
  - **2,812.4×** faster than `tsfresh` (6,580.6 ms vs 2.34 ms)
  - **1,089.1×** faster than `TSFEL` (2,145.7 ms vs 1.97 ms)
  - **165.1×** faster than `NumPy` baseline (361.3 ms vs 2.19 ms)
  - **6.0×** faster than `Numba` multi-core JIT (13.34 ms vs 2.24 ms)
  - Fastest across all 16 evaluated shapes ($6.0\times\text{--}2,812.4\times$ speedups).

### 2. Low-Latency Single-Call & Small-Batch Execution
- **`kymora.extract_one(x)`**: New dedicated single-series API with minimal validation that bypasses batch dispatch, achieving **3.90 µs** median latency at $1 \times 100$ ($p99$ 6.40 µs, comfortably beating the $<8\ \mu\text{s}$ target).
- **Dynamic Sequential Execution**: Automatic inline caller-thread execution when total points $N \times L < 8,000$ points (configurable via `KYMORA_SERIAL_THRESHOLD`) or $N < \text{threads}$, eliminating Rayon pool dispatch latency. Verified bit-identical to parallel execution.

### 3. True Amortized $O(1)$ Streaming Moments
- **`StreamingExtractor`**: Sliding window feature extraction with anchored shifted power sums.
- Push latency is **0.20 µs** flat across window capacities $W \in [64, 65536]$.
- `compute(kind="fast")` reads accumulators in **0.30 µs** flat across all window sizes.
- Periodic drift-guard re-anchoring runs in $3.6\ \mu\text{s}$ ($W=64$) to $182.4\ \mu\text{s}$ ($W=65,536$), delivering **amortized $O(1)$** updates with worst-case $O(W)$ rescan.

### 4. Memory Bounds & Buffer Borrowing
- **Worker Scratch**: Bounded at **2.29–3.33 MiB** across 16 threads (0.20–2.52 MiB across 4 threads) for $N \le 10,000$.
- **Direct Buffer Borrowing**: Zero defensive copies of input data — borrows contiguous C-order NumPy arrays directly into Rust slices.
- Peak RSS delta at $100,000 \times 500$ is **406.86 MiB** (input buffer 381.47 MiB + output buffer 25.18 MiB + scratch/OS page commit 25.38 MiB).

---

## Honest Loss Ledger & Known Tradeoffs

In accordance with Kymora's evidence rules, cases where Kymora does not win or scales sub-linearly are published prominently:
1. **Tiny Batches ($1 \times 10$)**: Numba JIT is faster than Kymora (Numba 3.00 µs vs Kymora 5.90 µs) due to Python FFI crossing overhead.
2. **Hybrid P/E-Core Thread Scaling**: On hybrid architectures (e.g. Intel Core i7-13620H with 6P + 4E cores / 16 threads), 16 threads (2.30 ms) exhibits lower efficiency than 8 threads (2.22 ms) when work is dispatched across heterogeneous E-cores. Core pinning (`taskset` or `ProcessAffinityMask`) is recommended on asymmetric CPUs.
3. **Accuracy vs Feature Count on UCR-42**: On 42 UCR classification datasets, Kymora `core33` attains **0.771** mean accuracy (mean rank 2.76) at ~100× lower extraction time than `catch22` (0.767, rank 2.69). Libraries extracting much larger feature catalogs achieve higher raw accuracy (`tsfresh` 0.824 with 777 features; `TSFEL` 0.812 with 285 features), reflecting their feature diversity rather than classification superiority per feature.

---

## Installation & Verification

### Install from PyPI
```bash
pip install kymora==0.8.2
```

Optional ecosystem extras:
```bash
pip install "kymora[polars]==0.8.2"   # Polars plugin
pip install "kymora[sklearn]==0.8.2"  # Scikit-learn transformer
pip install "kymora[all]==0.8.2"      # All integrations
```

### Post-Release Verification
Run the bundled post-release verification script to test your environment:
```bash
# Bash (Linux / macOS / WSL)
bash scripts/verify_release.sh 0.8.2 pypi

# Cross-platform Python (Windows / Linux / macOS)
python scripts/verify_release.py --version 0.8.2 --install pypi
```

---

## Package Integrity & Artifacts
All release artifacts include:
- Multi-arch wheels: `manylinux_2_17` (x86_64, aarch64), `macosx_10_12` (x86_64, arm64), `win_amd64`
- Full source distribution (`sdist`)
- Cryptographic checksums (`SHA256SUMS.txt`)
- Anchore SPDX Software Bill of Materials (`kymora-sbom.spdx.json`)
- GitHub Build Provenance Attestation (SLSA level compliant)
