"""Out-of-core and chunked feature extraction for large-scale time series.

Provides ``extract_features_chunked`` to process datasets exceeding available RAM
in streaming batches across disk formats (Parquet, CSV, NPY memmap) or in-memory
iterators.
"""

from __future__ import annotations

import os
from typing import TYPE_CHECKING, Any, Iterator, Sequence

import numpy as np

from ._core import extract_features, feature_names

if TYPE_CHECKING:  # pragma: no cover
    import pandas as pd
    import polars as pl


def extract_features_chunked(
    source: Any,
    chunk_size: int = 1000,
    profile: str | None = None,
    features: Sequence[str] | None = None,
    n_jobs: int | None = None,
    views: Sequence[str] | None = None,
    nan_policy: str | None = None,
    contiguous: str | None = None,
    as_df: bool = False,
    as_polars: bool = False,
) -> Iterator[Any]:
    """Extract features in chunks to minimize memory usage on large datasets.

    Accepts:
      - 2D numpy arrays or memory-mapped files (np.memmap)
      - File paths (str or Path) to .parquet, .csv, or .npy files
      - Python iterables / generators yielding 1D series

    Args:
        source: Array, iterable, or file path.
        chunk_size: Number of series per chunk (default 1000).
        profile: Feature profile name ("core33", "minimal", "extended", "full").
        features: Optional explicit list of feature names.
        n_jobs: Number of worker threads (default None = all cores).
        views: Optional list of view names.
        nan_policy: "propagate" (default) or "raise".
        contiguous: "error" (default) or "copy".
        as_df: If True, yield chunks as labeled pandas DataFrames.
        as_polars: If True, yield chunks as labeled polars DataFrames.

    Yields:
        Extracted features for each chunk (numpy.ndarray, pd.DataFrame, or pl.DataFrame).
    """
    if chunk_size <= 0:
        raise ValueError(f"chunk_size must be positive, got {chunk_size}")

    cols: list[str] | None = None
    if as_df or as_polars:
        cols = feature_names(profile=profile, features=features, views=views)

    def _wrap(vals: np.ndarray) -> Any:
        if as_polars:
            try:
                import polars as pl
                return pl.from_numpy(vals, schema=cols)
            except ImportError as exc:
                raise ImportError(
                    'as_polars=True requires polars: pip install "kymora[polars]"'
                ) from exc
        elif as_df:
            try:
                import pandas as pd
                return pd.DataFrame(vals, columns=cols)
            except ImportError as exc:
                raise ImportError(
                    'as_df=True requires pandas: pip install "kymora[pandas]"'
                ) from exc
        return vals

    # 1. Source is a file path string or os.PathLike
    if isinstance(source, (str, os.PathLike)):
        path_str = os.fspath(source)
        ext = os.path.splitext(path_str)[1].lower()

        if ext == ".npy":
            mmap = np.load(path_str, mmap_mode="r")
            n_rows = mmap.shape[0]
            for start in range(0, n_rows, chunk_size):
                chunk = np.ascontiguousarray(mmap[start : start + chunk_size], dtype=np.float64)
                out = extract_features(
                    chunk,
                    profile=profile,
                    features=features,
                    n_jobs=n_jobs,
                    views=views,
                    nan_policy=nan_policy,
                    contiguous=contiguous,
                )
                yield _wrap(out)
            return

        elif ext == ".parquet":
            try:
                import pyarrow.parquet as pq
            except ImportError as exc:
                raise ImportError(
                    "Parquet chunked extraction requires pyarrow: pip install pyarrow"
                ) from exc

            pf = pq.ParquetFile(path_str)
            for batch in pf.iter_batches(batch_size=chunk_size):
                df_batch = batch.to_pandas()
                arr = np.ascontiguousarray(df_batch.to_numpy(), dtype=np.float64)
                out = extract_features(
                    arr,
                    profile=profile,
                    features=features,
                    n_jobs=n_jobs,
                    views=views,
                    nan_policy=nan_policy,
                    contiguous=contiguous,
                )
                yield _wrap(out)
            return

        elif ext == ".csv":
            try:
                import pandas as pd
            except ImportError as exc:
                raise ImportError(
                    "CSV chunked extraction requires pandas: pip install pandas"
                ) from exc

            for chunk_df in pd.read_csv(path_str, chunksize=chunk_size, header=None):
                arr = np.ascontiguousarray(chunk_df.to_numpy(), dtype=np.float64)
                out = extract_features(
                    arr,
                    profile=profile,
                    features=features,
                    n_jobs=n_jobs,
                    views=views,
                    nan_policy=nan_policy,
                    contiguous=contiguous,
                )
                yield _wrap(out)
            return
        else:
            raise ValueError(f"Unsupported file format '{ext}'. Supported: .parquet, .csv, .npy")

    # 2. Source is an in-memory 2D array or array-like
    if hasattr(source, "shape") and len(getattr(source, "shape")) == 2:
        n_rows = source.shape[0]
        for start in range(0, n_rows, chunk_size):
            chunk = np.ascontiguousarray(source[start : start + chunk_size], dtype=np.float64)
            out = extract_features(
                chunk,
                profile=profile,
                features=features,
                n_jobs=n_jobs,
                views=views,
                nan_policy=nan_policy,
                contiguous=contiguous,
            )
            yield _wrap(out)
        return

    # 3. Source is an iterable / generator of series
    buffer: list[np.ndarray] = []
    for item in source:
        arr = np.ascontiguousarray(item, dtype=np.float64)
        buffer.append(arr)
        if len(buffer) == chunk_size:
            out = extract_features(
                buffer,
                profile=profile,
                features=features,
                n_jobs=n_jobs,
                views=views,
                nan_policy=nan_policy,
                contiguous=contiguous,
            )
            yield _wrap(out)
            buffer = []

    if buffer:
        out = extract_features(
            buffer,
            profile=profile,
            features=features,
            n_jobs=n_jobs,
            views=views,
            nan_policy=nan_policy,
            contiguous=contiguous,
        )
        yield _wrap(out)
