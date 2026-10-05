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
use crate::nan_policy::{self, NanPolicy};
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
        // A Fortran-ordered out= buffer would silently receive row-major
        // writes into column-major memory (transposed garbage on read-back),
        // so require C order exactly like the inputs.
        if !user_out.readonly().as_array().is_standard_layout() {
            return Err(KymoraError::NotContiguous { index: None }.into());
        }
        Ok(user_out.clone())
    } else {
        Ok(PyArray2::<f64>::zeros(py, [nrows, ncols], false))
    }
}

/// Strict C-contiguity rule (one place, documented once).
///
/// numpy's `PyReadonlyArray::as_slice` accepts Fortran-ordered buffers and
/// hands back *memory* order, which would silently transpose every row. Every
/// input borrow below is therefore gated on ndarray's standard-layout
/// (C-order) check first, so non-C input always surfaces as `NotContiguous`
/// and never as wrong numbers. 1D behavior is unchanged (strided 1D was
/// already rejected); the 2D/3D Fortran cases previously returned wrong
/// values silently. `out=` buffers are gated the same way in
/// [`get_out_array`].
///
/// Lifetime note: the gate is a plain `bool` check on a temporary view. The
/// borrow itself always comes straight from the source array
/// (`a.as_slice()`, `view.as_slice()` on a function-body view) with no
/// intermediate binding, which is the only shape the borrow checker extends
/// across loop iterations.
fn require_c_layout<T, D>(
    arr: &numpy::PyReadonlyArray<T, D>,
    index: Option<usize>,
) -> Result<(), KymoraError>
where
    T: numpy::Element,
    D: numpy::ndarray::Dimension,
{
    if arr.as_array().is_standard_layout() {
        Ok(())
    } else {
        Err(KymoraError::NotContiguous { index })
    }
}

/// Parse the `contiguous` option (arch D2): `"error"` (default) rejects
/// non-C input; `"copy"` performs one explicit C-order copy first.
fn parse_contiguous(contiguous: Option<&str>) -> PyResult<bool> {
    match contiguous {
        None | Some("error") => Ok(false),
        Some("copy") => Ok(true),
        Some(other) => Err(pyo3::exceptions::PyValueError::new_err(format!(
            "unknown contiguous '{other}'; valid values: 'error' (default), 'copy'"
        ))),
    }
}

/// Best-effort one-time-per-callsite `UserWarning` when `contiguous="copy"`
/// materializes a copy. A failure to warn must never fail the call itself.
fn warn_copy(py: Python, what: &str) {
    let msg = format!(
        "kymora copied {what} to C-contiguous layout (contiguous='copy'); \
         pass np.ascontiguousarray input to avoid the copy"
    );
    if let Ok(warnings) = py.import("warnings") {
        if let Ok(warn_fn) = warnings.getattr("warn") {
            let _ = warn_fn.call1((msg,));
        }
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
            // Cached per-thread-count pools: building a rayon ThreadPool per
            // call cost ~200 us (measured 2026-10-06, 32x500 batch), which
            // dominated small calls outright (arch F2). The global pool
            // (None) was already free of this; now explicit counts are too.
            // Build failure falls back to inline execution, never an error.
            static POOL_CACHE: std::sync::OnceLock<
                std::sync::Mutex<
                    std::collections::HashMap<usize, std::sync::Arc<rayon::ThreadPool>>,
                >,
            > = std::sync::OnceLock::new();
            let pool = POOL_CACHE
                .get_or_init(|| std::sync::Mutex::new(std::collections::HashMap::new()))
                .lock()
                .ok()
                .and_then(|mut cache| {
                    if let Some(p) = cache.get(&n) {
                        return Some(std::sync::Arc::clone(p));
                    }
                    rayon::ThreadPoolBuilder::new()
                        .num_threads(n)
                        .build()
                        .ok()
                        .map(|p| {
                            let p = std::sync::Arc::new(p);
                            cache.insert(n, std::sync::Arc::clone(&p));
                            p
                        })
                });
            match pool {
                Some(p) => p.install(f),
                None => f(),
            }
        }
        _ => f(),
    }
}

/// Enforce `nan_policy="raise"` on validated row views.
///
/// Returns `Ok(())` under propagate, or a `ValueError` naming the first
/// NaN-containing series. Deliberately NOT a `KymoraError`: NaN describes
/// values, not structure (see the `nan_policy` module docs).
fn enforce_nan_policy_f64(rows: &[&[f64]], policy: NanPolicy) -> PyResult<()> {
    if policy == NanPolicy::Raise {
        if let Some(i) = nan_policy::first_nan_series_f64(rows) {
            return Err(pyo3::exceptions::PyValueError::new_err(format!(
                "series at batch index {i} contains NaN (nan_policy='raise')"
            )));
        }
    }
    Ok(())
}

/// f32-input variant of [`enforce_nan_policy_f64`].
fn enforce_nan_policy_f32(rows: &[&[f32]], policy: NanPolicy) -> PyResult<()> {
    if policy == NanPolicy::Raise {
        if let Some(i) = nan_policy::first_nan_series_f32(rows) {
            return Err(pyo3::exceptions::PyValueError::new_err(format!(
                "series at batch index {i} contains NaN (nan_policy='raise')"
            )));
        }
    }
    Ok(())
}

/// Restriction for float32 input: the f32 kernels implement the core33 set
/// only (indices 0..33, which match the core33 column order).
///
/// Returns `None` for a direct core33 run, or `Some(indices)` to gather a
/// core33 subset (`minimal`, explicit feature lists) from a full core33 row.
/// Anything else — `extended`/`full` profiles, non-core33 features, non-raw
/// views — is a clear `ValueError` telling the caller to pass float64 input:
/// silently computing the wrong width would be worse than refusing, and this
/// path previously panicked across the FFI boundary.
fn f32_plan_gather(plan: &FeaturePlan) -> PyResult<Option<Vec<usize>>> {
    if plan.views.len() != 1 || plan.views[0] != "raw" {
        return Err(pyo3::exceptions::PyValueError::new_err(
            "views are not supported for float32 input; pass a float64 array for views",
        ));
    }
    if plan.indices.len() == 33 && plan.indices.iter().enumerate().all(|(j, &i)| i == j) {
        return Ok(None);
    }
    if plan.indices.iter().all(|&i| i < 33) {
        return Ok(Some(plan.indices.clone()));
    }
    Err(pyo3::exceptions::PyValueError::new_err(
        "this profile/feature set is not implemented for float32 input \
         (f32 kernels cover core33 only); pass a float64 array instead",
    ))
}

/// Validate the advisory `precision` option. Accumulation is always float64;
/// the input dtype governs the read path, so this only rejects typos.
fn parse_precision(precision: Option<&str>) -> PyResult<()> {
    match precision {
        None | Some("float64") | Some("f64") | Some("float32") | Some("f32") => Ok(()),
        Some(other) => Err(pyo3::exceptions::PyValueError::new_err(format!(
            "unknown precision '{other}'; valid values: 'float64' (default), 'float32'"
        ))),
    }
}

/// extract_features(X, profile="core33", features=None, n_jobs=None, out=None, views=None, precision=None, out_dtype=None, nan_policy=None, contiguous=None)
#[pyfunction]
#[pyo3(signature = (x, profile = None, features = None, n_jobs = None, out = None, views = None, precision = None, out_dtype = None, nan_policy = None, contiguous = None))]
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
    nan_policy: Option<&str>,
    contiguous: Option<&str>,
) -> PyResult<Bound<'py, PyAny>> {
    let feat_refs = features.as_deref();
    let plan = FeaturePlan::build_with_views(profile, feat_refs, views.as_deref())?;
    let n_cols = plan.n_features();
    let nan_policy =
        nan_policy::parse(nan_policy).map_err(pyo3::exceptions::PyValueError::new_err)?;
    parse_precision(precision)?;
    let copy_on_demand = parse_contiguous(contiguous)?;

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
        let owned: Vec<f64>;
        let slice: &[f64] = if view.is_standard_layout() {
            view.as_slice()
                .ok_or(KymoraError::NotContiguous { index: None })?
        } else if copy_on_demand {
            warn_copy(py, "input array");
            owned = view.iter().copied().collect();
            &owned
        } else {
            return Err(KymoraError::NotContiguous { index: None }.into());
        };
        let rows: Vec<&[f64]> = slice.chunks_exact(ncols).collect();
        enforce_nan_policy_f64(&rows, nan_policy)?;

        if wants_f32_out {
            let out_arr = PyArray2::<f32>::zeros(py, [nrows, n_cols], false);
            let out_slice = out_slice_mut_f32(&out_arr)?;
            py.detach(|| {
                run_in_pool(n_jobs, || {
                    let mut tmp = vec![0.0f64; nrows * n_cols];
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
        let owned: Vec<f32>;
        let slice: &[f32] = if view.is_standard_layout() {
            view.as_slice()
                .ok_or(KymoraError::NotContiguous { index: None })?
        } else if copy_on_demand {
            warn_copy(py, "input array");
            owned = view.iter().copied().collect();
            &owned
        } else {
            return Err(KymoraError::NotContiguous { index: None }.into());
        };
        let rows: Vec<&[f32]> = slice.chunks_exact(ncols).collect();
        enforce_nan_policy_f32(&rows, nan_policy)?;
        let gather = f32_plan_gather(&plan)?;

        if wants_f32_out {
            let out_arr = PyArray2::<f32>::zeros(py, [nrows, n_cols], false);
            let out_slice = out_slice_mut_f32(&out_arr)?;
            py.detach(|| {
                run_in_pool(n_jobs, || {
                    let mut tmp = vec![0.0f64; nrows * n_cols];
                    crate::exec::extract_into_slice_f32(&rows, &mut tmp, n_cols, gather.as_deref());
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
                crate::exec::extract_into_slice_f32(&rows, out_slice, n_cols, gather.as_deref());
            })
        });
        return Ok(out_arr.into_any());
    }

    // 3. List of 1D float64 arrays
    if let Ok(list) = x.extract::<Vec<PyReadonlyArray1<f64>>>() {
        // Two phases: copy non-contiguous elements up front (borrows below
        // must stay stable while `owned` grows), then borrow everything.
        let mut owned: Vec<Vec<f64>> = Vec::new();
        let mut owned_pos: Vec<Option<usize>> = vec![None; list.len()];
        for (index, a) in list.iter().enumerate() {
            if !a.as_array().is_standard_layout() {
                if !copy_on_demand {
                    return Err(KymoraError::NotContiguous { index: Some(index) }.into());
                }
                warn_copy(py, &format!("list element {index}"));
                owned_pos[index] = Some(owned.len());
                owned.push(a.as_array().iter().copied().collect());
            }
        }
        let mut slices: Vec<&[f64]> = Vec::with_capacity(list.len());
        for (index, a) in list.iter().enumerate() {
            match owned_pos[index] {
                Some(k) => slices.push(&owned[k][..]),
                None => {
                    require_c_layout(a, Some(index))?;
                    slices.push(
                        a.as_slice()
                            .map_err(|_| KymoraError::NotContiguous { index: Some(index) })?,
                    );
                }
            }
        }
        extract::validate_batch(&slices)?;
        enforce_nan_policy_f64(&slices, nan_policy)?;
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
        let mut owned: Vec<Vec<f32>> = Vec::new();
        let mut owned_pos: Vec<Option<usize>> = vec![None; list.len()];
        for (index, a) in list.iter().enumerate() {
            if !a.as_array().is_standard_layout() {
                if !copy_on_demand {
                    return Err(KymoraError::NotContiguous { index: Some(index) }.into());
                }
                warn_copy(py, &format!("list element {index}"));
                owned_pos[index] = Some(owned.len());
                owned.push(a.as_array().iter().copied().collect());
            }
        }
        let mut slices = Vec::with_capacity(list.len());
        for (index, a) in list.iter().enumerate() {
            let s: &[f32] = match owned_pos[index] {
                Some(k) => &owned[k][..],
                None => {
                    require_c_layout(a, Some(index))?;
                    a.as_slice()
                        .map_err(|_| KymoraError::NotContiguous { index: Some(index) })?
                }
            };
            if s.is_empty() {
                return Err(KymoraError::EmptySeries { index }.into());
            }
            slices.push(s);
        }
        enforce_nan_policy_f32(&slices, nan_policy)?;
        let gather = f32_plan_gather(&plan)?;
        let nrows = slices.len();
        let out_arr = get_out_array(py, nrows, n_cols, out)?;
        let out_slice = out_slice_mut(&out_arr)?;
        py.detach(|| {
            run_in_pool(n_jobs, || {
                crate::exec::extract_into_slice_f32(&slices, out_slice, n_cols, gather.as_deref())
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

/// Number of channel pairs used for cross features (capped by `max_pairs`).
fn mc_pair_count(n_channels: usize, cross: bool, max_pairs: usize) -> usize {
    if !cross || n_channels < 2 {
        return 0;
    }
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
}

/// Per-sample multichannel extraction shared by the 3D and list-of-2D paths:
/// per-channel plan features in `ch{c}` blocks, then cross-channel features.
#[allow(clippy::too_many_arguments)]
fn mc_extract_sample(
    channel_slices: &[&[f64]],
    plan: &FeaturePlan,
    scratch: &mut Scratch,
    max_pairs: usize,
    n_plan_cols: usize,
    n_cross_cols: usize,
    total_cols: usize,
    row_out: &mut [f64],
) {
    let n_channels = channel_slices.len();
    for (c, ch_data) in channel_slices.iter().enumerate() {
        let ch_out = &mut row_out[c * n_plan_cols..(c + 1) * n_plan_cols];
        pipeline::run_plan(ch_data, plan, scratch, ch_out);
    }
    if n_cross_cols > 0 {
        let cross_out = &mut row_out[n_channels * n_plan_cols..total_cols];
        compute_cross_features(channel_slices, max_pairs, cross_out);
    }
}

/// extract_features_mc(x, profile="core33", features=None, cross=True, max_pairs=8, n_jobs=None, views=None, nan_policy=None, contiguous=None)
///
/// `x` is a 3D float64 array `(n_samples, n_channels, length)`, or a list of
/// 2D float64 arrays `(n_channels, length_i)` for ragged lengths across
/// samples (channel count must agree; each sample is processed independently).
/// Output is `(n_samples, n_channels * n_plan + n_cross)` with per-channel
/// `ch{c}__{feature}` blocks followed by cross columns (see `feature_names_mc`).
#[pyfunction]
#[pyo3(signature = (x, profile = None, features = None, cross = true, max_pairs = 8, n_jobs = None, views = None, nan_policy = None, contiguous = None))]
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
    nan_policy: Option<&str>,
    contiguous: Option<&str>,
) -> PyResult<Bound<'py, PyArray2<f64>>> {
    let feat_refs = features.as_deref();
    let plan = FeaturePlan::build_with_views(profile, feat_refs, views.as_deref())?;
    let n_plan_cols = plan.n_features();
    let nan_policy =
        nan_policy::parse(nan_policy).map_err(pyo3::exceptions::PyValueError::new_err)?;
    let copy_on_demand = parse_contiguous(contiguous)?;

    // 1. 3D float64 array path.
    if let Ok(arr) = x.extract::<PyReadonlyArrayDyn<f64>>() {
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

        let mc_view = arr.as_array();
        let mc_owned: Vec<f64>;
        let slice: &[f64] = if mc_view.is_standard_layout() {
            mc_view
                .as_slice()
                .ok_or(KymoraError::NotContiguous { index: None })?
        } else if copy_on_demand {
            warn_copy(py, "input array");
            mc_owned = mc_view.iter().copied().collect();
            &mc_owned
        } else {
            return Err(KymoraError::NotContiguous { index: None }.into());
        };
        if nan_policy == NanPolicy::Raise {
            if let Some(pos) = nan_policy::first_nan_sample_f64(slice) {
                let per_sample = n_channels * length;
                let sample = pos / per_sample;
                let channel = (pos % per_sample) / length;
                return Err(pyo3::exceptions::PyValueError::new_err(format!(
                    "sample {sample} channel {channel} contains NaN (nan_policy='raise')"
                )));
            }
        }

        let pair_count = mc_pair_count(n_channels, cross, max_pairs);
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

                    let mut channel_slices = Vec::with_capacity(n_channels);
                    for c in 0..n_channels {
                        channel_slices.push(&sample_data[c * length..(c + 1) * length]);
                    }
                    mc_extract_sample(
                        &channel_slices,
                        &plan,
                        &mut scratch,
                        max_pairs,
                        n_plan_cols,
                        n_cross_cols,
                        total_cols,
                        row_out,
                    );
                }
            })
        });

        return Ok(out_arr);
    }

    // 2. List of 2D float64 arrays: ragged lengths across samples.
    if let Ok(list) = x.extract::<Vec<PyReadonlyArray2<f64>>>() {
        if list.is_empty() {
            return Err(KymoraError::EmptyInput.into());
        }
        // Two phases (see the batch list paths): copy non-contiguous elements
        // up front so the borrows below stay stable.
        let mut owned: Vec<Vec<f64>> = Vec::new();
        let mut owned_pos: Vec<Option<usize>> = vec![None; list.len()];
        let mut lengths: Vec<usize> = vec![0; list.len()];
        let mut n_channels = None;
        for (index, a) in list.iter().enumerate() {
            let view = a.as_array();
            let shape = view.shape();
            if shape.len() != 2 {
                return Err(pyo3::exceptions::PyValueError::new_err(format!(
                    "multichannel list element {index} must be 2D (n_channels, length)"
                )));
            }
            let (c, len) = (shape[0], shape[1]);
            if c == 0 || len == 0 {
                return Err(KymoraError::EmptyInput.into());
            }
            match n_channels {
                None => n_channels = Some(c),
                Some(first) if first != c => {
                    return Err(pyo3::exceptions::PyValueError::new_err(format!(
                        "multichannel list element {index} has {c} channels, expected {first}"
                    )));
                }
                _ => {}
            }
            lengths[index] = len;
            let el_view = a.as_array();
            if !el_view.is_standard_layout() {
                if !copy_on_demand {
                    return Err(KymoraError::NotContiguous { index: Some(index) }.into());
                }
                warn_copy(py, &format!("list element {index}"));
                owned_pos[index] = Some(owned.len());
                owned.push(el_view.iter().copied().collect());
            }
        }
        let mut samples: Vec<(usize, &[f64])> = Vec::with_capacity(list.len());
        for (index, a) in list.iter().enumerate() {
            let s: &[f64] = match owned_pos[index] {
                Some(k) => &owned[k][..],
                None => {
                    require_c_layout(a, Some(index))?;
                    a.as_slice()
                        .map_err(|_| KymoraError::NotContiguous { index: Some(index) })?
                }
            };
            samples.push((lengths[index], s));
        }
        let n_channels = n_channels.unwrap_or(0);
        let n_samples = samples.len();
        if nan_policy == NanPolicy::Raise {
            for (s, (_, data)) in samples.iter().enumerate() {
                if let Some(pos) = nan_policy::first_nan_sample_f64(data) {
                    let len = data.len() / n_channels;
                    return Err(pyo3::exceptions::PyValueError::new_err(format!(
                        "sample {s} channel {} contains NaN (nan_policy='raise')",
                        pos / len
                    )));
                }
            }
        }

        let pair_count = mc_pair_count(n_channels, cross, max_pairs);
        let n_cross_cols = if pair_count > 0 {
            pair_count * 4 + 4
        } else {
            0
        };
        let total_cols = n_channels * n_plan_cols + n_cross_cols;
        let max_len = samples
            .iter()
            .map(|(_, data)| data.len() / n_channels)
            .max()
            .unwrap_or(0);

        let out_arr = PyArray2::<f64>::zeros(py, [n_samples, total_cols], false);
        let out_slice = out_slice_mut(&out_arr)?;

        py.detach(|| {
            run_in_pool(n_jobs, || {
                let mut scratch = Scratch::new(max_len);
                for (s, (len, data)) in samples.iter().enumerate() {
                    let row_out = &mut out_slice[s * total_cols..(s + 1) * total_cols];
                    let mut channel_slices = Vec::with_capacity(n_channels);
                    for c in 0..n_channels {
                        channel_slices.push(&data[c * len..(c + 1) * len]);
                    }
                    mc_extract_sample(
                        &channel_slices,
                        &plan,
                        &mut scratch,
                        max_pairs,
                        n_plan_cols,
                        n_cross_cols,
                        total_cols,
                        row_out,
                    );
                }
            })
        });

        return Ok(out_arr);
    }

    Err(pyo3::exceptions::PyTypeError::new_err(
        "extract_features_mc expects a 3D float64 array of shape (n_samples, n_channels, length), \
         or a list of 2D float64 arrays (n_channels, length_i) for ragged lengths",
    ))
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

/// extract_features_ragged(values, offsets, profile="core33", features=None, n_jobs=None, out=None, nan_policy=None, contiguous=None)
#[pyfunction]
#[pyo3(signature = (values, offsets, profile = None, features = None, n_jobs = None, out = None, nan_policy = None, contiguous = None))]
#[allow(clippy::too_many_arguments)]
pub fn extract_features_ragged<'py>(
    py: Python<'py>,
    values: &Bound<'py, PyAny>,
    offsets: PyReadonlyArray1<'py, i64>,
    profile: Option<&str>,
    features: Option<Vec<String>>,
    n_jobs: Option<usize>,
    out: Option<&Bound<'py, PyArray2<f64>>>,
    nan_policy: Option<&str>,
    contiguous: Option<&str>,
) -> PyResult<Bound<'py, PyArray2<f64>>> {
    let copy_on_demand = parse_contiguous(contiguous)?;
    let offsets_view = offsets.as_array();
    let offsets_owned: Vec<i64>;
    let offsets_slice: &[i64] = if offsets_view.is_standard_layout() {
        offsets_view
            .as_slice()
            .ok_or(KymoraError::NotContiguous { index: None })?
    } else if copy_on_demand {
        warn_copy(py, "offsets array");
        offsets_owned = offsets_view.iter().copied().collect();
        &offsets_owned
    } else {
        return Err(KymoraError::NotContiguous { index: None }.into());
    };
    if offsets_slice.len() < 2 {
        return Err(KymoraError::EmptyInput.into());
    }
    let nrows = offsets_slice.len() - 1;

    let feat_refs = features.as_deref();
    let plan = FeaturePlan::build(profile, feat_refs)?;
    let n_cols = plan.n_features();
    let nan_policy =
        nan_policy::parse(nan_policy).map_err(pyo3::exceptions::PyValueError::new_err)?;

    if let Ok(v64) = values.extract::<PyReadonlyArray1<f64>>() {
        let v_view = v64.as_array();
        let v_owned: Vec<f64>;
        let v_slice: &[f64] = if v_view.is_standard_layout() {
            v_view
                .as_slice()
                .ok_or(KymoraError::NotContiguous { index: None })?
        } else if copy_on_demand {
            warn_copy(py, "values array");
            v_owned = v_view.iter().copied().collect();
            &v_owned
        } else {
            return Err(KymoraError::NotContiguous { index: None }.into());
        };
        if nan_policy == NanPolicy::Raise {
            if let Some(pos) = nan_policy::first_nan_sample_f64(v_slice) {
                let series = nan_policy::series_for_offset(offsets_slice, pos);
                return Err(pyo3::exceptions::PyValueError::new_err(format!(
                    "series at batch index {series} contains NaN (nan_policy='raise')"
                )));
            }
        }
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
        let v_view = v32.as_array();
        let v_owned: Vec<f32>;
        let v_slice: &[f32] = if v_view.is_standard_layout() {
            v_view
                .as_slice()
                .ok_or(KymoraError::NotContiguous { index: None })?
        } else if copy_on_demand {
            warn_copy(py, "values array");
            v_owned = v_view.iter().copied().collect();
            &v_owned
        } else {
            return Err(KymoraError::NotContiguous { index: None }.into());
        };
        if nan_policy == NanPolicy::Raise {
            if let Some(pos) = v_slice.iter().position(|v| v.is_nan()) {
                let series = nan_policy::series_for_offset(offsets_slice, pos);
                return Err(pyo3::exceptions::PyValueError::new_err(format!(
                    "series at batch index {series} contains NaN (nan_policy='raise')"
                )));
            }
        }
        let gather = f32_plan_gather(&plan)?;
        let out_arr = get_out_array(py, nrows, n_cols, out)?;
        let out_slice = out_slice_mut(&out_arr)?;
        py.detach(|| {
            run_in_pool(n_jobs, || {
                crate::exec::extract_ragged_csr_f32(
                    v_slice,
                    offsets_slice,
                    out_slice,
                    n_cols,
                    gather.as_deref(),
                )
            })
        })?;
        return Ok(out_arr);
    }

    Err(PyTypeError::new_err(
        "extract_features_ragged expects 1D float64 or float32 values and 1D int64 offsets",
    ))
}

/// sliding_features(x, window, stride=1, profile="core33", features=None, n_jobs=None, out=None, nan_policy=None, contiguous=None)
#[pyfunction]
#[pyo3(signature = (x, window, stride = 1, profile = None, features = None, n_jobs = None, out = None, nan_policy = None, contiguous = None))]
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
    nan_policy: Option<&str>,
    contiguous: Option<&str>,
) -> PyResult<Bound<'py, PyArray2<f64>>> {
    let copy_on_demand = parse_contiguous(contiguous)?;
    let x_view = x.as_array();
    let x_owned: Vec<f64>;
    let slice: &[f64] = if x_view.is_standard_layout() {
        x_view
            .as_slice()
            .ok_or(KymoraError::NotContiguous { index: None })?
    } else if copy_on_demand {
        warn_copy(py, "input series");
        x_owned = x_view.iter().copied().collect();
        &x_owned
    } else {
        return Err(KymoraError::NotContiguous { index: None }.into());
    };
    let (window, stride, n_windows) = extract::window_geometry(slice.len(), window, stride)?;
    let nan_policy =
        nan_policy::parse(nan_policy).map_err(pyo3::exceptions::PyValueError::new_err)?;
    if nan_policy == NanPolicy::Raise {
        if let Some(pos) = nan_policy::first_nan_sample_f64(slice) {
            return Err(pyo3::exceptions::PyValueError::new_err(format!(
                "series contains NaN at sample index {pos} (nan_policy='raise')"
            )));
        }
    }

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

/// describe_feature(name) -> dict with description, cost, aliases, needs, and
/// core33 documentation metadata (definition, min_length, nan_when).
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
    if let Some(meta) = registry::core_meta(def.name) {
        map.insert("definition", meta.definition.to_string());
        map.insert("min_length", meta.min_len.to_string());
        map.insert("nan_when", meta.nan_when.to_string());
    }
    Ok(map)
}

/// Streaming feature extractor for real-time sliding windows.
#[pyclass(name = "StreamingExtractor")]
pub struct PyStreamingExtractor {
    inner: features::StreamingExtractor,
    nan_policy_raise: bool,
}

#[pymethods]
impl PyStreamingExtractor {
    #[new]
    #[pyo3(signature = (window_size, anchor_interval = None, nan_policy = None))]
    pub fn new(
        window_size: usize,
        anchor_interval: Option<usize>,
        nan_policy: Option<&str>,
    ) -> PyResult<Self> {
        if window_size < 1 {
            return Err(pyo3::exceptions::PyValueError::new_err(
                "window_size must be at least 1",
            ));
        }
        let interval = anchor_interval.unwrap_or(features::streaming::DEFAULT_ANCHOR_INTERVAL);
        if interval < 1 {
            return Err(pyo3::exceptions::PyValueError::new_err(
                "anchor_interval must be at least 1",
            ));
        }
        let policy =
            nan_policy::parse(nan_policy).map_err(pyo3::exceptions::PyValueError::new_err)?;
        Ok(Self {
            inner: features::StreamingExtractor::new(window_size).with_anchor_interval(interval),
            nan_policy_raise: policy == NanPolicy::Raise,
        })
    }

    #[getter]
    pub fn window_size(&self) -> usize {
        self.inner.window_size()
    }

    #[getter]
    pub fn anchor_interval(&self) -> usize {
        self.inner.anchor_interval()
    }

    pub fn set_anchor_interval(&mut self, anchor_interval: usize) -> PyResult<()> {
        if anchor_interval < 1 {
            return Err(pyo3::exceptions::PyValueError::new_err(
                "anchor_interval must be at least 1",
            ));
        }
        self.inner.set_anchor_interval(anchor_interval);
        Ok(())
    }

    #[getter]
    pub fn is_full(&self) -> bool {
        self.inner.is_full()
    }

    pub fn push(&mut self, val: f64) -> PyResult<bool> {
        if self.nan_policy_raise && val.is_nan() {
            return Err(pyo3::exceptions::PyValueError::new_err(
                "pushed value is NaN (nan_policy='raise')",
            ));
        }
        Ok(self.inner.push(val))
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

    #[pyo3(signature = (values, contiguous = None))]
    pub fn push_many(
        &mut self,
        py: Python,
        values: PyReadonlyArray1<f64>,
        contiguous: Option<&str>,
    ) -> PyResult<bool> {
        let copy_on_demand = parse_contiguous(contiguous)?;
        let v_view = values.as_array();
        let owned: Vec<f64>;
        let slice: &[f64] = if v_view.is_standard_layout() {
            v_view
                .as_slice()
                .ok_or(KymoraError::NotContiguous { index: None })?
        } else if copy_on_demand {
            warn_copy(py, "values array");
            owned = v_view.iter().copied().collect();
            &owned
        } else {
            return Err(KymoraError::NotContiguous { index: None }.into());
        };
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
