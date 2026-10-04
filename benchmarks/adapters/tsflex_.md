# tsflex Adapter Tuning Notes

## Library Overview
- **Name:** tsflex
- **Version:** >=0.3.0
- **Purpose:** Time-series feature extraction toolkit optimized for sliding windows and multiple series.

## Fast Configuration & Tuning
- **Input Format:** Requires timestamp-indexed pandas `Series` or `DataFrame`.
- **Parallelism:** Supports multi-core calculation via `n_jobs=threads`.
- **Windowing:** Used in Suite Sliding to compare Tsxtract's native zero-copy windowed execution vs tsflex windowing.
