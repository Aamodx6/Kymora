# Contributing to kymora

Thanks for looking. This project has a deliberately small surface, so the most
useful contributions are usually correctness work, docs, and platform support
rather than new features — please read [Adding a feature](#adding-a-feature)
before opening a PR that adds one.

## Setup

You need a [Rust toolchain](https://rustup.rs/) and Python 3.10+.

```bash
git clone https://github.com/Aamodx6/Kymora
cd Kymora
python -m venv .venv
. .venv/bin/activate          # .venv\Scripts\activate on Windows
pip install maturin
pip install -e ".[test]"
maturin develop --release
```

Always build with `--release`. A debug build is roughly an order of magnitude
slower, which makes every timing observation meaningless.

## Checks

Run all of these before opening a PR; CI runs the same set.

```bash
pytest tests/                        # Python-visible behaviour
cargo test --no-default-features     # pure-Rust unit tests
cargo fmt --all -- --check
cargo clippy --no-default-features --all-targets -- -D warnings
python tools/validation_report.py  # exits non-zero if a feature drifts
```

`--no-default-features` disables `pyo3/extension-module`, which omits libpython
at link time; a test binary cannot link without it, so `cargo test` needs the
flag.

After editing **any** source in `python/` or `src/`, rebuild and reinstall
before running `pytest` — the interpreter imports the installed package, not
the working tree, so a stale wheel makes tests silently run old code:

```bash
maturin develop --release
```

## Benchmarks

The benchmark suite is plain Python; these commands work on any OS (the
`Makefile` and `reproduce.sh` are optional wrappers over the same sequence
for `make`/bash environments):

```bash
python benchmarks/setup_venvs.py --lib all  # isolated competitor environments
python benchmarks/smoke.py                  # B0 smoke test (all adapters)
python benchmarks/suites/agreement.py       # B1 feature agreement / parity
python benchmarks/reproduce.py --suite all  # full matrix (B1-B5)
python benchmarks/report/make_report.py     # REPORT.md + results.json
```

Run outputs under `benchmarks/results/` are artifacts — keep them out of
commits unless a phase record explicitly says otherwise.

## Architecture rules

Three constraints keep the correctness story tractable. A PR that breaks one will
be asked to change approach, not just to fix a test.

1. **No numeric logic in Python.** `python/kymora/__init__.py` is a
   pass-through with docstrings. All math lives in `src/features/`, so there is
   exactly one implementation to validate.
2. **No panic may cross the FFI boundary.** No `unwrap`, `expect`, or panicking
   index on a user-reachable path in `src/ffi.rs` or `src/extract.rs`. Fallible
   steps return `Result<_, KymoraError>`; `src/error.rs` is the single conversion
   point to `PyErr`.
3. **Structural errors and NaN values stay separate.** `KymoraError` describes
   shapes, lengths, and layout — never the values in a series. NaN is a value
   with a documented propagation contract. Do not let those code paths merge.

Validation happens before the parallel region, so a bad input fails immediately
instead of after occupying worker threads.

## Adding a feature

The 33-feature set is closed on purpose — the low-redundancy set *is* the product
differentiation, not a limitation to engineer around. Open a **New feature
proposal** issue first and get agreement before writing code; PRs that add a
feature without one may be closed on scope grounds regardless of quality.

Once agreed:

1. Implement it in the relevant `src/features/*.rs` (or a new module for a new
   group).
2. Register the name in `src/features/mod.rs`. `NAMES` is the single source of
   truth for `feature_names()` and column order — **append at the end**, never
   insert in the middle, and make sure the write order in `compute_all` matches.
3. Add a numpy/scipy reference to `reference()` in `tests/test_features.py`. The
   existing sample matrix (normal, trending, periodic, constant, two-element,
   single-element, heavily-tied) then covers it automatically.
4. Decide and document its undefined cases in `docs/features.md`, and add a case
   to `tests/test_nan_policy.py` if it introduces a new one.
5. Update `_core.pyi` only if a signature changed — adding a feature does not
   change one.
6. Add a `CHANGELOG.md` entry under `Unreleased`.

## Versioning policy

`feature_names()` order and length are public API.

| Change | Version bump |
|---|---|
| Reordering, renaming, or removing a feature | **major** |
| Appending a new feature at the end | minor |
| Changing which conditions produce a NaN row vs. a NaN cell | **major** |
| Changing output dtype away from float64 | **major** |
| Dropping a Python version or platform | **major** |
| New function, new optional parameter | minor |
| Bug fix with no contract change, docs, internals | patch |

If a PR's version impact is unclear, say so in the description rather than
guessing — see `docs/nan-policy.md#stability` and the compatibility table in
`arch.md`.

## Pull requests

- One logical change per PR. A feature and a refactor in one diff is two PRs.
- Explain *why*, not just what. The diff shows the what.
- New behaviour needs a test that fails without the change.
- Note the version impact per the table above.
- Match the surrounding style: `cargo fmt` for Rust, and comments that explain
  reasoning rather than restating the code.

Everyone participating agrees to follow the
[Code of Conduct](CODE_OF_CONDUCT.md).

## Reporting bugs

Include your OS, Python version, `kymora.__version__`, and a runnable
snippet. For a wrong-value report, include what you expected and how you
computed it (a numpy/scipy expression is ideal) — that turns the report straight
into a test case.
