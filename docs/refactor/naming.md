# Naming decision (Phase 1, 2026-10-04)

## Registry evidence (checked live 2026-10-04)

- **PyPI `tsxtract` 0.1.0** — owned by `ctseidler`, an unrelated JAX-based
  time-series project (uploaded 2025-11-30, active). **Not ours.**
  `pip install tsxtract` installs that project.
- **PyPI `tsxtract-rs`** — owned by `aamoddev11` (ours), versions
  0.3.0 / 0.3.1 / 0.3.2 / 0.4.0 / 0.5.0 with multi-platform wheels.
- **crates.io `tsxtract`** — 404, available.
- **crates.io `tsxtractor`** — 404, available.

## Decisions

- **D1 — import name / Python package dir: `tsxtract`** (`python/tsxtract/`).
  The import name collides with the JAX package at the *import* level, so
  the README and install docs must warn that the two distributions must
  never be installed in the same environment.
- **D2 — PyPI distribution name: `tsxtract-rs`** (kept). Rationale: `tsxtract`
  on PyPI is owned by the unrelated JAX project. This also repairs the
  release pipeline: `.github/workflows/release.yml` smoke-test installs
  `tsxtract-rs` from the built wheel, which the `name = "tsxtract"` rename
  (commit `f6b670c`) broke.
- **D3 — Rust crate name: `tsxtract`** (both candidates free on crates.io;
  chosen for consistency). Extension module: **`tsxtract._core`**
  (maturin `module-name`). The crate is `cdylib`-only and is not published
  to crates.io; the rename is local-only.
- **D4 — env vars: `TSXTRACT_*`** — already standard (`TSXTRACT_POOL`,
  `TSXTRACT_WISDOM`). No change.
- **D5 — display name: `tsxtract`** (lowercase) in docs/site (applied in
  Phases 5–6; Phase 1 changes code/config identifiers only).
- **D6 — old import `tsxtractor` becomes a thin deprecated shim** that
  re-exports `tsxtract` and emits a `DeprecationWarning` once per process.
  Removal scheduled for **0.7.0 at the earliest** (recorded in CHANGELOG).
- **D7 — version is single-sourced from `Cargo.toml`.** `pyproject.toml`
  carries no `version` field; maturin injects the crate version into the
  wheel metadata (verified by inspecting the built wheel in Phase 1).
- **D8 — install lines everywhere say `pip install tsxtract-rs`**
  (never bare `pip install tsxtract`, which resolves to the JAX project).

## Allowlisted residuals (post-rename scan)

`tsxtractor` remains only in: the shim itself, `python/tsxtract/__init__.py`
(legacy dist probe + docstring note), `pyproject.toml` (`python-packages`
ships the shim), `tests/test_python_api.py` (shim contract test),
`benches/adapters/tsxtract.py` (legacy-import fallback),
`.github/workflows/release.yml` (shim smoke check), `CHANGELOG.md`
(history), `docs/refactor/*` (frozen records), result data under
`benches/`. `PRD.md` keeps three historical `pip install tsxtract`
ship-bar lines untouched as history — flagged for the Phase 2
obsolete-file review.

## Follow-ups (later phases)

- `mkdocs.yml: site_url` still points at `aamod007.github.io` — Phase 5
  decides the single docs system and correct deployment URL.
- Personal author bylines (`README.md`, `landing/.../Footer.tsx` linking
  `github.com/Aamod007`) left untouched pending NEEDS-OWNER #1.
- `pyproject.toml: project.urls` already canonical (`Aamodx6/Tsxtract`).

## Consequences

- `python/tsxtractor/` holds only the shim; real code moves to
  `python/tsxtract/` via `git mv`.
- `maturin develop` / wheel builds produce `tsxtract._core`.
- `tests/test_python_api.py` tests the canonical `tsxtract` import plus
  the shim contract (warning + identity of re-exports).
