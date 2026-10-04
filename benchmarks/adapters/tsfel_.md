# TSFEL Adapter Tuning Notes

## Library Overview
- **Name:** TSFEL (Time Series Feature Extraction Library)
- **Version:** >=0.1.6
- **Implementation:** Python feature extraction with scipy/numpy dependencies.

## Fast Configuration & Tuning
- **Domain Configuration:** Evaluates all three feature domains: `statistical`, `temporal`, and `spectral` (`get_features_by_domain()`).
- **Parallelism:** When `threads > 1`, rows are processed concurrently via `joblib.Parallel(n_jobs=threads, prefer="processes")` to bypass GIL constraints.
- **Reporting:** Measures feature extraction time directly into NumPy matrix rows.
