# Install

```bash
pip install tsxtract-rs
```

That is the whole story on Linux (x86_64, aarch64), macOS (Intel and Apple
Silicon), and Windows (x86_64) for Python 3.10 and newer. Wheels are built as
`abi3-py310`, so one wheel per platform serves every supported Python version and
no Rust toolchain is involved.

The only required runtime dependency is numpy (>= 1.24).

## Optional extras

| Extra | Installs | Needed for |
|---|---|---|
| `pandas` | pandas | `extract_features_df()` |
| `test` | pytest, scipy, hypothesis, pandas | running the test suite |
| `bench` | tsfresh, pycatch22, tsfel, pandas | running the comparison benchmark |
| `docs` | mkdocs, mkdocs-material | building this site |

```bash
pip install "tsxtract-rs[pandas]"
```

## Building from source

Needed only on a platform without a prebuilt wheel, or when working on the
library itself. Requires a [Rust toolchain](https://rustup.rs/):

```bash
git clone https://github.com/Aamodx6/Tsxtract
cd Tsxtract
python -m venv .venv && . .venv/bin/activate   # .venv\Scripts\activate on Windows
pip install maturin
pip install -e ".[test]"
maturin develop --release
pytest tests/
```

!!! warning "Build in release mode"
    `maturin develop` without `--release` produces an unoptimised debug build
    that is roughly an order of magnitude slower. Never benchmark a debug build.
