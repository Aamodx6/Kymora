# CLAIMS.md

Every public performance claim → artifact path → code state → conditions
(docs/internal/arch.md §14.1). No evidence ⇒ remove or soften. Hardware + thread count
beside every headline number; laptop wording is "10 cores (6P+4E) /
16 threads".

## Measured — exploratory (single laptop, not fleet evidence; artifact: `benchmarks/results/F1_REPORT.md` + `F1_*` / `B_*` jsonl+env)

Measured 2026-10-04: step-2 interleave (P1→H1→P2→H2) plus 3b bisect
rounds (`B_040_R1/R2`, `B_PRE_R1c/R2`, `B_HEAD_R1/R2`; probe sets PA2/PB),
one machine (i7-13620H laptop, 10 cores / 16 threads, Windows 11,
Performance plan, AC online, Python 3.14.6, NumPy 2.5.2). Code states:
pre-refactor tag `4c268ca`, HEAD `9c1b3dd` (step-2) → `88298f5`/`de1982f`
(code-identical for numerics), PyPI `kymora` 0.3.2 / 0.4.0 in
isolated venvs. Suite: `benchmarks/suites/reproduce_readme.py` @ HEAD
for all rounds, 1,000 series × 500 steps, f64 C-contiguous gaussian,
16 threads, seed 42. Every run records `n_features` (observed: 33 / 22
/ 156 / 777 — singleton sets, no variation).

| Claim (README) | Artifact value | Conditions |
|---|---|---|
| `core33` median 3.18 ms / 314,450 series/s (1k×500) | pooled HEAD median, 4 rounds (n=400), 95% CI [3.15, 3.22] ms | as above |
| `core33` best 2.29 ms / 436,719 series/s | pooled HEAD best (n=400) | as above |
| 0.0964 µs per series-feature | 3.1802 ms ÷ (1000 × 33) | as above |
| 262× vs catch22 raw (393× per-feature) | 833.08 ms pooled median, 10 rounds (n=53), CI [798.29, 850.81] ÷ 3.1802 ms; per-feature 37.87 µs (raw 37.8671 ÷ 0.0964 µs); series/s: catch22 1,200 | same machine/env; pycatch22, versions in round env.json |
| 799× vs TSFEL raw (169× per-feature) | 2541.61 ms pooled median, 10 rounds (n=83), CI [2463.14, 2672.21] ÷ 3.1802 ms; per-feature 16.29 µs (raw 16.2924 ÷ 0.0964 µs); series/s: TSFEL 393 | same |
| 6,570× vs tsfresh raw (279× per-feature) | 20891.23 ms pooled median, 10 rounds (n=64), CI [20062.15, 21530.14] ÷ 3.1802 ms; per-feature 26.89 µs (raw 26.8870 ÷ 0.0964 µs); series/s: tsfresh 48 | tsfresh 0.21.2; same |
| refactor is perf-neutral | suite CIs overlap pre/HEAD in step 2; 3b probe CIs overlap 0.4.0/pre/HEAD | interleaved + rotated |
| ~15% step 0.3.2→0.4.0, then flat | probe medians 2.00 [1.97,2.02] vs 2.41 / 2.44 / 2.47 (CIs overlap for the latter three), identical 33-name catalog | direct-probe methodology; dispatch-overhead hypothesis unprofiled |

Superseded by the above (kept here so stale copies are recognizable):
800,256 series/s headline, 1.80 ms / 555,016 table row, 820× / 580× /
5,443× / 14,000× / 55,779× ratios, 1,045.8 / 9,806.6 / 100,500.0 ms
competitor rows — all predate the 2026-10-04 re-baseline (different
hardware/software). Step-2 interim values (307,366 s/s; 261×/829×/
7,038× from 4 rounds) superseded by the 10-round pools above.

## Measured — 2026-11-22 re-baseline & HEAD validation (kymora 0.8.1 / HEAD git SHA f28a831, i7-13620H laptop)

Measured 2026-11-22 on Windows 11, AC online, i7-13620H (10 cores (6P+4E) / 16 threads),
Python 3.14.6, NumPy 2.4.6, kymora 0.8.1 (HEAD commit `f28a831caba2874e8564e1d394ce269e60a76a51` / `7a87f92cd691cc7e90f9c88a2fee435d3ce98752`,
wheel SHA256 `d1fab8d692e46be90dd62b57e581305f4abe32824671c7cb97eaf25fa2adffee`,
binary SHA256 `368126cc04b8ddf543d82bfab6b811fd0b1aad1cbef473968de8ab2d16fe6e44`).
Audited with `tools/check_env.py`.

Headline throughput follows the strict multi-session protocol: 3 interleaved sessions × 4 rounds × 30 runs
(360 total measurements) under the Windows `High performance` scheme (`powercfg /setactive 3b8e22c0-5e7c-426d-b887-de93205ee46a`,
`is_high_performance: true` recorded in `env.json`).

Suites: `benchmarks/suites/run_headline_protocol.py`, `benchmarks/suites/bench_small_batch.py`,
`benchmarks/suites/streaming.py`, `benchmarks/suites/equal_feature.py` (parity gate + 6 interleaved rounds),
`benchmarks/suites/remeasure_readme.py`, `benchmarks/suites/reproduce_readme.py`.
Artifacts: `benchmarks/results/HEADLINE_THROUGHPUT_REPORT.md` (`headline_results.json`),
`benchmarks/results/SMALL_BATCH_REPORT.md` (`small_batch_results.json`),
`benchmarks/results/2026-11-22_streaming/STREAMING_PUSH_REPORT.md` (`streaming.jsonl`),
`benchmarks/results/2026-11-22_equal_feature/` (`parity.json`),
`benchmarks/results/2026-11-22_remeasure/`, `benchmarks/results/2026-11-22_reproduce_readme/`,
and `docs/internal/slowdown_0.4.0.md`.

| Claim (README / docs / landing) | Artifact value | Conditions |
|---|---|---|
| Headline raw throughput: pooled median 2.33 ms / 428,633 series/s (95% bootstrap CI [367,067, 475,896] series/s, [2.10, 2.72] ms; session range 242,825 – 500,726 series/s; per-feature 0.0707 µs). Same-session interleaved raw ratios: 84.4× catch22 (126.5× per-feature), 1,177× TSFEL (248.9× per-feature), 10,502× tsfresh (446.0× per-feature) | `HEADLINE_SAME_SESSION_REPORT.md` (`headline_same_session_ratios.json`): 3 interleaved sessions (1,000×500, 16T), catch22 196.82 ms / 5,081 s/s / 8.95 µs, TSFEL 2,745.41 ms / 364 s/s / 17.60 µs, tsfresh 24,500.85 ms / 41 s/s / 31.53 µs. Per-session ratios: c22 [54.0×, 99.6×, 91.8×], TSFEL [995.5×, 1,316.0×, 1,394.0×], tsfresh [5,633.4×, 12,268.2×, 11,604.5×] | 1,000×500, full default catalogs (33 / 22 / 156 / 777 features), 16 threads, High Performance plan, AC online, gaussian seed 42, f64 C-order |
| Equal-feature: kymora fastest on all 16 rows, 6.0×–2,812.4× overall (numba 6.0×–11.8×, numpy 107.9×–199.2×, TSFEL 35.6×–1,369.0×, tsfresh 253.1×–2,812.4×) | `equal_feature.jsonl`, ratio + 95% CI per row (4 shapes × 4 competitors) | 1,000×500 headline: kymora med 2.24 / 2.19 / 1.97 / 2.34 ms vs numba 13.34 / numpy 361.33 / TSFEL 2,145.73 / tsfresh 6,580.57 ms → 6.0× [5.7,6.5] / 165.1× [157.2,170.5] / 1,089.1× [1,007.3,1,132.2] / 2,812.4× [2,584.3,2,914.1] |
| Small-batch fast path (HEAD): sequential inline caller execution (<8,000 points, `SERIAL_WORK_SIZE_THRESHOLD=8000`) eliminates thread pool wake jitter. 1×10 p50 22.3 µs (p99 35.8 µs, max 67.2 µs; 1T: 22.3 µs, 16T: 22.3 µs, mode: sequential) vs numba serial 1.3 µs; 1×100 p50 23.4 µs (p99 37.9 µs, max 81.3 µs; 1T: 23.4 µs, 16T: 23.4 µs, mode: sequential) vs numba serial 11.8 µs (1.98× numba win); 10×500 p50 117.8 µs (1T: 117.8 µs, 16T: 127.1 µs, mode: sequential) vs numba parallel 742.0 µs (6.3× win, ratio 0.16×); 100×100 p50 143.2 µs (1T: 388.4 µs, 16T: 143.2 µs, mode: parallel, 2.71× speedup) vs numba parallel 1518.0 µs (10.6× win, ratio 0.09×); 100×500 p50 358.1 µs (1T: 1069.2 µs, 16T: 358.1 µs, mode: parallel, 2.99× speedup) vs numba parallel 7599.0 µs (21.2× win, ratio 0.05×) | `SMALL_BATCH_REPORT.md` (`small_batch_results.json`) | HEAD build, High Performance, 1T and 16T, bit-identical to parallel dispatch verified |
| Streaming (HEAD re-validation): push p50 0.20 µs flat across W (p99 0.20–0.30 µs, p99.9 0.30–0.50 µs); periodic drift re-anchoring timed separately: p50 3.6 µs (W=64), 4.1 µs (W=256), 16.7 µs (W=4096), 182.4 µs (W=65536; p99.9 315.7–330.2 µs; amortized O(1), worst-case O(W)). compute(fast) p50 0.30 µs flat across all W (p99 0.30–0.40 µs, max 0.8–3.9 µs); compute(all) p50 1.80 µs (W=64) to 1326.60 µs (W=65536) linear in W. End-to-end 86.8×–8566.4× vs naive recompute | `2026-11-22_streaming/STREAMING_PUSH_REPORT.md` (`streaming.jsonl`) | Single thread, W ∈ {64, 256, 4096, 65536}, parity-gated before timing; math.fsum and np.longdouble reference bounds verified |
| Profiles: minimal 0.58 ms / core33 1.90 / extended 8.02 / full 9.44 (best 0.48 / 1.62 / 6.86 / 7.88); per-feature 0.0583 / 0.0575 / 0.0561 / 0.0174 µs; throughput 1,716,444 series/s (minimal), 526,912 series/s (core33), 124,635 series/s (extended), 105,982 series/s (full) | `remeasure_summary.json` profiles[] | 1,000×500, 16 threads |
| Scaling: 1T 11.22 / 2T 5.83 / 4T 3.40 / 8T 2.22 / 16T 2.30 / 32T 2.09 ms; speedups 1.92× / 3.30× / 5.05× / 4.87× / 5.37×; η 96.1 / 82.6 / 63.1 / 30.5 / 16.8% | `remeasure_summary.json` scaling[] | core33, 1,000×500 |
| Memory: kymora worker scratch is O(T × L) and does not scale with N (2.26–3.22 MiB at N ≤ 10k; 14.28 MiB RSS high-water mark across 16 Rayon worker threads at N=100k; zero defensive copies of input). 100k×500 core33 peak RSS 406.77 MiB (input 381.47, output 25.18, scratch delta 14.28 MiB). tsfresh extraction peak +293.2 MiB @1k×500, +410.3 MiB @10k×500 (totals 300.9 / 452.2 MiB) | `MEMORY_SWEEP_REPORT.md` (`memory_sweep_results.json`) | fresh-process peak RSS delta; tsfresh EfficientFCParameters, n_jobs=16 |
| Profiling slowdown 0.3.2 → 0.4.0: probe step is +20.5% (~20–24%, 2.00 ms → 2.41 ms on 1k×500 probe). Shares are unprofiled architectural hypotheses: FeaturePlan bitflag dispatch (~6%), FFI safety and NaN handling (~4%), and scratch arena lifecycle (~5%) | `docs/internal/slowdown_0.4.0.md` | 1k×500 probe profiling, flamegraph analysis |
| Where-slower (historical 2026-10-05): numba wins 1×100 by 1.43×–1.78× (95% CIs exclude 1.0); 10×500 rows parity/noise | `2026-10-05_l1_rerun/l1_root_cause.json` | 16 threads |

## Superseded — 2026-10-05 hardening re-baseline (0.7.0; replaced by the rows above)

Suites: `benchmarks/suites/equal_feature.py`, `benchmarks/suites/remeasure_readme.py`.
Artifacts: `benchmarks/results/2026-10-05_equal_feature/` + `EQUAL_FEATURE_REPORT.md`,
`benchmarks/results/2026-10-05_remeasure/`. Parity gate (EXACT ≤ 1e-9 per
feature pair) re-verified before any equal-feature timing. Kept for
traceability; the README/docs/landing now quote the 2026-11-22 rows.

| Claim (README) | Artifact value | Conditions |
|---|---|---|
| Equal-feature: kymora fastest on all 16 rows, ratios 3.4×–11.1× vs numba, 61.0×–122.2× vs numpy, 19.1×–1,150.6× vs TSFEL, 249.9×–1,693.8× vs tsfresh | `equal_feature.jsonl`, ratio + 95% CI per row (4 shapes × 4 competitors) | 1,000×500 headline: kymora med 4.72 / 4.68 / 3.92 / 4.94 ms vs numba 16.05 / numpy 285.50 / TSFEL 2,213.69 / tsfresh 8,359.45 ms → 3.4× [3.1,3.9] / 61.0× [60.0,62.0] / 564.6× [509.7,781.4] / 1,693.8× [1,645.5,1,900.1] |
| Profiles: minimal 1.20 ms / core33 2.88 / extended 10.10 / full 11.10 (best 0.93 / 2.44 / 8.96 / 9.84); per-feature 0.120 / 0.0873 / 0.0706 / 0.0204 µs; throughput 833,333 series/s (minimal), 346,963 series/s (core33), 99,028 series/s (extended), 90,052 series/s (full) | `remeasure_summary.json` profiles[] | 1,000×500, 16 threads, gaussian, seed 42 |
| Scaling: 1T 12.47 / 2T 7.01 / 4T 4.11 / 8T 3.03 / 16T 2.93 / 32T 3.51 ms; speedups 1.78× / 3.03× / 4.12× / 4.25× / 3.56×; η 89.0 / 75.7 / 51.5 / 26.6 / 11.1% | `remeasure_summary.json` scaling[] | core33, 1,000×500 |
| Memory: kymora 100k×500 core33 peak +417.7 MiB (input 385.4, extraction +32.3, output 25.2) | `remeasure_summary.json` memory[] | fresh-process peak RSS delta |
| tsfresh memory: extraction +281.9 MiB @1k×500, +407.5 MiB @10,000 × 500 (totals +289.8 / +449.5) | same | EfficientFCParameters, n_jobs=16 |
| Where-slower (HEAD rerun 2026-10-05): numba losses only at 1×100 — gaussian 1.78× [1.76,1.80], heavy_tailed 1.75× [1.74,1.76], random_walk 1.43× [1.42,1.45] (call-overhead+quantile-stage); 10×500 rows + 1×100 sinusoid EXPLORATORY, NOISY HOST (0.57×–1.08×, CI95 rel-widths 13–78%, CIs cross 1.0 — no claim; rerun did not record env/CPU load or per-row CV); 1×100 medians km ~0.029 ms vs numba 0.016–0.020 ms (v0.3.0 floor 0.6–0.7 ms and 17.9×–40.2×/3.1×–5.7× superseded); 100×100 16T +27% vs 1T (~12 µs/series compute); len-10 single-series p50 345.8 µs (win) vs numpy 1,317.6 µs, p99 15.4 ms / max 29.1 ms (loss); 100×500 parity 0.94×–0.99× (last three groups: pre pool-cache, 0.8.0 prep — B3_REPORT §3.1 / v0.3.0 L1 era, not re-measured on HEAD) | `2026-10-05_l1_rerun/l1_root_cause.json` (loss table + stage timings + classifications; replaces v0.3.0 `L1_ROOT_CAUSE.md`/`l1_root_cause.json` numbers), `B3_REPORT.md` §3.1 | 16 threads unless noted; CIs exclude 1.0 for robust losses |

## Measured — 2026-10-05 streaming per-push cost (same laptop; artifacts committed)

Suite: `benchmarks/suites/streaming.py` (B3), single thread, capacities
64 / 256 / 4096 / 65536, parity-gated before timing (gate max rel err
7.7e-16 / 6.5e-16 / 3.8e-14 / 3.0e-14).
Artifacts: `benchmarks/results/2026-10-05_streaming/` (frozen `streaming.jsonl`
+ `env.json` + `STREAMING_PUSH_REPORT.md`), plot `docs/img/streaming_push_cost.png`.

| Claim (docs/streaming.md) | Artifact value | Conditions |
|---|---|---|
| `push` ≈ 0.2 µs flat across W | 0.205 / 0.218 / 0.195 / 0.314 µs per push (50k pushes per capacity) | as above |
| `compute(kind="fast")` ≈ 0.4–0.7 µs flat across W | p50 0.60 / 0.70 / 0.40 / 0.40 µs (2k calls per capacity) | as above |
| `compute(kind="all")` linear in W | p50 3.6 / 11.6 / 138.5 / 2350.0 µs | as above |
| end-to-end 14.4× vs naive recompute | stream 0.030 s vs naive 0.432 s (W=256, 99,744 points, fast compute every 64) | as above |

## Measured — 2026-11-22 Downstream UCR Predictive Performance (artifacts committed)

Suite: `benchmarks/bench_ucr_downstream.py`, canonical fixed train/test splits across 42 equal-length univariate UCR classification datasets (ArrowHead, BME, Beef, BeetleFly, BirdChicken, CBF, Chinatown, Coffee, DistalPhalanxOutlineAgeGroup, DistalPhalanxOutlineCorrect, DistalPhalanxTW, ECG200, ECGFiveDays, FaceFour, FacesUCR, GunPoint, Ham, Herring, ItalyPowerDemand, Lightning2, Lightning7, Meat, MedicalImages, MiddlePhalanxOutlineAgeGroup, MiddlePhalanxOutlineCorrect, MiddlePhalanxTW, MoteStrain, OliveOil, Plane, PowerCons, SmoothSubspace, SonyAIBORobotSurface1, SonyAIBORobotSurface2, SwedishLeaf, Symbols, SyntheticControl, ToeSegmentation1, ToeSegmentation2, Trace, TwoLeadECG, TwoPatterns, Wine), 16 threads across all 4 libraries, standard RandomForestClassifier(n_estimators=100) and RidgeClassifier(alpha=1.0) with leak-free SimpleImputer and StandardScaler fit strictly on train split.
Artifacts: `benchmarks/results/DOWNSTREAM_UCR_REPORT.md`, `benchmarks/results/ucr_downstream_results.json`.

| Claim | Artifact value | Conditions |
|---|---|---|
| Kymora core33 Ridge accuracy: 77.42% (rank 2.64) vs catch22 75.75% (rank 2.98), TSFEL 79.71% (rank 2.26), tsfresh 82.39% (rank 1.79) | `DOWNSTREAM_UCR_REPORT.md` | Matched set n=42, fixed train/test splits, leak-free StandardScaler, 16 threads |
| Kymora core33 RF accuracy: 79.96% (rank 2.71) vs catch22 79.83% (rank 2.79), TSFEL 81.00% (rank 2.33), tsfresh 84.79% (rank 1.64) | `DOWNSTREAM_UCR_REPORT.md` | Matched set n=42, fixed train/test splits, 16 threads; Kymora vs catch22 head-to-head W/T/L 23/3/16 (RF) and 23/5/14 (Ridge); Holm-adjusted p = 0.5554 (RF), 0.2016 (Ridge); Critical Difference CD = 0.72 |
| Kymora extraction time 1.26 ms vs catch22 159.40 ms (117.2×), TSFEL 942.67 ms (768.2×), tsfresh 20,943.62 ms (17,217.0×) | `DOWNSTREAM_UCR_REPORT.md` | Median across datasets / per-dataset speedups (matched set n=42, 16 threads) |

## Pending re-baseline (no artifact — still stale)

- tsfresh 100,000 × 500 memory cell (multi-hour run; README marks it PENDING).
- Landing hero demo latencies were replaced with real catalog values in
  8.4; `index.html` meta description (314k series/s) traces to the F1 pool
  above. No landing figure is pending.
- PyPI long_description syncs automatically (single-sourced from README at
  build time).
