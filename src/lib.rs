//! tsxtractor Rust core — PyO3 module registration only. No numeric logic here.
//!
//! Layout:
//!   error.rs    structural error type, single TsxError -> PyErr conversion
//!   ffi.rs      #[pyfunction] wrappers: zero-copy views, validation, GIL release
//!   extract.rs  pure-Rust dispatch and validation over borrowed series views
//!   features/   the 33 feature computations + the name registry

mod error;
mod extract;
mod features;
mod ffi;

use pyo3::prelude::*;

#[pymodule]
fn _core(m: &Bound<'_, PyModule>) -> PyResult<()> {
    m.add_function(wrap_pyfunction!(ffi::extract_features, m)?)?;
    m.add_function(wrap_pyfunction!(ffi::sliding_features, m)?)?;
    m.add_function(wrap_pyfunction!(ffi::feature_names, m)?)?;
    Ok(())
}
