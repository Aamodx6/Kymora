# Kymora 0.8.0 — release notes (draft, do not publish yet)

Release prep only: no tag has been pushed and nothing is published.
Owner checklist lives in OWNER_DECISIONS.md (trusted-publisher setup,
tagging, launch timing).

## What changed

Numerics, feature names/order, and the NaN/error contracts are unchanged
(`feature_names()` sha256
`8a1e27942b370ec886130db4f19ca973b2a1b36ea17823723c9d7afd1431af2e`).
Full list in CHANGELOG.md. Highlights:

- Streaming fast tier is now genuinely O(1) per push/compute (anchored
  accumulators, drift guard), with a documented accuracy contract and a
  complexity table in `docs/streaming.md`.
- New input options: `nan_policy="raise"`, `contiguous="copy"`,
  multichannel lists of 2D arrays, window size 1 streaming.
- `kymora.sklearn.KymoraTransformer` ships in the package (optional
  `kymora[sklearn]`), passing the full sklearn estimator-check suite;
  verified sktime adapter example included.
- Three FFI-crossing panics and two silent-wrong paths eliminated (all now
  `ValueError` or exact); see CHANGELOG Fixed section.
- Numerically-degenerate windows (1-ulp scale) now yield NaN for
  `skewness`/`kurtosis` in batch and streaming alike (scipy gh-15905
  parity); `nan_policy="raise"` does not fire on guard-produced NaN.
- Perf regression gate (`tools/perf_gate.py` + CI), generated feature
  catalog (`tools/gen_feature_docs.py` + CI), external parity suite,
  proptest/cargo-fuzz targets, cross-platform wheel-test CI.

## Numbers

Every figure traces to `benchmarks/results/` via CLAIMS.md. Headline
(equal-feature, like-for-like, 1,000 × 500, i7-13620H/16 threads):
kymora fastest on all 16 rows, 3.4×–1,693.8× depending on competitor.
Single-machine exploratory numbers; the "Where Kymora is slower" section
in the README lists every loss case.

## Upgrade notes

- `StreamingExtractor(1)` (window size 1) is now accepted (was
  `ValueError`); diff-based features are NaN exactly where batch leaves
  them undefined on length-1 input.
- `StreamingExtractor.push` returns `bool` as before but may now raise
  `ValueError` when constructed with `nan_policy="raise"` and fed NaN.
- New optional parameters everywhere (`nan_policy`, `contiguous`,
  `anchor_interval`, `precision` validation, `out_dtype`): all default to
  previous behavior.
- `pip install kymora[all]` pulls pandas, polars, and scikit-learn.
