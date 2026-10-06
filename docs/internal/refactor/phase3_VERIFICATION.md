# Phase 3 verification — Rust core cleanup (2026-10-04)

## Deletion evidence (reference search, zero non-def hits outside own file)

| Removed | Location | Superseded by / note |
|---|---|---|
| `n_features`, `extract_rows`, `build_matrix`, `extract_windows` (+ `features`/`Array2`/`rayon` imports, 4× `allow(dead_code)`) | `src/extract.rs` | Pre-plan legacy path (`165d149` era); live paths use `exec`+`pipeline` |
| `extract_into_slice`, `extract_windows_into_slice`, `extract_ragged_csr` (non-plan f64) | `src/exec.rs` | Superseded by `_plan` variants (v0.4.0); `extract_into_slice` had only dead callers (cascade) |
| stray `allow(dead_code)` on used `count()` | `src/features/streaming.rs` | `count()` is called from `ffi.rs:790` — attribute was vestigial |

Kept deliberately (fresh `875fd24` Zenith-session experiments — owner wire-or-delete,
NEEDS-OWNER #7/#8): `src/pool.rs` (whole module, `TSXTRACT_POOL` unread),
`aos_to_soa_4x`/`pass1_soa_4x`/`pass2_soa_4x`/`autocorr_soa_4x`
(`src/kernels/reduce.rs`), `run_core33_f32_out32` (`src/pipeline.rs`).
`fast_feature_names` ×2 are live Python API (`#[staticmethod]`, covered by
`test_phase5.py`/`test_zenith.py`) — regex false positive, untouched.

Adjacent gap found (not fixed — docs=Phase 5, Python=Phase 4): `TSXTRACT_POOL`
is set by `tune.py` and documented in `docs/api.md:313-320`, but no Rust code
reads it (`should_use_rayon` uncalled). `tune_pool()` spin-vs-rayon timings
therefore measure the same rayon path.

## Unsafe scoping (arch I8, amended)

- Before: 12 identical `unsafe { out_arr.as_slice_mut() ... }` blocks in `ffi.rs`.
- After: 2 helpers (`out_slice_mut`, `out_slice_mut_f32`) with one documented
  SAFETY contract; `#[allow(clippy::mut_from_ref)]` with justification
  (numpy hands `&mut` out of a shared `Bound` — that is the helper's purpose).
- `#![deny(unsafe_code)]` in all 17 other modules (not in `ffi.rs`, not in
  `kernels/*` = arch-blessed SIMD home, currently unsafe-free).
- Negative test: probe `unsafe {}` in `scratch.rs` fails the build
  (`error: usage of an unsafe block`); probe fully reverted (verified clean).
- `cargo doc --no-deps`: 0 warnings (fixed 6 pre-existing `x[i]` link parses
  + 1 new redundant link). Added missing module docs (`pipeline.rs`,
  `features/mod.rs`).

## Verification output (final tree)

- `cargo test`: 16 passed, 0 failed
- `cargo clippy --all-targets -- -D warnings`: exit 0
- `cargo fmt --check`: exit 0
- `cargo doc --no-deps`: 0 warnings
- `pytest tests -q` (against rebuilt release wheel): 138 passed, 0 warnings
- `feature_names()` sha256: `8a1e2794…431af` MATCH
- Perf (release `--release` wheel, same script): BEFORE best 1.2 ms →
  AFTER min 1.1 ms / median 1.3 ms on core33 200×1000; 4.0 ms on 1000×1000;
  11.4 ms on 200×10000. No regression (live-path codegen untouched:
  `pipeline.rs`/`kernels/*` diffs are doc comments + deny attributes only).
- `benchmarks/smoke.py`: 10/10 (tracked results reverted)
- `mypy`: 10 errors = Phase 0 baseline (Phase 4 item); `mkdocs --strict`: exit 0

## Commits

- `89bc857` dead-code removal + unsafe centralization (−133 net lines)
- `b105bde` deny attributes + module docs + rustdoc fixes
- (this phase) arch.md I8 + §4.1 layout corrected to post-cleanup reality
