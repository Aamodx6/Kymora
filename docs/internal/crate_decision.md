# Rust Crate Workspace Decision Record (Phase 6)

**Date:** 2026-11-22  
**Target:** v0.8.2 Launch  
**Decision:** **Retain Single-Crate Layout for v0.8.2; Schedule Workspace Split for v0.9.0**  
**Action:** **STOP at human gate before publishing to crates.io**

---

## 1. Context & Objective

Phase 6 of the Kymora launch preparation evaluated splitting the repository into a multi-crate Cargo workspace:
- `crates/kymora-core`: Pure Rust library with zero Python or NumPy dependencies, exposing `extract_core33(&[f64]) -> [f64; 33]`, with Rayon optional behind a `parallel` feature flag.
- `crates/kymora-py`: PyO3 wrapper crate compiling to `kymora._core` for the Python package.

The objective was to determine whether this workspace split could be completed cleanly and safely for v0.8.2 without jeopardizing wheel builds, ABI3 stability, sdist validation, or launch readiness.

---

## 2. Decision & Rationale

**Decision:** We retain the existing single-crate layout (`kymora` with `crate-type = ["cdylib", "rlib"]`) for the v0.8.2 release, and formally schedule the pure-Rust `kymora-core` workspace split for **v0.9.0**.

### Key Technical Blockers & Risks for v0.8.2:

### A. Maturin Sdist & CI Wheel Packaging Integrity
- Maturin packages single-crate repositories by placing `Cargo.toml`, `src/`, and metadata directly at the tarball root.
- The hardened release workflow (`.github/workflows/wheels.yml`) and `verify_clean_install.py` execute strict sdist verification:
  ```bash
  tar -tzf dist/*.tar.gz | grep "src/"
  python -m pip install dist/*.tar.gz
  ```
- Converting to a workspace requires moving Rust files to `crates/kymora-py` and configuring `pyproject.toml` with `manifest-path = "crates/kymora-py/Cargo.toml"`.
- In Maturin workspace packaging, sdist generation includes workspace root files and relative path dependencies, changing the archive layout. Introducing this structural change right before the 0.8.2 launch risks breaking source installs for Linux distributions and non-wheel platforms.

### B. Tight Coupling of Scratch Buffers & Rayon Parallelism
- The existing execution pipeline (`src/exec.rs`, `src/pipeline.rs`, `src/scratch.rs`) passes thread-local scratch buffers across Rayon work-stealing tasks.
- In `src/ffi.rs`, PyO3 buffers are borrowed as raw slices (`&[f64]`) and passed directly into the Rayon parallel engine.
- A clean `kymora-core` must separate:
  1. Pure single-series mathematical evaluators (`extract_one_core33(&[f64])`).
  2. Batch memory managers and thread-pool execution policies.
- Attempting to hastily decouple this state in under 2 hours risks introducing subtle numerical or concurrency regressions into a codebase that currently has 310 passing unit tests and 100% numerical parity against NumPy/SciPy.

### C. Local Build Script Blocking (os error 4551)
- Under the maintainer's Windows environment (Windows Application Control policy), executing newly compiled `build-script-build` binaries in `target/debug/build/...` fails with `os error 4551`.
- Running `cargo publish --dry-run` or building pure Rust test binaries locally requires compiling host build scripts (e.g. `crossbeam-epoch`, `libc`, `rayon-core`).
- Attempting workspace restructuring without local `cargo check` / `cargo test` iteration creates unnecessary friction and relies entirely on remote CI cycles.

---

## 3. Migration Roadmap for v0.9.0

The workspace split is fully scoped and scheduled for the v0.9.0 milestone:

### Target Directory Layout:
```
Kymora/
├── Cargo.toml                   # Workspace root
├── crates/
│   ├── kymora-core/             # Pure Rust library (crates.io package)
│   │   ├── Cargo.toml
│   │   ├── README.md
│   │   └── src/
│   │       ├── lib.rs
│   │       ├── features/        # Statistical, temporal, spectral kernels
│   │       ├── kernels/         # SIMD / Welford accumulators
│   │       └── plan.rs          # Evaluation plan & feature selection
│   │
│   └── kymora-py/               # PyO3 Python extension module
│       ├── Cargo.toml           # Depends on kymora-core
│       └── src/
│           ├── lib.rs
│           └── ffi.rs           # NumPy pointer borrowing & GIL release
│
├── python/kymora/               # Python package source
└── pyproject.toml               # Configured with manifest-path
```

### Planned `kymora-core` API Contract:
```rust
// Pure scalar single-series extraction (no heap allocation, no threads)
pub fn extract_core33(series: &[f64]) -> [f64; 33];

// Configurable batch extraction with optional Rayon parallelism
#[cfg(feature = "parallel")]
pub fn extract_batch(
    series: &[&[f64]], 
    profile: Profile, 
    n_jobs: Option<usize>
) -> Vec<Vec<f64>>;
```

### Feature Flags in `kymora-core`:
- `default = ["std", "parallel", "realfft"]`
- `parallel`: Enables Rayon multi-threading.
- `realfft`: Enables spectral features using `realfft`.
- `no_std` (future): Micro-controller and bare-metal support with scalar FFT fallback.

---

## 4. Release Protocol & Human Gates

In accordance with global release engineering rules:
- **No crates.io publication** will be executed for v0.8.2.
- **No git tags** (`v*`) will be pushed without an explicit instruction from the user.
- Kymora v0.8.2 will ship as a verified PyPI Python package with native binary wheels across all tier-1 platforms.
- `kymora-core` will be published to crates.io upon completion of the v0.9.0 workspace split.
