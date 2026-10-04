# tsfresh Adapter Tuning Notes

## Library Overview
- **Name:** tsfresh
- **Version:** >=0.20.0
- **Implementation:** Python + multiprocessing with pandas DataFrame input/output.

## Fast Configuration & Tuning
- **Parameter Sets:**
  - `efficient`: `EfficientFCParameters()` (~770 features, excludes combinatorial / quadratic features).
  - `comprehensive`: `ComprehensiveFCParameters()` (all ~790+ features).
  - `minimal`: `MinimalFCParameters()` (~8 summary statistics).
- **Parallelism:** Set via `n_jobs=threads`. Uses Python multiprocessing workers.
- **Reporting Views:**
  1. `end-to-end`: Includes flat 2D NumPy array reshaping into `id`-indexed long-format pandas DataFrame.
  2. `extract-only`: Evaluates feature computation time assuming the long DataFrame is already materialized in memory.
