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
- [ ] Phase 3: Rust core cleanup
- [ ] Phase 3: Rust core cleanup
- [ ] Phase 4: Python package cleanup
- [ ] Phase 5: documentation architecture
- [ ] Phase 6: website
- [ ] Phase 7: CI/CD, tooling, contributor experience
- [ ] Phase 8: final verification & report

## Decisions

- D0 (Phase 0): canonical repo = `origin` (`Aamodx6/Tsxtract`) until owner
  confirms otherwise.
- D0 (Phase 0): `feature_names()` sha256
  `8a1e2794…3e1431af` is the semantic invariance anchor for all phases.
- D9 (Phase 2): `benchmarks/` is the Python harness dir (arch.md §4.1
  updated); `mkdocs build --strict` passes (docs CI green); `make` is
  unavailable on the owner's Windows box — runner consolidation is Phase 7.

## NEEDS-OWNER

1. Confirm canonical repo (`Aamodx6/Tsxtract`) and fate of anything under
   handle `Aamod007` (no second remote is configured locally).
2. (Phase 1 input) PyPI `tsxtract` ownership — the unrelated JAX project
   holds the name; confirm keeping PyPI distribution name `tsxtract-rs`
   if `tsxtract` is not ours. crates.io check for `tsxtract` pending.
3. Stashed prior-session work: resolved (popped + committed in Phase 1).
4. `PRD.md`: archive or migrate-then-delete (sole product-requirements
   record; weak references only).
5. `patent/patent_disclosure.md`: 0 references, but IP content — confirm
   keep (do NOT delete on usage heuristic).
6. `mkdocs.yml: site_url` still `aamod007.github.io` (Phase 5 docs decision).

## Stash register

- `wip-arch-consolidation`: pre-existing uncommitted changes found on
  2026-10-04 (arch.md rewrite, arch_max.md/arch_zenith.md deletions,
  benchmarks/STATE.md + adapters + harness edits, LOSS_LEDGER.md).
