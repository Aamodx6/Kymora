import tempfile
from pathlib import Path
import numpy as np
import pytest
import kymora as km


def test_chunked_array():
    X = np.random.randn(25, 50)
    chunks = list(km.extract_features_chunked(X, chunk_size=10))
    assert len(chunks) == 3
    assert chunks[0].shape == (10, 33)
    assert chunks[1].shape == (10, 33)
    assert chunks[2].shape == (5, 33)

    # Parity with non-chunked
    direct = km.extract_features(X)
    concatenated = np.vstack(chunks)
    np.testing.assert_allclose(concatenated, direct)


def test_chunked_iterable():
    series_list = [np.random.randn(50) for _ in range(15)]
    chunks = list(km.extract_features_chunked(iter(series_list), chunk_size=5))
    assert len(chunks) == 3
    assert all(c.shape == (5, 33) for c in chunks)


def test_chunked_npy():
    with tempfile.TemporaryDirectory() as tmpdir:
        path = Path(tmpdir) / "test.npy"
        X = np.random.randn(20, 40)
        np.save(path, X)

        chunks = list(km.extract_features_chunked(path, chunk_size=8))
        assert len(chunks) == 3
        assert chunks[0].shape == (8, 33)
        assert chunks[1].shape == (8, 33)
        assert chunks[2].shape == (4, 33)

        direct = km.extract_features(X)
        concatenated = np.vstack(chunks)
        np.testing.assert_allclose(concatenated, direct)


def test_chunked_csv_and_parquet():
    import pandas as pd

    with tempfile.TemporaryDirectory() as tmpdir:
        X = np.random.randn(24, 30)
        df = pd.DataFrame(X)

        # CSV test
        csv_path = Path(tmpdir) / "data.csv"
        df.to_csv(csv_path, header=False, index=False)
        csv_chunks = list(km.extract_features_chunked(csv_path, chunk_size=10))
        assert len(csv_chunks) == 3
        np.testing.assert_allclose(np.vstack(csv_chunks), km.extract_features(X))

        # Parquet test
        pq_path = Path(tmpdir) / "data.parquet"
        df.to_parquet(pq_path, index=False)
        pq_chunks = list(km.extract_features_chunked(pq_path, chunk_size=10))
        assert len(pq_chunks) == 3
        np.testing.assert_allclose(np.vstack(pq_chunks), km.extract_features(X))

        # Polars output test
        pl_chunks = list(km.extract_features_chunked(X, chunk_size=10, as_polars=True))
        assert len(pl_chunks) == 3
        import polars as pl
        assert isinstance(pl_chunks[0], pl.DataFrame)
        assert pl_chunks[0].shape == (10, 33)


def test_chunked_invalid():
    with pytest.raises(ValueError, match="chunk_size must be positive"):
        list(km.extract_features_chunked(np.zeros((5, 10)), chunk_size=0))

    with pytest.raises(ValueError, match="Unsupported file format"):
        list(km.extract_features_chunked("dummy.txt"))
