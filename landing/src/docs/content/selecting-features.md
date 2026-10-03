---
title: "Selecting Feature Subsets"
description: "Techniques for pruning redundant metrics, filtering by variance, and selecting domain-specific feature groups."
order: 9
section: "Guides"
---

Thirty-three columns are cheap to compute but not all pull weight for every task. Slice by name for domain priors, drop zero-variance columns, and rank the rest with model-based importance — always resolving positions through `feature_names()`.

```python
import numpy as np
import tsxtractor
rng = np.random.default_rng(4)
F = tsxtractor.extract_features(np.ascontiguousarray(rng.standard_normal((50, 100))))
names = tsxtractor.feature_names()
keep = [names.index(n) for n in ["mean", "std", "trend_slope", "spectral_entropy"]]
print("Subset shape:", F[:, keep].shape)
print("Columns with variance:", int((F.var(axis=0) > 0).sum()))
```

```text
Subset shape: (50, 4)
Columns with variance: 33
```

## Goal

By the end of this guide you will be able to:

- Slice domain-motivated feature groups by name.
- Remove zero-variance and NaN-heavy columns safely.
- Rank features with tree-based importance.
- Avoid leakage when selection learns from data.
- Keep column meaning stable across code changes.

## Prerequisites

You need NumPy plus scikit-learn for the ranking step, and one definition:

- **Variance filter:** dropping columns whose values barely vary across rows, since constants cannot discriminate classes.

```bash
pip install "tsxtract-rs[pandas]" scikit-learn
```

## Steps

### 1. Slice domain groups by name

Feature groups map to signal properties, so start from physics rather than statistics. Resolve every position with `names.index(name)` so registry appends never break your code.

```python
groups = {
    "level": ["mean", "median", "min", "max"],
    "spread": ["std", "var", "quantile_10", "quantile_90"],
    "dynamics": ["mean_abs_change", "mean_change", "cid_ce"],
    "rhythm": ["autocorr_lag_1", "autocorr_lag_5", "trend_slope", "trend_r2"],
    "spectrum": ["dominant_frequency", "spectral_centroid", "spectral_entropy"],
}
idx = [names.index(n) for n in groups["dynamics"]]
print("Dynamics block:", F[:, idx].shape)
```

```text
Dynamics block: (50, 3)
```

### 2. Drop zero-variance columns

A constant column carries no signal for any classifier. On real heterogeneous batches this mostly bites for degenerate inputs, such as constant calibration series where `std` is exactly zero.

```python
variances = F.var(axis=0)
live = np.where(variances > 0)[0]
print("Live columns:", len(live), "of", F.shape[1])
F_live = F[:, live]
print(F_live.shape)
```

```text
Live columns: 33 of 33
(50, 33)
```

### 3. Drop NaN-heavy columns

Columns that are NaN for most rows (for example spectral features over constant-heavy batches) destabilize scalers and trees. Measure the NaN fraction per column, then cut.

```python
nan_frac = np.isnan(F).mean(axis=0)
usable = np.where(nan_frac < 0.2)[0]
print("Usable columns:", len(usable))
print("Worst NaN fraction:", round(float(nan_frac.max()), 4))
```

```text
Usable columns: 33
Worst NaN fraction: 0.0
```

### 4. Rank with tree-based importance

A random forest is an ensemble of decision trees whose split statistics yield per-feature importance scores. Fit on training rows only, then keep the top-k names for the final model.

```python
from sklearn.ensemble import RandomForestClassifier
y = np.array([0] * 25 + [1] * 25)
forest = RandomForestClassifier(n_estimators=100, random_state=42)
forest.fit(F_live, y)
ranked = np.argsort(forest.feature_importances_)[::-1]
top_names = [names[i] for i in ranked[:5]]
print("Top 5:", top_names)
```

```text
Top 5: ['trend_slope', 'mean_change', 'mean_second_derivative_central', 'trend_r2', 'permutation_entropy']
```

> [!IMPORTANT]
> Fit every learning selector on training rows only. Importances, variance thresholds, and scalers computed on the full matrix leak test information into the pipeline — wrap them in a `Pipeline` as shown in [Scikit-Learn Pipelines](/docs/sklearn-pipelines).

## Complete example

Name-based shortlist, variance filter, and importance ranking composed into one reusable selection:

```python
import numpy as np
import tsxtractor
from sklearn.ensemble import RandomForestClassifier
rng = np.random.default_rng(4)
F = tsxtractor.extract_features(np.ascontiguousarray(rng.standard_normal((50, 100))))
names = tsxtractor.feature_names()
y = np.array([0] * 25 + [1] * 25)
live = np.where(F.var(axis=0) > 0)[0]
forest = RandomForestClassifier(n_estimators=100, random_state=42)
forest.fit(F[:, live], y)
ranked = live[np.argsort(forest.feature_importances_)[::-1][:5]]
selected = [names[i] for i in ranked]
print("Selected:", selected)
print("Reduced shape:", F[:, ranked].shape)
```

```text
Selected: ['trend_slope', 'mean_change', 'mean_second_derivative_central', 'trend_r2', 'permutation_entropy']
Reduced shape: (50, 5)
```

## Common pitfalls

- **Hardcoded column indices:** registry order is stable within a major version, but literals still rot when features append. Always use `names.index(name)`.
- **Selecting on the full dataset:** filters fitted before the train/test split leak. Split raw series first, then select inside training folds.
- **Dropping NaN columns blindly:** a high-NaN column may flag constant inputs your model should know about. Inspect which rows go NaN before cutting.
- **Keeping everything by default:** all 33 columns are fine for gradient boosting, but linear models and tiny datasets prefer the ranked shortlist.

## Next steps

From selection to training and reference detail:

- [Scikit-Learn Pipelines](/docs/sklearn-pipelines) — leakage-free selection inside pipelines.
- [Feature Catalog](/docs/feature-catalog) — group membership for all 33 features.
- [Core Concepts](/docs/core-concepts) — which inputs produce NaN columns.
