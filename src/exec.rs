//! Parallel and serial execution schedulers.

use crate::pipeline;
use crate::plan::FeaturePlan;
use crate::scratch::Scratch;
use rayon::prelude::*;

pub const SERIAL_THRESHOLD: usize = 8;
pub const MIN_ROWS_PER_TASK: usize = 16;

/// Extract features into pre-allocated flat slice in row-major order (f64) using FeaturePlan.
pub fn extract_plan_into_slice(rows: &[&[f64]], plan: &FeaturePlan, out_slice: &mut [f64]) {
    let n_rows = rows.len();
    if n_rows == 0 {
        return;
    }
    let n_cols = plan.n_features();
    let max_len = rows.iter().map(|r| r.len()).max().unwrap_or(0);

    if n_rows < SERIAL_THRESHOLD {
        let mut scratch = Scratch::new(max_len);
        for (row, row_out) in rows.iter().zip(out_slice.chunks_exact_mut(n_cols)) {
            pipeline::run_plan(row, plan, &mut scratch, row_out);
        }
    } else {
        out_slice
            .par_chunks_exact_mut(n_cols)
            .with_min_len(MIN_ROWS_PER_TASK)
            .zip(rows.par_iter())
            .for_each_init(
                || Scratch::new(max_len),
                |scratch, (row_out, row)| {
                    pipeline::run_plan(row, plan, scratch, row_out);
                },
            );
    }
}

/// Extract features into pre-allocated flat slice in row-major order (f32).
pub fn extract_into_slice_f32(rows: &[&[f32]], out_slice: &mut [f64], n_cols: usize) {
    let n_rows = rows.len();
    if n_rows == 0 {
        return;
    }

    let max_len = rows.iter().map(|r| r.len()).max().unwrap_or(0);

    if n_rows < SERIAL_THRESHOLD {
        let mut scratch = Scratch::new(max_len);
        for (row, row_out) in rows.iter().zip(out_slice.chunks_exact_mut(n_cols)) {
            pipeline::run_core33_f32(row, &mut scratch, row_out);
        }
    } else {
        out_slice
            .par_chunks_exact_mut(n_cols)
            .with_min_len(MIN_ROWS_PER_TASK)
            .zip(rows.par_iter())
            .for_each_init(
                || Scratch::new(max_len),
                |scratch, (row_out, row)| {
                    pipeline::run_core33_f32(row, scratch, row_out);
                },
            );
    }
}

/// Extract features for rolling sliding windows using FeaturePlan.
pub fn extract_windows_plan_into_slice(
    x: &[f64],
    window: usize,
    stride: usize,
    plan: &FeaturePlan,
    out_slice: &mut [f64],
) {
    let n_cols = plan.n_features();
    let n_windows = out_slice.len() / n_cols;
    if n_windows == 0 {
        return;
    }

    if n_windows < SERIAL_THRESHOLD {
        let mut scratch = Scratch::new(window);
        for i in 0..n_windows {
            let start = i * stride;
            let window_slice = &x[start..start + window];
            let row_out = &mut out_slice[i * n_cols..(i + 1) * n_cols];
            pipeline::run_plan(window_slice, plan, &mut scratch, row_out);
        }
    } else {
        out_slice
            .par_chunks_exact_mut(n_cols)
            .enumerate()
            .with_min_len(MIN_ROWS_PER_TASK)
            .for_each_init(
                || Scratch::new(window),
                |scratch, (i, row_out)| {
                    let start = i * stride;
                    let window_slice = &x[start..start + window];
                    pipeline::run_plan(window_slice, plan, scratch, row_out);
                },
            );
    }
}

/// Extract features from CSR ragged arrays using FeaturePlan.
pub fn extract_ragged_csr_plan(
    values: &[f64],
    offsets: &[i64],
    plan: &FeaturePlan,
    out_slice: &mut [f64],
) -> Result<(), crate::error::TsxError> {
    if offsets.len() < 2 {
        return Err(crate::error::TsxError::EmptyInput);
    }
    let n_series = offsets.len() - 1;

    let mut rows = Vec::with_capacity(n_series);
    for i in 0..n_series {
        let start = offsets[i];
        let end = offsets[i + 1];
        if start < 0 || end < start || (end as usize) > values.len() {
            return Err(crate::error::TsxError::EmptySeries { index: i });
        }
        let start_u = start as usize;
        let end_u = end as usize;
        if start_u == end_u {
            return Err(crate::error::TsxError::EmptySeries { index: i });
        }
        rows.push(&values[start_u..end_u]);
    }

    extract_plan_into_slice(&rows, plan, out_slice);
    Ok(())
}

/// Extract features from CSR ragged arrays (f32 values).
pub fn extract_ragged_csr_f32(
    values: &[f32],
    offsets: &[i64],
    out_slice: &mut [f64],
    n_cols: usize,
) -> Result<(), crate::error::TsxError> {
    if offsets.len() < 2 {
        return Err(crate::error::TsxError::EmptyInput);
    }
    let n_series = offsets.len() - 1;

    let mut rows = Vec::with_capacity(n_series);
    for i in 0..n_series {
        let start = offsets[i];
        let end = offsets[i + 1];
        if start < 0 || end < start || (end as usize) > values.len() {
            return Err(crate::error::TsxError::EmptySeries { index: i });
        }
        let start_u = start as usize;
        let end_u = end as usize;
        if start_u == end_u {
            return Err(crate::error::TsxError::EmptySeries { index: i });
        }
        rows.push(&values[start_u..end_u]);
    }

    extract_into_slice_f32(&rows, out_slice, n_cols);
    Ok(())
}
