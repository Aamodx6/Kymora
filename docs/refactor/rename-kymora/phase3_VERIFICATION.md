# Phase 3 verification — restructure (2026-10-04)

## What the survey found

The tree already matched most of the target layout (prior refactor did the
heavy moves), verified rather than redone:

- `src/` Rust core (23 files) — no change.
- `tests/` — already `golden/`, `reference/` (`test_validation.py`),
  `property/` (`test_properties.py`), `fixtures/` — all tracked. No moves.
- `benchmarks/` only (`benches/` long gone). No Criterion Rust benches exist
  anywhere — recorded as not-present, not required.
- `.github/` complete: `workflows/` (benchmark, ci, docs, release),
  `actions/setup-venv`, `ISSUE_TEMPLATE/` ×3, `CODEOWNERS`, `dependabot.yml`,
  `PULL_REQUEST_TEMPLATE.md`. No change.
- Root files complete: README, arch, CHANGELOG, CONTRIBUTING,
  CODE_OF_CONDUCT, SECURITY, LICENSE, CITATION.cff, Cargo.toml/lock,
  pyproject.toml, Makefile, mkdocs.yml, Dockerfile, reproduce.sh,
  CLAIMS.md. No `justfile`/`noxfile.py` — deliberate per D14 (raw
  `python benchmarks/...` commands are canonical, portable; Makefile stays
  as wrapper). No change.

## Changes made

- **`scripts/` → `tools/`** via `git mv` (4 survivors from Phase 2).
  Path references updated by scripted word-boundary replace
  (`\bscripts/` → `tools/`, 16 hits in 12 files): `ci.yml:75`, PR template,
  `CLAUDE.md`, `CONTRIBUTING.md`, `docs/contributing.md`,
  `docs/validation.md`, `landing/.../contributing.md` ×3,
  `docs/naming/NAME_CHECK.md` ×2, plus self-refs in the moved scripts.
  Residual scan: `git grep 'scripts/'` (excl. frozen `docs/refactor/*`,
  `CHANGELOG` history, `benchmarks/results`) returns **zero**.
  Allowlist: frozen records + CHANGELOG history keep `scripts/` as history.
- **`landing/` → `site/`: NOT renamed.** Reason: the site is deployed on
  Vercel (`landing/vercel.json` SPA rewrites); renaming the directory
  requires an owner dashboard change (project root) plus redirect checks.
  → NEEDS-OWNER. `python/<newname>/` → Phase 4 (it is the rename itself).

## Gates

| Gate | Result |
|---|---|
| `python tools/validation_report.py` (moved tool) | **All 33 within tolerance**, exit 0 |
| `python tools/name_check.py Kymora` (moved tool) | runs, Kymora FREE everywhere |
| `python -m pytest tests -q` | **138 passed** in 21.29s (re-run after the move) |
| `feature_names()` hash | unchanged `8a1e2794…31af2e` |
| dangling refs | `scripts/` residual scan clean (above) |

**Phase 3 GATE: PASS** — tree matches target modulo the two recorded
deferrals (`landing/`, `python/kymora`); no dangling path references.
