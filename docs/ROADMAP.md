# Roadmap — quarantined experiments

Two uncalled Zenith-session prototypes were removed from `main`
(`refactor/tsxtract`) and preserved on experiment branches. They are **not
deleted**; they are **not wired**. Revival is gated on measurement per
`arch.md` — "decide, then build".

## experiment/spin-pool — persistent spin-then-park pool (NEEDS-OWNER #7)

- Contents: `src/pool.rs` (222 lines) as of `f7282a0`; was declared as
  `pub mod pool` in `src/lib.rs` with **zero callers**. `TSXTRACT_POOL`
  is read by nothing; `tune.py`'s pool dimension benchmarks variants of
  a backend that does not exist (recorded as provisional in
  `docs/api.md`).
- Revival gate — **arch.md Z6** (§10): re-baseline shows parallel
  efficiency η < 0.85 at (1k×500), **or** rayon wake/steal dominates the
  flamegraph. On revival, Z6 also requires: `TSXTRACT_POOL=rayon`
  fallback, panics converted to `TsxError`, loom/stress tests + env
  switch (arch.md §12 pool row), and the §9.4 stop rule (stop after two
  consecutive attempts each gaining <3% end-to-end).
- Revive with: `git checkout experiment/spin-pool -- src/pool.rs`, then
  wire + measure. Until then, `tune()` pool recommendations stay void.

## experiment/soa-4x — lane-batched SoA kernels (NEEDS-OWNER #8)

- Contents as of `f7282a0`:
  - SoA quartet `aos_to_soa_4x` / `pass1_soa_4x` / `pass2_soa_4x` /
    `autocorr_soa_4x` (`src/kernels/reduce.rs:821–1153`), **zero callers**;
  - `run_core33_f32_out32` (`src/pipeline.rs:252–260`), **zero callers**.
  - None of the above is parity-tested (`tests/` has zero references) and
    no benchmark demonstrates the ≥10% end-to-end gain that would have kept
    it on main behind a feature flag — so it moved here instead.
- Revival gate — **arch.md Z2** (§10): re-baseline shows
  fused+ACF+perm > 30% of per-series time **after Z1/Z3 land**;
  equal-length batches only; `L·n·8 B ≤ ~16 KB`. Plus the standing bars:
  ≥10% end-to-end gain for mainline inclusion, §9.4 stop rule.
- Revive with: `git show experiment/soa-4x:src/kernels/reduce.rs` (lines
  821–1153) and `git show experiment/soa-4x:src/pipeline.rs` (lines
  252–260), then parity-test against NumPy references *before* wiring
  (§14 claims policy applies to the revival PR too).
