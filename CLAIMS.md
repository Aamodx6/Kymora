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

## Measured — 2026-10-05 hardening re-baseline (same laptop, same conditions; artifacts committed)

Suites: `benchmarks/suites/equal_feature.py`, `benchmarks/suites/remeasure_readme.py`.
Artifacts: `benchmarks/results/2026-10-05_equal_feature/` + `EQUAL_FEATURE_REPORT.md`,
`benchmarks/results/2026-10-05_remeasure/`. Parity gate (EXACT ≤ 1e-9 per
feature pair) re-verified before any equal-feature timing.

| Claim (README) | Artifact value | Conditions |
|---|---|---|
| Equal-feature: kymora fastest on all 16 rows, ratios 3.4×–11.1× vs numba, 61.0×–122.2× vs numpy, 19.1×–1,150.6× vs TSFEL, 249.9×–1,693.8× vs tsfresh | `equal_feature.jsonl`, ratio + 95% CI per row (4 shapes × 4 competitors) | 1,000×500 headline: kymora med 4.72 / 4.68 / 3.92 / 4.94 ms vs numba 16.05 / numpy 285.50 / TSFEL 2,213.69 / tsfresh 8,359.45 ms → 3.4× [3.1,3.9] / 61.0× [60.0,62.0] / 564.6× [509.7,781.4] / 1,693.8× [1,645.5,1,900.1] |
| Profiles: minimal 1.20 ms / core33 2.88 / extended 10.10 / full 11.10 (best 0.93 / 2.44 / 8.96 / 9.84); per-feature 0.120 / 0.0873 / 0.0706 / 0.0204 µs; throughput 833,333 series/s (minimal), 346,963 series/s (core33), 99,028 series/s (extended), 90,052 series/s (full) | `remeasure_summary.json` profiles[] | 1,000×500, 16 threads, gaussian, seed 42 |
| Scaling: 1T 12.47 / 2T 7.01 / 4T 4.11 / 8T 3.03 / 16T 2.93 / 32T 3.51 ms; speedups 1.78× / 3.03× / 4.12× / 4.25× / 3.56×; η 89.0 / 75.7 / 51.5 / 26.6 / 11.1% | `remeasure_summary.json` scaling[] | core33, 1,000×500 |
| Memory: kymora 100k×500 core33 peak +417.7 MiB (input 385.4, extraction +32.3, output 25.2) | `remeasure_summary.json` memory[] | fresh-process peak RSS delta |
| tsfresh memory: extraction +281.9 MiB @1k×500, +407.5 MiB @10,000 × 500 (totals +289.8 / +449.5) | same | EfficientFCParameters, n_jobs=16 |
| Where-slower (HEAD rerun 2026-10-05): numba losses only at 1×100 — gaussian 1.78× [1.76,1.80], heavy_tailed 1.75× [1.74,1.76], random_walk 1.43× [1.42,1.45] (call-overhead+quantile-stage); 10×500 rows parity/noise (0.85×–1.08×, CIs cross 1.0); 1×100 medians km ~0.029 ms vs numba 0.016–0.020 ms (v0.3.0 floor 0.6–0.7 ms and 17.9×–40.2×/3.1×–5.7× superseded); 100×100 16T +27% vs 1T (~12 µs/series compute); len-10 single-series p50 345.8 µs (win) vs numpy 1,317.6 µs, p99 15.4 ms / max 29.1 ms (loss); 100×500 parity 0.94×–0.99× | `2026-10-05_l1_rerun/l1_root_cause.json` (loss table + stage timings + classifications; replaces v0.3.0 `L1_ROOT_CAUSE.md`/`l1_root_cause.json` numbers), `B3_REPORT.md` §3.1 | 16 threads unless noted; CIs exclude 1.0 for robust losses |

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

## Pending re-baseline (no artifact — still stale)

- tsfresh 100,000 × 500 memory cell (multi-hour run; README marks it PENDING).
- Single-series latency figures in `docs/benchmarks.md` (marked † there).
- Landing hero demo latencies were replaced with real catalog values in
  8.4; `index.html` meta description (314k series/s) traces to the F1 pool
  above. No landing figure is pending.
- PyPI long_description syncs automatically (single-sourced from README at
  build time).
