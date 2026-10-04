# Phase 4 verification — Python package cleanup (2026-10-04)

## Baseline (Phase 0 known-red): 10 mypy errors → 0

`mypy python/tsxtract` (same scope as CI): **Success: no issues found in
4 source files.**

| Error | Fix |
|---|---|
| `_core.pyi` missing `MultiStreamExtractor`, `extract_features_mc`, `feature_names_mc` (`__init__.py:36`) | Added to stubs, signatures taken from `src/ffi.rs` `#[pyo3(signature…)]` lines and verified at runtime (see below) |
| `_core.pyi` `extract_features`/`feature_names` missing `views` (`__init__.py:114,122`) | Added `views`; also added `precision`/`out_dtype` and corrected return to `_F64Array \| _F32Array` (`out_dtype="float32"` returns f32) |
| `select.py:188` ndarray→list reassignment | New `ranked_candidates: list[int]` (normalized via `int(i)`) |
| `select.py:193` missing annotation | `selected_indices: list[int]` |
| `select.py:242/244` DataFrame/dict + return-type mismatch | `report: Any` |
| `select.py:22` scipy import-untyped (env-dependent) | `pip install scipy-stubs` locally **plus** targeted `# type: ignore[import-untyped]` on both scipy imports, so the gate is hermetic with or without stubs (CI installs only `pandas-stubs`) |

Also: `__init__.py` docstring no longer claims "persistent spin workers"
(`pool.rs` is unwired — Phase 3 finding). Unused-import AST scan: clean
(only `__future__` false positives).

## Behavior notes

- `select_features` now returns plain `int` indices (was `np.int64`):
  same selection (sanity: 6/33 on seeded data), indexing/dict-key behavior
  identical; `TsxSelector` unaffected (suite green).
- Stub-surface runtime check passed: f32 `out_dtype` path, `views` on
  `extract_features`/`feature_names`, mc extract+names shape agreement
  (4, 115), `MultiStreamExtractor` props/`push_many`/`reset(None|idx)`/
  `compute(kind|streams)`/`fast_feature_names`, `list_profiles`,
  `describe_feature`.

## Dev-loop hazard found

`import tsxtract` resolves to **site-packages**, not `python/tsxtract/`, so
pytest runs against the *installed* wheel. The first Phase 4 pytest run
passed while testing pre-Phase-4 code. Fixed by rebuilding (`maturin build
--release`) + `pip install --force-reinstall` and re-running everything.
Candidate Phase 7 item: editable/venv dev loop so repo source is what tests.

## Verification output (final tree, installed wheel rebuilt)

- `mypy python/tsxtract`: clean (was 10 errors)
- `pytest tests -q`: 138 passed, 0 warnings
- `feature_names()` sha256: `8a1e2794…431af` MATCH
- `benchmarks/smoke.py`: 10/10 (tracked results reverted)

## Commits

- (this phase) `python/tsxtract/_core.pyi`, `select.py`, `__init__.py` —
  single commit below
