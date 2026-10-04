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
- [ ] Phase 2: repository structure & obsolete file removal
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

## NEEDS-OWNER

1. Confirm canonical repo (`Aamodx6/Tsxtract`) and fate of anything under
   handle `Aamod007` (no second remote is configured locally).
2. (Phase 1 input) PyPI `tsxtract` ownership — the unrelated JAX project
   holds the name; confirm keeping PyPI distribution name `tsxtract-rs`
   if `tsxtract` is not ours. crates.io check for `tsxtract` pending.
3. Stashed prior-session work: stash `wip-arch-consolidation` on
   `refactor/tsxtract` (arch.md consolidation + benches harness edits).
   Decide whether to keep it (pop after Phase 0 commit) or redo cleanly
   in later phases. Default plan: pop and review in Phase 2/5.

## Stash register

- `wip-arch-consolidation`: pre-existing uncommitted changes found on
  2026-10-04 (arch.md rewrite, arch_max.md/arch_zenith.md deletions,
  benches/STATE.md + adapters + harness edits, LOSS_LEDGER.md).
