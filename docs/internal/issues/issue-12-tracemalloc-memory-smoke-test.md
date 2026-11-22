---
title: "ci: Automated memory leak and RSS regression smoke test"
labels: ["ci", "testing", "memory", "good first issue"]
---

## Context
Kymora maintains a bounded memory scratch space of 2.29–3.33 MiB across 16 threads and borrows input arrays directly with zero defensive copies. Adding an automated test in CI that asserts memory allocation bounds helps prevent regressions in future PRs.

## Acceptance Criteria
1. Add `tests/unit/test_memory_bounds.py` utilizing Python's `tracemalloc` and `psutil`.
2. Extract features over $N=5,000, L=500$ across 10 iterations.
3. Assert that Python heap growth across iterations is $< 100\ \text{KiB}$ (no uncollected PyObject handles).
4. Assert that peak memory overhead matches expectations documented in `CLAIMS.md`.

## Files to Touch
- `tests/unit/test_memory_bounds.py`
- `.github/workflows/ci.yml`

## Tests to Add
- Run as part of standard `pytest` suite.
