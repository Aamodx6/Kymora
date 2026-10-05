"""External parity: kymora vs tsfresh / TSFEL on definition-matched features (6.1).

Covers only the B1-frozen matched sets (benchmarks/agreement/feature_map.json
+ benchmarks/results/2026-10-05_equal_feature/parity.json, all EXACT there).
Bounds here are deliberately 1000x looser than the measured ~1e-13 so the
suite stays green across library patch versions while still catching any
definition drift. Anything unmatched lives in intentional_differences.md.

Reference libraries are dev-only (`pip install kymora[dev-parity]`); each
test skips independently when its library is missing, so plain CI (which
lacks them) stays green.
"""

import numpy as np
import pytest

import warnings

import kymora

TSFRESH_MATCHED = [
    "median", "quantile_10", "quantile_90", "abs_energy", "root_mean_square",
    "mean_abs_change", "mean_change", "mean_second_derivative_central",
    "longest_strike_above_mean", "longest_strike_below_mean",
    "autocorr_lag_1", "autocorr_lag_2", "autocorr_lag_5",
]
TSFRESH_COLS = {
    "median": "val__median",
    "quantile_10": 'val__quantile__q_0.1',
    "quantile_90": 'val__quantile__q_0.9',
    "abs_energy": "val__abs_energy",
    "root_mean_square": "val__root_mean_square",
    "mean_abs_change": "val__mean_abs_change",
    "mean_change": "val__mean_change",
    "mean_second_derivative_central": "val__mean_second_derivative_central",
    "longest_strike_above_mean": "val__longest_strike_above_mean",
    "longest_strike_below_mean": "val__longest_strike_below_mean",
    "autocorr_lag_1": "val__autocorrelation__lag_1",
    "autocorr_lag_2": "val__autocorrelation__lag_2",
    "autocorr_lag_5": "val__autocorrelation__lag_5",
}
TSFRESH_FC_PARAMS = {
    "median": None,
    "quantile": [{"q": 0.1}, {"q": 0.9}],
    "abs_energy": None,
    "root_mean_square": None,
    "mean_abs_change": None,
    "mean_change": None,
    "mean_second_derivative_central": None,
    "longest_strike_above_mean": None,
    "longest_strike_below_mean": None,
    "autocorrelation": [{"lag": 1}, {"lag": 2}, {"lag": 5}],
}

TSFEL_MATCHED = [
    "mean", "std", "var", "min", "max", "median", "skewness", "kurtosis",
    "abs_energy", "root_mean_square", "mean_abs_change", "mean_change",
    "zero_crossings",
]
TSFEL_COLS = {
    "mean": "Mean",
    "std": "Standard deviation",
    "var": "Variance",
    "min": "Min",
    "max": "Max",
    "median": "Median",
    "skewness": "Skewness",
    "kurtosis": "Kurtosis",
    "abs_energy": "Absolute energy",
    "root_mean_square": "Root mean square",
    "mean_abs_change": "Mean absolute diff",
    "mean_change": "Mean diff",
    "zero_crossings": "Zero crossing rate",
}

RTOL = 1e-6
ATOL = 1e-9


def _series():
    rng = np.random.default_rng(20261006)
    n = 300
    t = np.arange(n, dtype=np.float64)
    return {
        "gaussian": rng.standard_normal(n),
        "sine": np.sin(0.05 * t) + 0.2 * rng.standard_normal(n),
        "walk": np.cumsum(rng.standard_normal(n)),
    }


def test_tsfresh_matched_features():
    tsfresh = pytest.importorskip("tsfresh")
    pytest.importorskip("pandas")
    import pandas as pd
    from tsfresh import extract_features as tsf_extract

    for label, x in _series().items():
        df = pd.DataFrame({"id": np.zeros(len(x), dtype=int), "val": x})
        out = tsf_extract(
            df, column_id="id", default_fc_parameters=dict(TSFRESH_FC_PARAMS),
            n_jobs=0, disable_progressbar=True,
        )
        got = kymora.extract_features(x[None, :], features=TSFRESH_MATCHED)[0]
        for j, name in enumerate(TSFRESH_MATCHED):
            b = float(out[TSFRESH_COLS[name]].iloc[0])
            s = float(got[j])
            if np.isnan(b):
                assert np.isnan(s), f"{label}/{name}"
            else:
                np.testing.assert_allclose(s, b, rtol=RTOL, atol=ATOL,
                                           err_msg=f"{label}/{name}: {s} vs {b}")


def test_tsfel_matched_features():
    tsfel = pytest.importorskip("tsfel")
    cfg_all = tsfel.get_features_by_domain()
    cfg = {
        domain: {k: v for k, v in funcs.items() if k in set(TSFEL_COLS.values())}
        for domain, funcs in cfg_all.items()
    }
    cfg = {domain: funcs for domain, funcs in cfg.items() if funcs}
    for label, x in _series().items():
        with warnings.catch_warnings():
            # Third-party noise, not ours: TSFEL restates its default fs.
            warnings.simplefilter("ignore", UserWarning)
            out = tsfel.time_series_features_extractor(cfg, x, verbose=0)
        got = kymora.extract_features(x[None, :], features=TSFEL_MATCHED)[0]
        for j, name in enumerate(TSFEL_MATCHED):
            # TSFEL prefixes 1D-input columns with "0_".
            b = float(out[f"0_{TSFEL_COLS[name]}"].iloc[0])
            s = float(got[j])
            if np.isnan(b):
                assert np.isnan(s), f"{label}/{name}"
            else:
                np.testing.assert_allclose(s, b, rtol=RTOL, atol=ATOL,
                                           err_msg=f"{label}/{name}: {s} vs {b}")
