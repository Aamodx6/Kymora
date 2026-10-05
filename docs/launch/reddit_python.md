# r/Python draft (DO NOT POST YET)

Title: Kymora 0.8.0: batch time-series feature extraction with a Rust core (3.4×–1,694× on matched features)

Body:

I maintain Kymora, a time-series feature extraction library with a Rust
core (PyO3/maturin) and a thin Python API. `extract_features` takes a
`(n_series, length)` array and returns 33 features per row — zero-copy
ingest, GIL released, parallel across series.

```python
import numpy as np, kymora
X = np.random.randn(1000, 500)
feats = kymora.extract_features(X)          # (1000, 33)
df = kymora.extract_features_df(X)          # labeled columns

from kymora.sklearn import KymoraTransformer  # pip install kymora[sklearn]
from sklearn.pipeline import Pipeline
pipe = Pipeline([("feat", KymoraTransformer()), ("clf", ...)])
```

What it does: curated 33-feature bank (frozen order), wider
extended/full profiles, O(1) streaming engine (`StreamingExtractor`),
multichannel input, NaN-in → NaN-row contract, `nan_policy="raise"` and
`contiguous="copy"` opt-ins.

Equal-feature results (only identically-defined features timed,
1,000 × 500, medians + 95% CIs): 3.4× vs a numba baseline, 61× vs numpy,
565× vs TSFEL, 1,694× vs tsfresh.

Limitations: single-machine numbers (reproduce with `./reproduce.sh`;
artifacts in `benchmarks/results/`); loses tiny-batch cases to numba;
scaling plateaus at physical cores; float32 covers core33-class features
only. All documented with artifacts in the repo.

Happy to take feedback on the API — especially the streaming and sklearn
integration.
