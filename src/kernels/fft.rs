//! Real FFT execution and spectral feature extraction.

use crate::scratch::Scratch;
use realfft::num_complex::Complex;

/// Compute spectral features: (dominant_frequency, spectral_centroid, spectral_entropy).
pub fn spectral_features(x: &[f64], constant: bool, scratch: &mut Scratch) -> (f64, f64, f64) {
    let n = x.len();
    let nbins = n / 2;
    if n < 2 || constant || nbins == 0 {
        return (f64::NAN, f64::NAN, f64::NAN);
    }

    let fft = scratch.planner.plan_fft_forward(n);
    let complex_len = fft.complex_len();
    let scratch_len = fft.get_scratch_len();

    scratch.fft_in.clear();
    scratch.fft_in.extend_from_slice(x);

    scratch.fft_out.clear();
    scratch.fft_out.resize(complex_len, Complex::new(0.0, 0.0));

    if scratch.fft_scratch.len() < scratch_len {
        scratch.fft_scratch.resize(scratch_len, Complex::new(0.0, 0.0));
    }

    if fft
        .process_with_scratch(
            &mut scratch.fft_in,
            &mut scratch.fft_out,
            &mut scratch.fft_scratch[..scratch_len],
        )
        .is_err()
    {
        return (f64::NAN, f64::NAN, f64::NAN);
    }

    scratch.power.clear();
    scratch
        .power
        .extend(scratch.fft_out[1..=nbins].iter().map(Complex::norm_sqr));

    let power = &scratch.power[..];
    let total: f64 = power.iter().sum();
    if total <= 0.0 || !total.is_finite() {
        return (f64::NAN, f64::NAN, f64::NAN);
    }

    let freq = |k: usize| (k + 1) as f64 / n as f64;

    let argmax = power
        .iter()
        .enumerate()
        .max_by(|a, b| a.1.total_cmp(b.1))
        .map(|(i, _)| i)
        .unwrap_or(0);
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
        let sent: f64 = -power
            .iter()
            .map(|&p| {
                let q = p / total;
                if q > 0.0 {
                    q * q.ln()
                } else {
                    0.0
                }
            })
            .sum::<f64>();
        sent / (nbins as f64).ln()
    };

    (dominant, centroid, entropy)
}

/// Compute spectral features for f32 series: (dominant_frequency, spectral_centroid, spectral_entropy).
pub fn spectral_features_f32(x: &[f32], constant: bool, scratch: &mut Scratch) -> (f64, f64, f64) {
    let n = x.len();
    let nbins = n / 2;
    if n < 2 || constant || nbins == 0 {
        return (f64::NAN, f64::NAN, f64::NAN);
    }

    let fft = scratch.planner.plan_fft_forward(n);
    let complex_len = fft.complex_len();
    let scratch_len = fft.get_scratch_len();

    scratch.fft_in.clear();
    scratch.fft_in.extend(x.iter().map(|&v| v as f64));

    scratch.fft_out.clear();
    scratch.fft_out.resize(complex_len, Complex::new(0.0, 0.0));

    if scratch.fft_scratch.len() < scratch_len {
        scratch.fft_scratch.resize(scratch_len, Complex::new(0.0, 0.0));
    }

    if fft
        .process_with_scratch(
            &mut scratch.fft_in,
            &mut scratch.fft_out,
            &mut scratch.fft_scratch[..scratch_len],
        )
        .is_err()
    {
        return (f64::NAN, f64::NAN, f64::NAN);
    }

    scratch.power.clear();
    scratch
        .power
        .extend(scratch.fft_out[1..=nbins].iter().map(Complex::norm_sqr));

    let power = &scratch.power[..];
    let total: f64 = power.iter().sum();
    if total <= 0.0 || !total.is_finite() {
        return (f64::NAN, f64::NAN, f64::NAN);
    }

    let freq = |k: usize| (k + 1) as f64 / n as f64;

    let argmax = power
        .iter()
        .enumerate()
        .max_by(|a, b| a.1.total_cmp(b.1))
        .map(|(i, _)| i)
        .unwrap_or(0);
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
        let sent: f64 = -power
            .iter()
            .map(|&p| {
                let q = p / total;
                if q > 0.0 {
                    q * q.ln()
                } else {
                    0.0
                }
            })
            .sum::<f64>();
        sent / (nbins as f64).ln()
    };

    (dominant, centroid, entropy)
}

#[derive(Debug, Clone, Copy)]
pub struct FftAggregatedResult {
    pub centroid: f64,
    pub variance: f64,
    pub skew: f64,
    pub kurtosis: f64,
}

/// Spectral centroid, variance, skew, and kurtosis of Fourier absolute spectrum.
pub fn fft_aggregated(fft_out: &[Complex<f64>]) -> FftAggregatedResult {
    let n = fft_out.len();
    if n == 0 {
        return FftAggregatedResult {
            centroid: f64::NAN,
            variance: f64::NAN,
            skew: f64::NAN,
            kurtosis: f64::NAN,
        };
    }
    let mut sum_y = 0.0f64;
    let mut m1 = 0.0f64;
    let mut m2 = 0.0f64;
    let mut m3 = 0.0f64;
    let mut m4 = 0.0f64;

    for (i, c) in fft_out.iter().enumerate() {
        let y = c.norm();
        let idx = i as f64;
        let idx2 = idx * idx;
        sum_y += y;
        m1 += idx * y;
        m2 += idx2 * y;
        m3 += idx2 * idx * y;
        m4 += idx2 * idx2 * y;
    }

    if sum_y == 0.0 {
        return FftAggregatedResult {
            centroid: f64::NAN,
            variance: f64::NAN,
            skew: f64::NAN,
            kurtosis: f64::NAN,
        };
    }

    m1 /= sum_y;
    m2 /= sum_y;
    m3 /= sum_y;
    m4 /= sum_y;

    let centroid = m1;
    let variance = m2 - centroid * centroid;
    if variance < 0.5 {
        return FftAggregatedResult {
            centroid,
            variance,
            skew: f64::NAN,
            kurtosis: f64::NAN,
        };
    }
    let var_pow_1_5 = variance.powf(1.5);
    let var_pow_2 = variance * variance;
    let skew = (m3 - 3.0 * centroid * variance - centroid.powi(3)) / var_pow_1_5;
    let kurtosis = (m4 - 4.0 * centroid * m3 + 6.0 * m2 * centroid * centroid - 3.0 * centroid) / var_pow_2;

    FftAggregatedResult {
        centroid,
        variance,
        skew,
        kurtosis,
    }
}

/// Fourier coefficient attribute: 0 = real, 1 = imag, 2 = abs, 3 = angle (in degrees).
#[inline]
pub fn fft_coeff(fft_out: &[Complex<f64>], k: usize, attr: usize) -> f64 {
    if k >= fft_out.len() {
        return f64::NAN;
    }
    let c = fft_out[k];
    match attr {
        0 => c.re,
        1 => c.im,
        2 => c.norm(),
        3 => c.im.atan2(c.re).to_degrees(),
        _ => f64::NAN,
    }
}

