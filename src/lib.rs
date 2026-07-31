mod features;

use numpy::{IntoPyArray, PyArray2, PyReadonlyArray1, PyReadonlyArray2};
use pyo3::prelude::*;
use rayon::prelude::*;

fn extract_rows(rows: &[&[f64]]) -> Vec<f64> {
    let nf = features::NAMES.len();
    let mut out = vec![0.0f64; rows.len() * nf];
    out.par_chunks_mut(nf)
        .zip(rows.par_iter())
        .for_each(|(chunk, row)| features::compute_all(row, chunk));
    out
}

fn to_array2<'py>(py: Python<'py>, flat: Vec<f64>, nrows: usize) -> Bound<'py, PyArray2<f64>> {
    let nf = features::NAMES.len();
    numpy::ndarray::Array2::from_shape_vec((nrows, nf), flat)
        .expect("shape mismatch")
        .into_pyarray(py)
}

/// extract_features(X) -> (n_series, n_features) array.
/// X: 2D float64 array or list of 1D float64 arrays (ragged ok).
#[pyfunction]
fn extract_features<'py>(
    py: Python<'py>,
    x: &Bound<'py, PyAny>,
) -> PyResult<Bound<'py, PyArray2<f64>>> {
    if let Ok(arr) = x.extract::<PyReadonlyArray2<f64>>() {
        let view = arr.as_array();
        let slice = view
            .as_slice()
            .ok_or_else(|| PyErr::new::<pyo3::exceptions::PyValueError, _>(
                "array must be C-contiguous",
            ))?;
        let ncols = view.ncols();
        let nrows = view.nrows();
        let flat = py.detach(|| {
            let rows: Vec<&[f64]> = slice.chunks_exact(ncols.max(1)).collect();
            extract_rows(&rows)
        });
        return Ok(to_array2(py, flat, nrows));
    }
    // list of 1D arrays (ragged)
    let list: Vec<PyReadonlyArray1<f64>> = x.extract().map_err(|_| {
        PyErr::new::<pyo3::exceptions::PyTypeError, _>(
            "expected 2D float64 array or list of 1D float64 arrays",
        )
    })?;
    let slices: Vec<&[f64]> = list
        .iter()
        .map(|a| {
            a.as_slice().map_err(|_| {
                PyErr::new::<pyo3::exceptions::PyValueError, _>("series must be contiguous")
            })
        })
        .collect::<PyResult<_>>()?;
    let nrows = slices.len();
    let flat = py.detach(|| extract_rows(&slices));
    Ok(to_array2(py, flat, nrows))
}

/// sliding_features(x, window, stride=1) -> (n_windows, n_features) array.
#[pyfunction]
#[pyo3(signature = (x, window, stride = 1))]
fn sliding_features<'py>(
    py: Python<'py>,
    x: PyReadonlyArray1<'py, f64>,
    window: usize,
    stride: usize,
) -> PyResult<Bound<'py, PyArray2<f64>>> {
    if window == 0 || stride == 0 {
        return Err(PyErr::new::<pyo3::exceptions::PyValueError, _>(
            "window and stride must be >= 1",
        ));
    }
    let slice = x.as_slice().map_err(|_| {
        PyErr::new::<pyo3::exceptions::PyValueError, _>("array must be contiguous")
    })?;
    if slice.len() < window {
        return Err(PyErr::new::<pyo3::exceptions::PyValueError, _>(
            "series shorter than window",
        ));
    }
    let flat = py.detach(|| {
        let rows: Vec<&[f64]> = slice.windows(window).step_by(stride).collect();
        extract_rows(&rows)
    });
    let nrows = (slice.len() - window) / stride + 1;
    Ok(to_array2(py, flat, nrows))
}

#[pyfunction]
fn feature_names() -> Vec<&'static str> {
    features::NAMES.to_vec()
}

#[pymodule]
fn _core(m: &Bound<'_, PyModule>) -> PyResult<()> {
    m.add_function(wrap_pyfunction!(extract_features, m)?)?;
    m.add_function(wrap_pyfunction!(sliding_features, m)?)?;
    m.add_function(wrap_pyfunction!(feature_names, m)?)?;
    Ok(())
}
