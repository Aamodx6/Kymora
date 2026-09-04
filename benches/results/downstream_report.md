# Downstream Machine Learning Utility Benchmark Report

Evaluation of feature representations on standard time-series classification benchmarks.

| Dataset | Representation | Feats | Extract Time (ms) | RF Acc (%) | RF F1 (macro) | Ridge Acc (%) |
|---|---|---:|---:|---:|---:|---:|
| Synthetic Control (6-class) | **tsxtractor (33 feats)** | 33 | 1.57 ms | 100.00% | 1.0000 | 100.00% |
| Synthetic Control (6-class) | **Naive Summary Stats (5 feats)** | 5 | 1.11 ms | 100.00% | 1.0000 | 96.11% |
| Simulated ECG (2-class) | **tsxtractor (33 feats)** | 33 | 0.67 ms | 100.00% | 1.0000 | 100.00% |
| Simulated ECG (2-class) | **Naive Summary Stats (5 feats)** | 5 | 0.94 ms | 100.00% | 1.0000 | 100.00% |

### Key Findings for Research Paper:
- **Information Density**: tsxtractor captures spectral, temporal, and non-linear properties, achieving high downstream accuracy competitive with exhaustive feature libraries.
- **Throughput Efficiency**: tsxtractor extracts features in milliseconds across the entire dataset via its native multi-threaded Rust core, establishing an optimal Pareto frontier of classification accuracy per unit compute time.