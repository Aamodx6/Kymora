# Phase 4 verification — rename to Kymora (2026-10-04)

Owner confirmations applied mid-phase: final name **Kymora**, bare (no `-rs`
suffix — bare `kymora` is FREE on PyPI/crates.io/npm per Phase 1), and the
older `tsxtractor` alias **deleted outright** instead of kept as a shim.

## Method (scripted, once)

- `tools/rename_to_kymora.py` — main pass (120 files, 967 replacements) +
  `--apply-pass2` (97: env vars, adapter/func identifiers, `tsx`→`km`
  aliases) + `--apply-pass3` (77: bare-`kymora` per owner direction).
  Rules are ordered, word-boundary, case-sensitive; `tsxtractor` and
  `tsxtract_jax` never match by construction.
- File moves via `git mv`: `python/tsxtract/` → `python/kymora/`,
  `benchmarks/adapters/tsxtract.{py,md}` → `kymora.*`,
  `benchmarks/requirements-tsxtract.txt` → `requirements-kymora.txt`,
  `scripts/` → `tools/` (Phase 3).
- Hand-written after the script: `python/kymora/__init__.py`,
  `python/tsxtract/__init__.py` (new single shim),
  `KymoraSelector` + `TsxSelector` alias, `tests/test_python_api.py` shim
  contract, CHANGELOG 0.7.0, `docs/migrating.md` section, `docs/RENAME_RELEASE_CHECKLIST.md`,
  `release.yml` smoke block, CLAUDE naming rule, JAX-note restores.
- `python/tsxtractor/` **deleted** (`git rm`) per owner direction: no
  `km`-style replacement was requested; the single `tsxtract` shim covers
  the migration path. `pyproject.toml` ships `[kymora, tsxtract]` only;
  adapter fallbacks, startup size targets, release smoke, and all live docs
  updated; history/data keys (`feature_map.json`, `tsxtractor_version`,
  B-track rows) untouched.
- Rust: `TsxError` → `KymoraError` (internal only; Python still gets
  `ValueError` with identical messages) + one `cargo fmt` width fix.

## Version + naming (final)

- `Cargo.toml`: crate `kymora` **0.7.0**; `pyproject.toml`: dist **`kymora`**,
  `module-name kymora._core`, `python-packages [kymora, tsxtract, tsxtractor]`.
- Wheel: `kymora-0.7.0-cp310-abi3-win_amd64.whl` builds clean.
- `import kymora` canonical (`as km`); `import tsxtract` warns + re-exports
  identically; removal >= 0.8.0. `import tsxtractor` is gone (deleted outright;
  enforced by `test_tsxtractor_shim_is_gone`).
- `TsxSelector` kept as alias of `KymoraSelector`; env `KYMORA_*`
  (old names/paths not read — documented breaking change, re-run `tune()`).

## Gates (real output)

| Gate | Result |
|---|---|
| wheel build + clean-venv install (`vKYM`, no repo on path) | `import kymora` works: (1000,33), df (5,33); old imports warn + match `kymora` output exactly |
| `feature_names()` hash | **MATCH** `8a1e2794…31af2e` (33 names) |
| golden diff vs `pre-rename` | **EMPTY** (`tests/golden`, `tests/fixtures`) |
| `pytest tests -q` | **139 passed** (138 + shim-gone contract) |
| `cargo test --no-default-features` | **16 passed** |
| `cargo fmt --check` / `clippy -D warnings` | exit **0** / exit **0** |
| `tools/validation_report.py` | all 33 within tolerance |
| `mypy python/kymora` | clean |
| `mkdocs build --strict` | exit **0** (INFO-only) |
| `npm run build` (landing) | ✓ 27.54s (pre-existing chunk warnings only) |
| API dump | 17 symbols = old 16 with `TsxSelector`→`KymoraSelector` + alias retained; differs only by the rename |
| post-rename timing | core33 1k×500 median **2.20 ms** in-process (same regime as F1-era 2.35–3.3 ms pooled) — rename is perf-neutral as expected (no numeric changes) |

## Residual `tsxtract` (case-insensitive) — allowlisted only

- **Frozen/history/evidence/IP (untouched):** `docs/refactor/*`, `benchmarks/results/*`,
  `benchmarks/report/*`, `paper/*`, `patent/*`, `CHANGELOG.md` history sections.
- **B-track evidence (lib id is data):** `benchmarks/STATE.md` (+ header rename note),
  `AGREEMENT_REPORT.md`, `zenith_baseline.md`, `feature_map.json` (`tsxtractor.feature_names()`
  source-of-truth), `baseline.json`, `LOSS_LEDGER.md`; data keys `tsxtract_matched_*`,
  `tsxtract_core33`, `tsxtractor_version`, `vs_tsx_core33` kept for row continuity
  (crossover reader accepts old+new keys).
- **Collision markers (the JAX project is literally named `tsxtract`):**
  `tsxtract_jax.*`, `requirements-jax-collision.txt`, JAX-warning sentences in
  README/CLAUDE/arch/intro, `tsxtract_pipe`→renamed, localStorage keys kept stable.
- **Migration shim (by design):** `python/tsxtract/` (fallback import in
  the `kymora.py` adapter, release smoke check); `python/tsxtractor/` deleted.

## Incidents

- Worktree integrity scare: commit `3e42b2e` accidentally recorded the
  deletion of `python/tsxtract/__init__.py` (the shim to keep) alongside the
  intended `python/tsxtractor/` removal — the file vanished from the working
  tree at an unidentified point after the last clean `git status`, and
  `git add -u` staged the deletion. Caught in post-commit review via
  `git show --stat`; the intact blob was restored from `7e10b38` in the
  follow-up commit, and a full `git diff 8662146 --name-status` audit
  confirmed no other unintended deletions. Installed-wheel tests were
  unaffected throughout (they import from site-packages, not the tree).

- Stale-wheel false alarm (Phase 0): installed 0.5.0 vs repo 0.6.0 — resolved
  by rebuild+reinstall; recorded the dev-loop hazard again.
- Old-dist uninstall wiped shared shim files (`tsxtract-rs` 0.6.0 removal
  deleted `tsxtract/`+`tsxtractor/` owned by both dists) — resolved by
  `kymora` force-reinstall; noted in the release checklist ordering
  (remove old dist first, then install new).

## Gate status

**Phase 4 GATE: PASS** — build + wheel + clean-venv + shims + goldens +
hash + full test/clippy/fmt/mypy/docs/site gates green. Nothing published;
release runbook at `docs/RENAME_RELEASE_CHECKLIST.md` (GitHub rename steps,
`kymora` trusted-publishing setup, `tsxtract-rs` 0.6.1 finale sketch).
