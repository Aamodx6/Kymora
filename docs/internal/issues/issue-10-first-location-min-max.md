---
title: "feat: Add count_above and count_below threshold features"
labels: ["features", "good first issue", "distribution"]
---

## Context
Threshold exceedance counts are standard features in time-series anomaly detection and feature extraction catalogs (e.g. `tsfresh.count_above`, `tsfresh.count_below`). They compute the fraction of samples strictly greater than or less than a specified threshold value $\theta$: $f(x, \theta) = \frac{1}{N}\sum_{t=1}^N \mathbb{I}(x_t > \theta)$.

## Acceptance Criteria
1. Implement single-pass scan counting values above and below threshold $\theta$ in `src/features/distribution.rs`.
2. Normalize count by length $N$ to yield a fraction in $[0.0, 1.0]$.
3. Default parameter $\theta = 0.0$ or user-specified value.
4. Register under `extended` and `full` profiles.

## Files to Touch
- `src/features/distribution.rs`
- `src/plan.rs`

## Tests to Add
- `tests/unit/test_threshold_counts.py`: Verification against NumPy reference `np.mean(x > theta)` and `np.mean(x < theta)`.
