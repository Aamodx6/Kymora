"""Tests for StreamingExtractor."""

import numpy as np
import pytest
import kymora


def test_streaming_extractor_basic():
    w = 16
    extractor = kymora.StreamingExtractor(w)
    assert extractor.window_size == w
    assert not extractor.is_full

    x = np.sin(np.linspace(0, 10, 50))
    for i, val in enumerate(x):
        ready = extractor.push(float(val))
        if i < w - 1:
            assert not ready
            assert not extractor.is_full
        else:
            assert ready
            assert extractor.is_full
            feats = extractor.compute_features()
            assert len(feats) == 33
            assert np.all(np.isfinite(feats))

    # Compare with sliding_features on the same window
    window_slice = x[-w:]
    batch_feat = kymora.extract_features(window_slice.reshape(1, -1))[0]
    stream_feat = extractor.compute_features()

    for k, name in enumerate(kymora.feature_names()):
        if np.isnan(batch_feat[k]):
            assert np.isnan(stream_feat[k]), f"Feature {name} should be NaN"
        else:
            np.testing.assert_allclose(
                stream_feat[k],
                batch_feat[k],
                rtol=1e-9,
                atol=1e-9,
                err_msg=f"Feature {name} mismatch",
            )


def test_streaming_extractor_reset():
    extractor = kymora.StreamingExtractor(5)
    for i in range(5):
        extractor.push(float(i))
    assert extractor.is_full

    extractor.reset()
    assert not extractor.is_full
    assert extractor.push(1.0) is False


def test_streaming_extractor_invalid():
    with pytest.raises(ValueError):
        kymora.StreamingExtractor(1)
