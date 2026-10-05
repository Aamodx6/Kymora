# Kymora Hardening — Status Tracker

**Branch:** `hardening/kymora-v-next`
**Last updated:** 2026-10-05T13:40Z

## Legend
- ✅ Done
- 🔄 In progress
- ⬜ Not started
- ⏭️ Skipped (with reason)
- 🚫 Blocked (with reason)

## Phase 0: Setup
| Task | Status | Notes |
|------|--------|-------|
| Read all ground-rule files | ✅ | CLAUDE.md, arch.md, CLAIMS.md, CHANGELOG.md, Cargo.toml, pyproject.toml, Makefile, workflows, F1_REPORT.md |
| Create branch | ✅ | `hardening/kymora-v-next` |
| Write PLAN.md | ✅ | |
| Write STATUS.md | ✅ | This file |
| Create OWNER_DECISIONS.md | ✅ | |

## Phase 1: Benchmark Credibility
| Task | Status | Commit | Notes |
|------|--------|--------|-------|
| 1.1 Equal-feature mapping | ✅ | | `docs/benchmarks/feature_mapping.md` from frozen `benchmarks/agreement/feature_map.json`; parity re-verified 2026-10-05 (`2026-10-05_equal_feature/parity.json`: TSFEL/tsfresh/numba/numpy all EXACT) |
| 1.2 Benchmark shared features | ✅ | | `benchmarks/suites/equal_feature.py` (parity + bench modes); 2026-10-05 run: 4 shapes × {tsfel 13, tsfresh 13, numba 33, numpy 33}, interleaved rounds, bootstrap CIs; kymora wins all 16 rows (3.4×–1,693.8×). Artifacts: `2026-10-05_equal_feature/` + `EQUAL_FEATURE_REPORT.md` |
| 1.3 Re-measure † rows | ✅ | | `benchmarks/suites/remeasure_readme.py`; 2026-10-05 run: profiles (minimal 1.20 ms / core33 2.88 / extended 10.10 / full 11.10), scaling (peak 4.25× @ 16T), memory (kymora 100k×500 +417.7 MiB peak, extraction +32.3; tsfresh +289.8/+449.5 @1k/10k); tsfresh 100k cell still PENDING (multi-hour). Fixed `default_fc_parameters` string bug |
| 1.4 Numba baseline + losses | ✅ | 7ec0f66, with 1.5 | Evidence committed (B3/COMPETITOR/L1 reports + raw json); "Where Kymora is slower" README section + numba/equal-feature rows delivered with task 1.5 |
| 1.5 Rewrite README bench section | ✅ | | Median-first: equal-feature table (like-for-like), raw-time F1 table, honest losses section; fresh profile/scaling/memory tables (2026-10-05); stale † rows removed; phantom feature list corrected to actual 33-name catalog; CLAIMS.md rows extended so check_claims passes |
| 1.6 bench.yml CI workflow | ✅ | | Manual dispatch + weekly cron; ubuntu + macos-14; parity gate + reduced equal-feature bench + re-measure; results uploaded as artifacts, never auto-copied into README/CLAIMS |
| 1.7 Propagate figures + check_claims.py | ✅ | | `tools/check_claims.py`: extracts numeric claims from README/docs/landing and verifies traceability to CLAIMS.md (1% tolerance or exact match); TS comments skipped; 3 landing Hero demo values KNOWN-PENDING (task 8.4). Gate: exit 0. README figures propagated; docs/landing tables still pending (tracked in CLAIMS) |

## Phase 2: Streaming Correctness + Performance
| Task | Status | Commit | Notes |
|------|--------|--------|-------|
| 2.1 Audit StreamingExtractor O(1) | ✅ | | Anchored shifted power sums + drift guard (0.25σ) + K=4096 re-anchor; `compute_fast` O(1), inf-window exact fallback; `anchor_interval` ctor param (additive); W=1 now valid; 8 Rust tests incl. quantized-exact proof on 1e9-offset |
| 2.2 Document O(1) vs O(W) | ✅ | | New docs/streaming.md (complexity + accuracy contract); README stale "two passes" fixed; api.md "100ns" replaced + anchor_interval signature |
| 2.3 Streaming vs batch tests | ✅ | | New tests/test_streaming_parity.py (44 tests): distributions × W, NaN/inf, W=1/2, anchor_interval, hypothesis; W=1 slope NaN fix; hypothesis-found stale-anchor abs_energy fix (constant-window W·first² shortcut) + sparse-spike regression test |
| 2.4 Per-push cost benchmark | ✅ | | B3 suite run (gates 6.5e-16..3e-14); artifact 2026-10-05_streaming/ + plot docs/img/; docs/streaming.md table; CLAIMS.md streaming section |

## Phase 3: Input Surface + Robustness
| Task | Status | Commit | Notes |
|------|--------|--------|-------|
| 3.1 NaN/Inf policy doc | ✅ | | docs/numerics.md canonical (nan-policy.md → pointer); `nan_policy` propagate(default)/raise on batch/ragged/sliding/mc/streaming; omit + unknown rejected with guidance; NaN errors bypass KymoraError (values≠structure) |
| 3.2 float32 support | ✅ | | Fixed FFI panic on f32+non-core33 (PanicException → ValueError); f32 gather for minimal/subsets; precision validated; f32≈f64 rtol 1e-4 (measured 8.8e-6); 9 tests |
| 3.3 Multivariate input | ✅ | | extract_features_mc accepts list of 2D (ragged T, uniform C) bit-identical to stacked 3D; ch{c}__{feature} blocks + cross verified vs batch; mc_df labeled; found silent-wrong on Fortran input/out (fixed in 3.4) |
| 3.4 Non-contiguous handling | ✅ | | Strict C-order gate on ALL borrows (fixed silent-wrong on Fortran mc input + Fortran out=); contiguous=error/copy + copy warning; copy bit-identical; stubs/docs updated |
| 3.5 Shape/dtype test matrix | ✅ | | tests/test_input_surface.py (layout/dtype/shape matrix, Fortran+copy, out=, never-panic fuzz) + tests/property/test_invariances.py (permutation/affine/monotonic); existing property suite covers the rest |

## Phase 4: sklearn / Ecosystem
| Task | Status | Commit | Notes |
|------|--------|--------|-------|
| 4.1 KymoraTransformer | ✅ | | python/kymora/sklearn.py (numpy-only core import preserved); 50/50 estimator checks pass; clone/pickle/pandas/polars output |
| 4.2 Optional extras | ✅ | | [pandas]/[polars]/[sklearn]/[all] in pyproject; core stays numpy-only |
| 4.3 sktime/aeon adapter | ✅ | | docs/examples/sktime_adapter.py verified vs sktime 1.2.0 (3 tests incl. sklearn pipeline on primitives output); aeon untested, marked in example |
| 4.4 py.typed + stubs + mypy | ✅ | | README quickstart uses in-package transformer; _core.pyi covers new params; mypy clean (5 files); CI typecheck installs .[all]; snippet gate green |

## Phase 5: Thread Scaling + Perf Regression
| Task | Status | Commit | Notes |
|------|--------|--------|-------|
| 5.1 Scaling plateau investigation | ✅ | | Plateau = P-core count (6) + E/SMT drag, not a bug; fixed per-call pool-build overhead (~200µs) with cached pools (small-call n_jobs 2.3×); bitwise thread-invariance test; analysis in docs/internal/thread_scaling.md |
| 5.2 Thread default | ✅ | | Keep default (None/global pool): capping would trade ~5% peak for platform-specific behavior; fresh scaling (12.16→2.78ms, peak 4.37×) consistent with 2026-10-05 artifact, no CLAIMS change; guidance in stubs + thread_scaling.md |
| 5.3 Bisect 0.3.2→0.4.0 | ✅ | | tools/perf_gate.py (median+Q1 rule, CV rerun, per-platform baselines) + CI perf-gate job + laptop baseline committed; per-commit bisect documented as deferred (F1 evidence + cross-day noise justification in thread_scaling.md appendix) |
| 5.4 Benchmark experiments | ✅ | | Worktree builds + same-session probes: spin-pool ±1% (bit-identical, no win), soa-4x −13% (bit-identical, slower); both stay quarantined; docs/internal/experiments.md; worktrees removed |

## Phase 6: Correctness Assurance
| Task | Status | Commit | Notes |
|------|--------|--------|-------|
| 6.1 Parity test suite | ⬜ | | |
| 6.2 Feature catalog docs | ⬜ | | |
| 6.3 Fuzz/proptest + unsafe audit | ⬜ | | |
| 6.4 Cross-platform CI | ⬜ | | |

## Phase 7: Identity, Packaging, Release
| Task | Status | Commit | Notes |
|------|--------|--------|-------|
| 7.1 URL/name grep | ⬜ | | |
| 7.2 CITATION.cff + metadata | ⬜ | | |
| 7.3 Release prep | ⬜ | | |
| 7.4 README sync + badges | ⬜ | | |
| 7.5 Security infrastructure | ⬜ | | |
| 7.6 patent/ documentation | ⬜ | | |

## Phase 8: Docs, Paper, Launch Assets
| Task | Status | Commit | Notes |
|------|--------|--------|-------|
| 8.1 Documentation refresh | ⬜ | | |
| 8.2 JOSS paper | ⬜ | | |
| 8.3 Launch kit | ⬜ | | |
| 8.4 Landing page | ⬜ | | |
