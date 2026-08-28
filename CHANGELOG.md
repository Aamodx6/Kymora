# Changelog

All notable changes to this project are documented here.

The format follows [Keep a Changelog](https://keepachangelog.com/en/1.1.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

Versioning note specific to this project: the order and length of
`feature_names()` is part of the public API. Reordering, renaming, or removing a
feature is a **major** version change; appending a new feature at the end is a
**minor** one. See [CONTRIBUTING.md](CONTRIBUTING.md#versioning-policy).

## [Unreleased]

## [0.2.0] - 2026-08-29

The first release installable without a Rust toolchain on Linux and macOS.
0.1.0 shipped a Windows-only wheel, so anyone else was silently falling back to
an sdist build; that is fixed here.

### Added
- Prebuilt wheels for Linux (x86_64, aarch64), macOS (x86_64, arm64), and
  Windows (x86_64). Built as abi3-py310, so one wheel per platform covers
  Python 3.10 through 3.13+.
- `extract_features_df()` — same output as `extract_features()`, returned as a
  `pandas.DataFrame` with `feature_names()` as columns. pandas is an optional
  extra (`pip install "tsxtractor[pandas]"`), not a hard dependency.
- `tsxtractor.__version__`.
- Type stubs (`_core.pyi`) and a `py.typed` marker, so IDEs and mypy see real
  signatures instead of `Any`.
- Structural input validation at the PyO3 boundary: empty input, zero-length
  series, non-contiguous arrays, `window`/`stride` < 1, and `window` longer than
  the series now raise `ValueError`; wrong dtype or shape raises `TypeError`.
  Previously these could reach the compute path.
- A documented, tested NaN contract (`tests/test_nan_policy.py`): any NaN in a
  series makes all 33 of that series' features NaN; individually-undefined
  features are NaN on their own.
- Property-based tests (`hypothesis`) asserting no panic crosses the FFI
  boundary for adversarial series, plus sliding-window boundary fuzzing.
- GitHub Actions: cross-platform test matrix, wheel build matrix, PyPI
  publishing via Trusted Publishing (OIDC, no long-lived tokens), and a docs
  deploy.
- Benchmark now covers `catch22` and `TSFEL` alongside `tsfresh`, and emits
  machine-readable JSON so published numbers are reproducible.
- A reference-validation report (`scripts/validation_report.py`) recording
  max absolute error per feature against numpy/scipy.
- Documentation site (MkDocs Material), `CONTRIBUTING.md`,
  `CODE_OF_CONDUCT.md`, and issue templates.

### Changed
- Rust core split into `lib.rs` (module registration only), `ffi.rs` (the PyO3
  boundary), `error.rs` (`TsxError` -> `PyErr`), and `extract.rs` (dispatch and
  validation). No math moved; `features/` remains the single source of truth.
- README leads with batch throughput rather than a per-feature multiplier
  against `tsfresh` alone, and states when *not* to use this library.
- Classifier moved from `Development Status :: 3 - Alpha` to `4 - Beta`.
- `sliding_features` `stride` now defaults to `1`.

### Fixed
- Exactly-constant series no longer emit float-noise variance (~1e-31), which
  previously leaked into std-guarded features.

## [0.1.1] - 2026-07-31

### Added
- PyPI metadata: long description from README, license, keywords, and project
  URLs.

## [0.1.0] - 2026-07-31

### Added
- Initial release. 33 features across six groups (stats, change, counts,
  correlation, entropy, spectral), computed in a Rust core with zero-copy numpy
  ingestion and `rayon` parallelism across the series dimension.
- `extract_features()` (2D arrays and ragged lists), `feature_names()`,
  `sliding_features()`.
- Windows x86_64 wheel and sdist only — see 0.2.0 for the full platform matrix.

[Unreleased]: https://github.com/Aamod007/Tsxtract/compare/v0.2.0...HEAD
[0.2.0]: https://github.com/Aamod007/Tsxtract/compare/v0.1.1...v0.2.0
[0.1.1]: https://github.com/Aamod007/Tsxtract/compare/v0.1.0...v0.1.1
[0.1.0]: https://github.com/Aamod007/Tsxtract/releases/tag/v0.1.0
