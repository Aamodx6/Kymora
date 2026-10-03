//! Permutation entropy kernel with branchless LUT mapping.

const PATTERN: [u8; 8] = [5, 2, 4, 2, 3, 1, 0, 0];

/// Normalized permutation entropy (order 3, delay 1).
#[inline]
pub fn permutation_entropy(x: &[f64]) -> f64 {
    let n = x.len();
    if n < 3 {
        return f64::NAN;
    }

    let mut counts = [0usize; 6];
    for w in x.windows(3) {
        let (a, b, c) = (w[0], w[1], w[2]);
        let key = (((a <= b) as usize) << 2) | (((b <= c) as usize) << 1) | ((a <= c) as usize);
        counts[PATTERN[key] as usize] += 1;
    }

    let total = (n - 2) as f64;
    let mut sent = 0.0f64;
    for &c in &counts {
        if c > 0 {
            let p = (c as f64) / total;
            sent -= p * p.ln();
        }
    }
    sent / 6f64.ln()
}

/// Normalized permutation entropy for f32 series (order 3, delay 1).
#[inline]
pub fn permutation_entropy_f32(x: &[f32]) -> f64 {
    let n = x.len();
    if n < 3 {
        return f64::NAN;
    }

    let mut counts = [0usize; 6];
    for w in x.windows(3) {
        let (a, b, c) = (w[0], w[1], w[2]);
        let key = (((a <= b) as usize) << 2) | (((b <= c) as usize) << 1) | ((a <= c) as usize);
        counts[PATTERN[key] as usize] += 1;
    }

    let total = (n - 2) as f64;
    let mut sent = 0.0f64;
    for &c in &counts {
        if c > 0 {
            let p = (c as f64) / total;
            sent -= p * p.ln();
        }
    }
    sent / 6f64.ln()
}
