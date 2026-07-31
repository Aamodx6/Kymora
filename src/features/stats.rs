/// Quantile with linear interpolation, matching numpy's default method.
/// `sorted` must be ascending, non-empty.
pub fn quantile(sorted: &[f64], q: f64) -> f64 {
    let n = sorted.len();
    if n == 1 {
        return sorted[0];
    }
    let pos = q * (n - 1) as f64;
    let lo = pos.floor() as usize;
    let hi = pos.ceil() as usize;
    let frac = pos - lo as f64;
    sorted[lo] + (sorted[hi] - sorted[lo]) * frac
}

/// Population skewness (scipy.stats.skew, bias=True). std == 0 -> NaN.
pub fn skewness(x: &[f64], mean: f64, std: f64) -> f64 {
    if std == 0.0 {
        return f64::NAN;
    }
    let n = x.len() as f64;
    x.iter().map(|v| ((v - mean) / std).powi(3)).sum::<f64>() / n
}

/// Population excess kurtosis (scipy.stats.kurtosis, fisher=True, bias=True).
pub fn kurtosis(x: &[f64], mean: f64, std: f64) -> f64 {
    if std == 0.0 {
        return f64::NAN;
    }
    let n = x.len() as f64;
    x.iter().map(|v| ((v - mean) / std).powi(4)).sum::<f64>() / n - 3.0
}
