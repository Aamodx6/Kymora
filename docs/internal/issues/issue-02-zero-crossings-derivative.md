---
title: "feat: Implement zero_crossings_derivative feature"
labels: ["enhancement", "good first issue", "signal-processing"]
---

## Context
In audio and vibration analysis, the zero-crossing rate of the first difference (derivative) $\Delta x_t = x_{t+1} - x_t$ measures signal roughness and high-frequency noise modulation.

## Acceptance Criteria
1. Compute the first difference: $d_t = x_{t+1} - x_t$.
2. Count the number of zero crossings in $d_t$: instances where $d_t \cdot d_{t+1} < 0$.
3. Normalize by $(N - 2)$ to yield a rate in $[0, 1]$.
4. Constant or linear signals return $0.0$. Series with length $N < 3$ return `NaN`.

## Files to Touch
- `src/features/temporal.rs`: Kernel implementation.
- `src/plan.rs`: Feature bitflag registration.

## Tests to Add
- `tests/unit/test_zero_crossings_derivative.py`: Verification against NumPy reference `np.sum((np.diff(x)[:-1] * np.diff(x)[1:]) < 0) / (len(x) - 2)`.
