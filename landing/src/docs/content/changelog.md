---
title: "Changelog"
description: "Release history and version progression for Kymora following the Keep a Changelog standard."
order: 15
section: "Help"
---

Releases follow [Keep a Changelog](https://keepachangelog.com/en/1.1.0/) and [Semantic Versioning](https://semver.org/spec/v2.0.0.html). Project-specific rule: `feature_names()` order and length are public API — reordering, renaming, or removing a feature is major, while appending at the end is minor.

## 0.7.0 — 2026-10-04

Rename release: `tsxtract` is now **Kymora**. No numerics changed — feature values, names, order, and the NaN/error contracts are identical to 0.6.0.

### Changed

- PyPI distribution is `kymora` (`pip install kymora`); import is `kymora` (`import kymora as km`); extension module `kymora._core`; sklearn selector `KymoraSelector`; env vars `KYMORA_WISDOM` / `KYMORA_POOL` (old names no longer read — re-run `tune()`).
- `TsxError` became `KymoraError` inside the Rust core; Python callers still get `ValueError` with identical messages.

### Deprecated

- `import tsxtract` and `import tsxtractor` are thin shims that re-export `kymora` with a `DeprecationWarning`. Removal no earlier than 0.8.0.

## 0.6.0 — 2026-10-04

Packaging release: the import name, distribution name, and extension module now match the documented contract.

### Fixed

- PyPI distribution name is `tsxtract-rs` (`pip install tsxtract-rs`). The `v0.5.0` tag carried `name = "tsxtract"`, which would publish into an unrelated JAX project's namespace.
- Import name is `tsxtract` with extension module `tsxtract._core`. The `v0.5.0` tag still built `tsxtractor._core`.
- Version is single-sourced from `Cargo.toml`; `pyproject.toml` carries no `version`.

### Deprecated

- `import tsxtractor` is a thin shim that re-exports `tsxtract` and emits a `DeprecationWarning` on first import. Removal no earlier than 0.7.0.

## 0.5.0 — 2026-10-04

Zenith Architecture release delivering vectorized compute enhancements, persistent low-latency worker pools, multi-view transforms with invariance pruning, multichannel sensor processing, real-time fleet streaming, and supervised feature selection.

### Added

- **Multi-Select Quantiles ($O(n)$):**
  - Linear-interpolation multi-quantile selection (`multi_select`) replaces sorting passes for Core33 and minimal profiles.
  - Intermediate split between `Needs::SELECT` and `Needs::SORTED` prevents unnecessary order-statistic computations.
- **SIMD & Structure-of-Arrays (SoA) Vectorization:**
  - 4-lane SoA transpositions (`aos_to_soa_4x`), Pass 1 moments, Pass 2 central moments, and fused autocorrelation loops.
  - Dedicated fast-path `run_core33_f32_out32` for single-precision execution.
- **Persistent Spin-Then-Park Thread Pool:**
  - Low-latency custom worker pool (`src/pool.rs`) eliminates thread wake-up overhead during high-frequency micro-batch processing.
  - Environment variable fallback `TSXTRACT_POOL=rayon` and automatic panic unwinding boundaries.
- **Multi-View Transform Engine:**
  - 8 mathematical domain views (`raw`, `diff`, `diff2`, `detrend`, `znorm`, `abs`, `logret`, `rank`) exposed via `extract_features(..., views=[...])`.
  - Invariance tracking (`Invariances::SHIFT`, `SCALE`, `MONOTONE`) prunes redundant feature computations automatically.
- **Multichannel & Cross-Channel Dynamics:**
  - `extract_features_mc` and `extract_features_mc_df` for 3D time-series batches `(samples, channels, length)`.
  - Pairwise cross-correlation peak, lag offset, cross-covariance, Pearson coefficient, plus global spectral coherence and eigenvalue spread.
- **Fleet Real-Time Streaming (`MultiStreamExtractor`):**
  - Streaming extractor managing thousands of concurrent time-series signals with sub-microsecond $O(1)$ state updates.
- **Supervised Feature Selection (`select_features`, `KymoraSelector`):**
  - ANOVA F and correlation relevance statistics, Benjamini-Hochberg FDR control, and correlation-threshold redundancy clustering.
  - Scikit-learn transformer integration for machine learning pipelines.
- **Wisdom Auto-Tuner (`tune`):**
  - Automatic hardware micro-benchmarking and local profile caching.

### Changed

- `Cargo.toml` and `pyproject.toml` version bumped to `0.5.0`.
- Scratchpad memory buffers aligned to 64-byte boundaries (`#[repr(align(64))]`) to prevent false sharing and cache line splits.

## 0.4.0 — 2026-10-04

### Added

- Dynamic feature planning and profile tiers (`minimal`, `core33`, `extended`, `full`).
- In-place output buffer support (`out=`).
- Flat CSR ragged array ingestion (`extract_features_ragged`).
- Fine-grained thread pool sizing via `n_jobs`.
- Real-time `StreamingExtractor` with $O(1)$ fast tier.

## 0.3.0 — 2026-08-31

### Changed

- Real-to-complex FFT (`realfft`) replaces complex FFT over zero-imaginary buffers.
- Selection (`select_nth_unstable_by`) on order statistics replaces full sorting.
- Fused per-series traversals for moments, extremes, and autocorrelations.
- Branchless permutation entropy and peak counting.

## 0.2.1 — 2026-08-29

### Fixed

- CI Python jobs virtualenv configuration.
- Formatting and mypy type coverage fixes.

## 0.2.0 — 2026-08-29

### Added

- Multi-platform prebuilt wheels for Linux, macOS, and Windows (`abi3-py310`).
- Labeled DataFrame output with `extract_features_df()`.
- FFI boundary structural validation.
