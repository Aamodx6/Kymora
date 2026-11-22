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
| Headline raw throughput: pooled median 1.74 ms / 575,391 series/s (95% bootstrap CI [566,701, 581,581] series/s, [1.72, 1.76] ms; session range 559,268 – 598,247 series/s; best single run 1.25 ms / 799,680 series/s). Raw ratios: 249× catch22 (373× per-feature), 1,175× TSFEL (248× per-feature), 8,612× tsfresh (366× per-feature); 0.0527 µs per series-feature | `HEADLINE_THROUGHPUT_REPORT.md` (`headline_results.json`) + `2026-11-22_reproduce_readme/readme_reproduce.jsonl`: catch22 432.59 ms / 2,312 s/s / 19.66 µs, TSFEL 2,041.53 ms / 490 / 13.09 µs, tsfresh 14,966.81 ms / 67 / 19.26 µs. Previous exploratory Silent session: 1.84 ms / 542,682 series/s (best 1.57 ms / 636,943 series/s; 235× raw / 352× per-feature catch22, 1,108× / 234× TSFEL, 8,122× / 345× tsfresh; 0.0558 µs; same-day 4-round repeat 2.53 ms) | 1,000×500, full default catalogs (33 / 22 / 156 / 777 features), 16 threads, High Performance plan, AC online, gaussian seed 42, f64 C-order |
| Equal-feature: kymora fastest on all 16 rows, 6.0×–2,812.4× overall (numba 6.0×–11.8×, numpy 107.9×–199.2×, TSFEL 35.6×–1,369.0×, tsfresh 253.1×–2,812.4×) | `equal_feature.jsonl`, ratio + 95% CI per row (4 shapes × 4 competitors) | 1,000×500 headline: kymora med 2.24 / 2.19 / 1.97 / 2.34 ms vs numba 13.34 / numpy 361.33 / TSFEL 2,145.73 / tsfresh 6,580.57 ms → 6.0× [5.7,6.5] / 165.1× [157.2,170.5] / 1,089.1× [1,007.3,1,132.2] / 2,812.4× [2,584.3,2,914.1] |
| Small-batch fast path (HEAD): sequential inline caller execution (<50k points) eliminates thread pool wake jitter. 1×10 p50 19.4 µs (p99 46.0 µs, max 64.9 µs; vs stale 15.4 ms); 1×100 p50 21.3 µs (p99 38.9 µs) vs numba 11.9 µs (honest loss 1.79×); 10×500 p50 120.5 µs vs numba 741.9 µs (6.2× win, ratio 0.16×); 100×100 p50 126.7 µs vs numba 1517.5 µs (12.0× win, ratio 0.08×; 16T vs 1T speedup 2.76×, ratio 0.36×); 100×500 p50 336.7 µs vs numba 7598.9 µs (22.6× win, ratio 0.04×; 16T vs 1T speedup 3.13×, ratio 0.32×) | `SMALL_BATCH_REPORT.md` (`small_batch_results.json`) | HEAD build, High Performance, 1T and 16T, bit-identical to parallel dispatch verified |
| Streaming (HEAD re-validation): push p50 0.20 µs flat across W (p99 0.20 µs); max push latency reflects drift-guard re-anchoring (60.1 µs @ W=64, 68.2 µs @ W=256, 21.7 µs @ W=4096, 315.7 µs @ W=65536; amortized O(1), worst-case O(W)). compute(fast) p50 0.30 µs flat across all W (p99 0.30–0.40 µs, max 0.8–3.9 µs); compute(all) p50 1.80 µs (W=64) to 1326.60 µs (W=65536) linear in W. End-to-end 86.8×–8566.4× vs naive recompute | `2026-11-22_streaming/STREAMING_PUSH_REPORT.md` (`streaming.jsonl`) | Single thread, W ∈ {64, 256, 4096, 65536}, parity-gated before timing; math.fsum and np.longdouble reference bounds verified |
| Profiles: minimal 0.58 ms / core33 1.90 / extended 8.02 / full 9.44 (best 0.48 / 1.62 / 6.86 / 7.88); per-feature 0.0583 / 0.0575 / 0.0561 / 0.0174 µs; throughput 1,716,444 series/s (minimal), 526,912 series/s (core33), 124,635 series/s (extended), 105,982 series/s (full) | `remeasure_summary.json` profiles[] | 1,000×500, 16 threads |
| Scaling: 1T 11.22 / 2T 5.83 / 4T 3.40 / 8T 2.22 / 16T 2.30 / 32T 2.09 ms; speedups 1.92× / 3.30× / 5.05× / 4.87× / 5.37×; η 96.1 / 82.6 / 63.1 / 30.5 / 16.8% | `remeasure_summary.json` scaling[] | core33, 1,000×500 |
| Memory: kymora 10k×500 peak extraction +5.73 MiB (input 41.73, output 2.52, scratch 3.21 MiB; no copy of the input); 100k×500 core33 peak +418.0 MiB (input 385.2, extraction +32.8, output 25.2, scratch ~7.6 MiB). tsfresh extraction peak +293.2 MiB @1k×500 and +410.3 MiB @10k×500 (totals 300.9 / 452.2; 71.6× kymora extraction overhead) | `remeasure_summary.json` memory[] + measured scratch deltas | fresh-process peak RSS delta; tsfresh EfficientFCParameters, n_jobs=16 |
| Profiling slowdown 0.3.2 → 0.4.0: ~15% delta (2.00 ms → 2.30–2.41 ms) explained by FeaturePlan bitflag dispatch (~6%), FFI safety and NaN handling (~4%), and scratch arena lifecycle (~5%) | `docs/internal/slowdown_0.4.0.md` | 1k×500 probe profiling, flamegraph analysis |
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

Suite: `benchmarks/bench_ucr_downstream.py`, 5-fold stratified cross-validation on canonical UCR classification datasets (GunPoint, ItalyPowerDemand, ArrowHead, Coffee, ECG200, Trace, TwoLeadECG, SyntheticControl), standard RandomForestClassifier(n_estimators=100) and RidgeClassifier(alpha=1.0).
Artifacts: `benchmarks/results/DOWNSTREAM_UCR_REPORT.md`, `benchmarks/results/ucr_downstream_results.json`.

| Claim | Artifact value | Conditions |
|---|---|---|
| Kymora core33 Ridge accuracy: 93.58% (rank 2.25) vs catch22 90.47% (rank 3.25) | `DOWNSTREAM_UCR_REPORT.md` | 5-fold stratified CV, leak-free StandardScaler, 8 UCR benchmarks |
| Kymora core33 RF accuracy: 92.34% vs catch22 93.73%, TSFEL 95.55%, tsfresh 95.97% | `DOWNSTREAM_UCR_REPORT.md` | 5-fold stratified CV, 8 UCR benchmarks (tsfresh evaluated on 5 matched datasets due to long series extraction runtime; Kymora RF accuracy on the same 5 matched datasets is 91.80%) |
| Kymora extraction time 0.81 ms vs catch22 60.68 ms (80×), TSFEL 3,037.06 ms (5,344×), tsfresh 7,592.33 ms (7,788×) | `DOWNSTREAM_UCR_REPORT.md` | Median across datasets / per-dataset speedups |

## Pending re-baseline (no artifact — still stale)

- tsfresh 100,000 × 500 memory cell (multi-hour run; README marks it PENDING).
- Landing hero demo latencies were replaced with real catalog values in
  8.4; `index.html` meta description (314k series/s) traces to the F1 pool
  above. No landing figure is pending.
- PyPI long_description syncs automatically (single-sourced from README at
  build time).
