# Numerics and NaN policy

Single source of truth for how kymora treats values at the edges. Two
categories are deliberately kept apart: **NaN is a value; structural problems
raise.** Conflating them is the most common way a feature pipeline hides a
bug, so the code paths are separate and both are tested.

## `nan_policy`

Accepted by `extract_features`, `extract_features_ragged`,
`sliding_features`, `extract_features_mc`, and `StreamingExtractor`:

| Policy | Behavior |
|---|---|
| `"propagate"` (default) | A series containing any NaN yields an all-NaN row. Behavior is identical with the parameter omitted. |
| `"raise"` | Fail fast with `ValueError` naming the first offending series (batch index, CSR series index, sample index, or sample/channel for multichannel; the pushed value for streaming). No partial output. |
| `"omit"` | **Not supported** — requesting it raises `ValueError`. Dropping samples would silently change window contents and lengths. Clean the series first (`x[~np.isnan(x)]` or an interpolation of your choosing) so the imputation is yours and visible, then call with `"propagate"`. |
| anything else | `ValueError` listing the valid policies. |

Unknown-policy and omit errors are raised before any compute starts. The
`raise` scan runs before the thread pool is entered, so an invalid call fails
immediately.

## NaN as a value (propagate)

| Input condition | Output |
|---|---|
| Series contains any NaN | **All features for that series are NaN.** No imputation, no partial results. |
| Feature undefined for an otherwise-valid series | **That one feature is NaN**; the rest compute normally. |
| Series contains ±infinity | Propagates under normal IEEE-754 arithmetic (`abs_energy` becomes `inf`, `mean` may become `inf` or NaN). Infinities are not rewritten. One exception: an all-`inf` (or all-`-inf`) series counts as constant, so `var`/`std` are exactly `0.0` and `skewness`/`kurtosis` NaN, by the constant rule below. |

Row-wide propagation is the conservative choice: with 500 samples and one NaN,
`mean` is meaningless but `min` would still look plausible, and a
plausible-looking number is worse than an obvious NaN.

Streaming follows the same contract: a NaN anywhere in the window yields an
all-NaN row from either `compute` kind; once the NaN slides out, exact
accumulators resume with no poisoning. A window containing ±inf takes the
exact O(W) fallback (see the [streaming guide](streaming.md)).

## Degenerate inputs

Measured on the batch pipeline (float64, core33); ragged, sliding, and
streaming agree element-wise by test:

| Input | Result |
|---|---|
| Constant series (incl. all-zero) | `var`/`std` exactly `0.0`; `skewness`, `kurtosis`, all autocorrelations, `trend_r2`, and all three spectral features NaN; `cid_ce` exactly `0.0`; `trend_slope` exactly `0.0`. |
| Length-1 series | Change features (`mean_abs_change`, `mean_change`, `cid_ce`), `mean_second_derivative_central`, `trend_slope`, `trend_r2`, `permutation_entropy`, autocorrelations, and spectral features NaN; the rest compute. |
| Length-2 series | `mean_second_derivative_central`, `autocorr_lag_2/5/10`, `permutation_entropy` NaN; skew/kurt are defined. |
| All-zero series | Same as constant: 10 NaN features, the rest finite (`mean` 0, `abs_energy` 0, crossings 0). |
| Empty batch / zero-length series | `ValueError` (structural, before compute). |
| `window`/`stride` < 1, `window` > length | `ValueError`. |

## Input layout and copies

All inputs are borrowed zero-copy (`as_slice` views; see `src/ffi.rs`
"Strict C-contiguity rule"). Consequences, tested in
`tests/test_input_surface.py`:

- C-contiguous float64/float32 arrays work everywhere, including read-only
  and memory-mapped buffers. Contiguous input is never copied: the
  non-contiguous cases below are *rejected* by default, which proves no
  silent copy (a copying implementation would accept them).
- Fortran-ordered, strided, and negative-stride inputs raise `ValueError`
  by default (`contiguous="error"`). So do Fortran-ordered `out=` buffers
  (row-major writes into column-major memory would silently transpose).
- `contiguous="copy"` performs one explicit C-order copy first (in logical
  element order, so results are bit-identical to contiguous input) and emits
  a `UserWarning` naming the copy; pass `np.ascontiguousarray` input to avoid
  it. Unknown values raise `ValueError`.
- Wrong dtype (anything but float64/float32) raises `TypeError` with a cast
  hint; kymora never upcasts silently. Wrong shapes raise `TypeError`;
  zero-size inputs and bad window geometry raise `ValueError`.

## Precision

Accumulation is always float64: float32 input is read natively (zero-copy, no
`astype` round-trip) and widened exactly on read; float64 input is
bit-identical to previous releases. `out_dtype="float32"` casts on write.
The `precision` argument is validated but currently informational — accepted
values are `"float64"`/`"f64"`/`"float32"`/`"f32"` (anything else raises
`ValueError`); the input dtype governs the read path either way.

Float32 coverage: the f32 kernels implement the core33 set, so float32 input
supports the default profile, `minimal`, and any core33 feature subset
(gathered from a full core33 row, still zero-copy). `extended`/`full`
profiles, non-core33 features, and non-raw views raise `ValueError` telling
the caller to pass float64 — this path previously panicked across the FFI
boundary. Results match the float64 pipeline on the same values within
f32-arithmetic tolerance (rtol 1e-4; measured max 8.8e-6).

## Stability

These rules are part of the public contract. Changing which conditions
produce a row of NaN versus a single NaN is a breaking change requiring a
major version bump, the same as reordering `feature_names()`.
