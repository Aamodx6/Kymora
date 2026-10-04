//! PyO3 boundary: the only place Rust and Python touch.
//!
//! Responsibilities, in order:
//!   1. obtain zero-copy read views of the caller's numpy buffers,
//!   2. validate structure (shapes, lengths, window geometry) *before* any
//!      compute starts, mapping failures to `KymoraError` -> `ValueError`,
//!   3. release the GIL and run the pure-Rust extraction,
//!   4. shape or write directly into in-place numpy buffers.
//!
//! No `panic!`, `unwrap`, or `expect` on a user-reachable path.

use numpy::{
    IntoPyArray, PyArray1, PyArray2, PyArrayMethods, PyReadonlyArray1, PyReadonlyArray2,
    PyReadonlyArrayDyn, PyUntypedArrayMethods,
};
use pyo3::exceptions::PyTypeError;
use pyo3::prelude::*;
use std::collections::HashMap;

use crate::error::KymoraError;
use crate::extract;
use crate::features;
use crate::pipeline;
use crate::plan::FeaturePlan;
use crate::registry;
use crate::scratch::Scratch;

const TYPE_HELP: &str = "extract_features expects a 2D float64 or float32 array of shape \
    (n_series, length), or a list of 1D float64/float32 arrays for ragged series. \
    Other dtypes are rejected rather than silently copied — cast explicitly \
    with X.astype(np.float64).";

fn get_out_array<'py>(
    py: Python<'py>,
    nrows: usize,
    ncols: usize,
    out: Option<&Bound<'py, PyArray2<f64>>>,
) -> PyResult<Bound<'py, PyArray2<f64>>> {
    if let Some(user_out) = out {
        let shape = user_out.shape();
        if shape.len() != 2 || shape[0] != nrows || shape[1] != ncols {
            return Err(pyo3::exceptions::PyValueError::new_err(format!(
                "out array shape mismatch: expected ({nrows}, {ncols}), got {shape:?}"
            )));
        }
        Ok(user_out.clone())
    } else {
        Ok(PyArray2::<f64>::zeros(py, [nrows, ncols], false))
    }
}

/// Mutable write view of an f64 output array for in-place feature writes.
///
/// Centralizes the `as_slice_mut` uses of this module (the only `unsafe` in
/// the file) behind one audited point. Callers pass either a freshly
/// allocated `zeros` array, which cannot be aliased, or a caller-supplied
/// `out` buffer whose shape was validated by [`get_out_array`].
///
/// Contract upheld at every call site: the array is C-contiguous and
/// writeable (a non-contiguous or read-only buffer surfaces as `Err` below,
/// never as a partial borrow); the returned slice is the only live Rust
/// borrow of the data until the array is handed back to Python; the borrow is
/// created while the GIL is held and compute only touches the borrow, never
/// Python objects. A caller-supplied `out` buffer must not alias the input
/// series buffer (same rule as `numpy.copyto` with `out=`).
#[inline]
// `mut_from_ref` is the point of this helper (numpy hands out `&mut` from a
// shared `Bound`); soundness rests on the contract above, not on the borrow.
#[allow(clippy::mut_from_ref)]
fn out_slice_mut<'a>(arr: &'a Bound<'_, PyArray2<f64>>) -> Result<&'a mut [f64], KymoraError> {
    // SAFETY: upheld per the contract above.
    unsafe { arr.as_slice_mut() }.map_err(|_| KymoraError::NotContiguous { index: None })
}

/// f32-output variant of [`out_slice_mut`]; same contract.
#[inline]
// See `out_slice_mut` for why `mut_from_ref` is allowed here.
#[allow(clippy::mut_from_ref)]
fn out_slice_mut_f32<'a>(arr: &'a Bound<'_, PyArray2<f32>>) -> Result<&'a mut [f32], KymoraError> {
    // SAFETY: upheld per the contract above.
    unsafe { arr.as_slice_mut() }.map_err(|_| KymoraError::NotContiguous { index: None })
}

fn run_in_pool<F, R>(n_jobs: Option<usize>, f: F) -> R
where
    F: FnOnce() -> R + Send,
    R: Send,
{
    match n_jobs {
        Some(n) if n > 0 => {
            let pool = match rayon::ThreadPoolBuilder::new().num_threads(n).build() {
                Ok(p) => p,
                Err(_) => return f(),
            };
            pool.install(f)
        }
        _ => f(),
    }
}

/// extract_features(X, profile="core33", features=None, n_jobs=None, out=None, views=None, precision=None, out_dtype=None)
#[pyfunction]
#[pyo3(signature = (x, profile = None, features = None, n_jobs = None, out = None, views = None, precision = None, out_dtype = None))]
#[allow(clippy::too_many_arguments)]
pub fn extract_features<'py>(
    py: Python<'py>,
    x: &Bound<'py, PyAny>,
    profile: Option<&str>,
    features: Option<Vec<String>>,
    n_jobs: Option<usize>,
    out: Option<&Bound<'py, PyArray2<f64>>>,
    views: Option<Vec<String>>,
    precision: Option<&str>,
    out_dtype: Option<&str>,
) -> PyResult<Bound<'py, PyAny>> {
    let feat_refs = features.as_deref();
    let plan = FeaturePlan::build_with_views(profile, feat_refs, views.as_deref())?;
    let n_cols = plan.n_features();

    let wants_f32_out = matches!(out_dtype, Some("float32") | Some("f32"));
    let _wants_f32_precision = matches!(precision, Some("float32") | Some("f32"));

    // 1. 2D float64 fast path
    if let Ok(arr) = x.extract::<PyReadonlyArray2<f64>>() {
        let view = arr.as_array();
        let nrows = view.nrows();
        let ncols = view.ncols();
        if nrows == 0 {
            return Err(KymoraError::EmptyInput.into());
        }
        if ncols == 0 {
            return Err(KymoraError::ZeroLengthColumns.into());
        }
        let slice = view
            .as_slice()
            .ok_or(KymoraError::NotContiguous { index: None })?;

        if wants_f32_out {
            let out_arr = PyArray2::<f32>::zeros(py, [nrows, n_cols], false);
            let out_slice = out_slice_mut_f32(&out_arr)?;
            py.detach(|| {
                run_in_pool(n_jobs, || {
                    let mut tmp = vec![0.0f64; nrows * n_cols];
                    let rows: Vec<&[f64]> = slice.chunks_exact(ncols).collect();
                    crate::exec::extract_plan_into_slice(&rows, &plan, &mut tmp);
                    for (dst, &src) in out_slice.iter_mut().zip(tmp.iter()) {
                        *dst = src as f32;
                    }
                })
            });
            return Ok(out_arr.into_any());
        }

        let out_arr = get_out_array(py, nrows, n_cols, out)?;
        let out_slice = out_slice_mut(&out_arr)?;
        py.detach(|| {
            run_in_pool(n_jobs, || {
                let rows: Vec<&[f64]> = slice.chunks_exact(ncols).collect();
                crate::exec::extract_plan_into_slice(&rows, &plan, out_slice);
            })
        });
        return Ok(out_arr.into_any());
    }

    // 2. 2D float32 fast path
    if let Ok(arr) = x.extract::<PyReadonlyArray2<f32>>() {
        let view = arr.as_array();
        let nrows = view.nrows();
        let ncols = view.ncols();
        if nrows == 0 {
            return Err(KymoraError::EmptyInput.into());
        }
        if ncols == 0 {
            return Err(KymoraError::ZeroLengthColumns.into());
        }
        let slice = view
            .as_slice()
            .ok_or(KymoraError::NotContiguous { index: None })?;

        if wants_f32_out {
            let out_arr = PyArray2::<f32>::zeros(py, [nrows, n_cols], false);
            let out_slice = out_slice_mut_f32(&out_arr)?;
            py.detach(|| {
                run_in_pool(n_jobs, || {
                    let mut tmp = vec![0.0f64; nrows * n_cols];
                    let rows: Vec<&[f32]> = slice.chunks_exact(ncols).collect();
                    crate::exec::extract_into_slice_f32(&rows, &mut tmp, n_cols);
                    for (dst, &src) in out_slice.iter_mut().zip(tmp.iter()) {
                        *dst = src as f32;
                    }
                })
            });
            return Ok(out_arr.into_any());
        }

        let out_arr = get_out_array(py, nrows, n_cols, out)?;
        let out_slice = out_slice_mut(&out_arr)?;
        py.detach(|| {
            run_in_pool(n_jobs, || {
                let rows: Vec<&[f32]> = slice.chunks_exact(ncols).collect();
                crate::exec::extract_into_slice_f32(&rows, out_slice, n_cols);
            })
        });
        return Ok(out_arr.into_any());
    }

    // 3. List of 1D float64 arrays
    if let Ok(list) = x.extract::<Vec<PyReadonlyArray1<f64>>>() {
        let slices: Vec<&[f64]> = list
            .iter()
            .enumerate()
            .map(|(index, a)| {
                a.as_slice()
                    .map_err(|_| KymoraError::NotContiguous { index: Some(index) })
            })
            .collect::<Result<_, KymoraError>>()?;
        extract::validate_batch(&slices)?;
        let nrows = slices.len();
        let out_arr = get_out_array(py, nrows, n_cols, out)?;
        let out_slice = out_slice_mut(&out_arr)?;
        py.detach(|| {
            run_in_pool(n_jobs, || {
                crate::exec::extract_plan_into_slice(&slices, &plan, out_slice)
            })
        });
        return Ok(out_arr.into_any());
    }

    // 4. List of 1D float32 arrays
    if let Ok(list) = x.extract::<Vec<PyReadonlyArray1<f32>>>() {
        if list.is_empty() {
            return Err(KymoraError::EmptyInput.into());
        }
        let mut slices = Vec::with_capacity(list.len());
        for (index, a) in list.iter().enumerate() {
            let s = a
                .as_slice()
                .map_err(|_| KymoraError::NotContiguous { index: Some(index) })?;
            if s.is_empty() {
                return Err(KymoraError::EmptySeries { index }.into());
            }
            slices.push(s);
        }
        let nrows = slices.len();
        let out_arr = get_out_array(py, nrows, n_cols, out)?;
        let out_slice = out_slice_mut(&out_arr)?;
        py.detach(|| {
            run_in_pool(n_jobs, || {
                crate::exec::extract_into_slice_f32(&slices, out_slice, n_cols)
            })
        });
        return Ok(out_arr.into_any());
    }

    Err(PyTypeError::new_err(TYPE_HELP))
}

/// Compute pairwise cross-channel features between channel pairs.
pub fn compute_cross_features(channels: &[&[f64]], max_pairs: usize, out: &mut [f64]) {
    let n_ch = channels.len();
    if n_ch < 2 || channels[0].is_empty() {
        out.fill(0.0);
        return;
    }
    let n = channels[0].len();
    let nf = n as f64;

    let mut means = Vec::with_capacity(n_ch);
    let mut stds = Vec::with_capacity(n_ch);
    let mut centered: Vec<Vec<f64>> = Vec::with_capacity(n_ch);

    for ch in channels {
        let m = ch.iter().sum::<f64>() / nf;
        means.push(m);
        let mut c = Vec::with_capacity(n);
        let mut sum_sq = 0.0f64;
        for &v in *ch {
            let d = v - m;
            c.push(d);
            sum_sq += d * d;
        }
        let s = (sum_sq / nf).sqrt();
        stds.push(s);
        centered.push(c);
    }

    let mut pairs = Vec::new();
    for i in 0..n_ch {
        for j in (i + 1)..n_ch {
            pairs.push((i, j));
            if pairs.len() >= max_pairs {
                break;
            }
        }
        if pairs.len() >= max_pairs {
            break;
        }
    }

    let mut out_idx = 0usize;
    let mut all_abs_corrs = Vec::with_capacity(pairs.len());
    let max_lag = 10.min(n / 2);

    for &(i, j) in &pairs {
        let s_i = stds[i];
        let s_j = stds[j];
        let denom = s_i * s_j;

        let (cov, corr) = if denom > 1e-12 {
            let dot: f64 = centered[i]
                .iter()
                .zip(centered[j].iter())
                .map(|(&a, &b)| a * b)
                .sum();
            let cov_val = dot / nf;
            let corr_val = (cov_val / denom).clamp(-1.0, 1.0);
            (cov_val, corr_val)
        } else {
            (0.0, 0.0)
        };

        all_abs_corrs.push(corr.abs());

        let mut best_peak = corr.abs();
        let mut best_lag = 0.0f64;

        if denom > 1e-12 && max_lag > 0 {
            for lag in 1..=max_lag {
                let mut dot_pos = 0.0f64;
                for t in 0..(n - lag) {
                    dot_pos += centered[i][t] * centered[j][t + lag];
                }
                let r_pos = ((dot_pos / nf) / denom).abs();
                if r_pos > best_peak {
                    best_peak = r_pos;
                    best_lag = lag as f64;
                }

                let mut dot_neg = 0.0f64;
                for t in 0..(n - lag) {
                    dot_neg += centered[i][t + lag] * centered[j][t];
                }
                let r_neg = ((dot_neg / nf) / denom).abs();
                if r_neg > best_peak {
                    best_peak = r_neg;
                    best_lag = -(lag as f64);
                }
            }
        }

        out[out_idx] = best_peak;
        out[out_idx + 1] = best_lag;
        out[out_idx + 2] = cov;
        out[out_idx + 3] = corr;
        out_idx += 4;
    }

    let mean_abs = if !all_abs_corrs.is_empty() {
        all_abs_corrs.iter().sum::<f64>() / (all_abs_corrs.len() as f64)
    } else {
        0.0
    };
    let max_abs = all_abs_corrs.iter().copied().fold(0.0f64, f64::max);
    let coherence_mean = if !all_abs_corrs.is_empty() {
        all_abs_corrs.iter().map(|&r| r * r).sum::<f64>() / (all_abs_corrs.len() as f64)
    } else {
        0.0
    };
    let eigen_spread = (1.0 + max_abs) / (1.0 - max_abs + 1e-6);

    out[out_idx] = mean_abs;
    out[out_idx + 1] = max_abs;
    out[out_idx + 2] = eigen_spread;
    out[out_idx + 3] = coherence_mean;
}

/// extract_features_mc(x, profile="core33", features=None, cross=True, max_pairs=8, n_jobs=None, views=None)
#[pyfunction]
#[pyo3(signature = (x, profile = None, features = None, cross = true, max_pairs = 8, n_jobs = None, views = None))]
#[allow(clippy::too_many_arguments)]
pub fn extract_features_mc<'py>(
    py: Python<'py>,
    x: &Bound<'py, PyAny>,
    profile: Option<&str>,
    features: Option<Vec<String>>,
    cross: bool,
    max_pairs: usize,
    n_jobs: Option<usize>,
    views: Option<Vec<String>>,
) -> PyResult<Bound<'py, PyArray2<f64>>> {
    let feat_refs = features.as_deref();
    let plan = FeaturePlan::build_with_views(profile, feat_refs, views.as_deref())?;
    let n_plan_cols = plan.n_features();

    let arr = x.extract::<PyReadonlyArrayDyn<f64>>().map_err(|_| {
        pyo3::exceptions::PyTypeError::new_err(
            "extract_features_mc expects a 3D float64 array of shape (n_samples, n_channels, length)",
        )
    })?;

    let shape = arr.shape();
    if shape.len() != 3 {
        return Err(pyo3::exceptions::PyValueError::new_err(format!(
            "extract_features_mc expects a 3D array of shape (n_samples, n_channels, length), got shape {shape:?}"
        )));
    }
    let n_samples = shape[0];
    let n_channels = shape[1];
    let length = shape[2];

    if n_samples == 0 || n_channels == 0 || length == 0 {
        return Err(KymoraError::EmptyInput.into());
    }

    let slice = arr
        .as_slice()
        .map_err(|_| KymoraError::NotContiguous { index: None })?;

    let pair_count = if cross && n_channels >= 2 {
        let mut count = 0usize;
        for i in 0..n_channels {
            for _ in (i + 1)..n_channels {
                count += 1;
                if count >= max_pairs {
                    break;
                }
            }
            if count >= max_pairs {
                break;
            }
        }
        count
    } else {
        0
    };

    let n_cross_cols = if pair_count > 0 {
        pair_count * 4 + 4
    } else {
        0
    };
    let total_cols = n_channels * n_plan_cols + n_cross_cols;

    let out_arr = PyArray2::<f64>::zeros(py, [n_samples, total_cols], false);
    let out_slice = out_slice_mut(&out_arr)?;

    py.detach(|| {
        run_in_pool(n_jobs, || {
            let sample_stride = n_channels * length;
            let mut scratch = Scratch::new(length);

            for s in 0..n_samples {
                let sample_data = &slice[s * sample_stride..(s + 1) * sample_stride];
                let row_out = &mut out_slice[s * total_cols..(s + 1) * total_cols];

                // 1. Per-channel features
                let mut channel_slices = Vec::with_capacity(n_channels);
                for c in 0..n_channels {
                    let ch_data = &sample_data[c * length..(c + 1) * length];
                    channel_slices.push(ch_data);
                    let ch_out = &mut row_out[c * n_plan_cols..(c + 1) * n_plan_cols];
                    pipeline::run_plan(ch_data, &plan, &mut scratch, ch_out);
                }

                // 2. Cross-channel features
                if n_cross_cols > 0 {
                    let cross_out = &mut row_out[n_channels * n_plan_cols..total_cols];
                    compute_cross_features(&channel_slices, max_pairs, cross_out);
                }
            }
        })
    });

    Ok(out_arr)
}

/// feature_names_mc(n_channels, profile=None, features=None, cross=True, max_pairs=8, views=None) -> list[str]
#[pyfunction]
#[pyo3(signature = (n_channels, profile = None, features = None, cross = true, max_pairs = 8, views = None))]
pub fn feature_names_mc(
    n_channels: usize,
    profile: Option<&str>,
    features: Option<Vec<String>>,
    cross: bool,
    max_pairs: usize,
    views: Option<Vec<String>>,
) -> PyResult<Vec<String>> {
    let feat_refs = features.as_deref();
    let plan = FeaturePlan::build_with_views(profile, feat_refs, views.as_deref())?;

    let mut names = Vec::new();
    for c in 0..n_channels {
        for fn_name in &plan.names {
            names.push(format!("ch{c}__{fn_name}"));
        }
    }

    if cross && n_channels >= 2 {
        let mut count = 0usize;
        for i in 0..n_channels {
            for j in (i + 1)..n_channels {
                names.push(format!("cross_corr_peak__ch{i}_ch{j}"));
                names.push(format!("cross_corr_lag__ch{i}_ch{j}"));
                names.push(format!("cross_cov__ch{i}_ch{j}"));
                names.push(format!("cross_corr_coef__ch{i}_ch{j}"));
                count += 1;
                if count >= max_pairs {
                    break;
                }
            }
            if count >= max_pairs {
                break;
            }
        }
        names.push("cross__mean_abs_corr".to_string());
        names.push("cross__max_abs_corr".to_string());
        names.push("cross__eigen_spread".to_string());
        names.push("cross__coherence_mean".to_string());
    }

    Ok(names)
}

/// extract_features_ragged(values, offsets, profile="core33", features=None, n_jobs=None, out=None)
#[pyfunction]
#[pyo3(signature = (values, offsets, profile = None, features = None, n_jobs = None, out = None))]
pub fn extract_features_ragged<'py>(
    py: Python<'py>,
    values: &Bound<'py, PyAny>,
    offsets: PyReadonlyArray1<'py, i64>,
    profile: Option<&str>,
    features: Option<Vec<String>>,
    n_jobs: Option<usize>,
    out: Option<&Bound<'py, PyArray2<f64>>>,
) -> PyResult<Bound<'py, PyArray2<f64>>> {
    let offsets_slice = offsets
        .as_slice()
        .map_err(|_| KymoraError::NotContiguous { index: None })?;
    if offsets_slice.len() < 2 {
        return Err(KymoraError::EmptyInput.into());
    }
    let nrows = offsets_slice.len() - 1;

    let feat_refs = features.as_deref();
    let plan = FeaturePlan::build(profile, feat_refs)?;
    let n_cols = plan.n_features();

    if let Ok(v64) = values.extract::<PyReadonlyArray1<f64>>() {
        let v_slice = v64
            .as_slice()
            .map_err(|_| KymoraError::NotContiguous { index: None })?;
        let out_arr = get_out_array(py, nrows, n_cols, out)?;
        let out_slice = out_slice_mut(&out_arr)?;
        py.detach(|| {
            run_in_pool(n_jobs, || {
                crate::exec::extract_ragged_csr_plan(v_slice, offsets_slice, &plan, out_slice)
            })
        })?;
        return Ok(out_arr);
    }

    if let Ok(v32) = values.extract::<PyReadonlyArray1<f32>>() {
        let v_slice = v32
            .as_slice()
            .map_err(|_| KymoraError::NotContiguous { index: None })?;
        let out_arr = get_out_array(py, nrows, n_cols, out)?;
        let out_slice = out_slice_mut(&out_arr)?;
        py.detach(|| {
            run_in_pool(n_jobs, || {
                crate::exec::extract_ragged_csr_f32(v_slice, offsets_slice, out_slice, n_cols)
            })
        })?;
        return Ok(out_arr);
    }

    Err(PyTypeError::new_err(
        "extract_features_ragged expects 1D float64 or float32 values and 1D int64 offsets",
    ))
}

/// sliding_features(x, window, stride=1, profile="core33", features=None, n_jobs=None, out=None)
#[pyfunction]
#[pyo3(signature = (x, window, stride = 1, profile = None, features = None, n_jobs = None, out = None))]
#[allow(clippy::too_many_arguments)]
pub fn sliding_features<'py>(
    py: Python<'py>,
    x: PyReadonlyArray1<'py, f64>,
    window: i64,
    stride: i64,
    profile: Option<&str>,
    features: Option<Vec<String>>,
    n_jobs: Option<usize>,
    out: Option<&Bound<'py, PyArray2<f64>>>,
) -> PyResult<Bound<'py, PyArray2<f64>>> {
    let slice = x
        .as_slice()
        .map_err(|_| KymoraError::NotContiguous { index: None })?;
    let (window, stride, n_windows) = extract::window_geometry(slice.len(), window, stride)?;

    let feat_refs = features.as_deref();
    let plan = FeaturePlan::build(profile, feat_refs)?;
    let n_cols = plan.n_features();

    let out_arr = get_out_array(py, n_windows, n_cols, out)?;
    let out_slice = out_slice_mut(&out_arr)?;
    py.detach(|| {
        run_in_pool(n_jobs, || {
            crate::exec::extract_windows_plan_into_slice(slice, window, stride, &plan, out_slice)
        })
    });
    Ok(out_arr)
}

/// feature_names(profile=None, features=None, views=None) -> list[str], in output column order.
#[pyfunction]
#[pyo3(signature = (profile = None, features = None, views = None))]
pub fn feature_names(
    profile: Option<&str>,
    features: Option<Vec<String>>,
    views: Option<Vec<String>>,
) -> PyResult<Vec<String>> {
    if profile.is_none() && features.is_none() && views.is_none() {
        return Ok(features::NAMES.iter().map(|s| s.to_string()).collect());
    }
    let feat_refs = features.as_deref();
    let plan = FeaturePlan::build_with_views(profile, feat_refs, views.as_deref())?;
    Ok(plan.names)
}

/// list_profiles() -> dict[str, int] of profile names to feature counts.
#[pyfunction]
pub fn list_profiles() -> HashMap<&'static str, usize> {
    let mut map = HashMap::new();
    let min_count = registry::FEATURES
        .iter()
        .filter(|f| f.profiles.contains(registry::ProfileMask::MINIMAL))
        .count();
    let ext_count = registry::FEATURES
        .iter()
        .filter(|f| f.profiles.contains(registry::ProfileMask::EXTENDED))
        .count();
    let full_count = registry::FEATURES
        .iter()
        .filter(|f| f.profiles.contains(registry::ProfileMask::FULL))
        .count();
    map.insert("minimal", min_count);
    map.insert("core33", 33);
    map.insert("extended", ext_count);
    map.insert("full", full_count);
    map
}

/// describe_feature(name) -> dict with description, cost, aliases, and needs.
#[pyfunction]
pub fn describe_feature(name: &str) -> PyResult<HashMap<&'static str, String>> {
    let idx = registry::find_feature(name).ok_or_else(|| KymoraError::UnknownFeature {
        name: name.to_string(),
    })?;
    let def = &registry::FEATURES[idx];
    let mut map = HashMap::new();
    map.insert("name", def.name.to_string());
    map.insert("cost", format!("{:?}", def.cost));
    map.insert("aliases", def.aliases.join(", "));
    map.insert("needs", format!("{:?}", def.needs));
    Ok(map)
}

/// Streaming feature extractor for real-time sliding windows.
#[pyclass(name = "StreamingExtractor")]
pub struct PyStreamingExtractor {
    inner: features::StreamingExtractor,
}

#[pymethods]
impl PyStreamingExtractor {
    #[new]
    pub fn new(window_size: usize) -> PyResult<Self> {
        if window_size < 2 {
            return Err(pyo3::exceptions::PyValueError::new_err(
                "window_size must be at least 2",
            ));
        }
        Ok(Self {
            inner: features::StreamingExtractor::new(window_size),
        })
    }

    #[getter]
    pub fn window_size(&self) -> usize {
        self.inner.window_size()
    }

    #[getter]
    pub fn is_full(&self) -> bool {
        self.inner.is_full()
    }

    pub fn push(&mut self, val: f64) -> bool {
        self.inner.push(val)
    }

    pub fn reset(&mut self) {
        self.inner.reset()
    }

    #[pyo3(signature = (kind = "all"))]
    pub fn compute<'py>(
        &self,
        py: Python<'py>,
        kind: Option<&str>,
    ) -> PyResult<Bound<'py, PyArray1<f64>>> {
        let mode = kind.unwrap_or("all");
        match mode {
            "fast" => {
                let mut feats = vec![0.0f64; features::streaming::FAST_NAMES.len()];
                self.inner.compute_fast(&mut feats);
                Ok(feats.into_pyarray(py))
            }
            "all" => {
                let mut feats = vec![0.0f64; features::NAMES.len()];
                self.inner.compute_features(&mut feats);
                Ok(feats.into_pyarray(py))
            }
            _ => Err(pyo3::exceptions::PyValueError::new_err(format!(
                "unknown compute kind '{mode}'; valid kinds: 'fast', 'all'"
            ))),
        }
    }

    pub fn compute_features<'py>(&self, py: Python<'py>) -> PyResult<Bound<'py, PyArray1<f64>>> {
        self.compute(py, Some("all"))
    }

    #[staticmethod]
    pub fn fast_feature_names() -> Vec<&'static str> {
        features::streaming::FAST_NAMES.to_vec()
    }
}

/// MultiStreamExtractor for fleet real-time streaming across thousands of streams.
#[pyclass(name = "MultiStreamExtractor")]
pub struct PyMultiStreamExtractor {
    inner: features::MultiStreamExtractor,
}

#[pymethods]
impl PyMultiStreamExtractor {
    #[new]
    pub fn new(n_streams: usize, window_size: usize) -> PyResult<Self> {
        if n_streams < 1 {
            return Err(pyo3::exceptions::PyValueError::new_err(
                "n_streams must be at least 1",
            ));
        }
        if window_size < 2 {
            return Err(pyo3::exceptions::PyValueError::new_err(
                "window_size must be at least 2",
            ));
        }
        Ok(Self {
            inner: features::MultiStreamExtractor::new(n_streams, window_size),
        })
    }

    #[getter]
    pub fn n_streams(&self) -> usize {
        self.inner.n_streams()
    }

    #[getter]
    pub fn window_size(&self) -> usize {
        self.inner.window_size()
    }

    #[getter]
    pub fn is_full(&self) -> bool {
        self.inner.is_full()
    }

    #[getter]
    pub fn count(&self) -> usize {
        self.inner.count()
    }

    pub fn push_many(&mut self, values: PyReadonlyArray1<f64>) -> PyResult<bool> {
        let slice = values
            .as_slice()
            .map_err(|_| KymoraError::NotContiguous { index: None })?;
        if slice.len() != self.inner.n_streams() {
            return Err(pyo3::exceptions::PyValueError::new_err(format!(
                "expected {} values, got {}",
                self.inner.n_streams(),
                slice.len()
            )));
        }
        Ok(self.inner.push_many(slice))
    }

    #[pyo3(signature = (stream_idx = None))]
    pub fn reset(&mut self, stream_idx: Option<usize>) -> PyResult<()> {
        if let Some(s) = stream_idx {
            if s >= self.inner.n_streams() {
                return Err(pyo3::exceptions::PyValueError::new_err(
                    "stream_idx out of bounds",
                ));
            }
        }
        self.inner.reset(stream_idx);
        Ok(())
    }

    #[pyo3(signature = (streams = None, kind = "all"))]
    pub fn compute<'py>(
        &self,
        py: Python<'py>,
        streams: Option<Vec<usize>>,
        kind: Option<&str>,
    ) -> PyResult<Bound<'py, PyArray2<f64>>> {
        let stream_list = match streams {
            Some(s) => s,
            None => (0..self.inner.n_streams()).collect(),
        };
        let mode = kind.unwrap_or("all");
        match mode {
            "fast" => {
                let n_cols = features::multistream::MULTISTREAM_FAST_NAMES.len();
                let out_arr = PyArray2::<f64>::zeros(py, [stream_list.len(), n_cols], false);
                let out_slice = out_slice_mut(&out_arr)?;
                self.inner.compute_fast(&stream_list, out_slice);
                Ok(out_arr)
            }
            "all" => {
                let n_cols = pipeline::CORE33_COUNT;
                let out_arr = PyArray2::<f64>::zeros(py, [stream_list.len(), n_cols], false);
                let out_slice = out_slice_mut(&out_arr)?;
                let mut scratch = Scratch::new(self.inner.window_size());
                self.inner
                    .compute_all(&stream_list, &mut scratch, out_slice);
                Ok(out_arr)
            }
            _ => Err(pyo3::exceptions::PyValueError::new_err(
                "invalid compute kind; choose 'fast' or 'all'",
            )),
        }
    }

    #[staticmethod]
    pub fn fast_feature_names() -> Vec<&'static str> {
        features::multistream::MULTISTREAM_FAST_NAMES.to_vec()
    }
}
