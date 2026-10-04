# Benchmarking and Performance State (`benches/STATE.md`)

**Role:** Benchmarking and performance-engineering lead for Tsxtract (Rust core, Python API).  
**Goal:** Build a rigorous, reproducible benchmark suite against every relevant competitor across all realistic circumstances and edge cases, find every place Tsxtract loses, is wrong, or is fragile, FIX those, and re-measure. Every number published must come from a committed artifact.

---

## Hard Rules Checklist
- [x] **Rule 1 — Correctness before speed:** Never time a feature until outputs are verified equal (within tolerance) to a reference, or the definition mismatch is documented.
- [x] **Rule 2 — No cherry-picking:** Report every case, including losses. No number without its conditions (hardware, threads, shape, dtype, versions, commit).
- [x] **Rule 3 — Equal competitor tuning:** Competitors get equal tuning effort and their recommended fast configuration. Document tuning in `benches/adapters/<lib>.md`.
- [x] **Rule 4 — Preserve semantics & contracts:** Do not change feature semantics or the `core33` contract. Parity tests must stay green (`arch_max.md` §8.2).
- [x] **Rule 5 — Traceable fixes:** Every fix: separate commit, references a Loss-Ledger ID, adds a regression benchmark + test, and records before/after in `benches/results/PERF_CHANGELOG.md`.
- [x] **Rule 6 — Stop rule:** Honor `arch_zenith.md` §1.3: stop optimizing a stage within 1.3x of its reference bound or after two <3% attempts.

---

## Phase Checklist

### Phase B0: Environment & Harness
- [x] Directory layout (`harness/`, `adapters/`, `datasets/`, `suites/`, `results/`, `report/`)
- [x] Competitor environment definitions (`benches/requirements-<lib>.txt`, uv venv setup script)
- [x] Adapters:
  - [x] `tsxtract.py`
  - [x] `tsfresh_.py`
  - [x] `tsfel_.py`
  - [x] `catch22_.py` (per-series loop & `multiprocessing.Pool` variant)
  - [x] `numpy_baseline.py` (pure numpy/scipy vectorized 33 features)
  - [x] `numba_baseline.py` (numba hand-rolled 33 features)
  - [x] `antropy_.py`
  - [x] `tsflex_.py`
  - [x] `sktime_.py` (Catch22 / TSFresh transformers)
  - [x] PyPI `tsxtract` (JAX) name collision adapter / doc
  - [x] Tuning documentation `.md` for every adapter in `benches/adapters/`
- [x] Environment capture (`benches/harness/env.py` generating `env.json`)
- [x] Subprocess runner (`benches/harness/runner.py`) with GC disabling, warmup, N>=15 or >=2s budget, stats (min, median, IQR, mean, p95, CV, bootstrap 95% CI)
- [x] Result JSONL schema validator (`benches/harness/schema.py`)
- [x] Orchestration (`Makefile`, `reproduce.sh`, `benches/reproduce.py`)
- [x] **GATE:** `make bench-smoke` (or `python benches/reproduce.py smoke`) runs every adapter on one tiny case end-to-end and writes valid JSONL.
- *Status:* **COMPLETED** (Gate passed: all 10 adapters executed and logged to `smoke.jsonl`)

### Amendments Prior to Phase B1 (All Applied & Verified)
- [x] **A1 — Numba FFT:** Replaced $O(N^2)$ DFT with iterative Radix-2 Cooley-Tukey + Bluestein chirp-z FFT ($O(N \log N)$) in `benches/adapters/numba_baseline.py` (<1.5e-12 error vs NumPy). Documented in `numba_baseline.md`.
- [x] **A2 — Numba Fastmath:** Dual compilation targets (`fastmath=True` for throughput, `fastmath=False` for strict IEEE 754 agreement & robustness). Recorded in result rows.
- [x] **A3 — Guarded Execution:** Added `guarded: bool` to `BenchmarkRecord` schema and runner. Robustness runs `guarded=False` recording exact exception type + message. Reverted silent sktime `ZeroDivisionError -> NaN` in raw mode.
- [x] **A4 — Extended Environment Capture:** Enhanced `benches/harness/env.py` to capture Windows active power scheme (`powercfg /getactivescheme`), AC vs battery status, CPU frequency sampling before/after suites, and hybrid core topology (P/E cores, physical/logical). Added report warnings and parallel efficiency against both physical and logical cores.
- [x] **A5 — README Reproduction Suite:** Implemented `benches/suites/reproduce_readme.py` (1,000 series × 500 points, 16 threads, comparing Tsxtract core33 vs catch22, TSFEL 156-feat, tsfresh 777-feat). Best-of-N and median reported side by side; automatic flagging and logging of >20% deviations to `LOSS_LEDGER.md`.
- [x] **A6 — Competitor Config Pinning:** Pinned tsfresh to 777-feature set (`EfficientFCParameters()`) and TSFEL to 156-feature set (`get_features_by_domain()`) as primary configs. Recorded `n_features` in every record.
- [x] **A7 — Latency Decomposition:** Implemented `benches/suites/latency_overhead.py` decomposing fixed overhead for $n=1, \text{len}=10$ and $n=2, \text{len}=32$ across PyO3 wrapper, contiguity/dtype checks, plan building, output allocation, GIL release/acquire, and math kernel. Logged `HIGH-LATENCY-SMALL-CALL` in `LOSS_LEDGER.md`.
- [x] **A8 — JAX Collision Exclusion:** Excluded `tsxtract_jax` from win/loss counts and loss ledgers in `make_report.py`, isolating it in a dedicated name-collision diagnostic note.
- [x] **A9 — Authoritative Feature Names:** Used `tsxtractor.feature_names()` from built library as single source of truth for the 33 names in `benches/agreement/feature_map.json`. Documented all discrepancies with `README.md` and `arch.md` in `docs/arch_audit.md`.

### Phase B1: Correctness & Agreement
- [x] Feature mapping table `benches/agreement/feature_map.json`: tsxtract_name -> {tsfresh, tsfel, catch22, antropy, numpy_reference} + definition diffs
- [x] Compute all libs on identical data across 25 distributions: 20 synthetic (gaussian, random_walk, sinusoid, AR(1) φ=0.1/0.7/0.9/0.99, trend+seasonality, heavy-tailed, cauchy, spikes, step_changes, piecewise_constant, quantized_8bit, sparse, bimodal, constant, cancellation, tiny_scale, huge_scale) + 5 UCR real (GunPoint, ItalyPowerDemand, Coffee, FordA, SyntheticControl)
- [x] Output `agreement_matrix.json`: max abs/rel error per (feature, distribution, competitor); classify EXACT (<=1e-9 rel), CLOSE (<=1e-5), DIFFERENT-DEFINITION, WRONG. Result: **33/33 EXACT** vs NumPy on 23/25 distributions; 24 EXACT + 9 CLOSE on `cancellation` (expected: naive variance catastrophic cancellation). **0 WRONG.**
- [x] Investigate every WRONG / unexplained mismatch: none found. Fixed numba baseline `ZeroDivisionError` on `tiny_scale` data (std^3 underflow below f64 minimum denormal; fixed via z-score computation).
- [x] Determinism checks: 1/2/4/16 threads **bitwise identical** (max diff 0.00e+00), repeated runs bitwise identical. ✅
- [x] Define and freeze MATCHED feature sets per competitor in `feature_map.json`: numpy=33, numba=23, tsfresh=13, tsfel=13, catch22=0, antropy=0 (not installed)
- [x] **GATE:** Agreement report committed (`benches/agreement/AGREEMENT_REPORT.md`); **no WRONG left open**; matched sets frozen.
- *Status:* **COMPLETED** (Gate ✅ PASS)

### Phase B2: Datasets
- [ ] Synthetic generator `benches/datasets/generators.py` (deterministic seeds, all distributions & odd shapes)
- [ ] Real data downloader & loader `benches/datasets/real.py` (>=12 UCR univariate sets, M4 sample, physiological/vibration)
- [ ] Dataset manifest `benches/datasets/manifest.json` with sha256 checksums and licenses
- [ ] **GATE:** Generators deterministic (seed -> identical sha256); manifest complete.
- *Status:* PENDING

### Phase B3: Throughput, Scaling, Latency
- [ ] Suite throughput (shapes x dists x libs x feature_sets: raw, µs/series-feat, matched-feat, tsfresh extract vs e2e)
- [ ] Suite scaling (threads 1..max + 2x; n_series sweep; length sweep; Amdahl fit & parallel efficiency; crossover analysis)
- [ ] Suite latency (single-series p50/p95/p99/max for lengths 10..1e5, per-call overhead, plan creation, cold vs warm)
- [ ] Suite memory (peak RSS delta subprocess+psutil, allocations, intermediate DF memory)
- [ ] Suite startup (import wall time, first-call time, installed size, cold install time)
- [ ] Suite sliding (windowed extraction vs tsflex, numpy sliding_window_view, pandas rolling)
- [ ] Suite streaming (StreamingExtractor push latency and compute vs naive recompute)
- [ ] Suite concurrency (Python threads GIL release check, joblib, multiprocessing fork/spawn, Dask, reload)
- [ ] Suite portability (f64, f32, int16, int32, uint8, F-order, strided, memmap, pandas, polars, ragged, out= buffer copy analysis)
- [ ] **GATE:** All suites produce valid results or explicit error rows; STATE.md updated.
- *Status:* PENDING

### Phase B4: Robustness / Edge Cases
- [ ] Comprehensive edge cases (len 0..5, constant, all-zero, NaN patterns, infs, denormals, huge/tiny scale, bad dtypes, 3D, non-contiguous strides, concurrency)
- [ ] Robustness matrix recording OK-correct / OK-NaN / silent-wrong / exception / crash / timeout across all libraries
- [ ] Fuzzing and adversarial hypothesis tests; zero crashes/hangs/silent-wrong for Tsxtract
- [ ] **GATE:** `robustness_matrix.md` committed; no Tsxtract crash/hang/silent-wrong open.
- *Status:* PENDING

### Phase B5: Feature Quality / Downstream
- [ ] >=20 UCR classification datasets with standardized CV + models (RF, Ridge/LogReg)
- [ ] Comparison: Tsxtract (core33, extended, full) vs catch22, TSFEL, tsfresh, antropy
- [ ] Metrics: accuracy, macro-F1, extraction time, total time, accuracy-per-second; paired Wilcoxon tests
- [ ] Regression task (M4 sample or UCR regression) with RMSE
- [ ] Document feature gaps where Tsxtract is weaker
- [ ] **GATE:** `downstream_report.md` committed with significance tests.
- *Status:* PENDING

### Phase B6: Analysis -> Loss Ledger
- [ ] Compile `benches/results/LOSS_LEDGER.md` with ranked impact scores
- [ ] Win/loss counts and thin wins (<2x) summary
- [ ] **GATE:** Ledger committed; ranking confirmed before B7.
- *Status:* PENDING

### Phase B7: Improvement Loop
- [ ] Iterative reproduction, flamegraph/profiling, root-cause classification, fix, regression benchmarks
- [ ] PERF_CHANGELOG.md updates with before/after CIs
- [ ] Re-run smoke matrix every 5 items
- [ ] **GATE:** All ledger items with impact >= medium closed or explicitly justified.
- *Status:* PENDING

### Phase B8: Final Run, Report, Website Feed
- [ ] Full re-run on clean tree at tagged commit vs pre-improvement baseline
- [ ] `make_report.py` producing `REPORT.md`, charts (SVG), `results.json`
- [ ] `CLAIMS.md` linking every claim to artifact + commit hash
- [ ] Update README and landing page from `results.json` only
- [ ] **GATE:** `make bench-all && make report` reproduces from scratch.
- *Status:* PENDING

---

## Current Execution Log
- **2026-10-04:** Initialized `benches/STATE.md`. Phase B0 started and Gate Passed (all 10 adapters verified on test batch).
- **2026-10-04:** Completed Amendments Prior to Phase B1 (A1–A9):
  - A1: Replaced $O(N^2)$ DFT in `numba_baseline.py` with iterative $O(N \log N)$ Radix-2 + Bluestein FFT (<1.5e-12 error vs NumPy). Documented in `numba_baseline.md`.
  - A2: Added `fastmath=False` strict IEEE 754 variant alongside `fastmath=True` in `numba_baseline.py`; recorded in result rows.
  - A3: Added `guarded: bool` to `BenchmarkRecord` schema and runner; reverted silent sktime `ZeroDivisionError -> NaN` when `guarded=False`; recorded exact exception type + message on error.
  - A4: Enhanced `env.py` with Windows power plan (`powercfg /getactivescheme`), AC vs battery status, CPU frequency before/after suite, and hybrid core topology (P/E cores, physical/logical). Added report warnings and dual-efficiency reporting.
  - A5: Built `benches/suites/reproduce_readme.py` comparing best-of-N and median on 1,000 × 500, 16 threads; flagged >20% deviations and logged to `LOSS_LEDGER.md`.
  - A6: Pinned primary competitor configs (tsfresh 777-feature set, TSFEL 156-feature set); recorded `n_features` in every record.
  - A7: Implemented `benches/suites/latency_overhead.py` decomposing fixed overhead floor for $n=1, \text{len}=10$ and $n=2, \text{len}=32$; logged `HIGH-LATENCY-SMALL-CALL` in `LOSS_LEDGER.md`.
  - A8: Excluded `tsxtract_jax` from win/loss counts and ledgers in `make_report.py`, isolating in name-collision diagnostic note.
  - A9: Frozen 33 names from `tsxtractor.feature_names()` as single source of truth in `benches/agreement/feature_map.json`; audited and documented README/arch discrepancies in `docs/arch_audit.md`.
- **2026-10-04:** Phase B1 Correctness & Agreement — **GATE ✅ PASS**:
  - Expanded agreement suite to 25 distributions (20 synthetic + 5 UCR real datasets).
  - All 33 features **EXACT** vs NumPy reference on 23/25 distributions; 9 features **CLOSE** on `cancellation` (1e9+noise) due to expected catastrophic cancellation in floating-point variance — documented, not a bug.
  - Fixed `ZeroDivisionError` in numba baseline `_compute_row` for `tiny_scale` (1e-150) data: `std³` underflows below f64 minimum denormal (~5e-324) → division by zero. Fix: compute skewness/kurtosis via z-scores (`z = (x-mean)/std`) instead of `m3/(n·std³)`.
  - Determinism: **bitwise identical** across 1/2/4/16 threads (max diff = 0.00e+00).
  - Frozen matched feature sets: numpy=33, numba=23, tsfresh=13, tsfel=13, catch22=0, antropy=0.
  - Artifacts: `benches/agreement/AGREEMENT_REPORT.md`, `agreement_matrix.json`, `feature_map.json`.

