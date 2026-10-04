# Downstream Machine Learning Utility Benchmark Report

Evaluation of feature representations on standard dynamic classification benchmarks (5-fold stratified CV).

| Dataset | Representation | Feats | Extract Time (ms) | RF Acc (%) | RF F1 | Ridge Acc (%) | Ridge F1 |
|---|---|---:|---:|---:|---:|---:|---:|
| Synthetic Control (6-class) | **Tsxtract (33 feats)** | 33 | 0.61 ms | 96.5% | 0.9650 | 93.3% | 0.9331 |
| Synthetic Control (6-class) | **Naive Stats (5 feats)** | 5 | 1.03 ms | 93.5% | 0.9349 | 77.0% | 0.7572 |
| Synthetic Control (6-class) | **catch22 (22 feats)** | 22 | 232.24 ms | 91.0% | 0.9094 | 85.5% | 0.8540 |
| Simulated ECG (2-class) | **Tsxtract (33 feats)** | 33 | 0.42 ms | 100.0% | 1.0000 | 100.0% | 1.0000 |
| Simulated ECG (2-class) | **Naive Stats (5 feats)** | 5 | 0.74 ms | 75.2% | 0.7509 | 62.8% | 0.6256 |
| Simulated ECG (2-class) | **catch22 (22 feats)** | 22 | 191.55 ms | 100.0% | 1.0000 | 100.0% | 1.0000 |
| Kinematic Gesture (2-class) | **Tsxtract (33 feats)** | 33 | 0.24 ms | 100.0% | 1.0000 | 100.0% | 1.0000 |
| Kinematic Gesture (2-class) | **Naive Stats (5 feats)** | 5 | 0.52 ms | 95.2% | 0.9525 | 96.5% | 0.9650 |
| Kinematic Gesture (2-class) | **catch22 (22 feats)** | 22 | 151.43 ms | 100.0% | 1.0000 | 100.0% | 1.0000 |
| Power Demand (2-class) | **Tsxtract (33 feats)** | 33 | 0.61 ms | 100.0% | 1.0000 | 100.0% | 1.0000 |
| Power Demand (2-class) | **Naive Stats (5 feats)** | 5 | 0.60 ms | 64.2% | 0.6408 | 65.2% | 0.6522 |
| Power Demand (2-class) | **catch22 (22 feats)** | 22 | 153.58 ms | 100.0% | 1.0000 | 100.0% | 1.0000 |