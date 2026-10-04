#![deny(unsafe_code)]

//! Derived series views and invariance pruning.
//!
//! Computes views (`raw`, `diff`, `diff2`, `detrend`, `znorm`, `abs`, `logret`, `rank`)
//! directly into scratchpad memory without allocating intermediate Python numpy arrays.
//! Redundant (view, feature) pairs are pruned based on declared invariances.

use crate::registry::Invariances;

pub const SUPPORTED_VIEWS: &[&str] = &[
    "raw", "diff", "diff2", "detrend", "znorm", "abs", "logret", "rank",
];

/// Check whether a (view, feature) pair should be pruned as mathematically redundant.
pub fn is_pruned(view: &str, feat_name: &str, inv: Invariances) -> bool {
    match view {
        "raw" => false,
        "znorm" => {
            // Mean is identically 0; variance and std are identically 1
            if feat_name == "mean" || feat_name == "std" || feat_name == "var" {
                return true;
            }
            // Features invariant to both shift and scale have identical values on znorm as raw
            inv.contains(Invariances::SHIFT | Invariances::SCALE)
        }
        "rank" => {
            // Rank moments are deterministic functions of series length n
            if feat_name == "mean" || feat_name == "std" || feat_name == "var" {
                return true;
            }
            // Permutation entropy is invariant under monotonic transformation
            if inv.contains(Invariances::MONOTONE) {
                return true;
            }
            false
        }
        "detrend" => {
            // Trend slope is identically 0 on linearly detrended series
            if feat_name == "trend_slope" || feat_name == "trend_r2" {
                return true;
            }
            false
        }
        _ => false,
    }
}

/// Compute a derived view of series `x` into `out`.
pub fn compute_view(x: &[f64], view: &str, out: &mut Vec<f64>) {
    let n = x.len();
    out.clear();

    match view {
        "raw" => {
            out.extend_from_slice(x);
        }
        "diff" => {
            if n > 1 {
                out.reserve(n - 1);
                for i in 1..n {
                    out.push(x[i] - x[i - 1]);
                }
            } else {
                out.push(0.0);
            }
        }
        "diff2" => {
            if n > 2 {
                out.reserve(n - 2);
                for i in 2..n {
                    let d1 = x[i] - x[i - 1];
                    let d0 = x[i - 1] - x[i - 2];
                    out.push(d1 - d0);
                }
            } else {
                out.push(0.0);
            }
        }
        "detrend" => {
            if n < 2 {
                out.extend_from_slice(x);
                return;
            }
            let nf = n as f64;
            let sum_x: f64 = x.iter().sum();
            let mean_x = sum_x / nf;

            // Compute OLS linear trend slope
            let mut sum_xy = 0.0f64;
            let sum_t2 = (nf - 1.0) * nf * (2.0 * nf - 1.0) / 6.0;
            let mean_t = (nf - 1.0) / 2.0;

            for (t, &val) in x.iter().enumerate() {
                sum_xy += (t as f64) * val;
            }
            let denom = sum_t2 - nf * mean_t * mean_t;
            let slope = if denom.abs() > 1e-12 {
                (sum_xy - nf * mean_t * mean_x) / denom
            } else {
                0.0
            };
            let intercept = mean_x - slope * mean_t;

            out.reserve(n);
            for (t, &val) in x.iter().enumerate() {
                let trend_val = intercept + slope * (t as f64);
                out.push(val - trend_val);
            }
        }
        "znorm" => {
            if n < 2 {
                out.extend_from_slice(x);
                return;
            }
            let nf = n as f64;
            let sum: f64 = x.iter().sum();
            let mean = sum / nf;
            let var: f64 = x.iter().map(|&v| (v - mean) * (v - mean)).sum::<f64>() / nf;
            let std = var.sqrt();

            out.reserve(n);
            if std > 1e-12 {
                for &v in x {
                    out.push((v - mean) / std);
                }
            } else {
                out.resize(n, 0.0);
            }
        }
        "abs" => {
            out.reserve(n);
            for &v in x {
                out.push(v.abs());
            }
        }
        "logret" => {
            if n > 1 {
                out.reserve(n - 1);
                const EPS: f64 = 1e-8;
                for i in 1..n {
                    let v_curr = x[i].abs() + EPS;
                    let v_prev = x[i - 1].abs() + EPS;
                    out.push((v_curr / v_prev).ln());
                }
            } else {
                out.push(0.0);
            }
        }
        "rank" => {
            if n == 0 {
                return;
            }
            // Pair each element with its index: (value, original_idx)
            let mut indexed: Vec<(f64, usize)> =
                x.iter().copied().enumerate().map(|(i, v)| (v, i)).collect();
            indexed.sort_unstable_by(|a, b| f64::total_cmp(&a.0, &b.0));

            out.resize(n, 0.0);
            let nf = n as f64;
            for (rank_pos, (_val, orig_idx)) in indexed.into_iter().enumerate() {
                out[orig_idx] = (rank_pos + 1) as f64 / nf;
            }
        }
        _ => {
            out.extend_from_slice(x);
        }
    }
}
