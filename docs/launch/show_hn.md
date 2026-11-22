# Show HN draft — Kymora (DO NOT POST YET; timing is an owner decision)

Title: Show HN: Kymora – batch time-series feature extraction with a Rust core

Body:

Kymora extracts 33 statistical, temporal, and spectral features from
batches of time series: one FFI crossing per batch, zero-copy NumPy
ingestion, GIL released, Rayon across series. Plus an O(1) streaming
engine for rolling windows, a scikit-learn transformer, and a documented
NaN contract.

Like-for-like numbers (each library restricted to definition-matched
features, parity-verified before timing; 1,000 × 500, i7-13620H/16
threads, pooled medians with 95% CIs):

- vs numba hand-rolled baseline (33 features): 6.0×
- vs numpy baseline (33 features): 165.1×
- vs TSFEL (13 features): 1,089.1×
- vs tsfresh (13 features): 2,812.4×

Limitations, stated plainly: these are single-machine exploratory numbers,
not fleet evidence. Kymora loses small-batch cases to numba (1.4×–1.8× at
1×100: fixed dispatch overhead dominates), thread scaling plateaus near
the physical core count, and skew/kurt on 1e9-offset series are
conditioning-limited in any implementation. The README has a "Where Kymora
is slower" section with every loss case.

Everything reproduces: `./reproduce.sh` regenerates every figure from a
clean checkout; claim→artifact map in CLAIMS.md.

`pip install kymora` — repo: https://github.com/Aamodx6/Kymora

Happy to answer anything about the streaming numerics (anchored power sums
+ drift guard) or the benchmark methodology.
