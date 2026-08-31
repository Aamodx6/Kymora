//! FFT-based features.
//!
//! Two things here are performance decisions, invisible from the outside:
//!
//! * a real-to-complex transform. The input is real, so the negative-frequency
//!   half of a full complex FFT is redundant; `realfft` computes an n/2 complex
//!   transform plus a cheap fix-up for even lengths, roughly halving the work.
//! * thread-local scratch. Every buffer is owned by the worker thread and reused
//!   across series, so extracting a batch of N series allocates O(threads)
//!   buffers rather than O(N).
//!
//! The planner caches one plan per series length, so a batch of equal-length
//! series plans exactly once per thread.

use super::entropy;
use realfft::num_complex::Complex;
use realfft::RealFftPlanner;
use std::cell::RefCell;

struct Workspace {
    planner: RealFftPlanner<f64>,
    input: Vec<f64>,
    spectrum: Vec<Complex<f64>>,
    scratch: Vec<Complex<f64>>,
    power: Vec<f64>,
}

impl Workspace {
    fn new() -> Self {
        Workspace {
            planner: RealFftPlanner::new(),
            input: Vec::new(),
            spectrum: Vec::new(),
            scratch: Vec::new(),
            power: Vec::new(),
        }
    }
}

thread_local! {
    static WORKSPACE: RefCell<Workspace> = RefCell::new(Workspace::new());
}

/// FFT features over positive-frequency bins `1..=n/2` (DC excluded), sample
/// spacing 1. Returns `(dominant_frequency, spectral_centroid, spectral_entropy)`.
///
/// `constant` is the caller's already-computed "every element is bit-equal"
/// flag: for such a series all power is DC and the remaining bins hold only FFT
/// rounding noise, so the analytic answer is NaN rather than whatever that noise
/// happens to argmax to. `n < 2` and zero total power are NaN for the same
/// reason.
pub fn spectral_features(x: &[f64], constant: bool) -> (f64, f64, f64) {
    let n = x.len();
    let nbins = n / 2; // bins 1..=n/2
    if n < 2 || constant || nbins == 0 {
        return (f64::NAN, f64::NAN, f64::NAN);
    }

    WORKSPACE.with(|cell| {
        let ws = &mut *cell.borrow_mut();
        let fft = ws.planner.plan_fft_forward(n);

        ws.input.clear();
        ws.input.extend_from_slice(x);
        ws.spectrum.clear();
        ws.spectrum
            .resize(fft.complex_len(), Complex::new(0.0, 0.0));
        let need = fft.get_scratch_len();
        if ws.scratch.len() < need {
            ws.scratch.resize(need, Complex::new(0.0, 0.0));
        }

        // Lengths come from the plan itself, so this cannot fail; propagating
        // NaN instead of unwrapping keeps the crate panic-free by construction.
        if fft
            .process_with_scratch(&mut ws.input, &mut ws.spectrum, &mut ws.scratch[..need])
            .is_err()
        {
            return (f64::NAN, f64::NAN, f64::NAN);
        }

        ws.power.clear();
        ws.power
            .extend(ws.spectrum[1..=nbins].iter().map(Complex::norm_sqr));
        let power = &ws.power[..];
        let total: f64 = power.iter().sum();
        // Zero total (a constant series is caught earlier, but underflow can
        // still get here) or a non-finite one (infinities in the input) leaves
        // every spectral feature undefined rather than division-derived noise.
        if total <= 0.0 || !total.is_finite() {
            return (f64::NAN, f64::NAN, f64::NAN);
        }

        let freq = |k: usize| (k + 1) as f64 / n as f64; // power[k] is FFT bin k+1

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
            entropy::shannon_entropy(power, total) / (nbins as f64).ln()
        };

        (dominant, centroid, entropy)
    })
}
