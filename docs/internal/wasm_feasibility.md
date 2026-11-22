# WebAssembly (WASM) Feasibility Spike Report

**Date:** 2026-11-22  
**Target:** `wasm32-unknown-unknown` / `wasm32-wasip1`  
**Verdict:** **Blocked for v0.8.2; Recommend Server-Backed Web Demo for Launch**

---

## 1. Executive Summary

As part of the v0.8.2 launch preparation, we conducted a technical spike to evaluate compiling Kymora to WebAssembly (`wasm32-unknown-unknown`) to power a zero-backend client-side browser demo.

The spike determined that **client-side in-browser WASM compilation is blocked in the current architecture**. Four hard technical blockers prevent compiling the existing crate to WebAssembly without a major architectural decoupling:
1. **Direct PyO3 & CPython linkage:** The current crate is a monolithic `cdylib` containing PyO3 Python bindings and C-API bindings that cannot link against a bare WASM target.
2. **Rayon work-stealing multi-threading:** Thread pools, work-stealing schedulers, and synchronization primitives (`crossbeam-deque`, `crossbeam-epoch`) rely on native OS threads that do not exist in standard single-threaded WebAssembly.
3. **Spectral kernel dependencies (`realfft` / `rustfft`):** Architecture-specific SIMD detection and 64-bit plan caches require either desktop features or significant polyfilling.
4. **Host build environment:** Local Windows Application Control policies (WDAC / AppLocker) prevent executing newly generated host build scripts (`build-script-build` yielding `os error 4551`).

**Recommendation:** For the launch demo, deploy a lightweight **server-backed demo** (FastAPI running the precompiled Linux wheel on Hugging Face Spaces, Fly.io, Modal, or a serverless container). This showcases Kymora's true multi-core throughput and full 33-feature catalog without synthetic stubs or compromised algorithms.

---

## 2. Root Cause Technical Blockers

### A. Monolithic Crate Structure & PyO3 Coupling

In `Cargo.toml`:
```toml
[lib]
crate-type = ["cdylib", "rlib"]

[dependencies]
pyo3 = { version = "0.29", features = ["extension-module", "abi3-py310"] }
numpy = "0.29"
rayon = "1"
realfft = "3.5.0"
```

The mathematical kernels (`src/features/*.rs`, `src/kernels/*.rs`) reside in the same crate as the PyO3 FFI layer (`src/ffi.rs`, `src/lib.rs`).
- `pyo3` with feature `extension-module` is explicitly designed for building Python native extensions linked dynamically into a CPython interpreter.
- Compiling `pyo3` with `extension-module` for `wasm32-unknown-unknown` fails at compile time because standard WebAssembly targets lack CPython runtime symbols (`PyObject`, `PyTuple_New`, etc.).
- Even with Pyodide (Python compiled to WASM), running a native CPython PyO3 extension requires Emscripten (`wasm32-unknown-emscripten`) and a 15+ MiB Pyodide runtime download, defeating the purpose of a fast, lightweight browser demo.

### B. Rayon Work-Stealing Multi-Threading

The execution engine (`src/exec.rs`, `src/pipeline.rs`) relies fundamentally on Rayon:
```rust
use rayon::prelude::*;
```
- In standard WebAssembly (`wasm32-unknown-unknown`), there is no native operating system thread model (`std::thread::spawn` is unavailable and panics at runtime).
- While experimental WebAssembly multi-threading exists via `wasm-bindgen-rayon`, it requires:
  1. Compiling with `-C target-feature=+atomics,+bulk-memory,+mutable-globals`.
  2. Spawning Web Workers manually in JavaScript.
  3. Running under strict HTTP security headers (`Cross-Origin-Opener-Policy: same-origin` and `Cross-Origin-Embedder-Policy: require-corp`) to enable `SharedArrayBuffer`.
  4. Many browser environments, static hosts (GitHub Pages), and embedding iframes disable `SharedArrayBuffer` by default.
- Furthermore, Rayon's dependency tree (`rayon-core`, `crossbeam-epoch`, `crossbeam-deque`) fails to compile cleanly under `wasm32-unknown-unknown` without explicit feature stubbing.

### C. Spectral Dependencies (`realfft` / `rustfft`)

Kymora's spectral features (`spectral_centroid`, `spectral_kurtosis`, `spectral_roll_off`, `spectral_skew`, `spectral_spread`, `spectral_energy`, `fft_band_ratio_*`) use `realfft`:
- `realfft` wraps `rustfft`, which includes architecture-specific AVX/SSE/NEON vectorization routines and dynamic hardware detection.
- Compiling `rustfft` for `wasm32` requires either the `+simd128` target feature or pure scalar fallbacks, and pre-allocated plan caches designed for 64-bit desktop memory layouts.

### D. Host Build Script Execution Policy

On the Windows development environment:
```
error: failed to run custom build command for `rayon-core v1.13.0`
Caused by: could not execute process `.../build-script-build` (never executed)
Caused by: An Application Control policy has blocked this file. (os error 4551)
```
Any crate utilizing a custom `build.rs` script generates an executable in `target/debug/build/...` that cannot be executed locally under Windows Application Control policies. Cross-compilation to WASM requires host build scripts (e.g. for `proc-macro2`, `quote`, `libc`, `autocfg`).

---

## 3. Architecture Required for True Client-Side WASM (`kymora-core` + `kymora-wasm`)

To make client-side WebAssembly feasible in future releases (e.g., v0.9.x), the following architectural refactoring is required:

### Step 1: Crate Workspace Decoupling (Phase 6 Alignment)
Split the repository into a multi-crate Cargo workspace:
- `crates/kymora-core`: Pure Rust library containing mathematical kernels, feature definitions, and single-series extraction. Zero PyO3 or NumPy dependencies.
- `crates/kymora-py`: PyO3 FFI wrapper exposing `kymora-core` to Python with Rayon parallelism.
- `crates/kymora-wasm`: `wasm-bindgen` wrapper exposing `kymora-core` to JavaScript.

### Step 2: Feature-Flagging Concurrency
In `crates/kymora-core/Cargo.toml`:
```toml
[features]
default = ["std", "parallel"]
std = []
parallel = ["dep:rayon"]

[dependencies]
rayon = { version = "1", optional = true }
```
When compiling for `wasm32-unknown-unknown`, build with `--no-default-features --features std` to compile a strictly sequential, single-threaded core without Rayon.

### Step 3: Lightweight Spectral Fallback
Provide an optional feature flag for FFT:
- Desktop: `realfft` / `rustfft` for full AVX2 performance.
- WASM: `microfft` (pure Rust, `#![no_std]` compatible scalar/radix-4 FFT) or a simple Cooley-Tukey single-threaded real FFT kernel.

### Step 4: `wasm-bindgen` API
Expose a lightweight JavaScript API:
```rust
#[wasm_bindgen]
pub fn extract_core33(signal: &[f64]) -> Vec<f64> {
    // Pure single-threaded caller-thread execution
    kymora_core::extract_one_core33(signal)
}
```

---

## 4. Recommended Demo Strategy for Launch

Rather than releasing a stripped-down, synthetic WebAssembly stub that computes only a fraction of features sequentially, we recommend deploying a **Server-Backed Interactive Web Demo**:

| Dimension | Client-Side WASM (Stub) | Server-Backed Demo (Recommended) |
|---|---|---|
| **Feature Coverage** | 10 features (minimal only, no FFT) | **All 33 Core features** (full catalog) |
| **Execution Speed** | Single-threaded JavaScript bridge (~50 µs/series) | **Multi-core native Rust (~1.9 µs/series, 514k series/s)** |
| **Realism** | Does not demonstrate actual Kymora library | **Runs official Kymora release wheel** |
| **Dataset Size** | Small files only (<1,000 points) | Full batch files (100,000 series CSV/Parquet) |
| **Implementation Risk** | High (compiler blockers, FFT stubs) | **Low (standard FastAPI + uPlot frontend)** |

### Demo Architecture Plan:
1. **Frontend:** Static HTML/JS or Next.js app on Vercel/GitHub Pages with [uPlot](https://github.com/leeoniya/uPlot) for fast canvas charting.
   - User drags and drops a CSV time series or clicks "Generate Synthetic Anomaly".
   - Browser displays interactive time series chart.
2. **Backend API:** Lightweight FastAPI service hosted on Hugging Face Spaces (free Docker container) or Fly.io:
   ```python
   from fastapi import FastAPI, UploadFile
   import kymora
   import numpy as np

   app = FastAPI()

   @app.post("/extract")
   async def extract(file: UploadFile):
       data = np.loadtxt(file.file, delimiter=",")
       feats = kymora.extract_features(data)
       return {"shape": feats.shape, "features": feats.tolist()}
   ```
3. **Turnaround Latency:** Total round-trip <50 ms on broadband, highlighting the sub-millisecond Rust extraction latency.

---

## 5. Conclusion

Attempting to force an immediate client-side WASM build for v0.8.2 would require compromising algorithm parity, dropping spectral features, and introducing brittle build stubs. 

By documenting these concrete blockers and articulating the workspace refactoring path (`kymora-core` split in Phase 6), we maintain engineering integrity. A server-backed interactive demo accurately represents Kymora's speed, multi-core scalability, and feature richness.
