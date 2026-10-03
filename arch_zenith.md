# Tsxtract — Zenith Architecture (`arch_zenith.md`)

**Extends:** `arch_max.md` (Phases 0–7). Start this file only after `arch_max.md` Phase 2 gate is green.
**Purpose:** define the practical ceiling for Tsxtract on three axes — **compute**, **runtime**, **output** — and a rule for when to stop.
**All speed numbers below are estimates from first principles, not measurements.** Phase Z0 replaces them with real data. Never implement a Z-item before its decision gate says the stage is worth it.

---

## 0. Rules

1. Same invariants as `arch_max.md` §2 (I1–I7). Core33 order and NaN contract stay frozen.
2. **Measure → decide → implement.** Each Z-item has a decision gate (a profile condition). If the gate is false, skip the item.
3. Every item ships behind a Criterion benchmark and a parity test (tolerances in `arch_max.md` §8.2).
4. Items that change numerics beyond §8.2 tolerances are **opt-in modes**, never defaults.

---

## 1. Ceiling Model & Stop Rule

### 1.1 Why the ceiling exists
- One series (n=500, f64) is 4 KB → lives in L1. Per-series work is **compute-bound**, not memory-bound.
- Batch level: 100k × 500 f64 = 400 MB. At ~40–60 GB/s DRAM bandwidth the floor is ~7–10 ms regardless of compute. Rule: **touch each series in DRAM exactly once** (fuse everything, prefetch next series).
- Parallel floor: at ~1 ms total runtime, pool wake/join overhead is a visible fraction. Measure parallel efficiency `η = T1 / (N · T_N)`.

### 1.2 Estimated per-series floor, core33, n=500, one core (AVX2-class CPU)

| Stage | `arch_max` budget | Zenith estimate | How |
|---|---|---|---|
| Fused passes (moments, crossings, peaks, abs-diff) | 0.3–0.6 µs | 0.15–0.3 µs | SIMD, one L1 sweep each |
| Quantiles + IQR + MAD | 2–5 µs | **0.6–1.2 µs** | Z1 histogram multi-select |
| FFT + 6 spectral stats | 2–4 µs | **1–2 µs** | Z3 specialization (500 = 2²·5³) |
| ACF lags (5) | 0.2–0.4 µs | 0.15–0.3 µs | SIMD dots |
| Permutation entropy | 0.3–0.8 µs | 0.2–0.4 µs | branchless LUT |
| Misc / write-out | — | 0.2 µs | |
| **Total** | ~6–11 µs | **~2.5–5 µs** | |

Implied batch ceiling (1,000 × 500, 16 cores, η≈0.85): ~0.18–0.37 ms ⇒ **≈2.7–5.5 M series/s** vs 800k today (≈3.4–6.9×). Treat as a hypothesis to falsify in Phase Z0.

### 1.3 Stop rule ("zenith reached")
Stop optimizing a stage when **either**:
- the stage is within **1.3×** of its reference bound (see §5.2: FFTW/pyFFTW for FFT, vectorized-sort libs for sorting, `llvm-mca` throughput bound for SIMD kernels), **or**
- the last two optimization attempts on it each gained **<3%** end-to-end.

Stop the *whole* speed effort when core33 reaches ≥85% of the §1.2 estimate **and** parallel efficiency η ≥ 0.85 at (1k × 500). Past that, additional speed has almost no marketing value (the library is already ~800× ahead of catch22); spend the effort on **output** (§4).

---

## 2. Compute Ceiling

### Z1 — Histogram multi-select (replace sorting for quantile features)  **[Priority 1]**
**Decision gate:** SORT stage >25% of per-series time in Phase Z0 profile.

Core33 needs q05, q25, q50, q75, q95 (+ IQR, MAD) — 5–7 order statistics, **not** a full sort. One value-range histogram locates all ranks at once; exactness is preserved.

Algorithm (exact, O(n)):
1. `min`, `max` already known from Pass 1 (free). If `min == max` → every rank = `min`.
2. Count pass: `b = ((x - min) * scale) as usize` with `scale = (B-1) / (max-min)`, clamp to `B-1`; `counts[b] += 1`. `B = 512` (tune 256–2048).
3. Prefix-sum `counts`; for each requested rank `r` (and `r+1` for linear interpolation) find bucket via prefix sums; mark target buckets in a bitset.
4. Gather pass: copy elements whose bucket is marked into small scratch groups (typically ~n/B ≈ 1–4 elements per target bucket for smooth data).
5. `select_nth_unstable` inside each gathered group at the local rank.
6. **Heavy-cluster guard:** if a target bucket holds > n/4 elements (ties, spikes, heavy tails), recurse with that bucket's own `[min,max]`; if all equal, return directly. Worst case falls back to sorting the gathered subset — still correct.
7. MAD: second `multi_select` on `|x − median|` using `[0, max|d|]`.

```rust
pub struct SelScratch { counts: Vec<u32>, gather: Vec<f64>, target: Vec<u64> /* bitset */ }

/// ranks must be sorted ascending, each < x.len(). Writes x_(rank) into out[i].
pub fn multi_select(x: &[f64], min: f64, max: f64, ranks: &[usize],
                    sc: &mut SelScratch, out: &mut [f64]) { /* steps above */ }
```
Registry impact: split intermediates into `SELECT` (cheap, quantile-only features) and `SORTED` (full order; only for features that need it: unique/reoccurring counts, change_quantiles). `minimal`/`core33` use `SELECT` only.

**Gate:** bit-for-bit equal to `numpy.quantile(..., method="linear")` within §8.2 on random, tied, heavy-tailed, near-constant, and bimodal data; ≥2× faster than best sort strategy at n∈{128,500,2000}, or documented why not.

### Z2 — Lane-batched (SoA) execution mode  **[Priority 3]**
**Decision gate:** after Z1 + Z3, fused-pass + ACF + perm-entropy stages together still >30% of time.

Vectorize **across series** instead of within a series: process `L` series at once in time-major layout `soa[t*L + lane]`. Every elementwise feature (moments, crossings via mask-and-count, peaks, ACF lag dots) then has **no horizontal reductions and no tail loops**.
- `L` = 4 for AVX2 f64 (16 KB block for n=500 fits L1); choose `L·n·8 B ≤ ~16 KB`, else tile the time axis.
- AoS→SoA transposition: register-level 4×4 blocks while loading; cost ≈ one pass.
- Only for **equal-length batches**; ragged/long series use the standard path. Selected automatically by the planner.
- Honest expectation: accelerates only the elementwise stages, so alone it is a ~10–20% end-to-end gain; its real value is as the layout enabling Z3-lane FFT.

### Z3 — FFT specialization  **[Priority 3, only if FFT >35% of profile after Z1]**
Tiers, stop at the first that reaches the 1.3× reference bound (§5.2):
1. **Verify `realfft`/`rustfft` plans are cached and scratch-reused** (Phase 1 of `arch_max`); confirm AVX path is actually selected at runtime.
2. **Length-specialized plans** for common lengths (64, 100, 128, 200, 250, 256, 500, 512, 1000, 1024, 2048): codegen mixed-radix (2/4/5) straight-line kernels via `build.rs`; fall back to `rustfft` otherwise.
3. **Inter-series lane FFT** (needs Z2 layout): run the same butterfly network on 4 series in SIMD lanes with shared twiddles. Highest effort and uncertain gain over an already-vectorized library — build only after a prototype shows ≥1.3× on the FFT stage.
Also: avoid computing the full spectrum when the profile needs only energy (Parseval from time domain).

### Z4 — `precision="f32"` fast mode (opt-in)  **[Priority 2]**
- 2× SIMD width, half the bandwidth, faster f32 FFT. Accumulate sensitive reductions in f64 (or compensated f32) where cheap; document tolerance (≈1e-5 relative on moments).
- Same registry, generic over `T: Float`; output remains f64 unless `out_dtype="float32"` is requested.
- Never default. Expose as `extract_features(X, precision="f32")` and benchmark separately.

### Z5 — Hand-fused `core33` fast path  **[Priority 3]**
Generate (via `build.rs` from `registry.rs`, so there is still one source of truth) a straight-line `core33_fused(x, scratch, out)` with no plan dispatch and all intermediates inlined. Expected gain small (3–8%) because dispatch is already ~ns vs µs of work; do it last, and only if the generated code stays derivable from the registry.

---

## 3. Runtime Ceiling

### Z6 — Persistent spin-then-park thread pool  **[Priority 1, gated on measurement]**
**Decision gate:** measured parallel efficiency η < 0.85 at (1k × 500, 16 threads), or flamegraph shows significant time in rayon wake/steal/join.

At ~1 ms total runtime each of 16 workers does ~70–80 µs of work; sleeping-worker wake-up (tens of µs) is a double-digit-percent tax.

Design: persistent worker threads, atomic `epoch` + `next_chunk` counter; workers **spin ~20–50 µs** after a job, then park; main thread publishes `(ptr_in, ptr_out, n, chunk)` and participates. Dynamic chunk self-scheduling (`fetch_add(chunk)`), chunk = 32–64 series, boundaries aligned so adjacent workers never share a cache line of output.
```rust
struct Job { x: *const f64, out: *mut f64, n: usize, len: usize, plan: *const FeaturePlan }
// worker loop: loop { wait_epoch(); while let Some(r) = next_range() { run_rows(r) } ; signal_done(); }
```
Keep rayon as the fallback (`TSXTRACT_POOL=rayon`). **Gate:** η ≥ 0.85 at (1k×500) and no regression at 100k×500; panics in workers must still never cross FFI (catch + propagate as `TsxError`).

### Z7 — First-touch & alignment
- Allocate output **uninitialized** (`PyArray2::uninit` / `np.empty`) so the worker that writes a row page-faults it (parallel page faults; correct NUMA first-touch on multi-socket boxes) — then verify every element is written (debug assertion, fuzz test).
- Scratch buffers 64-byte aligned.

### Z8 — One DRAM touch per series
Software prefetch the next series' first cache lines (`_mm_prefetch` / `core::intrinsics::prefetch_read_data` equivalent) while the current series computes; process series fully (all features) before moving on. Gate: `perf stat` shows LLC-miss rate drop at 100k×500.

### Z9 — Wisdom auto-tuner (FFTW-style)  **[Priority 2]**
`tsx.tune(shapes=[(1000,500),(100000,500)], budget_s=20)` microbenchmarks the variants that depend on hardware and length bucket, then caches the winners in `~/.cache/tsxtract/wisdom.json`, keyed by CPU model + feature flags + library version:
- select vs sort vs nested-select (Z1 bucket count `B`)
- chunk size, serial threshold, pool type (rayon vs Z6), thread count
- AVX2 vs AVX-512 variant, FFT mode
Default: ship a static wisdom table generated in CI so untuned users still get good defaults. `TSXTRACT_WISDOM=off` disables. Wisdom never changes numerical results beyond §8.2 tolerances.

### Z10 — Length-bucketed ragged scheduling
For ragged input, sort series *indices* by length into buckets, run each bucket with one cached FFT plan/lane layout, then scatter results back to original order. Cuts plan switching and lets Z2/Z3 apply to ragged data.

---

## 4. Output Ceiling (where the remaining differentiation is)

### Z11 — Views × features (multiplicative breadth)  **[Priority 1 for product value]**
Compute the same feature set on cheap derived **views** of each series and concatenate columns:

`views = ("raw", "diff", "diff2", "detrend", "znorm", "abs", "logret", "rank")`

- Output columns: `|views| × |features|` (e.g., 8 × 150 = 1,200) at a cost far below recomputing from scratch per library call.
- **Invariance pruning** in the registry avoids junk columns: each `FeatureDef` declares `invariances: {shift, scale, monotone}`. The planner drops redundant combos (e.g., autocorrelation is shift+scale invariant → skip `znorm`; rank-view moments are deterministic functions of `n` → skip).
- Column naming: `view__feature` (e.g., `diff__skewness`); aliases for tsfresh-style names.
- Views are computed into scratch, not new Python arrays; each view reuses the pipeline.
**Gate:** every pruned combo has a test proving it is truly redundant (equal to the unpruned value within tolerance); `views=("raw",)` equals the existing output exactly.

### Z12 — Multichannel + cross-channel features
Input `(n_samples, n_channels, length)`; output per-channel features concatenated, plus cross-channel features:
- covariance / correlation matrix summary (eigenvalue spread, mean |r|), cross-correlation at best lag (via per-channel spectra already computed → one extra IFFT per pair, or lag-limited direct dots), magnitude-squared coherence band summaries.
- Pair explosion guard: `max_pairs` parameter; default all pairs only when `n_channels ≤ 8`.
- API: `tsx.extract_features_mc(X, profile=..., cross=True)`.

### Z13 — Compute-everything-then-select (`select_features`)
Because extraction is nearly free, offer fast supervised selection so users can extract ~1,000 features and keep the best ~30:
- Per-feature relevance vs target: ANOVA F, Mann–Whitney/rank-biserial (classification), Pearson/Spearman and mutual information estimate (regression); Benjamini–Yekutieli FDR control (as tsfresh does) for the p-value path.
- Redundancy pruning: correlation-threshold clustering, keep the highest-relevance member per cluster.
- Implemented in Rust, parallel across features, zero-copy over the feature matrix.
- API: `tsx.select_features(F, y, task="auto", fdr=0.05, max_corr=0.9) -> (indices, report)`; sklearn-compatible `TsxSelector` transformer.
Differentiator: tsfresh's selection is the slow part of its workflow; this makes the whole extract→select pipeline interactive.

### Z14 — `MultiStreamExtractor` (many streams, one SIMD loop)
For fleets (e.g., 100k sensors): state in SoA layout across streams, `push_many(values: ndarray[n_streams])` updates every stream's O(1) statistics in lane-parallel loops; ring buffers `capacity × n_streams`. O(1)-tier features only; O(n)-tier features computed on `compute(streams=idx)` for the requested subset. No competitor offers this.

### Z15 — Stretch: very-large catalog
A full hctsa-scale (thousands of features) catalog is possible but low marginal value: most are highly redundant (catch22 was distilled from ~4,800 candidates). Prefer Z11 + Z13 over raw count. Only add families that a parity matrix shows users actually request.

---

## 5. Measurement Ceiling

### 5.1 Noise-free CI performance gates
Wall-clock on shared CI runners is noisy. Add **instruction-count benchmarks** (`iai-callgrind` / cachegrind, Linux) for every kernel and fail PRs on instruction-count regressions >2%; keep Criterion wall-clock for local/nightly dedicated-runner numbers.

### 5.2 Reference bounds (what "zenith" is measured against)
| Stage | Reference | Tool |
|---|---|---|
| FFT (500-pt real) | FFTW / `pyfftw`, `numpy.fft.rfft` | micro-bench, same machine |
| Quantile/selection | `numpy.partition`, vectorized-sort libs (e.g., x86-simd-sort / vqsort) | micro-bench |
| SIMD reductions | `llvm-mca` throughput bound for the emitted loop | `cargo asm` + `llvm-mca` |
| Whole pipeline | roofline: achieved GFLOP/s, bytes/s, IPC vs peak | `perf stat`, `likwid` (Linux) |

### 5.3 Per-stage reporting
`benches/report.py` emits a table per commit: stage time, % of total, achieved IPC, % of reference bound. A stage is "done" when it meets the §1.3 stop rule.

---

## 6. GPU / Accelerators — Decision
**Default: no.** For numpy-resident data the PCIe transfer (e.g., 1M × 500 f64 = 4 GB) rivals the CPU compute time, so a GPU path only wins when data already lives on the GPU. If demand appears, ship a separate `tsxtract-gpu` package consuming DLPack tensors (CuPy/PyTorch) with a subset of cost-class A–C features. Never in the core wheel.

---

## 7. Phases, Priorities, Gates

| Phase | Items | Gate |
|---|---|---|
| **Z0 — Re-baseline** | Run `arch_max` Phase 0 tooling on the post-Phase-2 code; produce stage table, η, IPC, LLC-miss rate; fill §1.2 with measured numbers | Decision table below filled in |
| **Z1 — Selection** | Z1 | quantile parity + ≥2× on stage |
| **Z2 — Runtime** | Z6 (if gated), Z7, Z8, Z10 | η ≥ 0.85 at (1k×500) |
| **Z3 — Tuning** | Z9 + static wisdom table in CI | no regression untuned; ≥ expected gain on 2+ machines |
| **Z4 — Output** | Z11, Z13, Z12 | invariance-pruning tests; select_features reference vs tsfresh selection on a public dataset |
| **Z5 — Speed tail** | Z4 (`f32`), then Z3/Z2/Z5 only if gated | stop rule §1.3 |
| **Z6 — Streams** | Z14 | lane-parallel push ≥ N× single-stream loop on 100k streams |
| **Z7 — Measurement** | §5.1 instruction-count CI gate; roofline report | gate live on `main` |

### Decision table (fill in at Z0)
| If measured… | Then |
|---|---|
| SORT/quantile stage >25% of time | do Z1 now |
| η < 0.85 at (1k×500) | do Z6 |
| FFT stage >35% after Z1 | prototype Z3 tier 2, then tier 3 only if ≥1.3× |
| Fused+ACF+perm >30% after Z1/Z3 | do Z2 |
| Results vary >10% across test machines | do Z9 earlier |
| All gates false | skip speed work; go to output (§4) |

---

## 8. Risks

| Risk | Mitigation |
|---|---|
| Exact selection edge cases (ties, ±0, denormals, tiny ranges → bucket-index overflow) | clamp bucket index; heavy-cluster recursion; fuzz with adversarial distributions |
| Custom pool bugs (deadlock, lost wakeups, panic propagation) | keep rayon fallback; loom/stress tests; env switch |
| Wisdom cache staleness / wrong-machine reuse | key by CPU model + flags + version; validate with one quick probe on load |
| f32 mode surprising users | opt-in only; tolerance documented; separate benchmark column |
| Views explosion (memory/time) | `max_columns` guard; invariance pruning; lazy per-view execution |
| Cross-channel pair explosion | `max_pairs`; default off for >8 channels |
| Chasing micro-gains | §1.3 stop rule; instruction-count gate keeps what's gained |
| Output uninit + missed writes | debug assertion that all elements written; NaN-poison in tests |

---

## 9. Kickoff Prompts

```
Z0: Read arch_zenith.md §1,§5,§7. Using the current main, produce benches/zenith_baseline.md:
per-stage time table (fused/select-or-sort/fft/acf/perm/misc), parallel efficiency at (1k,500)
for 1/2/4/8/16 threads, IPC and LLC-miss rate (perf stat). Fill the §7 decision table and
state which Z-items are gated in. No library changes.
```
```
Z1: Implement multi_select per arch_zenith.md §2 Z1 behind a SELECT intermediate. Parity-test vs
numpy.quantile(method="linear") on random/tied/heavy-tail/near-constant/bimodal data, benchmark vs
current sort path at n=128/500/2000, report speedup. Keep the old path behind a feature flag until
the gate passes.
```
```
Z4-output: Implement views (Z11) with invariance flags in registry.rs, then select_features (Z13).
Prove every pruned (view, feature) pair redundant in tests. Reference select_features against
tsfresh's selection on a public dataset. Report column counts and timing.
```
