# NumPy / SciPy Baseline Tuning Notes

## Implementation Overview
- **Name:** `numpy_baseline`
- **Purpose:** Honest, vectorized NumPy/SciPy reference implementation of the exact 33 `core33` features.
- **Role:** Establishes the performance and correctness ceiling for pure Python/C-vectorized arrays without custom native code.

## Vectorization & Optimization Details
- **Batch Vectorization:**
  - Moments (`mean`, `std`, `var`, `min`, `max`, `abs_energy`, `root_mean_square`): Computed along `axis=1` in vectorized C loops.
  - Spectral features: Uses vectorized 2D `np.fft.rfft(X, axis=1)`.
  - Differences & crossings: Vectorized slice operations along `axis=1`.
  - Linear trend (`slope`, `r2`): Closed-form vectorized analytical sums avoiding per-series regression objects.
- **Serial Reductions:**
  - `longest_strike_above_mean`, `longest_strike_below_mean`, and `permutation_entropy` are run per row where NumPy lacks native vectorized primitives.
