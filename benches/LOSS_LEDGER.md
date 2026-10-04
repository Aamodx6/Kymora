# Tsxtract Loss Ledger

**Purpose:** Record every case where Tsxtract loses, is fragile, or has a known limitation — per arch.md §13.
**Rule:** A thin lead or a known weakness is documented, not hidden.

---

## Active Losses / Known Limitations

### L1: Numba baseline faster than Tsxtract at small/mid batch sizes
- **Found:** Phase B3 throughput suite (complete: 45 paired cases, 5 shapes × 5 dists × {1×100, 1×10000, 10×500, 100×100, 100×500, 100×5000, 1000×100, 1000×500, 10000×500})
- **Detail:** `numba_baseline_fast` (fastmath=True, compiled, no FFI) beats Tsxtract in **17/45** paired cases (B3_REPORT.md §1.3). Losses at: **1×100 (5/5 dists**, e.g. gaussian 0.026 ms vs 0.639 ms — numba ~24× faster**), 10×500 (5/5**, 0.18 vs 0.54 ms**), 100×100 (5/5**, 0.43 vs 0.85 ms**), 100×500 (2/5**, heavy_tailed & random_walk, 1.96–2.08 vs 2.96–3.32 ms**)**.** Tsxtract wins everywhere else, including n=1 only for long series (1×10000: 0.97 vs 3.48 ms) and all n≥1000 shapes (up to 8.5× faster at 10000×500). Crossover is batch-size dependent: roughly n≈100–1000 series.
- **Impact:** **GENUINE LOSS.** For single-series or small-batch extraction, a compiled in-process kernel has near-zero call overhead; Tsxtract's ~150–200 µs fixed FFI+plan cost dominates (see L2). Tsxtract still beats the NumPy baseline in 45/45 cases (median 17×, thin win 1.99× at 1×100).
- **Mitigation:** Documented in "When NOT to use Tsxtract" (arch.md §1). Batch workloads (n≥1000) are the target use case where Tsxtract dominates. Candidate B7 fixes: reuse cached plans / skip pool wake for n=1 fast path; measure with latency_overhead decomposition.

### L2: HIGH-LATENCY-SMALL-CALL (fixed overhead)
- **Found:** Phase B0/A7
- **Detail:** Fixed per-call overhead ~150 µs p50 (110 µs min) for 1×10 (decomposition in `benches/suites/latency_overhead.py`: PyO3 wrapper, checks, plan build, output alloc, GIL release/acquire).
- **Impact:** NumPy baseline is ~1.3 ms at 1×10 (~8× slower p50), so Tsxtract still wins even on tiny calls. But the ~150 µs floor caps per-call throughput on trivially small inputs, and feeds L1.
- **Mitigation:** Documented in "When NOT to use Tsxtract" (arch.md §1). Pool wake/plan build cost.

### L3: Parallel efficiency degrades at 8+ threads on this hardware
- **Found:** Phase B3 scaling suite
- **Detail:** 10-core hybrid CPU (P+E cores), η=80% at 4T, η=54% at 8T, η=25% at 16T. Amdahl serial fraction f=21.2%.
- **Impact:** At 1000×500, speedup plateaus ~4.3× at 8T. Oversubscription (32T) hurts.
- **Root cause:** (1) Per-series compute ~10 µs is small vs rayon wake/join at 1k series. (2) E-cores are slower. (3) Serial fraction includes plan creation, output allocation.
- **Mitigation:** Expected on hybrid hardware. Need dedicated Linux/server runs for authoritative numbers. Efficiency improves at larger batches (100k series).

### L4: Cancellation distribution produces CLOSE (not EXACT) agreement
- **Found:** Phase B1 agreement suite
- **Detail:** For `1e9 + noise` data, 9/33 features are CLOSE (rel ≤ 1e-5) vs NumPy reference: skewness, kurtosis, autocorrelations, trend_r2, spectral centroid/entropy. This is expected: different algorithms (two-pass Welford vs one-pass) handle catastrophic cancellation differently.
- **Impact:** Not a bug. Both Tsxtract and NumPy produce valid results within tolerance.
- **Mitigation:** Documented in AGREEMENT_REPORT.md. No fix needed.

### L5: Numba baseline naive variance underflows for tiny_scale data
- **Found:** Phase B1 debugging (resolved — see R1)
- **Detail:** `std^3` underflows below f64 minimum denormal (~5e-324) when std < 7e-109, causing ZeroDivisionError in Numba fastmath=False mode.
- **Impact:** Only affects the numba benchmark baseline, NOT Tsxtract.
- **Fix:** Applied — compute skewness/kurtosis via z-scores instead of m3/(n·std^3).

### L6: catch22 matched set is 0/33
- **Found:** Phase B1
- **Detail:** pycatch22 uses different feature definitions (DN_HistogramMode_5, CO_trev_1_num, etc.) that don't correspond directly to our core33 canonical names.
- **Impact:** Cannot do matched-feature throughput comparison with catch22. Only raw runtime comparison.
- **Mitigation:** Document the mismatch. catch22 is still included in raw throughput comparisons.

### L7: Tail latency (p95+) loses to NumPy at len=10 single-series
- **Found:** Phase B3 latency suite (`single_series_by_length`, 200 runs, 1 thread)
- **Detail:** At 1×10, Tsxtract wins p50 (345.8 µs vs NumPy 1317.6 µs) but **loses the tail**: p95 6986.4 vs 2673.0 µs, p99 15375.8 vs 3220.5 µs, max 29121.1 vs 4732.2 µs. Throughput suite shows the same jitter (CV 1.8–2.4 at 1-series shapes vs 0.05–0.3 for baselines). At len≥50 the Tsxtract tail is clean (p99 ≤ 465 µs up to len=1000).
- **Impact:** **GENUINE LOSS for tail-latency-sensitive tiny-call workloads.** p50 still wins; the defect is sporadic ~15–29 ms spikes on the first touches of a tiny input.
- **Hypothesis (unconfirmed, for B7):** rayon pool wake on first call, OS scheduling on hybrid P/E cores, first-touch page faults, or power-state transitions. Needs targeted reproduction (e.g. pin thread, pre-warm, measure call 1 vs call N separately).
- **Mitigation:** Flag in "When NOT to use Tsxtract" (tiny-call tail). Investigate in B7 before any claim of fixed overhead being jitter-free.

---

## Resolved

### R1: Numba ZeroDivisionError on tiny_scale
- **Found:** B1
- **Fix:** z-score computation in numba_baseline.py (commit 81c2436)
- **Verified:** All 25 distributions pass after fix.

---

*Updated: 2026-10-04 (Phase B3 complete data: throughput 135/135, scaling 18, latency 30 rows)*
