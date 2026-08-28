pub mod spectral;
pub mod stats;
pub mod temporal;

/// Feature names, in output column order. Must match `compute_all` write order.
pub const NAMES: &[&str] = &[
    "mean",
    "std",
    "var",
    "min",
    "max",
    "median",
    "quantile_10",
    "quantile_25",
    "quantile_75",
    "quantile_90",
    "skewness",
    "kurtosis",
    "abs_energy",
    "root_mean_square",
    "mean_abs_change",
    "mean_change",
    "cid_ce",
    "mean_second_derivative_central",
    "zero_crossings",
    "mean_crossings",
    "number_of_peaks",
    "longest_strike_above_mean",
    "longest_strike_below_mean",
    "autocorr_lag_1",
    "autocorr_lag_2",
    "autocorr_lag_5",
    "autocorr_lag_10",
    "trend_slope",
    "trend_r2",
    "permutation_entropy",
    "dominant_frequency",
    "spectral_centroid",
    "spectral_entropy",
];

/// Compute all features for one series into `out` (len == NAMES.len()).
///
/// Value contract (distinct from the structural validation in `extract.rs`):
/// any NaN in the input propagates, so all 33 features become NaN. Features that
/// are individually undefined for an otherwise-valid series (autocorrelation or
/// spectral features of a constant series, change features of a length-1 series)
/// are NaN on their own.
///
/// Empty input is rejected at the FFI boundary as a structural error; the
/// `is_empty()` branch below is a defensive guard so this function stays
/// panic-free if ever called directly.
pub fn compute_all(x: &[f64], out: &mut [f64]) {
    debug_assert_eq!(out.len(), NAMES.len());
    if x.is_empty() || x.iter().any(|v| v.is_nan()) {
        out.fill(f64::NAN);
        return;
    }
    let n = x.len();
    let nf = n as f64;

    // shared moments (population)
    let mean = x.iter().sum::<f64>() / nf;
    // exact-constant series: force var to 0 so std-guarded features don't emit
    // float-noise garbage (sum rounding makes var ~1e-31 otherwise)
    let constant = x.iter().all(|&v| v == x[0]);
    let var = if constant {
        0.0
    } else {
        x.iter().map(|v| (v - mean).powi(2)).sum::<f64>() / nf
    };
    let std = var.sqrt();
    let abs_energy = x.iter().map(|v| v * v).sum::<f64>();

    let mut sorted = x.to_vec();
    sorted.sort_by(f64::total_cmp);

    let mut w = out.iter_mut();
    let mut put = |v: f64| *w.next().unwrap() = v;

    put(mean);
    put(std);
    put(var);
    put(sorted[0]);
    put(sorted[n - 1]);
    put(stats::quantile(&sorted, 0.5));
    put(stats::quantile(&sorted, 0.10));
    put(stats::quantile(&sorted, 0.25));
    put(stats::quantile(&sorted, 0.75));
    put(stats::quantile(&sorted, 0.90));
    put(stats::skewness(x, mean, std));
    put(stats::kurtosis(x, mean, std));
    put(abs_energy);
    put((abs_energy / nf).sqrt());

    // change features
    if n < 2 {
        put(f64::NAN); // mean_abs_change
        put(f64::NAN); // mean_change
        put(f64::NAN); // cid_ce
    } else {
        let diffs = x.windows(2).map(|w| w[1] - w[0]);
        put(diffs.clone().map(f64::abs).sum::<f64>() / (nf - 1.0));
        put((x[n - 1] - x[0]) / (nf - 1.0));
        // cid_ce, normalized: z-score the series first; constant series -> 0
        if std == 0.0 {
            put(0.0);
        } else {
            let ss: f64 = diffs.map(|d| (d / std).powi(2)).sum();
            put(ss.sqrt());
        }
    }
    if n < 3 {
        put(f64::NAN); // mean_second_derivative_central
    } else {
        let s: f64 = x.windows(3).map(|w| w[2] - 2.0 * w[1] + w[0]).sum();
        put(s / (2.0 * (nf - 2.0)));
    }

    put(temporal::crossings(x, 0.0));
    put(temporal::crossings(x, mean));
    put(temporal::number_of_peaks(x, 3));
    put(temporal::longest_strike(x, |v| v > mean));
    put(temporal::longest_strike(x, |v| v < mean));

    for k in [1, 2, 5, 10] {
        put(temporal::autocorr(x, mean, var, k));
    }

    let (slope, r2) = temporal::linear_trend(x, mean, var);
    put(slope);
    put(r2);

    put(temporal::permutation_entropy(x));

    let (dom, cent, sent) = spectral::spectral_features(x);
    put(dom);
    put(cent);
    put(sent);

    debug_assert!(w.next().is_none());
}
