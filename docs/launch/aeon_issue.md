# aeon integration issue draft (file against aeon when ready — owner timing)

Title: [ENH] kymora-backed feature transformer? (third-party adapter available)

Body:

Kymora (Rust-core batch time-series feature extraction,
https://github.com/Aamodx6/Kymora, MIT) computes 33 features over panels
at ~3 ms per 1,000 × 500 on a laptop CPU (equal-feature vs tsfresh
1,694× on matched definitions; artifacts in our repo, single-machine
numbers).

We ship a tested sktime `BaseTransformer` adapter
(`docs/examples/sktime_adapter.py`, panel→primitives). Since aeon shares
that interface lineage: would a corresponding aeon-side adapter be welcome
as a third-party integration, and are there aeon-specific conventions
(mtypes, tags, testing) it should follow? We have not tested against aeon
yet and will not claim compatibility until we do.

No vendoring requested — the adapter stays on our side; this is purely a
conventions question.
