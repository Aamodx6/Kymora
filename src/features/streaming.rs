#![deny(unsafe_code)]

//! Online incremental streaming feature extractor.
//!
//! Rolling window of size `window_size` with O(1)-amortized [`StreamingExtractor::push`]
//! and O(1) [`StreamingExtractor::compute_fast`]:
//!
//! - The four central-moment accumulators are kept as *anchored* shifted power
//!   sums `s_k = Σ (x - anchor)^k`. `anchor` is the exact window mean at the
//!   last re-anchor, so deviations are small and no catastrophic cancellation
//!   occurs (raw power sums `Σx^k` would lose all precision on e.g. `1e9 +
//!   noise`). Central moments come from the binomial expansion, which is
//!   accurate while `|mean - anchor|` is small relative to the window spread.
//! - Two guards keep that condition true. A periodic guard re-anchors every
//!   `anchor_interval` pushes (default 4096). A drift guard re-anchors as soon
//!   as the mean has drifted more than a quarter of a standard deviation from
//!   the anchor. Either way a re-anchor is one exact O(W) pass in batch
//!   summation order, so accumulator error never compounds.
//! - `trend_dev`, `abs_diff_sum`, `sq_diff_sum`, `zero_crossings` and the
//!   constant-series flag (`unequal_adjacent == 0`) are maintained exactly in
//!   O(1) per push; the trend accumulator stores deviations from the anchor
//!   (`Σ i·(x - anchor)`), so the slope stays accurate on large-offset series
//!   where `Σ i·x` would cancel catastrophically. NaN/±inf occupancy is
//!   counted so degenerate windows can follow the batch value contract.
//!
//! Complexity contract (see also the streaming guide in `docs/`):
//!
//! | operation | cost |
//! |---|---|
//! | `push` | O(1) amortized; an exact O(W) re-anchor fires at most every `min(anchor_interval, ~0.06 * W)` pushes |
//! | `compute_fast` (all 12 features) | O(1): pure accumulator reads, no window scan |
//! | `compute_fast` on a window containing ±inf | O(W) exact fallback via [`compute_all`], bit-matching batch |
//! | `compute_features` (`kind = "all"`) | O(W)-plus: the full batch pipeline on the current window |

use super::{compute_all, stats, NAMES};

/// Default number of pushes between exact accumulator re-anchors.
/// Caps the worst-case drift on huge windows; the drift guard below usually
/// fires first (about every 6% of the window on random data).
pub const DEFAULT_ANCHOR_INTERVAL: usize = 4096;

/// Re-anchor once the window mean has drifted more than this fraction of the
/// window standard deviation away from the anchor. Keeps the binomial
/// expansion in `compute_fast` accurate to ~1e-13 relative on stationary
/// data, far inside the 1e-9 streaming-vs-batch tolerance.
const DRIFT_GUARD_SIGMA_FRACTION: f64 = 0.25;

/// Incremental streaming extractor maintaining a rolling window of size `window_size`.
#[derive(Debug, Clone)]
pub struct StreamingExtractor {
    window_size: usize,
    buffer: Vec<f64>,
    head: usize,
    count: usize,

    // Anchored shifted power sums: s_k = Σ (x - anchor)^k over the window.
    anchor: f64,
    s1: f64,
    s2: f64,
    s3: f64,
    s4: f64,

    // Exact O(1) positional/difference accumulators. The trend accumulator
    // stores anchor-relative deviations so the slope never cancels on
    // large-offset series.
    trend_dev: f64,
    abs_diff_sum: f64,
    sq_diff_sum: f64,
    zero_crossings: usize,

    // Degenerate-window bookkeeping (batch value contract).
    nan_count: usize,
    inf_count: usize,
    unequal_adjacent: usize,

    // Numerical stabilization.
    anchor_interval: usize,
    steps_since_anchor: usize,
}

impl StreamingExtractor {
    /// Create a new streaming extractor with the specified window capacity.
    /// `window_size` must be at least 1 (the FFI layer rejects 0 with
    /// `ValueError`; this assertion is a backstop, never user-reachable).
    pub fn new(window_size: usize) -> Self {
        assert!(window_size >= 1, "window_size must be at least 1");
        Self {
            window_size,
            buffer: vec![0.0; window_size],
            head: 0,
            count: 0,
            anchor: 0.0,
            s1: 0.0,
            s2: 0.0,
            s3: 0.0,
            s4: 0.0,
            trend_dev: 0.0,
            abs_diff_sum: 0.0,
            sq_diff_sum: 0.0,
            zero_crossings: 0,
            nan_count: 0,
            inf_count: 0,
            unequal_adjacent: 0,
            anchor_interval: DEFAULT_ANCHOR_INTERVAL,
            steps_since_anchor: 0,
        }
    }

    /// Builder-style override of the periodic re-anchor interval (pushes).
    /// Must be at least 1; the FFI layer validates user input.
    pub fn with_anchor_interval(mut self, anchor_interval: usize) -> Self {
        assert!(anchor_interval >= 1, "anchor_interval must be at least 1");
        self.anchor_interval = anchor_interval;
        self
    }

    /// Override the periodic re-anchor interval (pushes) after construction.
    /// Must be at least 1; the FFI layer validates user input.
    pub fn set_anchor_interval(&mut self, anchor_interval: usize) {
        assert!(anchor_interval >= 1, "anchor_interval must be at least 1");
        self.anchor_interval = anchor_interval;
    }

    /// Returns the periodic re-anchor interval in pushes.
    #[inline]
    pub fn anchor_interval(&self) -> usize {
        self.anchor_interval
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
        self.anchor = 0.0;
        self.s1 = 0.0;
        self.s2 = 0.0;
        self.s3 = 0.0;
        self.s4 = 0.0;
        self.trend_dev = 0.0;
        self.abs_diff_sum = 0.0;
        self.sq_diff_sum = 0.0;
        self.zero_crossings = 0;
        self.nan_count = 0;
        self.inf_count = 0;
        self.unequal_adjacent = 0;
        self.steps_since_anchor = 0;
    }

    /// Ingest a new sample into the rolling window with O(1)-amortized state update.
    ///
    /// Returns `true` if the window is full and a valid feature vector is available.
    pub fn push(&mut self, val: f64) -> bool {
        let w = self.window_size;

        if self.count < w {
            // Warming up: fill buffer sequentially.
            self.buffer[self.count] = val;
            self.count += 1;
            if self.count == w {
                self.recompute_accumulators();
                return true;
            }
            return false;
        }

        // Rolling update: window is already full. Evict buffer[head].
        let old_val = self.buffer[self.head];
        let prev_new = self.buffer[(self.head + w - 1) % w];

        // Raw window sum before the update, needed for the anchor-relative
        // trend accumulator: t1' = t1 - ((s1_prev) - (old - a)) + (W-1)(new - a).
        // Everything is O(1)-magnitude (deviations from the anchor), so no
        // cancellation can occur regardless of the series offset.
        let dev_old = old_val - self.anchor;
        let dev_new = val - self.anchor;
        self.trend_dev += (w as f64 - 1.0) * dev_new - (self.s1 - dev_old);

        // Anchored shifted power sums, O(1). Deviations from the anchor are
        // small by the drift-guard invariant, so no cancellation occurs here.
        let d_old = dev_old;
        let d_new = dev_new;
        self.s1 += d_new - d_old;
        let n2 = d_new * d_new;
        let o2 = d_old * d_old;
        self.s2 += n2 - o2;
        self.s3 += n2 * d_new - o2 * d_old;
        self.s4 += n2 * n2 - o2 * o2;

        if w >= 2 {
            let second_old = self.buffer[(self.head + 1) % w];

            // Successive differences: one adjacency leaves, one enters.
            let d_out = second_old - old_val;
            let d_in = val - prev_new;
            self.abs_diff_sum += d_in.abs() - d_out.abs();
            self.sq_diff_sum += d_in * d_in - d_out * d_out;

            // Zero crossings with the batch `>`-on-both-sides convention.
            if (old_val > 0.0) != (second_old > 0.0) {
                self.zero_crossings = self.zero_crossings.saturating_sub(1);
            }
            if (prev_new > 0.0) != (val > 0.0) {
                self.zero_crossings += 1;
            }

            // Constant-series flag: zero unequal adjacencies <=> all equal
            // (NaN compares unequal to everything, so NaN windows are never
            // "constant" — but those return all-NaN before this is read).
            if old_val != second_old {
                self.unequal_adjacent = self.unequal_adjacent.saturating_sub(1);
            }
            if prev_new != val {
                self.unequal_adjacent += 1;
            }
        }

        // Degenerate-value occupancy.
        if old_val.is_nan() {
            self.nan_count -= 1;
        }
        if val.is_nan() {
            self.nan_count += 1;
        }
        if old_val.is_infinite() {
            self.inf_count -= 1;
        }
        if val.is_infinite() {
            self.inf_count += 1;
        }

        // Store new value in ring buffer and advance head.
        self.buffer[self.head] = val;
        self.head = (self.head + 1) % w;
        self.count += 1;
        self.steps_since_anchor += 1;

        // Numerical stabilization: periodic exact re-anchor (caps drift on
        // huge windows) plus drift guard (fires first on ordinary data, about
        // every 6% of the window, keeping the expansion accurate).
        if self.steps_since_anchor >= self.anchor_interval || self.drift_exceeded() {
            self.recompute_accumulators();
        }

        true
    }

    /// True when the window mean has drifted too far from the anchor for the
    /// binomial expansion in `compute_fast` to stay accurate. Never fires on
    /// constant, NaN/inf-containing, or unfilled windows.
    fn drift_exceeded(&self) -> bool {
        let w = self.window_size;
        if w < 2 || self.nan_count > 0 || self.inf_count > 0 {
            return false;
        }
        if self.unequal_adjacent == 0 {
            // Constant window: every deviation is exactly zero, expansion exact.
            return false;
        }
        let wf = w as f64;
        let drift = self.s1 / wf;
        let m2 = self.s2 - self.s1 * drift;
        if !m2.is_finite() || m2 <= 0.0 {
            // Non-positive spread estimate means the accumulators have already
            // degraded (or the window is numerically constant): re-anchor to
            // the exact state rather than expanding around a bad anchor.
            return true;
        }
        let frac = DRIFT_GUARD_SIGMA_FRACTION;
        drift * drift > frac * frac * (m2 / wf)
    }

    /// Re-anchors accumulators directly from current ring-buffer contents.
    ///
    /// Single source of exactness: the mean is the plain sequential sum in
    /// oldest-to-newest order (identical operations to the batch pass 1, so
    /// the anchor bit-matches the batch mean), and the shifted sums run
    /// oldest-to-newest exactly like the batch centered pass 2.
    fn recompute_accumulators(&mut self) {
        let w = self.window_size;
        let mut sum = 0.0;
        let mut nan_count = 0usize;
        let mut inf_count = 0usize;
        for i in 0..w {
            let v = self.buffer[(self.head + i) % w];
            sum += v;
            nan_count += v.is_nan() as usize;
            inf_count += v.is_infinite() as usize;
        }
        let mean = sum / w as f64;
        self.anchor = mean;

        let mut s1 = 0.0;
        let mut s2 = 0.0;
        let mut s3 = 0.0;
        let mut s4 = 0.0;
        let mut trend_dev = 0.0;
        let mut abs_diff_sum = 0.0;
        let mut sq_diff_sum = 0.0;
        let mut zero_crossings = 0usize;
        let mut unequal_adjacent = 0usize;

        let mut prev_above_zero = false;
        let mut prev_val = 0.0;

        for i in 0..w {
            let v = self.buffer[(self.head + i) % w];
            let dev = v - mean;
            let d2 = dev * dev;
            s1 += dev;
            s2 += d2;
            s3 += d2 * dev;
            s4 += d2 * d2;
            trend_dev += i as f64 * dev;

            let above_zero = v > 0.0;
            if i > 0 {
                let d = v - prev_val;
                abs_diff_sum += d.abs();
                sq_diff_sum += d * d;
                zero_crossings += (above_zero != prev_above_zero) as usize;
                unequal_adjacent += (v != prev_val) as usize;
            }
            prev_above_zero = above_zero;
            prev_val = v;
        }

        self.s1 = s1;
        self.s2 = s2;
        self.s3 = s3;
        self.s4 = s4;
        self.trend_dev = trend_dev;
        self.abs_diff_sum = abs_diff_sum;
        self.sq_diff_sum = sq_diff_sum;
        self.zero_crossings = zero_crossings;
        self.nan_count = nan_count;
        self.inf_count = inf_count;
        self.unequal_adjacent = unequal_adjacent;
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
    /// Exact: runs the full batch pipeline on the materialized window.
    pub fn compute_features(&self, out: &mut [f64]) {
        assert_eq!(out.len(), NAMES.len());
        if !self.is_full() {
            out.fill(f64::NAN);
            return;
        }

        // Sequential view for order statistics, entropy, and spectral features.
        let mut window_buf = vec![0.0; self.window_size];
        self.get_current_window(&mut window_buf);
        compute_all(&window_buf, out);
    }

    /// Computes the 12-feature online subset in O(1) from the accumulators —
    /// no window scan, no allocation, no sorting, no FFT.
    ///
    /// Accuracy: central moments come from the anchored binomial expansion,
    /// kept accurate by the re-anchor guards in [`Self::push`]; difference,
    /// trend and crossing accumulators are maintained exactly. Matches the
    /// batch pipeline within rtol 1e-9 on well-conditioned windows (random,
    /// trending, constant, large-offset, small-variance).
    ///
    /// Degenerate windows follow the batch value contract: any NaN in the
    /// window yields an all-NaN row; a window containing ±inf takes the exact
    /// O(W) fallback below (documented, rare) so its output matches batch by
    /// construction; a length-1 window yields NaN for every feature that
    /// batch leaves undefined on length-1 input.
    pub fn compute_fast(&self, out: &mut [f64]) {
        assert_eq!(out.len(), FAST_NAMES.len());
        if !self.is_full() {
            out.fill(f64::NAN);
            return;
        }
        if self.nan_count > 0 {
            out.fill(f64::NAN);
            return;
        }
        if self.inf_count > 0 {
            self.compute_fast_inf_fallback(out);
            return;
        }

        let w_len = self.window_size;
        let w = w_len as f64;
        let constant = self.unequal_adjacent == 0;

        // Anchored binomial expansion of the central moments.
        let drift = self.s1 / w;
        let m2 = self.s2 - self.s1 * drift;
        let m3 = self.s3 - 3.0 * drift * self.s2 + 2.0 * drift * drift * self.s1;
        let m4 = self.s4 - 4.0 * drift * self.s3 + 6.0 * drift * drift * self.s2
            - 3.0 * drift * drift * drift * self.s1;

        let mean = self.anchor + drift;
        // Batch forces var to exactly 0 on constant series; the clamp below
        // absorbs sub-ulp negative rounding on numerically-constant windows.
        let var = if constant { 0.0 } else { (m2 / w).max(0.0) };
        let std = var.sqrt();

        let skewness = stats::skewness(m3, w, var, std, mean);
        let kurtosis = stats::kurtosis(m4, w, var, std, mean);

        // Σx²: constant windows use W·first² exactly. The anchored expansion
        // would cancel catastrophically here whenever the anchor is stale
        // (e.g. an all-zero window with a pre-zero anchor: s2 + 2a·s1 + W·a²
        // = 0.333… − 0.667… + 0.333… leaves ~1e-16 residue instead of true 0,
        // and rms turns it into ~6e-9 vs batch 0.0). The drift guard skips
        // constant windows (their moments need no anchor), so this shortcut
        // is also what keeps them anchor-independent. Non-constant windows
        // use the exact expansion (result large ⇒ relatively accurate).
        let (abs_energy, rms) = if constant {
            let first = self.buffer[self.head];
            let e = w * first * first;
            (e, (e / w).sqrt())
        } else {
            let e = self.s2 + 2.0 * self.anchor * self.s1 + w * self.anchor * self.anchor;
            (e, (e / w).sqrt())
        };
        let mean_abs_change = self.abs_diff_sum / (w - 1.0);
        let last_idx = (self.head + self.window_size - 1) % self.window_size;
        let mean_change = (self.buffer[last_idx] - self.buffer[self.head]) / (w - 1.0);
        // Batch scales each difference by std before squaring (overflow-safe);
        // the O(1) form below differs from it only by summation rounding.
        // Length-1 windows: batch leaves cid_ce undefined -> NaN.
        let cid_ce = if w_len < 2 {
            f64::NAN
        } else if std == 0.0 {
            0.0
        } else {
            self.sq_diff_sum.sqrt() / std
        };
        let zero_crossings = self.zero_crossings as f64;

        // Least-squares slope vs t = 0..W-1, same closed form as batch
        // `linear_trend` but accumulated anchor-relative: cov = t1 - t_mean*s1
        // never subtracts offset-scale terms. Length-1: NaN like batch
        // (batch returns NaN for n < 2; the incremental trend_dev carries
        // ~1e-16 rounding residue, so this must be explicit, not 0/0).
        // Constant series: exactly 0 like batch.
        let slope = if w_len < 2 {
            f64::NAN
        } else if constant {
            0.0
        } else {
            let t_mean = (w - 1.0) * 0.5;
            let var_t = (w * w - 1.0) / 12.0;
            let sum_t2 = w * var_t;
            let cov_tx = self.trend_dev - t_mean * self.s1;
            cov_tx / sum_t2
        };

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
        out[11] = slope;
    }

    /// Exact O(W) fallback for windows containing ±inf: runs the batch
    /// pipeline on the materialized window and gathers the fast subset, so
    /// output matches batch by construction. Only non-finite windows pay this.
    fn compute_fast_inf_fallback(&self, out: &mut [f64]) {
        debug_assert!(self.is_full());
        debug_assert!(self.inf_count > 0);
        let mut window_buf = vec![0.0; self.window_size];
        self.get_current_window(&mut window_buf);
        let mut full = vec![0.0; NAMES.len()];
        compute_all(&window_buf, &mut full);
        // FAST_NAMES in batch column order: mean, std, var, skewness,
        // kurtosis, abs_energy, rms, mac, mc, cid, zc, slope.
        const GATHER: [usize; 12] = [0, 1, 2, 10, 11, 12, 13, 14, 15, 16, 18, 27];
        for (slot, &g) in out.iter_mut().zip(GATHER.iter()) {
            *slot = full[g];
        }
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

    fn check_window_matches_batch(data: &[f64], w: usize, anchor_interval: Option<usize>) {
        let mut extractor = match anchor_interval {
            Some(k) => StreamingExtractor::new(w).with_anchor_interval(k),
            None => StreamingExtractor::new(w),
        };
        for (i, &val) in data.iter().enumerate() {
            let ready = extractor.push(val);
            if i + 1 >= w {
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

                // Fast tier must match the batch fast subset to rtol 1e-9
                // (plus an absolute floor for features that are ~0 on this
                // window, e.g. the mean of a full sine period).
                let mut fast = [0.0; 12];
                extractor.compute_fast(&mut fast);
                const GATHER: [usize; 12] = [0, 1, 2, 10, 11, 12, 13, 14, 15, 16, 18, 27];
                for (j, &g) in GATHER.iter().enumerate() {
                    let s = fast[j];
                    let b = batch_feats[g];
                    if b.is_nan() {
                        assert!(s.is_nan(), "fast {j} should be NaN");
                    } else {
                        let diff = (s - b).abs();
                        assert!(
                            diff <= 1e-12 + 1e-9 * b.abs(),
                            "fast {j} diff {diff}: stream {s}, batch {b}",
                        );
                    }
                }
            } else {
                assert!(!ready);
            }
        }
    }

    #[test]
    fn streaming_matches_batch_window() {
        let w = 10;
        let data: Vec<f64> = (0..50)
            .map(|i| (i as f64 * 0.3).sin() * 5.0 + 2.0)
            .collect();
        check_window_matches_batch(&data, w, None);
    }

    #[test]
    fn near_degenerate_window_yields_nan_both_paths() {
        // Found by hypothesis exploration after the .hypothesis/ cache purge:
        // a 1-ulp window. Batch summation rounds the mean onto an endpoint,
        // so the naive skew/kurt ratios are rounding garbage (~sqrt(2));
        // both paths must return NaN like scipy (gh-15905 guard).
        let mut data = vec![0.0; 30];
        data.push(-10.0);
        data.push(-9.999999999999998);
        let w = 2;
        let mut extractor = StreamingExtractor::new(w);
        extractor.set_anchor_interval(1);
        for (i, &val) in data.iter().enumerate() {
            let ready = extractor.push(val);
            assert_eq!(ready, i + 1 >= w);
        }
        let mut fast = [0.0; 12];
        extractor.compute_fast(&mut fast);
        assert!(
            fast[3].is_nan(),
            "stream skew should be NaN, got {}",
            fast[3]
        );
        assert!(
            fast[4].is_nan(),
            "stream kurt should be NaN, got {}",
            fast[4]
        );
        let mut batch = [0.0; 33];
        compute_all(&data[data.len() - w..], &mut batch);
        assert!(
            batch[10].is_nan(),
            "batch skew should be NaN, got {}",
            batch[10]
        );
        assert!(
            batch[11].is_nan(),
            "batch kurt should be NaN, got {}",
            batch[11]
        );
    }

    #[test]
    fn anchored_fast_matches_batch_with_rare_reanchor() {
        // Anchor interval far beyond the stream length: only the drift guard
        // keeps the expansion accurate.
        let w = 32;
        let data: Vec<f64> = (0..2000)
            .map(|i| (i as f64 * 0.11).sin() * 3.0 + 0.5 * (i as f64 * 0.031).cos())
            .collect();
        check_window_matches_batch(&data, w, Some(1_000_000));
    }

    #[test]
    fn anchored_fast_matches_batch_large_offset() {
        // 1e9 + noise: raw power sums would lose everything here.
        //
        // Two floating-point facts shape the bounds below (both verified by
        // measurement, not assumed):
        //
        // 1. INPUT QUANTIZATION. ulp(1e9) = 1.19e-7, so storing 1e9 + noise
        //    already rounds each sample by up to 6e-8. m3/m4 amplify sample
        //    error ~3x/4x per unit deviation, so the third/fourth moments of
        //    the STORED window legitimately differ from the moments of the
        //    pre-offset noise by ~1e-7. Any exact reference must therefore be
        //    computed on the quantized values `(x - 1e9)` (exact by Sterbenz),
        //    never on the pristine noise.
        // 2. BATCH CENTER ERROR. The batch mean is a plain sum with ~3e-8
        //    absolute error at 1e9 offset (W=64), and m3/m4 amplify center
        //    error by 3*m2 / 4*m3 (~60x/~100x here). Measured on this
        //    generator: batch-vs-quantized-exact disagrees by 1.3e-8 (var),
        //    3.7e-7 (skew), 4.7e-8 (kurt). No independently-rounded O(1)
        //    computation can match batch skew/kurt to 1e-9 under these
        //    conditions; the streaming center (anchor + s1/W) is in fact the
        //    MORE accurate of the two (it cancels the summation residual).
        //
        // Hence: skew/kurt assert streaming-vs-batch within the measured
        // center-conditioning envelope (5e-6 absolute, ~10x above the observed
        // max), and streaming-vs-QUANTIZED-exact to 1e-9 (the real accuracy
        // proof). All other fast features match batch to 1e-9.
        let mut state = 0x12345678u64;
        let mut next = || {
            state = state.wrapping_mul(6364136223846793005).wrapping_add(1);
            ((state >> 11) as f64 / (1u64 << 53) as f64) * 2.0 - 1.0
        };
        let w = 64;
        let noise: Vec<f64> = (0..3000).map(|_| next()).collect();
        let data: Vec<f64> = noise.iter().map(|v| 1e9 + v).collect();

        let mut extractor = StreamingExtractor::new(w);
        const GATHER: [usize; 12] = [0, 1, 2, 10, 11, 12, 13, 14, 15, 16, 18, 27];
        for (i, &val) in data.iter().enumerate() {
            if !extractor.push(val) {
                continue;
            }
            let mut fast = [0.0; 12];
            extractor.compute_fast(&mut fast);
            let window_slice = &data[i + 1 - w..=i];
            let mut batch = [0.0; 33];
            compute_all(window_slice, &mut batch);

            // Quantized-exact reference: the noise actually stored in each
            // f64 sample (Sterbenz-exact), with plain two-pass moments.
            let qmean: f64 = window_slice.iter().map(|v| v - 1e9).sum::<f64>() / w as f64;
            let (mut e2, mut e3, mut e4) = (0.0, 0.0, 0.0);
            for &v in window_slice {
                let d = (v - 1e9) - qmean;
                let d2 = d * d;
                e2 += d2;
                e3 += d2 * d;
                e4 += d2 * d2;
            }
            let wf = w as f64;
            let evar = e2 / wf;
            let estd = evar.sqrt();

            for (j, &g) in GATHER.iter().enumerate() {
                let (s, b) = (fast[j], batch[g]);
                if b.is_nan() {
                    assert!(s.is_nan(), "offset fast {j} should be NaN");
                    continue;
                }
                let diff = (s - b).abs();
                if g == 10 || g == 11 {
                    assert!(diff < 5e-6, "offset fast {j} diff {diff}: {s} vs {b}");
                    let e = if g == 10 {
                        e3 / wf / (evar * estd)
                    } else {
                        e4 / wf / (evar * evar) - 3.0
                    };
                    let ediff = (s - e).abs();
                    assert!(
                        ediff <= 1e-9 + 1e-9 * e.abs(),
                        "offset fast {j} vs quantized-exact: {s} vs {e}"
                    );
                } else {
                    assert!(
                        diff <= 1e-12 + 1e-9 * b.abs(),
                        "offset fast {j} diff {diff}: stream {s}, batch {b}",
                    );
                }
            }
        }
    }

    #[test]
    fn anchored_fast_matches_batch_trending() {
        let w = 48;
        let data: Vec<f64> = (0..3000)
            .map(|i| 0.05 * i as f64 + (i as f64 * 0.2).sin())
            .collect();
        check_window_matches_batch(&data, w, None);
    }

    #[test]
    fn fast_tier_constant_window() {
        let w = 16;
        let mut extractor = StreamingExtractor::new(w);
        for _ in 0..w {
            extractor.push(3.25);
        }
        let mut fast = [0.0; 12];
        extractor.compute_fast(&mut fast);
        let mut batch = [0.0; 33];
        compute_all(&vec![3.25; w], &mut batch);
        const GATHER: [usize; 12] = [0, 1, 2, 10, 11, 12, 13, 14, 15, 16, 18, 27];
        for (j, &g) in GATHER.iter().enumerate() {
            let (s, b) = (fast[j], batch[g]);
            if b.is_nan() {
                assert!(s.is_nan(), "fast {j} should be NaN");
            } else {
                // Exact for counters/NaN-guarded features; summation-order
                // rounding (~1e-16) for mean/abs_energy/rms.
                let diff = (s - b).abs();
                assert!(diff <= 1e-12 + 1e-9 * b.abs(), "fast {j}: {s} vs {b}");
            }
        }
    }

    #[test]
    fn window_size_one_matches_batch() {
        let mut extractor = StreamingExtractor::new(1);
        for &v in &[2.5, -1.0, 0.0] {
            assert!(extractor.push(v));
            let mut fast = [0.0; 12];
            extractor.compute_fast(&mut fast);
            let mut batch = [0.0; 33];
            compute_all(&[v], &mut batch);
            const GATHER: [usize; 12] = [0, 1, 2, 10, 11, 12, 13, 14, 15, 16, 18, 27];
            for (j, &g) in GATHER.iter().enumerate() {
                let (s, b) = (fast[j], batch[g]);
                if b.is_nan() {
                    assert!(s.is_nan(), "w=1 fast {j} should be NaN");
                } else {
                    assert_eq!(s.to_bits(), b.to_bits(), "w=1 fast {j}: {s} vs {b}");
                }
            }
        }
    }

    #[test]
    fn nan_window_yields_all_nan_fast_row() {
        let w = 8;
        let mut extractor = StreamingExtractor::new(w);
        for i in 0..w {
            extractor.push(if i == 3 { f64::NAN } else { i as f64 });
        }
        let mut fast = [0.0; 12];
        extractor.compute_fast(&mut fast);
        assert!(fast.iter().all(|v| v.is_nan()));
        // NaN slides out: exact recovery, no poisoned accumulators.
        for i in 0..w {
            extractor.push(100.0 + i as f64);
        }
        extractor.compute_fast(&mut fast);
        let mut batch = [0.0; 33];
        let win: Vec<f64> = (0..w).map(|i| 100.0 + i as f64).collect();
        compute_all(&win, &mut batch);
        const GATHER: [usize; 12] = [0, 1, 2, 10, 11, 12, 13, 14, 15, 16, 18, 27];
        for (j, &g) in GATHER.iter().enumerate() {
            let diff = (fast[j] - batch[g]).abs();
            assert!(diff <= 1e-12 + 1e-9 * batch[g].abs(), "fast {j}");
        }
    }

    #[test]
    fn inf_window_matches_batch_by_fallback() {
        let w = 8;
        for bad in [f64::INFINITY, f64::NEG_INFINITY] {
            let mut extractor = StreamingExtractor::new(w);
            for i in 0..w {
                extractor.push(if i == 5 { bad } else { i as f64 });
            }
            let mut fast = [0.0; 12];
            extractor.compute_fast(&mut fast);
            let mut win: Vec<f64> = (0..w).map(|i| i as f64).collect();
            win[5] = bad;
            let mut batch = [0.0; 33];
            compute_all(&win, &mut batch);
            const GATHER: [usize; 12] = [0, 1, 2, 10, 11, 12, 13, 14, 15, 16, 18, 27];
            for (j, &g) in GATHER.iter().enumerate() {
                let (s, b) = (fast[j], batch[g]);
                if b.is_nan() {
                    assert!(s.is_nan(), "inf fast {j} should be NaN");
                } else {
                    assert_eq!(s.to_bits(), b.to_bits(), "inf fast {j}: {s} vs {b}");
                }
            }
        }
    }
}
