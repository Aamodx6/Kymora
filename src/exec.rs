#![deny(unsafe_code)]

//! Parallel and serial execution schedulers.

use crate::pipeline;
use crate::plan::FeaturePlan;
use crate::scratch::Scratch;
use rayon::prelude::*;
use std::sync::atomic::{AtomicU32, Ordering};

pub const SERIAL_THRESHOLD: usize = 8;
pub const MIN_ROWS_PER_TASK: usize = 16;
pub const SERIAL_WORK_SIZE_THRESHOLD: usize = 8_000;

static POOL_PID: AtomicU32 = AtomicU32::new(0);

/// Check if the current process is a forked child of a process that already initialized/used a thread pool.
pub fn is_forked_child() -> bool {
    let pid = POOL_PID.load(Ordering::Relaxed);
    pid != 0 && std::process::id() != pid
}

/// Record thread pool usage in the current process.
pub fn record_pool_use() {
    let _ = POOL_PID.compare_exchange(0, std::process::id(), Ordering::SeqCst, Ordering::SeqCst);
}

/// Dynamic work size threshold: reads `KYMORA_SERIAL_THRESHOLD` environment variable if set,
/// otherwise dynamically scales with hardware/pool thread count (500 points per thread, min 8,000).
pub fn get_serial_work_threshold() -> usize {
    if let Ok(val) = std::env::var("KYMORA_SERIAL_THRESHOLD") {
        if let Ok(thresh) = val.trim().parse::<usize>() {
            return thresh;
        }
    }
    let pool_threads = rayon::current_num_threads();
    (pool_threads * 500).max(8_000)
}

/// Determine whether a workload should execute in parallel or sequentially.
pub fn should_run_parallel(n_rows: usize, total_points: usize) -> bool {
    if is_forked_child() {
        return false;
    }
    let pool_threads = rayon::current_num_threads();
    pool_threads > 1 && n_rows >= pool_threads && total_points >= get_serial_work_threshold()
}

/// Extract features into pre-allocated flat slice in row-major order (f64) using FeaturePlan.
pub fn extract_plan_into_slice(rows: &[&[f64]], plan: &FeaturePlan, out_slice: &mut [f64]) {
    let n_rows = rows.len();
    if n_rows == 0 {
        return;
    }
    let n_cols = plan.n_features();
    let max_len = rows.iter().map(|r| r.len()).max().unwrap_or(0);
    let total_points: usize = rows.iter().map(|r| r.len()).sum();

    if !should_run_parallel(n_rows, total_points) {
        crate::scratch::with_thread_scratch(max_len, |scratch| {
            for (row, row_out) in rows.iter().zip(out_slice.chunks_exact_mut(n_cols)) {
                pipeline::run_plan(row, plan, scratch, row_out);
            }
        });
    } else {
        record_pool_use();
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
///
/// The f32 kernels implement the core33 set only. `gather` selects the plan:
/// - `None`: direct core33 output (`out` must be 33 wide per row).
/// - `Some(idxs)`: every index must be < 33; each row runs full core33 into a
///   stack buffer and gathers the requested columns (covers `minimal` and any
///   core33 subset with zero copies). Non-core33 plans are rejected at the FFI
///   boundary before this is reached, never here.
pub fn extract_into_slice_f32(
    rows: &[&[f32]],
    out_slice: &mut [f64],
    n_cols: usize,
    gather: Option<&[usize]>,
) {
    let n_rows = rows.len();
    if n_rows == 0 {
        return;
    }

    let max_len = rows.iter().map(|r| r.len()).max().unwrap_or(0);
    let total_points: usize = rows.iter().map(|r| r.len()).sum();
    if !should_run_parallel(n_rows, total_points) {
        crate::scratch::with_thread_scratch(max_len, |scratch| match gather {
            None => {
                for (row, row_out) in rows.iter().zip(out_slice.chunks_exact_mut(n_cols)) {
                    pipeline::run_core33_f32(row, scratch, row_out);
                }
            }
            Some(idxs) => {
                for (row, row_out) in rows.iter().zip(out_slice.chunks_exact_mut(n_cols)) {
                    let mut full = [0.0f64; 33];
                    pipeline::run_core33_f32(row, scratch, &mut full);
                    for (dst, &src) in row_out.iter_mut().zip(idxs.iter()) {
                        *dst = full[src];
                    }
                }
            }
        });
    } else {
        record_pool_use();
        out_slice
            .par_chunks_exact_mut(n_cols)
            .with_min_len(MIN_ROWS_PER_TASK)
            .zip(rows.par_iter())
            .for_each_init(
                || Scratch::new(max_len),
                |scratch, (row_out, row)| {
                    if let Some(idxs) = gather {
                        let mut full = [0.0f64; 33];
                        pipeline::run_core33_f32(row, scratch, &mut full);
                        for (dst, &src) in row_out.iter_mut().zip(idxs.iter()) {
                            *dst = full[src];
                        }
                    } else {
                        pipeline::run_core33_f32(row, scratch, row_out);
                    }
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

    let total_points = n_windows * window;
    if !should_run_parallel(n_windows, total_points) {
        crate::scratch::with_thread_scratch(window, |scratch| {
            for i in 0..n_windows {
                let start = i * stride;
                let window_slice = &x[start..start + window];
                let row_out = &mut out_slice[i * n_cols..(i + 1) * n_cols];
                pipeline::run_plan(window_slice, plan, scratch, row_out);
            }
        });
    } else {
        record_pool_use();
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
) -> Result<(), crate::error::KymoraError> {
    if offsets.len() < 2 {
        return Err(crate::error::KymoraError::EmptyInput);
    }
    let n_series = offsets.len() - 1;

    let mut rows = Vec::with_capacity(n_series);
    for i in 0..n_series {
        let start = offsets[i];
        let end = offsets[i + 1];
        if start < 0 || end < start || (end as usize) > values.len() {
            return Err(crate::error::KymoraError::EmptySeries { index: i });
        }
        let start_u = start as usize;
        let end_u = end as usize;
        if start_u == end_u {
            return Err(crate::error::KymoraError::EmptySeries { index: i });
        }
        rows.push(&values[start_u..end_u]);
    }

    extract_plan_into_slice(&rows, plan, out_slice);
    Ok(())
}

/// Extract features from CSR ragged arrays (f32 values).
/// `gather` follows [`extract_into_slice_f32`].
pub fn extract_ragged_csr_f32(
    values: &[f32],
    offsets: &[i64],
    out_slice: &mut [f64],
    n_cols: usize,
    gather: Option<&[usize]>,
) -> Result<(), crate::error::KymoraError> {
    if offsets.len() < 2 {
        return Err(crate::error::KymoraError::EmptyInput);
    }
    let n_series = offsets.len() - 1;

    let mut rows = Vec::with_capacity(n_series);
    for i in 0..n_series {
        let start = offsets[i];
        let end = offsets[i + 1];
        if start < 0 || end < start || (end as usize) > values.len() {
            return Err(crate::error::KymoraError::EmptySeries { index: i });
        }
        let start_u = start as usize;
        let end_u = end as usize;
        if start_u == end_u {
            return Err(crate::error::KymoraError::EmptySeries { index: i });
        }
        rows.push(&values[start_u..end_u]);
    }

    extract_into_slice_f32(&rows, out_slice, n_cols, gather);
    Ok(())
}
