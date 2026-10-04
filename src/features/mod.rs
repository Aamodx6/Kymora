pub mod entropy;
pub mod multistream;
pub mod spectral;
pub mod stats;
pub mod streaming;
pub mod temporal;
pub mod views;

pub use multistream::MultiStreamExtractor;
pub use streaming::StreamingExtractor;

use std::cell::RefCell;

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

/// Autocorrelation lags, in output column order.
const LAGS: [usize; 4] = [1, 2, 5, 10];

thread_local! {
    /// Copy of the current series, permuted in place for the order statistics.
    /// Owned by the rayon worker and reused across every series it handles, so a
    /// batch costs one allocation per thread rather than one per series.
    static ORDER_BUF: RefCell<Vec<f64>> = const { RefCell::new(Vec::new()) };
}

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
///
/// Traversal budget: the series is read twice for the moments, then once each
/// for the order statistics, the successive differences, the threshold features,
/// the peaks, the autocorrelations (all four lags together), the trend, the
/// ordinal patterns, and the FFT. Features that share a traversal share it
/// deliberately; the accumulation order within each is the same as a
/// one-loop-per-feature version, so fusing changed no output bit.
pub fn compute_all(x: &[f64], out: &mut [f64]) {
    debug_assert_eq!(out.len(), NAMES.len());
    if x.is_empty() {
        out.fill(f64::NAN);
        return;
    }
    let n = x.len();
    let nf = n as f64;

    // Pass 1 -- raw-value accumulations: the two sums, the extremes, and the two
    // cheap predicates that decide the rest of the function (is anything NaN, is
    // everything equal). Extremes are taken here rather than from the order
    // statistics below, which keeps them out of the selection set entirely.
    let first = x[0];
    let mut sum = 0.0f64;
    let mut abs_energy = 0.0f64;
    let mut min = first;
    let mut max = first;
    let mut constant = true;
    let mut has_nan = false;
    for &v in x {
        sum += v;
        abs_energy += v * v;
        if v < min {
            min = v;
        }
        if v > max {
            max = v;
        }
        constant &= v == first;
        has_nan |= v.is_nan();
    }
    if has_nan {
        out.fill(f64::NAN);
        return;
    }

    let mean = sum / nf;

    // Pass 2 -- central moments 2, 3 and 4 together. var, skewness and kurtosis
    // are all functions of these sums.
    let mut m2 = 0.0f64;
    let mut m3 = 0.0f64;
    let mut m4 = 0.0f64;
    for &v in x {
        let d = v - mean;
        let d2 = d * d;
        m2 += d2;
        m3 += d2 * d;
        m4 += d2 * d2;
    }
    // exact-constant series: force var to 0 so std-guarded features don't emit
    // float-noise garbage (sum rounding makes var ~1e-31 otherwise)
    let var = if constant { 0.0 } else { m2 / nf };
    let std = var.sqrt();

    let quantiles = ORDER_BUF.with(|cell| {
        let buf = &mut *cell.borrow_mut();
        buf.clear();
        buf.extend_from_slice(x);
        stats::quantiles(buf)
    });
    let [median, q10, q25, q75, q90] = quantiles;

    let mut w = out.iter_mut();
    let mut put = |v: f64| {
        if let Some(slot) = w.next() {
            *slot = v;
        }
    };

    put(mean);
    put(std);
    put(var);
    put(min);
    put(max);
    put(median);
    put(q10);
    put(q25);
    put(q75);
    put(q90);
    put(stats::skewness(m3, nf, var, std));
    put(stats::kurtosis(m4, nf, var, std));
    put(abs_energy);
    put((abs_energy / nf).sqrt());

    // Successive differences: mean_abs_change and cid_ce read the same diffs, so
    // they accumulate side by side. cid_ce scales each difference by std before
    // squaring (rather than squaring and dividing once at the end) so a series of
    // huge values cannot overflow a partial sum.
    if n < 2 {
        put(f64::NAN); // mean_abs_change
        put(f64::NAN); // mean_change
        put(f64::NAN); // cid_ce
    } else {
        let mut abs_change = 0.0f64;
        let mut scaled_sq = 0.0f64;
        if std == 0.0 {
            for pair in x.windows(2) {
                abs_change += (pair[1] - pair[0]).abs();
            }
        } else {
            for pair in x.windows(2) {
                let d = pair[1] - pair[0];
                abs_change += d.abs();
                let s = d / std;
                scaled_sq += s * s;
            }
        }
        put(abs_change / (nf - 1.0));
        put((x[n - 1] - x[0]) / (nf - 1.0));
        // cid_ce, normalized: z-score the series first; constant series -> 0
        if std == 0.0 {
            put(0.0);
        } else {
            put(scaled_sq.sqrt());
        }
    }
    if n < 3 {
        put(f64::NAN); // mean_second_derivative_central
    } else {
        let s: f64 = x.windows(3).map(|w| w[2] - 2.0 * w[1] + w[0]).sum();
        put(s / (2.0 * (nf - 2.0)));
    }

    let thresholds = temporal::thresholds(x, mean);
    put(thresholds.zero_crossings);
    put(thresholds.mean_crossings);
    put(temporal::number_of_peaks(x, 3));
    put(thresholds.strike_above);
    put(thresholds.strike_below);

    for a in temporal::autocorr_multi(x, mean, var, LAGS) {
        put(a);
    }

    let (slope, r2) = temporal::linear_trend(x, mean, var);
    put(slope);
    put(r2);

    put(temporal::permutation_entropy(x));

    let (dom, cent, sent) = spectral::spectral_features(x, constant);
    put(dom);
    put(cent);
    put(sent);

    debug_assert!(w.next().is_none());
}
