---
title: "Selecting Feature Subsets"
description: "Techniques for pruning redundant metrics, filtering by variance, and selecting domain-specific feature groups with TsxSelector."
order: 9
section: "Guides"
---

Feature selection reduces model complexity, prevents overfitting, and speeds up inference. `tsxtractor` provides both high-level automated supervised selection (`select_features`, `TsxSelector`) and manual domain-guided filtering.

```python
import numpy as np
import tsxtractor

rng = np.random.default_rng(42)
X = rng.standard_normal((100, 500))
y = rng.integers(0, 2, size=100)

F = tsxtractor.extract_features(X)

# Fast automated feature selection with FDR control
selected_idx, report = tsxtractor.select_features(F, y, task="classification", fdr=0.05)
print(f"Selected {len(selected_idx)} non-redundant features.")
```

## Native Supervised Selection (`TsxSelector`)

`tsxtractor.TsxSelector` is a scikit-learn compatible transformer that:
1. Computes univariate relevance statistics (ANOVA F-statistic for classification, Pearson correlation for regression).
2. Controls the False Discovery Rate (FDR) using the Benjamini-Hochberg procedure at a configurable threshold $\alpha$ (default `0.05`).
3. Clusters surviving features by pairwise correlation and prunes collinear duplicates (`max_corr=0.90`).

```python
from sklearn.pipeline import Pipeline
from sklearn.ensemble import HistGradientBoostingClassifier

pipeline = Pipeline([
    ("selector", tsxtractor.TsxSelector(task="classification", fdr=0.05)),
    ("classifier", HistGradientBoostingClassifier())
])

pipeline.fit(F, y)
predictions = pipeline.predict(F)
```

## Manual Feature Filtering

### 1. Slice Domain Groups by Name

Group features by physical properties and resolve indices dynamically:

```python
names = tsxtractor.feature_names()

groups = {
    "level": ["mean", "median", "min", "max"],
    "spread": ["std", "var", "quantile_10", "quantile_90"],
    "dynamics": ["mean_abs_change", "mean_change", "cid_ce"],
    "rhythm": ["autocorr_lag_1", "autocorr_lag_5", "trend_slope", "trend_r2"],
    "spectrum": ["dominant_frequency", "spectral_centroid", "spectral_entropy"],
}

dynamics_idx = [names.index(n) for n in groups["dynamics"]]
F_dynamics = F[:, dynamics_idx]
```

### 2. Variance and Degeneracy Filtering

Filter zero-variance columns caused by constant or calibration series:

```python
variances = F.var(axis=0)
live_indices = np.where(variances > 1e-12)[0]
F_live = F[:, live_indices]
```

### 3. Tree-Based Importance Ranking

Rank features using gradient boosting or random forest feature importances:

```python
from sklearn.ensemble import RandomForestClassifier

rf = RandomForestClassifier(n_estimators=100, random_state=42)
rf.fit(F_live, y)

ranked = np.argsort(rf.feature_importances_)[::-1]
top_5_features = [names[live_indices[i]] for i in ranked[:5]]
print("Top 5 features:", top_5_features)
```

## Best Practices

- **Avoid Leakage:** Always fit `TsxSelector` on training folds only. Fitting on the entire dataset leaks label distributions.
- **Index Safety:** Never hardcode integer indices. Use `names.index(col_name)` or `TsxSelector.get_support()`.
- **Interpretability:** Use the detailed tabular report returned by `select_features` to inspect p-values and cluster exemplars.
