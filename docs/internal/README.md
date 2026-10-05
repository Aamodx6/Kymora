# docs/internal/ — developer and process docs (not the user site)

`docs/` is the mkdocs user site; everything under `docs/internal/` is
process, architecture, and historical record. User guides must not link
here (and `check_snippets.py` only executes top-level `docs/*.md`).

- `arch.md` — architecture source of truth (read before changing `src/`).
- `experiments.md`, `thread_scaling.md`, `unsafe_audit.md` — design notes.
- `hardening/` — v0.8.0 hardening process: `PLAN.md`, `STATUS.md`,
  `RELEASE_NOTES.md`, `CLEANUP_STATUS.md` (repo-cleanup tracker),
  `CLEANUP_MOVES.tsv` (Phase 4 path map).
- `refactor/` — completed-refactor records: `REFACTOR_STATE.md`,
  per-phase `phaseN_VERIFICATION.md`, `rename-kymora/`, `baseline/`
  (frozen evidence — content never edited, paths moved with history).
