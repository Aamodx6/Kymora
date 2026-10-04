# Refactor state (tsxtract standardization)

Branch: `refactor/tsxtract`. Tag: `pre-refactor`. Base: `4c268ca`.
arch.md is the architecture source of truth.

## Phase checklist

- [x] Phase 0: baseline & inventory (2026-10-04). Gate: baseline recorded;
      two known-red items documented (mypy 10 errors, mkdocs warnings).
- [x] Phase 1: naming decision & packaging (2026-10-04). Gate: wheel builds
      as `tsxtract-rs 0.5.0`, `import tsxtract` works, `import tsxtractor`
      warns + works, 138 tests pass, feature hash unchanged, clean-venv
      install verified. See `docs/refactor/naming.md`,
      `docs/refactor/phase1_VERIFICATION.md`.
- [x] Phase 2: repository structure & obsolete file removal (2026-10-04).
      Gate: `benchmarks/` move + path updates (53 files, zero residuals),
      `tests/{property,reference}/` subdirs, `insp/` deleted with evidence,
      `.gitignore` fixed, builds/tests green. See
      `docs/refactor/deleted_files.md`. Contributor files
      (CODE_OF_CONDUCT, SECURITY, CITATION.cff, templates, dependabot)
      deferred to Phase 7; docs-system dedup deferred to Phase 5.
- [x] Phase 3: Rust core cleanup (2026-10-04). Gate: legacy dead code
      removed with evidence (−133 net), unsafe centralized into 2 helpers
      with SAFETY contract, `deny(unsafe_code)` in 17 modules
      (negative-tested), rustdoc warning-free, arch.md I8 + §4.1 aligned,
      cargo/pytest green, feature hash unchanged, perf no-regression.
      Fresh Zenith experiments kept (pool.rs, soa_4x, out32) pending owner
      wire-or-delete. See `docs/refactor/phase3_VERIFICATION.md`.
- [x] Phase 4: Python package cleanup (2026-10-04). Gate: mypy clean
      (was 10 errors; stubs completed from `ffi.rs` signatures, select.py
      typing fixed, scipy import made hermetic), 138 tests pass, feature
      hash unchanged. Dev-loop hazard found: tests import site-packages,
      so the wheel must be rebuilt+reinstalled before pytest means
      anything (done this phase; Phase 7 tooling candidate). See
      `docs/refactor/phase4_VERIFICATION.md`.
- [x] Phase 5: documentation architecture (2026-10-04). Gate: false
      SIMD/spin-pool/O(1)/sub-microsecond claims corrected in `docs/` +
      README (measured 1.8 µs fast-tier), 2 anchors fixed by adding the
      missing sections, `site_url` aligned (closes #6), mkdocs strict
      INFO-free, roles decision (no landing merge). PRD/patent untouched
      (#4/#5). See `docs/refactor/phase5_VERIFICATION.md`.
- [x] Phase 6: website (2026-10-04). Gate: landing build clean; removed
      4 false conda-forge blocks (Anaconda API 404 on both names) and
      fixed 9 wrong `tsxtract` dist names in install commands (would hit
      the unrelated JAX PyPI project); docs/api.md D8 violation fixed;
      dead `TSXTRACT_VERSION` removed; nav/links/figures integrity
      16/16. **#2 RESOLVED** (PyPI `tsxtract-rs` owned by `aamoddev11`,
      0.5.0 live). F1 exposure + Footer profile deferred (#1/B-track).
      See `docs/refactor/phase6_VERIFICATION.md`.
- [x] Phase 7: CI/CD, tooling, contributor experience (2026-10-04). Gate:
      setup-venv composite action wired into ci.yml ×3 + benchmark.yml
      (was untracked dup); docs.yml never-succeeding install replaced with
      pyproject floors; contributor files created (CODEOWNERS, CoC — was a
      dead link in CONTRIBUTING — SECURITY, CITATION.cff, issue/PR
      templates, dependabot, CLAUDE.md); dev-loop hazard + cross-platform
      benchmark commands documented (D14: raw commands canonical, wrappers
      kept for arch/Dockerfile refs). All YAML parse; full gates green.
      See `docs/refactor/phase7_VERIFICATION.md`.
- [ ] Phase 8: final verification & report

## Decisions

- D0 (Phase 0): canonical repo = `origin` (`Aamodx6/Tsxtract`) until owner
  confirms otherwise.
- D0 (Phase 0): `feature_names()` sha256
  `8a1e2794…3e1431af` is the semantic invariance anchor for all phases.
- D9 (Phase 2): `benchmarks/` is the Python harness dir (arch.md §4.1
  updated); `mkdocs build --strict` passes (docs CI green); `make` is
  unavailable on the owner's Windows box — runner consolidation is Phase 7.
- D10 (Phase 3): unsafe lives only in `ffi.rs` (numpy boundary, centralized
  helpers + SAFETY) and `kernels/` (designated home, currently unsafe-free);
  compile-enforced elsewhere via `deny(unsafe_code)`.
- D11 (Phase 3): deleted only legacy-superseded dead code; kept fresh
  Zenith-session experiments (`pool.rs`, `soa_4x`, `run_core33_f32_out32`)
  for an owner wire-or-delete call.
- D12 (Phase 4): `_core.pyi` is complete and runtime-verified; mypy gate is
  hermetic (no new CI deps needed for scipy); `select_features` returns
  plain `int` indices.
- D13 (Phase 5): `docs/` is the versioned project reference, landing docs
  are product-site content — no mirroring either way (overlap 0.02–0.29);
  new shared facts go in `docs/` first; historical reports stay out of nav.
- D14 (Phase 7): benchmark runner entry points — the five raw
  `python benchmarks/...` commands are the canonical portable path
  (Windows-safe); `Makefile` and `reproduce.sh` remain optional wrappers
  (referenced by arch.md gates and Dockerfile CMD), not deleted.

## NEEDS-OWNER

1. Confirm canonical repo (`Aamodx6/Tsxtract`) and fate of anything under
   handle `Aamod007` (no second remote is configured locally).
2. ~~PyPI `tsxtract-rs` ownership~~ — resolved Phase 6: PyPI API shows
   releases 0.3.0–0.5.0 under owner `aamoddev11`, metadata identical to
   this repo. JAX project keeps bare `tsxtract` (D8 still applies:
   never `pip install tsxtract`).
3. Stashed prior-session work: resolved (popped + committed in Phase 1).
4. `PRD.md`: archive or migrate-then-delete (sole product-requirements
   record; weak references only).
5. `patent/patent_disclosure.md`: 0 references, but IP content — confirm
   keep (do NOT delete on usage heuristic).
6. ~~`mkdocs.yml: site_url` still `aamod007.github.io`~~ — resolved Phase 5
   (`aamodx6.github.io`, per D0).
7. `pool.rs` / `TSXTRACT_POOL`: Rust ignores the env var; docs now say so
   (`api.md`, `quickstart.md`), but `tune.py` still records spin-vs-rayon
   recommendations — wire the backend (behavior change), delete `pool.rs`,
   or keep as documented prototype?
8. `soa_4x` kernels + `run_core33_f32_out32`: uncalled Zenith-session
   experiments — keep or delete?

## Stash register

- `wip-arch-consolidation`: pre-existing uncommitted changes found on
  2026-10-04 (arch.md rewrite, arch_max.md/arch_zenith.md deletions,
  benchmarks/STATE.md + adapters + harness edits, LOSS_LEDGER.md).
