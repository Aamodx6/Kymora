# Contributing

The full guide lives in
[CONTRIBUTING.md](https://github.com/Aamodx6/Tsxtract/blob/main/CONTRIBUTING.md)
in the repository. This page is the short version.

## Setup

You need a [Rust toolchain](https://rustup.rs/) and Python 3.10+.

```bash
git clone https://github.com/Aamodx6/Tsxtract
cd Tsxtract
python -m venv .venv
. .venv/bin/activate          # .venv\Scripts\activate on Windows
pip install maturin
pip install -e ".[test]"
maturin develop --release
```

Always build with `--release`. A debug build is roughly an order of magnitude
slower, which makes every timing observation meaningless.

## Checks

Run all of these before opening a PR; CI runs the same set.

```bash
pytest tests/                        # Python-visible behaviour
cargo test --no-default-features     # pure-Rust unit tests
cargo fmt --all -- --check
cargo clippy --no-default-features --all-targets -- -D warnings
python tools/validation_report.py  # exits non-zero if a feature drifts
```

`--no-default-features` disables `pyo3/extension-module`, which omits libpython
at link time; a test binary cannot link without it, so `cargo test` needs the
flag.

## Architecture rules

1. **No numeric logic in Python.** `python/tsxtract/__init__.py` is a
   pass-through with docstrings; all math lives in `src/features/`.
2. **No panic may cross the FFI boundary.** Fallible steps return
   `Result<_, TsxError>`; `src/error.rs` is the single conversion point to
   `PyErr`.
3. **Structural errors and NaN values stay separate.** `TsxError` describes
   shapes and layout, never values — see the [NaN policy](nan-policy.md).

## Adding a feature

The 33-feature set is closed on purpose. Open a **New feature proposal** issue
and get agreement before writing code. `NAMES` in `src/features/mod.rs` is the
single source of truth for column order — append at the end, never insert in the
middle.

## Versioning policy

`feature_names()` order and length are public API. Reordering, renaming, or
removing a feature is a **major** bump; appending one at the end is a minor bump.
The full table is in the repository guide.
