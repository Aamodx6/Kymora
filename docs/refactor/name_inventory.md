# Name inventory (Phase 0 baseline, 2026-10-04)

Raw machine output: `docs/refactor/baseline/name_inventory_raw.txt`
(scan of 214 text files among 240 git-tracked files; binaries skipped).

## Canonical repository

`git remote -v` shows a single remote:

- `origin  https://github.com/Aamodx6/Tsxtract.git` (fetch + push)

No second remote is configured. The brief mentions handles `Aamodx6` and
`Aamod007`; only `Aamodx6/Tsxtract` is observable from the repo.
**Decision:** use `origin` as canonical. **NEEDS-OWNER:** confirm
`Aamodx6/Tsxtract` is canonical and whether `Aamod007` owns a live fork
that needs redirect/archival.

## Counts

| Name | Files | Hits |
| --- | --- | --- |
| `tsxtract-rs` | 6 | 8 |
| `tsxtractor` | 82 | 514 |
| `TSXTRACT` | 8 | (see raw) |
| `Tsxtract` | 67 | (see raw) |
| standalone `tsxtract` | 44 | (see raw) |

## `tsxtract-rs` hits (must all be resolved in Phase 1)

1. `.github/workflows/release.yml` (2)
2. `benches/report/results.json` (1) — generated; update generator, not the file
3. `benches/results/2026-10-04_Aamod/env.json` (1) — result artifact; path updates only
4. `benches/results/2026-10-04_reproduce_readme/env.json` (1) — result artifact; path updates only
5. `python/tsxtractor/__init__.py` (1) — `_resolve_version` dist-name probe
6. `tests/test_python_api.py` (2)

## Current naming reality (pre-refactor)

- Real Python code lives in `python/tsxtractor/` (`__init__.py`, `select.py`,
  `tune.py`, `_core.pyi`, `_core.pyd` build artifact committed? — see below).
- `python/tsxtract/__init__.py` is a thin alias that re-exports `tsxtractor`
  with **no** deprecation warning.
- `pyproject.toml`: distribution name is already `tsxtract`; maturin
  `module-name = "tsxtractor._core"`, ships both `tsxtractor` and `tsxtract`
  python-packages.
- `Cargo.toml`: crate name `tsxtractor`, lib name `_core`.
- Installed environment has BOTH dists `tsxtract 0.5.0` and `tsxtract-rs 0.5.0`
  (stale `tsxtract-rs` metadata from a previous release line).
- `TSXTRACT_*` env vars: 8 files — check `src/pool.rs`, `src/exec.rs`,
  docs for `TSXTRACT_POOL` / `TSXTRACT_WISDOM` (Phase 1 to standardize).

## Notes for Phase 1

- The unrelated JAX `tsxtract` package on PyPI is already acknowledged
  in-repo via the `tsxtract_jax` benchmark adapter (documents the collision).
- `python/tsxtractor/_core.pyd` + `_core.pdb` appear in the working tree
  (untracked or build output — verify tracked status in Phase 2; build
  artifacts must not be committed).
