//! Dispatch and validation, independent of Python.
//!
//! Everything here is pure Rust: it takes borrowed `&[f64]` views (already
//! obtained zero-copy at the FFI boundary) and returns `Result`, never panics,
//! and never inspects series *values* — value semantics (NaN propagation) live
//! entirely in `features::compute_all`.

use crate::error::TsxError;
use crate::features;
use numpy::ndarray::Array2;
use rayon::prelude::*;

/// Number of output columns.
#[inline]
#[allow(dead_code)]
pub fn n_features() -> usize {
    features::NAMES.len()
}

/// Structural validation of a batch of series views.
///
/// Checks lengths only — no data is read, so this adds no copy and no pass over
/// the series contents.
pub fn validate_batch(rows: &[&[f64]]) -> Result<(), TsxError> {
    if rows.is_empty() {
        return Err(TsxError::EmptyInput);
    }
    for (index, row) in rows.iter().enumerate() {
        if row.is_empty() {
            return Err(TsxError::EmptySeries { index });
        }
    }
    Ok(())
}

/// Compute all features for every series, in parallel across series.
///
/// Callers must have validated with [`validate_batch`] first. The GIL is
/// expected to be released by the caller around this call.
#[allow(dead_code)]
pub fn extract_rows(rows: &[&[f64]]) -> Vec<f64> {
    let nf = n_features();
    let mut out = vec![0.0f64; rows.len() * nf];
    out.par_chunks_mut(nf)
        .zip(rows.par_iter())
        .for_each(|(chunk, row)| features::compute_all(row, chunk));
    out
}

/// Shape a flat feature buffer into `(nrows, n_features)` without panicking.
#[allow(dead_code)]
pub fn build_matrix(flat: Vec<f64>, nrows: usize) -> Result<Array2<f64>, TsxError> {
    let cols = n_features();
    let len = flat.len();
    Array2::from_shape_vec((nrows, cols), flat).map_err(|_| TsxError::OutputShape {
        rows: nrows,
        cols,
        len,
    })
}

/// Validated sliding-window geometry: `(window, stride, n_windows)`.
///
/// `window` and `stride` arrive as `i64` so that negative values produce a
/// `ValueError` here rather than an `OverflowError` during PyO3's conversion to
/// `usize`.
pub fn window_geometry(
    len: usize,
    window: i64,
    stride: i64,
) -> Result<(usize, usize, usize), TsxError> {
    if window < 1 {
        return Err(TsxError::NonPositiveWindowParam {
            name: "window",
            value: window,
        });
    }
    if stride < 1 {
        return Err(TsxError::NonPositiveWindowParam {
            name: "stride",
            value: stride,
        });
    }
    let window = window as usize;
    let stride = stride as usize;
    if len == 0 {
        return Err(TsxError::EmptySeries { index: 0 });
    }
    if window > len {
        return Err(TsxError::WindowTooLarge { window, len });
    }
    let n_windows = (len - window) / stride + 1;
    Ok((window, stride, n_windows))
}

/// Feature matrix over rolling windows of one series.
///
/// Windows are borrowed slices of the caller's buffer — no data is copied.
#[allow(dead_code)]
pub fn extract_windows(x: &[f64], window: usize, stride: usize) -> Vec<f64> {
    let rows: Vec<&[f64]> = x.windows(window).step_by(stride).collect();
    extract_rows(&rows)
}

#[cfg(test)]
mod tests {
    use super::*;

    #[test]
    fn empty_batch_is_an_error() {
        assert_eq!(validate_batch(&[]), Err(TsxError::EmptyInput));
    }

    #[test]
    fn zero_length_series_is_an_error() {
        let a = [1.0, 2.0];
        let rows: Vec<&[f64]> = vec![&a[..], &[]];
        assert_eq!(
            validate_batch(&rows),
            Err(TsxError::EmptySeries { index: 1 })
        );
    }

    #[test]
    fn nan_is_not_a_structural_error() {
        let a = [f64::NAN, 1.0];
        let rows: Vec<&[f64]> = vec![&a[..]];
        assert!(validate_batch(&rows).is_ok());
    }

    #[test]
    fn window_geometry_rejects_bad_params() {
        assert!(window_geometry(10, 0, 1).is_err());
        assert!(window_geometry(10, -1, 1).is_err());
        assert!(window_geometry(10, 5, 0).is_err());
        assert!(window_geometry(10, 5, -3).is_err());
        assert!(window_geometry(10, 11, 1).is_err());
        assert!(window_geometry(0, 1, 1).is_err());
        // returns (window, stride, n_windows)
        assert_eq!(window_geometry(10, 10, 1).unwrap(), (10, 1, 1));
        assert_eq!(window_geometry(10, 4, 3).unwrap(), (4, 3, 3));
        assert_eq!(window_geometry(10, 1, 1).unwrap(), (1, 1, 10));
    }
}
