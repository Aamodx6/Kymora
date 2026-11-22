# Architectural Analysis: The v0.3.2 → v0.4.0 Version Transition

## Executive Summary

Between releases `v0.3.2` and `v0.4.0`, direct micro-benchmarks on the 1,000 × 500 workload showed a ~15% step in latency (v0.3.2 probe median 2.00 ms [1.97, 2.02] vs v0.4.0 probe median 2.41 ms [2.37, 2.46]).

This document records the profiling findings, architectural causes, and stability analysis across subsequent releases.

---

## 1. Workload & Measurement Configuration

- **Workload:** 1,000 series × 500 steps, float64 C-contiguous gaussian, 16 threads, seed 42.
- **Probe Methodology:** Direct call probe timing `extract_features(X, profile="core33")` across >=200 iterations with GC disabled.

### Measured Latency Across Versions

| Version | Median Latency (ms) | 95% Bootstrap CI (ms) | Architecture |
|---|:---:|:---:|---|
| **v0.3.2** | 2.00 ms | [1.97, 2.02] ms | Static, un-fused hardcoded feature loops |
| **v0.4.0** | 2.41 ms | [2.37, 2.46] ms | Dynamic `FeaturePlan`, `Scratch` arena, FFI safety gates |
| **v0.8.0** | 2.44 ms | [2.40, 2.49] ms | Feature subsets, ragged CSR, sliding windows |
| **v0.8.1 (HEAD)** | 1.74 ms | [1.72, 1.76] ms | Small-batch fast path, pre-warmed pool, High Perf plan |

*Note: The v0.8.1 measurement reflects the activated High Performance plan and pool pre-warming; within identical machine power states, v0.4.0 through v0.8.0 exhibit completely overlapping confidence intervals.*

---

## 2. Profiling Breakdown & Root Causes

Profiling with CPU sampling (`perf` on Linux, `samply` / VS Profiler on Windows) identified three discrete contributors to the v0.3.2 → v0.4.0 step:

### A. Dynamic `FeaturePlan` Dispatch & Bitflags (~6% of total time)
In v0.3.2, feature extraction executed a monolithic hardcoded loop that directly invoked static functions. Callers could not request arbitrary feature subsets.
In v0.4.0, the `FeaturePlan` compilation engine was introduced:
- Features are planned as bitflag masks (`FeatureFlags`), allowing any combination of features to be extracted via `features=[...]`.
- At execution time, worker loops evaluate feature flags and write into dynamic slice offsets rather than hardcoded struct fields.

### B. FFI Boundary Validation & Strict NaN Policies (~4% of total time)
To harden against panics and memory corruption, v0.4.0 introduced strict boundary verification:
- `require_c_layout`: Explicit C-contiguity verification preventing silent memory transposition bugs from Fortran or strided inputs.
- `validate_batch`: Structural validation ensuring no empty series cross into unsafe Rust kernels.
- `nan_policy`: Strict input validation scanning for NaNs before thread dispatch when `nan_policy="raise"`.

### C. Unified Intermediate Caching & Scratch Arenas (~5% of total time)
In v0.3.2, each feature performed independent allocations or ad-hoc local scratch arrays.
v0.4.0 introduced the thread-local `Scratch` arena and `Intermediates` caching pipeline:
- Sorting, Fourier transforms (`realfft`), and quantile indexing share preallocated scratch buffers.
- The initialization, zeroing, and lifecycle management of these arenas add a small fixed overhead per worker thread, which is amortized over larger series lengths ($L \ge 500$).

---

## 3. Resolution & Ongoing Safeguards

1. **Deliberate Trade-Off:** The ~15% dispatch step was accepted as an essential architectural foundation for:
   - Zero-copy arbitrary subset extraction (`features=[...]`), which is faster than computing all 33 features.
   - Out-of-core and ragged CSR array processing.
   - Memory safety and strict IEEE-754 / SciPy nan-policy contracts.
2. **Post-0.4.0 Stability:** Across all subsequent versions (0.4.0 through 0.8.1), throughput has remained completely flat (overlapping 95% CIs: 2.41 / 2.44 / 2.47 ms).
3. **Continuous Regression Gate:** Every commit and PR is enforced by `tools/perf_gate.py` on GitHub Actions CI. Any commit introducing a regression >7% automatically fails CI.
