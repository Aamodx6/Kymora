#![deny(unsafe_code)]

//! `nan_policy` handling for the FFI boundary.
//!
//! Scope discipline (arch I2, hard rule): finding NaN in a series describes
//! *values*, so it is never a [`crate::error::KymoraError`]. This module
//! returns plain positions / message strings and the FFI layer raises them
//! directly as Python `ValueError`. Supported policies:
//!
//! - `"propagate"` (default): NaN rows propagate per the value contract in
//!   `features::compute_all`. Existing behavior, unchanged.
//! - `"raise"`: fail fast naming the first offending series/window.
//! - `"omit"`: NOT supported. Pairwise deletion would silently change window
//!   contents and lengths; per the documented policy the caller cleans the
//!   series first (`x[~np.isnan(x)]`), so the imputation stays theirs and
//!   visible. Requesting it is an explicit error, not silent propagation.

/// Parsed `nan_policy` option.
#[derive(Debug, Clone, Copy, PartialEq, Eq)]
pub enum NanPolicy {
    Propagate,
    Raise,
}

/// Parse the user-facing option. `None` means the default (`"propagate"`).
/// `Err(String)` carries the exact Python error message.
pub fn parse(policy: Option<&str>) -> Result<NanPolicy, String> {
    match policy {
        None | Some("propagate") => Ok(NanPolicy::Propagate),
        Some("raise") => Ok(NanPolicy::Raise),
        Some("omit") => Err(
            "nan_policy='omit' is not supported: kymora never imputes or drops \
             samples silently (see docs/numerics.md). Clean the series first, e.g. \
             x[~np.isnan(x)] or an interpolation of your choosing, then call with \
             nan_policy='propagate' (default)."
                .to_string(),
        ),
        Some(other) => Err(format!(
            "unknown nan_policy '{other}'; valid policies: 'propagate' (default), 'raise'"
        )),
    }
}

/// Index of the first series containing a NaN, if any.
pub fn first_nan_series_f64(rows: &[&[f64]]) -> Option<usize> {
    rows.iter().position(|row| row.iter().any(|v| v.is_nan()))
}

/// Index of the first series containing a NaN, if any (f32 input).
pub fn first_nan_series_f32(rows: &[&[f32]]) -> Option<usize> {
    rows.iter().position(|row| row.iter().any(|v| v.is_nan()))
}

/// Index of the first NaN sample in a flat slice, if any.
pub fn first_nan_sample_f64(values: &[f64]) -> Option<usize> {
    values.iter().position(|v| v.is_nan())
}

/// Series index containing flat offset `pos` given CSR `offsets`.
pub fn series_for_offset(offsets: &[i64], pos: usize) -> usize {
    let mut lo = 0usize;
    let mut hi = offsets.len() - 1;
    while lo + 1 < hi {
        let mid = (lo + hi) / 2;
        if offsets[mid] as usize <= pos {
            lo = mid;
        } else {
            hi = mid;
        }
    }
    lo
}

#[cfg(test)]
mod tests {
    use super::*;

    #[test]
    fn parse_defaults_to_propagate() {
        assert_eq!(parse(None), Ok(NanPolicy::Propagate));
        assert_eq!(parse(Some("propagate")), Ok(NanPolicy::Propagate));
        assert_eq!(parse(Some("raise")), Ok(NanPolicy::Raise));
        assert!(parse(Some("omit")).is_err());
        assert!(parse(Some("drop")).is_err());
    }

    #[test]
    fn scanners_find_first_nan() {
        let a = [1.0, 2.0];
        let b = [1.0, f64::NAN];
        let c = [f64::NAN, 0.0];
        let rows: Vec<&[f64]> = vec![&a, &b, &c];
        assert_eq!(first_nan_series_f64(&rows), Some(1));
        assert_eq!(first_nan_sample_f64(&b), Some(1));
        assert_eq!(first_nan_sample_f64(&a), None);
        assert_eq!(series_for_offset(&[0, 2, 4, 6], 4), 2);
        assert_eq!(series_for_offset(&[0, 2, 4, 6], 0), 0);
    }
}
