# NaN policy

Two categories, deliberately kept apart: **NaN is a value; structural problems
raise.** Conflating them is the most common way a feature pipeline hides a bug,
so this library keeps the code paths separate and tests both.

## NaN as a value

| Input condition | Output |
|---|---|
| Series contains any NaN | **All 33 features for that series are NaN.** No imputation, no partial results. |
| Feature undefined for an otherwise-valid series | **That one feature is NaN**; the rest compute normally. |
| Series contains an infinity | Features propagate it under normal IEEE-754 arithmetic (`abs_energy` becomes `inf`, `mean` may become `inf` or NaN). Infinities are not rewritten. |

Row-wide propagation is the conservative choice: with 500 samples and one NaN,
`mean` is meaningless but `min` would still look plausible, and a plausible-looking
number is worse than an obvious NaN. If you want NaN-tolerant behaviour, clean the
series before calling — `x[~np.isnan(x)]` or an interpolation of your choosing —
so the imputation is yours and visible.

The per-feature undefined cases are listed in the
[feature reference](features.md); the recurring ones are:

- **Constant series** — autocorrelation at every lag, `trend_r2`, all three
  spectral features, and skewness/kurtosis. There is no variation to describe.
- **Short series** — change features need `n >= 2`,
  `mean_second_derivative_central` needs `n >= 3`, permutation entropy needs
  `n >= 3`, autocorrelation at lag `k` needs `n > k`.

Two features are defined to a specific finite value rather than NaN on a
constant series, because the answer is unambiguous: `cid_ce` is exactly `0.0`
(no complexity) and `trend_slope` is exactly `0.0` (a flat line has zero slope).

## Structural problems raise

Checked at the PyO3 boundary before any compute starts, so an invalid call fails
immediately rather than after burning a thread pool:

| Condition | Exception |
|---|---|
| No series at all (empty array or empty list) | `ValueError` |
| A zero-length series | `ValueError` |
| Non-contiguous array (e.g. `X[:, ::2]`) | `ValueError` |
| `window < 1` or `stride < 1` | `ValueError` |
| `window` longer than the series | `ValueError` |
| Wrong dtype (not float64) or wrong shape | `TypeError` |

```python
>>> tsxtractor.extract_features(np.zeros((0, 10)))
ValueError: input contains no series; expected at least one series of length >= 1
>>> tsxtractor.sliding_features(np.zeros(10), window=20)
ValueError: window (20) is larger than the series length (10)
```

## No panics

A Rust `panic!` crossing the FFI boundary would surface as an opaque abort
rather than a catchable Python exception, so the boundary has no `unwrap`,
`expect`, or panicking index on a user-reachable path, and every fallible step
returns `Result`. `tests/test_properties.py` uses `hypothesis` to throw
adversarial series at the API — all-NaN, all-zero, single element, values near
`f64::MAX`, mixed signs, extreme window geometry — and asserts that each call
either returns a correctly shaped array or raises `ValueError`/`TypeError`,
never anything else.

## Stability

These rules are part of the public contract. Changing which conditions produce a
row of NaN versus a single NaN is a breaking change requiring a major version
bump, the same as reordering `feature_names()`.
