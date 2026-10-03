# Tsxtract Comprehensive Benchmark Matrix

- **Environment**: Windows-11-10.0.26300-SP0, Python 3.14.7, 16 CPU cores
- **Standard Batch Shape**: 1000 series × 500 points
- **Tsxtract Version**: 0.3.2

## 1. Profile Throughput (1,000 × 500)

| Profile | Features | Latency (1k) | Per-Series | Per-Feature Cost | Throughput |
|:---|:---:|:---:|:---:|:---:|:---:|
| `minimal` | 10 | 0.51 ms | 0.51 µs | 0.0507 µs | 1,972,776 series/s |
| `core33` | 33 | 1.80 ms | 1.80 µs | 0.0546 µs | 555,016 series/s |
| `extended` | 143 | 7.12 ms | 7.12 µs | 0.0498 µs | 140,395 series/s |
| `full` | 543 | 8.36 ms | 8.36 µs | 0.0154 µs | 119,654 series/s |

## 2. Multi-Core Scaling (Profile `core33`, 1,000 × 500)

| Threads | Latency | Per-Series | Speedup vs 1T | Scaling Efficiency |
|:---:|:---:|:---:|:---:|:---:|
| 1 | 11.31 ms | 11.31 µs | 1.00× | 100.0% |
| 2 | 6.03 ms | 6.03 µs | 1.88× | 93.8% |
| 4 | 3.58 ms | 3.58 µs | 3.16× | 78.9% |
| 8 | 2.52 ms | 2.52 µs | 4.49× | 56.1% |
| 16 | 2.60 ms | 2.60 µs | 4.34× | 27.1% |

## 3. Memory Footprint (100,000 series × 500 steps)

- Expected output matrix (100k × 33 × float64): **25.18 MB**
- Peak memory allocated during extraction: **25.18 MB**
- Overhead beyond output buffer: **0.00 MB** (strictly zero intermediate duplication)
- Runtime for 100k series (50,000,000 points): **0.10 s**

## 4. Competitive Landscape Comparison (1,000 × 500)

| Engine | Features | Runtime (1k × 500) | Per-Series Cost | Speedup vs Competitor |
|:---|:---:|:---:|:---:|:---:|
| **Tsxtract (`core33`)** | **33** | **1.80 ms** | **1.80 µs** | **Baseline (1.0×)** |
| `catch22` | 22 | 1.05 s | 1045.8 µs | **580× slower** |
| `tsfel` | 156 | 9.81 s | 9806.6 µs | **5443× slower** |
| `tsfresh` | 777 | 100.50 s | 100500.0 µs | **55779× slower** |
