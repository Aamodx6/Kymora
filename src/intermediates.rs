#![deny(unsafe_code)]

//! Lazy and shared intermediates calculation.
//!
//! Shared intermediate structures (Pass1, Pass2, Centered, Sorted, Spectrum, ACF, Diffs)
//! are computed at most once per series based on the `Needs` bitmask.

use crate::kernels;
use crate::scratch::Scratch;

bitflags::bitflags! {
    #[derive(Debug, Clone, Copy, PartialEq, Eq)]
    pub struct Needs: u16 {
        const PASS1     = 1 << 0;
        const CENTERED  = 1 << 1;
        const PASS2     = 1 << 2;
        const SORTED    = 1 << 3;
        const SPECTRUM  = 1 << 4;
        const ACF       = 1 << 5;
        const DIFFS     = 1 << 6;
        const PERM      = 1 << 7;
        const PEAKS     = 1 << 8;
        const TREND     = 1 << 9;
        const C3        = 1 << 10;
        const NONLIN    = 1 << 11;
        const CROSSINGS = 1 << 12;
        const SELECT    = 1 << 13;
    }
}

pub struct Intermediates<'a> {
    pub p1: kernels::reduce::Pass1Result,
    pub centered: &'a [f64],
    pub p2: kernels::reduce::FusedPass2Result,
    pub quantiles: [f64; 5],
    pub deciles: [f64; 9],
    pub diffs: (f64, f64, f64, f64),
    pub cid_ce_raw: f64,
    pub abs_sum_changes: f64,
    pub acf: [f64; 4],
    pub acf_10: [f64; 10],
    pub pacf_9: [f64; 9],
    pub trend: (f64, f64),
    pub trend_full: (f64, f64, f64, f64),
    pub perm_entropy: f64,
    pub peaks: f64,
    pub peaks_extra: (f64, f64, f64, f64),
    pub crossings_extra: (f64, f64),
    pub c3: (f64, f64, f64),
    pub tr: (f64, f64, f64),
    pub spectral: (f64, f64, f64),
    pub fft_agg: kernels::fft::FftAggregatedResult,
    pub fft_out: &'a [realfft::num_complex::Complex<f64>],
    pub has_duplicate: bool,
    pub has_nan: bool,
}

impl<'a> Intermediates<'a> {
    /// Compute requested intermediates for series `x`.
    pub fn compute(x: &[f64], needs: Needs, scratch: &'a mut Scratch) -> Self {
        let n = x.len();
        if n == 0 {
            let p1 = kernels::reduce::pass1(x);
            let p2 = kernels::reduce::pass2_fused(x, 0.0, true, &mut scratch.centered);
            return Self {
                p1,
                centered: &[],
                p2,
                quantiles: [f64::NAN; 5],
                deciles: [f64::NAN; 9],
                diffs: (f64::NAN, f64::NAN, f64::NAN, f64::NAN),
                cid_ce_raw: f64::NAN,
                abs_sum_changes: f64::NAN,
                acf: [f64::NAN; 4],
                acf_10: [f64::NAN; 10],
                pacf_9: [f64::NAN; 9],
                trend: (f64::NAN, f64::NAN),
                trend_full: (f64::NAN, f64::NAN, f64::NAN, f64::NAN),
                perm_entropy: f64::NAN,
                peaks: 0.0,
                peaks_extra: (0.0, 0.0, 0.0, 0.0),
                crossings_extra: (0.0, 0.0),
                c3: (f64::NAN, f64::NAN, f64::NAN),
                tr: (f64::NAN, f64::NAN, f64::NAN),
                spectral: (f64::NAN, f64::NAN, f64::NAN),
                fft_agg: kernels::fft::FftAggregatedResult {
                    centroid: f64::NAN,
                    variance: f64::NAN,
                    skew: f64::NAN,
                    kurtosis: f64::NAN,
                },
                fft_out: &[],
                has_duplicate: false,
                has_nan: false,
            };
        }

        scratch.ensure_capacity(n);

        // Always compute pass1 if any processing is needed
        let p1 = kernels::reduce::pass1(x);
        if p1.has_nan {
            let p2 = kernels::reduce::pass2_fused(&[], 0.0, true, &mut scratch.centered);
            return Self {
                p1,
                centered: &[],
                p2,
                quantiles: [f64::NAN; 5],
                deciles: [f64::NAN; 9],
                diffs: (f64::NAN, f64::NAN, f64::NAN, f64::NAN),
                cid_ce_raw: f64::NAN,
                abs_sum_changes: f64::NAN,
                acf: [f64::NAN; 4],
                acf_10: [f64::NAN; 10],
                pacf_9: [f64::NAN; 9],
                trend: (f64::NAN, f64::NAN),
                trend_full: (f64::NAN, f64::NAN, f64::NAN, f64::NAN),
                perm_entropy: f64::NAN,
                peaks: 0.0,
                peaks_extra: (0.0, 0.0, 0.0, 0.0),
                crossings_extra: (0.0, 0.0),
                c3: (f64::NAN, f64::NAN, f64::NAN),
                tr: (f64::NAN, f64::NAN, f64::NAN),
                spectral: (f64::NAN, f64::NAN, f64::NAN),
                fft_agg: kernels::fft::FftAggregatedResult {
                    centroid: f64::NAN,
                    variance: f64::NAN,
                    skew: f64::NAN,
                    kurtosis: f64::NAN,
                },
                fft_out: &[],
                has_duplicate: false,
                has_nan: true,
            };
        }

        // Pass 2 Fused + Centered buffer
        let p2 = if needs
            .intersects(Needs::CENTERED | Needs::PASS2 | Needs::ACF | Needs::TREND | Needs::PEAKS)
        {
            kernels::reduce::pass2_fused(x, p1.mean, p1.constant, &mut scratch.centered)
        } else {
            kernels::reduce::FusedPass2Result {
                m2: 0.0,
                m3: 0.0,
                m4: 0.0,
                var: 0.0,
                std: 0.0,
                skewness: 0.0,
                kurtosis: 0.0,
                zero_crossings: 0.0,
                mean_crossings: 0.0,
                strike_above: 0.0,
                strike_below: 0.0,
                count_above_mean: 0.0,
                count_below_mean: 0.0,
            }
        };

        // Quantiles / Order stats
        let (quantiles, deciles, has_duplicate) = if needs.contains(Needs::SORTED) {
            scratch.sorted.clear();
            scratch.sorted.extend_from_slice(x);
            scratch.sorted.sort_unstable_by(f64::total_cmp);
            (
                kernels::sort::quantiles_from_sorted(&scratch.sorted),
                kernels::sort::deciles_from_sorted(&scratch.sorted),
                kernels::sort::has_duplicate_sorted(&scratch.sorted),
            )
        } else if needs.contains(Needs::SELECT) {
            (
                kernels::sort::quantiles_multi_select(x, p1.min, p1.max, &mut scratch.sel_scratch),
                kernels::sort::deciles_multi_select(x, p1.min, p1.max, &mut scratch.sel_scratch),
                false,
            )
        } else {
            ([0.0; 5], [0.0; 9], false)
        };

        // Differences
        let (diffs, cid_ce_raw, abs_sum_changes) = if needs.contains(Needs::DIFFS) {
            let d = kernels::reduce::diffs_full(x, p2.std);
            (
                (
                    d.mean_abs_change,
                    d.mean_change,
                    d.cid_ce_norm,
                    d.mean_second_derivative,
                ),
                d.cid_ce_raw,
                d.abs_sum_changes,
            )
        } else {
            ((0.0, 0.0, 0.0, 0.0), 0.0, 0.0)
        };

        // Autocorrelation & PACF
        let (acf, acf_10, pacf_9) = if needs.contains(Needs::ACF) {
            let a10 = kernels::reduce::autocorr_10(&scratch.centered, p2.var);
            let a4 = kernels::reduce::autocorr_multi(&scratch.centered, p2.var);
            let p9 = kernels::reduce::pacf_9(&a10);
            (a4, a10, p9)
        } else {
            ([0.0; 4], [0.0; 10], [0.0; 9])
        };

        // Linear trend
        let (trend, trend_full) = if needs.contains(Needs::TREND) {
            let tf = kernels::reduce::linear_trend_full(&scratch.centered, p2.var, p1.mean);
            ((tf.0, tf.2 * tf.2), tf)
        } else {
            ((0.0, 0.0), (0.0, 0.0, 0.0, 0.0))
        };

        // Permutation entropy
        let perm_entropy = if needs.contains(Needs::PERM) {
            kernels::perm::permutation_entropy(x)
        } else {
            0.0
        };

        // Peaks
        let (peaks, peaks_extra) = if needs.contains(Needs::PEAKS) {
            (
                kernels::reduce::number_of_peaks(x, 3),
                (
                    kernels::reduce::number_of_peaks(x, 1),
                    kernels::reduce::number_of_peaks(x, 5),
                    kernels::reduce::number_of_peaks(x, 10),
                    kernels::reduce::number_of_peaks(x, 50),
                ),
            )
        } else {
            (0.0, (0.0, 0.0, 0.0, 0.0))
        };

        // Crossings extra
        let crossings_extra = if needs.contains(Needs::CROSSINGS) {
            (
                kernels::reduce::number_crossing_m(x, -1.0),
                kernels::reduce::number_crossing_m(x, 1.0),
            )
        } else {
            (0.0, 0.0)
        };

        // C3 nonlinear
        let c3 = if needs.contains(Needs::C3) {
            (
                kernels::reduce::c3(x, 1),
                kernels::reduce::c3(x, 2),
                kernels::reduce::c3(x, 3),
            )
        } else {
            (0.0, 0.0, 0.0)
        };

        // Time reversal asymmetry
        let tr = if needs.contains(Needs::NONLIN) {
            (
                kernels::reduce::time_reversal_asymmetry_statistic(x, 1),
                kernels::reduce::time_reversal_asymmetry_statistic(x, 2),
                kernels::reduce::time_reversal_asymmetry_statistic(x, 3),
            )
        } else {
            (0.0, 0.0, 0.0)
        };

        // Spectral features
        let (spectral, fft_agg) = if needs.contains(Needs::SPECTRUM) {
            let spec = kernels::fft::spectral_features(x, p1.constant, scratch);
            let agg = kernels::fft::fft_aggregated(&scratch.fft_out);
            (spec, agg)
        } else {
            (
                (0.0, 0.0, 0.0),
                kernels::fft::FftAggregatedResult {
                    centroid: 0.0,
                    variance: 0.0,
                    skew: 0.0,
                    kurtosis: 0.0,
                },
            )
        };

        Self {
            p1,
            centered: &scratch.centered,
            p2,
            quantiles,
            deciles,
            diffs,
            cid_ce_raw,
            abs_sum_changes,
            acf,
            acf_10,
            pacf_9,
            trend,
            trend_full,
            perm_entropy,
            peaks,
            peaks_extra,
            crossings_extra,
            c3,
            tr,
            spectral,
            fft_agg,
            fft_out: &scratch.fft_out,
            has_duplicate,
            has_nan: false,
        }
    }
}
