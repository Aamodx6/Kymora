# Numba Baseline Tuning Notes

## Implementation Overview
- **Name:** `numba_baseline`
- **Purpose:** Hand-rolled, LLVM-compiled JIT baseline implementing the exact 33 `core33` features.
- **Role:** Establishes the performance and precision ceiling for JIT-compiled Python on identical feature definitions.

## Algorithm & FFT Architecture (Amendment A1)
- **O(N log N) FFT:** Rather than falling back to an $O(N^2)$ direct discrete Fourier transform, this baseline implements:
  1. **Iterative Radix-2 Cooley-Tukey FFT:** In-place bit-reversal permutation and butterfly passes for powers of 2 ($N = 2^p$).
  2. **Bluestein's Chirp-z Transform:** For non-power-of-2 and prime lengths, converts the DFT into a cyclic convolution of length $M = 2^{\lceil \log_2(2N-1) \rceil}$ evaluated via forward/inverse radix-2 FFTs. This guarantees $O(N \log N)$ complexity for all lengths without external dependencies.
- **Verified Accuracy:** Maximum absolute error versus `numpy.fft.fft` is $< 2 \times 10^{-12}$ on double precision inputs across odd, prime, and power-of-2 lengths.

## Fastmath Modes (Amendment A2)
- **Dual Compilation Targets:**
  - `fastmath=True`: Aggressive vectorization, reciprocal approximations, and reassociation. Used exclusively for **throughput** benchmarks.
  - `fastmath=False`: Strict IEEE 754 compliance. Used for **agreement (B1)** and **robustness (B4)** suites to ensure zero arithmetic discrepancies.
- **Reporting:** Every benchmark record explicitly documents which mode (`fastmath=True` or `fastmath=False`) was executed.
