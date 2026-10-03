---
title: "FAQ & Troubleshooting"
description: "Frequently asked questions, common error diagnostics, and practical solutions for Tsxtract."
order: 13
section: "Help"
---

Short answers to the questions that recur in issues and integrations. Each answer links to the authoritative page, and every fix below is runnable as written.

```python
import numpy as np
import tsxtractor
print(tsxtractor.__version__, len(tsxtractor.feature_names()))
```

```text
0.3.0 33
```

## Errors and inputs

### Why does `extract_features()` raise `TypeError` on my integer array?

- **Cause:** the zero-copy core accepts float64 buffers only and refuses to silently copy or reinterpret other dtypes.
- **Fix:** convert once upstream with `X.astype(np.float64)` and keep that buffer for all calls.

```python
X = np.ascontiguousarray(np.arange(20.0).reshape(2, 10).astype(np.int64).astype(np.float64))
print(tsxtractor.extract_features(X).shape)
```

```text
(2, 33)
```

### Why does a sliced view raise `ValueError` about contiguity?

- **Cause:** strided views such as `X[:, ::2]` have no single flat address range, so they cannot be borrowed without a copy.
- **Fix:** pass the slice through `np.ascontiguousarray()` first.

### Why is my whole row NaN when only one sample is missing?

- **Cause:** the NaN contract poisons all 33 features of any series containing a NaN, by design and under test.
- **Fix:** impute or drop missing samples before extraction when partial features are required.

### Do infinite values behave like NaN?

- **Answer:** no. `inf` is an ordinary float64 that flows through arithmetic — it never raises and never triggers the all-NaN row.
- **Example:** a series containing `inf` still computes, with affected statistics such as `max` reporting `inf`.

### Why does an empty series raise instead of returning NaNs?

- **Cause:** zero-length input is a structural error (`TsxError::EmptySeries`), not a value condition, and the error names the offending batch index.
- **Fix:** filter zero-length recordings before the call; length 1 remains legal.

### What window and stride values are legal for `sliding_features()`?

- **Rules:** `window >= 1`, `stride >= 1`, and `window <= len(X)`; `stride` defaults to `1` and `window == len(X)` is legal.
- **Counts:** rows follow `(len(X) - window) // stride + 1`, so `x` of length 50 with `window=10, stride=10` yields 5 rows.

## Performance and scope

### Why is one short series no faster than NumPy?

- **Cause:** Rayon parallelizes across the series (or window) dimension, so a single series uses one worker by construction.
- **Fix:** batch many series per call, or convert one long recording with `sliding_features()` to create a parallel dimension.

### Can I add a custom 34th feature?

- **Answer:** no plugin hook exists; the registry in `src/features/mod.rs` is intentionally closed.
- **Path:** open a New feature proposal issue first per `CONTRIBUTING.md`; unagreed PRs may close on scope regardless of quality.

### Does Tsxtract run on GPUs or in R/Julia/MATLAB?

- **Answer:** neither. The engine is CPU-only via Rayon, and bindings are Python-only.
- **Alternative:** `catch22` publishes multi-language bindings, and `arch.md` records GPU work as explicitly out of scope.

### How do I use Tsxtract with Polars?

- **Answer:** through an explicit NumPy bridge — Tsxtract ships no Polars-native function.
- **Pattern:** select value columns, convert with `.to_numpy()`, extract, and wrap back with `pl.DataFrame(feats, schema=tsxtractor.feature_names())`.

### Is `StreamingExtractor` output identical to batch output?

- **Answer:** yes to `rtol=1e-9` per `tests/test_streaming.py`, with re-anchoring every 4,096 steps bounding drift on endless streams.
- **Caveat:** `compute_features()` returns all NaN until the window fills, and `window_size` below 2 raises `ValueError`.

## Versions and stability

### Will column order change between releases?

- **Answer:** never within a major version. `feature_names()` order and length are public API.
- **Rule:** reordering, renaming, or removing a feature requires a major bump; appending at the end is a minor bump.

### Which versions introduced the current API?

- **Summary:** `0.1.0` shipped the 33 features on Windows only; `0.2.0` added wheels for Linux/macOS, `extract_features_df()`, `__version__`, stubs, validation, and the NaN contract; `0.2.1` fixed packaging only; `0.3.0` made extraction about 1.8x faster with identical values.
- **Detail:** see the full per-release record in [Changelog](/docs/changelog).

### Where do I report a wrong value?

- **Requirement:** include OS, Python version, `tsxtractor.__version__`, a runnable snippet, and the expected value with its NumPy/SciPy expression.
- **Reason:** that expression converts directly into a reference test, which is the fastest path to a fix.

## See also

Deeper coverage behind each answer:

- [Core Concepts](/docs/core-concepts) — input rules and the NaN contract.
- [Large Datasets & Streaming](/docs/large-datasets) — chunking and streaming patterns.
- [Changelog](/docs/changelog) — what each version changed.
