# Equal-Feature Benchmark Report (F2)

**Generated:** 2026-11-22 10:26:34
**Subset:** definition-agreed features per competitor (frozen Phase B1 parity: TSFEL 13, tsfresh 13, numba 33, numpy 33; catch22 excluded — no definition-agreed features).
**Parity gate:** `parity` mode re-verifies numeric agreement before timing (per-feature rel err, EXACT <=1e-9 / CLOSE <=1e-5).
**Protocol:** interleaved rounds (kymora, competitor alternating), pooled medians, 95% bootstrap CI on the ratio, GC disabled, warmup, single machine (i7-13620H laptop, 10 cores / 16 threads, Windows 11) — exploratory, not fleet evidence.

## Shape 100 × 50,000 (equal features per row)

| Competitor | Equal features | Kymora med (ms) | Competitor med (ms) | Ratio (comp/kymora) | 95% CI |
|---|---:|---:|---:|---:|---|
| numba | 33 | 32.733 | 300.895 | 9.2x | [8.8, 9.5] |
| numpy | 33 | 30.773 | 3319.905 | 107.9x | [105.5, 109.5] |
| tsfel | 13 | 23.457 | 834.030 | 35.6x | [35.1, 35.9] |
| tsfresh | 13 | 32.337 | 8183.778 | 253.1x | [242.4, 263.0] |

## Shape 1,000 × 500 (equal features per row)

| Competitor | Equal features | Kymora med (ms) | Competitor med (ms) | Ratio (comp/kymora) | 95% CI |
|---|---:|---:|---:|---:|---|
| numba | 33 | 2.238 | 13.343 | 6.0x | [5.7, 6.5] |
| numpy | 33 | 2.188 | 361.335 | 165.1x | [157.2, 170.5] |
| tsfel | 13 | 1.970 | 2145.726 | 1089.1x | [1007.3, 1132.2] |
| tsfresh | 13 | 2.340 | 6580.569 | 2812.4x | [2584.3, 2914.1] |

## Shape 1,000 × 5,000 (equal features per row)

| Competitor | Equal features | Kymora med (ms) | Competitor med (ms) | Ratio (comp/kymora) | 95% CI |
|---|---:|---:|---:|---:|---|
| numba | 33 | 18.118 | 213.594 | 11.8x | [11.3, 12.0] |
| numpy | 33 | 17.165 | 3347.943 | 195.0x | [190.0, 199.8] |
| tsfel | 13 | 13.088 | 2732.725 | 208.8x | [206.2, 211.2] |
| tsfresh | 13 | 16.860 | 8198.944 | 486.3x | [466.3, 504.6] |

## Shape 10,000 × 500 (equal features per row)

| Competitor | Equal features | Kymora med (ms) | Competitor med (ms) | Ratio (comp/kymora) | 95% CI |
|---|---:|---:|---:|---:|---|
| numba | 33 | 19.285 | 120.581 | 6.3x | [6.0, 6.3] |
| numpy | 33 | 17.755 | 3537.498 | 199.2x | [186.2, 204.1] |
| tsfel | 13 | 15.894 | 21758.623 | 1369.0x | [1311.3, 1389.4] |
| tsfresh | 13 | 20.516 | 9435.006 | 459.9x | [447.5, 484.8] |

## What this table does and does not show

- **Shows:** wall-clock to extract *the same, definition-agreed feature subset* — the closest thing to an equal-work comparison.
- **Does not show:** each library's full default catalog (see the raw-time table for that), feature quality/coverage differences, or multi-machine variance.
- Kymora's subset runs through the same fused core33 pipeline; competitors run their own matched-config extractors at their best documented tuning.

Reproduce: `python benchmarks/suites/equal_feature.py parity && python benchmarks/suites/equal_feature.py bench`
