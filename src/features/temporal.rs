#![deny(unsafe_code)]

//! Temporal features. Several of these are fused into a single traversal of the
//! series: they read the same values, so walking the series once per feature
//! wastes memory bandwidth without simplifying anything. Accumulation order is
//! unchanged from the one-pass-per-feature form, so the results are unchanged.

/// Autocorrelation at every lag in `lags`, in one pass.
///
/// Lag `k` is `sum_i (x[i] - mean)(x[i + k] - mean) / ((n - k) * var)`, summed
/// ascending in `i` exactly as a per-lag loop would. NaN where `n <= k` or
/// `var == 0`. `lags` must be ascending.
pub fn autocorr_multi<const K: usize>(
    x: &[f64],
    mean: f64,
    var: f64,
    lags: [usize; K],
) -> [f64; K] {
    let n = x.len();
    let mut acc = [0.0f64; K];
    if var != 0.0 && K > 0 {
        let max_lag = lags[K - 1];
        // Body where every lag is in bounds, so the inner loop carries no test.
        let body = n.saturating_sub(max_lag);
        for i in 0..body {
            let d = x[i] - mean;
            for (a, &k) in acc.iter_mut().zip(lags.iter()) {
                *a += d * (x[i + k] - mean);
            }
        }
        // Tail: shorter lags still contribute.
        for i in body..n {
            let d = x[i] - mean;
            for (a, &k) in acc.iter_mut().zip(lags.iter()) {
                if i + k < n {
                    *a += d * (x[i + k] - mean);
                }
            }
        }
    }
    let mut out = [f64::NAN; K];
    for (o, (&k, &a)) in out.iter_mut().zip(lags.iter().zip(acc.iter())) {
        if n > k && var != 0.0 {
            *o = a / ((n - k) as f64 * var);
        }
    }
    out
}

/// Least-squares linear trend vs `t = 0..n-1`. Returns `(slope, r_squared)`.
/// Constant series: slope 0, r2 NaN. `n < 2`: both NaN.
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

/// Ordinal pattern for each comparison key; see [`permutation_entropy`].
const PATTERN_FOR_TEST: [u8; 8] = [5, 2, 4, 2, 3, 1, 0, 0];

/// Normalized permutation entropy, order 3, delay 1. Range [0, 1]. n < 3 -> NaN.
pub fn permutation_entropy(x: &[f64]) -> f64 {
    let n = x.len();
    if n < 3 {
        return f64::NAN;
    }
    // Ordinal pattern index from the three pairwise comparisons, keyed as
    // `(a<=b)<<2 | (b<=c)<<1 | (a<=c)`. Two of the eight keys are unreachable by
    // transitivity (`110`, `001`); they map to the same pattern as the sibling
    // that ignores the redundant comparison, so the table needs no branch to
    // exclude them. Ties break by position, matching a stable rank of the
    // window: 0 = abc, 1 = acb, 2 = bac, 3 = cab, 4 = bca, 5 = cba.
    const PATTERN: [u8; 8] = PATTERN_FOR_TEST;
    let mut counts = [0usize; 6];
    for w in x.windows(3) {
        let (a, b, c) = (w[0], w[1], w[2]);
        // Bitwise `|` rather than short-circuiting `||`: all three comparisons
        // are cheap, and on real data their outcomes are unpredictable, so a
        // table lookup beats three mispredictable branches per window.
        let key = (((a <= b) as usize) << 2) | (((b <= c) as usize) << 1) | ((a <= c) as usize);
        counts[PATTERN[key] as usize] += 1;
    }
    let total = (n - 2) as f64;
    let weights = counts.map(|c| c as f64);
    super::entropy::shannon_entropy(&weights, total) / 6f64.ln()
}

/// Count of indices `i` where ``x[i]`` is strictly greater than all neighbors within `support`
/// on both sides (tsfresh `number_peaks`).
pub fn number_of_peaks(x: &[f64], support: usize) -> f64 {
    let n = x.len();
    if n < 2 * support + 1 {
        return 0.0;
    }
    // `&` rather than `&&`: every comparison is a register op, whereas the
    // early exit `all` would give is a branch whose outcome real data makes
    // unpredictable. Fully evaluating the support window is both cheaper and
    // vectorisable. Identical results -- no NaN can reach here.
    let mut count = 0usize;
    for i in support..n - support {
        let v = x[i];
        let mut peak = true;
        for d in 1..=support {
            peak &= (v > x[i - d]) & (v > x[i + d]);
        }
        count += peak as usize;
    }
    count as f64
}

/// The four threshold features, from one traversal.
pub struct Thresholds {
    pub zero_crossings: f64,
    pub mean_crossings: f64,
    pub strike_above: f64,
    pub strike_below: f64,
}

/// Crossings of zero and of `mean`, plus the longest runs strictly above and
/// strictly below `mean`.
///
/// A crossing is a consecutive pair straddling the level, with the same `>`
/// convention on both sides as a separate per-level pass would use.
pub fn thresholds(x: &[f64], mean: f64) -> Thresholds {
    let mut zero_crossings = 0usize;
    let mut mean_crossings = 0usize;
    let mut above_best = 0usize;
    let mut above_run = 0usize;
    let mut below_best = 0usize;
    let mut below_run = 0usize;

    let mut prev_above_zero = false;
    let mut prev_above_mean = false;

    for (i, &v) in x.iter().enumerate() {
        let above_zero = v > 0.0;
        let above_mean = v > mean;
        if i > 0 {
            zero_crossings += (above_zero != prev_above_zero) as usize;
            mean_crossings += (above_mean != prev_above_mean) as usize;
        }
        prev_above_zero = above_zero;
        prev_above_mean = above_mean;

        if above_mean {
            above_run += 1;
            above_best = above_best.max(above_run);
        } else {
            above_run = 0;
        }
        if v < mean {
            below_run += 1;
            below_best = below_best.max(below_run);
        } else {
            below_run = 0;
        }
    }

    Thresholds {
        zero_crossings: zero_crossings as f64,
        mean_crossings: mean_crossings as f64,
        strike_above: above_best as f64,
        strike_below: below_best as f64,
    }
}

#[cfg(test)]
mod tests {
    use super::*;

    fn autocorr_single(x: &[f64], mean: f64, var: f64, k: usize) -> f64 {
        let n = x.len();
        if n <= k || var == 0.0 {
            return f64::NAN;
        }
        let cov: f64 = (0..n - k).map(|i| (x[i] - mean) * (x[i + k] - mean)).sum();
        cov / ((n - k) as f64 * var)
    }

    #[test]
    fn fused_autocorr_matches_per_lag_loops() {
        for n in [1usize, 2, 3, 6, 11, 12, 40, 257] {
            let x: Vec<f64> = (0..n).map(|i| ((i * 37 % 11) as f64) - 5.0).collect();
            let mean = x.iter().sum::<f64>() / n as f64;
            let var = x.iter().map(|v| (v - mean) * (v - mean)).sum::<f64>() / n as f64;
            let got = autocorr_multi(&x, mean, var, [1, 2, 5, 10]);
            for (j, k) in [1usize, 2, 5, 10].into_iter().enumerate() {
                let want = autocorr_single(&x, mean, var, k);
                assert_eq!(got[j].to_bits(), want.to_bits(), "n = {n}, lag = {k}");
            }
        }
    }

    #[test]
    fn fused_thresholds_match_separate_passes() {
        let cases: Vec<Vec<f64>> = vec![
            vec![1.0, -1.0, 1.0, -1.0, 1.0],
            vec![0.0; 5],
            vec![3.0, 3.0, -2.0, -2.0, -2.0, 4.0],
            vec![-1.0],
            vec![1e-300, -1e-300, 0.0, 5.0],
        ];
        for x in cases {
            let n = x.len() as f64;
            let mean = x.iter().sum::<f64>() / n;
            let t = thresholds(&x, mean);
            let crossings = |level: f64| {
                x.windows(2)
                    .filter(|w| (w[0] > level) != (w[1] > level))
                    .count() as f64
            };
            let strike = |pred: &dyn Fn(f64) -> bool| {
                let mut best = 0usize;
                let mut cur = 0usize;
                for &v in &x {
                    if pred(v) {
                        cur += 1;
                        best = best.max(cur);
                    } else {
                        cur = 0;
                    }
                }
                best as f64
            };
            assert_eq!(t.zero_crossings, crossings(0.0));
            assert_eq!(t.mean_crossings, crossings(mean));
            assert_eq!(t.strike_above, strike(&|v| v > mean));
            assert_eq!(t.strike_below, strike(&|v| v < mean));
        }
    }

    /// The table-driven ordinal pattern must agree with the readable
    /// match-on-comparisons form for every reachable window ordering, including
    /// ties. Enumerating small integer triples covers every branch.
    #[test]
    fn pattern_table_matches_the_branching_classifier() {
        fn reference(a: f64, b: f64, c: f64) -> usize {
            match (a <= b, b <= c, a <= c) {
                (true, true, _) => 0,
                (true, false, true) => 1,
                (false, _, true) => 2,
                (true, false, false) => 3,
                (false, true, _) => 4,
                (false, false, false) => 5,
            }
        }
        for a in 0..4 {
            for b in 0..4 {
                for c in 0..4 {
                    let (a, b, c) = (a as f64, b as f64, c as f64);
                    let key = (((a <= b) as usize) << 2)
                        | (((b <= c) as usize) << 1)
                        | ((a <= c) as usize);
                    let got = PATTERN_FOR_TEST[key] as usize;
                    assert_eq!(got, reference(a, b, c), "({a}, {b}, {c})");
                }
            }
        }
        // Every pattern is reachable, so the entropy denominator ln(6) is right.
        let mut seen = [false; 6];
        for a in 0..3 {
            for b in 0..3 {
                for c in 0..3 {
                    seen[reference(a as f64, b as f64, c as f64)] = true;
                }
            }
        }
        assert!(seen.iter().all(|&s| s));
    }

    /// The branchless peak count must agree with the short-circuiting form.
    #[test]
    fn peaks_match_a_short_circuiting_scan() {
        let mut state = 987654321u64;
        let mut next = || {
            state = state.wrapping_mul(6364136223846793005).wrapping_add(1);
            ((state >> 11) as f64 / (1u64 << 53) as f64) * 10.0 - 5.0
        };
        for n in [0usize, 1, 5, 6, 7, 9, 64, 501] {
            let x: Vec<f64> = (0..n).map(|_| next().round()).collect();
            for support in [1usize, 3, 5] {
                let want = if n < 2 * support + 1 {
                    0.0
                } else {
                    (support..n - support)
                        .filter(|&i| (1..=support).all(|d| x[i] > x[i - d] && x[i] > x[i + d]))
                        .count() as f64
                };
                assert_eq!(
                    number_of_peaks(&x, support),
                    want,
                    "n={n} support={support}"
                );
            }
        }
    }
}
