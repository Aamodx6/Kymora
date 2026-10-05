# NaN policy

The value policy now lives in a single document: [Numerics and NaN
policy](numerics.md). Summary of the contract:

- **NaN is a value; structural problems raise** — the code paths stay
  separate and both are tested.
- `nan_policy="propagate"` (default): any NaN in a series makes that series'
  whole row NaN. `nan_policy="raise"` fails fast naming the series.
  `nan_policy="omit"` is rejected: clean the series first so the imputation
  stays yours and visible.
- Empty input, zero-length series, non-contiguous arrays, and bad
  window/stride raise `ValueError`; wrong dtype/shape raises `TypeError`.
