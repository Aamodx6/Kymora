---
title: "Changelog"
description: "Release history and version progression for Tsxtract following the Keep a Changelog standard."
order: 15
section: "Help"
---

Releases follow [Keep a Changelog](https://keepachangelog.com/en/1.1.0/) and [Semantic Versioning](https://semver.org/spec/v2.0.0.html). Project-specific rule: `feature_names()` order and length are public API — reordering, renaming, or removing a feature is major, while appending at the end is minor.

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
- **Supervised Feature Selection (`select_features`, `TsxSelector`):**
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
