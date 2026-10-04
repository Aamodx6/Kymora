# Phase 8 verification — final gate run & refactor report (2026-10-04)

## Final gate suite (run on the completed tree, wheel current with source)

| Gate | Result |
|---|---|
| `cargo test --no-default-features` | **16 passed**, 0 failed |
| `cargo clippy --no-default-features --all-targets -- -D warnings` | exit **0** |
| `cargo fmt --all -- --check` | exit **0** |
| `cargo doc --no-deps` | exit **0**, 0 warnings |
| `pytest tests -q -W error` | **138 passed**, 0 warnings (stricter than the `-q` baseline) |
| `feature_names()` sha256 | **MATCH** `8a1e2794…31af2e` (33 names) |
| `python scripts/validation_report.py` | **All features within tolerance**, exit 0 |
| `python -m mkdocs build --strict` | exit **0**, zero anchor diagnostics |
| `python -m mypy python/tsxtract` | **clean** (4 files; was 10 errors at baseline) |
| `landing: npm run build` | ✓ built in 32.83s (tsc clean) |
| Phase-record audit | phase1, 3–7 verification files + naming + deleted_files present (phase 0 = `baseline/SUMMARY.md`; phase 2 decisions live in REFACTOR_STATE D-series) |
| Residual claim scan (README/docs/landing/CONTRIBUTING) | no wrong dist names, no Aamod007 repo URLs, no false SIMD/spin/sub-microsecond claims — only REFACTOR_STATE meta-text and the deliberately-frozen `changelog.md` historical entries |

## Refactor summary (17 commits, `pre-refactor` tag → HEAD)

| Phase | What shipped |
|---|---|
| 0 | Baseline logs (later UTF-8 fixed), name inventory, state file |
| 1 | Package rename: import `tsxtract`, dist `tsxtract-rs`, crate `tsxtract`, shim; naming.md D-series |
| 2 | `benches/`→`benchmarks/` (53 files), tests subdirs, `insp/` deleted with evidence |
| 3 | Rust cleanup: −133 dead-code lines, unsafe centralized into 2 SAFETY-contracted helpers, `deny(unsafe_code)` in 17 modules, rustdoc 0 warnings, perf no-regression |
| 4 | `_core.pyi` completed, select typing fixed, **mypy 10 errors → clean**, stub surface runtime-verified |
| 5 | Claims cleanup (SIMD/spin/O(1)/sub-microsecond → measured reality: fast tier 1.8 µs), 2 anchors fixed by adding real sections, site_url→aamodx6, D13 docs/landing roles |
| 6 | Website: 4 false conda blocks removed (API-404 verified), 9 wrong dist names fixed (would hit unrelated JAX project), nav/links/figures 16/16, **#2 closed** (PyPI owned by `aamoddev11`) |
| 7 | Composite venv action wired (was untracked dup, ci×3+bench), docs.yml dead install path fixed, contributor files created (CoC dead link closed, SECURITY, CITATION, templates, dependabot, CODEOWNERS, CLAUDE.md), dev-loop rule + D14 benchmark commands |
| 8 | This record — all gates green on final tree |

## Known-good invariants preserved

- Numerical behaviour untouched end-to-end: validation report + goldens +
  feature hash identical; `benchmarks/results/` artifacts never modified.
- Shim contract: `import tsxtractor` warns and re-exports identically
  (suite passes under `-W error` with the capture test).
- PyPI smoke path (release.yml) already installs `tsxtract-rs` from wheel
  and asserts shim identity.

## Handoff — not done / awaiting owner

1. **Not pushed.** All 17 commits are local on `refactor/tsxtract`; push
   and PR are the owner's call (no force-push, ever).
2. NEEDS-OWNER remaining: **#1** `Aamod007` identity (README:250 byline,
   CHANGELOG compare URLs, Footer.tsx:165 profile — repo URLs already
   corrected), **#4** PRD.md archive-or-migrate, **#5** patent/ keep,
   **#7** pool.rs wire-or-delete (`tune.py` still records a spin/rayon
   recommendation for an unwired backend), **#8** soa_4x/out32
   keep-or-delete.
3. **F1 throughput numbers** (README headline vs tables vs B3 evidence)
   need a B-track rerun before any number is rewritten; landing meta +
   docs tables still carry the old figures (flagged, not guessed).
4. PyPI 0.5.0 long_description is stale (pre-refactor README) —
   self-corrects on next release.
5. CI has not run on these commits yet (workflows verified by YAML parse
   + structural checks only); first push exercises ci/docs/release.
