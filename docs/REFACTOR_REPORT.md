# Refactor report — rename tsxtract → Kymora (2026-10-04)

Branch `refactor/rename-kymora` (tag `pre-rename` at `6a9f308`), merged to
`main` (`97a5c7e`) per owner direction; Phases 5–6 continued on `main`.
`main` already contained the merged `refactor/tsxtract` work, so no earlier
refactor was redone. Owner mid-phase directions: bare **`Kymora`** (no `-rs`
suffix) and **delete `tsxtractor` outright**.

## What moved / deleted / renamed (with justification)

| Change | Justification |
|---|---|
| `python/tsxtract/` → `python/kymora/`; shims removed entirely | Canonical import `kymora` only — `tsxtract` shim added in 0.7.0 then deleted same day per owner ("everything kymora"); `tsxtractor` likewise deleted, no aliases remain |
| `python/tsxtractor/` deleted; `TsxSelector` alias deleted | Owner: drop all legacy names now instead of shimming them; enforced by gone-contract tests |
| PyPI dist `tsxtract-rs` → **`kymora`** (0.7.0), `module-name kymora._core`, crate `kymora` | Bare `kymora` FREE on PyPI/crates.io/npm (Phase 1 evidence); `-rs` only ever existed because bare `tsxtract` was taken |
| `TsxError` → `KymoraError`, `TsxSelector` → `KymoraSelector` (+`TsxSelector` alias) | Name-derived public symbols; Rust error stays `ValueError` in Python |
| `TSXTRACT_*` → `KYMORA_*`, wisdom cache → `~/.cache/kymora` | Documented breaking change (CHANGELOG 0.7.0) |
| `tsx` snippet alias → `km`; benchmark-local `tsx*` vars → `km*` | Old abbreviation retired everywhere except frozen data |
| `scripts/` → `tools/` | Target layout (CI/docs refs updated, residual scan clean) |
| `PRD.md` removed (§15 items → `docs/ROADMAP.md`) | v1.0 task list fully shipped; launch plan dated |
| `landing/src/docs/**` retired (33 files) | Duplicate of `docs/`; mkdocs site is the single source (deploys via docs.yml). Nav Docs links → canonical docs URL; `/docs/*` redirects added |
| `benchmarks/adapters/tsxtract.{py,md}` → `kymora.*`, `requirements-tsxtract.txt` → `requirements-kymora.txt` | Same library, new name; new runs record lib id `kymora` |
| Untouched | `patent/`, `paper/`, `tests/golden/`, fixtures, `benchmarks/results/*`, `benchmarks/report/*`, B-track evidence files, CHANGELOG history, frozen `docs/refactor/*` |

## Decisions

- D-R0: canonical remote recorded (`Aamodx6/Tsxtract`), account decision stays owner-side.
- D-R1: Kymora ranked #1 of 3 (all registries FREE; `.io` free); owner-confirmed.
- D-R2: thin Phase 2 — prior refactor had already cleared `insp/`, dead code, arch dupes; only PRD.md deleted, rest evidenced as keep.
- D-R3: `landing/` NOT renamed to `site/` (Vercel root setting needs owner); no `justfile`/`noxfile` (D14 raw commands stay canonical); `tests/` already matched target.
- D-R4: data keys frozen (`tsxtract_matched_*`, `tsxtractor_version`, `vs_tsx_core33`, old lib ids) — readers accept old+new; localStorage keys kept stable; `tsxtract-rs 0.6.1` finale sketch kept for both old imports.
- D-R5: docs/ = single source; API reference stays hand-written (stub surface test-enforced); signature fences marked `skip`, real programs execute in CI.

## Verification output (gates)

| Check | Phase 0 | Phase 6 | Δ |
|---|---|---|---|
| Tracked files | 312 | 297 | −15 net (see table) |
| `pytest` | 138 passed | **139 passed** | +shim-gone contract |
| `cargo test` | 16/16 | 16/16 | — |
| fmt / clippy / mypy / mkdocs-strict | clean | clean | — |
| validation report | 33/33 in tol | 33/33 in tol | — |
| `feature_names()` hash | `8a1e2794…31af2e` | MATCH | — |
| golden diff vs `pre-rename` | — | EMPTY | — |
| secrets scan | none | none (gitleaks still owner-side) | — |
| snippets | n/a (new) | 20 run / 0 fail | — |
| link check | n/a (new) | clean | — |
| landing build | ok | ok (−1.1 MB JS) | — |
| Lighthouse | n/a (new) | 94 / 100 / 100 / 100 | perf: lab-local drag, documented |
| smoke PRE/POST | n/a | **FLAGGED −22%, investigated** | A/A control ±32% under "Silent" plan → noise; outputs bitwise identical |

## NEEDS-OWNER (consolidated)

1. Canonical account (`Aamodx6` vs `Aamod007` bylines) + GitHub repo rename
   to `Kymora` (runbook: `docs/RENAME_RELEASE_CHECKLIST.md`; Pages/Vercel
   follow-ups listed there).
2. PyPI trusted publishing for **`kymora`** (owner; `kymora` verified FREE).
   `tsxtract-rs` was deleted by the owner — deleted PyPI names can never be
   re-registered, so the planned 0.6.1 deprecation finale is impossible.
   Nothing published by this work.
3. `patent/` + `paper/` fate (IP/publication).
4. Trademark (WIPO/IP India/USPTO 9+42), web-search, meaning check for Kymora.
5. gitleaks in CI; real domain + 1200×630 OG card; perf ≥95 + Linux re-baseline.
6. Push `main` (origin/main holds a dependabot commit we lack — pull first).
7. B-track continuation under the new lib id.

## Follow-ups (not started)

- Phase 5 leftovers: `landing/`→`site/` rename, perf ≥95 (font/code-split),
  external-link checking in CI.
- `tune()` pool dimension still void (spin backend on `experiment/spin-pool`).
- Stale `benchmarks/results/*` untracked run outputs: owner decides what (if
  anything) gets committed or deleted; this work never touched them.

## State

Merged to `main`, **not pushed**. Worktree clean except untracked
`benchmarks/results/*` run outputs (must stay untracked per repo rule).
