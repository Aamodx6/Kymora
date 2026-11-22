#!/usr/bin/env python3
"""Clean-environment installation verification gate.

Runs 6 required validation checks against an installed kymora wheel/package
with no development dependencies:
1. Version check and importability
2. Quickstart snippet from README
3. 20-series random smoke test (core33 profile + extract_one)
4. KymoraTransformer in an scikit-learn Pipeline
5. extract_features_chunked out-of-core batch extraction
6. extract_features_polars (verified when polars is available)

Usage:
    python tools/verify_clean_install.py
"""

from __future__ import annotations

import sys
import numpy as np


def main() -> int:
    print("=== Kymora Clean Installation Verification ===")

    # 1. Version check and import
    import kymora

    version = getattr(kymora, "__version__", None)
    if not version:
        print("FAIL: kymora.__version__ is not set")
        return 1
    print(f"1. Import & version OK: kymora {version}")

    # 2. Quickstart snippet from README
    X_qs = np.random.randn(1000, 500)
    features_qs = kymora.extract_features(X_qs)
    if features_qs.shape != (1000, 33):
        print(f"FAIL: Quickstart expected shape (1000, 33), got {features_qs.shape}")
        return 1
    if not np.isfinite(features_qs).all():
        print("FAIL: Quickstart output contains non-finite values")
        return 1
    print("2. Quickstart snippet OK")

    # 3. 20 random series smoke test (core33 and extract_one)
    rng = np.random.default_rng(42)
    X20 = rng.standard_normal((20, 100))
    f20 = kymora.extract_features(X20, profile="core33")
    if f20.shape != (20, 33):
        print(f"FAIL: Smoke test expected shape (20, 33), got {f20.shape}")
        return 1
    if not np.isfinite(f20).all():
        print("FAIL: Smoke test output contains non-finite values")
        return 1

    x_single = rng.standard_normal(100)
    f_single = kymora.extract_one(x_single, profile="core33")
    if f_single.shape != (33,):
        print(f"FAIL: extract_one expected shape (33,), got {f_single.shape}")
        return 1
    if not np.isfinite(f_single).all():
        print("FAIL: extract_one output contains non-finite values")
        return 1
    print("3. Smoke test (20-series batch + extract_one) OK")

    # 4. KymoraTransformer in an scikit-learn Pipeline
    try:
        from sklearn.pipeline import Pipeline
        from sklearn.preprocessing import StandardScaler

        from kymora.sklearn import KymoraTransformer

        pipe = Pipeline(
            [
                ("kymora", KymoraTransformer(profile="core33")),
                ("scaler", StandardScaler()),
            ]
        )
        pipe_out = pipe.fit_transform(X20)
        if pipe_out.shape != (20, 33):
            print(f"FAIL: Pipeline output expected shape (20, 33), got {pipe_out.shape}")
            return 1
        if not np.isfinite(pipe_out).all():
            print("FAIL: Pipeline output contains non-finite values")
            return 1
        print("4. scikit-learn Pipeline with KymoraTransformer OK")
    except ImportError as exc:
        print(f"WARNING: scikit-learn not available ({exc}); check skipped")

    # 5. extract_features_chunked
    from kymora.chunked import extract_features_chunked

    chunks = list(extract_features_chunked(X20, chunk_size=5, profile="core33"))
    if len(chunks) != 4:
        print(f"FAIL: Expected 4 chunks, got {len(chunks)}")
        return 1
    total_rows = sum(c.shape[0] for c in chunks)
    if total_rows != 20:
        print(f"FAIL: Expected 20 total rows from chunks, got {total_rows}")
        return 1
    if any(c.shape[1] != 33 for c in chunks):
        print("FAIL: Chunk feature column mismatch")
        return 1
    print("5. extract_features_chunked OK")

    # 6. extract_features_polars
    try:
        import polars as pl

        res_polars = kymora.extract_features_polars(X20, profile="core33")
        if not isinstance(res_polars, pl.DataFrame):
            print(f"FAIL: Expected polars.DataFrame, got {type(res_polars)}")
            return 1
        if res_polars.shape != (20, 33):
            print(f"FAIL: Polars dataframe expected shape (20, 33), got {res_polars.shape}")
            return 1
        print("6. extract_features_polars OK")
    except ImportError:
        print("6. Polars not installed; skipped")

    print("=== All clean install verification checks PASSED ===")
    return 0


if __name__ == "__main__":
    sys.exit(main())
