---
title: "Configuration & Environment Variables"
description: "Runtime controls, thread tuning, environment variables, and compilation flags for Tsxtract."
order: 12
section: "Reference"
---

Tsxtract has no configuration file. Per-call behavior is fully described by arguments, plus two `TSXTRACT_*` environment variables consumed by the wisdom tuner (`python/tsxtract/tune.py`; the Rust core itself reads no environment). The tunable surface is therefore small — call arguments at run time and build flags at compile time.

```python
import tsxtract
print(tsxtract.__version__)
print(len(tsxtract.feature_names()))
```

```text
0.6.0
33
```

> [!NOTE]
> A repository-wide search of `src/` finds no environment-variable reads, thread-pool sizing, or global settings. Options below are exactly what the source evidences, plus one standard Rayon control flagged as unverified.

## Runtime options

| Name | Default | Effect | Example |
| :--- | :--- | :--- | :--- |
| `profile` (`extract_features`, ...) | `"core33"` | Feature tier: `"minimal"` (10), `"core33"` (33), `"extended"` (143), `"full"` (543) | `extract_features(X, profile="minimal")` |
| `features` (batch entry points) | None | Explicit feature names or aliases; unknown names raise `ValueError` with close matches | `extract_features(X, features=["mean", "std"])` |
| `views` (batch entry points) | `("raw",)` | Multi-view transforms (`"raw"`, `"diff"`, `"diff2"`, `"detrend"`, `"znorm"`, `"abs"`, `"logret"`, `"rank"`); invariant features are pruned per view | `extract_features(X, views=["raw", "diff"])` |
| `n_jobs` (batch entry points) | None (all cores) | Worker thread count override | `extract_features(X, n_jobs=4)` |
| `out` (batch entry points) | None (allocate) | Pre-allocated C-contiguous buffer for zero-allocation writes | `extract_features(X, out=buf)` |
| `precision` (`extract_features`) | `"float64"` | Compute precision (`"float64"` or `"float32"`) | `extract_features(X, precision="float32")` |
| `out_dtype` (`extract_features`) | `"float64"` | Output dtype; `"float32"` halves output memory | `extract_features(X, out_dtype="float32")` |
| `window` (`sliding_features`) | Required | Window length; `1 <= window <= len(X)` | `sliding_features(x, window=256, stride=64)` |
| `stride` (`sliding_features`) | `1` | Step between window starts | `sliding_features(x, window=256, stride=1)` |
| `window_size` (`StreamingExtractor`) | Required | Rolling capacity; must be `>= 2` | `StreamingExtractor(window_size=16)` |
| `X` dtype/layout (all entry points) | `float64` C-contiguous (`float32` also accepted) | Non-conforming buffers raise instead of copying | `np.ascontiguousarray(X, dtype=np.float64)` |

There is deliberately nothing else: no feature toggles and no plugin registry. The `core33` set is frozen by design; new features are append-only.

## Environment variables

| Name | Default | Effect | Example |
| :--- | :--- | :--- | :--- |
| `TSXTRACT_WISDOM` | unset (enabled) | `off`/`0`/`false` disables loading the cached `tune()` wisdom file | `TSXTRACT_WISDOM=off python job.py` |
| `TSXTRACT_POOL` | unset (Rayon) | Recorded by `tune()` when comparing pool variants | Set by `tune()` during benchmarking |
| `RAYON_NUM_THREADS` | Core count | Caps Rayon worker threads process-wide (standard Rayon mechanism) | `RAYON_NUM_THREADS=4 python job.py` |

> [!NOTE]
> `TSXTRACT_WISDOM` selects the cache file by machine signature (`platform.machine`-`platform.processor`) and ignores mismatched hosts. The cached `pool` recommendation is currently advisory: the alternative spin backend lives in `experiment/spin-pool`, so main runs the Rayon pool. `RAYON_NUM_THREADS` is honored by Rayon's default global pool, but no thread-count test exists in this repo — treat pinned-thread benchmarks as unverified until a test covers them.

## Build flags

Release-profile settings come from `Cargo.toml`, and the recommended build commands from `CONTRIBUTING.md`:

| Name | Default | Effect | Example |
| :--- | :--- | :--- | :--- |
| `maturin develop --release` | Debug if flag omitted | Optimized native extension for local use | `maturin develop --release` |
| `cargo test --no-default-features` | N/A (test-only) | Disables `pyo3/extension-module` so test binaries link | `cargo test --no-default-features` |
| `[profile.release] lto = "fat"` | Set in `Cargo.toml` | Link-time optimization for the shipped binary | Fixed at build |
| `[profile.release] codegen-units = 1` | Set in `Cargo.toml` | Single codegen unit, slower build, faster output | Fixed at build |

```bash
pip install maturin
maturin develop --release
```

```toml
[profile.release]
lto = "fat"
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
