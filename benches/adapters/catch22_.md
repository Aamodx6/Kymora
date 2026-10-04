# pycatch22 Adapter Tuning Notes

## Library Overview
- **Name:** pycatch22
- **Version:** >=0.4.5
- **Underlying Core:** C implementation of 22 canonical time-series features (hctsa subset).

## Fast Configuration & Tuning
- **Input Format:** Requires 1D lists or 1D arrays per call.
- **Multiprocessing Parallelism:** Because pycatch22 does not natively release Python GIL across a 2D batch, we implement both:
  1. Serial loop (`threads=1` or `feature_set="serial"`).
  2. `multiprocessing.Pool(processes=threads)` batching with optimal `chunksize` for multi-core scaling.
- **Memory Footprint:** Python list allocations per call inside the C wrapper.
