# F1 interleaved benchmark — pre-refactor vs HEAD (2026-10-04)

Resolves the measurement half of arch.md F1 (README 1.25 ms / 800,256
series/s vs release-notes ~1.80 ms / 555k series/s for core33).

Code states: pre-refactor tag `4c268ca` (dist `tsxtract` 0.5.0 wheel built
2026-10-04 from a clean worktree) vs HEAD `9c1b3dd` (dist `tsxtract-rs`
0.5.0 wheel built from the trimmed tree). Claim updates derived from
this artifact only: README headline/profile/competitive rows +
root `CLAIMS.md`.

## Conditions (identical for all rounds)

- Machine: Intel i7-13620H, 10 cores (6P+4E) / 16 threads, Windows
  11 (10.0.26300), Python 3.14.6, NumPy 2.5.2
- Power plan: **Performance** (`powercfg` GUID 27fa6203-…); AC line
  **Online** (plugged in), battery 80%
- Suite: `benchmarks/suites/reproduce_readme.py` (HEAD version for every
  round — only the installed tsxtract wheel varies), 1,000 series × 500
  steps, f64 C-contiguous gaussian, 16 threads, seed 42
- Competitors from the same env all rounds: pycatch22, tsfel, tsfresh
  0.21.2 (unchanged — control for machine drift)
- Order (interleaved): **P1 → H1 → P2 → H2**; fresh
  `pip uninstall + force-reinstall --no-deps` between rounds
- Provenance per round: installed dist name + sha256 of live
  `tsxtract/__init__.py` (`fc73d17d…` = pre-refactor dist `tsxtract`,
  `0e3843cf…` = HEAD dist `tsxtract-rs`; `tsxtract-rs` absent in P
  rounds, `tsxtract` absent in H rounds)

## Per-round results (best / median, ms)

| Round | tsxtract (33) | catch22 (22) | tsfel (156) | tsfresh (777) |
|---|---|---|---|---|
| P1 pre-refactor | 2.36 / 3.18 | 769.78 / 778.25 | 2541.61 / 2797.13 | 22127.92 / 22634.57 |
| H1 HEAD | 2.95 / 3.46 | 837.95 / 857.79 | 2674.30 / 2937.34 | 22959.85 / 23659.88 |
| P2 pre-refactor | 2.62 / 3.44 | 875.76 / 913.60 | 2536.83 / 2694.08 | 22702.14 / 23144.48 |
| H2 HEAD | 2.29 / 3.10 | 798.29 / 827.40 | 2418.41 / 2458.23 | 19987.60 / 20231.09 |

Raw runs: `F1_P1/`, `F1_H1/`, `F1_P2/`, `F1_H2/` (`readme_reproduce.jsonl`
+ `env.json` each).

## Pooled (P1+P2 vs H1+H2) — median / best / 95% bootstrap CI of median

| Library | pre-refactor (n) | HEAD (n) |
|---|---|---|
| tsxtract | med **3.31**, best **2.36**, CI **[3.26, 3.36]** (n=200) | med **3.25**, best **2.29**, CI **[3.21, 3.32]** (n=200) |
| catch22 | med 833.08, CI [774.67, 913.60] (n=11) | med 851.73, CI [827.40, 870.06] (n=10) |
| tsfel | med 2734.53, CI [2693.66, 2811.43] (n=16) | med 2591.87, CI [2458.23, 2937.34] (n=16) |
| tsfresh | med 22896.46, CI [22634.57, 23166.56] (n=12) | med 22244.99, CI [20231.09, 23659.88] (n=12) |

In series/s (1,000 series): pre-refactor med **302,160** / best
**423,245**; HEAD med **307,366** / best **436,719**.
Pooled-median speedups on this machine: **258×** vs catch22, **821×**
vs tsfel, **6,967×** vs tsfresh.

## Verdict

1. **Refactor is perf-neutral:** tsxtract CIs overlap
   ([3.26,3.36] vs [3.21,3.32]); median delta −1.8% is noise. The
   quarantine (step 1) and renames changed nothing measurable.
2. **README numbers are irreproducible here:** headline 800,256 s/s
   (1.25 ms) is ~2.6× the measured median and ~1.9× the measured best;
   the 1.80 ms / 555,016 table row is ~1.8× the measured median.
   Competitor ratios are likewise inflated (820×/14,000× claimed vs
   258×/6,967× measured) — competitors also run *faster* than README
   here (tsfresh 22.9 s vs 100.5 s claimed: newer version + different
   machine). All README/landing/site figures predate this re-baseline
   and came from different hardware/software.
3. `LOSS_LEDGER.md` was left untouched (suite appends were backed up,
   inspected, and reverted — discrepancy data lives in the F1_* jsonl
   files and this report instead).

## Appendix 3b — version bisect (0.3.2 / 0.4.0 / pre-refactor / HEAD)

Same machine/plan/AC (Performance + Online, verified per-round via
`env.json`; one flap event during a discarded PRE round — Silent plan +
battery — excluded, as was an aborted partial round superseded by a full
re-run). Isolated venvs per version (`--system-site-packages` for
numpy/competitors; per-round provenance via installed dist + file sha).
Suite order R1: 032-probe, 040, PRE, HEAD; R2 rotated: PRE, HEAD, 040,
032-probe. 0.3.2 has no `import tsxtract` and its `extract_features(x)`
takes no kwargs, so it ran a direct probe (5 warmup + 100 timed, same
1k×500 f64 gaussian seed-42 input); a methodology-control probe set ran
all four versions through the identical direct probe (PA2 order
032→040→PRE→HEAD, PB rotated HEAD→PRE→040→032). 0.3.2's 33 feature
names hash **equals** HEAD's — identical catalog, so timing compares
identical work.

Pooled medians (95% bootstrap CI of median):

| version | suite med / best / CI (n) | direct-probe med / best / CI (n) |
|---|---|---|
| 0.3.2 (PyPI) | N/A (adapter-incompatible, see above) | 2.00 / 1.62 / [1.97, 2.02] (400) |
| 0.4.0 (PyPI) | 2.96 / 2.50 / [2.93, 3.01] (200) | 2.41 / 1.78 / [2.38, 2.44] (300) |
| pre-refactor `4c268ca` | 2.89 / 2.37 / [2.84, 2.94] (200) | 2.44 / 1.77 / [2.41, 2.50] (300) |
| HEAD `9c1b3dd` | 3.13 / 2.60 / [3.07, 3.16] (200) | 2.47 / 1.81 / [2.42, 2.53] (400) |

Rounds: `B_040_R1/R2`, `B_PRE_R1c/R2`, `B_HEAD_R1/R2` (full suites);
probes `B_032_R1/R2`, `B_probe_PA_v040`, `B_probe_PA2_*` (×4), `B_probe_PB_*` (×4), `B_probe_PA_vPRE`, `B_probe_PA_vHEAD`, `B_HEAD_probe`.
Excluded: `B_PRE_R1` (battery flap), partial `B_PRE_R1b` (aborted,
superseded), one mis-probed 032 run that measured main-env code (caught
by provenance check, redone).

Verdict: ~15% step down 0.3.2→0.4.0 on the identical catalog (dispatch
overhead from the profile/plan machinery is the unprofiled hypothesis);
0.4.0 ≈ pre-refactor ≈ HEAD flat (probe CIs overlap; suite shows HEAD
~3% above pre-refactor, inside same-day machine variance — competitors
drifted coherently across rounds). The 1.25/1.80 ms figures are
irreproducible at EVERY version on this machine (even 0.3.2's best,
1.62 ms) → different hardware, not a regression. 0.3.2's own PyPI page
already claimed 800,256.
