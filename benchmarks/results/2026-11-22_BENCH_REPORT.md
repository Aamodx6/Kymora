# Benchmark re-baseline — 2026-11-22

Re-measured kymora against catch22, TSFEL, tsfresh, and hand-written numba/numpy
baselines on one machine, then propagated every published figure to these
artifacts. Exploratory single-machine numbers, not fleet evidence.

## Environment

| Item | Value |
|---|---|
| CPU / OS | i7-13620H, 10 cores (6P+4E) / 16 threads, Windows 11 (10.0.26300) |
| Power | AC online, Windows scheme `Silent` (`is_high_performance: false`) — recorded in each `env.json` |
| Python / NumPy | 3.14.6 (Anaconda) / 2.4.6 |
| kymora | **0.8.0** — the installed PyPI release wheel |
| Competitors | pycatch22 1.0.2, TSFEL 0.3.0, tsfresh 0.21.2, numba 0.65.1 |
| Code state | `9e1c664` (`chore/remove-dead-files`), feature hash `8a1e2794…31af2e` (33 names, MATCH) |

**Build caveat.** `python -m maturin build --release` fails on this host with
`An Application Control policy has blocked this file. (os error 4551)`, so the
timed artifact is the released 0.8.0 wheel rather than a local build of HEAD.
HEAD carries post-0.8.0 fixes (clippy view-pruning cleanup, skew/kurt
degenerate-window NaN guard — the installed wheel already exhibits the guard).
Timing is unaffected by those changes; version labels say 0.8.0 accordingly.

**Conditions caveat.** Ratios are measured interleaved (kymora/competitor
alternating) inside one session, so they are insensitive to the power scheme.
Absolute milliseconds are not: two same-day runs measured core33 at
**1.90 ms** and **2.53 ms** (both committed). Treat ms values as ±25 % across
sessions; treat ratios as the comparable quantity.

## Method

1. **Parity gate first** (`equal_feature.py parity`, 40 series × 500 points,
   seed 42). Each competitor is restricted to the features whose definitions
   provably agree with kymora's; every pair is checked before any timing.
   Result: **all four PASS, 0 mismatches** — worst rel err TSFEL 9.66e-13,
   tsfresh 9.39e-14, numba 2.58e-12, numpy 9.66e-13 (EXACT ≤ 1e-9).
2. **Equal-feature timing** (`equal_feature.py bench --rounds 6`): 4 shapes ×
   4 competitors, 6 interleaved rounds per row, pooled medians, 95 % bootstrap
   CI on the ratio, GC disabled, warmup, in-process timing after subprocess
   isolation. NumPy `einsum`/FFT thread envs unset (env.json).
3. **Profiles / scaling / memory** (`remeasure_readme.py`): 1,000 × 500,
   minimal/core33/extended/full; 1–32 threads; fresh-process peak RSS.
4. **Raw-time comparison** (`reproduce_readme.py`): each library's full default
   catalog, including the reshaping it requires (tsfresh long DataFrame,
   catch22/TSFEL per-series loops), 80 kymora runs and 8/10/7 competitor runs.

Commands:

```bash
python benchmarks/suites/equal_feature.py parity
python benchmarks/suites/equal_feature.py bench --rounds 6
python benchmarks/suites/remeasure_readme.py
python benchmarks/suites/reproduce_readme.py
```

## Equal-feature results (like-for-like)

| Shape | Competitor | Equalfeats | Kymora (ms) | Competitor (ms) | Ratio | 95 % CI |
|---|---|---:|---:|---:|---:|---|
| 100×50,000 | numba | 33 | 32.73 | 300.9 | 9.2× | [8.8, 9.5] |
| 100×50,000 | numpy | 33 | 30.77 | 3,319.9 | 107.9× | [105.5, 109.5] |
| 100×50,000 | TSFEL | 13 | 23.46 | 834.0 | 35.6× | [35.1, 35.9] |
| 100×50,000 | tsfresh | 13 | 32.34 | 8,183.8 | 253.1× | [242.4, 263.0] |
| 1,000×500 | numba | 33 | 2.24 | 13.3 | 6.0× | [5.7, 6.5] |
| 1,000×500 | numpy | 33 | 2.19 | 361.3 | 165.1× | [157.2, 170.5] |
| 1,000×500 | TSFEL | 13 | 1.97 | 2,145.7 | 1,089.1× | [1,007.3, 1,132.2] |
| 1,000×500 | tsfresh | 13 | 2.34 | 6,580.6 | 2,812.4× | [2,584.3, 2,914.1] |
| 1,000×5,000 | numba | 33 | 18.12 | 213.6 | 11.8× | [11.3, 12.0] |
| 1,000×5,000 | numpy | 33 | 17.16 | 3,347.9 | 195.0× | [190.0, 199.8] |
| 1,000×5,000 | TSFEL | 13 | 13.09 | 2,732.7 | 208.8× | [206.2, 211.2] |
| 1,000×5,000 | tsfresh | 13 | 16.86 | 8,198.9 | 486.3× | [466.3, 504.6] |
| 10,000×500 | numba | 33 | 19.29 | 120.6 | 6.3× | [6.0, 6.3] |
| 10,000×500 | numpy | 33 | 17.75 | 3,537.5 | 199.2× | [186.2, 204.1] |
| 10,000×500 | TSFEL | 13 | 15.89 | 21,758.6 | 1,369.0× | [1,311.3, 1,389.4] |
| 10,000×500 | tsfresh | 13 | 20.52 | 9,435.0 | 459.9× | [447.5, 484.8] |

Per-competitor ranges across shapes: numba 6.0×–11.8×, numpy 107.9×–199.2×,
TSFEL 35.6×–1,369.0×, tsfresh 253.1×–2,812.4×. kymora is fastest on all 16 rows.

Row CVs are 0.008–0.062 (kymora) and 0.005–0.062 (competitors). An earlier
4-round run produced one unstable row (numpy 10,000×500: kymora 49.6 ms,
ratio CI [118, 396]); at 6 rounds it is 199.2× [186.2, 204.1], confirming that
was scheduling noise, not a kymora regression.

## Raw time — full default catalogs (1,000 × 500)

| Library | Features | Runtime (ms) | Series/s | µs / series-feature | Raw ratio | Per-feature ratio |
|---|---:|---:|---:|---:|---:|---:|
| **kymora (core33)** | **33** | **1.84** | **542,682** | **0.0558** | 1.0× | 1.0× |
| catch22 (pycatch22) | 22 | 432.6 | 2,312 | 19.66 | 235× | 352× |
| TSFEL (all domains) | 156 | 2,041.5 | 490 | 13.09 | 1,108× | 234× |
| tsfresh (EfficientFC) | 777 | 14,966.8 | 67 | 19.26 | 8,122× | 345× |

Best kymora run 1.57 ms (636,943 series/s). Raw time is not like-for-like
(33 vs 22/156/777 features) — the per-feature and equal-feature columns are.

## Profiles (1,000 × 500, 16 threads)

| Profile | Features | Median | Best | Per-feature | Throughput |
|---|---:|---:|---:|---:|---:|
| minimal | 10 | 0.58 ms | 0.48 ms | 0.0583 µs | 1,716,444 series/s |
| core33 | 33 | 1.90 ms | 1.62 ms | 0.0575 µs | 526,912 series/s |
| extended | 143 | 8.02 ms | 6.86 ms | 0.0561 µs | 124,635 series/s |
| full | 543 | 9.44 ms | 7.88 ms | 0.0174 µs | 105,982 series/s |

## Thread scaling (core33, 1,000 × 500)

| Threads | 1 | 2 | 4 | 8 | 16 | 32 |
|---|---:|---:|---:|---:|---:|---:|
| Median (ms) | 11.22 | 5.83 | 3.40 | 2.22 | 2.30 | 2.09 |
| Speedup | 1.00× | 1.92× | 3.30× | 5.05× | 4.87× | 5.37× |
| Efficiency | 100 % | 96.1 % | 82.6 % | 63.1 % | 30.5 % | 16.8 % |

Scaling is hardware-bound on this hybrid P+E laptop: useful efficiency to ~8
threads, then diminishing (and noisy) returns past the 10 physical cores.
The 32-thread row exceeding 16 threads is within run-to-run noise.

## Memory (fresh-process peak RSS)

| Library | Shape | Extraction peak | Total delta | Output |
|---|---|---:|---:|---:|
| kymora core33 | 100,000 × 500 | +32.8 MiB | +418.0 MiB | 25.2 MiB |
| kymora core33 | 10,000 × 500 | +10.0 MiB | +51.9 MiB | 2.5 MiB |
| kymora extended | 10,000 × 500 | +18.5 MiB | +60.5 MiB | 10.9 MiB |
| kymora full | 1,000 × 500 | +10.8 MiB | +18.3 MiB | 4.1 MiB |
| tsfresh EfficientFC | 1,000 × 500 | +293.2 MiB | +300.9 MiB | 5.9 MiB |
| tsfresh EfficientFC | 10,000 × 500 | +410.3 MiB | +452.2 MiB | 59.3 MiB |

Where kymora loses: numba still wins the smallest batch (1×100) by
1.43×–1.78× (2026-10-05 HEAD rerun, 95 % CIs exclude 1.0) because fixed
per-call overhead dominates at that size. 10×500 is parity/noise.

## Landscape (external sources)

- **catch22** (Lubba et al. 2019): 22 features selected from 4,791 candidates
  over 93 classification datasets; C core, no runtime deps. In the 2021
  empirical comparison (arXiv:2110.10914) catch22 and TSFEL were the fastest
  sets at ~0.1 ms per feature for 1,000-sample series, versus ~2 ms/feature for
  tsfresh and ~280 ms/feature for tsfeatures.
- **TSFEL** (Barandas et al. 2020): 156 features in this config; pure
  Python/NumPy per-series loops. The 2026 manufacturing benchmark (ScienceDirect
  S0957417426033221) found TSFEL the lowest-effort option among multithreaded
  packages but with weaker predictive reliability on complex data; EPIA 2025
  found it the most efficient for algorithm selection.
- **tsfresh** (Christ et al. 2018): 777 features under EfficientFCParameters;
  the 2026 classification comparison (arXiv:2608.01586) still ranks it the
  strongest feature set overall (29.03 % wins, 85.3 % ties) — breadth is the
  product, and it is why the equal-feature table exists.
- **tsflex** (arXiv:2111.12429) reports the same structural cost kymora avoids:
  tsfresh peaked at 3,540 MB in their extraction task versus 3.5 MB for TSFEL,
  driven by the long-format expansion — consistent with the +293/+410 MiB
  tsfresh extraction overhead measured here.
- **Rust/PyO3 alternatives**: ChronoXtract (GitHub, amanasci) is a comparable
  Rust-backed Python extractor; kymora's differentiators are the closed 33-feature
  catalog, parity-gated competitor benchmarks, streaming extractor, and
  NaN contract. kymora 0.8.0 is live on PyPI (dist `kymora`).

## What changed

Published figures updated to the artifacts above in: `README.md`,
`docs/benchmarks.md`, `CLAIMS.md` (new 2026-11-22 section; 0.7.0 rows retained as
superseded), `landing/src/benchmarks.ts`, `landing/src/components/{Benchmarks,
Features,Hero}.tsx`, the five `docs/launch/*.md` drafts, and
`docs/internal/hardening/STATUS.md`. `EQUAL_FEATURE_REPORT.md` was regenerated by
the suite itself. Stale "up to ~40×" small-batch loss claims were corrected to
the measured 1.4×–1.8×.

Not changed: `benchmarks/results/LOSS_LEDGER.md` (the suite appended deviation
notes against the pre-update README; the append was reverted to keep that frozen
evidence intact), `docs/internal/hardening/RELEASE_NOTES.md` (historical 0.8.0
record), and `tests/golden/`.

Follow-ups: PyPI's long description still shows the old 3.18 ms line until the
next release (it is single-sourced from README at build time); the tsfresh
100,000 × 500 memory cell remains PENDING (multi-hour run); a build-host
unblock is needed to benchmark HEAD rather than the 0.8.0 wheel.
