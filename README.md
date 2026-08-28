# tsxtractor

Batch time-series feature extraction for Python, with a Rust core.

33 curated statistical, temporal, and spectral features, computed across a whole
batch of series at once. The Rust core takes zero-copy views of your numpy
buffers, releases the GIL, and parallelises across the *series* dimension with
[rayon](https://github.com/rayon-rs/rayon) — so throughput scales with your
cores when you have many series to process.

```bash
pip install tsxtractor
```

Wheels ship for Linux (x86_64, aarch64), macOS (Intel, Apple Silicon), and
Windows (x86_64), for Python 3.10+. No Rust toolchain needed.

## Quickstart

```python
import numpy as np
import tsxtractor

# batch: one row per series
X = np.random.randn(100_000, 500)
feats = tsxtractor.extract_features(X)        # (100_000, 33) float64
names = tsxtractor.feature_names()            # stable column order

# same thing with labeled columns (needs pandas)
df = tsxtractor.extract_features_df(X)

# ragged series of different lengths
feats = tsxtractor.extract_features([arr1, arr2, arr3])

# rolling windows over one long series
feats = tsxtractor.sliding_features(x, window=256, stride=64)
```

Input must be float64 and C-contiguous — a wrong dtype raises `TypeError`
instead of being silently copied, so you decide where the conversion cost is
paid (`X.astype(np.float64)`).

## Where the speed comes from

Parallelism is across **series**, not across the feature computations within one
series. The practical consequences:

- Extracting from 100 000 series scales close to linearly with core count.
- Extracting from *one* series shows no speedup versus a good numpy
  implementation, and is not meant to. If your workload is one long series, use
  `sliding_features`, which parallelises over the windows.

The GIL is released for the whole compute region, so this parallelism is real
under threaded Python callers, not capped by the interpreter lock.

## Benchmark

```bash
pip install -e ".[bench]"
python benches/bench_libraries.py --n-series 1000 --n-steps 500
```

The benchmark compares batch throughput against `tsfresh`, `catch22`, and
`TSFEL` on the same input, timing each library end to end *including* the input
reshaping it requires (tsfresh needs a long DataFrame; catch22 and TSFEL need a
per-series Python loop). It is run on a GitHub Linux runner by the
[Benchmark workflow](.github/workflows/benchmark.yml) so the published numbers
are reproducible by a stranger rather than measured on one laptop; the latest
committed run is in [`benches/results/`](benches/results/).

These libraries compute different numbers of features, so total wall-clock time
is not a like-for-like comparison — read the per-feature column alongside it.
`catch22` is competitive per feature; the claim here is batch throughput.

## When not to use this

- **You need exhaustive feature coverage.** `tsfresh` computes up to 1 558
  features and `TSFEL` around 390. tsxtractor computes 33, chosen to stay
  low-redundancy. If you want to throw everything at a feature selector, use
  `tsfresh`.
- **You need custom or parameterised features.** The feature set is
  intentionally closed; there is no plugin hook.
- **You are in R, Julia, or MATLAB.** Use `catch22`, which has bindings for all
  three. tsxtractor is Python-only.
- **Your workload is one short series at a time.** The parallelism has nothing
  to work with; numpy is fine.

## Comparison

| Library | Features | Core | Batch-parallel | Notes |
|---|---:|---|---|---|
| **tsxtractor** | 33 | Rust + PyO3 | yes (rayon, across series) | curated, low-redundancy set; numpy-only dependency |
| `tsfresh` | up to 1 558 | Python | no | most exhaustive; slowest by a wide margin at scale |
| `TSFEL` | ~390 | Python | no | fast per feature; high within-set redundancy |
| `catch22` | 22 | C | no | fastest per feature; fixed set; multi-language bindings |
| `tsflex` | n/a | Python | no | windowing framework, not a feature bank — calls others |

## Features (33)

| Group | Features |
|---|---|
| Stats | mean, std, var, min, max, median, quantile_10/25/75/90, skewness, kurtosis, abs_energy, root_mean_square |
| Change | mean_abs_change, mean_change, cid_ce (z-normalized), mean_second_derivative_central |
| Counts | zero_crossings, mean_crossings, number_of_peaks (support 3), longest_strike_above/below_mean |
| Correlation | autocorr at lags 1, 2, 5, 10; linear trend slope and r² |
| Entropy | permutation_entropy (order 3, normalized to [0, 1]) |
| Spectral | dominant_frequency, spectral_centroid, spectral_entropy (positive bins, DC excluded, sample spacing 1) |

Conventions: population moments (`ddof=0`); numpy-default linear interpolation
for quantiles; skewness/kurtosis follow `scipy.stats` with `bias=True`
(kurtosis is Fisher/excess).

`feature_names()` order is a **stability guarantee**: column `i` means the same
feature for every release within a major version. Reordering or renaming is a
major-version change.

## NaN policy

Two separate categories, deliberately not conflated:

- **NaN is a value.** Any NaN anywhere in a series makes all 33 of that series'
  features NaN — no silent imputation. Features that are individually undefined
  for an otherwise-valid series (autocorrelation or spectral features of a
  constant series, change features of a length-1 series) are NaN on their own
  while the rest compute normally.
- **Structural problems raise.** No series at all, a zero-length series, a
  non-contiguous array, `window`/`stride` < 1, or `window` longer than the
  series raise `ValueError`. A wrong dtype or shape raises `TypeError`. No Rust
  panic crosses the boundary; this is enforced by property-based tests.

## Correctness

Every feature is checked against a numpy/scipy reference implementation across
normal, trending, periodic, constant, two-element, single-element, and
heavily-tied series. CI publishes a
[reference-validation report](docs/validation.md) with the max absolute error
per feature, plus `hypothesis` property tests asserting that no input produces a
panic, a wrong output shape, or a NaN-policy violation.

## Development

```bash
python -m venv .venv && . .venv/bin/activate   # .venv\Scripts\activate on Windows
pip install maturin
pip install -e ".[test]"
maturin develop --release
pytest tests/
cargo test --no-default-features    # pure-Rust unit tests
```

See [CONTRIBUTING.md](CONTRIBUTING.md) for how to add a feature and what
requires a version bump.

## License

MIT — see [LICENSE](LICENSE).
