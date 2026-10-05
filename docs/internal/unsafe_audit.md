# Unsafe audit (Phase 6.3)

Rule (arch I8): `unsafe` appears only in `src/ffi.rs` (numpy buffer
boundary) and `src/kernels/` (designated SIMD home, currently unsafe-free).
Every other module carries `#![deny(unsafe_code)]`, enforced by rustc.

## Inventory (complete as of this writing)

Exactly two `unsafe` blocks exist in the tree. Verify with:

```
rg -n "unsafe" src/ --glob '!*deny*'
```

| # | Location | Code | SAFETY contract |
|---|---|---|---|
| U1 | `src/ffi.rs` `out_slice_mut` | `unsafe { arr.as_slice_mut() }` on `&Bound<PyArray2<f64>>` | Centralized helper; soundness rests on the documented call-site contract (C-contiguous, writeable, sole live Rust borrow until handed back, created under GIL, no aliasing with input). Enforced: `get_out_array` validates shape + C-order; contiguous or fresh-zeros only. |
| U2 | `src/ffi.rs` `out_slice_mut_f32` | `unsafe { arr.as_slice_mut() }` on `&Bound<PyArray2<f32>>` | Same contract as U1; only ever called on freshly allocated `zeros` arrays (no caller-supplied f32 `out=` exists), so aliasing is impossible by construction. |

Both carry `#[allow(clippy::mut_from_ref)]` with a comment explaining why
(numpy hands out `&mut` from a shared `Bound`).

## Clippy pedantic

`cargo clippy -- -W clippy::pedantic` is informational only: it reports
repo-wide style lints (single-char bindings, literal separators, doc
backticks) that would churn numerics to fix. The two unsafe helpers and
their contract docs are pedantic-clean. Full pedantic adoption is
explicitly out of scope; `-D warnings` (default lints) stays the gate.

## Fuzzing

- In-process (stable, all platforms): `src/proptest_checks.rs` —
  arbitrary hostile values/shapes/geometries over `compute_all`,
  `StreamingExtractor`, `FeaturePlan::build`, CSR ragged extraction.
- Coverage-guided (nightly, Linux CI): `fuzz/` (cargo-fuzz, libfuzzer).
  Run locally with a nightly toolchain: `cargo fuzz run compute_all --
  -max_total_time=300`. Minimized crashers become `proptest_checks`
  regression tests. Release protocol: ≥30 min per target before a minor
  or major release; corpus in `fuzz/corpus/` (do not commit crashers —
  minimize into regression tests instead).
