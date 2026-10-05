# FAQ

## Install / names

**What do I install?** `pip install kymora`, then `import kymora`.
The distribution, import, crate, and repo are all one name now.

**What about `tsxtract` / `tsxtractor`?** Deleted old names — no shims, no
aliases. `import kymora` is the only spelling. (The bare `tsxtract` name on
PyPI is an unrelated JAX project; never install it expecting this library.)

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
