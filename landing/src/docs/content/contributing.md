---
title: "Contributing Guide"
description: "Development environment setup, code guidelines, testing procedures, and tutorials for contributing to Tsxtract."
order: 14
section: "Help"
---

Contributions with the highest leverage are correctness work, documentation, and platform support — the 33-feature set is closed on purpose. This guide covers environment setup, repo layout, checks, the add-a-feature walkthrough, and pull-request expectations.

```bash
git clone https://github.com/Aamodx6/Tsxtract.git
cd Tsxtract
python -m venv .venv
source .venv/bin/activate
pip install maturin
pip install -e ".[test]"
maturin develop --release
```

## Environment setup

You need a stable Rust toolchain (from [rustup.rs](https://rustup.rs/)) and Python 3.10+. The block above clones the repo, isolates a virtual environment, installs the build backend and test extras, and compiles the extension in release mode.

- **Release builds only:** debug builds run roughly an order of magnitude slower and invalidate every timing observation.
- **Virtualenv for CI parity:** `maturin develop` requires an active virtualenv; bare interpreters fail the same way CI once did.
- **Verify the setup:** `python -c "import tsxtract; print(tsxtract.__version__)"` should print the built version.

## Repository layout

```text
Tsxtract/
  src/lib.rs            # PyO3 module registration only, no math
  src/ffi.rs            # Boundary wrappers: views, validation, GIL release
  src/error.rs          # TsxError enum, single conversion to PyErr
  src/extract.rs        # Dispatch, batch validation, Rayon fan-out
  src/features/mod.rs   # NAMES registry + compute_all (single source of truth)
  src/features/         # stats, temporal, spectral, entropy, streaming
  python/tsxtract/    # __init__.py, _core.pyi stubs, py.typed marker
  tests/                # reference, property, NaN, validation, streaming suites
  benchmarks/              # bench_libraries, ablation, UCR downstream + results/
  scripts/              # validation_report, feature_redundancy_analysis
  docs/                 # MkDocs site sources (validation, features, nan-policy)
  landing/src/docs/     # This documentation site (content, nav, features.ts)
```

Three architecture rules constrain every change, and PRs breaking one are asked to change approach:

- **No numeric logic in Python:** `__init__.py` is a documented pass-through; all math lives in `src/features/`.
- **No panic crosses the FFI boundary:** no `unwrap`, `expect`, or panicking index on user-reachable paths; fallible steps return `Result<_, TsxError>`.
- **Structure and NaN stay separate:** `TsxError` covers shapes, lengths, and layout only; NaN is a value with its own propagation contract.

## Running tests and checks

Run the full set before opening a PR — CI runs the same commands:

```bash
pytest tests/
cargo test --no-default-features
cargo fmt --all -- --check
cargo clippy --no-default-features --all-targets -- -D warnings
python scripts/validation_report.py
```

| Command | Scope | Notes |
| :--- | :--- | :--- |
| `pytest tests/` | Python-visible behavior | Reference, property, NaN, validation, streaming suites |
| `cargo test --no-default-features` | Pure-Rust unit tests | Flag disables `pyo3/extension-module` so binaries link |
| `cargo fmt --all -- --check` | Rust formatting | Must pass with no diff |
| `cargo clippy --no-default-features --all-targets -- -D warnings` | Lints as errors | Zero warnings accepted |
| `python scripts/validation_report.py` | Reference drift gate | Exits non-zero if any feature drifts from NumPy/SciPy |

## Adding a new feature

Worked example: suppose a `range_over_iqr` metric is agreed in a New feature proposal issue. Agree first — PRs without an agreed proposal may close on scope regardless of quality.

1. **Implement the math** in the matching `src/features/*.rs` module (or a new module for a new group), keeping the function panic-free on every input including empty, constant, and NaN series.
2. **Register the name** by appending to `NAMES` in `src/features/mod.rs` — never insert mid-list — and write its value at the matching tail position in `compute_all`.
3. **Add a reference** implementation to `reference()` in `tests/test_features.py`; the existing sample matrix (normal, trending, periodic, constant, two-element, single-element, heavily-tied) then covers it automatically.
4. **Document undefined cases** in `docs/features.md`, and add a case to `tests/test_nan_policy.py` when the feature introduces a new undefined condition.
5. **Touch `_core.pyi`** only when a signature changed — appending a feature does not change one.
6. **Add a CHANGELOG.md entry** under `Unreleased` in the correct Added/Changed/Fixed/Removed group.

Version impact follows the policy table: appending at the end is a minor bump, while reordering, renaming, removing, or changing NaN row-vs-cell conditions is major. When unsure, state the uncertainty in the PR description instead of guessing.

## Pull-request checklist

- **One logical change:** a feature plus a refactor is two PRs, not one diff.
- **Why, not what:** the diff shows the what, so the description explains the motivation.
- **Regression test:** new behavior needs a test that fails without the change.
- **Version impact:** note the bump implied by the versioning table.
- **Style match:** `cargo fmt` clean, Clippy silent, and comments explaining reasoning rather than restating code.
- **Bug reports:** include OS, Python version, `tsxtract.__version__`, a runnable snippet, and the expected NumPy/SciPy expression for wrong values.

> [!WARNING]
> TODO(verify): commit-message convention and Code of Conduct file. No commit convention is configured in-repo, and `CONTRIBUTING.md` links `CODE_OF_CONDUCT.md` but that file is absent from the repo root — confirm both before enforcing them on contributors.

## License and conduct

The project is MIT-licensed (see `LICENSE` and the `MIT` classifier in `pyproject.toml`). Participation follows the Code of Conduct linked from `CONTRIBUTING.md`; report gaps in that file as part of the `TODO(verify)` above rather than assuming coverage.

## See also

References used throughout this guide:

- [Changelog](/docs/changelog) — where your `Unreleased` entry lands.
- [Feature Catalog](/docs/feature-catalog) — the registry your feature extends.
- [Core Concepts](/docs/core-concepts) — contracts your tests must preserve.
