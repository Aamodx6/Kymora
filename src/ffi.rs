//! PyO3 boundary: the only place Rust and Python touch.
//!
//! Responsibilities, in order:
//!   1. obtain zero-copy read views of the caller's numpy buffers,
//!   2. validate structure (shapes, lengths, window geometry) *before* any
//!      compute starts, mapping failures to `TsxError` -> `ValueError`,
//!   3. release the GIL and run the pure-Rust extraction,
//!   4. shape or write directly into in-place numpy buffers.
//!
//! No `panic!`, `unwrap`, or `expect` on a user-reachable path.

use numpy::{
    IntoPyArray, PyArray1, PyArray2, PyArrayMethods, PyReadonlyArray1, PyReadonlyArray2,
    PyUntypedArrayMethods,
};
use pyo3::exceptions::PyTypeError;
use pyo3::prelude::*;
use std::collections::HashMap;

use crate::error::TsxError;
use crate::extract;
use crate::features;
use crate::plan::FeaturePlan;
use crate::registry;

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

/// extract_features(X, profile="core33", features=None, n_jobs=None, out=None) -> (n_series, n_features) float64 array.
///
/// X: 2D C-contiguous float64/float32 array, or a list of 1D arrays (ragged ok).
#[pyfunction]
#[pyo3(signature = (x, profile = None, features = None, n_jobs = None, out = None))]
pub fn extract_features<'py>(
    py: Python<'py>,
    x: &Bound<'py, PyAny>,
    profile: Option<&str>,
    features: Option<Vec<String>>,
    n_jobs: Option<usize>,
    out: Option<&Bound<'py, PyArray2<f64>>>,
) -> PyResult<Bound<'py, PyArray2<f64>>> {
    let feat_refs = features.as_deref();
    let plan = FeaturePlan::build(profile, feat_refs)?;
    let n_cols = plan.n_features();

    // 1. 2D float64 fast path
    if let Ok(arr) = x.extract::<PyReadonlyArray2<f64>>() {
        let view = arr.as_array();
        let nrows = view.nrows();
        let ncols = view.ncols();
        if nrows == 0 {
            return Err(TsxError::EmptyInput.into());
        }
        if ncols == 0 {
            return Err(TsxError::ZeroLengthColumns.into());
        }
        let slice = view
            .as_slice()
            .ok_or(TsxError::NotContiguous { index: None })?;
        let out_arr = get_out_array(py, nrows, n_cols, out)?;
        let out_slice = unsafe {
            out_arr
                .as_slice_mut()
                .map_err(|_| TsxError::NotContiguous { index: None })?
        };
        py.detach(|| {
            run_in_pool(n_jobs, || {
                let rows: Vec<&[f64]> = slice.chunks_exact(ncols).collect();
                crate::exec::extract_plan_into_slice(&rows, &plan, out_slice);
            })
        });
        return Ok(out_arr);
    }

    // 2. 2D float32 fast path (zero-copy memory view, accumulates in f64)
    if let Ok(arr) = x.extract::<PyReadonlyArray2<f32>>() {
        let view = arr.as_array();
        let nrows = view.nrows();
        let ncols = view.ncols();
        if nrows == 0 {
            return Err(TsxError::EmptyInput.into());
        }
        if ncols == 0 {
            return Err(TsxError::ZeroLengthColumns.into());
        }
        let slice = view
            .as_slice()
            .ok_or(TsxError::NotContiguous { index: None })?;
        let out_arr = get_out_array(py, nrows, n_cols, out)?;
        let out_slice = unsafe {
            out_arr
                .as_slice_mut()
                .map_err(|_| TsxError::NotContiguous { index: None })?
        };
        py.detach(|| {
            run_in_pool(n_jobs, || {
                let rows: Vec<&[f32]> = slice.chunks_exact(ncols).collect();
                crate::exec::extract_into_slice_f32(&rows, out_slice, n_cols);
            })
        });
        return Ok(out_arr);
    }

    // 3. List of 1D float64 arrays
    if let Ok(list) = x.extract::<Vec<PyReadonlyArray1<f64>>>() {
        let slices: Vec<&[f64]> = list
            .iter()
            .enumerate()
            .map(|(index, a)| {
                a.as_slice()
                    .map_err(|_| TsxError::NotContiguous { index: Some(index) })
            })
            .collect::<Result<_, TsxError>>()?;
        extract::validate_batch(&slices)?;
        let nrows = slices.len();
        let out_arr = get_out_array(py, nrows, n_cols, out)?;
        let out_slice = unsafe {
            out_arr
                .as_slice_mut()
                .map_err(|_| TsxError::NotContiguous { index: None })?
        };
        py.detach(|| {
            run_in_pool(n_jobs, || {
                crate::exec::extract_plan_into_slice(&slices, &plan, out_slice)
            })
        });
        return Ok(out_arr);
    }

    // 4. List of 1D float32 arrays
    if let Ok(list) = x.extract::<Vec<PyReadonlyArray1<f32>>>() {
        if list.is_empty() {
            return Err(TsxError::EmptyInput.into());
        }
        let mut slices = Vec::with_capacity(list.len());
        for (index, a) in list.iter().enumerate() {
            let s = a
                .as_slice()
                .map_err(|_| TsxError::NotContiguous { index: Some(index) })?;
            if s.is_empty() {
                return Err(TsxError::EmptySeries { index }.into());
            }
            slices.push(s);
        }
        let nrows = slices.len();
        let out_arr = get_out_array(py, nrows, n_cols, out)?;
        let out_slice = unsafe {
            out_arr
                .as_slice_mut()
                .map_err(|_| TsxError::NotContiguous { index: None })?
        };
        py.detach(|| {
            run_in_pool(n_jobs, || {
                crate::exec::extract_into_slice_f32(&slices, out_slice, n_cols)
            })
        });
        return Ok(out_arr);
    }

    Err(PyTypeError::new_err(TYPE_HELP))
}

/// extract_features_ragged(values, offsets, profile="core33", features=None, n_jobs=None, out=None) -> (n_series, n_features) float64 array.
///
/// CSR-style ragged API with zero per-element Python extraction overhead.
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
        .map_err(|_| TsxError::NotContiguous { index: None })?;
    if offsets_slice.len() < 2 {
        return Err(TsxError::EmptyInput.into());
    }
    let nrows = offsets_slice.len() - 1;

    let feat_refs = features.as_deref();
    let plan = FeaturePlan::build(profile, feat_refs)?;
    let n_cols = plan.n_features();

    if let Ok(v64) = values.extract::<PyReadonlyArray1<f64>>() {
        let v_slice = v64
            .as_slice()
            .map_err(|_| TsxError::NotContiguous { index: None })?;
        let out_arr = get_out_array(py, nrows, n_cols, out)?;
        let out_slice = unsafe {
            out_arr
                .as_slice_mut()
                .map_err(|_| TsxError::NotContiguous { index: None })?
        };
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
            .map_err(|_| TsxError::NotContiguous { index: None })?;
        let out_arr = get_out_array(py, nrows, n_cols, out)?;
        let out_slice = unsafe {
            out_arr
                .as_slice_mut()
                .map_err(|_| TsxError::NotContiguous { index: None })?
        };
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

/// sliding_features(x, window, stride=1, profile="core33", features=None, n_jobs=None, out=None) -> (n_windows, n_features) float64 array.
#[pyfunction]
#[pyo3(signature = (x, window, stride = 1, profile = None, features = None, n_jobs = None, out = None))]
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
        .map_err(|_| TsxError::NotContiguous { index: None })?;
    let (window, stride, n_windows) = extract::window_geometry(slice.len(), window, stride)?;

    let feat_refs = features.as_deref();
    let plan = FeaturePlan::build(profile, feat_refs)?;
    let n_cols = plan.n_features();

    let out_arr = get_out_array(py, n_windows, n_cols, out)?;
    let out_slice = unsafe {
        out_arr
            .as_slice_mut()
            .map_err(|_| TsxError::NotContiguous { index: None })?
    };
    py.detach(|| {
        run_in_pool(n_jobs, || {
            crate::exec::extract_windows_plan_into_slice(slice, window, stride, &plan, out_slice)
        })
    });
    Ok(out_arr)
}

/// feature_names(profile=None, features=None) -> list[str], in output column order.
#[pyfunction]
#[pyo3(signature = (profile = None, features = None))]
pub fn feature_names(
    profile: Option<&str>,
    features: Option<Vec<String>>,
) -> PyResult<Vec<&'static str>> {
    if profile.is_none() && features.is_none() {
        return Ok(features::NAMES.to_vec());
    }
    let feat_refs = features.as_deref();
    let plan = FeaturePlan::build(profile, feat_refs)?;
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
    let idx = registry::find_feature(name)
        .ok_or_else(|| TsxError::UnknownFeature { name: name.to_string() })?;
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
