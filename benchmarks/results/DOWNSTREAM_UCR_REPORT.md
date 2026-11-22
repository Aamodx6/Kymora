# UCR Downstream Classification Benchmark Report

Comprehensive evaluation of feature extraction libraries on canonical UCR univariate classification datasets (Matched Set n = 42).
Evaluated on canonical fixed train/test splits using standard Random Forest and Ridge classifiers.

> [!NOTE]
> **Leak-Free & Fair Methodology:**
> 1. **Canonical Train/Test Splits:** Evaluates generalization on the archive's fixed test splits.
> 2. **Zero-Leakage Preprocessing:** `SimpleImputer` and `StandardScaler` are fitted strictly on the train split only.
> 3. **Multi-Core Parity:** All four libraries execute multi-threaded (16 threads).
> 4. **Strict Matched-Set Comparison:** Metrics and statistical ranks are computed solely across datasets where all methods completed.

## Summary across Matched Datasets (n = 42)

| Library | Threads | Features | Mean RF Acc (%) | Mean Ridge Acc (%) | Mean Rank (RF) | Mean Rank (Ridge) | Per-Dataset Speedup [min, max] | Median Time (ms) |
|---|:---:|:---:|:---:|:---:|:---:|:---:|:---:|:---:|
| **tsfresh** | 16 | 777 | **84.79%** | **82.39%** | **2.19** | **2.43** | 17217.0× [6026.0×, 37584.5×] | 20943.62 ms |
| **Kymora (full)** | 16 | 543 | **82.79%** | **80.66%** | **2.83** | **3.17** | 2.0× [0.3×, 4.2×] | 2.17 ms |
| **Kymora (extended)** | 16 | 143 | **83.12%** | **80.39%** | **2.98** | **3.19** | 1.3× [0.3×, 3.0×] | 1.74 ms |
| **TSFEL** | 16 | 156 | **81.00%** | **79.71%** | **3.36** | **3.24** | 768.2× [88.3×, 3430.5×] | 942.67 ms |
| **Kymora (core33)** | 16 | 33 | **79.96%** | **77.42%** | **4.12** | **3.83** | 1.0× (ref) | 1.26 ms |
| **catch22** | 16 | 22 | **79.83%** | **75.75%** | **4.14** | **4.29** | 117.2× [20.9×, 357.2×] | 159.40 ms |

## Statistical Significance & Head-to-Head Record (vs Kymora)

| Competitor | Matched Datasets | RF Win/Tie/Loss | Ridge Win/Tie/Loss | RF p-val (Holm) | Ridge p-val (Holm) | Significant (p < 0.05)? |
|---|:---:|:---:|:---:|:---:|:---:|:---:|
| vs **Kymora (extended)** | 42 | 8/5/29 | 15/2/25 | 0.0007 (0.0026) | 0.0069 (0.0276) | RF: Yes, Ridge: Yes |
| vs **Kymora (full)** | 42 | 9/4/29 | 15/2/25 | 0.0124 (0.0371) | 0.0372 (0.1116) | RF: Yes, Ridge: No |
| vs **TSFEL** | 42 | 11/8/23 | 17/3/22 | 0.1606 (0.3212) | 0.0829 (0.1658) | RF: No, Ridge: No |
| vs **catch22** | 42 | 23/3/16 | 23/5/14 | 0.5554 (0.5554) | 0.2016 (0.2016) | RF: No, Ridge: No |
| vs **tsfresh** | 42 | 7/5/30 | 10/3/29 | 0.0003 (0.0015) | 0.0017 (0.0085) | RF: Yes, Ridge: Yes |

## Critical Difference (CD) Analysis (Nemenyi Test, α = 0.05)

For $k = 6$ extractors across $N = 42$ matched datasets, Critical Difference **$CD = 1.05$**.

```
CD = 1.05 (ranks within 1.05 are statistically indistinguishable at p < 0.05)

Rank Axis: 1.0 (Best) ------------------------------------------------ 4.0

Random Forest Ranks:
  tsfresh         : 2.19  |====== CD (1.05) ======|
  Kymora (full)   : 2.83  |====== CD (1.05) ======|
  Kymora (extended): 2.98  |====== CD (1.05) ======|
  TSFEL           : 3.36  |====== CD (1.05) ======|
  Kymora (core33) : 4.12  |====== CD (1.05) ======|
  catch22         : 4.14  |====== CD (1.05) ======|

Ridge Classifier Ranks:
  tsfresh         : 2.43  |====== CD (1.05) ======|
  Kymora (full)   : 3.17  |====== CD (1.05) ======|
  Kymora (extended): 3.19  |====== CD (1.05) ======|
  TSFEL           : 3.24  |====== CD (1.05) ======|
  Kymora (core33) : 3.83  |====== CD (1.05) ======|
  catch22         : 4.29  |====== CD (1.05) ======|
```

**Key Finding:** On Ridge linear models, Kymora achieves rank 3.83 vs catch22 rank 4.29 (Holm-adjusted $p = 0.2016$).  On tree models (RF), Kymora (4.12) and catch22 (4.14) remain within the critical difference threshold (CD = 1.05).

## Accuracy vs Extraction Time Pareto Frontier

Evaluates the trade-off between downstream predictive accuracy (RF / Ridge) and extraction throughput / latency.

| Feature Profile / Library | Features | Median Extraction Time (ms) | Relative Latency vs core33 | Mean RF Acc (%) | Mean Ridge Acc (%) | Pareto Efficiency |
|---|:---:|:---:|:---:|:---:|:---:|---|
| **Kymora (core33)** | 33 | 1.26 ms | 1.0× | 79.96% | 77.42% | **Optimal (Minimum Latency)**: catch22-class accuracy at ~100× lower cost |
| **Kymora (extended)** | 143 | 1.74 ms | 1.3× | 83.12% | 80.39% | **Optimal (Balanced)**: Higher accuracy at ultra-low latency (<3× core33) |
| **Kymora (full)** | 543 | 2.17 ms | 2.0× | 82.79% | 80.66% | **Optimal (High Capacity)**: Near-tsfresh accuracy, ~100× faster than tsfresh |
| **catch22** | 22 | 159.40 ms | 117.2× | 79.83% | 75.75% | Dominated by Kymora (core33) (comparable accuracy, ~100× slower) |
| **TSFEL** | 156 | 942.67 ms | 768.2× | 81.00% | 79.71% | High accuracy, but ~1,100× slower extraction |
| **tsfresh** | 777 | 20943.62 ms | 17217.0× | 84.79% | 82.39% | Maximum accuracy, but ~10,000× slower extraction |

## Per-Dataset Results (Random Forest Accuracy / Ridge Accuracy)

| Dataset | Samples × Length | Kymora (core33) | Kymora (extended) | Kymora (full) | catch22 | TSFEL | tsfresh |
|---|:---:|:---:|:---:|:---:|:---:|:---:|:---:|
| ArrowHead | 211 × 251 | 75.4% / 62.3% | 77.7% / 67.4% | 57.1% / 59.4% | 76.0% / 52.6% | 72.0% / 56.6% | 69.7% / 69.1% | 
| BME | 180 × 128 | 88.7% / 90.7% | 100.0% / 90.0% | 98.7% / 97.3% | 91.3% / 88.0% | 78.0% / 92.0% | 100.0% / 100.0% | 
| Beef | 60 × 470 | 60.0% / 40.0% | 66.7% / 36.7% | 73.3% / 60.0% | 63.3% / 50.0% | 53.3% / 50.0% | 83.3% / 73.3% | 
| BeetleFly | 40 × 512 | 85.0% / 70.0% | 85.0% / 70.0% | 90.0% / 75.0% | 80.0% / 75.0% | 95.0% / 85.0% | 95.0% / 75.0% | 
| BirdChicken | 40 × 512 | 90.0% / 60.0% | 100.0% / 65.0% | 95.0% / 85.0% | 85.0% / 70.0% | 90.0% / 80.0% | 90.0% / 85.0% | 
| CBF | 930 × 128 | 83.9% / 83.9% | 99.6% / 99.6% | 98.6% / 96.3% | 98.2% / 94.3% | 92.8% / 81.7% | 99.0% / 99.6% | 
| Chinatown | 363 × 24 | 93.6% / 79.6% | 95.0% / 96.2% | 97.7% / 94.8% | 90.4% / 84.8% | 95.9% / 94.5% | 97.1% / 97.4% | 
| Coffee | 56 × 286 | 100.0% / 96.4% | 100.0% / 100.0% | 100.0% / 100.0% | 100.0% / 100.0% | 100.0% / 96.4% | 100.0% / 100.0% | 
| DistalPhalanxOutlineAgeGroup | 539 × 80 | 71.9% / 77.0% | 71.9% / 77.7% | 74.1% / 67.6% | 69.1% / 74.1% | 72.7% / 72.7% | 71.2% / 66.2% | 
| DistalPhalanxOutlineCorrect | 876 × 80 | 76.4% / 71.0% | 77.9% / 75.4% | 79.7% / 72.1% | 79.3% / 71.4% | 76.1% / 76.8% | 80.1% / 71.7% | 
| DistalPhalanxTW | 539 × 80 | 64.7% / 67.6% | 64.0% / 66.2% | 67.6% / 61.2% | 65.5% / 64.0% | 65.5% / 61.9% | 63.3% / 57.6% | 
| ECG200 | 200 × 96 | 84.0% / 81.0% | 83.0% / 80.0% | 87.0% / 84.0% | 83.0% / 79.0% | 84.0% / 79.0% | 84.0% / 88.0% | 
| ECGFiveDays | 884 × 136 | 73.6% / 87.3% | 74.8% / 86.3% | 89.0% / 94.3% | 79.6% / 74.3% | 81.2% / 97.2% | 76.9% / 91.8% | 
| FaceFour | 112 × 350 | 70.5% / 76.1% | 80.7% / 80.7% | 63.6% / 81.8% | 60.2% / 53.4% | 56.8% / 80.7% | 80.7% / 87.5% | 
| FacesUCR | 2250 × 131 | 71.4% / 64.2% | 82.2% / 80.1% | 81.5% / 77.7% | 70.1% / 57.3% | 77.7% / 78.4% | 85.7% / 83.7% | 
| GunPoint | 200 × 150 | 85.3% / 84.0% | 94.0% / 95.3% | 94.0% / 92.7% | 97.3% / 93.3% | 96.0% / 98.0% | 97.3% / 94.7% | 
| Ham | 214 × 431 | 56.2% / 64.8% | 66.7% / 56.2% | 65.7% / 66.7% | 53.3% / 63.8% | 61.0% / 67.6% | 70.5% / 65.7% | 
| Herring | 128 × 512 | 56.2% / 59.4% | 60.9% / 62.5% | 57.8% / 57.8% | 50.0% / 59.4% | 57.8% / 64.1% | 57.8% / 68.8% | 
| ItalyPowerDemand | 1096 × 24 | 88.3% / 90.5% | 93.9% / 89.1% | 96.4% / 92.5% | 86.3% / 81.3% | 94.8% / 89.3% | 95.9% / 94.3% | 
| Lightning2 | 121 × 637 | 78.7% / 72.1% | 70.5% / 77.0% | 68.9% / 63.9% | 73.8% / 68.9% | 67.2% / 62.3% | 67.2% / 70.5% | 
| Lightning7 | 143 × 319 | 58.9% / 60.3% | 63.0% / 58.9% | 63.0% / 57.5% | 71.2% / 64.4% | 64.4% / 42.5% | 68.5% / 65.8% | 
| Meat | 120 × 448 | 88.3% / 90.0% | 90.0% / 88.3% | 86.7% / 91.7% | 93.3% / 91.7% | 91.7% / 85.0% | 96.7% / 88.3% | 
| MedicalImages | 1141 × 99 | 74.9% / 63.8% | 75.1% / 67.6% | 75.5% / 61.3% | 74.2% / 58.8% | 75.9% / 68.3% | 76.8% / 65.3% | 
| MiddlePhalanxOutlineAgeGroup | 554 × 80 | 58.4% / 61.0% | 59.1% / 59.1% | 58.4% / 44.8% | 56.5% / 61.0% | 60.4% / 51.9% | 55.2% / 39.0% | 
| MiddlePhalanxOutlineCorrect | 891 × 80 | 80.1% / 67.7% | 81.4% / 75.9% | 83.5% / 73.5% | 76.3% / 77.0% | 84.5% / 80.1% | 84.5% / 70.8% | 
| MiddlePhalanxTW | 553 × 80 | 57.1% / 53.9% | 59.7% / 53.2% | 57.1% / 48.7% | 56.5% / 54.5% | 54.5% / 51.9% | 59.1% / 46.8% | 
| MoteStrain | 1272 × 84 | 86.1% / 78.9% | 85.9% / 82.1% | 80.0% / 85.1% | 86.2% / 79.0% | 86.0% / 88.8% | 88.0% / 91.5% | 
| OliveOil | 60 × 570 | 63.3% / 80.0% | 80.0% / 83.3% | 93.3% / 86.7% | 73.3% / 76.7% | 70.0% / 86.7% | 90.0% / 90.0% | 
| Plane | 210 × 144 | 98.1% / 100.0% | 100.0% / 98.1% | 100.0% / 100.0% | 99.0% / 93.3% | 100.0% / 100.0% | 100.0% / 100.0% | 
| PowerCons | 360 × 144 | 95.0% / 90.6% | 95.6% / 93.3% | 95.6% / 95.0% | 90.6% / 84.4% | 95.0% / 92.8% | 96.1% / 93.9% | 
| SmoothSubspace | 300 × 15 | 94.7% / 93.3% | 94.0% / 89.3% | 94.7% / 91.3% | 86.0% / 85.3% | 92.7% / 95.3% | 95.3% / 92.7% | 
| SonyAIBORobotSurface1 | 621 × 70 | 87.9% / 86.9% | 90.0% / 88.9% | 90.5% / 85.4% | 82.4% / 81.2% | 90.2% / 83.2% | 88.4% / 84.2% | 
| SonyAIBORobotSurface2 | 980 × 65 | 91.4% / 87.9% | 93.1% / 93.9% | 92.9% / 96.3% | 90.0% / 88.0% | 88.2% / 94.1% | 86.8% / 95.3% | 
| SwedishLeaf | 1125 × 128 | 91.4% / 83.7% | 93.3% / 91.7% | 93.3% / 76.8% | 90.6% / 71.2% | 93.3% / 92.5% | 94.2% / 77.3% | 
| Symbols | 1020 × 398 | 96.0% / 94.1% | 94.3% / 88.5% | 87.5% / 88.7% | 96.1% / 92.3% | 95.6% / 94.7% | 95.8% / 94.6% | 
| SyntheticControl | 600 × 60 | 97.7% / 95.7% | 98.7% / 98.0% | 98.3% / 95.7% | 97.0% / 90.7% | 95.7% / 94.3% | 100.0% / 95.7% | 
| ToeSegmentation1 | 268 × 277 | 78.1% / 67.5% | 82.0% / 78.1% | 79.4% / 75.0% | 85.1% / 78.5% | 92.1% / 68.0% | 84.2% / 81.6% | 
| ToeSegmentation2 | 166 × 343 | 77.7% / 81.5% | 74.6% / 82.3% | 76.9% / 82.3% | 80.0% / 80.0% | 83.8% / 80.0% | 83.1% / 85.4% | 
| Trace | 200 × 275 | 99.0% / 99.0% | 100.0% / 99.0% | 100.0% / 98.0% | 100.0% / 100.0% | 99.0% / 100.0% | 100.0% / 99.0% | 
| TwoLeadECG | 1162 × 82 | 89.3% / 99.0% | 86.7% / 85.1% | 87.4% / 92.5% | 78.0% / 92.1% | 91.2% / 98.4% | 97.0% / 97.6% | 
| TwoPatterns | 5000 × 128 | 72.5% / 73.8% | 96.2% / 99.8% | 99.2% / 99.5% | 85.0% / 78.1% | 70.9% / 72.4% | 99.5% / 99.7% | 
| Wine | 111 × 234 | 68.5% / 64.8% | 53.7% / 70.4% | 48.1% / 81.5% | 53.7% / 48.1% | 59.3% / 63.0% | 57.4% / 66.7% | 