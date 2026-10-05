# Phase B3: Throughput, Scaling & Latency Report

**Generated:** 2026-10-04 11:44:41  
**Hardware:** 13th Gen Intel(R) Core(TM) i7-13620H (10C/16T hybrid)  
**OS:** Windows-11-10.0.26300-SP0  
**Software:** Python 3.14.6, numpy 2.5.2, numba 0.67.0, tsxtractor 0.3.0  
**Code state:** captured at commit f6b670c43952 (dirty tree), results generated at 4c268ca  
**Conditions:** all numbers are medians over warmup + n≥15 timed runs with GC disabled (see `benches/harness/runner.py`); 16 threads unless noted; f64 C-contiguous input.  

---

## 1. Throughput Results

### 1.1 Median runtime (ms) by shape × library (gaussian)

| Shape | numba_baseline_fast | numpy_baseline | tsxtract |
|---|---|---|---|
| 1×100 | 0.026 | 1.270 | 0.639 |
| 1×10000 | 3.484 | 6.453 | 0.971 |
| 10×500 | 0.181 | 3.529 | 0.542 |
| 100×100 | 0.425 | 7.554 | 0.854 |
| 100×500 | 2.944 | 31.391 | 1.831 |
| 100×5000 | 29.853 | 277.071 | 7.160 |
| 1000×100 | 4.044 | 60.383 | 2.808 |
| 1000×500 | 13.975 | 268.970 | 4.965 |
| 10000×500 | 135.970 | 3272.883 | 27.091 |

### 1.2 µs per series-feature by shape × library (gaussian)

| Shape | numba_baseline_fast | numpy_baseline | tsxtract |
|---|---|---|---|
| 1×100 | 0.786 | 38.480 | 19.376 |
| 1×10000 | 105.565 | 195.541 | 29.424 |
| 10×500 | 0.549 | 10.692 | 1.643 |
| 100×100 | 0.129 | 2.289 | 0.259 |
| 100×500 | 0.892 | 9.512 | 0.555 |
| 100×5000 | 9.046 | 83.961 | 2.170 |
| 1000×100 | 0.123 | 1.830 | 0.085 |
| 1000×500 | 0.423 | 8.151 | 0.150 |
| 10000×500 | 0.412 | 9.918 | 0.082 |

### 1.3 Win/loss summary (Tsxtract vs competitor, median, all 5 dists)

| Library | Tsxtract wins | Tsxtract losses | Thin wins (<2×) | Ratio range (competitor/tsx) | Median ratio |
|---|---|---|---|---|---|
| numba_baseline_fast | 28 | 17 | 7 | 0.02× – 8.5× | 1.44× |
| numpy_baseline | 45 | 0 | 1 | 1.99× – 130.2× | 17.14× |

- **Tsxtract loses to `numba_baseline_fast`** at: 1×100 (5/5), 10×500 (5/5), 100×100 (5/5), 100×500 (2/5) — see LOSS_LEDGER L1.

## 2. Scaling Results

### 2.1 Thread scaling @ 1000×500 gaussian

| Threads | Median (ms) | Speedup | Efficiency (η) |
|---|---|---|---|
| 1 | 13.569 | 1.00× | 100.00% |
| 2 | 7.479 | 1.81× | 90.71% |
| 4 | 4.221 | 3.21× | 80.35% |
| 8 | 3.159 | 4.29× | 53.69% |
| 16 | 3.338 | 4.06× | 25.41% |
| 32 | 4.159 | 3.26× | 10.19% |

> ⚠️ η drops past 4 threads on this 10C/16T hybrid (P+E cores) laptop. Treat as hardware-bound; re-measure on homogeneous server cores (see LOSS_LEDGER L3).

### 2.2 Series count scaling @ len=500

| N series | Median (ms) | µs/series | µs/series-feature |
|---|---|---|---|
| 1 | 0.520 | 519.950 | 15.7561 |
| 10 | 0.660 | 65.990 | 1.9997 |
| 100 | 1.217 | 12.171 | 0.3688 |
| 1,000 | 3.228 | 3.228 | 0.0978 |
| 10,000 | 24.062 | 2.406 | 0.0729 |
| 100,000 | 213.203 | 2.132 | 0.0646 |

### 2.3 Length scaling @ n=1000

| Length | Median (ms) | µs/series | µs/series-feature |
|---|---|---|---|
| 10 | 0.922 | 0.922 | 0.0279 |
| 100 | 1.739 | 1.739 | 0.0527 |
| 500 | 3.399 | 3.399 | 0.1030 |
| 1,000 | 6.451 | 6.451 | 0.1955 |
| 5,000 | 22.293 | 22.293 | 0.6756 |
| 50,000 | 227.913 | 227.913 | 6.9064 |

## 3. Latency Results

### 3.1 Single-series latency by length (1 thread)

| Length | Library | p50 (µs) | p95 (µs) | p99 (µs) | max (µs) |
|---|---|---|---|---|---|
| 10 | numpy | 1317.6 | 2673.0 | 3220.5 | 4732.2 |
| 10 | tsxtract | 345.8 | 6986.4 | 15375.8 | 29121.1 |
| 50 | numpy | 1235.6 | 2537.5 | 2821.2 | 3384.0 |
| 50 | tsxtract | 204.6 | 298.8 | 327.3 | 362.1 |
| 100 | numpy | 1350.7 | 2145.8 | 2344.0 | 2787.7 |
| 100 | tsxtract | 211.6 | 319.2 | 396.7 | 522.1 |
| 500 | numpy | 1564.8 | 2404.6 | 2777.9 | 3296.8 |
| 500 | tsxtract | 191.8 | 289.5 | 364.8 | 456.0 |
| 1,000 | numpy | 1760.8 | 2230.7 | 2775.9 | 3450.6 |
| 1,000 | tsxtract | 201.3 | 274.9 | 365.8 | 407.6 |
| 5,000 | numpy | 3711.8 | 4697.4 | 5918.5 | 6666.8 |
| 5,000 | tsxtract | 358.1 | 525.1 | 634.7 | 708.0 |
| 10,000 | numpy | 6294.1 | 9704.3 | 11803.5 | 13533.1 |
| 10,000 | tsxtract | 552.0 | 728.9 | 833.7 | 1230.8 |
| 50,000 | numpy | 27151.8 | 37749.9 | 43763.1 | 46277.7 |
| 50,000 | tsxtract | 2323.0 | 3060.5 | 3675.2 | 3960.9 |
| 100,000 | numpy | 52189.8 | 74883.0 | 86707.9 | 94317.0 |
| 100,000 | tsxtract | 5184.3 | 8801.0 | 9446.7 | 9748.3 |

> ⚠️ At len=10 Tsxtract wins p50 (345.8 µs vs 1317.6 µs) but loses the tail (p99 15,375.8 µs vs 3,220.5 µs; max 29.1 ms) — thread-pool/FFI wake jitter on the very first touches of a tiny input. See LOSS_LEDGER L2/L7.

### 3.2 Crossover analysis (Tsxtract vs NumPy @ 1 series, 1 thread)

| Length | Tsxtract (µs) | NumPy (µs) | Winner | Ratio |
|---|---|---|---|---|
| 10 | 151.1 | 1234.7 | tsx | 8.17× |
| 25 | 164.4 | 1245.5 | tsx | 7.57× |
| 50 | 157.1 | 1330.4 | tsx | 8.47× |
| 100 | 183.9 | 1309.5 | tsx | 7.12× |
| 200 | 171.6 | 1292.6 | tsx | 7.53× |
| 500 | 160.2 | 1460.2 | tsx | 9.11× |
| 1,000 | 203.3 | 1712.4 | tsx | 8.42× |
| 5,000 | 337.8 | 3630.7 | tsx | 10.75× |

**No crossover vs NumPy:** Tsxtract wins at every measured length (7.1×–10.7×). The numba baseline does cross Tsxtract — see §1.3 and LOSS_LEDGER L1.

---
*Phase B3 Report generated 2026-10-04 11:44:41 from F:\Active Repo\Tsxtract\benches\results\throughput.jsonl, scaling.jsonl, latency.jsonl.*