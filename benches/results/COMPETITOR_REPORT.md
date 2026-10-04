# Phase B3 Step 2: Competitor Throughput Matrix — Three Views

**Generated:** 2026-10-04 16:57:28  
**Hardware:** 13th Gen Intel i7-13620H (10C/16T hybrid), Windows 11, 16 threads, f64 C-contiguous  
**Views per row (arch.md §11.6):** raw median ms · µs/series-feature · matched-feature (definition-agreed subset only)  
**Protocol:** fresh subprocess per case, warmup, GC disabled; per-case wall-clock timeout recorded as an explicit `timeout` row; tsfresh/sktime slow families use min_runs=1 (single full run dominates); see `benches/suites/throughput_competitors.py`.

## Shape 1 × 100

| Library | n_feat | raw med (ms) | raw best (ms) | µs/series-feat | matched med (ms) | matched µs/sf | ratio raw | ratio matched |
|---|---|---|---|---|---|---|---|---|
| Tsxtract core33 | 33 | 0.58 | 0.28 | 17.589 | — | — | 1.0× | — |
| catch22 (22) | 22 | 0.26 | 0.22 | 11.741 | — | — | 0.4× | — |
| TSFEL (156, README cfg) | 156 | 2,159.00 | 3,952.70 | 13,839.775 | 2,120.00 | 163,077.235 | 3,376.6× | 5,907.77× |
| tsfresh (777, e2e) | 777 | 7,202.19 | 17,881.17 | 9,269.226 | 7,180.16 | 552,319.708 | 11,264.0× | 18,652.18× |
| tsfresh (777, extract-only) | 777 | 7,078.65 | 10,723.72 | 9,110.228 | 7,180.16 | 552,319.708 | 11,070.8× | 18,652.18× |
| antropy (8) | 8 | 0.74 | 0.64 | 92.675 | — | — | 1.2× | — |
| tsflex (7 stats) | 7 | 4.62 | 5.65 | 659.707 | — | — | 7.2× | — |
| sktime Catch22 (22) | 22 | 24.63 | 11.36 | 1,119.323 | — | — | 38.5× | — |

## Shape 1 × 10,000

| Library | n_feat | raw med (ms) | raw best (ms) | µs/series-feat | matched med (ms) | matched µs/sf | ratio raw | ratio matched |
|---|---|---|---|---|---|---|---|---|
| Tsxtract core33 | 33 | 0.88 | 0.58 | 26.541 | — | — | 1.0× | — |
| catch22 (22) | 22 | 33.52 | 36.37 | 1,523.618 | — | — | 34.5× | — |
| TSFEL (156, README cfg) | 156 | 2,070.43 | 2,180.29 | 13,271.968 | 1,996.51 | 153,577.677 | 2,132.3× | 2,868.55× |
| tsfresh (777, e2e) | 777 | 7,303.37 | 7,936.26 | 9,399.453 | 6,568.05 | 505,234.292 | 7,521.5× | 9,630.57× |
| tsfresh (777, extract-only) | 777 | 7,272.81 | 11,432.14 | 9,360.116 | 6,568.05 | 505,234.292 | 7,490.0× | 9,630.57× |
| antropy (8) | 8 | 237.56 | 227.28 | 29,694.425 | — | — | 244.7× | — |
| tsflex (7 stats) | 7 | 5.09 | 5.04 | 726.771 | — | — | 5.2× | — |
| sktime Catch22 (22) | 22 | 21.74 | 49.33 | 988.186 | — | — | 22.4× | — |

## Shape 10 × 500

| Library | n_feat | raw med (ms) | raw best (ms) | µs/series-feat | matched med (ms) | matched µs/sf | ratio raw | ratio matched |
|---|---|---|---|---|---|---|---|---|
| Tsxtract core33 | 33 | 0.54 | 0.39 | 1.643 | — | — | 1.0× | — |
| catch22 (22) | 22 | 537.38 | 528.69 | 2,442.625 | — | — | 991.4× | — |
| TSFEL (156, README cfg) | 156 | 3,032.39 | 2,224.83 | 1,943.840 | 2,970.70 | 22,851.529 | 5,594.3× | 6,151.79× |
| tsfresh (777, e2e) | 777 | 7,015.16 | 7,086.14 | 902.852 | 7,101.58 | 54,627.551 | 12,941.9× | 13,875.70× |
| tsfresh (777, extract-only) | 777 | 7,185.05 | 7,185.05 | 924.716 | 7,101.58 | 54,627.551 | 13,255.3× | 13,875.70× |
| antropy (8) | 8 | 26.52 | 23.94 | 331.538 | — | — | 48.9× | — |
| tsflex (7 stats) | 7 | 41.31 | 38.75 | 590.075 | — | — | 76.2× | — |
| sktime Catch22 (22) | 22 | 28.80 | 28.49 | 130.930 | — | — | 53.1× | — |

## Shape 100 × 100

| Library | n_feat | raw med (ms) | raw best (ms) | µs/series-feat | matched med (ms) | matched µs/sf | ratio raw | ratio matched |
|---|---|---|---|---|---|---|---|---|
| Tsxtract core33 | 33 | 0.73 | 0.50 | 0.222 | — | — | 1.0× | — |
| catch22 (22) | 22 | 586.47 | 566.82 | 266.576 | — | — | 686.4× | — |
| TSFEL (156, README cfg) | 156 | 2,225.18 | 285.86 | 142.640 | 2,101.22 | 1,616.322 | 2,604.2× | 3,619.67× |
| tsfresh (777, e2e) | 777 | 7,648.62 | 7,648.62 | 98.438 | 6,881.43 | 5,293.409 | 8,951.5× | 10,709.57× |
| tsfresh (777, extract-only) | 777 | 7,743.59 | 7,743.59 | 99.660 | 6,881.43 | 5,293.409 | 9,062.7× | 10,709.57× |
| antropy (8) | 8 | 75.35 | 71.77 | 94.187 | — | — | 88.2× | — |
| tsflex (7 stats) | 7 | 400.75 | 395.34 | 572.495 | — | — | 469.0× | — |
| sktime Catch22 (22) | 22 | 182.01 | 179.74 | 82.733 | — | — | 213.0× | — |

## Shape 100 × 500

| Library | n_feat | raw med (ms) | raw best (ms) | µs/series-feat | matched med (ms) | matched µs/sf | ratio raw | ratio matched |
|---|---|---|---|---|---|---|---|---|
| Tsxtract core33 | 33 | 1.71 | 0.94 | 0.519 | — | — | 1.0× | — |
| catch22 (22) | 22 | 635.52 | 620.29 | 288.871 | — | — | 347.0× | — |
| TSFEL (156, README cfg) | 156 | 2,377.41 | 333.03 | 152.398 | 2,188.16 | 1,683.200 | 1,298.1× | 2,448.43× |
| tsfresh (777, e2e) | 777 | 8,250.32 | 8,250.32 | 106.182 | 7,052.85 | 5,425.269 | 4,504.9× | 7,237.40× |
| tsfresh (777, extract-only) | 777 | 8,349.52 | 8,349.52 | 107.458 | 7,052.85 | 5,425.269 | 4,559.1× | 7,237.40× |
| antropy (8) | 8 | 265.05 | 256.40 | 331.309 | — | — | 144.7× | — |
| tsflex (7 stats) | 7 | 414.82 | 412.94 | 592.598 | — | — | 226.5× | — |
| sktime Catch22 (22) | 22 | 226.36 | 245.46 | 102.893 | — | — | 123.6× | — |

## Shape 100 × 5,000

| Library | n_feat | raw med (ms) | raw best (ms) | µs/series-feat | matched med (ms) | matched µs/sf | ratio raw | ratio matched |
|---|---|---|---|---|---|---|---|---|
| Tsxtract core33 | 33 | 7.02 | 4.93 | 2.127 | — | — | 1.0× | — |
| catch22 (22) | 22 | 777.16 | 763.77 | 353.253 | — | — | 108.5× | — |
| TSFEL (156, README cfg) | 156 | 2,590.58 | 559.22 | 166.063 | 2,202.57 | 1,694.287 | 361.8× | 680.73× |
| tsfresh (777, e2e) | 777 | 20,373.52 | 20,475.37 | 262.207 | 7,222.55 | 5,555.807 | 2,845.5× | 1,776.22× |
| tsfresh (777, extract-only) | 777 | 19,974.42 | 19,974.42 | 257.071 | 7,222.55 | 5,555.807 | 2,789.7× | 1,776.22× |
| antropy (8) | 8 | 8,032.02 | 8,016.11 | 10,040.030 | — | — | 1,121.8× | — |
| tsflex (7 stats) | 7 | 435.02 | 431.68 | 621.459 | — | — | 60.8× | — |
| sktime Catch22 (22) | 22 | 935.53 | 918.28 | 425.242 | — | — | 130.7× | — |

## Shape 1,000 × 100

| Library | n_feat | raw med (ms) | raw best (ms) | µs/series-feat | matched med (ms) | matched µs/sf | ratio raw | ratio matched |
|---|---|---|---|---|---|---|---|---|
| Tsxtract core33 | 33 | 2.74 | 1.79 | 0.083 | — | — | 1.0× | — |
| catch22 (22) | 22 | 644.10 | 634.43 | 29.277 | — | — | 229.4× | — |
| TSFEL (156, README cfg) | 156 | 3,965.43 | 1,949.09 | 25.419 | 2,426.36 | 186.643 | 1,412.1× | 1,704.92× |
| tsfresh (777, e2e) | 777 | 15,129.59 | 15,384.26 | 19.472 | 7,169.46 | 551.497 | 5,387.5× | 4,640.28× |
| tsfresh (777, extract-only) | 777 | 15,315.51 | 15,315.51 | 19.711 | 7,169.46 | 551.497 | 5,453.8× | 4,640.28× |
| antropy (8) | 8 | 769.43 | 776.64 | 96.178 | — | — | 274.0× | — |
| tsflex (7 stats) | 7 | 4,103.32 | 4,109.97 | 586.189 | — | — | 1,461.2× | — |
| sktime Catch22 (22) | 22 | 1,753.55 | 1,839.58 | 79.707 | — | — | 624.4× | — |

## Shape 1,000 × 500

| Library | n_feat | raw med (ms) | raw best (ms) | µs/series-feat | matched med (ms) | matched µs/sf | ratio raw | ratio matched |
|---|---|---|---|---|---|---|---|---|
| Tsxtract core33 | 33 | 3.90 | 3.75 | 0.118 | — | — | 1.0× | — |
| catch22 (22) | 22 | 690.67 | 710.47 | 31.394 | — | — | 139.1× | — |
| TSFEL (156, README cfg) | 156 | 4,233.71 | 2,283.13 | 27.139 | 2,448.53 | 188.348 | 852.7× | 991.89× |
| tsfresh (777, e2e) | 777 | 19,071.44 | 19,537.37 | 24.545 | 7,281.89 | 560.146 | 3,840.9× | 2,467.56× |
| tsfresh (777, extract-only) | 777 | 18,354.70 | 19,758.46 | 23.623 | 7,281.89 | 560.146 | 3,696.6× | 2,467.56× |
| antropy (8) | 8 | 2,657.18 | 2,632.23 | 332.148 | — | — | 535.1× | — |
| tsflex (7 stats) | 7 | 4,108.19 | 4,157.61 | 586.884 | — | — | 827.4× | — |
| sktime Catch22 (22) | 22 | 2,226.75 | 2,476.68 | 101.216 | — | — | 448.5× | — |

## Shape 10,000 × 500

| Library | n_feat | raw med (ms) | raw best (ms) | µs/series-feat | matched med (ms) | matched µs/sf | ratio raw | ratio matched |
|---|---|---|---|---|---|---|---|---|
| Tsxtract core33 | 33 | 21.94 | 23.34 | 0.066 | — | — | 1.0× | — |
| catch22 (22) | 22 | 1,885.05 | 2,064.07 | 8.568 | — | — | 69.6× | — |
| TSFEL (156, README cfg) | 156 | 22,151.29 | 21,420.92 | 14.200 | 5,136.25 | 39.510 | 817.7× | 291.57× |
| tsfresh (777, e2e) | — | — | — | — | — | — | — | — | not run: {'timeout'} |
| tsfresh (777, extract-only) | — | — | — | — | — | — | — | — | not run: {'timeout'} |
| antropy (8) | 8 | 26,095.73 | 25,787.45 | 326.197 | — | — | 963.3× | — |
| tsflex (7 stats) | — | — | — | — | — | — | — | — | not run: {'timeout'} |
| sktime Catch22 (22) | 22 | 21,198.58 | 23,388.98 | 96.357 | — | — | 782.5× | — |

## Per-distribution detail — 1,000 × 500

| Library | gaussian | random_walk | ar1 | heavy_tailed | sinusoid |
|---|---|---|---|---|---|
| Tsxtract core33 | 5.0 | 3.9 | 4.1 | 4.7 | 4.6 |
| catch22 (22) | 753.1 | 733.7 | 738.6 | 721.1 | 690.7 |
| TSFEL (156, README cfg) | 4,349.9 | 4,294.8 | 4,299.2 | 4,233.7 | 4,278.3 |
| tsfresh (777, e2e) | 19,537.4 | 19,071.4 | 19,316.1 | 19,487.9 | 19,154.7 |
| tsfresh (777, extract-only) | 19,758.5 | 19,508.9 | 18,354.7 | 19,698.6 | 18,359.9 |
| antropy (8) | 2,657.2 | 3,041.6 | 2,729.5 | 2,948.6 | 3,044.6 |
| tsflex (7 stats) | 4,163.7 | 4,152.0 | 4,108.2 | 4,169.6 | 4,233.6 |
| sktime Catch22 (22) | 2,476.7 | 4,383.3 | 2,509.8 | 3,076.5 | 2,226.7 |

## Per-distribution detail — 10,000 × 500

| Library | gaussian | random_walk | ar1 | heavy_tailed | sinusoid |
|---|---|---|---|---|---|
| Tsxtract core33 | 27.1 | 22.3 | 21.9 | 23.4 | 24.1 |
| catch22 (22) | 2,082.8 | 1,885.0 | 1,891.3 | 2,032.8 | 1,891.9 |
| TSFEL (156, README cfg) | 23,508.8 | 22,618.5 | 22,211.2 | 22,151.3 | 22,391.6 |
| tsfresh (777, e2e) | **timeout** | **timeout** | **timeout** | **timeout** | **timeout** |
| tsfresh (777, extract-only) | **timeout** | **timeout** | **timeout** | **timeout** | **timeout** |
| antropy (8) | 26,189.4 | **timeout** | 26,095.7 | **timeout** | **timeout** |
| tsflex (7 stats) | **timeout** | **timeout** | **timeout** | **timeout** | **timeout** |
| sktime Catch22 (22) | 23,389.0 | 42,925.2 | 24,213.8 | 29,662.8 | 21,198.6 |

## Explicit timeout / error rows (no silent skips)

| Library | Case | dist | Status | Detail |
|---|---|---|---|---|
| antropy (8) | 10,000×500 | heavy_tailed | timeout | TimeoutExpired: case exceeded 60s wall clock (recorded as explicit timeout row) |
| antropy (8) | 10,000×500 | random_walk | timeout | TimeoutExpired: case exceeded 60s wall clock (recorded as explicit timeout row) |
| antropy (8) | 10,000×500 | sinusoid | timeout | TimeoutExpired: case exceeded 60s wall clock (recorded as explicit timeout row) |
| tsflex (7 stats) | 10,000×500 | ar1 | timeout | TimeoutExpired: case exceeded 60s wall clock (recorded as explicit timeout row) |
| tsflex (7 stats) | 10,000×500 | gaussian | timeout | TimeoutExpired: case exceeded 60s wall clock (recorded as explicit timeout row) |
| tsflex (7 stats) | 10,000×500 | heavy_tailed | timeout | TimeoutExpired: case exceeded 60s wall clock (recorded as explicit timeout row) |
| tsflex (7 stats) | 10,000×500 | random_walk | timeout | TimeoutExpired: case exceeded 60s wall clock (recorded as explicit timeout row) |
| tsflex (7 stats) | 10,000×500 | sinusoid | timeout | TimeoutExpired: case exceeded 60s wall clock (recorded as explicit timeout row) |
| tsfresh (777, e2e) | 10,000×500 | ar1 | timeout | TimeoutExpired: case exceeded 60s wall clock (recorded as explicit timeout row) |
| tsfresh (777, e2e) | 10,000×500 | gaussian | timeout | TimeoutExpired: case exceeded 60s wall clock (recorded as explicit timeout row) |
| tsfresh (777, e2e) | 10,000×500 | heavy_tailed | timeout | TimeoutExpired: case exceeded 60s wall clock (recorded as explicit timeout row) |
| tsfresh (777, e2e) | 10,000×500 | random_walk | timeout | TimeoutExpired: case exceeded 60s wall clock (recorded as explicit timeout row) |
| tsfresh (777, e2e) | 10,000×500 | sinusoid | timeout | TimeoutExpired: case exceeded 60s wall clock (recorded as explicit timeout row) |
| tsfresh (777, extract-only) | 10,000×500 | ar1 | timeout | TimeoutExpired: case exceeded 60s wall clock (recorded as explicit timeout row) |
| tsfresh (777, extract-only) | 10,000×500 | gaussian | timeout | TimeoutExpired: case exceeded 60s wall clock (recorded as explicit timeout row) |
| tsfresh (777, extract-only) | 10,000×500 | heavy_tailed | timeout | TimeoutExpired: case exceeded 60s wall clock (recorded as explicit timeout row) |
| tsfresh (777, extract-only) | 10,000×500 | random_walk | timeout | TimeoutExpired: case exceeded 60s wall clock (recorded as explicit timeout row) |
| tsfresh (777, extract-only) | 10,000×500 | sinusoid | timeout | TimeoutExpired: case exceeded 60s wall clock (recorded as explicit timeout row) |

## Methodology notes (equal tuning, documented)

- **catch22**: pycatch22 serial per-series loop; `multiprocessing.Pool(16)` variant is what runs at threads=16 (adapter default fast config).
- **TSFEL**: `get_features_by_domain()` (README 156-feature config), joblib `Parallel(n_jobs=16)`.
- **tsfresh**: `EfficientFCParameters` (README 777-feature config), `n_jobs=16`. End-to-end includes long-format DataFrame construction; extract-only builds the DataFrame outside the timed region (`variant=extract_only`).
- **Matched-feature runs**: only the 13 definition-agreed features per competitor (frozen in `benches/agreement/feature_map.json`); Tsxtract matched runs use the same 13 via the `features=` subset API.
- **antropy / tsflex / sktime**: included where installed; matched set vs core33 is empty (B1), so matched view is N/A.
- Per-case subprocess import overhead (numba/pandas/tsfresh) is *included* in competitor wall times — a conservative choice against Tsxtract.
- Dist aggregation in the per-shape tables reports the **best** dist median per library (worst-case vs Tsxtract); per-dist detail tables above give all five.
