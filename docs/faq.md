# FAQ

## Install / names

**What do I install?** `pip install kymora`, then `import kymora`.
The distribution, import, crate, and repo are all one name now.

**What about `tsxtract` / `tsxtractor`?** Old names. `import tsxtract`
still works as a deprecated shim (removal ≥ 0.8.0); `tsxtractor` was
deleted. The bare `tsxtract` name on PyPI belongs to an unrelated JAX
project — never install it alongside this package.

**Which Python versions?** 3.10–3.13, via prebuilt wheels (no Rust needed).
See [Install](install.md).

## Stability

**Is `feature_names()` order stable?** Yes — order and length are public
API. Reordering or removing a feature is a major-version change.

**What happens on NaN / bad input?** NaN is a value (row-wide propagation);
structural problems raise `ValueError`/`TypeError`. See
[NaN policy](nan-policy.md).

## Performance

**What do the headline numbers mean?** `core33` medians from the committed
F1 artifact on one laptop (exploratory — hardware and threads are always
stated beside a number). Every published number traces to an artifact via
[CLAIMS.md](https://github.com/Aamodx6/Kymora/blob/main/CLAIMS.md). Numbers marked † are pending re-baseline.

**When should I *not* use this?** See
[When not to use this](index.md#when-not-to-use-this).
