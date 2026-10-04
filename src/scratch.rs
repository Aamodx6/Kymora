//! Per-thread scratchpad for allocation-free execution in the hot path.
//!
//! Reused across every series processed by a worker thread. Grow-only;
//! never deallocates during batch feature extraction.

use realfft::num_complex::Complex;
use realfft::RealFftPlanner;

#[repr(align(64))]
pub struct Scratch {
    pub centered: Vec<f64>,
    pub sorted: Vec<f64>,
    pub diffs: Vec<f64>,
    pub fft_in: Vec<f64>,
    pub fft_out: Vec<Complex<f64>>,
    pub fft_scratch: Vec<Complex<f64>>,
    pub power: Vec<f64>,
    pub acf: Vec<f64>,
    pub planner: RealFftPlanner<f64>,
    pub sel_scratch: crate::kernels::sort::SelScratch,
    pub view_buf: Vec<f64>,
}

impl Scratch {
    /// Create a new scratchpad with initial preallocated capacity.
    pub fn new(capacity: usize) -> Self {
        let cap = capacity.max(64);
        let nbins = cap / 2 + 1;
        Self {
            centered: Vec::with_capacity(cap),
            sorted: Vec::with_capacity(cap),
            diffs: Vec::with_capacity(cap),
            fft_in: Vec::with_capacity(cap),
            fft_out: Vec::with_capacity(nbins),
            fft_scratch: Vec::with_capacity(nbins * 2),
            power: Vec::with_capacity(nbins),
            acf: Vec::with_capacity(32),
            planner: RealFftPlanner::new(),
            sel_scratch: crate::kernels::sort::SelScratch::new(),
            view_buf: Vec::with_capacity(cap),
        }
    }

    /// Ensure all scratch vectors can hold at least `len` elements without reallocation.
    #[inline]
    pub fn ensure_capacity(&mut self, len: usize) {
        if self.centered.capacity() < len {
            self.centered.reserve(len - self.centered.capacity());
        }
        if self.sorted.capacity() < len {
            self.sorted.reserve(len - self.sorted.capacity());
        }
        if self.diffs.capacity() < len {
            self.diffs.reserve(len - self.diffs.capacity());
        }
        if self.fft_in.capacity() < len {
            self.fft_in.reserve(len - self.fft_in.capacity());
        }
        let nbins = len / 2 + 1;
        if self.power.capacity() < nbins {
            self.power.reserve(nbins - self.power.capacity());
        }
        self.sel_scratch.ensure_capacity(len);
        if self.view_buf.capacity() < len {
            self.view_buf.reserve(len - self.view_buf.capacity());
        }
    }
}
