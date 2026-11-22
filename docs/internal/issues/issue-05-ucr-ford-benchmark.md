---
title: "bench: Add FordA and FordB UCR benchmark pipeline"
labels: ["benchmarks", "good first issue", "reproducibility"]
---

## Context
The UCR archive contains FordA and FordB datasets (automotive subsystem sensor classification with $N=3,601$ train and $N=1,320$ test series, length $L=500$). These represent real-world acoustic diagnosis tasks.

## Acceptance Criteria
1. Add an automated download and caching runner for FordA/FordB in `benchmarks/suites/ucr/`.
2. Extract features using Kymora `core33`, `catch22`, `TSFEL`, and `tsfresh`.
3. Train standard RidgeClassifier and RandomForest on extracted features.
4. Output classification accuracy, macro F1, and wall-clock extraction time.

## Files to Touch
- `benchmarks/suites/ucr/run_ford_bench.py`: Script orchestration.
- `docs/benchmarks.md`: Document findings if added to standardized benchmarks.

## Tests to Add
- Smoke test in `tests/test_bench_smoke.py` verifying the script runs with a synthetic mock dataset.
