# Obsolete-file triage (Phase 2, 2026-10-04)

Method: `git ls-files` classified (Phase 0 `file_classification.txt`);
reference search over all tracked text files
(`Temp/opencode/triage_refs.py`); `git log` last-touch per candidate.
Rule: delete only with zero non-self references; never delete golden files,
tests, benchmark result artifacts, LICENSE, arch.md, CHANGELOG.md.

## Deleted

### `insp/` (8 PNG screenshots + `framer.md`)
- Evidence: 0 references in any tracked file; last touched `e8eb7a7`
  (v0.3.0 release commit). Scratch inspection captures, superseded by
  `landing/public/figures/` and `paper/figures/`.
- Action: `git rm -r insp/` (Phase 2 commit).

## Moved (not deleted)

- `benches/` → `benchmarks/` via `git mv` (tracked) — whole-tree move,
  untracked run outputs carried along on disk. Scripted content pass
  (`\bbenches\b` → `benchmarks`, 53 files, zero residuals outside
  allowlist: `paper/` frozen publication, `CHANGELOG.md` history,
  `docs/refactor/*` frozen records, result/agreement/baseline data).
- `tests/test_properties.py` → `tests/property/` and
  `tests/test_validation.py` → `tests/reference/` via `git mv`
  (no filesystem-path assumptions in either file; pytest collects
  recursively; no `conftest.py`).

## Considered, kept (with rationale)

- `PRD.md` — weak references only (arch.md grep-scope listing,
  `docs/timeline_progress.md` history), but it is the sole product
  requirements record and contains un-migrated v1.0 ship criteria
  (stale `pip install tsxtract` lines kept as history).
  → NEEDS-OWNER: archive or migrate-then-delete.
- `patent/patent_disclosure.md` — 0 references, but IP content must never
  be deleted on a usage heuristic. → NEEDS-OWNER.
- `scripts/run_phase0_baseline.py` — 0 external references, but it is the
  generator of tracked artifact `benchmarks/baseline/baseline.json`.
  Deleting the generator while keeping the artifact is worse. Kept.
- `benchmarks/bench_ablation.py`, `bench_matrix.py` — invoked from
  `paper/main.tex` repro commands and referenced by README/docs/landing.
  Not provably unused. Kept (revisit in Phase 5 docs pass).
- `Dockerfile`, `reproduce.sh` — referenced (Dockerfile CMD, STATE.md).
  `reproduce.sh` is bash-only; consolidating runners is Phase 7 work.
- `paper/`, `paper/*.tex` — frozen publication pinning commit `1e8b277`;
  excluded from path updates deliberately.
- `docs/arch_audit.md`, `docs/redundancy_report.md`,
  `docs/timeline_progress.md` — unlisted in `mkdocs.yml` nav (mkdocs INFO),
  but content triage is a Phase 5 docs-architecture decision. Deferred.
- `mkdocs.yml` + `landing/src/docs/` duplicate docs systems — Phase 5
  decision. Both kept.
- Missing root files (`CODE_OF_CONDUCT.md`, `SECURITY.md`, `CITATION.cff`,
  `CLAUDE.md`, issue/PR templates, `dependabot.yml`,
  `.github/CODEOWNERS`) — creation is Phase 7 work, recorded here so the
  Phase 2 layout gate is read with that split in mind.

## `.gitignore` changes

- `benches/.venvs/`, `benches/datasets/cache/` → `benchmarks/` equivalents
  (via scripted pass); added `.DS_Store`.
- Verified ignored and absent from tracking: `target/`, `dist/`, `.venv/`,
  `__pycache__/`, `*.pyd`, `*.pdb`, `site/`, `node_modules/`,
  `landing/dist/`, `.freebuff/`, `.gstack/`, `.hypothesis/`,
  `.pytest_cache/`. No build artifacts are committed.
