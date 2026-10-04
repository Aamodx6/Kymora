# sktime Adapter Tuning Notes

## Library Overview
- **Name:** sktime
- **Version:** >=0.30.0
- **Purpose:** Scikit-learn unified framework for machine learning with time series.

## Fast Configuration & Tuning
- **Transformers Evaluated:**
  1. `Catch22`: sktime's scikit-learn compatible wrapper around pycatch22.
  2. `TSFreshFeatureExtractor`: sktime's wrapper around tsfresh using `default_fc_parameters="efficient"`.
- **Parallelism:** Evaluates `n_jobs=threads` across panel inputs.
