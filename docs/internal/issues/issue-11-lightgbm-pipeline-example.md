---
title: "docs: End-to-end classification pipeline with KymoraTransformer and LightGBM"
labels: ["documentation", "examples", "good first issue", "machine-learning"]
---

## Context
`kymora.sklearn.KymoraTransformer` implements the standard Scikit-Learn transformer API (`fit`/`transform`/`get_feature_names_out`). Demonstrating integration into a gradient boosting pipeline (e.g. `Pipeline([('extract', KymoraTransformer()), ('clf', LGBMClassifier())])`) helps machine learning practitioners adopt Kymora.

## Acceptance Criteria
1. Add a self-contained script `docs/examples/lightgbm_pipeline.py`.
2. Generate synthetic multivariate time-series classification dataset.
3. Construct `sklearn.pipeline.Pipeline` with `KymoraTransformer` and `LightGBM` (with graceful fallback to `HistGradientBoostingClassifier`).
4. Evaluate cross-validation score and latency.

## Files to Touch
- `docs/examples/lightgbm_pipeline.py`
- `docs/sklearn.md`

## Tests to Add
- Add execution test in `tests/test_sklearn.py`.
