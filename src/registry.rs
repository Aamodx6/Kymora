#![deny(unsafe_code)]

//! Single source of truth for all feature definitions, aliases, needs, and profiles.

use std::collections::HashMap;
use std::sync::LazyLock;

use crate::intermediates::{Intermediates, Needs};
use crate::kernels;

#[derive(Debug, Clone, Copy, PartialEq, Eq)]
pub enum CostClass {
    A, // Fused reductions (O(N) memory/SIMD)
    B, // Order statistics / selection (O(N) - O(N log N))
    C, // Spectral / FFT (O(N log N))
    D, // Autocorrelations / lags (O(N * K))
    E, // Heavy / quadratic (O(N * M) or O(N^2))
}

bitflags::bitflags! {
    #[derive(Debug, Clone, Copy, PartialEq, Eq)]
    pub struct ProfileMask: u8 {
        const MINIMAL  = 1 << 0;
        const CORE33   = 1 << 1;
        const EXTENDED = 1 << 2;
        const FULL     = 1 << 3;
        const HEAVY    = 1 << 4;
    }
}

const MIN_ALL: ProfileMask = ProfileMask::MINIMAL
    .union(ProfileMask::CORE33)
    .union(ProfileMask::EXTENDED)
    .union(ProfileMask::FULL);

const CORE_ALL: ProfileMask = ProfileMask::CORE33
    .union(ProfileMask::EXTENDED)
    .union(ProfileMask::FULL);

const EXT_ALL: ProfileMask = ProfileMask::EXTENDED.union(ProfileMask::FULL);
const FULL_ONLY: ProfileMask = ProfileMask::FULL;

#[derive(Debug, Clone, Copy)]
pub enum FeatureCompute {
    Fn(fn(&[f64], &Intermediates) -> f64),
    FftCoeff { k: usize, attr: usize },
    Symmetry { r: f64 },
    LargeStd { r: f64 },
    RatioBeyondR { r: f64 },
    EnergyChunk { seg: usize, num: usize },
    Decile { idx: usize },
    Pacf { lag: usize },
    Acf10 { lag: usize },
    C3 { lag: usize },
    TimeRev { lag: usize },
    CrossingM { m: f64 },
    Peaks { n: usize },
}

bitflags::bitflags! {
    #[derive(Debug, Clone, Copy, PartialEq, Eq)]
    pub struct Invariances: u8 {
        const SHIFT    = 1 << 0;
        const SCALE    = 1 << 1;
        const MONOTONE = 1 << 2;
    }
}

pub struct FeatureDef {
    pub name: &'static str,
    pub aliases: &'static [&'static str],
    pub needs: Needs,
    pub cost: CostClass,
    pub profiles: ProfileMask,
    pub compute: FeatureCompute,
    pub invariances: Invariances,
}

impl FeatureDef {
    #[inline]
    pub fn compute(&self, x: &[f64], inter: &Intermediates) -> f64 {
        match self.compute {
            FeatureCompute::Fn(f) => f(x, inter),
            FeatureCompute::FftCoeff { k, attr } => kernels::fft::fft_coeff(inter.fft_out, k, attr),
            FeatureCompute::Symmetry { r } => {
                let diff = (inter.p1.mean - inter.quantiles[0]).abs();
                let range = inter.p1.max - inter.p1.min;
                if diff < r * range {
                    1.0
                } else {
                    0.0
                }
            }
            FeatureCompute::LargeStd { r } => {
                let range = inter.p1.max - inter.p1.min;
                if inter.p2.std > r * range {
                    1.0
                } else {
                    0.0
                }
            }
            FeatureCompute::RatioBeyondR { r } => {
                kernels::reduce::ratio_beyond_r_sigma(inter.centered, inter.p2.std, r)
            }
            FeatureCompute::EnergyChunk { seg, num } => {
                kernels::reduce::energy_ratio_chunk(x, inter.p1.abs_energy, seg, num)
            }
            FeatureCompute::Decile { idx } => inter.deciles[idx],
            FeatureCompute::Pacf { lag } => {
                if (1..=9).contains(&lag) {
                    inter.pacf_9[lag - 1]
                } else {
                    f64::NAN
                }
            }
            FeatureCompute::Acf10 { lag } => {
                if lag < 10 {
                    inter.acf_10[lag]
                } else {
                    f64::NAN
                }
            }
            FeatureCompute::C3 { lag } => match lag {
                1 => inter.c3.0,
                2 => inter.c3.1,
                3 => inter.c3.2,
                _ => kernels::reduce::c3(x, lag),
            },
            FeatureCompute::TimeRev { lag } => match lag {
                1 => inter.tr.0,
                2 => inter.tr.1,
                3 => inter.tr.2,
                _ => kernels::reduce::time_reversal_asymmetry_statistic(x, lag),
            },
            FeatureCompute::CrossingM { m } => {
                if (m - (-1.0)).abs() < 1e-6 {
                    inter.crossings_extra.0
                } else if (m - 1.0).abs() < 1e-6 {
                    inter.crossings_extra.1
                } else {
                    kernels::reduce::number_crossing_m(x, m)
                }
            }
            FeatureCompute::Peaks { n } => match n {
                1 => inter.peaks_extra.0,
                3 => inter.peaks,
                5 => inter.peaks_extra.1,
                10 => inter.peaks_extra.2,
                50 => inter.peaks_extra.3,
                _ => kernels::reduce::number_of_peaks(x, n),
            },
        }
    }
}

pub fn infer_invariances(name: &str) -> Invariances {
    if name == "permutation_entropy" {
        return Invariances::SHIFT
            .union(Invariances::SCALE)
            .union(Invariances::MONOTONE);
    }
    if name.starts_with("autocorr")
        || name == "skewness"
        || name == "kurtosis"
        || name == "mean_crossings"
        || name == "spectral_entropy"
        || name == "dominant_frequency"
    {
        return Invariances::SHIFT.union(Invariances::SCALE);
    }
    if name == "std"
        || name == "var"
        || name == "mean_abs_change"
        || name == "cid_ce"
        || name == "mean_second_derivative_central"
        || name.starts_with("pacf")
    {
        return Invariances::SHIFT;
    }
    if name == "zero_crossings"
        || name.starts_with("c3")
        || name.starts_with("time_reversal")
        || name == "abs_energy"
    {
        return Invariances::SCALE;
    }
    Invariances::empty()
}

fn add_feat(
    list: &mut Vec<FeatureDef>,
    name: &'static str,
    aliases: &'static [&'static str],
    needs: Needs,
    cost: CostClass,
    profiles: ProfileMask,
    compute: FeatureCompute,
) {
    let invariances = infer_invariances(name);
    list.push(FeatureDef {
        name,
        aliases,
        needs,
        cost,
        profiles,
        compute,
        invariances,
    });
}

pub static FEATURES: LazyLock<Vec<FeatureDef>> = LazyLock::new(|| {
    let mut list = Vec::with_capacity(600);

    // =========================================================================
    // Core 33 Features (indices 0..32 strictly frozen in exact canonical order)
    // =========================================================================
    // 0: mean
    add_feat(
        &mut list,
        "mean",
        &["tsfresh__mean"],
        Needs::PASS1,
        CostClass::A,
        MIN_ALL,
        FeatureCompute::Fn(|_x, inter| inter.p1.mean),
    );
    // 1: std
    add_feat(
        &mut list,
        "std",
        &["standard_deviation", "tsfresh__standard_deviation"],
        Needs::PASS1.union(Needs::PASS2),
        CostClass::A,
        MIN_ALL,
        FeatureCompute::Fn(|_x, inter| inter.p2.std),
    );
    // 2: var
    add_feat(
        &mut list,
        "var",
        &["variance", "tsfresh__variance"],
        Needs::PASS1.union(Needs::PASS2),
        CostClass::A,
        MIN_ALL,
        FeatureCompute::Fn(|_x, inter| inter.p2.var),
    );
    // 3: min
    add_feat(
        &mut list,
        "min",
        &["minimum", "tsfresh__minimum"],
        Needs::PASS1,
        CostClass::A,
        MIN_ALL,
        FeatureCompute::Fn(|_x, inter| inter.p1.min),
    );
    // 4: max
    add_feat(
        &mut list,
        "max",
        &["maximum", "tsfresh__maximum"],
        Needs::PASS1,
        CostClass::A,
        MIN_ALL,
        FeatureCompute::Fn(|_x, inter| inter.p1.max),
    );
    // 5: median
    add_feat(
        &mut list,
        "median",
        &["tsfresh__median"],
        Needs::SELECT,
        CostClass::B,
        CORE_ALL,
        FeatureCompute::Fn(|_x, inter| inter.quantiles[0]),
    );
    // 6: quantile_10
    add_feat(
        &mut list,
        "quantile_10",
        &["tsfresh__quantile__q_0.1"],
        Needs::SELECT,
        CostClass::B,
        CORE_ALL,
        FeatureCompute::Fn(|_x, inter| inter.quantiles[1]),
    );
    // 7: quantile_25
    add_feat(
        &mut list,
        "quantile_25",
        &["tsfresh__quantile__q_0.25"],
        Needs::SELECT,
        CostClass::B,
        CORE_ALL,
        FeatureCompute::Fn(|_x, inter| inter.quantiles[2]),
    );
    // 8: quantile_75
    add_feat(
        &mut list,
        "quantile_75",
        &["tsfresh__quantile__q_0.75"],
        Needs::SELECT,
        CostClass::B,
        CORE_ALL,
        FeatureCompute::Fn(|_x, inter| inter.quantiles[3]),
    );
    // 9: quantile_90
    add_feat(
        &mut list,
        "quantile_90",
        &["tsfresh__quantile__q_0.9"],
        Needs::SELECT,
        CostClass::B,
        CORE_ALL,
        FeatureCompute::Fn(|_x, inter| inter.quantiles[4]),
    );
    // 10: skewness
    add_feat(
        &mut list,
        "skewness",
        &["tsfresh__skewness"],
        Needs::PASS1.union(Needs::PASS2),
        CostClass::A,
        CORE_ALL,
        FeatureCompute::Fn(|_x, inter| inter.p2.skewness),
    );
    // 11: kurtosis
    add_feat(
        &mut list,
        "kurtosis",
        &["tsfresh__kurtosis"],
        Needs::PASS1.union(Needs::PASS2),
        CostClass::A,
        CORE_ALL,
        FeatureCompute::Fn(|_x, inter| inter.p2.kurtosis),
    );
    // 12: abs_energy
    add_feat(
        &mut list,
        "abs_energy",
        &["energy", "tsfresh__abs_energy"],
        Needs::PASS1,
        CostClass::A,
        MIN_ALL,
        FeatureCompute::Fn(|_x, inter| inter.p1.abs_energy),
    );
    // 13: root_mean_square
    add_feat(
        &mut list,
        "root_mean_square",
        &["tsfresh__root_mean_square"],
        Needs::PASS1,
        CostClass::A,
        MIN_ALL,
        FeatureCompute::Fn(|x, inter| {
            let n = x.len();
            if n == 0 {
                f64::NAN
            } else {
                (inter.p1.abs_energy / (n as f64)).sqrt()
            }
        }),
    );
    // 14: mean_abs_change
    add_feat(
        &mut list,
        "mean_abs_change",
        &["tsfresh__mean_abs_change"],
        Needs::DIFFS,
        CostClass::A,
        CORE_ALL,
        FeatureCompute::Fn(|_x, inter| inter.diffs.0),
    );
    // 15: mean_change
    add_feat(
        &mut list,
        "mean_change",
        &["tsfresh__mean_change"],
        Needs::DIFFS,
        CostClass::A,
        MIN_ALL,
        FeatureCompute::Fn(|_x, inter| inter.diffs.1),
    );
    // 16: cid_ce
    add_feat(
        &mut list,
        "cid_ce",
        &["tsfresh__cid_ce__normalize_True"],
        Needs::PASS1.union(Needs::PASS2).union(Needs::DIFFS),
        CostClass::A,
        CORE_ALL,
        FeatureCompute::Fn(|_x, inter| inter.diffs.2),
    );
    // 17: mean_second_derivative_central
    add_feat(
        &mut list,
        "mean_second_derivative_central",
        &["tsfresh__mean_second_derivative_central"],
        Needs::DIFFS,
        CostClass::A,
        CORE_ALL,
        FeatureCompute::Fn(|_x, inter| inter.diffs.3),
    );
    // 18: zero_crossings
    add_feat(
        &mut list,
        "zero_crossings",
        &["tsfresh__number_crossing_m__m_0"],
        Needs::PASS1.union(Needs::PASS2),
        CostClass::A,
        MIN_ALL,
        FeatureCompute::Fn(|_x, inter| inter.p2.zero_crossings),
    );
    // 19: mean_crossings
    add_feat(
        &mut list,
        "mean_crossings",
        &[],
        Needs::PASS1.union(Needs::PASS2),
        CostClass::A,
        MIN_ALL,
        FeatureCompute::Fn(|_x, inter| inter.p2.mean_crossings),
    );
    // 20: number_of_peaks
    add_feat(
        &mut list,
        "number_of_peaks",
        &["tsfresh__number_peaks__n_3"],
        Needs::PEAKS,
        CostClass::A,
        CORE_ALL,
        FeatureCompute::Fn(|_x, inter| inter.peaks),
    );
    // 21: longest_strike_above_mean
    add_feat(
        &mut list,
        "longest_strike_above_mean",
        &["tsfresh__longest_strike_above_mean"],
        Needs::PASS1.union(Needs::PASS2),
        CostClass::A,
        CORE_ALL,
        FeatureCompute::Fn(|_x, inter| inter.p2.strike_above),
    );
    // 22: longest_strike_below_mean
    add_feat(
        &mut list,
        "longest_strike_below_mean",
        &["tsfresh__longest_strike_below_mean"],
        Needs::PASS1.union(Needs::PASS2),
        CostClass::A,
        CORE_ALL,
        FeatureCompute::Fn(|_x, inter| inter.p2.strike_below),
    );
    // 23: autocorr_lag_1
    add_feat(
        &mut list,
        "autocorr_lag_1",
        &["tsfresh__autocorrelation__lag_1"],
        Needs::PASS1.union(Needs::PASS2).union(Needs::ACF),
        CostClass::D,
        CORE_ALL,
        FeatureCompute::Fn(|_x, inter| inter.acf[0]),
    );
    // 24: autocorr_lag_2
    add_feat(
        &mut list,
        "autocorr_lag_2",
        &["tsfresh__autocorrelation__lag_2"],
        Needs::PASS1.union(Needs::PASS2).union(Needs::ACF),
        CostClass::D,
        CORE_ALL,
        FeatureCompute::Fn(|_x, inter| inter.acf[1]),
    );
    // 25: autocorr_lag_5
    add_feat(
        &mut list,
        "autocorr_lag_5",
        &["tsfresh__autocorrelation__lag_5"],
        Needs::PASS1.union(Needs::PASS2).union(Needs::ACF),
        CostClass::D,
        CORE_ALL,
        FeatureCompute::Fn(|_x, inter| inter.acf[2]),
    );
    // 26: autocorr_lag_10
    add_feat(
        &mut list,
        "autocorr_lag_10",
        &["tsfresh__autocorrelation__lag_10"],
        Needs::PASS1.union(Needs::PASS2).union(Needs::ACF),
        CostClass::D,
        CORE_ALL,
        FeatureCompute::Fn(|_x, inter| inter.acf[3]),
    );
    // 27: trend_slope
    add_feat(
        &mut list,
        "trend_slope",
        &["tsfresh__linear_trend__attr_\"slope\""],
        Needs::PASS1.union(Needs::PASS2).union(Needs::TREND),
        CostClass::A,
        CORE_ALL,
        FeatureCompute::Fn(|_x, inter| inter.trend.0),
    );
    // 28: trend_r2
    add_feat(
        &mut list,
        "trend_r2",
        &["tsfresh__linear_trend__attr_\"rvalue\""],
        Needs::PASS1.union(Needs::PASS2).union(Needs::TREND),
        CostClass::A,
        CORE_ALL,
        FeatureCompute::Fn(|_x, inter| inter.trend.1),
    );
    // 29: permutation_entropy
    add_feat(
        &mut list,
        "permutation_entropy",
        &["tsfresh__permutation_entropy__dimension_3__tau_1"],
        Needs::PERM,
        CostClass::A,
        CORE_ALL,
        FeatureCompute::Fn(|_x, inter| inter.perm_entropy),
    );
    // 30: dominant_frequency
    add_feat(
        &mut list,
        "dominant_frequency",
        &[],
        Needs::PASS1.union(Needs::SPECTRUM),
        CostClass::C,
        CORE_ALL,
        FeatureCompute::Fn(|_x, inter| inter.spectral.0),
    );
    // 31: spectral_centroid
    add_feat(
        &mut list,
        "spectral_centroid",
        &[],
        Needs::PASS1.union(Needs::SPECTRUM),
        CostClass::C,
        CORE_ALL,
        FeatureCompute::Fn(|_x, inter| inter.spectral.1),
    );
    // 32: spectral_entropy
    add_feat(
        &mut list,
        "spectral_entropy",
        &[],
        Needs::PASS1.union(Needs::SPECTRUM),
        CostClass::C,
        CORE_ALL,
        FeatureCompute::Fn(|_x, inter| inter.spectral.2),
    );

    // =========================================================================
    // Extended Catalog Features (indices 33..): Distribution+, Change, Lags, etc.
    // =========================================================================
    add_feat(
        &mut list,
        "sum_values",
        &["tsfresh__sum_values"],
        Needs::PASS1,
        CostClass::A,
        EXT_ALL,
        FeatureCompute::Fn(|_x, inter| inter.p1.sum),
    );
    add_feat(
        &mut list,
        "length",
        &["tsfresh__length"],
        Needs::empty(),
        CostClass::A,
        EXT_ALL,
        FeatureCompute::Fn(|x, _inter| x.len() as f64),
    );
    add_feat(
        &mut list,
        "count_above_mean",
        &["tsfresh__count_above_mean"],
        Needs::PASS1.union(Needs::PASS2),
        CostClass::A,
        EXT_ALL,
        FeatureCompute::Fn(|_x, inter| inter.p2.count_above_mean),
    );
    add_feat(
        &mut list,
        "count_below_mean",
        &["tsfresh__count_below_mean"],
        Needs::PASS1.union(Needs::PASS2),
        CostClass::A,
        EXT_ALL,
        FeatureCompute::Fn(|_x, inter| inter.p2.count_below_mean),
    );
    add_feat(
        &mut list,
        "has_duplicate",
        &["tsfresh__has_duplicate"],
        Needs::SORTED,
        CostClass::B,
        EXT_ALL,
        FeatureCompute::Fn(|_x, inter| if inter.has_duplicate { 1.0 } else { 0.0 }),
    );
    add_feat(
        &mut list,
        "has_duplicate_max",
        &["tsfresh__has_duplicate_max"],
        Needs::PASS1,
        CostClass::A,
        EXT_ALL,
        FeatureCompute::Fn(|_x, inter| if inter.p1.max_count > 1 { 1.0 } else { 0.0 }),
    );
    add_feat(
        &mut list,
        "has_duplicate_min",
        &["tsfresh__has_duplicate_min"],
        Needs::PASS1,
        CostClass::A,
        EXT_ALL,
        FeatureCompute::Fn(|_x, inter| if inter.p1.min_count > 1 { 1.0 } else { 0.0 }),
    );
    add_feat(
        &mut list,
        "variance_larger_than_standard_deviation",
        &["tsfresh__variance_larger_than_standard_deviation"],
        Needs::PASS1.union(Needs::PASS2),
        CostClass::A,
        EXT_ALL,
        FeatureCompute::Fn(|_x, inter| {
            if inter.p2.var > inter.p2.std {
                1.0
            } else {
                0.0
            }
        }),
    );
    add_feat(
        &mut list,
        "variation_coefficient",
        &["tsfresh__variation_coefficient"],
        Needs::PASS1.union(Needs::PASS2),
        CostClass::A,
        EXT_ALL,
        FeatureCompute::Fn(|_x, inter| {
            if inter.p1.mean != 0.0 {
                inter.p2.std / inter.p1.mean
            } else {
                f64::NAN
            }
        }),
    );
    add_feat(
        &mut list,
        "first_location_of_maximum",
        &["tsfresh__first_location_of_maximum"],
        Needs::PASS1,
        CostClass::A,
        EXT_ALL,
        FeatureCompute::Fn(|x, inter| {
            let n = x.len();
            if n == 0 {
                f64::NAN
            } else {
                inter.p1.first_max_idx as f64 / n as f64
            }
        }),
    );
    add_feat(
        &mut list,
        "first_location_of_minimum",
        &["tsfresh__first_location_of_minimum"],
        Needs::PASS1,
        CostClass::A,
        EXT_ALL,
        FeatureCompute::Fn(|x, inter| {
            let n = x.len();
            if n == 0 {
                f64::NAN
            } else {
                inter.p1.first_min_idx as f64 / n as f64
            }
        }),
    );
    add_feat(
        &mut list,
        "last_location_of_maximum",
        &["tsfresh__last_location_of_maximum"],
        Needs::PASS1,
        CostClass::A,
        EXT_ALL,
        FeatureCompute::Fn(|x, inter| {
            let n = x.len();
            if n == 0 {
                f64::NAN
            } else {
                inter.p1.last_max_idx as f64 / n as f64
            }
        }),
    );
    add_feat(
        &mut list,
        "last_location_of_minimum",
        &["tsfresh__last_location_of_minimum"],
        Needs::PASS1,
        CostClass::A,
        EXT_ALL,
        FeatureCompute::Fn(|x, inter| {
            let n = x.len();
            if n == 0 {
                f64::NAN
            } else {
                inter.p1.last_min_idx as f64 / n as f64
            }
        }),
    );
    add_feat(
        &mut list,
        "absolute_sum_of_changes",
        &["tsfresh__absolute_sum_of_changes"],
        Needs::DIFFS,
        CostClass::A,
        EXT_ALL,
        FeatureCompute::Fn(|_x, inter| inter.abs_sum_changes),
    );
    add_feat(
        &mut list,
        "cid_ce_raw",
        &["tsfresh__cid_ce__normalize_False"],
        Needs::DIFFS,
        CostClass::A,
        EXT_ALL,
        FeatureCompute::Fn(|_x, inter| inter.cid_ce_raw),
    );

    // C3 Nonlinear
    add_feat(
        &mut list,
        "c3__lag_1",
        &["tsfresh__c3__lag_1"],
        Needs::C3,
        CostClass::A,
        EXT_ALL,
        FeatureCompute::C3 { lag: 1 },
    );
    add_feat(
        &mut list,
        "c3__lag_2",
        &["tsfresh__c3__lag_2"],
        Needs::C3,
        CostClass::A,
        EXT_ALL,
        FeatureCompute::C3 { lag: 2 },
    );
    add_feat(
        &mut list,
        "c3__lag_3",
        &["tsfresh__c3__lag_3"],
        Needs::C3,
        CostClass::A,
        EXT_ALL,
        FeatureCompute::C3 { lag: 3 },
    );

    // Time Reversal Asymmetry
    add_feat(
        &mut list,
        "time_reversal_asymmetry_statistic__lag_1",
        &["tsfresh__time_reversal_asymmetry_statistic__lag_1"],
        Needs::NONLIN,
        CostClass::A,
        EXT_ALL,
        FeatureCompute::TimeRev { lag: 1 },
    );
    add_feat(
        &mut list,
        "time_reversal_asymmetry_statistic__lag_2",
        &["tsfresh__time_reversal_asymmetry_statistic__lag_2"],
        Needs::NONLIN,
        CostClass::A,
        EXT_ALL,
        FeatureCompute::TimeRev { lag: 2 },
    );
    add_feat(
        &mut list,
        "time_reversal_asymmetry_statistic__lag_3",
        &["tsfresh__time_reversal_asymmetry_statistic__lag_3"],
        Needs::NONLIN,
        CostClass::A,
        EXT_ALL,
        FeatureCompute::TimeRev { lag: 3 },
    );

    // Crossings extra
    add_feat(
        &mut list,
        "number_crossing_m__m_-1",
        &["tsfresh__number_crossing_m__m_-1"],
        Needs::CROSSINGS,
        CostClass::A,
        EXT_ALL,
        FeatureCompute::CrossingM { m: -1.0 },
    );
    add_feat(
        &mut list,
        "number_crossing_m__m_1",
        &["tsfresh__number_crossing_m__m_1"],
        Needs::CROSSINGS,
        CostClass::A,
        EXT_ALL,
        FeatureCompute::CrossingM { m: 1.0 },
    );

    // Peaks extra
    add_feat(
        &mut list,
        "number_peaks__n_1",
        &["tsfresh__number_peaks__n_1"],
        Needs::PEAKS,
        CostClass::A,
        EXT_ALL,
        FeatureCompute::Peaks { n: 1 },
    );
    add_feat(
        &mut list,
        "number_peaks__n_5",
        &["tsfresh__number_peaks__n_5"],
        Needs::PEAKS,
        CostClass::A,
        EXT_ALL,
        FeatureCompute::Peaks { n: 5 },
    );
    add_feat(
        &mut list,
        "number_peaks__n_10",
        &["tsfresh__number_peaks__n_10"],
        Needs::PEAKS,
        CostClass::A,
        EXT_ALL,
        FeatureCompute::Peaks { n: 10 },
    );
    add_feat(
        &mut list,
        "number_peaks__n_50",
        &["tsfresh__number_peaks__n_50"],
        Needs::PEAKS,
        CostClass::A,
        EXT_ALL,
        FeatureCompute::Peaks { n: 50 },
    );

    // Linear trend extra
    add_feat(
        &mut list,
        "linear_trend__attr_\"intercept\"",
        &["tsfresh__linear_trend__attr_\"intercept\""],
        Needs::PASS1.union(Needs::PASS2).union(Needs::TREND),
        CostClass::A,
        EXT_ALL,
        FeatureCompute::Fn(|_x, inter| inter.trend_full.1),
    );
    add_feat(
        &mut list,
        "linear_trend__attr_\"stderr\"",
        &["tsfresh__linear_trend__attr_\"stderr\""],
        Needs::PASS1.union(Needs::PASS2).union(Needs::TREND),
        CostClass::A,
        EXT_ALL,
        FeatureCompute::Fn(|_x, inter| inter.trend_full.3),
    );

    // Autocorrelation extra lags
    add_feat(
        &mut list,
        "autocorrelation__lag_0",
        &["tsfresh__autocorrelation__lag_0"],
        Needs::PASS1.union(Needs::PASS2).union(Needs::ACF),
        CostClass::D,
        EXT_ALL,
        FeatureCompute::Acf10 { lag: 0 },
    );
    add_feat(
        &mut list,
        "autocorrelation__lag_3",
        &["tsfresh__autocorrelation__lag_3"],
        Needs::PASS1.union(Needs::PASS2).union(Needs::ACF),
        CostClass::D,
        EXT_ALL,
        FeatureCompute::Acf10 { lag: 3 },
    );
    add_feat(
        &mut list,
        "autocorrelation__lag_4",
        &["tsfresh__autocorrelation__lag_4"],
        Needs::PASS1.union(Needs::PASS2).union(Needs::ACF),
        CostClass::D,
        EXT_ALL,
        FeatureCompute::Acf10 { lag: 4 },
    );
    add_feat(
        &mut list,
        "autocorrelation__lag_6",
        &["tsfresh__autocorrelation__lag_6"],
        Needs::PASS1.union(Needs::PASS2).union(Needs::ACF),
        CostClass::D,
        EXT_ALL,
        FeatureCompute::Acf10 { lag: 6 },
    );
    add_feat(
        &mut list,
        "autocorrelation__lag_7",
        &["tsfresh__autocorrelation__lag_7"],
        Needs::PASS1.union(Needs::PASS2).union(Needs::ACF),
        CostClass::D,
        EXT_ALL,
        FeatureCompute::Acf10 { lag: 7 },
    );
    add_feat(
        &mut list,
        "autocorrelation__lag_8",
        &["tsfresh__autocorrelation__lag_8"],
        Needs::PASS1.union(Needs::PASS2).union(Needs::ACF),
        CostClass::D,
        EXT_ALL,
        FeatureCompute::Acf10 { lag: 8 },
    );
    add_feat(
        &mut list,
        "autocorrelation__lag_9",
        &["tsfresh__autocorrelation__lag_9"],
        Needs::PASS1.union(Needs::PASS2).union(Needs::ACF),
        CostClass::D,
        EXT_ALL,
        FeatureCompute::Acf10 { lag: 9 },
    );

    // PACF lags 1..9
    for lag in 1..=9 {
        let name: &'static str =
            Box::leak(format!("partial_autocorrelation__lag_{lag}").into_boxed_str());
        let tsfresh_alias: &'static str =
            Box::leak(format!("tsfresh__partial_autocorrelation__lag_{lag}").into_boxed_str());
        let aliases: &'static [&'static str] = Box::leak(vec![tsfresh_alias].into_boxed_slice());
        add_feat(
            &mut list,
            name,
            aliases,
            Needs::PASS1.union(Needs::PASS2).union(Needs::ACF),
            CostClass::D,
            EXT_ALL,
            FeatureCompute::Pacf { lag },
        );
    }

    // FFT Aggregated
    add_feat(
        &mut list,
        "fft_aggregated__aggtype_\"centroid\"",
        &["tsfresh__fft_aggregated__aggtype_\"centroid\""],
        Needs::PASS1.union(Needs::SPECTRUM),
        CostClass::C,
        EXT_ALL,
        FeatureCompute::Fn(|_x, inter| inter.fft_agg.centroid),
    );
    add_feat(
        &mut list,
        "fft_aggregated__aggtype_\"variance\"",
        &["tsfresh__fft_aggregated__aggtype_\"variance\""],
        Needs::PASS1.union(Needs::SPECTRUM),
        CostClass::C,
        EXT_ALL,
        FeatureCompute::Fn(|_x, inter| inter.fft_agg.variance),
    );
    add_feat(
        &mut list,
        "fft_aggregated__aggtype_\"skew\"",
        &["tsfresh__fft_aggregated__aggtype_\"skew\""],
        Needs::PASS1.union(Needs::SPECTRUM),
        CostClass::C,
        EXT_ALL,
        FeatureCompute::Fn(|_x, inter| inter.fft_agg.skew),
    );
    add_feat(
        &mut list,
        "fft_aggregated__aggtype_\"kurtosis\"",
        &["tsfresh__fft_aggregated__aggtype_\"kurtosis\""],
        Needs::PASS1.union(Needs::SPECTRUM),
        CostClass::C,
        EXT_ALL,
        FeatureCompute::Fn(|_x, inter| inter.fft_agg.kurtosis),
    );

    // Deciles 0.2, 0.3, 0.4, 0.6, 0.7, 0.8
    for &(idx, q_str) in &[
        (1, "0.2"),
        (2, "0.3"),
        (3, "0.4"),
        (5, "0.6"),
        (6, "0.7"),
        (7, "0.8"),
    ] {
        let name: &'static str = Box::leak(format!("quantile__q_{q_str}").into_boxed_str());
        let tsfresh_alias: &'static str =
            Box::leak(format!("tsfresh__quantile__q_{q_str}").into_boxed_str());
        let aliases: &'static [&'static str] = Box::leak(vec![tsfresh_alias].into_boxed_slice());
        add_feat(
            &mut list,
            name,
            aliases,
            Needs::SELECT,
            CostClass::B,
            EXT_ALL,
            FeatureCompute::Decile { idx },
        );
    }

    // Ratio beyond r sigma
    for &r in &[0.5f64, 1.0, 1.5, 2.0, 2.5, 3.0] {
        let name: &'static str = Box::leak(format!("ratio_beyond_r_sigma__r_{r}").into_boxed_str());
        let tsfresh_alias: &'static str =
            Box::leak(format!("tsfresh__ratio_beyond_r_sigma__r_{r}").into_boxed_str());
        let aliases: &'static [&'static str] = Box::leak(vec![tsfresh_alias].into_boxed_slice());
        add_feat(
            &mut list,
            name,
            aliases,
            Needs::PASS1.union(Needs::PASS2).union(Needs::CENTERED),
            CostClass::A,
            EXT_ALL,
            FeatureCompute::RatioBeyondR { r },
        );
    }

    // Large standard deviation
    for r_step in 1..=19 {
        let r = (r_step as f64) * 0.05;
        let name: &'static str =
            Box::leak(format!("large_standard_deviation__r_{r:.2}").into_boxed_str());
        let tsfresh_alias: &'static str =
            Box::leak(format!("tsfresh__large_standard_deviation__r_{r:.2}").into_boxed_str());
        let aliases: &'static [&'static str] = Box::leak(vec![tsfresh_alias].into_boxed_slice());
        add_feat(
            &mut list,
            name,
            aliases,
            Needs::PASS1.union(Needs::PASS2),
            CostClass::A,
            EXT_ALL,
            FeatureCompute::LargeStd { r },
        );
    }

    // Symmetry looking
    for r_step in 1..=20 {
        let r = (r_step as f64) * 0.05;
        let name: &'static str = Box::leak(format!("symmetry_looking__r_{r:.2}").into_boxed_str());
        let tsfresh_alias: &'static str =
            Box::leak(format!("tsfresh__symmetry_looking__r_{r:.2}").into_boxed_str());
        let aliases: &'static [&'static str] = Box::leak(vec![tsfresh_alias].into_boxed_slice());
        add_feat(
            &mut list,
            name,
            aliases,
            Needs::PASS1.union(Needs::SELECT),
            CostClass::B,
            EXT_ALL,
            FeatureCompute::Symmetry { r },
        );
    }

    // Energy ratio by chunks (10 segments)
    for seg in 0..10 {
        let name: &'static str = Box::leak(
            format!("energy_ratio_by_chunks__num_segments_10__segment_focus_{seg}")
                .into_boxed_str(),
        );
        let tsfresh_alias: &'static str = Box::leak(
            format!("tsfresh__energy_ratio_by_chunks__num_segments_10__segment_focus_{seg}")
                .into_boxed_str(),
        );
        let aliases: &'static [&'static str] = Box::leak(vec![tsfresh_alias].into_boxed_slice());
        add_feat(
            &mut list,
            name,
            aliases,
            Needs::PASS1,
            CostClass::A,
            EXT_ALL,
            FeatureCompute::EnergyChunk { seg, num: 10 },
        );
    }

    // =========================================================================
    // Full Catalog Features: 400 FFT Coefficients (k=0..99 x 4 attributes)
    // =========================================================================
    for k in 0..100 {
        for &(attr_idx, attr_str) in &[(0, "real"), (1, "imag"), (2, "abs"), (3, "angle")] {
            let name: &'static str = Box::leak(
                format!("fft_coefficient__coeff_{k}__attr_\"{attr_str}\"").into_boxed_str(),
            );
            let tsfresh_alias: &'static str = Box::leak(
                format!("tsfresh__fft_coefficient__coeff_{k}__attr_\"{attr_str}\"")
                    .into_boxed_str(),
            );
            let aliases: &'static [&'static str] =
                Box::leak(vec![tsfresh_alias].into_boxed_slice());
            add_feat(
                &mut list,
                name,
                aliases,
                Needs::PASS1.union(Needs::SPECTRUM),
                CostClass::C,
                FULL_ONLY,
                FeatureCompute::FftCoeff { k, attr: attr_idx },
            );
        }
    }

    list
});

static LOOKUP: LazyLock<HashMap<&'static str, usize>> = LazyLock::new(|| {
    let mut map = HashMap::with_capacity(FEATURES.len() * 3);
    for (i, def) in FEATURES.iter().enumerate() {
        map.insert(def.name, i);
        for &alias in def.aliases {
            map.insert(alias, i);
        }
    }
    map
});

/// Find feature index by canonical name or alias.
pub fn find_feature(name_or_alias: &str) -> Option<usize> {
    LOOKUP.get(name_or_alias).copied()
}

/// Documentation metadata for one core33 feature.
///
/// This is the single source of truth for `docs/features.md`, generated by
/// `tools/gen_feature_docs.py` from the built library. `definition` states
/// the exact formula as implemented; `min_len` is the shortest series the
/// feature is defined on (shorter input yields NaN); `nan_when` lists every
/// other condition producing NaN for otherwise-valid input. All three are
/// asserted by `tests/test_nan_policy.py` and `tests/test_features.py`.
pub struct CoreMeta {
    pub name: &'static str,
    pub definition: &'static str,
    pub min_len: usize,
    pub nan_when: &'static str,
}

/// Per-feature documentation for core33, in frozen column order.
pub static CORE33_META: [CoreMeta; 33] = [
    CoreMeta { name: "mean", definition: "sum(x)/n", min_len: 1, nan_when: "never" },
    CoreMeta { name: "std", definition: "sqrt(var), population (ddof=0)", min_len: 1, nan_when: "never" },
    CoreMeta { name: "var", definition: "sum((x-m)^2)/n, forced to exactly 0.0 on constant series", min_len: 1, nan_when: "never" },
    CoreMeta { name: "min", definition: "smallest value", min_len: 1, nan_when: "never" },
    CoreMeta { name: "max", definition: "largest value", min_len: 1, nan_when: "never" },
    CoreMeta { name: "median", definition: "50th percentile, linear interpolation (numpy default)", min_len: 1, nan_when: "never" },
    CoreMeta { name: "quantile_10", definition: "10th percentile, linear interpolation", min_len: 1, nan_when: "never" },
    CoreMeta { name: "quantile_25", definition: "25th percentile, linear interpolation", min_len: 1, nan_when: "never" },
    CoreMeta { name: "quantile_75", definition: "75th percentile, linear interpolation", min_len: 1, nan_when: "never" },
    CoreMeta { name: "quantile_90", definition: "90th percentile, linear interpolation", min_len: 1, nan_when: "never" },
    CoreMeta { name: "skewness", definition: "(m3/n)/(var*std), m3 = sum((x-m)^3); scipy bias=True", min_len: 2, nan_when: "std == 0" },
    CoreMeta { name: "kurtosis", definition: "(m4/n)/var^2 - 3 (Fisher excess); scipy bias=True", min_len: 2, nan_when: "std == 0" },
    CoreMeta { name: "abs_energy", definition: "sum(x^2)", min_len: 1, nan_when: "never" },
    CoreMeta { name: "root_mean_square", definition: "sqrt(sum(x^2)/n)", min_len: 1, nan_when: "never" },
    CoreMeta { name: "mean_abs_change", definition: "sum|x[i+1]-x[i]|/(n-1)", min_len: 2, nan_when: "n < 2" },
    CoreMeta { name: "mean_change", definition: "(x[n-1]-x[0])/(n-1)", min_len: 2, nan_when: "n < 2" },
    CoreMeta { name: "cid_ce", definition: "sqrt(sum(((x[i+1]-x[i])/std)^2)); exactly 0.0 when std == 0", min_len: 2, nan_when: "n < 2" },
    CoreMeta { name: "mean_second_derivative_central", definition: "sum(x[i+1]-2*x[i]+x[i-1])/(2*(n-2))", min_len: 3, nan_when: "n < 3" },
    CoreMeta { name: "zero_crossings", definition: "count of i with (x[i] > 0) != (x[i+1] > 0)", min_len: 1, nan_when: "never" },
    CoreMeta { name: "mean_crossings", definition: "count of i with (x[i] > m) != (x[i+1] > m)", min_len: 1, nan_when: "never" },
    CoreMeta { name: "number_of_peaks", definition: "count of i strictly greater than all 3 neighbors on each side", min_len: 1, nan_when: "never (0 when n <= 6)" },
    CoreMeta { name: "longest_strike_above_mean", definition: "longest run with x[i] > m", min_len: 1, nan_when: "never" },
    CoreMeta { name: "longest_strike_below_mean", definition: "longest run with x[i] < m", min_len: 1, nan_when: "never" },
    CoreMeta { name: "autocorr_lag_1", definition: "sum((x[i]-m)(x[i+1]-m))/((n-1)*var)", min_len: 2, nan_when: "n <= 1 or var == 0" },
    CoreMeta { name: "autocorr_lag_2", definition: "sum((x[i]-m)(x[i+2]-m))/((n-2)*var)", min_len: 3, nan_when: "n <= 2 or var == 0" },
    CoreMeta { name: "autocorr_lag_5", definition: "sum((x[i]-m)(x[i+5]-m))/((n-5)*var)", min_len: 6, nan_when: "n <= 5 or var == 0" },
    CoreMeta { name: "autocorr_lag_10", definition: "sum((x[i]-m)(x[i+10]-m))/((n-10)*var)", min_len: 11, nan_when: "n <= 10 or var == 0" },
    CoreMeta { name: "trend_slope", definition: "least-squares slope vs t = 0..n-1; exactly 0.0 on constant series", min_len: 2, nan_when: "n < 2" },
    CoreMeta { name: "trend_r2", definition: "squared Pearson r of (t, x)", min_len: 2, nan_when: "n < 2 or var == 0" },
    CoreMeta { name: "permutation_entropy", definition: "normalized order-3 delay-1 ordinal-pattern entropy (/ln 6)", min_len: 3, nan_when: "n < 3" },
    CoreMeta { name: "dominant_frequency", definition: "argmax power-bin frequency (k+1)/n over FFT bins 1..=n/2, DC excluded", min_len: 2, nan_when: "n < 2, constant series, or non-finite/zero total power" },
    CoreMeta { name: "spectral_centroid", definition: "sum(f*p)/sum(p) over FFT bins 1..=n/2", min_len: 2, nan_when: "n < 2, constant series, or non-finite/zero total power" },
    CoreMeta { name: "spectral_entropy", definition: "shannon(p/sum(p))/ln(nbins); 0.0 when nbins == 1", min_len: 2, nan_when: "n < 2, constant series, or non-finite/zero total power" },
];

/// Documentation metadata for a core33 feature by canonical name.
pub fn core_meta(name: &str) -> Option<&'static CoreMeta> {
    CORE33_META.iter().find(|m| m.name == name)
}
