# r/rust draft (DO NOT POST YET)

Title: Kymora: PyO3 time-series feature extraction — anchored streaming accumulators, strict FFI boundary

Body:

Kymora's compute core is Rust behind a PyO3 boundary, and the interesting
bits are the constraints it operates under:

- **Numeric logic lives only in Rust** (`src/features/`); Python is a
  pass-through. No panics cross the FFI (one `KymoraError → PyErr`
  conversion point; `unsafe` confined to two audited buffer helpers).
- **Streaming without cancellation**: rolling-window moments use anchored
  shifted power sums with a drift guard (re-anchor past 0.25σ drift), so
  `compute(kind="fast")` is O(1) and matches batch output within 1e-9 —
  including on 1e9-offset series where raw power sums lose everything.
- **Layout strictness as a feature**: the boundary rejects Fortran/strided
  input instead of silently transposing it (we found and fixed two
  silent-wrong paths this release via the strictness gate), with an
  explicit `contiguous="copy"` opt-in.
- **Frozen goldens**: 33-column output is byte-tested against committed
  artifacts; property tests + proptest fuzz + cargo-fuzz targets guard the
  boundary.

Throughput comes from boring wins: one FFI crossing per batch, fused
passes, shared intermediates, Rayon across series. Thread-pool
construction per call (~200 µs) turned out to dominate small calls, so
pools are now cached per thread count.

Matched-feature numbers (1,000 × 500, i7-13620H/16 threads): 3.4× vs
numba, 61× vs numpy, 565× vs TSFEL, 1,694× vs tsfresh — all like-for-like,
parity-gated, in `benchmarks/results/` with a claim→artifact map.

Repo: https://github.com/Aamodx6/Kymora (`pip install kymora`, abi3
wheels). Genuinely interested in criticism of the FFI boundary design.
