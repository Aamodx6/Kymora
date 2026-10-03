---
title: "Configuration & Environment Variables"
description: "Runtime controls, thread tuning, environment variables, and compilation flags for Tsxtract."
order: 12
section: "Reference"
---

Tsxtract has no configuration file and reads no library-specific environment variables: every call is fully described by its arguments. The tunable surface is therefore small — build flags at compile time and process-level thread controls at run time.

```python
import tsxtractor
print(tsxtractor.__version__)
print(len(tsxtractor.feature_names()))
```

```text
0.3.0
33
```

> [!NOTE]
> A repository-wide search of `src/` finds no environment-variable reads, thread-pool sizing, or global settings. Options below are exactly what the source evidences, plus one standard Rayon control flagged as unverified.

## Runtime options

| Name | Default | Effect | Example |
| :--- | :--- | :--- | :--- |
| `window` (`sliding_features`) | Required | Window length; `1 <= window <= len(X)` | `sliding_features(x, window=256, stride=64)` |
| `stride` (`sliding_features`) | `1` | Step between window starts | `sliding_features(x, window=256, stride=1)` |
| `window_size` (`StreamingExtractor`) | Required | Rolling capacity; must be `>= 2` | `StreamingExtractor(window_size=16)` |
| `X` dtype/layout (all entry points) | `float64` C-contiguous | Non-conforming buffers raise instead of copying | `np.ascontiguousarray(X, dtype=np.float64)` |

There is deliberately nothing else: no output-precision switch, no feature toggles, and no plugin registry. The 33-feature set is closed by design, and output is always float64.

## Environment variables

| Name | Default | Effect | Example |
| :--- | :--- | :--- | :--- |
| `RAYON_NUM_THREADS` | Core count | Caps Rayon worker threads process-wide (standard Rayon mechanism) | `RAYON_NUM_THREADS=4 python job.py` |

> [!WARNING]
> TODO(verify): `RAYON_NUM_THREADS` is honored by Rayon's default global pool, but no thread-count test or documentation exists in this repo and `src/` never references it. Treat pinned-thread benchmarks as unverified until a test covers them.

## Build flags

Release-profile settings come from `Cargo.toml`, and the recommended build commands from `CONTRIBUTING.md`:

| Name | Default | Effect | Example |
| :--- | :--- | :--- | :--- |
| `maturin develop --release` | Debug if flag omitted | Optimized native extension for local use | `maturin develop --release` |
| `cargo test --no-default-features` | N/A (test-only) | Disables `pyo3/extension-module` so test binaries link | `cargo test --no-default-features` |
| `[profile.release] lto = true` | Set in `Cargo.toml` | Link-time optimization for the shipped binary | Fixed at build |
| `[profile.release] codegen-units = 1` | Set in `Cargo.toml` | Single codegen unit, slower build, faster output | Fixed at build |

```bash
pip install maturin
maturin develop --release
```

```toml
[profile.release]
lto = true
codegen-units = 1
```

## Dependency pins

Version floors from `pyproject.toml` that constrain environments:

| Name | Default | Effect | Example |
| :--- | :--- | :--- | :--- |
| `requires-python` | `>=3.10` | Older interpreters cannot install the package | `python --version` |
| `numpy` | `>=1.24` | Minimum array runtime | `pip install "numpy>=1.24"` |
| `pandas` (extra) | `>=1.5` | Needed only for `extract_features_df()` | `pip install "tsxtract-rs[pandas]"` |
| `maturin` (build) | `>=1.14,<2.0` | Build backend for source builds | `pip install "maturin>=1.14,<2.0"` |

## See also

Where configuration questions usually lead next:

- [Installation](/docs/installation) — wheels, extras, and source builds.
- [Performance & Architecture](/docs/performance) — memory and threading behavior.
- [Contributing Guide](/docs/contributing) — full check suite for source changes.
