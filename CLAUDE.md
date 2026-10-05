# CLAUDE.md

Guidance for AI coding agents working in this repository. The architecture
source of truth is `arch.md` — read it before changing `src/`. Human
contributor rules are in `CONTRIBUTING.md`.

## Dev loop (critical)

pytest imports the **installed** package (site-packages), not `python/kymora/`
from the working tree. After any change to Python or Rust source:

```bash
maturin develop --release        # inside an active venv (maturin requires one)
# or, without a venv:
python -m maturin build --release
pip install --force-reinstall --no-deps target/wheels/kymora-*.whl
```

Bare `maturin build` is a debug build (~10× slower) — always `--release` for
anything measured or benchmarked.

## Gates (run before claiming done)

```bash
pytest tests -q                              # must be 138 passed, 0 warnings
cargo test --no-default-features
cargo fmt --all -- --check
cargo clippy --no-default-features --all-targets -- -D warnings
python tools/validation_report.py          # feature-drift check
python -m mkdocs build --strict
python -m mypy python/kymora
```

Feature-order invariant: `feature_names()` must keep sha256
`8a1e27942b370ec886130db4f19ca973b2a1b36ea17823723c9d7afd1431af2e`
(33 names) unless the PR intentionally changes public API.

## Hard rules

- **Numeric logic lives only in Rust** (`src/features/`); Python is a
  pass-through. No new computation in `python/`.
- **No panic crosses the FFI boundary**: no `unwrap`/`expect`/panicking index
  on user-reachable paths in `src/ffi.rs`.
- **Structural errors vs NaN values stay separate**: `KymoraError` never describes
  values; NaN has its own documented propagation contract (`docs/nan-policy.md`).
- Naming: import `kymora`, PyPI dist `kymora` (bare `tsxtract` on PyPI is an
  unrelated JAX project — never `pip install tsxtract`), crate `kymora`,
  `KymoraSelector`. No shims, no aliases — `tsxtract`/`tsxtractor` are gone.
- Never edit `benchmarks/results/` artifacts in place; never `git add -A`
  (bench run outputs must stay untracked).

## Layout

- `src/` Rust core; unsafe only in `ffi.rs` (helpers + SAFETY contract) and
  `kernels/` by convention (`#![deny(unsafe_code)]` elsewhere).
- `python/kymora/` real package (`__init__.py`, `select.py`, `tune.py`,
  `_core.pyi`); no other top-level packages.
- `tests/` goldens in `tests/golden/` — never regenerate to "fix" a failure
  without understanding the drift first.
- `docs/` mkdocs site (deployed by `.github/workflows/docs.yml`);
  `landing/` marketing site (Vercel, separate); no mirroring between them.
- `benchmarks/` suite; `make` targets wrap plain `python benchmarks/...`
  commands (raw commands are the portable path, esp. on Windows).

## State tracking

Ongoing work is tracked in `docs/REFACTOR_STATE.md` (phases, decisions,
NEEDS-OWNER items). Phase records live in `docs/refactor/phaseN_VERIFICATION.md`.
