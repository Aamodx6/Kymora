# CLAIMS.md

Every public performance claim → artifact path → code state → conditions
(arch.md §14.1). No evidence ⇒ remove or soften. Hardware + thread count
beside every headline number; laptop wording is "10 cores (6P+4E) /
16 threads".

## Measured (artifact: `benchmarks/results/F1_REPORT.md` + `F1_P1/`, `F1_H1/`, `F1_P2/`, `F1_H2/` jsonl+env)

Measured 2026-10-04, interleaved P1→H1→P2→H2 on one machine (i7-13620H
laptop, 10 cores / 16 threads, Windows 11, Performance plan, AC online,
Python 3.14.6, NumPy 2.5.2). Code states: pre-refactor tag `4c268ca`
(dist `tsxtract` 0.5.0 wheel, built from worktree) vs HEAD `9c1b3dd`
(dist `tsxtract-rs` 0.5.0 wheel). Suite:
`benchmarks/suites/reproduce_readme.py` @ HEAD for all rounds, 1,000
series × 500 steps, f64 C-contiguous gaussian, 16 threads, seed 42.

| Claim (README) | Artifact value | Conditions |
|---|---|---|
| `core33` median 3.25 ms / 307,366 series/s (1k×500) | pooled HEAD median (n=200), 95% CI [3.21, 3.32] ms | as above |
| `core33` best 2.29 ms / 436,719 series/s | pooled HEAD best (n=200) | as above |
| ~261× vs catch22 | 848.51 ms pooled competitor median (n=21) ÷ 3.2534 ms | same machine/env; pycatch22, versions in F1 env.json |
| ~829× vs TSFEL | 2,698.67 ms pooled median (n=32) ÷ 3.2534 ms | same |
| ~7,038× vs tsfresh | 22,896.46 ms pooled median (n=24) ÷ 3.2534 ms | tsfresh 0.21.2; same |
| refactor is perf-neutral | tsxtract CIs overlap: pre [3.26,3.36] vs HEAD [3.21,3.32] ms | interleaved; median delta −1.8% is noise |

Superseded by the above (kept here so stale copies are recognizable):
800,256 series/s headline, 1.80 ms / 555,016 table row, 820× / 580× /
5,443× / 14,000× / 55,779× ratios, 1,045.8 / 9,806.6 / 100,500.0 ms
competitor rows — all predate the 2026-10-04 re-baseline (different
hardware/software).

## Pending re-baseline (no artifact — marked † in README)

- Profile rows `minimal` / `extended` / `full` (0.51 / 7.12 / 8.36 ms…).
- Multi-core scaling table (11.31 → 2.60 ms…).
- Memory footprint rows (25.18 MiB own / +1,250 MiB tsfresh).
- Landing + docs benchmark figures, `index.html` meta description,
  PyPI long_description (self-corrects on next release build).
