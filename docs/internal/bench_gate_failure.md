# Benchmark Regression Gate Failure Analysis & Postmortem

## Executive Summary

On the `main` branch, recent CI workflow runs experienced persistent failures in the `benchmark regression gate (ubuntu-latest, py3.12)` job and consequently in the aggregate `ci gate (all green)` job:
- **Run 45020682677** (Phase 8): Failed with ratio `1.7568x` (exceeded ratio threshold `1.20`)
- **Run 45024113242** (Phase 10): Failed with ratio `1.3792x` (exceeded ratio threshold `1.20`)

These failures blocked PR merges and caused red status indicators on `main` despite all unit tests, external parity tests, typing, hygiene, and wheel builds passing without error.

---

## 1. Failed Job Logs (`gh run view --log-failed`)

Inspecting the failed CI runs via `gh run view --log-failed` isolates the failure directly to step `Store and track benchmark result` within the `benchmark` job:

### Run 45024113242 (Commit `e0fbda7c21`):
```text
benchmark regression gate (ubuntu-latest, py3.12)	Store and track benchmark result
##[warning]Performance alert! Previous value was 4.5956 and current value is 6.3384. It is 1.3792323091652885x worse than previous exceeding a ratio threshold 1.2
##[error]# :warning: **Performance Alert** :warning:

Possible performance regression was detected for benchmark 'Kymora Core33 1kx500 Benchmark'.
Benchmark result of this commit is worse than the previous benchmark result exceeding threshold 1.20.

| Benchmark suite | Current: e0fbda7c21feca43dfb3292d2c655b308e8b77db | Previous: 601526218e6c81fd779b536756c4962cad2c3fbb | Ratio |
|-|-|-|-|
| `core33_1000x500` | `6.3384` ms (`0.2078`) | `4.5956` ms (`0.6076`) | `1.38` |
```
Result in `ci gate (all green)`:
```text
BLOCKED by benchmark: failure
##[error]Process completed with exit code 1.
```

### Run 45020682677 (Commit `53c7427633`):
```text
benchmark regression gate (ubuntu-latest, py3.12)	Store and track benchmark result
##[warning]Performance alert! Previous value was 3.3113 and current value is 5.8176. It is 1.7568930933410777x worse than previous exceeding a ratio threshold 1.2
##[error]# :warning: **Performance Alert** :warning:

Possible performance regression was detected for benchmark 'Kymora Core33 1kx500 Benchmark'.
Benchmark result of this commit is worse than the previous benchmark result exceeding threshold 1.20.

| Benchmark suite | Current: 53c7427633de5921850f8397653666cf612f1df1 | Previous: f4d229944626d944dd08f4ac57452e54268a1447 | Ratio |
|-|-|-|-|
| `core33_1000x500` | `5.8176` ms (`0.0494`) | `3.3113` ms (`0.5124`) | `1.76` |
```
Result in `ci gate (all green)`:
```text
BLOCKED by benchmark: failure
##[error]Process completed with exit code 1.
```

---

## 2. Benchmark Measurement Spread Across Main Runs

Historical data tracked on `origin/gh-pages` (`dev/bench/data.js`) reveals significant wall-clock latency fluctuations across consecutive commits with identical `core33` numeric kernels:

| Commit | Run ID | Date / Time | Median Wall-Clock (`core33_1000x500`) | CV | Prior Value | Ratio vs Prior | Gate Status |
| :--- | :--- | :--- | :--- | :--- | :--- | :--- | :--- |
| `f695a0e` | 45015316404 | 2026-11-22 11:02 UTC | **5.8653 ms** | 1.6% | — | — | PASSED |
| `dc75aad` | 45016408305 | 2026-11-22 11:15 UTC | **6.4137 ms** | 2.4% | 5.8653 ms | 1.09x | PASSED |
| `46985fb` | 45018275590 | 2026-11-22 11:37 UTC | **5.8312 ms** | 4.8% | 6.4137 ms | 0.91x | PASSED |
| `42c5c51` | 45018926001 | 2026-11-22 11:46 UTC | **3.3312 ms** | 2.8% | 5.8312 ms | 0.57x | PASSED |
| `f4d2299` | 45019973939 | 2026-11-22 11:59 UTC | **3.3113 ms** | 15.6% | 3.3312 ms | 0.99x | PASSED |
| `53c7427` | 45020682677 | 2026-11-22 12:07 UTC | **5.8176 ms** | 5.0% | 3.3113 ms | **1.76x** | **FAILED** (> 1.20) |
| `6015262` | 45021770443 | 2026-11-22 12:20 UTC | **4.5956 ms** | 14.6% | 5.8176 ms | 0.79x | PASSED |
| `e0fbda7` | 45024113242 | 2026-11-22 12:47 UTC | **6.3384 ms** | 9.7% | 4.5956 ms | **1.38x** | **FAILED** (> 1.20) |

### Key Observations
1. **Spread Range:** The measured median elapsed time for the exact same workload (1000 series × 500 steps `core33`) ranged from **3.31 ms** to **6.41 ms**.
2. **Variance:** This represents a **93.7% variation** (nearly 2× speed difference) attributable purely to GitHub Actions virtual machine host hardware differences and CPU throttling.
3. **Flapping Gate:** Every time a runner landed on a fast host (~3.3 ms), the subsequent commit—even if documentation-only or release metadata—was virtually guaranteed to fail when scheduled on a standard host (~5.8–6.3 ms), producing a false regression ratio > 1.20.

---

## 3. Root Cause Analysis

The failure stems from the combination of three structural factors:

### 1. Missing Stored Baseline for Linux
In `tools/perf_gate.py`, the probe compares against a platform-keyed baseline stored in `benchmarks/results/perf_baseline.json`:
```json
{
  "win32-Intel64 Family 6 Model 186 Stepping 2, GenuineIntel-py314": {
    "runs": 30,
    "median_ms": 2.1107,
    "shape": [1000, 500],
    "profile": "core33"
  }
}
```
Only the maintainer's Windows laptop baseline was recorded. When running with `--ci`, `perf_gate.py` detected no entry for `linux-x86_64-py312` and printed:
```text
no baseline for linux-x86_64-py312; pass --update-baseline to record one
current median: 6.338 ms (not gated)
```
Consequently, `perf_gate.py` exited with code 0 and did not gate the commit.

### 2. Relative Wall-Clock Gating in `github-action-benchmark`
Because `perf_gate.py` did not fail, CI handed off the exported JSON to `benchmark-action/github-action-benchmark` in `ci.yml`:
```yaml
- name: Store and track benchmark result
  uses: benchmark-action/github-action-benchmark@4322e5726e6334590d251fc4f92bec0efafc45dc
  with:
    name: Kymora Core33 1kx500 Benchmark
    tool: 'customSmallerIsBetter'
    output-file-path: ${{ runner.temp }}/benchmark_results.json
    alert-threshold: '120%'
    fail-on-alert: ${{ github.ref == 'refs/heads/main' }}
    auto-push: ${{ github.ref == 'refs/heads/main' }}
```
This action compared the current run directly against the *immediately preceding commit* on `gh-pages` with a strict `120%` ratio cutoff.

### 3. Multi-Tenant Shared Runner Noise
GitHub-hosted `ubuntu-latest` runners run on hyperthreaded Azure virtual machines (Standard_D2s_v3/v4/v5, AMD EPYC or Intel Xeon). They do not offer dedicated CPU cores, fixed clock speeds, or CPU isolation:
- Background noisy neighbors on the same physical host cause CPU scheduling delays.
- Different physical CPU models have differing IPC characteristics (e.g. 3.3 ms on newer Sapphire Rapids / Zen 4 vs 6.4 ms on older Broadwell / Cascadelake).
- Wall-clock time on shared public runners is fundamentally non-deterministic and cannot be used as a hard merge gate with a 20% tolerance.

---

## 4. Remediation Plan

1. **Unblock CI Immediately:**
   - Remove `benchmark` from `ci-gate`'s `needs` list.
   - Configure the existing wall-clock benchmark job with `continue-on-error: true`.
   - Enable `comment-on-alert: true` so regressions trigger notifications without failing the workflow.
2. **Replace the Hard Gate with Instruction Counting:**
   - Implement an instruction-count benchmark (`valgrind`/`callgrind` or `iai-callgrind`) measuring instruction reads (`Ir`).
   - Instruction counts are CPU-clock and runner-noise independent (deterministic down to instruction counts).
   - In PR CI, compare Base vs Head within the exact same runner and environment; fail only on a true >2% instruction regression.
   - Provide a documented `perf-ok` label to override expected instruction increases.
3. **Move Wall-Clock Tracking to Nightly:**
   - Keep `github-action-benchmark` wall-clock trend monitoring in `nightly.yml` for alerting and long-term trend visualization only, with `fail-on-alert: false`.
