# Tsxtract Loss Ledger

**Purpose:** Record every case where Tsxtract loses, is fragile, or has a known limitation — per arch.md §13.
**Rule:** A thin lead or a known weakness is documented, not hidden.
**Canonical path:** `benchmarks/results/LOSS_LEDGER.md` (arch.md §13; also the append target of `benchmarks/suites/reproduce_readme.py` and `benchmarks/suites/latency_overhead.py`).

> Merge note (2026-10-04): this file unifies two ledgers — the B3-era ledger
> previously kept at `benchmarks/LOSS_LEDGER.md` (L1–L7, R1; that duplicate
> has been removed) and the B0-era detailed evidence in Appendix A (A5/A7
> deep-dives, previously the sole content of this file). No entry was
> deleted. Where numbers differ between eras (e.g. L2's ~150 µs floor vs the
> Appendix A 7.29 µs decomposition), both are kept with their provenance;
> reconciling them is B7 work, not an edit to this file.

---

## Active Losses / Known Limitations

### L1: Numba baseline faster than Tsxtract at small/mid batch sizes
- **Found:** Phase B3 throughput suite (complete: 45 paired cases, 5 shapes × 5 dists × {1×100, 1×10000, 10×500, 100×100, 100×500, 100×5000, 1000×100, 1000×500, 10000×500})
- **Detail:** `numba_baseline_fast` (fastmath=True, compiled, no FFI) beats Tsxtract in **17/45** paired cases (B3_REPORT.md §1.3). Losses at: **1×100 (5/5 dists**, e.g. gaussian 0.026 ms vs 0.639 ms — numba ~24× faster**), 10×500 (5/5**, 0.18 vs 0.54 ms**), 100×100 (5/5**, 0.43 vs 0.85 ms**), 100×500 (2/5**, heavy_tailed & random_walk, 1.96–2.08 vs 2.96–3.32 ms**)**.** Tsxtract wins everywhere else, including n=1 only for long series (1×10000: 0.97 vs 3.48 ms) and all n≥1000 shapes (up to 8.5× faster at 10000×500). Crossover is batch-size dependent: roughly n≈100–1000 series.
- **Impact:** **GENUINE LOSS.** For single-series or small-batch extraction, a compiled in-process kernel has near-zero call overhead; Tsxtract's ~150–200 µs fixed FFI+plan cost dominates (see L2). Tsxtract still beats the NumPy baseline in 45/45 cases (median 17×, thin win 1.99× at 1×100).
- **Mitigation:** Documented in "When NOT to use Tsxtract" (arch.md §1). Batch workloads (n≥1000) are the target use case where Tsxtract dominates. Candidate B7 fixes: reuse cached plans / skip pool wake for n=1 fast path; measure with latency_overhead decomposition.

### L2: HIGH-LATENCY-SMALL-CALL (fixed overhead)
- **Found:** Phase B0/A7
- **Detail:** Fixed per-call overhead ~150 µs p50 (110 µs min) for 1×10 (decomposition in `benchmarks/suites/latency_overhead.py`: PyO3 wrapper, checks, plan build, output alloc, GIL release/acquire).
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

## Appendix A — Prior detailed evidence (B0 era, carried over verbatim)

The two items below are the pre-merge content of this file (Phase B0 /
Amendments A5/A7). Kept for their quantitative detail (overhead
decomposition table, README audit table). Status note: the
README-discrepancy investigation was later superseded by the F1
reproduce_readme audit — see `benchmarks/results/F1_REPORT.md` and arch.md
§2.2 (F1: RESOLVED 2026-10-04, claims rewritten from artifact). The original
entries are preserved unedited.

## Item: HIGH-LATENCY-SMALL-CALL
- **Category:** Latency / Small Batch Dispatch Floor
- **Discovered In:** Phase B0 / Amendment A7 Fixed-Overhead Decomposition Benchmark
- **Status:** OPEN (Baseline Evidence Established)
- **Impact Score:** 4 (High impact for real-time single-sample telemetry / online streaming)

### Summary & Evidence
When invoking `tsxtractor.extract_features` on tiny series ($n=1, \text{len}=10$ or $n=2, \text{len}=32$), execution exhibits a fixed latency floor of **7.29 µs** (preallocated: **6.93 µs**), compared to pure mathematical kernel execution time of **~1.73 µs**. Over 75% of the wall-clock time is spent in fixed dispatch overhead.

### Quantitative Decomposition Table:
| Stage / Benchmark Component | n=1, len=10 (µs) | n=2, len=32 (µs) | Percentage (n=1) |
|---|---|---|---|
| **Total Call Latency (Standard)** | **7.29 µs** | **12.22 µs** | **100.0%** |
| Preallocated Buffer Call (`out=`) | 6.93 µs | 11.49 µs | 95.1% |
| Output Array Allocation (`PyArray2::zeros`) | 0.37 µs | 0.73 µs | 5.1% |
| PyO3 Wrapper & FFI Boundary | ~1.20 µs | ~1.20 µs | ~18.8% |
| Dynamic `FeaturePlan::build` (Vec / String allocs) | ~2.10 µs | ~2.10 µs | ~32.9% |
| Thread Pool / Rayon Threshold Check (Serial) | ~0.60 µs | ~0.60 µs | ~9.4% |
| Scratch Workspace Allocation (`Scratch::new`) | ~0.80 µs | ~1.20 µs | ~12.5% |
| Pure Math Kernel Computation | ~1.73 µs | ~2.87 µs | ~23.7% |

### Root Cause Analysis:
1. **Dynamic Plan Allocation on Every Call:** `extract_features` calls `FeaturePlan::build_with_views` unconditionally, allocating `Vec<PlanItem>`, `Vec<String>`, and `Vec<usize>` on every call even when profile is default `core33`.
2. **Scratch Buffer Allocation:** In `extract_plan_into_slice`, `Scratch::new(max_len)` is allocated on every serial invocation instead of reusing a thread-local scratchpad.
3. **PyO3 Output Allocation:** Default allocation creates a fresh NumPy 2D array inside PyO3.

### Remediation Targets for Phase B7:
1. Cache static pre-built `FeaturePlan` instances for standard profiles (`core33`, `minimal`, `full`) to eliminate vector allocations.
2. Use thread-local reusable `Scratch` workspace for small serial batches ($N < 8$).
3. Target: reduce single-call latency floor from ~6.4 µs to < 1.8 µs.

## Item: README-DISCREPANCY-INVESTIGATION
- **Category:** Methodological / Environment Variance vs README
- **Discovered In:** Phase B0 / Amendment A5 README Reproduction Suite
- **Status:** OPEN (Investigation Required Before Phase B3)
- **Impact Score:** 3 (Cross-system reproducibility and documentation accuracy)

### Summary & Measured Evidence
On the current test environment (Intel Core i7-13620H 10 cores / 16 threads @ 2.4 GHz, Windows 11), measured figures for 1,000 series × 500 length with 16 threads exhibit a consistent ~85–95% latency delta relative to the published README benchmark numbers:

| Item ID | Library | Target Feats | README Best (ms) | Measured Best (ms) | Measured Median (ms) | Deviation vs README | Status |
|---|---|---|---|---|---|---|---|
| `README-DISCREPANCY-TSXTRACT` | `tsxtract` | 33 | 1.80 ms | 3.54 ms | 7.34 ms | +96.6% | OPEN |
| `README-DISCREPANCY-CATCH22` | `catch22` | 22 | 1,045.80 ms | 1,950.92 ms | 2,040.59 ms | +86.5% | OPEN |

### Methodology Investigation Requirement:
1. **Clock Frequency & Thermal Throttling:** README figures were obtained on high-performance desktop/server hardware with higher sustained multi-core clock speeds (>4.5 GHz vs 2.4 GHz laptop base clock).
2. **OS & SMT Topology:** Windows thread scheduling across hybrid P-cores (6) and E-cores (4) introduces core migration jitter compared to homogeneous Linux servers.
3. Both libraries scale proportionally (~85-95% shift), confirming that Tsxtract maintains its relative 550× advantage over catch22 under identical hardware conditions.


### README Reproduction Discrepancy Ledger Entries
**Audit Run Date:** 2026-10-04 12:12:50  
| Item ID | Library | Target Feats | README ms | Meas Best ms | Meas Med ms | Dev % | Status |
|---|---|---|---|---|---|---|---|
| `README-DISCREPANCY-TSXTRACT` | tsxtract | 33 | 1.80 | 2.90 | 3.56 | +60.9% | OPEN |
| `README-DISCREPANCY-TSFEL` | tsfel | 156 | 9806.60 | 2433.66 | 2495.76 | -75.2% | OPEN |
| `README-DISCREPANCY-TSFRESH` | tsfresh | 777 | 100500.00 | 20081.46 | 20398.95 | -80.0% | OPEN |

**Investigation Requirement:** Competitor methodology, core pinning, and multiprocessing pool overhead must be investigated before Phase B3.

---

*Updated: 2026-10-04 (merged B3 ledger L1–L7/R1 from `benchmarks/LOSS_LEDGER.md` with B0 deep-dives; duplicate removed)*
