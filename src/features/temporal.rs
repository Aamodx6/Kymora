/// Autocorrelation at lag k: sum((x_i - mean)(x_{i+k} - mean)) / ((n - k) * var).
/// NaN if n <= k or var == 0.
pub fn autocorr(x: &[f64], mean: f64, var: f64, k: usize) -> f64 {
    let n = x.len();
    if n <= k || var == 0.0 {
        return f64::NAN;
    }
    let cov: f64 = (0..n - k).map(|i| (x[i] - mean) * (x[i + k] - mean)).sum();
    cov / ((n - k) as f64 * var)
}

/// Least-squares linear trend vs t = 0..n-1. Returns (slope, r_squared).
/// Constant series: slope 0, r2 NaN. n < 2: both NaN.
pub fn linear_trend(x: &[f64], mean: f64, var: f64) -> (f64, f64) {
    let n = x.len();
    if n < 2 {
        return (f64::NAN, f64::NAN);
    }
    let nf = n as f64;
    let t_mean = (nf - 1.0) / 2.0;
    let t_var = (nf * nf - 1.0) / 12.0; // population variance of 0..n-1
    let cov: f64 = x
        .iter()
        .enumerate()
        .map(|(i, v)| (i as f64 - t_mean) * (v - mean))
        .sum::<f64>()
        / nf;
    let slope = cov / t_var;
    if var == 0.0 {
        return (0.0, f64::NAN);
    }
    let r = cov / (t_var.sqrt() * var.sqrt());
    (slope, r * r)
}

/// Normalized permutation entropy, order 3, delay 1. Range [0, 1]. n < 3 -> NaN.
pub fn permutation_entropy(x: &[f64]) -> f64 {
    let n = x.len();
    if n < 3 {
        return f64::NAN;
    }
    let mut counts = [0usize; 6];
    for w in x.windows(3) {
        let (a, b, c) = (w[0], w[1], w[2]);
        // ordinal pattern index: ranks of (a,b,c) with ties broken by position (stable)
        let idx = match (a <= b, b <= c, a <= c) {
            (true, true, _) => 0,      // a b c
            (true, false, true) => 1,  // a c b
            (false, _, true) => 2,     // b a c
            (true, false, false) => 3, // c a b
            (false, true, _) => 4,     // b c a
            (false, false, false) => 5, // c b a
        };
        counts[idx] += 1;
    }
    let total = (n - 2) as f64;
    let h: f64 = counts
        .iter()
        .filter(|&&c| c > 0)
        .map(|&c| {
            let p = c as f64 / total;
            -p * p.ln()
        })
        .sum();
    h / 6f64.ln()
}

/// Count of i where x[i] is strictly greater than all neighbors within `support` on both sides
/// (tsfresh number_peaks).
pub fn number_of_peaks(x: &[f64], support: usize) -> f64 {
    let n = x.len();
    if n < 2 * support + 1 {
        return 0.0;
    }
    (support..n - support)
        .filter(|&i| {
            (1..=support).all(|d| x[i] > x[i - d] && x[i] > x[i + d])
        })
        .count() as f64
}

/// Longest run where pred holds.
pub fn longest_strike(x: &[f64], pred: impl Fn(f64) -> bool) -> f64 {
    let mut best = 0usize;
    let mut cur = 0usize;
    for &v in x {
        if pred(v) {
            cur += 1;
            best = best.max(cur);
        } else {
            cur = 0;
        }
    }
    best as f64
}

/// Number of crossings of `level`: count of consecutive pairs strictly straddling it.
pub fn crossings(x: &[f64], level: f64) -> f64 {
    x.windows(2)
        .filter(|w| (w[0] > level) != (w[1] > level))
        .count() as f64
}
