
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
