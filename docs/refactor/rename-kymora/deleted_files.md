# Phase 2 deletion report — rename to Kymora (2026-10-04)

Rule: each candidate has path, why obsolete/kept, proof of non-use
(search output + `git log` last-touch), decision. The 2026-10-04
`refactor/tsxtract` pass already removed `insp/`, legacy dead code,
`arch_max/zenith.md`, and fixed `.gitignore` — verified below, not redone.

## Deleted this phase

| Path | Why obsolete | Proof of non-use | Decision |
|---|---|---|---|
| `PRD.md` (268 lines) | v1.0 PRD; §17 task list fully shipped; §§6/14/18 launch metrics/GTM dated | Last substantive touch pre-0.5.0; remaining refs are frozen records (`docs/refactor/*`, old `naming.md` allowlist) + `REFACTOR_STATE` NEEDS-OWNER #4 + historical arch.md App. C checklist | **DELETED** (`git rm`, commit `21e1b85`). Still-true §15 items migrated to `docs/ROADMAP.md` (commit `4add5c8`). History keeps it. |

## Evaluated, kept (with evidence)

- **`scripts/validation_report.py`** — KEPT. Referenced by CI
  (`.github/workflows/ci.yml:75`) + CLAUDE.md + CONTRIBUTING.md gates.
  Survivor → moves to `tools/` in Phase 3.
- **`scripts/feature_redundancy_analysis.py`** — KEPT. Zero CI/Makefile
  refs, but it is the sole provenance of committed
  `docs/redundancy_report.md` (`--output-md` in its docstring; last-touch
  `d56c88f` layout move). Deleting it would orphan the report.
  Survivor → `tools/` in Phase 3.
- **`scripts/run_phase0_baseline.py`** — KEPT. Zero refs, but sole
  provenance of committed `benchmarks/baseline/baseline.json` (tracked
  since the layout move). Survivor → `tools/` in Phase 3.
- **`scripts/name_check.py`** — KEPT (new, Phase 1 audit trail).
  Survivor → `tools/` in Phase 3.
- **Duplicate docs (`docs/` + `mkdocs.yml` + `landing/src/docs/`)** — KEPT
  both. Decided in D13: `docs/` is the versioned project reference,
  landing docs are product-site content, no mirroring either way.
  IA dedup belongs to Phase 5, not deletion.
- **`tests/fixtures/tsfresh_777_names.json`** — KEPT. Referenced by
  arch.md §6 parity discipline + frozen baseline records; `tests/` and
  fixtures are never-delete.
- **`insp/`** — already deleted by the prior refactor; confirmed absent
  (`Test-Path insp` = False). Not redone.
- **`arch_max.md` / `arch_zenith.md`** — already deleted; confirmed absent
  from `git ls-files`. Not redone.
- **Committed artifacts (`target/`, `dist/`, caches, `.DS_Store`,
  `__pycache__`)** — none tracked (`git ls-files dist target` empty;
  `.gitignore` covers `/target`, `dist/`, `__pycache__/`, `.pytest_cache/`,
  `.hypothesis/`, `site/`, `.DS_Store`). `.freebuff/`, `.gstack/` ignored +
  untracked. Nothing to delete.
- **Unused dependencies** — none found: no `cargo-machete`/`udeps`/
  `vulture`/`ruff-F401`/`knip` references in `Cargo.toml`,
  `pyproject.toml`, `landing/package.json`; `cargo clippy -D warnings`
  green (dead code would fail the gate).
- **Dead code/modules** — prior Phase 3 removed legacy dead code with
  evidence; fresh Zenith experiments live on `experiment/*` branches by
  owner decision. `cargo test` 16/16 + clippy clean confirm no rot.
- **`paper/` + `patent/` (17 files)** — UNTOUCHED per hard rule;
  NEEDS-OWNER (IP/publication decision belongs to the owner).
- **`tests/`, golden files, `LICENSE`, `arch.md`, `CHANGELOG.md`,
  benchmark results** — untouched per hard rule.

## `scripts/` → `tools/` move

Deferred to Phase 3 (owns layout + path-reference updates) to avoid
breaking the CI gate mid-phase. Survivors: all 4 scripts above.

## Gate

**Phase 2 GATE: PASS** — report complete with evidence per file; build and
tests re-verified green after the `PRD.md` removal (below).
