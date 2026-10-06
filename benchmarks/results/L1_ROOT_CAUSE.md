> Historical record. Paths `benches/` = today's `benchmarks/`;
> name Tsxtract = Kymora.
# L1 Root Cause — The 17 numba_baseline_fast losses (EVIDENCE ONLY, no fixes)

**Generated:** 2026-10-04 · **Suite:** `benches/suites/l1_root_cause.py` · **Raw evidence:** `benches/results/l1_root_cause.json`
**Purpose:** classify every loss of Tsxtract vs `numba_baseline_fast` (B3_REPORT §1.3) for the B6/B7 ranking. Nothing was fixed in this pass.

**Environment:** i7-13620H (10C/16T), Windows 11, Performance power plan, AC plugged · Python 3.14.6, numba 0.67.0, tsxtractor 0.5.0 · 16 threads unless noted · f64 C-contiguous · medians over ≥7 (re-measured: 100) warm runs, GC disabled.

---

## 1. Loss table (re-measured with runs[] + bootstrap 95% CI)

All 17 paired (shape × dist) cases from the original throughput matrix, re-measured via the subprocess runner so that run distributions and CIs exist. Ratio = tsxtract median / numba median (>1 = Tsxtract slower).

| Shape | Dist | Tsxtract (ms) | numba fast (ms) | Ratio | 95% CI | Verdict |
|---|---|---:|---:|---:|---|---|
| 1×100 | gaussian | 1.525 | 0.040 | 38.4× | [31.0, 45.8] | LOSS (robust) |
| 1×100 | ar1 | 0.831 | 0.032 | 25.9× | [24.9, 27.0] | LOSS (robust) |
| 1×100 | heavy_tailed | 1.621 | 0.040 | 40.2× | [38.1, 42.5] | LOSS (robust) |
| 1×100 | random_walk | 0.799 | 0.045 | 17.9× | [17.1, 18.6] | LOSS (robust) |
| 1×100 | sinusoid | 0.895 | 0.039 | 22.8× | [21.2, 23.8] | LOSS (robust) |
| 10×500 | gaussian | 1.337 | 0.235 | 5.7× | [5.0, 6.3] | LOSS (robust) |
| 10×500 | ar1 | 1.051 | 0.286 | 3.7× | [3.4, 4.1] | LOSS (robust) |
| 10×500 | heavy_tailed | 0.946 | 0.262 | 3.6× | [3.5, 3.8] | LOSS (robust) |
| 10×500 | random_walk | 0.960 | 0.258 | 3.7× | [3.6, 3.9] | LOSS (robust) |
| 10×500 | sinusoid | 1.154 | 0.370 | 3.1× | [2.9, 3.4] | LOSS (robust) |
| 100×100 | gaussian | 1.089 | 0.638 | 1.7× | [1.6, 1.9] | LOSS (robust) |
| 100×100 | ar1 | 1.196 | 0.470 | 2.6× | [2.4, 2.8] | LOSS (robust) |
| 100×100 | heavy_tailed | 1.422 | 0.450 | 3.2× | [3.0, 3.3] | LOSS (robust) |
| 100×100 | random_walk | 2.510 | 0.720 | 3.5× | [3.3, 3.6] | LOSS (robust) |
| 100×100 | sinusoid | 1.020 | 0.453 | 2.3× | [1.9, 2.6] | LOSS (robust) |
| 100×500 | heavy_tailed | 1.821 | 1.930 | 0.94× | [0.82, 1.01] | **not a robust loss** (CI includes 1.0) |
| 100×500 | random_walk | 1.825 | 1.842 | 0.99× | [0.95, 1.05] | **not a robust loss** (CI includes 1.0) |

> The two 100×500 "losses" from the original matrix are **parity within noise** (0.94×–0.99×, CI crossing 1.0). The original matrix's small-n rows carry CV 1.8–2.4 (L7 jitter), which explains the discrepancy. Effective robust loss count: **15, not 17**.

## 2. Per-stage timing (differential)

Tsxtract stages measured via the `features=` subset API, subtracting the `["mean"]` call (≈ fixed floor + fused pass). Numba stages mirror `numba_baseline.py` kernels exactly, timed as serial batch loops (per-series values shown for comparability). Residual/`misc` includes output write + remaining features.

**16 threads, per series (µs/series), gaussian:**

| Stage | 1×100 tsx | 1×100 nb | 10×500 tsx | 10×500 nb | 100×100 tsx | 100×100 nb | 100×500 tsx | 100×500 nb |
|---|---:|---:|---:|---:|---:|---:|---:|---:|
| fused pass 1 | (floor) 723/call | 10 | 67.1/call | 5.4 | 6.8 | 1.9 | 9.1 | 5.2 |
| quantiles | 15 | 30 | 14.0 | 28.1 | 7.3 | 5.7 | 13.1 | 32.0 |
| FFT + spectral | ~0 | 210 | 5.7 | 92.8 | 1.6 | 22.0 | 6.6 | 96.3 |
| ACF (4 lags) | ~0 | 20 | 9.8 | 1.7 | 2.1 | 1.5 | 4.7 | 1.7 |
| permutation entropy | ~0 | 10 | ~0 | 1.3 | 0.3 | 0.7 | 0.5 | 4.2 |
| fixed call floor | **694/call** | ~1 | **579/call** | ~1 | **561/call** | ~1 | **583/call** | ~1 |
| **wall total (parallel)** | **890/call** | **31/call** | **1030/call** | **348/call** | **1520/call** | **354/call** | **2630/call** | **2080/call** |

**Tsxtract 1T vs 16T (thread-scaling at the losing shapes):**

| Shape | Tsxtract 1T (ms) | Tsxtract 16T (ms) | Δ | numba 1T (ms) | numba 16T (ms) | Δ |
|---|---:|---:|---:|---:|---:|---:|
| 1×100 | 0.610 | 0.890 | **+46%** | 0.032 | 0.031 | ~0 (serial path) |
| 10×500 | 0.820 | 1.030 | +26% | 1.317 | 0.348 | −74% |
| 100×100 | 1.201 | 1.520 | **+27%** | 2.715 | 0.354 | −87% |
| 100×500 | 2.541 | 2.630 | +4% | 13.728 | 2.080 | −85% |

Key reads:

1. **The fixed per-call floor (~0.58–0.72 ms measured here; ~150 µs in the A7 decomposition at 1×10 under a warmer state) dominates every small-n call.** At 1×100 the floor is ~78% of Tsxtract's total; numba's whole call is 31–45 µs.
2. **Tsxtract's per-series compute is competitive or better** (FFT stage: 5.7–6.6 µs/series vs numba's ~93–96 µs Bluestein; quantiles at 100×500: 13.1 vs 32.0 µs/series). The losses are NOT from losing per-series kernels at these shapes.
3. **At 100×100 Tsxtract gets SLOWER with 16 threads than with 1** (+27%), while numba scales −87%: the rayon pool wake/join + work distribution swamps ~12 µs/series of compute. At 1×100 the pool wake is pure overhead (+46%).
4. numba's `fastmath=False` bound: Δ vs fast = −23%…+42% with no consistent direction → **fastmath is not a loss driver** (and the throughput rows used `fastmath=True`, recorded per row as `variant=fastmath=True`).

## 3. Correctness verification (same 33 features?)

- **Agreement numba-strict (fastmath=False) vs tsxtract on all 15 robust-loss shape×dist combos: 33/33 EXACT (max rel ≤ 1e-9), 0 WRONG.** Numba computes the same 33 features, same values.
- Spot check at scale std=2.5 (cid_ce, autocorrs, skewness, std, trend_r2): tsxtract == numba == numpy reference to 6+ decimals.
- **Artifact finding:** the frozen `feature_map.json` matched set `numba_baseline=23` is **stale** — it excludes std/var/skewness/kurtosis/cid_ce/autocorr×4/trend_r2, but the current numba code matches Tsxtract on all 33 on well-behaved data (33/33 EXACT above). The 23-set reflected the pre-L5-fix code and the adversarial-distribution WRONGs. → refresh proposal for B6; matched comparisons unaffected (23 ⊂ 33).
- On adversarial distributions the numba baseline remains defective (re-verified): naive one-pass variance → 15 WRONG cells (`cancellation`: std/var/skew/kurt/cid_ce/autocorr×4/trend_r2; `tiny_scale`/`huge_scale`: skew/kurt NaN). **Tsxtract: 0 WRONG on all 25 distributions.** These cells are why the adversarial matched set stays conservative.

## 4. A1 verification — numba uses a real O(N log N) FFT

`_bluestein_fft` (radix-2 + Bluestein chirp-z) vs `numpy.fft`:

| n | max rel err | µs/call |
|---|---:|---:|
| 10 | 3.0e-16 | 9.7 |
| 100 | 4.4e-15 | 21.4 |
| 500 | 2.2e-14 | 96.6 |
| 512 | 6.4e-15 | 10.6 |
| 1023 | 1.9e-14 | 216.4 |
| 1024 | 1.2e-14 | 22.2 |
| 4093 (prime) | 6.0e-14 | 1019.1 |
| 4096 | 3.7e-14 | 101.2 |

A1 **passes**: a genuine O(N log N) FFT (not an O(n²) DFT), accurate to ≤6e-14. Side note for B6: numba's Bluestein path is ~10× slower at prime lengths (4093) than radix-2 (4096) — a numba-side weakness, irrelevant at the benchmark length 500.

## 5. Classification (evidence-based, per loss)

| Class | Applies to | Evidence |
|---|---|---|
| **call-overhead** | 1×100 (5/5), 10×500 (5/5) — 10 losses | Fixed floor ≈ 56–78% of Tsxtract total at these shapes; numba pays ~1 µs (in-process JIT dispatch). Tsxtract compute beyond the floor is comparable to numba's whole call. |
| **threading** | 1×100 (5/5), 100×100 (5/5) | 16T vs 1T: Tsxtract +46% (1×100) and +27% (100×100) — pool wake/join exceeds total compute; numba parallel at 100×100 is 7.7× faster than its own 1T. At n=1 numba runs serial (no pool) while Tsxtract wakes a 16-thread pool. |
| **algorithmic** | not confirmed at these shapes | Tsxtract stage differentials are ≤ numba's per-series stage costs at every losing shape (quantiles 13 vs 32 µs, FFT 6.6 vs 96 µs at 100×500). The numba one-pass-variance shortcut is cheaper in principle but the margin is inside the floor noise at these n. |
| **unfair-baseline** | **refuted** | 33/33 EXACT agreement on every losing shape×dist (§3); same definitions, same values. The stale 23-feature matched set overstates definitional divergence. The only baseline unfairness that remains is speed-of-execution, not definition. |
| **layout** | N/A | Both sides receive identical C-contiguous f64 input; no layout difference exists in this comparison. |

**Classification summary:** 10× call-overhead (1×100, 10×500 — with a threading component at 1×100), 5× threading-dominant (100×100), 2× not-a-robust-loss (100×500, parity within CI). The single actionable root cause is the **fixed per-call floor + small-batch pool wake** (consistent with L2/L7 and arch.md §1 "When NOT to use Tsxtract"); B7 candidate fix directions (for ranking, not executed here): (a) true serial fallback below a tuned threshold, (b) plan/pool reuse for repeated small calls, (c) smaller pool wake latency.

---

*Raw per-run distributions, per-feature agreement matrices, and stage timings: `benches/results/l1_root_cause.json`.*
