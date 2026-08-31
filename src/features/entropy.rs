//! Shannon entropy, shared by the spectral and ordinal-pattern features.
//!
//! Both compute the same thing over different weights, so the summation, the
//! zero handling and the normalization live in one place.

/// Shannon entropy in nats of `weights` normalized by `total`:
/// `-sum(q * ln q)` for `q = w / total`, skipping zero weights.
///
/// `total` must be the sum of `weights`. Weights of zero contribute nothing, as
/// does any weight whose normalized share underflows to zero -- which is why the
/// guard is on `q` rather than on `w`: `0 * ln(0)` is NaN, and an underflowing
/// share used to be able to reach it.
pub fn shannon_entropy(weights: &[f64], total: f64) -> f64 {
    -weights
        .iter()
        .map(|&w| {
            let q = w / total;
            if q > 0.0 {
                q * q.ln()
            } else {
                0.0
            }
        })
        .sum::<f64>()
}

#[cfg(test)]
mod tests {
    use super::*;

    #[test]
    fn entropy_matches_the_std_ln_formula() {
        let cases: Vec<Vec<f64>> = vec![
            vec![1.0; 8],
            vec![1.0, 0.0, 3.0, 0.0, 5.5],
            vec![1e-9, 1.0, 2.0],
            vec![7.0],
            vec![1e300, 1e300],
            vec![f64::MIN_POSITIVE / 4.0, 1.0], // subnormal -> fallback path
        ];
        for w in cases {
            let total: f64 = w.iter().sum();
            let want: f64 = -w
                .iter()
                .filter(|&&p| p / total > 0.0)
                .map(|&p| {
                    let q = p / total;
                    q * q.ln()
                })
                .sum::<f64>();
            let got = shannon_entropy(&w, total);
            let denom = if want.abs() > 0.0 { want.abs() } else { 1.0 };
            assert!(
                (got - want).abs() / denom < 1e-14,
                "weights {w:?}: got {got}, want {want}"
            );
        }
    }

    /// A uniform distribution over k outcomes has entropy exactly ln(k).
    ///
    /// The tolerance here is set by the sequential summation of k terms, not by
    /// the logarithm: it grows with k the same way `f64::ln` would.
    #[test]
    fn uniform_entropy_is_log_k() {
        for k in [1usize, 2, 3, 17, 250, 4096] {
            let w = vec![2.5f64; k];
            let got = shannon_entropy(&w, 2.5 * k as f64);
            let want = (k as f64).ln();
            assert!(
                (got - want).abs() <= 1e-15 * k as f64 * want.max(1.0),
                "k = {k}: got {got}, want {want}"
            );
        }
    }
}
