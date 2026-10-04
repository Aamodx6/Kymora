# CLAIMS.md

Every public performance claim → artifact path → code state → conditions
(arch.md §14.1). No evidence ⇒ remove or soften. Hardware + thread count
beside every headline number; laptop wording is "10 cores (6P+4E) /
16 threads".

## Measured — exploratory (single laptop, not fleet evidence; artifact: `benchmarks/results/F1_REPORT.md` + `F1_*` / `B_*` jsonl+env)

Measured 2026-10-04: step-2 interleave (P1→H1→P2→H2) plus 3b bisect
rounds (`B_040_R1/R2`, `B_PRE_R1c/R2`, `B_HEAD_R1/R2`; probe sets PA2/PB),
one machine (i7-13620H laptop, 10 cores / 16 threads, Windows 11,
Performance plan, AC online, Python 3.14.6, NumPy 2.5.2). Code states:
pre-refactor tag `4c268ca`, HEAD `9c1b3dd` (step-2) → `88298f5`/`de1982f`
(code-identical for numerics), PyPI `tsxtract-rs` 0.3.2 / 0.4.0 in
isolated venvs. Suite: `benchmarks/suites/reproduce_readme.py` @ HEAD
for all rounds, 1,000 series × 500 steps, f64 C-contiguous gaussian,
16 threads, seed 42. Every run records `n_features` (observed: 33 / 22
/ 156 / 777 — singleton sets, no variation).

| Claim (README) | Artifact value | Conditions |
|---|---|---|
| `core33` median 3.18 ms / 314,450 series/s (1k×500) | pooled HEAD median, 4 rounds (n=400), 95% CI [3.15, 3.22] ms | as above |
| `core33` best 2.29 ms / 436,719 series/s | pooled HEAD best (n=400) | as above |
| 0.0964 µs per series-feature | 3.1802 ms ÷ (1000 × 33) | as above |
| 262× vs catch22 raw (393× per-feature) | 833.08 ms pooled median, 10 rounds (n=53), CI [798.29, 850.81] ÷ 3.1802 ms; per-feature 37.8671 ÷ 0.0964 µs | same machine/env; pycatch22, versions in round env.json |
| 799× vs TSFEL raw (169× per-feature) | 2541.61 ms pooled median, 10 rounds (n=83), CI [2463.14, 2672.21] ÷ 3.1802 ms; per-feature 16.2924 ÷ 0.0964 µs | same |
| 6,570× vs tsfresh raw (279× per-feature) | 20891.23 ms pooled median, 10 rounds (n=64), CI [20062.15, 21530.14] ÷ 3.1802 ms; per-feature 26.8870 ÷ 0.0964 µs | tsfresh 0.21.2; same |
| refactor is perf-neutral | suite CIs overlap pre/HEAD in step 2; 3b probe CIs overlap 0.4.0/pre/HEAD | interleaved + rotated |
| ~15% step 0.3.2→0.4.0, then flat | probe medians 2.00 [1.97,2.02] vs 2.41 / 2.44 / 2.47 (CIs overlap for the latter three), identical 33-name catalog | direct-probe methodology; dispatch-overhead hypothesis unprofiled |

Superseded by the above (kept here so stale copies are recognizable):
800,256 series/s headline, 1.80 ms / 555,016 table row, 820× / 580× /
5,443× / 14,000× / 55,779× ratios, 1,045.8 / 9,806.6 / 100,500.0 ms
competitor rows — all predate the 2026-10-04 re-baseline (different
hardware/software). Step-2 interim values (307,366 s/s; 261×/829×/
7,038× from 4 rounds) superseded by the 10-round pools above.

## Pending re-baseline (no artifact — marked † in README)

- Profile rows `minimal` / `extended` / `full` (0.51 / 7.12 / 8.36 ms…).
- Multi-core scaling table (11.31 → 2.60 ms…).
- Memory footprint rows (25.18 MiB own / +1,250 MiB tsfresh).
- Landing + docs benchmark figures, `index.html` meta description,
  PyPI long_description (self-corrects on next release build).
