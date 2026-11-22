---
title: "ux: Enhance error message on non-contiguous multichannel inputs"
labels: ["ux", "good first issue", "diagnostics"]
---

## Context
When multi-channel inputs passed to `extract_features_mc` are non-contiguous (e.g. slices from a Fortran-ordered array) and `contiguous="error"` is set, the exception message could offer clearer remediation advice.

## Acceptance Criteria
1. Intercept non-contiguous 3D arrays or lists of 2D arrays early in Python validation layer.
2. Format an informative `ValueError` stating the exact strides and shape, and recommend using `np.ascontiguousarray(...)` or setting `contiguous="copy"`.
3. Ensure no performance regression on already-contiguous inputs.

## Files to Touch
- `python/kymora/multichannel.py`
- `tests/unit/test_multichannel.py`

## Tests to Add
- Unit test verifying the exact wording and guidance of the raised `ValueError`.
