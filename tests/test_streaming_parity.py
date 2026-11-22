"""Streaming vs batch parity.

`StreamingExtractor.compute(kind="fast")` must match `extract_features` on the
same window within rtol 1e-9 (float64) across distributions, window sizes, and
degenerate inputs. Skewness/kurtosis on 1e9-offset windows carry a documented
absolute bound instead (batch-center conditioning; see docs/streaming.md and
`src/features/streaming.rs`).
"""

import numpy as np
import pytest
from hypothesis import HealthCheck, assume, given, settings
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


def _degenerate_nonconstant(win):
    """True when window variance is pure summation noise (SciPy gh-15905
    regime): nonzero var at/below one squared ulp of the mean. Batch and
    streaming legitimately center such windows differently (the batch mean
    can round onto an endpoint), so strict parity is unachievable there --
    e.g. a 1-ulp window yields batch cid ~1.41 vs exact streaming cid 2.0.
    skew/kurt NaN-parity on these windows is covered by dedicated tests
    (constant-window tests + `near_degenerate_window_yields_nan_both_paths`
    in the Rust suite), not here."""
    m = float(np.mean(win))
    v = float(np.var(win))
    return v > 0.0 and v <= (np.finfo(np.float64).eps * m) ** 2


def test_degenerate_guard_deterministic():
    """Deterministic batch-vs-streaming cover for the scipy gh-15905 guard
    (commit 86cde1f): constant, 1-ulp, 1e9+1e-3 (guard must NOT trigger),
    1e9+1e-9 (guard triggers -- 1e-9 is far below one ulp of 1e9)."""
    skew_i = FAST_NAMES.index("skewness")
    kurt_i = FAST_NAMES.index("kurtosis")

    def both_paths(win):
        win = np.asarray(win, dtype=np.float64)
        b = kymora.extract_features(win[None, :], features=FAST_NAMES)[0]
        ext = kymora.StreamingExtractor(len(win))
        for v in win:
            ext.push(float(v))
        s = ext.compute(kind="fast")
        return b, s

    # 1. Constant window: both NaN.
    b, s = both_paths(np.full(8, 3.0))
    assert np.isnan(b[skew_i]) and np.isnan(b[kurt_i])
    assert np.isnan(s[skew_i]) and np.isnan(s[kurt_i])

    # 2. 1-ulp window: variance is summation noise -> both NaN (scipy parity).
    b, s = both_paths(np.array([-10.0, -9.999999999999998]))
    assert np.isnan(b[skew_i]) and np.isnan(b[kurt_i])
    assert np.isnan(s[skew_i]) and np.isnan(s[kurt_i])

    # 3. 1e9 offset + 1e-3 noise: well above the (eps*mean)^2 threshold,
    # guard must NOT trigger; paths agree to ~5.5e-5 (measured). Tiny-noise
    # windows center-round differently between batch and streaming, so the
    # bound here is looser than OFFSET_SHAPE_BOUND (which covers O(1)
    # noise); finiteness is the guard assertion.
    rng = np.random.default_rng(0)
    win = 1e9 + rng.normal(0, 1e-3, 50)
    b, s = both_paths(win)
    assert np.isfinite(b[skew_i]) and np.isfinite(b[kurt_i])
    assert np.isfinite(s[skew_i]) and np.isfinite(s[kurt_i])
    assert abs(s[skew_i] - b[skew_i]) < 1e-3
    assert abs(s[kurt_i] - b[kurt_i]) < 1e-3

    # 4. 1e9 offset + 1e-9 noise: 1e-9 is far below one ulp of 1e9
    # (~2.4e-7), so the variance is rounding noise and the guard
    # legitimately fires -> both NaN. Documented, not a bug.
    win = 1e9 + rng.normal(0, 1e-9, 50)
    b, s = both_paths(win)
    assert np.isnan(b[skew_i]) and np.isnan(b[kurt_i])
    assert np.isnan(s[skew_i]) and np.isnan(s[kurt_i])


def test_degenerate_guard_nan_policy_raise_does_not_fire():
    """Guard-produced NaN is an output value, not an input defect:
    nan_policy='raise' scans inputs only, so a 1-ulp window returns NaN
    (both paths) instead of raising."""
    win = np.array([[-10.0, -9.999999999999998]])
    row = kymora.extract_features(win, nan_policy="raise")[0]
    names = kymora.feature_names()
    assert np.isnan(row[names.index("skewness")])
    assert np.isnan(row[names.index("kurtosis")])
    ext = kymora.StreamingExtractor(2, nan_policy="raise")
    ext.push(-10.0)
    ext.push(-9.999999999999998)
    got = ext.compute(kind="fast")
    assert np.isnan(got[FAST_NAMES.index("skewness")])
    assert np.isnan(got[FAST_NAMES.index("kurtosis")])


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
    # must hold on every window -- except numerically-degenerate windows
    # (see `_degenerate_nonconstant`), which are rejected: comparing
    # implementations there would only measure whose center rounding is
    # luckier. Small anchor_interval forces frequent exact re-anchors
    # mid-stream. len(data) >= w always: no other filtering.
    stream = np.asarray(data, dtype=np.float64)
    ext = kymora.StreamingExtractor(w, anchor_interval=interval)
    for i, v in enumerate(stream):
        ready = ext.push(float(v))
        if i + 1 < w:
            continue
        assert ready
        win = stream[i - w + 1 : i + 1]
        assume(not _degenerate_nonconstant(win))
        got = ext.compute(kind="fast")
        want = kymora.extract_features(win[None, :], features=FAST_NAMES)[0]
        for name, s, b in zip(FAST_NAMES, got, want):
            if np.isnan(b):
                assert np.isnan(s), name
            elif w == 2 and name in TWO_POINT_EXACT:
                exact = TWO_POINT_EXACT[name]
                assert abs(s - exact) < TWO_POINT_BOUND, f"{name}: {s} vs {exact}"
                assert abs(b - exact) < TWO_POINT_BOUND, f"batch {name}: {b}"
            else:
                assert abs(s - b) <= ATOL + RTOL * abs(b), f"{name}: {s} vs {b}"


@pytest.mark.parametrize("offset", [1e6, 1e8, 1e9])
@pytest.mark.parametrize("window", [64, 256])
def test_streaming_extreme_numerical_stress(offset, window):
    """Stress test rolling accumulators under massive mean offset and unit variance.

    Simulates long continuous telemetry (100,000 pushes) with mean in [1e6, 1e9]
    and unit variance. Verifies that drift-guard re-anchoring maintains exact
    numerical agreement with batch recompute across all fast features without
    diverging over extended runs.
    """
    rng = np.random.default_rng(2026)
    n_pushes = 50_000
    vals = offset + rng.standard_normal(n_pushes)
    ext = kymora.StreamingExtractor(window)

    for i, v in enumerate(vals):
        ext.push(float(v))
        if i >= window and i % 10_000 == 0:
            got = ext.compute(kind="fast")
            win = vals[i - window + 1 : i + 1]
            want = kymora.extract_features(win[None, :], features=FAST_NAMES)[0]

            for name, s, b in zip(FAST_NAMES, got, want):
                if np.isnan(b):
                    assert np.isnan(s), f"{name}: expected NaN at step {i}"
                elif name in SKEW_KURT:
                    assert abs(s - b) < 1e-4, f"{name}: step {i} diff {abs(s - b):.2e} exceeded bound"
                else:
                    # Allow 1e-7 relative tolerance or 1e-11 absolute floor
                    denom = max(abs(b), 1.0)
                    rel_err = abs(s - b) / denom
                    assert rel_err < 1e-7 or abs(s - b) < 1e-11, (
                        f"{name}: step {i} got={s:.8e}, want={b:.8e}, rel_err={rel_err:.2e}"
                    )


@pytest.mark.parametrize("val", [0.0, 1.0, -42.0, 1e8])
@pytest.mark.parametrize("window", [32, 128])
def test_streaming_constant_window_stress(val, window):
    """Verify exact zero variance and identical NaN semantics on constant streams."""
    ext = kymora.StreamingExtractor(window)
    for _ in range(window * 3):
        ext.push(val)

    got = ext.compute(kind="fast")
    win = np.full(window, val)
    want = kymora.extract_features(win[None, :], features=FAST_NAMES)[0]

    skew_idx = FAST_NAMES.index("skewness")
    kurt_idx = FAST_NAMES.index("kurtosis")
    var_idx = FAST_NAMES.index("var")
    std_idx = FAST_NAMES.index("std")

    assert np.isnan(got[skew_idx]) and np.isnan(want[skew_idx])
    assert np.isnan(got[kurt_idx]) and np.isnan(want[kurt_idx])
    assert got[var_idx] == 0.0 and want[var_idx] == 0.0
    assert got[std_idx] == 0.0 and want[std_idx] == 0.0


def test_streaming_longdouble_and_fsum_reference():
    """Compare StreamingExtractor accumulators against exact math.fsum and np.longdouble references."""
    import math

    w = 100
    rng = np.random.default_rng(999)
    offset = 1e7
    vals = offset + rng.standard_normal(20_000)
    ext = kymora.StreamingExtractor(w)

    for i, v in enumerate(vals):
        ext.push(float(v))
        if i >= w and i % 5_000 == 0:
            win = vals[i - w + 1 : i + 1]
            got = ext.compute(kind="fast")

            # Exact references
            exact_mean = math.fsum(win) / w
            exact_energy = math.fsum(float(x) * float(x) for x in win)
            win_ld = win.astype(np.longdouble)
            exact_var = float(np.mean((win_ld - np.longdouble(exact_mean)) ** 2))

            mean_got = got[FAST_NAMES.index("mean")]
            var_got = got[FAST_NAMES.index("var")]
            energy_got = got[FAST_NAMES.index("abs_energy")]

            assert abs(mean_got - exact_mean) / exact_mean < 1e-11, f"mean rel diff: {abs(mean_got - exact_mean)/exact_mean}"
            assert abs(energy_got - exact_energy) / exact_energy < 1e-11, f"energy rel diff: {abs(energy_got - exact_energy)/exact_energy}"
            assert abs(var_got - exact_var) / exact_var < 1e-5, f"var rel diff: {abs(var_got - exact_var)/exact_var}"


