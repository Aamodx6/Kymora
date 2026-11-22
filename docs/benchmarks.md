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
Windows 11, AC online, High Performance power scheme (artifacts:
`benchmarks/results/HEADLINE_THROUGHPUT_REPORT.md` for pooled headline protocol,
`2026-11-22_reproduce_readme/` for raw + competitor rounds, 2026-11-22;
`EQUAL_FEATURE_REPORT.md` + `2026-11-22_equal_feature/` for matched,
2026-11-22; exploratory single-machine numbers):

| library | features | total time | series/s | µs/series-feature |
|---|---:|---:|---:|---:|
| **kymora** | 33 | **1.74 ms** | **575,391** | **0.0527** |
| `catch22` (pycatch22) | 22 | 432.6 ms | 2,312 | 19.66 |
| `TSFEL` (all domains) | 156 | 2,041.5 ms | 490 | 13.09 |
| `tsfresh` (EfficientFCParameters) | 777 | 14,966.8 ms | 67 | 19.26 |

Raw ratios (249×/1,175×/8,612×) compare 33 against up to 777 features — read
the per-feature column (373×/248×/366×) next to them, and the matched table
below for the like-for-like view. (Previous exploratory Silent session: 1.84 ms / 542,682 series/s, best 1.57 ms / 636,943 series/s, ratios 235×/1,108×/8,122×; per-feature 0.0558 µs / 352×/234×/345×; tracked in `CLAIMS.md`.)

### Equal-feature (like-for-like, 1,000 × 500, 16 threads)

| Library | Equal features | Kymora med (ms) | Library med (ms) | Ratio (95% CI) |
| :--- | :---: | :---: | :---: | :--- |
| numba baseline | 33 | 2.24 | 13.34 | **6.0× slower** [5.7, 6.5] |
| numpy baseline | 33 | 2.19 | 361.33 | **165.1× slower** [157.2, 170.5] |
| TSFEL | 13 | 1.97 | 2,145.73 | **1,089.1× slower** [1,007.3, 1,132.2] |
| tsfresh | 13 | 2.34 | 6,580.57 | **2,812.4× slower** [2,584.3, 2,914.1] |

The batch gap has two independent causes. One is parallelism plus a single
FFI crossing instead of a thousand Python calls. The other is that all 33
features here are O(n) or O(n log n), while `catch22` includes costlier
estimators. If you need those specific estimators, that difference is not
overhead you can optimise away.

### Predictive utility on real-world datasets (UCR Archive)

| Library | Features | Mean RF Acc (%) | Mean Ridge Acc (%) | Mean Rank (RF) | Mean Rank (Ridge) | Median Extract Time |
| :--- | :---: | :---: | :---: | :---: | :---: | :---: |
| `tsfresh` | 777 | **95.97%** | **95.27%** | 1.60 | 1.60 | 7,592.33 ms |
| `TSFEL` | 156 | **95.55%** | **94.75%** | 1.75 | 1.50 | 3,037.06 ms |
| **Kymora (`core33`)** | **33** | **92.34%** | **93.58%** | 2.88 | **2.25** | **0.81 ms** |
| `catch22` | 22 | 93.73% | 90.47% | 2.38 | 3.25 | 60.68 ms |

On linear classifiers (Ridge with fold-isolated `StandardScaler`), Kymora achieves **93.58% mean accuracy**, outperforming `catch22` (**90.47%**, Wilcoxon $p = 0.0156$) with an average rank of **2.25 vs 3.25**, while extracting 80× to 7,788× faster than existing libraries. Full report: `benchmarks/results/DOWNSTREAM_UCR_REPORT.md`.

## Where kymora is slower

No honest benchmark omits the losses (full analysis in
`benchmarks/results/L1_ROOT_CAUSE.md`):

- Tiny calls (a handful of series): fixed per-call overhead (~70 µs
  dispatch floor) dominates; numba/numpy win that case (1.4×–1.8× measured).
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
