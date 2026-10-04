# Benchmarking and Performance State (`benchmarks/STATE.md`)

**Role:** Benchmarking and performance-engineering lead for Tsxtract (Rust core, Python API).  
**Goal:** Build a rigorous, reproducible benchmark suite against every relevant competitor across all realistic circumstances and edge cases, find every place Tsxtract loses, is wrong, or is fragile, FIX those, and re-measure. Every number published must come from a committed artifact.

---

## Hard Rules Checklist
- [x] **Rule 1 — Correctness before speed:** Never time a feature until outputs are verified equal (within tolerance) to a reference, or the definition mismatch is documented.
- [x] **Rule 2 — No cherry-picking:** Report every case, including losses. No number without its conditions (hardware, threads, shape, dtype, versions, commit).
- [x] **Rule 3 — Equal competitor tuning:** Competitors get equal tuning effort and their recommended fast configuration. Document tuning in `benchmarks/adapters/<lib>.md`.
- [x] **Rule 4 — Preserve semantics & contracts:** Do not change feature semantics or the `core33` contract. Parity tests must stay green (`arch_max.md` §8.2).
- [x] **Rule 5 — Traceable fixes:** Every fix: separate commit, references a Loss-Ledger ID, adds a regression benchmark + test, and records before/after in `benchmarks/results/PERF_CHANGELOG.md`.
- [x] **Rule 6 — Stop rule:** Honor `arch_zenith.md` §1.3: stop optimizing a stage within 1.3x of its reference bound or after two <3% attempts.

---

## Phase Checklist

### Phase B0: Environment & Harness
- [x] Directory layout (`harness/`, `adapters/`, `datasets/`, `suites/`, `results/`, `report/`)
- [x] Competitor environment definitions (`benchmarks/requirements-<lib>.txt`, uv venv setup script)
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
  - [x] Tuning documentation `.md` for every adapter in `benchmarks/adapters/`
- [x] Environment capture (`benchmarks/harness/env.py` generating `env.json`)
- [x] Subprocess runner (`benchmarks/harness/runner.py`) with GC disabling, warmup, N>=15 or >=2s budget, stats (min, median, IQR, mean, p95, CV, bootstrap 95% CI)
- [x] Result JSONL schema validator (`benchmarks/harness/schema.py`)
- [x] Orchestration (`Makefile`, `reproduce.sh`, `benchmarks/reproduce.py`)
- [x] **GATE:** `make bench-smoke` (or `python benchmarks/reproduce.py smoke`) runs every adapter on one tiny case end-to-end and writes valid JSONL.
- *Status:* **COMPLETED** (Gate passed: all 10 adapters executed and logged to `smoke.jsonl`)

### Amendments Prior to Phase B1 (All Applied & Verified)
- [x] **A1 — Numba FFT:** Replaced $O(N^2)$ DFT with iterative Radix-2 Cooley-Tukey + Bluestein chirp-z FFT ($O(N \log N)$) in `benchmarks/adapters/numba_baseline.py` (<1.5e-12 error vs NumPy). Documented in `numba_baseline.md`.
- [x] **A2 — Numba Fastmath:** Dual compilation targets (`fastmath=True` for throughput, `fastmath=False` for strict IEEE 754 agreement & robustness). Recorded in result rows.
- [x] **A3 — Guarded Execution:** Added `guarded: bool` to `BenchmarkRecord` schema and runner. Robustness runs `guarded=False` recording exact exception type + message. Reverted silent sktime `ZeroDivisionError -> NaN` in raw mode.
- [x] **A4 — Extended Environment Capture:** Enhanced `benchmarks/harness/env.py` to capture Windows active power scheme (`powercfg /getactivescheme`), AC vs battery status, CPU frequency sampling before/after suites, and hybrid core topology (P/E cores, physical/logical). Added report warnings and parallel efficiency against both physical and logical cores.
- [x] **A5 — README Reproduction Suite:** Implemented `benchmarks/suites/reproduce_readme.py` (1,000 series × 500 points, 16 threads, comparing Tsxtract core33 vs catch22, TSFEL 156-feat, tsfresh 777-feat). Best-of-N and median reported side by side; automatic flagging and logging of >20% deviations to `LOSS_LEDGER.md`.
- [x] **A6 — Competitor Config Pinning:** Pinned tsfresh to 777-feature set (`EfficientFCParameters()`) and TSFEL to 156-feature set (`get_features_by_domain()`) as primary configs. Recorded `n_features` in every record.
- [x] **A7 — Latency Decomposition:** Implemented `benchmarks/suites/latency_overhead.py` decomposing fixed overhead for $n=1, \text{len}=10$ and $n=2, \text{len}=32$ across PyO3 wrapper, contiguity/dtype checks, plan building, output allocation, GIL release/acquire, and math kernel. Logged `HIGH-LATENCY-SMALL-CALL` in `LOSS_LEDGER.md`.
- [x] **A8 — JAX Collision Exclusion:** Excluded `tsxtract_jax` from win/loss counts and loss ledgers in `make_report.py`, isolating it in a dedicated name-collision diagnostic note.
- [x] **A9 — Authoritative Feature Names:** Used `tsxtract.feature_names()` from built library as single source of truth for the 33 names in `benchmarks/agreement/feature_map.json`. Documented all discrepancies with `README.md` and `arch.md` in `docs/arch_audit.md`.

### Phase B1: Correctness & Agreement
- [x] Feature mapping table `benchmarks/agreement/feature_map.json`: tsxtract_name -> {tsfresh, tsfel, catch22, antropy, numpy_reference} + definition diffs
- [x] Compute all libs on identical data across 25 distributions: 20 synthetic (gaussian, random_walk, sinusoid, AR(1) φ=0.1/0.7/0.9/0.99, trend+seasonality, heavy-tailed, cauchy, spikes, step_changes, piecewise_constant, quantized_8bit, sparse, bimodal, constant, cancellation, tiny_scale, huge_scale) + 5 UCR real (GunPoint, ItalyPowerDemand, Coffee, FordA, SyntheticControl)
- [x] Output `agreement_matrix.json`: max abs/rel error per (feature, distribution, competitor); classify EXACT (<=1e-9 rel), CLOSE (<=1e-5), DIFFERENT-DEFINITION, WRONG. Result: **33/33 EXACT** vs NumPy on 23/25 distributions; 24 EXACT + 9 CLOSE on `cancellation` (expected: naive variance catastrophic cancellation). **0 WRONG.**
- [x] Investigate every WRONG / unexplained mismatch: none found. Fixed numba baseline `ZeroDivisionError` on `tiny_scale` data (std^3 underflow below f64 minimum denormal; fixed via z-score computation).
- [x] Determinism checks: 1/2/4/16 threads **bitwise identical** (max diff 0.00e+00), repeated runs bitwise identical. ✅
- [x] Define and freeze MATCHED feature sets per competitor in `feature_map.json`: numpy=33, numba=23, tsfresh=13, tsfel=13, catch22=0, antropy=0 (not installed)
- [x] **GATE:** Agreement report committed (`benchmarks/agreement/AGREEMENT_REPORT.md`); **no WRONG left open**; matched sets frozen.
- *Status:* **COMPLETED** (Gate ✅ PASS)

### Phase B2: Datasets
- [x] Synthetic generator `benchmarks/datasets/generators.py` — 22 distributions, `ALL_DISTRIBUTIONS` constant, `BENCHMARK_SHAPES` (15 shapes), `ODD_LENGTHS` (12 lengths), `generate_benchmark_matrix()`, `verify_determinism()`, `array_sha256()`.
- [x] Real data downloader & loader `benchmarks/datasets/real.py` — 13 UCR univariate sets (GunPoint through CBF, lengths 24–1024), M4 Daily/Hourly sample, SHA-256 validation, offline fallback generation.
- [x] Dataset manifest `benchmarks/datasets/manifest.json` — 15 real datasets with license/domain, 22 synthetic distributions with SHA-256 checksums (100×500, seed=42), benchmark shapes, odd lengths.
- [x] **GATE:** All 22 distributions + all 12 odd lengths produce identical SHA-256 across repeated generation. Manifest complete.
- *Status:* **COMPLETED** (Gate ✅ PASS)

### Phase B3: Throughput, Scaling, Latency
- [x] Suite throughput (shapes x dists x libs x feature_sets: raw, µs/series-feat, matched-feat, tsfresh extract vs e2e) — **135/135 rows OK** (3 libs × 9 shapes × 5 dists: tsxtract, numpy_baseline, numba_baseline_fast)
- [x] Suite scaling (threads 1..max + 2x; n_series sweep; length sweep; Amdahl fit & parallel efficiency; crossover analysis) — 18 rows: thread 1/2/4/8/16/32, series 1→100k, length 10→50k
- [x] Suite latency (single-series p50/p95/p99/max for lengths 10..1e5, per-call overhead, plan creation, cold vs warm) — 30 rows incl. crossover (tsx wins 7.1×–10.7× at ALL lengths) + overhead decomposition
- [ ] Suite memory (peak RSS delta subprocess+psutil, allocations, intermediate DF memory)
- [ ] Suite startup (import wall time, first-call time, installed size, cold install time)
- [ ] Suite sliding (windowed extraction vs tsflex, numpy sliding_window_view, pandas rolling)
- [ ] Suite streaming (StreamingExtractor push latency and compute vs naive recompute)
- [ ] Suite concurrency (Python threads GIL release check, joblib, multiprocessing fork/spawn, Dask, reload)
- [ ] Suite portability (f64, f32, int16, int32, uint8, F-order, strided, memmap, pandas, polars, ragged, out= buffer copy analysis)
- [ ] **GATE:** All suites produce valid results or explicit error rows; STATE.md updated.
- *Status:* **IN PROGRESS** — throughput/scaling/latency **COMPLETE** (report: `benchmarks/results/B3_REPORT.md`, findings in `benchmarks/LOSS_LEDGER.md` L1/L3/L7); **step 2 competitor matrix COMPLETE** (see below); memory, startup, sliding, streaming, concurrency, portability pending

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
- [ ] Compile `benchmarks/results/LOSS_LEDGER.md` with ranked impact scores
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
- **2026-10-04:** Initialized `benchmarks/STATE.md`. Phase B0 started and Gate Passed (all 10 adapters verified on test batch).
- **2026-10-04:** Completed Amendments Prior to Phase B1 (A1–A9):
  - A1: Replaced $O(N^2)$ DFT in `numba_baseline.py` with iterative $O(N \log N)$ Radix-2 + Bluestein FFT (<1.5e-12 error vs NumPy). Documented in `numba_baseline.md`.
  - A2: Added `fastmath=False` strict IEEE 754 variant alongside `fastmath=True` in `numba_baseline.py`; recorded in result rows.
  - A3: Added `guarded: bool` to `BenchmarkRecord` schema and runner; reverted silent sktime `ZeroDivisionError -> NaN` when `guarded=False`; recorded exact exception type + message on error.
  - A4: Enhanced `env.py` with Windows power plan (`powercfg /getactivescheme`), AC vs battery status, CPU frequency before/after suite, and hybrid core topology (P/E cores, physical/logical). Added report warnings and dual-efficiency reporting.
  - A5: Built `benchmarks/suites/reproduce_readme.py` comparing best-of-N and median on 1,000 × 500, 16 threads; flagged >20% deviations and logged to `LOSS_LEDGER.md`.
  - A6: Pinned primary competitor configs (tsfresh 777-feature set, TSFEL 156-feature set); recorded `n_features` in every record.
  - A7: Implemented `benchmarks/suites/latency_overhead.py` decomposing fixed overhead floor for $n=1, \text{len}=10$ and $n=2, \text{len}=32$; logged `HIGH-LATENCY-SMALL-CALL` in `LOSS_LEDGER.md`.
  - A8: Excluded `tsxtract_jax` from win/loss counts and ledgers in `make_report.py`, isolating in name-collision diagnostic note.
  - A9: Frozen 33 names from `tsxtract.feature_names()` as single source of truth in `benchmarks/agreement/feature_map.json`; audited and documented README/arch discrepancies in `docs/arch_audit.md`.
- **2026-10-04:** Phase B1 Correctness & Agreement — **GATE ✅ PASS**:
  - Expanded agreement suite to 25 distributions (20 synthetic + 5 UCR real datasets).
  - All 33 features **EXACT** vs NumPy reference on 23/25 distributions; 9 features **CLOSE** on `cancellation` (1e9+noise) due to expected catastrophic cancellation in floating-point variance — documented, not a bug.
  - Fixed `ZeroDivisionError` in numba baseline `_compute_row` for `tiny_scale` (1e-150) data: `std³` underflows below f64 minimum denormal (~5e-324) → division by zero. Fix: compute skewness/kurtosis via z-scores (`z = (x-mean)/std`) instead of `m3/(n·std³)`.
  - Determinism: **bitwise identical** across 1/2/4/16 threads (max diff = 0.00e+00).
  - Frozen matched feature sets: numpy=33, numba=23, tsfresh=13, tsfel=13, catch22=0, antropy=0.
  - Artifacts: `benchmarks/agreement/AGREEMENT_REPORT.md`, `agreement_matrix.json`, `feature_map.json`.
- **2026-10-04:** Phase B2 Datasets — **GATE ✅ PASS**:
  - Enhanced `generators.py`: 22 distributions, `ALL_DISTRIBUTIONS`, `BENCHMARK_SHAPES` (15 shapes), `ODD_LENGTHS` (12), `generate_benchmark_matrix()`, `verify_determinism()`, `array_sha256()`.
  - Enhanced `real.py`: 13 UCR datasets (lengths 24–1024), M4 Daily/Hourly, SHA-256 validation, offline fallback.
  - Updated `manifest.json`: 15 real datasets with license/domain, 22 synthetic distributions with SHA-256 checksums.
  - Verified: all 22 distributions × 12 odd lengths produce identical SHA-256 across repeated generation.
- **2026-10-04:** Phase B3 (part 1) — throughput, scaling, latency **COMPLETE**:
  - Throughput: 135/135 rows OK (9 shapes × 5 dists × tsxtract/numpy_baseline/numba_baseline_fast, 16 threads). Win/loss (median, paired per shape×dist): **vs numpy_baseline 45–0** (ratio 1.99×–130×, median 17.1×; single thin win 1.99× at 1×100); **vs numba_baseline_fast 28–17** — losses at 1×100, 10×500, 100×100 (all 5/5 dists each) and 100×500 (2/5) → **L1** (numba up to ~24× faster at 1×100, no FFI overhead; crossover n≈100–1000).
  - Scaling: threads 1→32 at 1000×500 (speedup 1.81× @2T, 3.21× @4T, plateau 4.29× @8T, η=25% @16T, 3.26× @32T oversubscription → **L3**, hybrid P/E hardware); series sweep 1→100k (µs/series 520→2.13, asymptote ~2.1 µs/series); length sweep 10→50k (µs/series-feature 0.028→6.91, superlinear beyond len≈5k from FFT/autocorr).
  - Latency: single-series p50 wins vs NumPy at ALL lengths 10→100k (7.1×–10.7×, no crossover) — BUT tail loss at len=10 (p99 15.4 ms vs 3.2 ms, max 29.1 ms; clean tail at len≥50) → **new L7**. Overhead decomposition: ~150 µs fixed floor (**L2**). Crossover table: tsx wins 8/8 lengths.
  - Artifacts: `benchmarks/results/B3_REPORT.md` (env header from `2026-10-04_Aamod/env.json`, §1.3 win/loss summary), `benchmarks/results/LOSS_LEDGER.md` (renumbered L1–L7, duplicate L2 fixed).

### 2026-10-04: B3 GATE AUDIT (pre-continuation audit ordered by owner)
- **A1–A9 verified in code/artifacts:**
  - A1 ✅ `numba_baseline.py` uses iterative Radix-2 + Bluestein O(N log N) FFT (no O(N²) DFT). A2 ✅ dual fastmath variants, recorded per row (`extra.fastmath_variant`). A3 ✅ `guarded` on schema + runner; sktime raw mode raises instead of silent NaN. A4 ✅ `env.json` captures power scheme/AC/P-E-topology/frequencies. A5 ✅ `suites/reproduce_readme.py` exists (see F1 below). A6 ✅ tsfresh=EfficientFCParameters(777), TSFEL=get_features_by_domain()(156), targets match README table. A7 ✅ `suites/latency_overhead.py` + ledger `HIGH-LATENCY-SMALL-CALL`. A8 ✅ `benchmarks/report/make_report.py` excludes `tsxtract_jax` from win/loss (dedicated collision note). A9 ✅ `tsxtract.feature_names()` source of truth in `feature_map.json`; discrepancies in `docs/arch_audit.md`.
  - Note: `tsxtract` and `tsxtract` wheels both installed; verified identical 0.5.0 build (bitwise-equal output, same feature_names). B3_REPORT header's "tsxtract 0.3.0" is a stale version string (pip metadata) — library under test is 0.5.0.
- **F1 reproduce_readme — WAS INCOMPLETE, COMPLETED THIS AUDIT.** Prior run had only tsxtract (2 rows) + catch22 (1 error + 1 OK); tsfel/tsfresh rows missing. Full re-run (`benchmarks/results/2026-10-04_gate_audit/`):
  - tsxtract core33: README 1.80 ms → measured best 2.90 ms / median 3.56 ms = **+60.9% deviation → discrepancy CONFIRMED** (README headline 1.25 ms/800,256 series-s disagrees with README table 1.80 ms/555k, and neither reproduces on this harness).
  - catch22: 1045.8 → 1034.6 ms = −1.1% ✅ reproduces.
  - tsfel: 9806.6 → 2433.7 ms = **−75.2%** (measured much faster; README competitor numbers stale).
  - tsfresh: 100500 → 20081.5 ms = **−80.0%** (same).
  - Consequence: README comparison ratios (820×/5,443×/55,779×) are not supported by this harness; measured best-of ratios ≈ 357×/839×/6,925×. Ledger entries auto-appended (README-DISCREPANCY-*). No new claims until §14.1 evidence chain is fixed.
- **B1 agreement + matched sets:** artifacts present (`agreement_matrix.json`, `AGREEMENT_REPORT.md`, frozen `feature_map.json`; matched sets numpy=33, numba=23, tsfresh=13, tsfel=13, catch22=0, antropy=0). **Discrepancy found:** matrix contains **14 numba_ref WRONG cells** (std/var/skewness/kurtosis/cid_ce/autocorr×4/trend_r2 on `cancellation`; skew/kurt on `tiny_scale`/`huge_scale`) — STATE's "0 WRONG" claim was true only for Tsxtract vs NumPy. These are baseline numerical defects (naive one-pass variance under catastrophic cancellation), not Tsxtract losses; they are exactly why numba's frozen matched set is 23/33. Re-verification + Tsxtract-side status: see L1 root-cause artifact. B1 gate accepted **with this documented caveat** (Tsxtract: 0 WRONG across 25 dists).
- **B2 datasets:** manifest complete (15 real datasets w/ license+sha256, 22 synthetic dists w/ sha256, 15 shapes, 12 odd lengths); determinism previously verified. Gate ✅.
- **B3 provisional marking:** all 183 existing B3 rows (throughput 135, scaling 18, latency 30) marked `"provisional": true` with reason `pending gate-audit confirmation of B1 agreement re-verification` in `throughput.jsonl`/`scaling.jsonl`/`latency.jsonl`. Flag to be lifted at the B8 clean re-run (or by owner instruction now that the audit is green with the numba caveat documented).
- **Step 2 (competitor matrix):** new `benchmarks/suites/throughput_competitors.py` (catch22, tsfel 156, tsfresh 777 e2e + extract-only, tsfresh/tsfel matched-subset runs, antropy, tsflex, sktime; same 9-shape matrix; per-case wall-clock timeouts recorded as explicit `timeout` rows; §11.8 schema with `variant` + `env_ref`). Runner upgraded: `timeout_s` param, `heavy_tailed` alias fix, `variant`/`adapter_kwargs` passthrough (extract-only builds long_df outside the timed region). Adapters amended: tsfresh `matched` (13 frozen features), tsfel `matched` (13 frozen features).

### 2026-10-04: B3 Step 2 — Competitor Throughput Matrix COMPLETE
- Full matrix run: **495/495 rows** in `benchmarks/results/throughput_competitors.jsonl` — 477 `ok` + 18 explicit `timeout` rows (all at 10,000×500: tsfresh e2e & extract-only 5/5, tsflex 5/5, antropy 3/5). **0 schema violations**, 0 silent skips. Suite gained `--resume` (skips case_ids already in the JSONL) after an interrupted run at 375/495.
- Report: `benchmarks/results/COMPETITOR_REPORT.md` (generated by `benchmarks/suites/make_competitor_report.py`) — three views per §11.6: raw median/best ms, µs/series-feature, matched-13-feature; per-dist detail for 1,000×500 and 10,000×500; all 18 timeout rows listed explicitly.
- Headline (median, best dist, 16 threads, i7-13620H):
  - **vs catch22:** Tsxtract wins 8/9 shapes (69.6×–991×); at 1×100 catch22 leads (Tsxtract ratio 0.4× — per-series loop has no FFI/plan overhead at n=1); 1×10,000 also close (34.5×).
  - **vs TSFEL (156):** 361.8×–5,594× raw; matched-13 291.6×–6,152×.
  - **vs tsfresh (777):** e2e 2,846×–12,942×, extract-only 2,790×–13,255×; matched-13 1,776×–18,652×; explicit timeout at 10,000×500 for both views.
  - **vs antropy:** 1.2× (1×100, thin) up to 1,122×; antropy times out on 3/5 dists at 10,000×500.
  - **vs tsflex:** 5.2×–1,461×; timeout 5/5 at 10,000×500 (8/9 shapes reported).
  - **vs sktime Catch22:** 22.4×–782× (slowest-but-consistent, completes all shapes).
- Report generator bug fixed during review: `load_rows()` mapped only by `lib`, so `tsfresh_matched`/`tsfel_matched` rows collided with defaults and `tsfresh_e2e`/`sktime_catch22` showed "not run" despite existing rows. Now keyed on (lib, feature_set, extra.variant); Tsxtract self-ratio pinned to 1.0×.

