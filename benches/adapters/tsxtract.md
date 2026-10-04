# Tsxtract Adapter Tuning Notes

## Library Overview
- **Name:** Tsxtract (`tsxtractor._core`)
- **Version:** 0.5.0
- **Implementation:** Rust native extension with PyO3 bindings and Rayon/SpinPool execution.

## Fast Configuration & Tuning
- **Zero-Copy Ingestion:** 2D NumPy array pointers are borrowed directly via PyO3 `PyReadonlyArray2`. Contiguous C-order arrays are processed without allocation.
- **Threading Model:** GIL is released during the parallel compute region (`py.allow_threads`). Multi-core parallelism is handled across the series dimension via `RAYON_NUM_THREADS` or `n_jobs`.
- **Profiles:**
  - `core33`: 33 frozen, curated statistical, temporal, and spectral features.
  - `minimal`: Cheap fused moments and statistics without SORT or FFT.
  - `extended`: Rich catalog spanning 100+ features.
  - `full`: Complete catalog.
- **Memory Footprint:** Output is allocated once as `(n_series, n_features)` float64 array.
