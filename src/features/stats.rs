#![deny(unsafe_code)]

//! Order statistics and shape moments.
//!
//! The quantile path is selection-based rather than sort-based: the five
//! quantiles this crate needs touch at most ten order statistics, and
//! `select_nth_unstable_by` reaches those in O(n) each without ordering
//! everything in between. Results are identical to sorting — a quantile is a
//! function of its two bracketing order statistics, and `f64::total_cmp` makes
//! the ordering total, so equal-ranked elements are bit-identical.

/// Quantile levels, in output column order. `quantiles` returns values in this
/// order.
pub const QUANTILE_LEVELS: [f64; 5] = [0.50, 0.10, 0.25, 0.75, 0.90];

/// Most order statistics ever requested: a floor/ceil pair per quantile level.
/// Min and max are not among them -- the caller already has those from its own
/// single pass over the series, for two comparisons per element.
const MAX_STATS: usize = 2 * QUANTILE_LEVELS.len();

/// [`QUANTILE_LEVELS`] with linear interpolation between bracketing ranks —
/// numpy's default quantile method.
///
/// `buf` is permuted in place and must be NaN-free (NaN is short-circuited
/// before this is reached, so `total_cmp` never has to define away a NaN here).
pub fn quantiles(buf: &mut [f64]) -> [f64; 5] {
    let n = buf.len();
    if n == 0 {
        return [f64::NAN; 5];
    }
    if n == 1 {
        return [buf[0]; 5];
    }

    // Collect the ranks needed, ascending and deduplicated.
    let mut ranks = [0usize; MAX_STATS];
    let mut count = 0usize;
    let push = |k: usize, ranks: &mut [usize; MAX_STATS], count: &mut usize| {
        let mut i = 0;
        while i < *count {
            if ranks[i] == k {
                return;
            }
            if ranks[i] > k {
                break;
            }
            i += 1;
        }
        let mut j = *count;
        while j > i {
            ranks[j] = ranks[j - 1];
            j -= 1;
        }
        ranks[i] = k;
        *count += 1;
    };
    for &q in &QUANTILE_LEVELS {
        let pos = q * (n - 1) as f64;
        push(pos.floor() as usize, &mut ranks, &mut count);
        push(pos.ceil() as usize, &mut ranks, &mut count);
    }

    let mut values = [0.0f64; MAX_STATS];
    select_ranks(buf, 0, &ranks[..count], &mut values[..count]);

    let at = |k: usize| match ranks[..count].binary_search(&k) {
        Ok(i) => values[i],
        // unreachable: every rank read below was pushed above. Returning NaN
        // rather than indexing keeps this function panic-free by construction.
        Err(_) => f64::NAN,
    };

    let mut out = [0.0f64; 5];
    for (slot, &q) in out.iter_mut().zip(QUANTILE_LEVELS.iter()) {
        let pos = q * (n - 1) as f64;
        let lo = pos.floor() as usize;
        let hi = pos.ceil() as usize;
        let frac = pos - lo as f64;
        let lo_v = at(lo);
        *slot = lo_v + (at(hi) - lo_v) * frac;
    }
    out
}

/// Write the values of the given (ascending, deduplicated) `ranks` into
/// `values`, partitioning `buf` in place.
///
/// `offset` is the rank of `buf[0]` within the original slice. Recursing on the
/// median rank first keeps the depth logarithmic in the number of ranks, so the
/// selections cost little more than one full pass plus a few partial ones.
fn select_ranks(buf: &mut [f64], offset: usize, ranks: &[usize], values: &mut [f64]) {
    if ranks.is_empty() {
        return;
    }
    let mid = ranks.len() / 2;
    let rank = ranks[mid];
    let local = rank - offset;
    let (left, pivot, right) = buf.select_nth_unstable_by(local, f64::total_cmp);
    values[mid] = *pivot;
    select_ranks(left, offset, &ranks[..mid], &mut values[..mid]);
    select_ranks(right, rank + 1, &ranks[mid + 1..], &mut values[mid + 1..]);
}

/// Population skewness (`scipy.stats.skew`, `bias=True`) from the second and
/// third central moment sums. NaN when the window is exactly constant
/// (`std == 0`) or numerically degenerate: mirroring SciPy (`m2 <=
/// (eps*mean)^2`, gh-15905), a variance at/below the square of one ulp of
/// the mean is pure summation rounding noise, so the ratio is unreliable
/// (e.g. a 1-ulp window otherwise yields ~sqrt(2) from rounding alone).
pub fn skewness(m3: f64, n: f64, var: f64, std: f64, mean: f64) -> f64 {
    if std == 0.0 || var <= (f64::EPSILON * mean) * (f64::EPSILON * mean) {
        return f64::NAN;
    }
    (m3 / n) / (var * std)
}

/// Population excess kurtosis (`scipy.stats.kurtosis`, `fisher=True`,
/// `bias=True`) from the second and fourth central moment sums. Same
/// degenerate-window NaN rule as [`skewness`].
pub fn kurtosis(m4: f64, n: f64, var: f64, std: f64, mean: f64) -> f64 {
    if std == 0.0 || var <= (f64::EPSILON * mean) * (f64::EPSILON * mean) {
        return f64::NAN;
    }
    (m4 / n) / (var * var) - 3.0
}

#[cfg(test)]
mod tests {
    use super::*;

    fn sorted_reference(x: &[f64]) -> [f64; 5] {
        let mut s = x.to_vec();
        s.sort_by(f64::total_cmp);
        let n = s.len();
        let q = |p: f64| {
            if n == 1 {
                return s[0];
            }
            let pos = p * (n - 1) as f64;
            let lo = pos.floor() as usize;
            let hi = pos.ceil() as usize;
            s[lo] + (s[hi] - s[lo]) * (pos - lo as f64)
        };
        let mut out = [0.0; 5];
        for (o, &p) in out.iter_mut().zip(QUANTILE_LEVELS.iter()) {
            *o = q(p);
        }
        out
    }

    #[test]
    fn selection_matches_a_full_sort() {
        let mut state = 12345u64;
        let mut next = || {
            state = state.wrapping_mul(6364136223846793005).wrapping_add(1);
            ((state >> 11) as f64 / (1u64 << 53) as f64) * 200.0 - 100.0
        };
        for n in [1usize, 2, 3, 4, 5, 7, 8, 16, 33, 100, 501, 1024] {
            let x: Vec<f64> = (0..n).map(|_| next()).collect();
            let mut buf = x.clone();
            assert_eq!(quantiles(&mut buf), sorted_reference(&x), "n = {n}");
        }
    }

    #[test]
    fn handles_ties_and_signed_zero() {
        let cases: Vec<Vec<f64>> = vec![
            vec![1.0; 9],
            vec![0.0, -0.0, 0.0, -0.0],
            vec![2.0, 1.0, 2.0, 1.0, 2.0],
            vec![f64::MIN, f64::MAX, 0.0],
            vec![5.0],
        ];
        for x in cases {
            let mut buf = x.clone();
            assert_eq!(quantiles(&mut buf), sorted_reference(&x));
        }
    }

    /// Sums a slice exactly the way batch pass 1 does (sequential `+=`).
    fn batch_moments(x: &[f64]) -> (f64, f64, f64, f64, f64, f64) {
        let n = x.len() as f64;
        let mut sum = 0.0;
        for &v in x {
            sum += v;
        }
        let mean = sum / n;
        let (mut m2, mut m3, mut m4) = (0.0, 0.0, 0.0);
        for &v in x {
            let d = v - mean;
            let d2 = d * d;
            m2 += d2;
            m3 += d2 * d;
            m4 += d2 * d2;
        }
        let var = m2 / n;
        (mean, m2, m3, m4, var, var.sqrt())
    }

    #[test]
    fn degenerate_window_yields_nan_like_scipy() {
        // 1-ulp window: the variance is pure summation rounding noise, so the
        // naive skew/kurt ratios are rounding garbage (~sqrt(2) for skew).
        // scipy.stats.skew/kurtosis return NaN here (catastrophic-
        // cancellation guard, gh-15905); we must match.
        let x = [-10.0f64, -9.999999999999998];
        let (mean, _m2, m3, m4, var, std) = batch_moments(&x);
        assert!(var > 0.0, "test setup: window must not be exactly constant");
        assert!(skewness(m3, 2.0, var, std, mean).is_nan());
        assert!(kurtosis(m4, 2.0, var, std, mean).is_nan());
    }

    #[test]
    fn healthy_window_unaffected_by_degenerate_guard() {
        // Well-conditioned data must take the plain-ratio path bit-identically.
        let x = [1.0f64, 2.0, 3.0, 4.0, 5.0];
        let (mean, _m2, m3, m4, var, std) = batch_moments(&x);
        let n = x.len() as f64;
        assert_eq!(skewness(m3, n, var, std, mean), (m3 / n) / (var * std));
        assert_eq!(
            kurtosis(m4, n, var, std, mean),
            (m4 / n) / (var * var) - 3.0
        );
    }
}
