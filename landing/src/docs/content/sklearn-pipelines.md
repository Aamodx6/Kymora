---
title: "Scikit-Learn Pipelines & Transformers"
description: "Encapsulating Tsxtract inside Scikit-Learn pipelines, custom estimators, cross-validation, and leak prevention."
order: 7
section: "Guides"
---

Wrap extraction in a stateless transformer so scaling, selection, and classification compose into one reproducible pipeline object. Extraction itself is deterministic per series, so leakage control focuses on everything fitted after it.

```python
import numpy as np
import tsxtractor
from sklearn.base import BaseEstimator, TransformerMixin
class TsxtractTransformer(BaseEstimator, TransformerMixin):
    def fit(self, X, y=None):
        return self
    def transform(self, X):
        return tsxtractor.extract_features(np.ascontiguousarray(X, dtype=np.float64))
rng = np.random.default_rng(42)
X = np.ascontiguousarray(rng.standard_normal((20, 120)))
print(TsxtractTransformer().fit_transform(X).shape)
```

```text
(20, 33)
```

## Goal

By the end of this guide you will be able to:

- Write a `TsxtractTransformer` compatible with `Pipeline` and `GridSearchCV`.
- Chain extraction with scaling and a classifier in one object.
- Tune hyperparameters with cross-validation over full series.
- State exactly where leakage can and cannot enter.
- Persist and reload the fitted pipeline for serving.

## Prerequisites

You need scikit-learn alongside Tsxtract, plus an understanding of two terms:

- **Estimator:** any object with `fit()` that learns parameters from training data.
- **Transformer:** an estimator with `transform()` that converts input rows into a new representation.

```bash
pip install "tsxtractor[pandas]" scikit-learn
```

## Steps

### 1. Build the custom transformer

A transformer is a class mixing in `BaseEstimator` and `TransformerMixin` with `fit()` returning `self`. Extraction learns nothing, so `fit()` is a no-op and all work happens in `transform()`.

```python
import numpy as np
import tsxtractor
from sklearn.base import BaseEstimator, TransformerMixin
class TsxtractTransformer(BaseEstimator, TransformerMixin):
    """Extract 33 Tsxtract features per input row (one series per row)."""
    def fit(self, X, y=None):
        return self
    def transform(self, X):
        X = np.ascontiguousarray(X, dtype=np.float64)
        return tsxtractor.extract_features(X)
```

### 2. Assemble the pipeline

A pipeline is an ordered list of `(name, estimator)` steps where every step except the last is a transformer. This one extracts, standardizes columns, and classifies.

```python
from sklearn.ensemble import HistGradientBoostingClassifier
from sklearn.pipeline import Pipeline
from sklearn.preprocessing import StandardScaler
pipe = Pipeline([
    ("features", TsxtractTransformer()),
    ("scaler", StandardScaler()),
    ("clf", HistGradientBoostingClassifier(random_state=42)),
])
print([name for name, _ in pipe.steps])
```

```text
['features', 'scaler', 'clf']
```

### 3. Train and evaluate

Split raw series (not features) so the test partition stays untouched until scoring. The pipeline extracts separately on each side of the split.

```python
from sklearn.model_selection import train_test_split
rng = np.random.default_rng(42)
c0 = rng.standard_normal((100, 120))
t = np.linspace(0, 5, 120)
c1 = rng.standard_normal((100, 120)) + 0.5 * t
X = np.ascontiguousarray(np.vstack([c0, c1]))
y = np.array([0] * 100 + [1] * 100)
X_train, X_test, y_train, y_test = train_test_split(
    X, y, test_size=0.3, random_state=0, stratify=y
)
pipe.fit(X_train, y_train)
print("Pipeline test score:", round(float(pipe.score(X_test, y_test)), 4))
```

```text
Pipeline test score: 1.0
```

### 4. Tune with GridSearchCV

`GridSearchCV` is exhaustive search over a parameter grid with cross-validation. Name extraction-adjacent parameters with the `step__parameter` convention; here the classifier's iteration budget is tuned.

```python
from sklearn.model_selection import GridSearchCV
grid = GridSearchCV(pipe, {"clf__max_iter": [50, 100]}, cv=2)
grid.fit(X_train, y_train)
print("Best params:", grid.best_params_)
print("Best CV score:", round(float(grid.best_score_), 4))
```

```text
Best params: {'clf__max_iter': 50}
Best CV score: 1.0
```

### 5. Persist the fitted pipeline

Serialize the whole fitted object so serving replays identical extraction, scaling, and classification without reimplementing any step.

```python
import pickle
with open("tsxtract_pipe.pkl", "wb") as fh:
    pickle.dump(grid.best_estimator_, fh)
with open("tsxtract_pipe.pkl", "rb") as fh:
    loaded = pickle.load(fh)
print("Reloaded score:", round(float(loaded.score(X_test, y_test)), 4))
```

```text
Reloaded score: 1.0
```

> [!IMPORTANT]
> Leakage is about fitted state, and extraction has none. `TsxtractTransformer.fit()` learns nothing, so extracting before the split cannot leak. `StandardScaler`, feature selectors, and the classifier do learn, so they must be fitted inside the pipeline on training folds only — never pre-fitted on the full dataset.

## Complete example

End-to-end transformer, pipeline, tuning, and persistence in one file:

```python
import pickle
import numpy as np
import tsxtractor
from sklearn.base import BaseEstimator, TransformerMixin
from sklearn.ensemble import HistGradientBoostingClassifier
from sklearn.model_selection import GridSearchCV, train_test_split
from sklearn.pipeline import Pipeline
from sklearn.preprocessing import StandardScaler
class TsxtractTransformer(BaseEstimator, TransformerMixin):
    def fit(self, X, y=None):
        return self
    def transform(self, X):
        return tsxtractor.extract_features(np.ascontiguousarray(X, dtype=np.float64))
rng = np.random.default_rng(42)
c0 = rng.standard_normal((100, 120))
t = np.linspace(0, 5, 120)
c1 = rng.standard_normal((100, 120)) + 0.5 * t
X = np.ascontiguousarray(np.vstack([c0, c1]))
y = np.array([0] * 100 + [1] * 100)
X_train, X_test, y_train, y_test = train_test_split(X, y, test_size=0.3, random_state=0, stratify=y)
pipe = Pipeline([
    ("features", TsxtractTransformer()),
    ("scaler", StandardScaler()),
    ("clf", HistGradientBoostingClassifier(random_state=42)),
])
grid = GridSearchCV(pipe, {"clf__max_iter": [50, 100]}, cv=2)
grid.fit(X_train, y_train)
print("Test score:", round(float(grid.score(X_test, y_test)), 4))
with open("tsxtract_pipe.pkl", "wb") as fh:
    pickle.dump(grid.best_estimator_, fh)
print("Saved:", type(grid.best_estimator_).__name__)
```

```text
Test score: 1.0
Saved: Pipeline
```

## Common pitfalls

- **Pre-extracting then scaling globally:** fitting `StandardScaler` on all rows before `train_test_split` leaks test statistics into training. Keep the scaler inside the pipeline.
- **Selecting features on full data:** variance or importance filters fitted before splitting have seen the test set. Fit selectors inside the pipeline or on training features only.
- **1D input to the transformer:** single-series rows still need 2D shape `(1, length)`. Reshape upstream or route through `sliding_features()` for windowed inference.
- **NaN rows in training:** a NaN anywhere blanks that row's 33 columns, and most estimators reject NaN. Impute series before extraction or drop affected rows.

## Next steps

From pipelines to production scale and slimmer inputs:

- [Selecting Feature Subsets](/docs/selecting-features) — variance and importance filtering without leakage.
- [Large Datasets & Streaming](/docs/large-datasets) — chunked extraction for millions of series.
- [Core Concepts](/docs/core-concepts) — the NaN contract behind the imputation advice.
