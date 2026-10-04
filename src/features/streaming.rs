#![deny(unsafe_code)]

//! Online incremental streaming feature extractor.
//!
//! Provides an O(1) incremental update engine for rolling windows over time series.
//! Maintains circular buffer history and running accumulators for moments, trend,
//! successive differences, and cross-products, eliminating O(W) redundant scans.

use super::{compute_all, NAMES};

/// Incremental streaming extractor maintaining a rolling window of size `window_size`.
#[derive(Debug, Clone)]
pub struct StreamingExtractor {
    window_size: usize,
    buffer: Vec<f64>,
    head: usize,
    count: usize,

    // Running accumulators
    sum: f64,
    sum_sq: f64,
    sum_cube: f64,
    sum_quad: f64,
    trend_sum: f64,
    abs_diff_sum: f64,
    sq_diff_sum: f64,
    zero_crossings: usize,

    // Step counter for periodic numerical stabilization
    steps_since_anchor: usize,
}

impl StreamingExtractor {
    /// Create a new streaming extractor with the specified window capacity.
    pub fn new(window_size: usize) -> Self {
        assert!(window_size >= 2, "window_size must be at least 2");
        Self {
            window_size,
            buffer: vec![0.0; window_size],
            head: 0,
            count: 0,
            sum: 0.0,
            sum_sq: 0.0,
            sum_cube: 0.0,
            sum_quad: 0.0,
            trend_sum: 0.0,
            abs_diff_sum: 0.0,
            sq_diff_sum: 0.0,
            zero_crossings: 0,
            steps_since_anchor: 0,
        }
    }

    /// Returns the configured window size.
    #[inline]
    pub fn window_size(&self) -> usize {
        self.window_size
    }

    /// Returns the number of samples ingested so far.
    #[inline]
    pub fn count(&self) -> usize {
        self.count
    }

    /// Returns true if the rolling window is completely filled.
    #[inline]
    pub fn is_full(&self) -> bool {
        self.count >= self.window_size
    }

    /// Reset the extractor state.
    pub fn reset(&mut self) {
        self.head = 0;
        self.count = 0;
        self.sum = 0.0;
        self.sum_sq = 0.0;
        self.sum_cube = 0.0;
        self.sum_quad = 0.0;
        self.trend_sum = 0.0;
        self.abs_diff_sum = 0.0;
        self.sq_diff_sum = 0.0;
        self.zero_crossings = 0;
        self.steps_since_anchor = 0;
    }

    /// Ingest a new sample into the rolling window with O(1) state update.
    ///
    /// Returns `true` if the window is full and a valid feature vector is available.
    pub fn push(&mut self, val: f64) -> bool {
        let w = self.window_size;

        if self.count < w {
            // Warming up: fill buffer sequentially
            self.buffer[self.count] = val;
            self.count += 1;
            if self.count == w {
                self.recompute_accumulators();
                return true;
            }
            return false;
        }

        // Rolling update: window is already full
        let old_val = self.buffer[self.head];
        let prev_val_index = if self.head == 0 { w - 1 } else { self.head - 1 };
        let prev_new = self.buffer[prev_val_index];
        let next_head = (self.head + 1) % w;
        let second_old = self.buffer[next_head];

        // 1. Update power sums O(1)
        let old_sq = old_val * old_val;
        let old_cube = old_sq * old_val;
        let old_quad = old_sq * old_sq;

        let new_sq = val * val;
        let new_cube = new_sq * val;
        let new_quad = new_sq * new_sq;

        let prev_sum = self.sum;
        self.sum += val - old_val;
        self.sum_sq += new_sq - old_sq;
        self.sum_cube += new_cube - old_cube;
        self.sum_quad += new_quad - old_quad;

        // 2. Update linear trend covariance O(1):
        // T_new = T_old - (S_prev - old_val) + (W - 1) * new_val
        self.trend_sum += (w as f64 - 1.0) * val - (prev_sum - old_val);

        // 3. Update successive differences O(1):
        let outgoing_diff = (second_old - old_val).abs();
        let incoming_diff = (val - prev_new).abs();
        self.abs_diff_sum += incoming_diff - outgoing_diff;

        let outgoing_sq_diff = (second_old - old_val) * (second_old - old_val);
        let incoming_sq_diff = (val - prev_new) * (val - prev_new);
        self.sq_diff_sum += incoming_sq_diff - outgoing_sq_diff;

        // 4. Update zero crossings O(1)
        let outgoing_crossing = (old_val > 0.0) != (second_old > 0.0);
        let incoming_crossing = (prev_new > 0.0) != (val > 0.0);
        if outgoing_crossing {
            self.zero_crossings = self.zero_crossings.saturating_sub(1);
        }
        if incoming_crossing {
            self.zero_crossings += 1;
        }

        // Store new value in ring buffer and advance head
        self.buffer[self.head] = val;
        self.head = next_head;
        self.count += 1;
        self.steps_since_anchor += 1;

        // Numerical re-anchoring every 4096 steps to eliminate IEEE 754 drift
        if self.steps_since_anchor >= 4096 {
            self.recompute_accumulators();
        }

        true
    }

    /// Re-anchors accumulators directly from current ring buffer contents.
    fn recompute_accumulators(&mut self) {
        let w = self.window_size;
        let mut sum = 0.0;
        let mut sum_sq = 0.0;
        let mut sum_cube = 0.0;
        let mut sum_quad = 0.0;
        let mut trend_sum = 0.0;
        let mut abs_diff_sum = 0.0;
        let mut sq_diff_sum = 0.0;
        let mut zero_crossings = 0;

        let mut prev_above_zero = false;
        let mut prev_val = 0.0;

        for i in 0..w {
            let idx = (self.head + i) % w;
            let v = self.buffer[idx];
            let v_sq = v * v;
            sum += v;
            sum_sq += v_sq;
            sum_cube += v_sq * v;
            sum_quad += v_sq * v_sq;
            trend_sum += i as f64 * v;

            let above_zero = v > 0.0;
            if i > 0 {
                let d = (v - prev_val).abs();
                abs_diff_sum += d;
                sq_diff_sum += d * d;
                zero_crossings += (above_zero != prev_above_zero) as usize;
            }
            prev_above_zero = above_zero;
            prev_val = v;
        }

        self.sum = sum;
        self.sum_sq = sum_sq;
        self.sum_cube = sum_cube;
        self.sum_quad = sum_quad;
        self.trend_sum = trend_sum;
        self.abs_diff_sum = abs_diff_sum;
        self.sq_diff_sum = sq_diff_sum;
        self.zero_crossings = zero_crossings;
        self.steps_since_anchor = 0;
    }

    /// Copies the current rolling window in sequential order into `out`.
    pub fn get_current_window(&self, out: &mut [f64]) {
        assert_eq!(out.len(), self.window_size);
        let w = self.window_size;
        for (i, val) in out.iter_mut().enumerate() {
            *val = self.buffer[(self.head + i) % w];
        }
    }

    /// Computes the complete 33 features for the current rolling window.
    pub fn compute_features(&self, out: &mut [f64]) {
        assert_eq!(out.len(), NAMES.len());
        if !self.is_full() {
            out.fill(f64::NAN);
            return;
        }

        // Sequential view for order statistics, entropy, and spectral features
        let mut window_buf = vec![0.0; self.window_size];
        self.get_current_window(&mut window_buf);
        compute_all(&window_buf, out);
    }

    /// Computes the 12-feature online subset (no sorting, no FFT).
    ///
    /// Two linear passes over the window plus accumulator reads — O(window),
    /// not O(1); the O(1)-amortized part is the per-sample `push` update.
    pub fn compute_fast(&self, out: &mut [f64]) {
        assert_eq!(out.len(), FAST_NAMES.len());
        if !self.is_full() {
            out.fill(f64::NAN);
            return;
        }

        let w_len = self.window_size;
        let w = w_len as f64;

        let mut sum = 0.0;
        let mut sum_sq = 0.0;
        for &v in &self.buffer {
            sum += v;
            sum_sq += v * v;
        }
        let mean = sum / w;

        let mut m2 = 0.0;
        let mut m3 = 0.0;
        let mut m4 = 0.0;
        for &v in &self.buffer {
            let diff = v - mean;
            let d2 = diff * diff;
            m2 += d2;
            m3 += d2 * diff;
            m4 += d2 * d2;
        }

        let var = m2 / w;
        let std = var.sqrt();

        let skewness = if std == 0.0 {
            f64::NAN
        } else {
            (m3 / w) / (var * std)
        };
        let kurtosis = if std == 0.0 {
            f64::NAN
        } else {
            (m4 / w) / (var * var) - 3.0
        };

        let abs_energy = sum_sq;
        let rms = (abs_energy / w).sqrt();
        let mean_abs_change = self.abs_diff_sum / (w - 1.0);
        let last_idx = (self.head + self.window_size - 1) % self.window_size;
        let mean_change = (self.buffer[last_idx] - self.buffer[self.head]) / (w - 1.0);
        let cid_ce = if std == 0.0 {
            0.0
        } else {
            self.sq_diff_sum.sqrt() / std
        };
        let zero_crossings = self.zero_crossings as f64;

        let t_mean = (w - 1.0) * 0.5;
        let var_t = (w * w - 1.0) / 12.0;
        let sum_t2 = w * var_t;
        let cov_tx = self.trend_sum - w * t_mean * mean;
        let trend_slope = cov_tx / sum_t2;

        out[0] = mean;
        out[1] = std;
        out[2] = var;
        out[3] = skewness;
        out[4] = kurtosis;
        out[5] = abs_energy;
        out[6] = rms;
        out[7] = mean_abs_change;
        out[8] = mean_change;
        out[9] = cid_ce;
        out[10] = zero_crossings;
        out[11] = trend_slope;
    }
}

pub const FAST_NAMES: &[&str] = &[
    "mean",
    "std",
    "var",
    "skewness",
    "kurtosis",
    "abs_energy",
    "root_mean_square",
    "mean_abs_change",
    "mean_change",
    "cid_ce",
    "zero_crossings",
    "trend_slope",
];

#[cfg(test)]
mod tests {
    use super::*;

    #[test]
    fn streaming_matches_batch_window() {
        let w = 10;
        let mut extractor = StreamingExtractor::new(w);
        let data: Vec<f64> = (0..50)
            .map(|i| (i as f64 * 0.3).sin() * 5.0 + 2.0)
            .collect();

        for (i, &val) in data.iter().enumerate() {
            let ready = extractor.push(val);
            if i >= w - 1 {
                assert!(ready);
                let mut stream_feats = [0.0; 33];
                extractor.compute_features(&mut stream_feats);

                let window_slice = &data[i + 1 - w..=i];
                let mut batch_feats = [0.0; 33];
                compute_all(window_slice, &mut batch_feats);

                for k in 0..33 {
                    let s = stream_feats[k];
                    let b = batch_feats[k];
                    if s.is_nan() {
                        assert!(b.is_nan(), "Feature {k} ({}) mismatch", NAMES[k]);
                    } else {
                        let diff = (s - b).abs();
                        assert!(
                            diff < 1e-10,
                            "Feature {k} ({}) diff {diff}: stream {s}, batch {b}",
                            NAMES[k]
                        );
                    }
                }
            } else {
                assert!(!ready);
            }
        }
    }
}
