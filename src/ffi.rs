//! PyO3 boundary: the only place Rust and Python touch.
//!
//! Responsibilities, in order:
//!   1. obtain zero-copy read views of the caller's numpy buffers,
//!   2. validate structure (shapes, lengths, window geometry) *before* any
//!      compute starts, mapping failures to `TsxError` -> `ValueError`,
//!   3. release the GIL and run the pure-Rust extraction,
//!   4. shape the result into a numpy array.
//!
//! No `panic!`, `unwrap`, or `expect` on a user-reachable path.

use numpy::{IntoPyArray, PyArray2, PyReadonlyArray1, PyReadonlyArray2};
use pyo3::exceptions::PyTypeError;
use pyo3::prelude::*;

use crate::error::TsxError;
use crate::extract;
use crate::features;

const TYPE_HELP: &str = "extract_features expects a 2D float64 array of shape \
    (n_series, length), or a list of 1D float64 arrays for ragged series. \
    Other dtypes are rejected rather than silently copied — cast explicitly \
    with X.astype(np.float64).";

/// extract_features(X) -> (n_series, n_features) float64 array.
///
/// X: 2D C-contiguous float64 array, or a list of 1D float64 arrays (ragged ok).
#[pyfunction]
pub fn extract_features<'py>(
    py: Python<'py>,
    x: &Bound<'py, PyAny>,
) -> PyResult<Bound<'py, PyArray2<f64>>> {
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
        let flat = py.detach(|| {
            let rows: Vec<&[f64]> = slice.chunks_exact(ncols).collect();
            extract::extract_rows(&rows)
        });
        return Ok(extract::build_matrix(flat, nrows)?.into_pyarray(py));
    }

    let list: Vec<PyReadonlyArray1<f64>> = x
        .extract()
        .map_err(|_| PyTypeError::new_err(TYPE_HELP))?;
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
    let flat = py.detach(|| extract::extract_rows(&slices));
    Ok(extract::build_matrix(flat, nrows)?.into_pyarray(py))
}

/// sliding_features(x, window, stride=1) -> (n_windows, n_features) float64 array.
#[pyfunction]
#[pyo3(signature = (x, window, stride = 1))]
pub fn sliding_features<'py>(
    py: Python<'py>,
    x: PyReadonlyArray1<'py, f64>,
    window: i64,
    stride: i64,
) -> PyResult<Bound<'py, PyArray2<f64>>> {
    let slice = x
        .as_slice()
        .map_err(|_| TsxError::NotContiguous { index: None })?;
    let (window, stride, n_windows) = extract::window_geometry(slice.len(), window, stride)?;
    let flat = py.detach(|| extract::extract_windows(slice, window, stride));
    Ok(extract::build_matrix(flat, n_windows)?.into_pyarray(py))
}

/// feature_names() -> list[str], in output column order.
///
/// This order is a stability guarantee: column `i` of `extract_features` output
/// corresponds to `feature_names()[i]` for every release within a major version.
/// Reordering, renaming, or removing a name is a major-version change.
#[pyfunction]
pub fn feature_names() -> Vec<&'static str> {
    features::NAMES.to_vec()
}
