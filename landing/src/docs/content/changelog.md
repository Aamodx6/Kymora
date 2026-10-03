---
title: "Changelog"
description: "Release history and version progression for Tsxtract following the Keep a Changelog standard."
order: 15
section: "Help"
---

Releases follow [Keep a Changelog](https://keepachangelog.com/en/1.1.0/) and [Semantic Versioning](https://semver.org/spec/v2.0.0.html). Project-specific rule: `feature_names()` order and length are public API — reordering, renaming, or removing a feature is major, while appending at the end is minor.

## Unreleased

No entries yet. Add new rows under the correct Added, Changed, Fixed, or Removed heading with each PR.

## 0.3.0 — 2026-08-31

Extraction runs roughly 1.8x faster end to end with no change to any feature value, column order, or the NaN contract. Reference tests (`rtol=1e-9`) and bit-exactness property tests pass unchanged.

### Changed

- Real-to-complex FFT (`realfft`) replaces the complex FFT over a zero-imaginary buffer, halving transform work.
- Quantiles use selection (`select_nth_unstable_by`) over the needed order statistics instead of a full sort; min and max moved into the first pass.
- Per-series traversals are fused: one pass for sums, extremes, NaN and constant checks; one for central moments 2–4; one for differences; one for all four threshold features; one for all four autocorrelation lags.
- Permutation entropy and peak counting are branchless (ordinal-pattern lookup table, non-short-circuiting comparisons).
- FFT workspace and order-statistics buffers are thread-local, so allocations scale with thread count rather than series count.
- Measured on a 16-core Windows machine: 1000×500 from 2.46 ms to 1.34 ms, 5000×500 from 11.07 ms to 7.43 ms, 1000×2000 from 10.08 ms to 5.32 ms.

### Removed

- Direct `rustfft` dependency, replaced by `realfft` (which wraps `rustfft`, so the tree is not shorter — the transform is the right one for real input).

### Fixed

- Spectral entropy and centroid now return NaN, instead of a value derived from non-finite power, when total power is not positive-finite (reachable via infinities).
- Shannon entropy no longer yields NaN when a probability share underflows to zero while its weight stays positive.

## 0.2.1 — 2026-08-29

Packaging-only release; library code, output order, and the NaN contract are identical to 0.2.0. (0.2.0 was tagged but never reached PyPI, so this is the first 0.2.x on PyPI and the first with Linux and macOS wheels.)

### Fixed

- CI Python jobs now create and activate a virtualenv before `maturin develop`, with native Windows paths on Windows runners.
- Release smoke test resolves NumPy from PyPI while `tsxtractor` still comes only from the fresh wheel.
- `cargo fmt` drift in `src/extract.rs`, `src/features/temporal.rs`, and `src/ffi.rs`.
- `mypy` coverage via installed `pandas-stubs`.
- Docs navigation now includes the contributing page, and the docs site publishes at `https://aamod007.github.io/Tsxtract/`.

## 0.2.0 — 2026-08-29

First release installable without a Rust toolchain on Linux and macOS; 0.1.0 shipped a Windows-only wheel.

### Added

- Prebuilt wheels for Linux (`x86_64`, `aarch64`), macOS (`x86_64`, `arm64`), and Windows (`x86_64`) as `abi3-py310`, covering Python 3.10 through 3.13+.
- `extract_features_df()` returning `feature_names()`-labeled DataFrames; pandas stays an optional extra.
- `tsxtractor.__version__`, `_core.pyi` type stubs, and the `py.typed` marker.
- Structural validation at the PyO3 boundary: bad shapes, lengths, layouts, and window geometry raise `ValueError`/`TypeError` instead of reaching compute.
- Documented, tested NaN contract in `tests/test_nan_policy.py`.
- `hypothesis` property tests asserting no panic crosses the FFI boundary, plus sliding-window fuzzing.
- GitHub Actions matrices for tests and wheels, PyPI Trusted Publishing, and docs deployment.
- Cross-library benchmark with machine-readable JSON, and a reference-validation report script.
- MkDocs documentation site, `CONTRIBUTING.md`, and issue templates.

### Changed

- Rust core split into `lib.rs`, `ffi.rs`, `error.rs`, and `extract.rs` with `features/` as the single math source of truth.
- README leads with batch throughput and states when not to use the library.
- Development classifier moved from Alpha to Beta; `sliding_features` `stride` defaults to `1`.

### Fixed

- Exactly-constant series report variance of precisely `0.0` instead of float-noise residue near `1e-31`.

## 0.1.1 — 2026-07-31

### Added

- PyPI metadata: README long description, license, keywords, and project URLs.

## 0.1.0 — 2026-07-31

### Added

- Initial release: 33 features across six groups (stats, change, counts, correlation, entropy, spectral) with a Rust core, zero-copy NumPy ingestion, and Rayon parallelism across series.
- `extract_features()` for 2D and ragged input, `feature_names()`, and `sliding_features()`.
- Windows `x86_64` wheel and sdist; other platforms fell back to source builds until 0.2.0.

## See also

Context for the entries above:

- [Contributing Guide](/docs/contributing) — adding `Unreleased` entries with each PR.
- [Installation](/docs/installation) — verifying which release is installed.
- [Core Concepts](/docs/core-concepts) — the stability guarantees releases must preserve.
