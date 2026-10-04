# Phase 0 baseline summary (2026-10-04, branch `refactor/tsxtract`, clean tree)

Full logs: `docs/refactor/baseline/`.

| Check | Command | Result |
| --- | --- | --- |
| Rust tests | `cargo test` | PASS — 16/16 (`cargo_test.txt`) |
| Clippy | `cargo clippy --all-targets -- -D warnings` | PASS — exit 0, no warnings (`cargo_clippy.txt`) |
| rustfmt | `cargo fmt --check` | PASS — exit 0 (`cargo_fmt.txt`, empty) |
| Python tests | `python -m pytest tests -x -q` | PASS — 138 passed in 52s (`pytest.txt`) |
| Type check | `python -m mypy python/tsxtractor` | **FAIL — 10 errors** (`mypy.txt`). mypy 1.x installed to match CI. `_core.pyi` is missing `MultiStreamExtractor`, `extract_features_mc`, `feature_names_mc`, and the `views` kwargs on `extract_features`/`feature_names`; plus 2 `select.py` typing errors. Runtime is unaffected (tests green). Fix in Phase 4 (regenerate/complete `_core.pyi`). |
| Benchmark smoke | `python benches/smoke.py` | PASS — exit 0, 10/10 adapters processed (`bench_smoke.txt`). The `tsxtract_jax` adapter reports ERROR by design (documents the unrelated-JAX-package collision). |
| Docs build | `python -m mkdocs build` | PASS with warnings (`mkdocs_build.txt`): 4 pages not in nav (`arch_audit`, `parity_matrix`, `redundancy_report`, `timeline_progress`); 2 broken anchors (`benchmarks.md`, `migrating.md` → missing `index.md` anchors). Fix in Phase 5. |
| Website build | `npm run build` (in `landing/`) | PASS — exit 0, built in ~49s (`website_build.txt`); chunk-size warnings (mermaid/plot bundles >500 kB). Address in Phase 6. |

## Frozen hashes

- `feature_names()` (33 names): sha256
  `8a1e27942b370ec886130db4f19ca973b2a1b36ea17823723c9d7afd1431af2e`
  (`feature_names.txt`)
- Golden files (`golden_hashes.txt`):
  - `tests/golden/core33_names.json`
  - `tests/golden/core33_output.json`
  - `tests/fixtures/tsfresh_777_names.json`
- Public API: `tsxtract.__all__ == tsxtractor.__all__` (16 symbols each,
  `api_surface.txt`).

## File inventory

- 240 tracked files, classified in `file_classification.txt`:
  source-rust (`src/`), source-python (`python/`), tests, benchmarks
  (`benches/`), docs, website (`landing/`), ci (`.github/`),
  paper/patent, scripts, scratch (`insp/` screenshots), config-root.
- Name occurrences: `name_inventory.md` + `name_inventory_raw.txt`.

## Toolchain notes

- `cargo` 1.98.1 (not on default PATH; at `%USERPROFILE%\.cargo\bin`).
- Python 3.14.6, pytest 9.1.1, mkdocs 1.6.1/material 9.7.7, node+npm present.
- No `rg`, `ruff`, `just`/`nox` installed — Phase 7 to choose/install the
  task runner; cross-platform commands required.
