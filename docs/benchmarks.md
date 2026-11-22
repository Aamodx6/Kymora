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
`benchmarks/results/HEADLINE_SAME_SESSION_REPORT.md` (`headline_same_session_ratios.json`) for 3-session interleaved headline protocol with inter-block cooldowns;
`EQUAL_FEATURE_REPORT.md` + `2026-11-22_equal_feature/` for matched,
2026-11-22; exploratory single-machine numbers):

| library | features | total time | series/s | µs/series-feature | Raw Speedup | Per-Feature Speedup |
|---|---:|---:|---:|---:|---:|---:|
| **kymora (`core33`)** | **33** | **1.94 ms** | **514,245** | **0.0589** | **1.0× (ref)** | **1.0× (ref)** |
| `catch22` (pycatch22) | 22 | 185.50 ms | 5,391 | 8.43 | **95.4×** | **143.1×** |
| `TSFEL` (all domains) | 156 | 2,509.53 ms | 398 | 16.09 | **1,291×** | **273.0×** |
| `tsfresh` (EfficientFCParameters) | 777 | 23,540.62 ms | 42 | 30.30 | **12,106×** | **514.1×** |

Raw ratios (95.4×/1,291×/12,106×) compare 33 against up to 777 features — read
the per-feature column (143.1×/273.0×/514.1×) next to them, and the matched table
below for the like-for-like view. Per-session ratios across 3 same-session interleaved rounds: catch22 [91.8×, 100.5×, 87.9×], TSFEL [2,036.3×, 1,325.6×, 1,256.3×], tsfresh [11,952.0×, 12,014.0×, 12,630.8×]; 95% bootstrap CI on Kymora throughput is [495,050, 529,605] series/s ([1.89, 2.02] ms; isolated baseline 358,654 series/s / 2.79 ms).

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

| Library | Features | Datasets | Mean RF Acc (%) | Mean Ridge Acc (%) | Mean Rank (RF) | Mean Rank (Ridge) | Median Extract Time |
| :--- | :---: | :---: | :---: | :---: | :---: | :---: | :---: |
| `tsfresh` | 777 | 42 | **84.79%** | **82.39%** | **2.19** | **2.43** | 20,943.62 ms |
| **Kymora (`full`)** | 543 | 42 | **82.79%** | **80.66%** | **2.83** | **3.17** | **2.17 ms** |
| **Kymora (`extended`)** | 143 | 42 | **83.12%** | **80.39%** | **2.98** | **3.19** | **1.74 ms** |
| `TSFEL` | 156 | 42 | 81.00% | 79.71% | 3.36 | 3.24 | 942.67 ms |
| **Kymora (`core33`)** | **33** | **42** | **79.96%** | **77.42%** | **4.12** | **3.83** | **1.26 ms** |
| `catch22` | 22 | 42 | 79.83% | 75.75% | 4.14 | 4.29 | 159.40 ms |

On linear classifiers (Ridge with fold-isolated `StandardScaler`), Kymora achieves **77.42% mean accuracy**, outperforming `catch22` (**75.75%**) with an average rank of **3.83 vs 4.29** (W/T/L 23/5/14, Holm-adjusted $p = 0.2016$), while extracting 117.2× to 17,217.0× faster than existing libraries across 42 matched datasets (Random Forest accuracy: **79.96%**, rank 4.12 vs catch22 4.14, Holm-adjusted $p = 0.5554$, Critical Difference $CD = 1.05$). Kymora's `extended` (143 feats) and `full` (543 feats) profiles achieve 83.12% and 82.79% RF accuracy, closing the predictive gap to tsfresh. Full report: `benchmarks/results/DOWNSTREAM_UCR_REPORT.md`.

## Where kymora is slower

No honest benchmark omits the losses (full analysis in
`benchmarks/results/L1_ROOT_CAUSE.md`, `benchmarks/results/SMALL_BATCH_REPORT.md`, and `docs/internal/single_call_overhead.md`):

- **Tiny single-shot calls:** Against a hand-written Numba baseline on the same 33 features, Kymora loses at 1 × 10 (p50 5.90 µs vs Numba 3.00 µs) and 1 × 100 with standard `extract_features` (p50 7.50 µs vs Numba 14.40 µs steady-state; first-call 35.2 µs), where Numba JIT compiles inline loops. With dedicated `kymora.extract_one(x)`, single-call latency drops to **3.90 µs** (p99 6.40 µs; target <8 µs achieved by bypassing GIL release and caching thread-local scratchpads). We keep the Numba 1×10 loss in the ledger honestly.
- **Small-batch threshold:** Inline sequential caller execution below 8,000 points (`SERIAL_WORK_SIZE_THRESHOLD = 8000`, configurable via `KYMORA_SERIAL_THRESHOLD`) matches 1T and 16T execution and avoids Rayon thread wake jitter.
- **Batch inflection:** At 10 × 500, Kymora wins 2.4× (103.5 µs vs 247.3 µs); at 100 × 100, Kymora wins 2.4× (156.8 µs vs 375.3 µs); at 100 × 500, Kymora wins 3.0× (396.5 µs vs 1,195.2 µs); at ≥1,000 series, Kymora beats the Numba baseline 6.0×–11.8× on identical features (equal-feature table above).

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
