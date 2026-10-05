# sktime integration issue draft (file against sktime when ready — owner timing)

Title: [ENH] Native kymora panel transformer? (third-party adapter available)

Body:

Kymora (Rust-core batch time-series feature extraction,
https://github.com/Aamodx6/Kymora, MIT) ships a thin adapter example
(`docs/examples/sktime_adapter.py`): a `BaseTransformer` taking univariate
or multivariate panels (`numpy3D`) to Primitives via `extract_features` /
`extract_features_mc`, verified against sktime 1.2.0 in our test suite.

Question for maintainers: is there interest in (a) listing it as a
third-party transformer, or (b) guidance on the preferred panel→primitives
pattern we should follow? Our current tags:

- `scitype:transform-input: Panel`, `scitype:transform-output: Primitives`
- `X_inner_mtype: numpy3D`, `capability:multivariate: True`,
  `capability:missing_values: False`, `capability:unequal_length: False`,
  `fit_is_empty: True`

Happy to adapt the adapter to whatever conventions you prefer. No vendoring
requested — the adapter stays on our side.
