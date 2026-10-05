# Phase 1 verification (2026-10-04, branch `refactor/tsxtract`)

## Registry checks (live, via PyPI/ crates.io JSON APIs)

- `tsxtract` on PyPI: 0.1.0, owner `ctseidler`, unrelated JAX project
  (uploaded 2025-11-30). NOT ours → dist name stays `tsxtract-rs`.
- `tsxtract-rs` on PyPI: owner `aamoddev11` (ours), releases
  0.3.0–0.5.0 with multi-platform wheels.
- crates.io `tsxtract` / `tsxtractor`: both 404 (free) → crate renamed to
  `tsxtract` (local-only; cdylib, unpublished).

## Commands run (real output, trimmed)

`cargo test` → 16 passed, exit 0 (Cargo.lock regenerated: `tsxtractor`→`tsxtract`).

`python -m maturin build --release --out dist` →
`dist\tsxtract_rs-0.5.0-cp310-abi3-win_amd64.whl`
Wheel contents: `tsxtract/_core.pyd`, `tsxtract/_core.pyi`,
`tsxtract_rs-0.5.0.dist-info/METADATA` with `Name: tsxtract-rs`,
`Version: 0.5.0` (version single-sourced from Cargo.toml; adding
`dynamic = ["version"]` silenced the maturin warning).

`pip install --force-reinstall --no-deps <wheel>` →
`import tsxtract` → `.../site-packages/tsxtract/__init__.py 0.5.0`.
`import tsxtractor` → `DeprecationWarning: The 'tsxtractor' import name is
deprecated and will be removed no earlier than version 0.7.0; ...` + works.

`python -m pytest tests -x -q` → **138 passed**, 1 warning (the expected
shim DeprecationWarning), 16.35s.

`feature_names()` sha256 → `8a1e2794…431af` — UNCHANGED vs Phase 0.

`cargo clippy --all-targets -- -D warnings` → exit 0.
`cargo fmt --check` → exit 0.

Clean venv (`Temp\opencode\cleanvenv`, wheel + numpy only):
`extract_features((8, 64))` → shape (8, 33), all finite; feature hash match;
`__version__ 0.5.0`. `python -W error::DeprecationWarning -c "import
tsxtractor"` → DeprecationWarning raised. Shim identity
(`tsxtractor.extract_features is tsxtract.extract_features`) ok.

`python benches/smoke.py` → 10/10 adapters processed (jax adapter ERROR by
design); tracked result files reverted afterwards (`git checkout --`).

`python -m mypy python/tsxtract` → same 10 pre-existing errors as Phase 0
(stale `_core.pyi`; fix in Phase 4), no new errors.

Residual scan (`\btsxtractor\b`, `\bTsxtractor\b`, install-line patterns):
only allowlisted hits remain (see `docs/refactor/naming.md`).

## Files renamed via `git mv`

- `python/tsxtractor/{select,tune}.py` + `_core.pyi` → `python/tsxtract/`
- `python/tsxtractor/py.typed` removed (kept `python/tsxtract/py.typed`)
- `python/tsxtract/__init__.py`: real package; `python/tsxtractor/__init__.py`: shim
- Scripted pass touched 70 files + 18 URL/handle files; hand-fixed:
  `pyproject.toml` (incl. duplicate `python-packages` the script created),
  bench adapters, `release.yml` smoke test, `test_python_api.py`,
  `parity_matrix.md` header, `mkdocs.yml` repo_name, README note, CHANGELOG.
