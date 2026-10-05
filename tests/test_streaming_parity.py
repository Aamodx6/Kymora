"""Streaming vs batch parity (Phase 2.3).

`StreamingExtractor.compute(kind="fast")` must match `extract_features` on the
same window within rtol 1e-9 (float64) across distributions, window sizes, and
degenerate inputs. Skewness/kurtosis on 1e9-offset windows carry a documented
absolute bound instead (batch-center conditioning; see docs/streaming.md and
`src/features/streaming.rs`).
"""

import numpy as np
import pytest
from hypothesis import HealthCheck, given, settings
from hypothesis import strategies as st

import kymora

FAST_NAMES = kymora.StreamingExtractor.fast_feature_names()
SKEW_KURT = {"skewness", "kurtosis"}

RTOL = 1e-9
# Absolute floor covers summation-residual noise on near-zero O(1)-scale
# features (observed max 1.3e-12: 2-point skew on O(100) random-walk data,
# where the batch center itself carries ~4e-14 error). Deterministic given
# fixed seeds, so the 1.5x margin is safe.
ATOL = 2e-12
# Absolute bound for skew/kurt streaming-vs-batch on 1e9-offset windows.
# Measured max 2.5e-6 over ~10k gaussian windows (W=50); Rust suite bound is
# 5e-6 over uniform noise. Both documented in docs/streaming.md.
OFFSET_SHAPE_BOUND = 1e-5
# Exact skew/kurt of any 2-point window (symmetric deviations): 0 and -2.
# Both implementations must sit near these; comparing them to each other
# would only measure whose center rounding is luckier.
TWO_POINT_EXACT = {"skewness": 0.0, "kurtosis": -2.0}
TWO_POINT_BOUND = 1e-4


def check_fast_matches_batch(data, window, offset_mode=False):
    """Push `data` through a fresh extractor, comparing every full window."""
    data = np.asarray(data, dtype=np.float64)
    w = window
    ext = kymora.StreamingExtractor(w)
    n_checked = 0
    for i, v in enumerate(data):
        ready = ext.push(float(v))
        if i + 1 < w:
            assert not ready
            assert np.all(np.isnan(ext.compute(kind="fast")))
            continue
        assert ready
        win = data[i - w + 1 : i + 1]
        got = ext.compute(kind="fast")
        want = kymora.extract_features(win[None, :], features=FAST_NAMES)[0]
        assert got.shape == want.shape
        for name, s, b in zip(FAST_NAMES, got, want):
            if np.isnan(b):
                assert np.isnan(s), f"{name}: batch NaN but stream {s}"
            elif window == 2 and name in TWO_POINT_EXACT:
                exact = TWO_POINT_EXACT[name]
                assert abs(s - exact) < TWO_POINT_BOUND, f"{name}: {s} vs {exact}"
                assert abs(b - exact) < TWO_POINT_BOUND, f"batch {name}: {b}"
            elif offset_mode and name in SKEW_KURT:
                assert abs(s - b) < OFFSET_SHAPE_BOUND, f"{name}: {s} vs {b}"
            else:
                np.testing.assert_allclose(
                    s, b, rtol=RTOL, atol=ATOL, err_msg=f"{name}: {s} vs {b}"
                )
        n_checked += 1
    assert n_checked == len(data) - w + 1
    return n_checked


@pytest.mark.parametrize("window", [2, 8, 64, 500])
def test_parity_random(window):
    rng = np.random.default_rng(1234)
    check_fast_matches_batch(rng.standard_normal(600), window)


@pytest.mark.parametrize("window", [2, 8, 64])
def test_parity_constant(window):
    check_fast_matches_batch(np.full(200, 3.25), window)
    check_fast_matches_batch(np.zeros(200), window)


@pytest.mark.parametrize("window", [2, 8, 64, 200])
def test_parity_trending(window):
    n = 600
    t = np.arange(n, dtype=np.float64)
    check_fast_matches_batch(0.05 * t + np.sin(0.2 * t), window)


@pytest.mark.parametrize("window", [2, 8, 64])
def test_parity_large_offset(window):
    rng = np.random.default_rng(99)
    check_fast_matches_batch(1e9 + rng.standard_normal(600), window, offset_mode=True)


@pytest.mark.parametrize("scale", [1e-3, 1e-6])
@pytest.mark.parametrize("window", [2, 8, 64])
def test_parity_small_variance(scale, window):
    rng = np.random.default_rng(7)
    check_fast_matches_batch(rng.standard_normal(600) * scale, window)


@pytest.mark.parametrize("window", [2, 5, 64])
def test_parity_random_walk_long(window):
    # Long stream exercises periodic + drift-guard re-anchors mid-stream.
    rng = np.random.default_rng(555)
    check_fast_matches_batch(np.cumsum(rng.standard_normal(20_000)), window)


def test_not_full_yields_nan():
    ext = kymora.StreamingExtractor(8)
    for v in [1.0, 2.0, 3.0]:
        assert ext.push(v) is False
        assert np.all(np.isnan(ext.compute(kind="fast")))
        assert np.all(np.isnan(ext.compute(kind="all")))


@pytest.mark.parametrize("window", [1, 2, 16])
@pytest.mark.parametrize("pos", ["first", "middle", "last"])
def test_nan_position_yields_all_nan_fast(window, pos):
    rng = np.random.default_rng(3)
    data = rng.standard_normal(window + 4)
    idx = {"first": 0, "middle": len(data) // 2, "last": len(data) - 1}[pos]
    data[idx] = np.nan
    ext = kymora.StreamingExtractor(window)
    saw_nan_row = False
    for i, v in enumerate(data):
        if ext.push(float(v)):
            win = data[i - window + 1 : i + 1]
            got = ext.compute(kind="fast")
            if np.any(np.isnan(win)):
                assert np.all(np.isnan(got))
                saw_nan_row = True
    assert saw_nan_row


@pytest.mark.parametrize("bad", [np.inf, -np.inf])
@pytest.mark.parametrize("window", [2, 5, 32])
def test_inf_matches_batch_exactly(bad, window):
    # ±inf windows take the exact fallback: outputs match batch bit-for-bit
    # where defined (NaN where batch is NaN). Windows after the inf slides
    # out resume the O(1) path, which agrees within 1-2 ulp
    # (anchor + s1/W summation residual).
    rng = np.random.default_rng(11)
    data = rng.standard_normal(window + 3)
    data[1] = bad
    ext = kymora.StreamingExtractor(window)
    for i, v in enumerate(data):
        if ext.push(float(v)):
            win = data[i - window + 1 : i + 1]
            got = ext.compute(kind="fast")
            want = kymora.extract_features(win[None, :], features=FAST_NAMES)[0]
            has_inf = bool(np.isinf(win).any())
            for name, s, b in zip(FAST_NAMES, got, want):
                if np.isnan(b):
                    assert np.isnan(s), name
                elif has_inf:
                    assert s == b, f"{name}: {s} vs {b}"
                else:
                    # Post-inf recovery windows: O(1) path, 1-2 ulp agreement.
                    np.testing.assert_allclose(s, b, rtol=1e-12, atol=1e-15,
                                               err_msg=name)


def test_all_nan_window_recovery():
    # NaN slides out and exact accumulators resume with no poisoning.
    w = 8
    ext = kymora.StreamingExtractor(w)
    for v in [1.0, np.nan, 3.0, 4.0, 5.0, 6.0, 7.0, 8.0]:
        ext.push(float(v))
    assert np.all(np.isnan(ext.compute(kind="fast")))
    for v in [10.0, 11.0, 12.0, 13.0, 14.0, 15.0, 16.0, 17.0]:
        ext.push(float(v))
    got = ext.compute(kind="fast")
    win = np.arange(10.0, 18.0)
    want = kymora.extract_features(win[None, :], features=FAST_NAMES)[0]
    np.testing.assert_allclose(got, want, rtol=RTOL, atol=ATOL)


def test_window_sizes_one_and_two():
    rng = np.random.default_rng(21)
    data = rng.standard_normal(50)
    for w in (1, 2):
        check_fast_matches_batch(data, w)


def test_sparse_spike_then_zeros():
    # Regression (found by hypothesis): after a lone spike slides out, the
    # window is constant-zero while the anchor is still stale (1/3 here).
    # The anchored abs_energy expansion then cancels catastrophically
    # (0.333-0.667+0.333 -> ~1e-16 instead of 0, rms ~6e-9 vs batch 0.0).
    # Constant windows must use the exact W*first^2 shortcut.
    data = np.array([0.0] * 28 + [1.0] + [0.0] * 3)
    for interval in (1, 2, 4096):
        ext = kymora.StreamingExtractor(3, anchor_interval=interval)
        for i, v in enumerate(data):
            if ext.push(float(v)):
                got = ext.compute(kind="fast")
                want = kymora.extract_features(
                    data[i - 2 : i + 1][None, :], features=FAST_NAMES
                )[0]
                for name, s, b in zip(FAST_NAMES, got, want):
                    if np.isnan(b):
                        assert np.isnan(s), name
                    else:
                        assert abs(s - b) <= ATOL + RTOL * abs(b), f"{name}: {s} vs {b}"


def test_anchor_interval_configurable():
    ext = kymora.StreamingExtractor(16, anchor_interval=7)
    assert ext.anchor_interval == 7
    ext.set_anchor_interval(3)
    assert ext.anchor_interval == 3
    with pytest.raises(ValueError):
        kymora.StreamingExtractor(16, anchor_interval=0)
    with pytest.raises(ValueError):
        ext.set_anchor_interval(0)
    # Forced re-anchor every push still matches batch.
    rng = np.random.default_rng(5)
    data = rng.standard_normal(100)
    ext = kymora.StreamingExtractor(16, anchor_interval=1)
    for i, v in enumerate(data):
        if ext.push(float(v)):
            got = ext.compute(kind="fast")
            want = kymora.extract_features(
                data[i - 15 : i + 1][None, :], features=FAST_NAMES
            )[0]
            np.testing.assert_allclose(got, want, rtol=RTOL, atol=ATOL)


HYP_SETTINGS = settings(
    max_examples=100,
    deadline=None,
    suppress_health_check=[HealthCheck.too_slow],
)


@HYP_SETTINGS
@given(
    w=st.integers(min_value=2, max_value=32),
    interval=st.integers(min_value=1, max_value=16),
    data=st.lists(
        st.floats(min_value=-10.0, max_value=10.0, allow_nan=False, allow_infinity=False),
        min_size=32,
        max_size=72,
    ),
)
def test_hypothesis_fast_matches_batch(w, interval, data):
    # Bounded magnitudes keep every feature well-conditioned, so rtol 1e-9
    # must hold on every window. Small anchor_interval forces frequent
    # exact re-anchors mid-stream. len(data) >= w always: no filtering.
    stream = np.asarray(data, dtype=np.float64)
    ext = kymora.StreamingExtractor(w, anchor_interval=interval)
    for i, v in enumerate(stream):
        ready = ext.push(float(v))
        if i + 1 < w:
            continue
        assert ready
        got = ext.compute(kind="fast")
        want = kymora.extract_features(
            stream[i - w + 1 : i + 1][None, :], features=FAST_NAMES
        )[0]
        for name, s, b in zip(FAST_NAMES, got, want):
            if np.isnan(b):
                assert np.isnan(s), name
            else:
                assert abs(s - b) <= ATOL + RTOL * abs(b), f"{name}: {s} vs {b}"
