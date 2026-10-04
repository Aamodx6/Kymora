---
title: "Installation"
description: "Install Tsxtract wheels, build from source, verify the install, and fix platform issues."
order: 2
section: "Start here"
---

Install Tsxtract from PyPI as precompiled wheels with no Rust toolchain required, then verify the native extension loads. Standard use needs only Python 3.10+ and NumPy on a 64-bit OS.

```bash tab="pip"
pip install tsxtract
```

```bash tab="uv"
uv add tsxtract-rs
```

```bash tab="conda"
conda install -c conda-forge tsxtract-rs
```

> [!NOTE]
> The PyPI package uses `abi3` wheels for Python 3.10+, so one wheel per architecture covers CPython 3.10 through 3.13. This matches the `abi3-py310` feature in `Cargo.toml` and `requires-python = ">=3.10"` in `pyproject.toml`.

## Requirements

| Component | Minimum | Recommended | Notes |
| :--- | :--- | :--- | :--- |
| **Python** | 3.10 | 3.11, 3.12, or 3.13 | CPython only; `requires-python = ">=3.10"` in `pyproject.toml` |
| **Linux** | 64-bit `x86_64` | Ubuntu 22.04+, Debian 12+, or RHEL 9+ | Prebuilt wheels for `x86_64` and `aarch64` |
| **macOS** | Apple Silicon (`arm64`) or Intel (`x86_64`) | Recent macOS release | Native wheels for both architectures |
| **Windows** | Windows 10 64-bit | Windows 11 or Server 2022 | Native wheel for `x86_64` |
| **NumPy** | `>=1.24` | `>=1.26` or NumPy 2.x | Only required runtime dependency |
| **pandas** | Optional, `>=1.5` | `>=2.0` | Needed solely for `extract_features_df()` |

> [!WARNING]
> TODO(verify): exact minimum OS releases, glibc/manylinux tags, and conda-forge availability. Wheel targets above come from the README; `pyproject.toml` pins only Python and NumPy, so treat the conda channel and precise OS floors as unverified until checked against PyPI.

## Optional extras

The core install stays NumPy-only, so install extras only for the workflow you need:

```bash tab="pip"
pip install "tsxtract-rs[pandas]"
pip install "tsxtract-rs[test]"
pip install "tsxtract-rs[bench]"
```

```bash tab="uv"
uv add "tsxtract-rs[pandas]"
uv add "tsxtract-rs[test]"
```

```bash tab="conda"
conda install -c conda-forge tsxtractor pandas
```

Available extras and their contents:

- **Pandas support:** `"tsxtractor[pandas]"` pulls `pandas>=1.5` for `extract_features_df()`.
- **Test suite:** `"tsxtractor[test]"` pulls `pytest`, `scipy`, `hypothesis`, and `pandas`.
- **Benchmarks:** `"tsxtractor[bench]"` pulls `pandas`, `tsfresh`, `pycatch22`, and `tsfel`.
- **Docs tooling:** the `docs` extra pulls `mkdocs` and `mkdocs-material` for local docs builds.

## Verify installation

Run this snippet to confirm the version, the 33-feature registry, and a real extraction:

```python
import numpy as np
import tsxtractor
print("tsxtractor version:", tsxtractor.__version__)
print("Total registered features:", len(tsxtractor.feature_names()))
sample = np.linspace(0.0, 10.0, 100, dtype=np.float64).reshape(1, -1)
result = tsxtractor.extract_features(sample)
print("Test feature vector shape:", result.shape)
print("Computed mean value:", result[0, 0])
```

```text
tsxtractor version: 0.3.0
Total registered features: 33
Test feature vector shape: (1, 33)
Computed mean value: 5.0
```

## Build from source

Build from source when developing features, targeting an architecture without prebuilt wheels, or customizing compiler flags. The steps below follow `CONTRIBUTING.md` and the README development section.

### Prerequisites

- **Python 3.10+:** with development headers available to the compiler.
- **Stable Rust toolchain:** install from [rustup.rs](https://rustup.rs/) when `cargo` is missing.
- **Maturin:** the build backend pinned as `maturin>=1.14,<2.0` in `pyproject.toml`.

### Compile steps

```bash
git clone https://github.com/Aamod007/Tsxtract.git
cd Tsxtract
python -m venv .venv
source .venv/bin/activate
pip install maturin
pip install -e ".[test]"
maturin develop --release
pytest tests/
cargo test --no-default-features
```

> [!IMPORTANT]
> Always compile with `--release`. Debug builds run roughly an order of magnitude slower and misrepresent real throughput. `cargo test` needs `--no-default-features` because the `extension-module` feature omits the Python link Frost test binaries require.

## Upgrade

Move to the latest published release with your usual manager:

```bash tab="pip"
pip install --upgrade tsxtract-rs
```

```bash tab="uv"
uv lock --upgrade-package tsxtract-rs
uv sync
```

```bash tab="conda"
conda update -c conda-forge tsxtract-rs
```

## Uninstall

Remove the library cleanly when switching environments:

```bash tab="pip"
pip uninstall -y tsxtract-rs
```

```bash tab="uv"
uv remove tsxtract-rs
```

```bash tab="conda"
conda remove tsxtract-rs
```

## Troubleshooting

### Wheel not found during install

- **Symptom:** `ERROR: Could not find a version that satisfies the requirement tsxtract-rs`.
- **Cause:** Python older than 3.10 or an unsupported architecture such as 32-bit x86.
- **Resolution:** check `python --version`, then recreate the environment on Python 3.10+.

### Missing Rust compiler from source builds

- **Symptom:** `can't find Rust compiler` or `cargo: command not found`.
- **Cause:** `pip` fell back to a source distribution because no wheel matched your platform.
- **Resolution:** install Rust via `rustup`, upgrade `pip` so it recognizes modern tags, or prefer a platform with prebuilt wheels.

### Windows C++ build tools missing

- **Symptom:** `error: Microsoft Visual C++ 14.0 or greater is required`.
- **Cause:** compiling from source on Windows needs native C++ link tooling.
- **Resolution:** install the Visual Studio Build Tools workload for desktop C++ development, or install the prebuilt wheel instead of building.

### Apple Silicon architecture mismatch

- **Symptom:** `mach-o file, but is an incompatible architecture (have 'x86_64', need 'arm64')`.
- **Cause:** an x86_64 Python under Rosetta 2 loading `arm64` wheels, or vice versa.
- **Resolution:** confirm with `python -c "import platform; print(platform.machine())"`, then install a native `arm64` Python via Homebrew or pyenv.

### Import fails with missing library or symbol

- **Symptom:** `ImportError: DLL load failed` on Windows or `undefined symbol` on Linux.
- **Cause:** stale virtual environment paths or an outdated system C runtime.
- **Resolution:** recreate the virtual environment, update the OS runtime, and reinstall `tsxtract-rs` plus `numpy>=1.24`.

### Proxy and corporate firewall timeouts

- **Symptom:** `SSLError` or connection timeouts fetching wheels from PyPI.
- **Cause:** enterprise proxies intercepting TLS or blocking the package index.
- **Resolution:** pass your proxy and certificate bundle explicitly during install.

```bash
pip install --proxy http://proxy.corporate.internal:8080 --cert /path/to/ca-bundle.crt tsxtract-rs
```

```text
Successfully installed tsxtract-rs-0.3.2
```

### Contiguous and dtype errors at call time

- **Symptom:** `ValueError` mentioning `ascontiguousarray`, or `TypeError` mentioning `astype`.
- **Cause:** strided views or non-float64 dtypes, which the zero-copy core rejects by design.
- **Resolution:** normalize once with `np.ascontiguousarray(X, dtype=np.float64)` before extracting.

## Next steps

With a verified install, move to hands-on extraction and internals:

- [Quickstart](/docs/quickstart) — first feature matrices and a trained classifier.
- [Core Concepts](/docs/core-concepts) — memory layout, dtypes, and determinism.
- [FAQ & Troubleshooting](/docs/faq) — runtime errors beyond installation.
