# Equal-Feature Benchmark Report (F2)

**Generated:** 2026-10-05 12:51:02
**Subset:** definition-agreed features per competitor (frozen Phase B1 parity: TSFEL 13, tsfresh 13, numba 33, numpy 33; catch22 excluded — no definition-agreed features).
**Parity gate:** `parity` mode re-verifies numeric agreement before timing (per-feature rel err, EXACT <=1e-9 / CLOSE <=1e-5).
**Protocol:** interleaved rounds (kymora, competitor alternating), pooled medians, 95% bootstrap CI on the ratio, GC disabled, warmup, single machine (i7-13620H laptop, 10 cores / 16 threads, Windows 11) — exploratory, not fleet evidence.

## Shape 100 × 50,000 (equal features per row)

| Competitor | Equal features | Kymora med (ms) | Competitor med (ms) | Ratio (comp/kymora) | 95% CI |
|---|---:|---:|---:|---:|---|
| numba | 33 | 37.721 | 326.591 | 8.7x | [8.2, 9.0] |
| numpy | 33 | 36.477 | 2426.515 | 66.5x | [62.3, 70.3] |
| tsfel | 13 | 30.755 | 586.788 | 19.1x | [18.1, 19.7] |
| tsfresh | 13 | 42.540 | 10630.155 | 249.9x | [227.1, 302.0] |

## Shape 1,000 × 500 (equal features per row)

| Competitor | Equal features | Kymora med (ms) | Competitor med (ms) | Ratio (comp/kymora) | 95% CI |
|---|---:|---:|---:|---:|---|
| numba | 33 | 4.719 | 16.045 | 3.4x | [3.1, 3.9] |
| numpy | 33 | 4.679 | 285.501 | 61.0x | [60.0, 62.0] |
| tsfel | 13 | 3.921 | 2213.688 | 564.6x | [509.7, 781.4] |
| tsfresh | 13 | 4.935 | 8359.452 | 1693.8x | [1645.5, 1900.1] |

## Shape 1,000 × 5,000 (equal features per row)

| Competitor | Equal features | Kymora med (ms) | Competitor med (ms) | Ratio (comp/kymora) | 95% CI |
|---|---:|---:|---:|---:|---|
| numba | 33 | 23.710 | 262.359 | 11.1x | [10.8, 11.4] |
| numpy | 33 | 22.823 | 2659.069 | 116.5x | [111.7, 119.3] |
| tsfel | 13 | 17.787 | 2571.439 | 144.6x | [142.7, 149.1] |
| tsfresh | 13 | 22.652 | 10392.383 | 458.8x | [435.8, 486.5] |

## Shape 10,000 × 500 (equal features per row)

| Competitor | Equal features | Kymora med (ms) | Competitor med (ms) | Ratio (comp/kymora) | 95% CI |
|---|---:|---:|---:|---:|---|
| numba | 33 | 24.241 | 143.386 | 5.9x | [5.5, 6.1] |
| numpy | 33 | 23.886 | 2918.605 | 122.2x | [118.5, 123.4] |
| tsfel | 13 | 21.641 | 24900.456 | 1150.6x | [962.7, 1383.2] |
| tsfresh | 13 | 25.802 | 11367.040 | 440.6x | [424.0, 457.3] |

## What this table does and does not show

- **Shows:** wall-clock to extract *the same, definition-agreed feature subset* — the closest thing to an equal-work comparison.
- **Does not show:** each library's full default catalog (see the raw-time table for that), feature quality/coverage differences, or multi-machine variance.
- Kymora's subset runs through the same fused core33 pipeline; competitors run their own matched-config extractors at their best documented tuning.

Reproduce: `python benchmarks/suites/equal_feature.py parity && python benchmarks/suites/equal_feature.py bench`
