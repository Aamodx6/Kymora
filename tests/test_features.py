"""Every feature checked against a numpy/scipy reference implementation."""
import numpy as np
import pytest
import scipy.stats
import tsxtractor

rng = np.random.default_rng(42)


def ref_autocorr(x, k):
    n, m, v = len(x), x.mean(), x.var()
    if n <= k or v == 0 or x.min() == x.max():
        return np.nan
    return ((x[: n - k] - m) * (x[k:] - m)).sum() / ((n - k) * v)


def ref_perm_entropy(x):
    if len(x) < 3:
        return np.nan
    counts = {}
    for a, b, c in zip(x, x[1:], x[2:]):
        # same tie-breaking as Rust: stable comparisons with <=
        key = (a <= b, b <= c, a <= c)
        counts[key] = counts.get(key, 0) + 1
    p = np.array(list(counts.values())) / (len(x) - 2)
    return -(p * np.log(p)).sum() / np.log(6)


def ref_spectral(x):
    n = len(x)
    if n < 2 or x.min() == x.max():
        return np.nan, np.nan, np.nan
    fft = np.fft.fft(x)
    nbins = n // 2
    power = np.abs(fft[1 : nbins + 1]) ** 2
    total = power.sum()
    if total == 0 or nbins == 0:
        return np.nan, np.nan, np.nan
    freqs = np.arange(1, nbins + 1) / n
    dominant = freqs[np.argmax(power)]
    centroid = (freqs * power).sum() / total
    if nbins == 1:
        entropy = 0.0
    else:
        q = power[power > 0] / total
        entropy = -(q * np.log(q)).sum() / np.log(nbins)
    return dominant, centroid, entropy


def ref_number_of_peaks(x, support=3):
    n = len(x)
    return sum(
        all(x[i] > x[i - d] and x[i] > x[i + d] for d in range(1, support + 1))
        for i in range(support, n - support)
    )


def ref_longest_strike(mask):
    best = cur = 0
    for m in mask:
        cur = cur + 1 if m else 0
        best = max(best, cur)
    return best


def ref_trend(x):
    n = len(x)
    if n < 2:
        return np.nan, np.nan
    if x.min() == x.max():
        return 0.0, np.nan
    res = scipy.stats.linregress(np.arange(n), x)
    return res.slope, res.rvalue**2


def reference(x, level=None):
    """Dict of feature name -> reference value.

    level: mean to use for crossing/strike masks (pass the library's own mean —
    values sitting exactly at the mean make these counts sensitive to which
    summation order computed it).
    """
    x = np.asarray(x, dtype=np.float64)
    n = len(x)
    m, v, s = x.mean(), x.var(), x.std()
    if x.min() == x.max():  # exact-constant: kill float-noise variance
        v = s = 0.0
    if level is None:
        level = m
    d = np.diff(x)
    out = {
        "mean": m,
        "std": s,
        "var": v,
        "min": x.min(),
        "max": x.max(),
        "median": np.median(x),
        "quantile_10": np.quantile(x, 0.10),
        "quantile_25": np.quantile(x, 0.25),
        "quantile_75": np.quantile(x, 0.75),
        "quantile_90": np.quantile(x, 0.90),
        "skewness": scipy.stats.skew(x, bias=True) if s > 0 else np.nan,
        "kurtosis": scipy.stats.kurtosis(x, bias=True) if s > 0 else np.nan,
        "abs_energy": (x**2).sum(),
        "root_mean_square": np.sqrt((x**2).mean()),
        "mean_abs_change": np.abs(d).mean() if n >= 2 else np.nan,
        "mean_change": (x[-1] - x[0]) / (n - 1) if n >= 2 else np.nan,
        "cid_ce": (np.sqrt(((d / s) ** 2).sum()) if s > 0 else 0.0) if n >= 2 else np.nan,
        "mean_second_derivative_central": (
            (x[2:] - 2 * x[1:-1] + x[:-2]).sum() / (2 * (n - 2)) if n >= 3 else np.nan
        ),
        "zero_crossings": ((x[:-1] > 0) != (x[1:] > 0)).sum(),
        "mean_crossings": ((x[:-1] > level) != (x[1:] > level)).sum(),
        "number_of_peaks": ref_number_of_peaks(x),
        "longest_strike_above_mean": ref_longest_strike(x > level),
        "longest_strike_below_mean": ref_longest_strike(x < level),
        "autocorr_lag_1": ref_autocorr(x, 1),
        "autocorr_lag_2": ref_autocorr(x, 2),
        "autocorr_lag_5": ref_autocorr(x, 5),
        "autocorr_lag_10": ref_autocorr(x, 10),
        "permutation_entropy": ref_perm_entropy(x),
    }
    out["trend_slope"], out["trend_r2"] = ref_trend(x)
    (
        out["dominant_frequency"],
        out["spectral_centroid"],
        out["spectral_entropy"],
    ) = ref_spectral(x)
    return out


SERIES = {
    "gaussian": rng.standard_normal(500),
    "trend": np.arange(300) * 0.5 + rng.standard_normal(300),
    "sine": np.sin(np.linspace(0, 40 * np.pi, 512)),
    "constant": np.full(100, 3.7),
    "tiny": np.array([1.0, 2.0]),
    "single": np.array([5.0]),
    "integers_with_ties": rng.integers(0, 5, 200).astype(np.float64),
}


@pytest.mark.parametrize("name", SERIES)
def test_against_reference(name):
    x = SERIES[name]
    got = dict(zip(tsxtractor.feature_names(), tsxtractor.extract_features([x])[0]))
    want = reference(x, level=got["mean"])
    assert set(got) == set(want)
    for feat in want:
        np.testing.assert_allclose(
            got[feat], want[feat], rtol=1e-9, atol=1e-10,
            err_msg=f"{name}/{feat}", equal_nan=True,
        )


def test_2d_matches_ragged():
    X = rng.standard_normal((50, 128))
    a = tsxtractor.extract_features(X)
    b = tsxtractor.extract_features(list(X))
    np.testing.assert_array_equal(a, b)


def test_nan_propagates():
    x = rng.standard_normal(100)
    x[13] = np.nan
    out = tsxtractor.extract_features([x])
    assert np.isnan(out).all()


def test_empty_series_all_nan():
    out = tsxtractor.extract_features([np.array([], dtype=np.float64)])
    assert np.isnan(out).all()


def test_sliding_matches_manual():
    x = rng.standard_normal(1000)
    s = tsxtractor.sliding_features(x, window=100, stride=37)
    manual = tsxtractor.extract_features([x[i : i + 100] for i in range(0, 901, 37)])
    np.testing.assert_array_equal(s, manual)


def test_sliding_validation():
    x = rng.standard_normal(50)
    with pytest.raises(ValueError):
        tsxtractor.sliding_features(x, window=0)
    with pytest.raises(ValueError):
        tsxtractor.sliding_features(x, window=100)


def test_non_contiguous_rejected():
    X = rng.standard_normal((100, 100))[:, ::2]
    with pytest.raises(ValueError):
        tsxtractor.extract_features(X)
