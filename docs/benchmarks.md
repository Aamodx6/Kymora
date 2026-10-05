# Benchmarks

## What is actually being measured

Wall-clock time to turn a batch of `n_series` equal-length series into one
feature row per series — the shape of work a real feature pipeline does.

Three views are published side by side for every comparison, because each
answers a different question (arch §11.6):

1. **Raw runtime** — the as-is configs (33 vs 777 features). Answers "how
   long does my batch take with each library's natural setup".
2. **Per series-feature** — total divided by (series × features). Answers
   "how efficient is each computed value".
3. **Matched-feature runtime** — every library restricted to the feature
   subset whose definitions provably agree (parity-gated before timing).
   Answers "who computes the same work faster". This is the only
   like-for-like table.

Each library is timed end to end, **including the input reshaping it
requires**: `tsfresh` needs a long-format DataFrame, `catch22` and `TSFEL`
need a per-series Python loop. That reshaping is a cost users pay, so
excluding it would flatter the Python libraries in a way no production
pipeline ever sees.

## Methodology

- Fresh subprocess per measurement, warmup, GC disabled during timing.
- Interleaved rounds across libraries (no library gets a warm- or
  cold-machine advantage); pooled medians with 95% bootstrap CIs.
- ≥15 runs or ≥2 s budget per cell; one automatic re-run when CV > 5%.
- Best-of and median reported **separately** — headlines use medians.
- Every result row carries hardware, thread count, shape, dtype, library
  versions, and commit (`env.json` next to each artifact).
- Numeric parity is verified *before* timing on matched sets (max rel err
  ≤ 1e-9); failures are recorded as `mismatch` rows and never timed.

## A measured run

1,000 series × 500 steps, i7-13620H laptop, 10 cores (6P+4E) / 16 threads,
Windows 11, Performance plan, AC online (artifacts:
`benchmarks/results/F1_REPORT.md` for raw + competitor rounds, 2026-10-04;
`EQUAL_FEATURE_REPORT.md` + `2026-10-05_equal_feature/` for matched,
2026-10-05; exploratory single-machine numbers):

| library | features | total time | series/s | µs/series-feature |
|---|---:|---:|---:|---:|
| **kymora** | 33 | **3.18 ms** | 314,450 | 0.0964 |
| `catch22` (pycatch22) | 22 | 833.1 ms | 1,200 | 37.87 |
| `TSFEL` (all domains) | 156 | 2,541.6 ms | 393 | 16.29 |
| `tsfresh` (EfficientFCParameters) | 777 | 20,891.2 ms | 48 | 26.89 |

Raw ratios (262×/799×/6,570×) compare 33 against up to 777 features — read
the per-feature column (393×/169×/279×) next to them, and the matched table
below for the like-for-like view.

### Equal-feature (like-for-like, 1,000 × 500, 16 threads)

| Library | Equal features | Kymora med (ms) | Library med (ms) | Ratio (95% CI) |
| :--- | :---: | :---: | :---: | :--- |
| numba baseline | 33 | 4.72 | 16.05 | **3.4× slower** [3.1, 3.9] |
| numpy baseline | 33 | 4.68 | 285.50 | **61.0× slower** [60.0, 62.0] |
| TSFEL | 13 | 3.92 | 2,213.69 | **564.6× slower** [509.7, 781.4] |
| tsfresh | 13 | 4.94 | 8,359.45 | **1,693.8× slower** [1,645.5, 1,900.1] |

The batch gap has two independent causes. One is parallelism plus a single
FFI crossing instead of a thousand Python calls. The other is that all 33
features here are O(n) or O(n log n), while `catch22` includes costlier
estimators — on one 500-point series, `catch22_all` takes 945 us against
9.4 us for `extract_features` (best of 200 runs each) †. If you need those
specific estimators, that difference is not overhead you can optimise away.

† predates the 2026-10-04 re-baseline; single-series figures pending
re-measurement (tracked in `CLAIMS.md`).

## Where kymora is slower

No honest benchmark omits the losses (full analysis in
`benchmarks/results/L1_ROOT_CAUSE.md`):

- Tiny calls (a handful of series): fixed per-call overhead (~70 µs
  dispatch floor) dominates; numba/numpy win up to ~40× at 1×100.
- The numba baseline wins small-batch throughput cases (10×500 and below).
- Oversubscribing threads past the physical core count adds nothing on
  hybrid laptops (see [Performance](performance.md)).

## Reproducing every figure

```bash
./reproduce.sh            # full pipeline: venvs, smoke, agreement, report
```

which runs, in order: competitor venv setup (`benchmarks/setup_venvs.py`),
the B0 smoke matrix, the B1 agreement/parity suite, and the report build.
Every figure in the README, docs, landing page, and paper traces to an
artifact in `benchmarks/results/` via [CLAIMS.md](https://github.com/Aamodx6/Kymora/blob/main/CLAIMS.md);
`tools/check_claims.py` fails the build if a figure appears anywhere
without a CLAIMS.md entry.

CI runs the suite reduced on every schedule: `.github/workflows/bench.yml`
(manual dispatch + weekly, ubuntu + macOS Apple Silicon) runs the parity
gate, a reduced equal-feature matrix, and the profile/scaling re-measure,
uploading artifacts without copying numbers into claims. Do not quote CI
numbers until real artifacts exist.

## Reading the results honestly

- **Total time across libraries is not like-for-like.** 33 features against
  777 is not the same amount of work. Read the per-feature column next to
  the total, and the matched table above for equal work.
- **Core count dominates.** The advantage is parallelism across series, so a
  4-core runner and a 64-core machine tell very different stories. The recorded
  core count is part of the result.
- **A single series shows no *parallel* advantage.** Expected, not a bug: with
  one series there is nothing to spread across cores, and what is left is the
  cost of the feature set itself.
- **Debug builds are roughly an order of magnitude slower.** Always
  `maturin develop --release` (or `--release` wheels) before timing anything.
- **One laptop is not fleet evidence.** All numbers here are exploratory
  until the Linux/macOS CI matrix produces committed artifacts.
