---
title: "feat: Add sample_entropy feature to extended profile"
labels: ["enhancement", "good first issue", "mathematics"]
---

## Context
Sample Entropy ($SampEn$) is a popular measure of time series regularity and complexity, commonly used in physiological signal analysis (ECG, EEG) and mechanical vibration monitoring. It measures the log likelihood that runs of patterns that are close remain close on next incremental comparisons.

$$\text{SampEn}(m, r, N) = -\ln \frac{A}{B}$$
where $m$ is the template length (default $m=2$), $r$ is the tolerance threshold (default $r = 0.2 \times \sigma$), $B$ is the count of template matches of length $m$, and $A$ is the count of template matches of length $m+1$.

## Acceptance Criteria
1. Implement `sample_entropy(x, m=2, r=0.2)` in `src/features/` with an $O(N^2)$ scalar fallback or SIMD-accelerated distance check.
2. Register the feature under `FeaturePlan::SAMPLE_ENTROPY` in the `extended` profile.
3. Validate against `scipy` or `antropy.sample_entropy` reference values with relative tolerance $< 10^{-6}$.
4. Handle edge cases: constant series (should return 0.0 or defined baseline), series length $N < m + 2$ (returns `NaN`).

## Files to Touch
- `src/features/entropy.rs`: Feature kernel implementation.
- `src/plan.rs`: Add feature to `FeaturePlan` and registry.
- `python/kymora/__init__.py`: Update docstrings if exposed directly.

## Tests to Add
- `tests/unit/test_sample_entropy.py`: Parity against reference values on Gaussian and periodic signals.
- `tests/property/test_invariances.py`: Assert scale and translation properties if applicable.
