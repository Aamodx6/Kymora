# Float32 input and output

Float32 is supported end to end where the kernels allow it, with no silent
conversions anywhere.

## What works

| Call | f32 input | Notes |
|---|---|---|
| `extract_features` 2D / list | yes | Native narrow read, float64 accumulation; matches float64 on the same values within rtol 1e-4 (measured max 8.8e-6) |
| `extract_features_ragged` CSR | yes | Same agreement |
| `extract_features` + `minimal` / core33 subsets | yes | Gathered from a full core33 row, still zero-copy |
| `extract_features` + `extended` / `full` / non-raw views | **no** | Raises `ValueError` (f32 kernels implement core33 only); pass float64. This path previously panicked across the FFI boundary. |
| `sliding_features`, `extract_features_mc`, streaming | **no** | `ValueError`; pass float64 |

## Precision rules

- Accumulation is always float64. Float32 samples widen exactly on read,
  so the only differences vs the float64 pipeline are f32-arithmetic
  rounding inside a few kernels (worst measured: second differences).
- The float64 path is unchanged and bit-identical release to release.
- `out_dtype="float32"` casts on write (default `"float64"`).
- `precision` accepts `"float64"`/`"float32"` (anything else raises
  `ValueError`) but is currently informational: the input dtype governs
  the read path either way. It never triggers a silent downcast.

```python
import numpy as np
import kymora

X32 = np.ascontiguousarray(np.random.default_rng(0).standard_normal((1000, 500)).astype(np.float32))
feats = kymora.extract_features(X32)                       # (1000, 33) float64
small = kymora.extract_features(X32, out_dtype="float32")  # (1000, 33) float32
```
