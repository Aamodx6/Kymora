//! kymora Rust core — PyO3 module registration only. No numeric logic here.

mod error;
pub mod exec;
mod extract;
pub mod features;
mod ffi;
pub mod intermediates;
pub mod kernels;
pub mod nan_policy;
pub mod pipeline;
pub mod plan;
pub mod registry;
pub mod scratch;

#[cfg(test)]
mod proptest_checks;

use pyo3::prelude::*;

#[pymodule]
fn _core(m: &Bound<'_, PyModule>) -> PyResult<()> {
    m.add_function(wrap_pyfunction!(ffi::extract_features, m)?)?;
    m.add_function(wrap_pyfunction!(ffi::extract_features_mc, m)?)?;
    m.add_function(wrap_pyfunction!(ffi::extract_features_ragged, m)?)?;
    m.add_function(wrap_pyfunction!(ffi::sliding_features, m)?)?;
    m.add_function(wrap_pyfunction!(ffi::feature_names, m)?)?;
    m.add_function(wrap_pyfunction!(ffi::feature_names_mc, m)?)?;
    m.add_function(wrap_pyfunction!(ffi::list_profiles, m)?)?;
    m.add_function(wrap_pyfunction!(ffi::describe_feature, m)?)?;
    m.add_class::<ffi::PyStreamingExtractor>()?;
    m.add_class::<ffi::PyMultiStreamExtractor>()?;
    Ok(())
}
