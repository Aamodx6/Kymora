#![deny(unsafe_code)]

//! Per-series execution pipelines: plan dispatch plus the fused core33 paths.
//!
//! [`run_plan`] routes a [`crate::plan::FeaturePlan`] through
//! lazy intermediates (or the fused [`run_core33`]/[`run_core33_f32`] fast
//! paths for plain raw core33); kernels write directly into the caller's
//! output row — no per-series allocation here.

use crate::intermediates::{Intermediates, Needs};
use crate::kernels;
use crate::plan::FeaturePlan;
use crate::registry;
use crate::scratch::Scratch;

pub const CORE33_COUNT: usize = 33;

/// Run a general feature plan on series `x` using lazy intermediates and multi-view dispatch.
#[inline]
pub fn run_plan(x: &[f64], plan: &FeaturePlan, scratch: &mut Scratch, out: &mut [f64]) {
    let nf = plan.n_features();
    debug_assert!(out.len() >= nf);

    if x.is_empty() {
        out[..nf].fill(f64::NAN);
        return;
    }

    // Fast path: if plan is plain raw core33, use direct fused kernel pipeline
    let is_plain_raw = plan.views.len() == 1 && plan.views[0] == "raw";
    if is_plain_raw
        && plan.indices.len() == CORE33_COUNT
        && plan.indices.iter().enumerate().all(|(i, &idx)| i == idx)
    {
        run_core33(x, scratch, out);
        return;
    }

    if is_plain_raw {
        let inter = Intermediates::compute(x, plan.needs, scratch);
        if inter.has_nan {
            out[..nf].fill(f64::NAN);
            return;
        }

        for (slot, item) in out[..nf].iter_mut().zip(&plan.items) {
            let def = &registry::FEATURES[item.feature_idx];
            *slot = def.compute(x, &inter);
        }
        return;
    }

    let mut out_idx = 0usize;
    for v in &plan.views {
        let view_items: Vec<&crate::plan::PlanItem> =
            plan.items.iter().filter(|it| &it.view == v).collect();

        if view_items.is_empty() {
            continue;
        }

        let mut view_needs = Needs::empty();
        for it in &view_items {
            view_needs |= registry::FEATURES[it.feature_idx].needs;
        }

        if v == "raw" {
            let inter = Intermediates::compute(x, view_needs, scratch);
            if inter.has_nan {
                for _ in 0..view_items.len() {
                    out[out_idx] = f64::NAN;
                    out_idx += 1;
                }
            } else {
                for it in view_items {
                    let def = &registry::FEATURES[it.feature_idx];
                    out[out_idx] = def.compute(x, &inter);
                    out_idx += 1;
                }
            }
        } else {
            let mut view_buf = std::mem::take(&mut scratch.view_buf);
            crate::features::views::compute_view(x, v, &mut view_buf);
            let inter = Intermediates::compute(&view_buf, view_needs, scratch);
            if inter.has_nan {
                for _ in 0..view_items.len() {
                    out[out_idx] = f64::NAN;
                    out_idx += 1;
                }
            } else {
                for it in view_items {
                    let def = &registry::FEATURES[it.feature_idx];
                    out[out_idx] = def.compute(&view_buf, &inter);
                    out_idx += 1;
                }
            }
            scratch.view_buf = view_buf;
        }
    }
}

/// Run the full core33 extraction pipeline for one series `x` into mutable slice `out`.
#[inline]
pub fn run_core33(x: &[f64], scratch: &mut Scratch, out: &mut [f64]) {
    debug_assert!(out.len() >= CORE33_COUNT);

    let n = x.len();
    if n == 0 {
        out[..CORE33_COUNT].fill(f64::NAN);
        return;
    }

    scratch.ensure_capacity(n);

    // Pass 1: raw accumulations, min/max, energy, nan check
    let p1 = kernels::reduce::pass1(x);
    if p1.has_nan {
        out[..CORE33_COUNT].fill(f64::NAN);
        return;
    }

    // Pass 2 Fused: writes centered buffer and computes m2, m3, m4, crossings, and strikes in one pass
    let p2 = kernels::reduce::pass2_fused(x, p1.mean, p1.constant, &mut scratch.centered);

    // Order statistics via optimal histogram multi-select
    let quantiles =
        kernels::sort::quantiles_multi_select(x, p1.min, p1.max, &mut scratch.sel_scratch);

    // Write moments, extremes, and quantiles
    out[0] = p1.mean;
    out[1] = p2.std;
    out[2] = p2.var;
    out[3] = p1.min;
    out[4] = p1.max;
    out[5] = quantiles[0]; // median
    out[6] = quantiles[1]; // q10
    out[7] = quantiles[2]; // q25
    out[8] = quantiles[3]; // q75
    out[9] = quantiles[4]; // q90
    out[10] = p2.skewness;
    out[11] = p2.kurtosis;
    out[12] = p1.abs_energy;
    out[13] = (p1.abs_energy / (n as f64)).sqrt(); // root_mean_square

    // Differences
    let (m_abs_ch, m_ch, cid, m_2nd_der) = kernels::reduce::successive_differences(x, p2.std);
    out[14] = m_abs_ch;
    out[15] = m_ch;
    out[16] = cid;
    out[17] = m_2nd_der;

    // Thresholds & peaks
    out[18] = p2.zero_crossings;
    out[19] = p2.mean_crossings;
    out[20] = kernels::reduce::number_of_peaks(x, 3);
    out[21] = p2.strike_above;
    out[22] = p2.strike_below;

    // Autocorrelation at lags [1, 2, 5, 10] in single pass over centered
    let acf = kernels::reduce::autocorr_multi(&scratch.centered, p2.var);
    out[23] = acf[0];
    out[24] = acf[1];
    out[25] = acf[2];
    out[26] = acf[3];

    // Linear trend
    let (slope, r2) = kernels::reduce::linear_trend(&scratch.centered, p2.var);
    out[27] = slope;
    out[28] = r2;

    // Permutation entropy
    out[29] = kernels::perm::permutation_entropy(x);

    // Spectral features
    let (dom, cent, sent) = kernels::fft::spectral_features(x, p1.constant, scratch);
    out[30] = dom;
    out[31] = cent;
    out[32] = sent;
}

/// Run core33 pipeline directly over an f32 series, accumulating in f64 without memory copy.
#[inline]
pub fn run_core33_f32(x: &[f32], scratch: &mut Scratch, out: &mut [f64]) {
    debug_assert!(out.len() >= CORE33_COUNT);

    let n = x.len();
    if n == 0 {
        out[..CORE33_COUNT].fill(f64::NAN);
        return;
    }

    scratch.ensure_capacity(n);

    // Pass 1 f32
    let p1 = kernels::reduce::pass1_f32(x);
    if p1.has_nan {
        out[..CORE33_COUNT].fill(f64::NAN);
        return;
    }

    // Pass 2 Fused f32
    let p2 = kernels::reduce::pass2_fused_f32(x, p1.mean, p1.constant, &mut scratch.centered);

    // Quantiles
    let quantiles = kernels::sort::quantiles_f32(x, &mut scratch.sorted);

    out[0] = p1.mean;
    out[1] = p2.std;
    out[2] = p2.var;
    out[3] = p1.min;
    out[4] = p1.max;
    out[5] = quantiles[0];
    out[6] = quantiles[1];
    out[7] = quantiles[2];
    out[8] = quantiles[3];
    out[9] = quantiles[4];
    out[10] = p2.skewness;
    out[11] = p2.kurtosis;
    out[12] = p1.abs_energy;
    out[13] = (p1.abs_energy / (n as f64)).sqrt();

    let (m_abs_ch, m_ch, cid, m_2nd_der) = kernels::reduce::successive_differences_f32(x, p2.std);
    out[14] = m_abs_ch;
    out[15] = m_ch;
    out[16] = cid;
    out[17] = m_2nd_der;

    out[18] = p2.zero_crossings;
    out[19] = p2.mean_crossings;
    out[20] = kernels::reduce::number_of_peaks_f32(x, 3);
    out[21] = p2.strike_above;
    out[22] = p2.strike_below;

    let acf = kernels::reduce::autocorr_multi(&scratch.centered, p2.var);
    out[23] = acf[0];
    out[24] = acf[1];
    out[25] = acf[2];
    out[26] = acf[3];

    let (slope, r2) = kernels::reduce::linear_trend(&scratch.centered, p2.var);
    out[27] = slope;
    out[28] = r2;

    out[29] = kernels::perm::permutation_entropy_f32(x);

    let (dom, cent, sent) = kernels::fft::spectral_features_f32(x, p1.constant, scratch);
    out[30] = dom;
    out[31] = cent;
    out[32] = sent;
}

/// Run core33 pipeline over f32 series writing directly to f32 output buffer.
#[inline]
pub fn run_core33_f32_out32(x: &[f32], scratch: &mut Scratch, out: &mut [f32]) {
    let mut tmp = [0.0f64; CORE33_COUNT];
    run_core33_f32(x, scratch, &mut tmp);
    for (o, &v) in out[..CORE33_COUNT].iter_mut().zip(tmp.iter()) {
        *o = v as f32;
    }
}
