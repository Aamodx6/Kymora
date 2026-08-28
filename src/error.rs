//! Structural error type for the FFI boundary.
//!
//! Scope discipline: `TsxError` describes *structural* problems with a call —
//! shapes, lengths, window geometry, memory layout. It never describes the
//! *values* in a series. NaN in the input is a legitimate value with a
//! documented propagation contract (see `features::compute_all`), not an error,
//! and no variant here may be used to signal it.

use pyo3::exceptions::PyValueError;
use pyo3::PyErr;
use std::fmt;

#[derive(Debug, Clone, PartialEq, Eq)]
pub enum TsxError {
    /// No series at all: empty list, or a 2D array with zero rows.
    EmptyInput,
    /// A series with zero elements. `index` is its position in the batch.
    EmptySeries { index: usize },
    /// A 2D input with zero columns (every series would be zero-length).
    ZeroLengthColumns,
    /// Input array is not contiguous, so it cannot be viewed without a copy.
    NotContiguous { index: Option<usize> },
    /// `window` or `stride` was zero or negative.
    NonPositiveWindowParam { name: &'static str, value: i64 },
    /// `window` exceeds the series length.
    WindowTooLarge { window: usize, len: usize },
    /// Output buffer could not be shaped as expected. Indicates an internal
    /// inconsistency rather than bad user input; surfaced instead of panicking.
    OutputShape {
        rows: usize,
        cols: usize,
        len: usize,
    },
}

impl fmt::Display for TsxError {
    fn fmt(&self, f: &mut fmt::Formatter<'_>) -> fmt::Result {
        match self {
            TsxError::EmptyInput => write!(
                f,
                "input contains no series; expected at least one series of length >= 1"
            ),
            TsxError::EmptySeries { index } => write!(
                f,
                "series at index {index} has length 0; zero-length series are not \
                 supported (features are undefined, so this is an error rather than \
                 a NaN row)"
            ),
            TsxError::ZeroLengthColumns => write!(
                f,
                "input array has 0 columns; every series would be zero-length"
            ),
            TsxError::NotContiguous { index } => match index {
                Some(i) => write!(
                    f,
                    "series at index {i} is not contiguous; pass \
                     np.ascontiguousarray(x) (tsxtractor reads numpy buffers \
                     without copying, so a strided view cannot be used)"
                ),
                None => write!(
                    f,
                    "input array is not C-contiguous; pass \
                     np.ascontiguousarray(X) (tsxtractor reads numpy buffers \
                     without copying, so a strided view cannot be used)"
                ),
            },
            TsxError::NonPositiveWindowParam { name, value } => {
                write!(f, "{name} must be >= 1, got {value}")
            }
            TsxError::WindowTooLarge { window, len } => write!(
                f,
                "window ({window}) is larger than the series length ({len})"
            ),
            TsxError::OutputShape { rows, cols, len } => write!(
                f,
                "internal error: cannot shape {len} values as ({rows}, {cols})"
            ),
        }
    }
}

impl std::error::Error for TsxError {}

/// Single conversion point: every structural error becomes a Python `ValueError`.
impl From<TsxError> for PyErr {
    fn from(e: TsxError) -> PyErr {
        PyValueError::new_err(e.to_string())
    }
}
