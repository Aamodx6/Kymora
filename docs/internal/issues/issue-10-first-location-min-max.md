---
title: "feat: Add first_location_of_maximum and first_location_of_minimum"
labels: ["features", "good first issue", "temporal"]
---

## Context
Relative temporal position of extremes is a standard descriptor in time-series classification (e.g. `tsfresh.first_location_of_maximum`). It represents the index of the first occurrence of the series global maximum/minimum, normalized by length: $\tau_{\max} = \arg\max_t(x_t) / N$.

## Acceptance Criteria
1. Implement single-pass scan recording the index of the first maximum and minimum in `src/features/extrema.rs`.
2. Normalize index to $[0.0, 1.0]$.
3. For constant series, return $0.0$.
4. Register under `extended` profile.

## Files to Touch
- `src/features/extrema.rs`
- `src/plan.rs`

## Tests to Add
- `tests/unit/test_extrema_locations.py`: Test on step, ramp, sinusoid, and noisy signals vs `np.argmax(x) / len(x)`.
