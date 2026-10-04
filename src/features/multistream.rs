#![deny(unsafe_code)]

//! Fleet MultiStreamExtractor for processing thousands of time-series streams concurrently.
//!
//! Stores ring buffers in a contiguous time-major SoA layout `(window_size, n_streams)`
//! and executes lane-parallel O(1) moment updates across all streams on `push_many`.

use crate::pipeline;
use crate::scratch::Scratch;

pub const MULTISTREAM_FAST_NAMES: &[&str] = &[
    "mean",
    "std",
    "var",
    "abs_energy",
    "root_mean_square",
    "zero_crossings",
];

#[derive(Debug, Clone)]
pub struct MultiStreamExtractor {
    pub n_streams: usize,
    pub window_size: usize,
    buffer: Vec<f64>, // layout: [t * n_streams + stream]
    head: usize,
    count: usize,
    sum: Vec<f64>,
    sum_sq: Vec<f64>,
    zero_crossings: Vec<usize>,
    last_val: Vec<f64>,
}

impl MultiStreamExtractor {
    pub fn new(n_streams: usize, window_size: usize) -> Self {
        assert!(n_streams > 0, "n_streams must be at least 1");
        assert!(window_size >= 2, "window_size must be at least 2");

        let total_cap = n_streams * window_size;
        Self {
            n_streams,
            window_size,
            buffer: vec![0.0; total_cap],
            head: 0,
            count: 0,
            sum: vec![0.0; n_streams],
            sum_sq: vec![0.0; n_streams],
            zero_crossings: vec![0; n_streams],
            last_val: vec![0.0; n_streams],
        }
    }

    #[inline]
    pub fn window_size(&self) -> usize {
        self.window_size
    }

    #[inline]
    pub fn n_streams(&self) -> usize {
        self.n_streams
    }

    #[inline]
    pub fn is_full(&self) -> bool {
        self.count >= self.window_size
    }

    #[inline]
    pub fn count(&self) -> usize {
        self.count
    }

    /// Ingest one new sample across all streams simultaneously in a lane-parallel loop.
    pub fn push_many(&mut self, values: &[f64]) -> bool {
        assert_eq!(
            values.len(),
            self.n_streams,
            "values length must match n_streams"
        );

        let s_count = self.n_streams;
        let base = self.head * s_count;
        let is_full = self.count >= self.window_size;

        if is_full {
            for s in 0..s_count {
                let old_v = self.buffer[base + s];
                self.sum[s] -= old_v;
                self.sum_sq[s] -= old_v * old_v;
            }
        }

        for (s, &v) in values.iter().enumerate().take(s_count) {
            self.buffer[base + s] = v;
            self.sum[s] += v;
            self.sum_sq[s] += v * v;

            if self.count > 0 && ((v > 0.0) != (self.last_val[s] > 0.0)) && v != 0.0 {
                self.zero_crossings[s] += 1;
            }
            self.last_val[s] = v;
        }

        self.head = (self.head + 1) % self.window_size;
        self.count += 1;
        self.count >= self.window_size
    }

    /// Reset state across all streams or a single stream.
    pub fn reset(&mut self, stream_idx: Option<usize>) {
        match stream_idx {
            Some(s) => {
                assert!(s < self.n_streams, "stream index out of bounds");
                self.sum[s] = 0.0;
                self.sum_sq[s] = 0.0;
                self.zero_crossings[s] = 0;
                self.last_val[s] = 0.0;
                for t in 0..self.window_size {
                    self.buffer[t * self.n_streams + s] = 0.0;
                }
            }
            None => {
                self.buffer.fill(0.0);
                self.head = 0;
                self.count = 0;
                self.sum.fill(0.0);
                self.sum_sq.fill(0.0);
                self.zero_crossings.fill(0);
                self.last_val.fill(0.0);
            }
        }
    }

    /// Compute O(1) online fast features for requested stream subset.
    pub fn compute_fast(&self, streams: &[usize], out: &mut [f64]) {
        let n_cols = MULTISTREAM_FAST_NAMES.len();
        assert!(out.len() >= streams.len() * n_cols);

        let w = self.count.min(self.window_size).max(1);
        let wf = w as f64;

        for (row_idx, &s) in streams.iter().enumerate() {
            let row_out = &mut out[row_idx * n_cols..(row_idx + 1) * n_cols];
            if s >= self.n_streams || self.count == 0 {
                row_out.fill(f64::NAN);
                continue;
            }

            let mean = self.sum[s] / wf;
            let sum_sq = self.sum_sq[s];
            let var = (sum_sq / wf - mean * mean).max(0.0);
            let std = var.sqrt();
            let abs_energy = sum_sq;
            let rms = (abs_energy / wf).sqrt();
            let zc = self.zero_crossings[s] as f64;

            row_out[0] = mean;
            row_out[1] = std;
            row_out[2] = var;
            row_out[3] = abs_energy;
            row_out[4] = rms;
            row_out[5] = zc;
        }
    }

    /// Compute full core33 features for requested stream subset.
    pub fn compute_all(&self, streams: &[usize], scratch: &mut Scratch, out: &mut [f64]) {
        let n_cols = pipeline::CORE33_COUNT;
        assert!(out.len() >= streams.len() * n_cols);

        let w = self.count.min(self.window_size);
        if w == 0 {
            out[..streams.len() * n_cols].fill(f64::NAN);
            return;
        }

        let mut series_buf = vec![0.0f64; w];

        for (row_idx, &s) in streams.iter().enumerate() {
            let row_out = &mut out[row_idx * n_cols..(row_idx + 1) * n_cols];
            if s >= self.n_streams {
                row_out.fill(f64::NAN);
                continue;
            }

            // Extract stream history in chronological order
            let start = if self.count < self.window_size {
                0
            } else {
                self.head
            };

            for (i, elem) in series_buf.iter_mut().enumerate().take(w) {
                let t = (start + i) % self.window_size;
                *elem = self.buffer[t * self.n_streams + s];
            }

            pipeline::run_core33(&series_buf, scratch, row_out);
        }
    }
}
