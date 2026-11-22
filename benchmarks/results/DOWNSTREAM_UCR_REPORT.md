# UCR Downstream Classification Benchmark Report

Comprehensive evaluation of feature extraction libraries on canonical UCR univariate classification datasets.
Evaluated via 5-fold stratified cross-validation using standard Random Forest and Ridge classifiers.

> [!NOTE]
> **Leak-Free & Fair Methodology:**
> 1. **Zero-Leakage Preprocessing:** `SimpleImputer` and `StandardScaler` are fitted strictly within each cross-validation fold.
> 2. **Multi-Core Baselines:** tsfresh and TSFEL run multi-threaded (`n_jobs=4`).
> 3. **Per-Dataset Speedup:** Speedup ratios are calculated per-dataset (`time_baseline / time_kymora`) rather than dividing mixed aggregate times.

## Summary across Datasets

| Library | Features | Mean RF Acc (%) | Mean Ridge Acc (%) | Mean Rank (RF) | Mean Rank (Ridge) | Per-Dataset Speedup | Median Time (ms) |
|---|:---:|:---:|:---:|:---:|:---:|:---:|:---:|
| **tsfresh** | 777 | **95.97%** | **95.27%** | **1.60** | **1.60** | 7788.1× slower | 7592.33 ms |
| **TSFEL** | 156 | **95.55%** | **94.75%** | **1.75** | **1.50** | 5344.2× slower | 3037.06 ms |
| **catch22** | 22 | **93.73%** | **90.47%** | **2.38** | **3.25** | 79.5× slower | 60.68 ms |
| **Kymora (core33)** | 33 | **92.34%** | **93.58%** | **2.88** | **2.25** | 1.0× (ref) | 0.81 ms |

## Statistical Significance (Wilcoxon Signed-Rank Test vs Kymora)

| Comparison (Kymora vs) | Datasets | RF p-value | Ridge p-value | Significant (p < 0.05)? |
|---|:---:|:---:|:---:|:---:|
| vs **TSFEL** | 8 | 0.0469 (Yes) | 0.1094 (No) | RF: Yes, Ridge: No |
| vs **catch22** | 8 | 0.6406 (No) | 0.0156 (Yes) | RF: No, Ridge: Yes |
| vs **tsfresh** | 5 | 0.0625 (No) | 0.1250 (No) | RF: No, Ridge: No |

## Per-Dataset Results (Random Forest Accuracy / Ridge Accuracy)

| Dataset | Samples × Length | Kymora (core33) | catch22 | TSFEL | tsfresh |
|---|:---:|:---:|:---:|:---:|:---:|
| ArrowHead | 211 × 251 | 79.2% / 80.1% | 82.5% / 78.7% | 86.3% / 79.6% | 85.8% / 83.0% | 
| Coffee | 56 × 286 | 91.4% / 100.0% | 100.0% / 98.3% | 98.2% / 100.0% | 98.2% / 100.0% | 
| ECG200 | 200 × 96 | 82.5% / 84.5% | 81.0% / 78.5% | 87.5% / 85.5% | — | 
| GunPoint | 200 × 150 | 93.5% / 95.5% | 98.5% / 93.0% | 99.0% / 99.5% | 98.5% / 97.0% | 
| ItalyPowerDemand | 1096 × 24 | 95.0% / 92.7% | 93.3% / 84.8% | 96.4% / 96.4% | 97.4% / 96.9% | 
| SyntheticControl | 600 × 60 | 98.7% / 97.2% | 98.0% / 93.0% | 97.8% / 97.0% | — | 
| Trace | 200 × 275 | 99.5% / 99.0% | 100.0% / 100.0% | 99.5% / 100.0% | 100.0% / 99.5% | 
| TwoLeadECG | 1162 × 82 | 99.1% / 99.7% | 96.5% / 97.5% | 99.7% / 100.0% | — | 