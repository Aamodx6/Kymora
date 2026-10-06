# tools/ — maintainer scripts (each has a one-line docstring; see index)

Scripts only — no packages, no vendored code. Run from the repo root
(`python tools/<script>.py`); several require the built wheel installed
(`pip install target/wheels/kymora-*.whl` after `maturin build --release`).

| Script | One line |
|---|---|
| `check_claims.py` | Check that every numeric claim in README, landing, and docs is present in CLAIMS.md. |
| `check_snippets.py` | Execute every python snippet in README.md + docs/*.md (stdlib only). |
| `feature_redundancy_analysis.py` | Information-Theoretic Feature Redundancy and Collinearity Analysis. |
| `gen_feature_docs.py` | Generate docs/features.md from the built library (Phase 6.2). |
| `name_check.py` | Name-availability check for rename candidates (stdlib only). |
| `perf_gate.py` | Performance regression gate for the core33 hot path (Phase 5.3). |
| `rename_to_kymora.py` | One-shot rename tsxtract -> Kymora (content only; file moves done via git mv). |
| `run_phase0_baseline.py` | Phase 0 Baseline & Profiling Script. |
| `streaming_report.py` | Build the Phase 2.4 streaming artifact from B3 suite rows. |
| `validation_report.py` | Generate the reference-validation report: max absolute error per feature. |

Gates that consume these: `mkdocs build --strict`, `check_claims.py`,
`gen_feature_docs.py --check`, `validation_report.py`, `check_snippets.py`,
`mypy python/kymora`, `perf_gate.py` (see CLAUDE.md).
