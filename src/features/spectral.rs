use rustfft::{num_complex::Complex, FftPlanner};
use std::cell::RefCell;

thread_local! {
    // ponytail: per-thread planner caches twiddles per length; fine for rayon workers
    static PLANNER: RefCell<FftPlanner<f64>> = RefCell::new(FftPlanner::new());
}

/// FFT-based features over positive-frequency bins 1..=n/2 (DC excluded), sample spacing 1.
/// Returns (dominant_frequency, spectral_centroid, spectral_entropy).
/// Zero total power (constant series) or n < 2 -> all NaN.
pub fn spectral_features(x: &[f64]) -> (f64, f64, f64) {
    let n = x.len();
    // constant series: all power is DC; FFT rounding noise in the other bins
    // would otherwise produce garbage instead of the analytic zero
    if n < 2 || x.iter().all(|&v| v == x[0]) {
        return (f64::NAN, f64::NAN, f64::NAN);
    }
    let mut buf: Vec<Complex<f64>> = x.iter().map(|&v| Complex::new(v, 0.0)).collect();
    PLANNER.with(|p| p.borrow_mut().plan_fft_forward(n).process(&mut buf));

    let nbins = n / 2; // bins 1..=n/2
    let power: Vec<f64> = (1..=nbins).map(|k| buf[k].norm_sqr()).collect();
    let total: f64 = power.iter().sum();
    if total == 0.0 || nbins == 0 {
        return (f64::NAN, f64::NAN, f64::NAN);
    }

    let freq = |k: usize| (k + 1) as f64 / n as f64; // power[k] is FFT bin k+1

    let argmax = power
        .iter()
        .enumerate()
        .max_by(|a, b| a.1.total_cmp(b.1))
        .map(|(i, _)| i)
        .unwrap();
    let dominant = freq(argmax);

    let centroid = power
        .iter()
        .enumerate()
        .map(|(i, &p)| freq(i) * p)
        .sum::<f64>()
        / total;

    let entropy = if nbins == 1 {
        0.0
    } else {
        let h: f64 = power
            .iter()
            .filter(|&&p| p > 0.0)
            .map(|&p| {
                let q = p / total;
                -q * q.ln()
            })
            .sum();
        h / (nbins as f64).ln()
    };

    (dominant, centroid, entropy)
}
